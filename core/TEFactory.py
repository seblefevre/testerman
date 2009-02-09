# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008-2009 Sebastien Lefevre and other contributors
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
##

##
# Test Executable Builder: contains all the necessary
# to create a TE from an ATS.
#
# Currently, the TE is a python script linked to Testerman modules
# to provide access to the Testerman features (distributed test
# environment, TTCN-3 primitives).
#
##

import ConfigManager
import FileSystemManager
import JobTools
import Versions

import logging
import os.path
import pickle
import time
import tokenize
import StringIO
import modulefinder
import imp


def getLogger():
	return logging.getLogger('TEFactory')

def smartReindent(code, indentCharacter = '\t', reindentCount = 1):
	"""
	Adds reindentCount times indentCharacters before each line of Python code code,
	enabling try..catch block code generations.
	Leaves multi-line strings unchanged (i.e. does not add indentation in them).
	
	Due to a limitation in Python tokenizer (INDENT/DEDENT are not reported on comments),
	if a comment starts a code block, it won't be reindented correcty. The code is still
	functional and correctly indented, however.
	
	@type  code: string, as utf-8 
	@param code: the Python code to reindent
	@param indentCharacter: the character/substring to use for indendation. Will also
	                        replace current indentation character(s) with it.
	@param reindentCount: the number of new reindentation level (>= 0)
	
	@rtype: string (utf-8)
	@param: the reindented code.
	"""
	source = StringIO.StringIO(code)

	last_tok_end_pos = 0
	last_tok_line = 0

	# Current indent level
	indentLevel = 0 

	# Now tokenize, keep track of current indentation,
	# add new indents on new lines only.
	# tokenize ensure that multiline tokens will be reproduced unchanged (i.e. not reindented)
	ret = []
	for toknum, tokval, (srow, scol), (erow, ecol), tok_line in tokenize.generate_tokens(source.readline):
		# INDENT/DEDENT are reported only once for the block. So keep track of the current indentation level.
		if toknum == tokenize.INDENT:
			indentLevel += 1
		elif toknum == tokenize.DEDENT:
			indentLevel -= 1
		else:
			if last_tok_line < srow:
				# We are starting a new line. Add the indentation.
				ret.append(reindentCount * indentCharacter)
				last_tok_line = erow
				# Restore the current block indentation
				ret.append(indentLevel * indentCharacter)
			else:
				# Same line. Make sure to add the original spaces
				ret.append(tok_line[last_tok_end_pos:scol])

			last_tok_end_pos = ecol
			ret.append(tokval)

	return ''.join(ret)

