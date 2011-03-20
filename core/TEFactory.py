# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008,2009,2010 Sebastien Lefevre and other contributors
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
import re


cm = ConfigManager.instance()

# The Test Executable template is basically a python file
# with some ${token} in it, substituted on TE generation.
# If you modify it, make sure that the resulting TE
# keeps the same command line flags for server-controlled executions.
TE_TEMPLATE_NAME = "TestExecutable.py.template"


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
	Creates a complete, command-line parameterized TE from a source ATS.
	This basically replaces specific fields in the TE template with
	actual values.

	@type  name: string
	@param name: the ATS friendly name / identifier	
	@type  ats: string (utf-8)
	@param ats: the source ats (contains metadata as Python comments)
	
	@rtype: string (utf-8 encoded)
	@returns: the test executable Python script content.
	"""
	# For now, not everythin can be controlled by option flags.
	tacsIp = cm.get("tacs.ip")
	tacsPort = cm.get("tacs.port")
	ilPort = cm.get("interface.il.port")
	ilIp = cm.get("interface.il.ip")
	maxLogPayloadSize = cm.get("testerman.te.log.max_payload_size")
	
	codecPaths = cm.get("testerman.te.codec_paths")
	probePaths = cm.get("testerman.te.probe_paths")
	
	metadata = getMetadata(ats)
	
	getLogger().info("%s: using language API %s" % (name, metadata.api))
	if metadata.api:
		adapterModuleName = cm.get("testerman.te.python.module.api.%s" % metadata.api)
		if not adapterModuleName:
			raise Exception("Unsupported language API '%s'" % metadata.api)
	else:
		adapterModuleName = cm.get("testerman.te.python.ttcn3module")

	getLogger().info("%s: language API %s - selected adapter module: %s" % (name, metadata.api, adapterModuleName))
	
	# Open the template.
	templateFilename =  "%s/%s" % (cm.get_transient('ts.server_root'), TE_TEMPLATE_NAME)
	try:
		f = open(templateFilename, 'r')
		template = f.read()
		f.close()
	except:
		raise Exception("Unable to build Test Executable: Test Executable template %s not found" % templateFilename)

	# Continue with variable substitution	
	def substituteVariables(s, values):
		"""
		Replaces ${name} with values[name] in s.
		If name is not found, the token is left unchanged.
		"""
		def _subst(match, local_vars = None):
			name = match.group(1)
			if name.endswith('_repr'):
				return repr(values.get(name[:-5], '${%s}' % name))
			else:
				return values.get(name, '${%s}' % name)
		return re.sub(r'\$\{([a-zA-Z_0-9-]+)\}', _subst, s)

	now = time.time()
	variables = dict(
		il_ip = ilIp, il_port = ilPort, 
		tacs_ip = tacsIp, tacs_port = tacsPort,
    max_log_payload_size = maxLogPayloadSize, 
		probe_paths = probePaths, codec_paths = codecPaths,
		adapter_module_name = adapterModuleName, 
		metadata = metadata.toDict(),
		source_ats = smartReindent(ats),
		ats_id = name,
		ts_version = Versions.TESTERMAN_SERVER_VERSION,
		ts_name = cm.get('ts.name'),
		gen_timestamp = now,
		gen_time = time.strftime('%Y%m%d %H:%M:%S UTC', time.gmtime(now)),
		)
	try:
		te = substituteVariables(template, variables)
	except Exception, e:
		getLogger().error("Unable to substitute variables in TE: %s" % str(e))
		raise e
	
	return te
	
def createCommandLine(jobId, teFilename, logFilename, inputSessionFilename, outputSessionFilename, modulePaths, selectedGroups = None):
	"""
	@rtype: a dict { 'executable': string, 'env': dict[string] of strings, 'args': list of strings }
	@returns: the info needed to an execve or the like to execute the TE.
	"""
	ret = {}

	# Add the various flags for a server-controlled execution
	cmdOptions = map(str, [ 
		'--server-controlled', 
		'--job-id', jobId, 
		'--remote-log-filename', logFilename, 
		'--input-session-filename', inputSessionFilename, 
		'--output-session-filename', outputSessionFilename,
		'--tacs-ip', cm.get("tacs.ip"),
		'--tacs-port', cm.get("tacs.port"),
		'--il-ip', cm.get("interface.il.ip"),
		'--il-port', cm.get("interface.il.port"),
		])

	if selectedGroups is not None:
		cmdOptions += [ '--groups', ','.join(selectedGroups) ]

	# Interpreter
	pythonInterpreter = cm.get("testerman.te.python.interpreter")
	ret['executable'] = pythonInterpreter

	#	Env
	# User modules are in the module paths, shared "administrative" modules are in server_root/modules
	pythonPath = '%(root)s:%(root)s/modules:%(modulepaths)s' % dict(
		root = cm.get_transient("ts.server_root"),
		modulepaths = ':'.join(modulePaths))
	libraryPath = '%(root)s:$LD_LIBRARY_PATH' % dict(root = cm.get_transient("ts.server_root"))
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
	
def getDefaultSession(script):
	"""
	Extracts the default parameters & values from an ats.
	
	@type  script: string (utf-8)
	@param script: the ats/campaign code, should includes metadata
	
	@rtype: a dict[unicode] of dict(type: string, default: unicode)
	@returns: the default session dictionary (parameter_name: default_value)
	"""
	xmlMetadata = JobTools.extractMetadata(script, '#')
	if xmlMetadata:
		m = JobTools.parseMetadata(xmlMetadata)
		if m:
			return m.getDefaultSessionDict()
	return None

def getMetadata(script):
	"""
	Extracts the metadata from a script and returns it as a structured object.
	"""
	xmlMetadata = JobTools.extractMetadata(script, '#')
	if xmlMetadata:
		return JobTools.parseMetadata(xmlMetadata)

def createDependency(dependencyContent, adapterModuleName = None):
	"""
	From a dependency content, modify it so that it can be
	used by the TE.
	
	In particular, adds the import TestermanTTCN3 adapter lib,
	so that the user does not need to take care of it.
	
	@type dependencyContent: utf-8 string
	@param dependencyContent: the raw, untouched dependency as retrieved from the VFS
	
	@rtype: utf-8 string
	@returns: the modified dependency content, ready to be dumped and used by the TE
	"""
	if adapterModuleName is None:
		adapterModuleName = cm.get("testerman.te.python.ttcn3module")

	ret = ''
	ret += """# -*- coding: utf-8 -*-
from %s import *
""" % adapterModuleName
	ret += dependencyContent
	return ret