def createTestExecutable(name, ats):
	"""
	Creates a complete, command-line parametrized TE from a source ATS.

	@type  name: string
	@param name: the ATS friendly name / identifier	
	@type  ats: string (utf-8)
	@param ats: the source ats (contains metadata as Python comments)
	
	@rtype: string (utf-8 encoded)
	@returns: the test executable Python script content.
	"""
	# For now, not everythin can be controlled by option flags.
	tacsIp = ConfigManager.get("tacs.ip")
	tacsPort = ConfigManager.get("tacs.port")
	ilPort = ConfigManager.get("interface.il.port")
	ilIp = ConfigManager.get("interface.il.ip")
	maxLogPayloadSize = int(ConfigManager.get("testerman.te.log.maxpayloadsize"))
	adapterModuleName = ConfigManager.get("testerman.te.python.ttcn3module")
	
	probePaths = [ os.path.normpath(ConfigManager.get("testerman.server_path") + "/../plugins/probes") ]
	codecPaths = [ os.path.normpath(ConfigManager.get("testerman.server_path") + "/../plugins/codecs") ]

	# We construct the te as a list to ''.join() for better performance (better than str += operator)
	te = []

	# The decorator header
	te.append("""################################################################################
# -*- coding: utf-8 -*-
#
# This Test Executable (TE) was automatically created
# by Testerman Server %(version)s on %(time)s
# based on the source ATS %(name)s.
#
################################################################################

import os
import pickle
import random
import signal
import sys
import time

################################################################################
# Some constants
################################################################################

RETURN_CODE_LOGGER_FAILURE = 10
RETURN_CODE_INIT_FAILURE = 11
RETURN_CODE_CANCELLED = 1
RETURN_CODE_TTCN3_ERROR = 12
RETURN_CODE_TE_ERROR = 13
RETURN_CODE_OK = 0

TS_VERSION = %(version)s

ATS_ID = %(name)s
""" % dict(name = repr(name), version = repr(Versions.getServerVersion()), time = time.strftime("%Y%m%d, at %H:%M:%S", time.localtime(time.time()))))

	# TE global variables
	te.append("""
################################################################################
# TE variables (overridable on the command line)
################################################################################

# Set from command line: job dependent
JobId = int(sys.argv[1])
LogFilename = sys.argv[2]
InputSessionFilename = sys.argv[3]
OutputSessionFilename = sys.argv[4]

# Set from command line (soon): server dependent
IlServerIp = %(ilIp)s
IlServerPort = %(ilPort)d
TacsIp = %(tacsIp)s
TacsPort = %(tacsPort)d
MaxLogPayloadSize = %(maxLogPayloadSize)d
ProbePaths = %(probePaths)s
CodecPaths = %(codecPaths)s
""" % dict(ilIp = repr(ilIp), ilPort = ilPort, tacsIp = repr(tacsIp), tacsPort = tacsPort, 
           maxLogPayloadSize = maxLogPayloadSize, probePaths = repr(probePaths), codecPaths = repr(codecPaths)))

	# Some ATS-dedicated functions
	te.append("""
################################################################################
# TE base functions
################################################################################

def scanPlugins(paths, label):
	for path in paths:
		if not path in sys.path:
			sys.path.append(path)
	for path in paths:
		try:
			for m in os.listdir(path):
				if m.startswith('.') or m.startswith('__init__') or not (os.path.isdir(path + '/' + m) or m.endswith('.py')):
					continue
				if m.endswith('.py'):
					m = m[:-3]
				try:
					__import__(m)
					TestermanTCI.logUser("INFO: analyzed %s %s" % (label, m))
				except Exception, e:
					TestermanTCI.logUser("WARNING: unable to import %s %s: %s" % (label, m, str(e)))
		except Exception, e:
			TestermanTCI.logUser("WARNING: unable to scan %s path %s: %s" % (label, path, str(e)))

def initializeLogger(ilServerIp, ilServerPort, jobId, logFilename, maxPayloadSize):
	TestermanTCI.initialize(ilServerAddress = (ilServerIp, ilServerPort), jobId = jobId, logFilename = logFilename, maxPayloadSize = maxPayloadSize)
	TestermanTCI.logInternal("initializing: using IlServer tcp://%s:%d" % (ilServerIp, ilServerPort))

def finalizeLogger():
	TestermanTCI.finalize()

def initializeTe(tacsIP, tacsPort):
	"\"\"
	Global TE initialization.
	Testerman core libs initialization, connections to Testerman infrastructure,
	TE plugins (probes and codecs) loading.
	"\"\"
	TestermanTCI.logInternal("initializing: using TACS tcp://%s:%d" % (tacsIP, tacsPort))
	TestermanSA.initialize((tacsIP, tacsPort))
	TestermanPA.initialize()
	Testerman._initialize()
	scanPlugins(ProbePaths, "probe")
	scanPlugins(CodecPaths, "codec")

def finalizeTe():
	TestermanTCI.logInternal("finalizing...")
	Testerman._finalize()
	TestermanPA.finalize()
	TestermanSA.finalize()
	TestermanTCI.logInternal("finalized.")

""")

	# TE Initialization
	te.append("""
################################################################################
# TE Main
################################################################################

#: Main return result from the execution
# WARNING/FIXME: make sure that the ATS won't override such a variable (oh well.. what if it does ? nothing impacting...)
ReturnCode = RETURN_CODE_OK
ReturnMessage = ''

##
# Logger initialization
##
try:
	import TestermanTCI
	initializeLogger(ilServerIp = IlServerIp, ilServerPort = IlServerPort, jobId = JobId, logFilename = LogFilename, maxPayloadSize = MaxLogPayloadSize)
except Exception, e:
	# We can't even log anything. 
	print("Unable to connect to logging server: %%s" %% str(e))
	sys.exit(RETURN_CODE_LOGGER_FAILURE)

# TODO: check the current implementation version against the version that generated the TE (TS_VERSION).

# OK, now we can at least log our start event
TestermanTCI.logAtsStarted(id_ = ATS_ID)

##
# Core libs initialization
##
try:
	import %(adapterModuleName)s as Testerman
	from %(adapterModuleName)s import *
	initializeTe(TacsIp, TacsPort)
except Exception, e:
	ReturnCode = RETURN_CODE_INIT_FAILURE
	TestermanTCI.logAtsStopped(id_ = ATS_ID, result = ReturnCode, message = "Unable to initialize Code TE librairies: %%s" %% TestermanTCI.getBacktrace())
	sys.exit(ReturnCode)
""" % dict(adapterModuleName = adapterModuleName))

	# Main try/catch containing the (almost) untouched ATS code
	te.append("""

##
# Cancellation setup (SIGINT/KeyboardInterrupt)
##
def onUserInterruptSignal(sig, frame):
	# Will raise a CancelException before next test execution.
	Testerman._cancel()

signal.signal(signal.SIGINT, onUserInterruptSignal)

##
# "action" management (SIGUSR1)
def onActionPerformed(sig, frame):
	Testerman._actionPerformedByUser()

signal.signal(signal.SIGUSR1, onActionPerformed)

##
# Loads the input session
##
inputSession = {}
try:
	f = open(InputSessionFilename, 'r')
	inputSession = pickle.loads(f.read())
	f.close()
except Exception, e:
	TestermanTCI.logInternal("Unable to load input session: %s" % str(e))

for k, v in inputSession.items():
	Testerman.set_variable(k, v)

##
# Globals wrapping: a way to to export to the global scopes
# variables that will change along the time
# DOES NOT WORK, SORRY.
##
#class GlobalWrapper:
#	@property
#	def mtc(self):
#		testcase = getLocalContext().getTestCase()
#		if testcase:
#			return testcase._mtc
#		else:
#			return None
#
#TheGlobalWrapper = GlobalWrapper()
#
#globals()['mtc'] = TheGlobalWrapper.mtc

##
# ATS code reinjection
##
try:
	# TODO: Normally we should load input session variables here.
	# Note: an empty ATS would lead to an error, since the try/except block
	# won't be filled with any instruction.
	pass

""")
	te.append(smartReindent(ats))
	te.append("""

except TestermanCancelException, e:
	ReturnCode = RETURN_CODE_CANCELLED
	ReturnMessage = "ATS cancelled by user."

except TestermanStopException, e:
	ReturnCode = e.retcode
	if e.retcode is None:
		ReturnCode = RETURN_CODE_OK
	ReturnMessage = "ATS explicitely stopped in control part."

except TestermanTtcn3Exception, e:
	ReturnCode = RETURN_CODE_TTCN3_ERROR
	ReturnMessage = "TTCN-3 like error: %s" % str(TestermanTCI.getBacktrace())

except Exception, e:
	ReturnCode = RETURN_CODE_TE_ERROR
	ReturnMessage = "Generic exception: %s" % str(TestermanTCI.getBacktrace())


# Dumps the current session
try:
	f = open(OutputSessionFilename, 'w')
	# FIXME: implement the real session dump
	f.write(pickle.dumps({}))
	f.close()
except Exception, e:
	TestermanTCI.logInternal("Unable to dump current session: %s" % str(e))


##
# Finalization
##
try:
	finalizeTe()
except:
	pass

TestermanTCI.logAtsStopped(id_ = ATS_ID, result = ReturnCode, message = ReturnMessage)

try:
	finalizeLogger()
except:
	pass

# Make sure all our process children are killed
TestermanPA.killChildren()
sys.exit(ReturnCode)
""")
	
	return ''.join(te)

	
def createCommandLine(jobId, teFilename, logFilename, inputSessionFilename, outputSessionFilename, modulePaths):
	"""
	@rtype: a dict { 'executable': string, 'env': dict[string] of strings, 'args': list of strings }
	@returns: the info needed to an execve or the like to execute the TE.
	"""
	ret = {}

	# No --flags for now.
	cmdOptions = [ str(jobId), logFilename, inputSessionFilename, outputSessionFilename ]

	# Interpreter
	pythonInterpreter = ConfigManager.get("testerman.te.python.interpreter")
	ret['executable'] = pythonInterpreter

	#	Env
	# User modules are in the module paths, shared "administrative" modules are in server_path/modules
	pythonPath = '%(root)s:%(root)s/modules:%(modulepaths)s' % dict(
		root = ConfigManager.get("testerman.server_path"),
		modulepaths = ':'.join(modulePaths))
	libraryPath = '%(root)s:$LD_LIBRARY_PATH' % dict(root = ConfigManager.get("testerman.server_path"))
	ret['env'] = { 'LD_LIBRARY_PATH': libraryPath, 'PYTHONPATH': pythonPath }

	# Executable arguments
	ret['args'] = [ pythonInterpreter, teFilename ] + cmdOptions

	return ret

def dumpSession(session):
	"""
	@type  session: dict[unicode] of python objects
	@param session: the session to dump/serialize so that the TE can reload it from a file.
	
	@rtype: string (not unicode)
	@returns: the session to a TE-readable format (for its input session)
	"""
	return pickle.dumps(session)

def loadSession(dump):
	"""
	Reloads a session struct from a dump as generated by the TE (and by dumpSession).
	
	@type  dump: string
	@param dump: encoded session dump, as created by the TE
	
	@rtype: dict[unicode] of python objects
	@returns: the unserialized session.
	"""
	return pickle.loads(dump)
	
def getDefaultSession(ats):
	"""
	Extracts the default parameters & values from an ats.
	
	@type  ats: string (utf-8)
	@param ats: the ats code, should includes metadata
	
	@rtype: a dict[unicode] of unicode
	@returns: the default session dictionary (parameter_name: default_value)
	"""
	xmlMetadata = JobTools.extractMetadata(ats, '#')
	if xmlMetadata:
		m = JobTools.parseMetadata(xmlMetadata)
		if m:
			return m.getDefaultSessionDict()
	return None

def getDependencyFilenames(ats, atsPath = None):
	"""
	Returns a list of (user) module filenames (including their own dependencies) the ATS depends on.

	NB: this works only because user modules are files only, not packages.
	"""
	ret = []
	# Bootstrap the deps (stored as (list of imported modules, path of the importing file) )
	deps = [ (d, atsPath) for d in _getDirectDependencies(ats) ]
	
	analyzedDeps = []
	
	while len(deps):
		dep, fromFilePath = deps.pop()
		# Some non-userland files - not resolved to build the TE userland package
		if dep in [ 'Testerman' ]:
			continue

		# Skip already analyzed deps (analyzed from this very path,
		# since the same dep name, from different paths, may resolved to
		# different things)
		if (dep, fromFilePath) in analyzedDeps:
			continue

		getLogger().debug("Analyzing dependency %s..." % (dep))

		# Ordered list of filenames within the docroot that could provide the dependency:
		# (module path)
		# - first search from the local file path, if provided,
		# - then search from the userland module paths (limited to '/repository/' for now)
		modulePaths = []
		# First, try a local module (relative path) (same dir as the currently analyzed file)
		if fromFilePath:
			modulePaths.append(fromFilePath)
		for modulePath in [ '/repository' ]:
			modulePaths.append(modulePath)

		getLogger().debug("Analyzing dependency %s, search path: %s..." % (dep, modulePaths))

		found = None
		depSource = None
		for path in modulePaths:
			depFilename = '%s/%s.py' % (path, dep.replace('.', '/'))
			try:
				depSource = FileSystemManager.instance().read(depFilename)
			except Exception:
				pass
			if depSource is not None:
				found = depFilename
				break
		if not found:
			raise Exception('Missing module: %s is not available in the repository (search path: %s)' % (dep, modulePaths))

		# OK, we found a file.
		if not depFilename in ret:
			ret.append(depFilename)

		# Now, analyze it and add new dependencies to analyze
		fromFilePath = '/'.join(depFilename.split('/')[:-1])
		for d in _getDirectDependencies(depSource):
			if not d in deps and d != dep:
				deps.append((d, fromFilePath))

		# Flag the dep as analyzed - from this path (since it may lead to another filename
		# when evaluated from another path)
		analyzedDeps.append((dep, fromFilePath))

	return ret	

def _getDirectDependencies(source):
	"""
	Returns a list of direct dependencies (source is an ATS/Module source code),
	as a list of module names (not filenames !)
	"""
	mf = modulefinder.ModuleFinder()
	fp = StringIO.StringIO(source)
	mf.load_module('__main__', fp, '<string>', ("", "r", imp.PY_SOURCE))

	ret = []	
	for module in mf.any_missing():
		ret.append(module)
	return ret
