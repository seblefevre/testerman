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
# Job Manager:
# a job scheduler able to execute scheduling jobs on time.
#
# Jobs may be of different types:
# - AtsJob, the most used job type. Contructs a TE based on a source ATS,
#   then executes it.
# - CampaignJob, a job representing a tree of jobs.
# - PauseJob, a special job for campaign management.
#
##

import ConfigManager
import EventManager
import FileSystemManager
import TestermanMessages as Messages
import TEFactory
import Tools
import Versions

import compiler
import fcntl
import logging
import os
import parser
import re
import shutil
import signal
import sys
import tempfile
import threading
import time


################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.JobManager')

################################################################################
# Exceptions
################################################################################

class PrepareException(Exception):
	"""
	This exception can be raised from Job.prepare() in case of
	an application-level error (i.e. not an Internal error)
	"""
	pass

################################################################################
# The usual tools
################################################################################

_GeneratorBaseId = 0
_GeneratorBaseIdMutex = threading.RLock()

def getNewId():
	"""
	Generates a new unique ID.

	@rtype: int
	@returns: a new unique ID
	"""
	global _GeneratorBaseId
	_GeneratorBaseIdMutex.acquire()
	_GeneratorBaseId += 1
	ret = _GeneratorBaseId
	_GeneratorBaseIdMutex.release()
	return ret

def createJobEventNotification(uri, jobDict):
	notification = Messages.Notification("JOB-EVENT", uri, "Xc", Versions.getXcVersion())
	notification.setApplicationBody(jobDict)
	return notification

################################################################################
# Base Job
################################################################################

class Job(object):
	"""
	Main job base class.
	Jobs are organized in trees, based on _childBranches and _parent (Job instances).
	The tree is a 2-branch tree:
	each job may have a list of job to execute on success (success branch)
	or to execute in case of an error (error branch)
	"""

	# Job-acceptable signals
	SIGNAL_PAUSE = "pause"
	SIGNAL_CANCEL = "cancel"
	SIGNAL_KILL = "kill"
	SIGNAL_RESUME = "resume"
	SIGNAL_ACTION_PERFORMED = "action_performed"
	SIGNALS = [ SIGNAL_KILL, SIGNAL_PAUSE, SIGNAL_RESUME, SIGNAL_CANCEL, SIGNAL_ACTION_PERFORMED ]

	# Job states.
	# Basic state machine: initializing -> waiting -> running -> complete
	STATE_INITIALIZING = "initializing" # (i.e. preparing)
	STATE_WAITING = "waiting"
	STATE_RUNNING = "running"
	STATE_KILLING = "killing"
	STATE_CANCELLING = "cancelling"
	STATE_PAUSED = "paused"
	# Final states (ie indicating the Job is over)
	STATE_COMPLETE = "complete"
	STATE_CANCELLED = "cancelled"
	STATE_KILLED = "killed"
	STATE_ERROR = "error"
	STARTED_STATES = [ STATE_RUNNING, STATE_KILLING, STATE_PAUSED ]
	FINAL_STATES = [ STATE_COMPLETE, STATE_CANCELLED, STATE_KILLED, STATE_ERROR ]
	STATES = [ STATE_INITIALIZING, STATE_WAITING, STATE_RUNNING, STATE_KILLING, STATE_CANCELLING, STATE_PAUSED, STATE_COMPLETE, STATE_CANCELLED, STATE_KILLED, STATE_ERROR ]

	BRANCH_SUCCESS = 0 # actually, this is more a "default" or "normal completion"
	BRANCH_ERROR = 1 # actualy, this is more a "abnormal termination"
	BRANCHES = [ BRANCH_ERROR, BRANCH_SUCCESS ]
	
	##
	# To reimplement in your own subclasses
	##
	_type = "undefined"

	def __init__(self, name):
		"""
		@type  name: string
		@param name: a friendly name for this job
		"""
		# id is int
		self._id = getNewId()
		self._parent = None
		# Children Job instances are referenced here, according to their branch
		self._childBranches = { self.BRANCH_ERROR: [], self.BRANCH_SUCCESS: [] }
		self._name = name
		self._state = self.STATE_INITIALIZING
		self._scheduledStartTime = time.time() # By default, immediate execution
		# the initial, input session variables.
		# passed as actual input session to execute() by the scheduler,
		# overriden by previous output sessions in case of campaign execution.
		self._scheduledSession = {}
		
		self._startTime = None
		self._stopTime = None
		
		# the final job result status (int, 0 = OK)
		self._result = None
		# the output, updated session variables after a complete execution
		self._outputSession = {}
		
		# the associated log filename with this job (within the docroot - not an absolute path)
		self._logFilename = None
		
		self._username = None
		# The docroot path to the source, for server-based execution.
		# client-based source and non-source based jobs set it to None
		# You may see it as a 'working (docroot) directory' for the job.
		self._path = None

		self._mutex = threading.RLock()
	
	def setScheduledStartTime(self, timestamp):
		now = time.time()
		if timestamp < now:
			timestamp = now
		self._scheduledStartTime = timestamp
	
	def getScheduledStartTime(self):
		return self._scheduledStartTime

	def setScheduledSession(self, session):
		self._scheduledSession = session
	
	def getScheduledSession(self):
		return self._scheduledSession

	def getOutputSession(self):
		return self._outputSession
	
	def getUsername(self):
		return self._username
	
	def setUsername(self, username):
		self._username = username
	
	def getId(self):
		return self._id
	
	def getParent(self):
		return self._parent
	
	def getName(self):
		return self._name

	def addChild(self, job, branch):
		"""
		Adds a job as a child to this job, in the success or error branch.
		
		@type  job: a Job instance
		@param job: the job to add as a child
		@type  branch: integer in self.BRANCHES
		@param branch: the child branch
		"""
		self._childBranches[branch].append(job)
		job._parent = self
	
	def setResult(self, result):
		self._result = result

	def getResult(self):
		"""
		Returns the job return code/result.
		Its value is job-type dependent.
		However, the following classification applies:
		0: complete
		1: cancelled
		2: killed
		3: runtime low-level error (process segfault, ...)
		4-9: other low-level errors 
		10-19: reserved
		20-29: preparation errors (not executed)
		30-49: reserved
		50-99: reserved for client-side retcode
		100+: userland set retcode
		
		@rtype: integer
		@returns: the job return code
		"""
		return self._result
	
	def getLogFilename(self):
		"""
		Returns a docroot-path to the job's log filename.
		
		@rtype: string
		@returns: the docroot-path to the job's log filename
		"""
		return self._logFilename

	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def getState(self):
		self._lock()
		ret = self._state
		self._unlock()
		return ret
	
	def isFinished(self):
		return self.getState() in self.FINAL_STATES
	
	def isStarted(self):
		return self.getState() in self.STARTED_STATES

	def setState(self, state):
		"""
		Automatically sends notifications according to the state.
		Also handles start/stop time assignments.
		"""
		self._lock()
		if state == self._state:
			# No change
			self._unlock()
			return
		
		self._state = state
		self._unlock()
		getLogger().info("%s changed state to %s" % (str(self), state))
		
		if state == self.STATE_RUNNING and not self._startTime:
			self._startTime = time.time()
		elif state in self.FINAL_STATES:
			if self._startTime and not self._stopTime:
				self._stopTime = time.time()
				getLogger().info("%s stopped, running time: %f" % (str(self), self._stopTime - self._startTime))
			else:
				# Never started. Keep start/stop and running time to None.
				getLogger().info("%s aborted" % (str(self)))
			self.cleanup()
		
		self.notifyStateChange()

	def notifyStateChange(self):
		"""
		Dispatches JOB-EVENT
		notifications through the Event Manager
		"""
		jobDict = self.toDict()
		EventManager.instance().dispatchNotification(createJobEventNotification(self.getUri(), jobDict))
		EventManager.instance().dispatchNotification(createJobEventNotification('system:jobs', jobDict))

	def toDict(self):
		"""
		Returns the job info as a dict
		"""
		runningTime = None		
		if self._stopTime:
			runningTime = self._stopTime - self._startTime
	
		if self._parent:
			parentId = self._parent._id
		else:
			parentId = 0
	
		ret = { 'id': self._id, 'name': self._name, 
		'start-time': self._startTime, 'stop-time': self._stopTime,
		'running-time': runningTime, 'parent-id': parentId,
		'state': self.getState(), 'result': self._result, 'type': self._type,
		'username': self._username, 'scheduled-at': self._scheduledStartTime,
		'path': self._path }
		return ret
	
	def __str__(self):
		return "%s:%s (%s)" % (self._type, self._name, self.getUri())
	
	def getUri(self):
		"""
		Returns the job URI. Format: job:<id>

		@rtype: string
		@returns: the job URI.
		"""
		return "job:%s" % self._id
	
	def getType(self):
		return self._type
	
	def reschedule(self, at):
		"""
		Reschedule the job.
		Only possible if the job has not started yet.
		
		@type  at: timestamp
		@param at: the new recheduling
		
		@rtype: bool
		@returns: True if the rescheduling was ok, False otherwise
		"""

		self._lock()		
		if self._scheduledStartTime > time.time():
			self.setScheduledStartTime(at)
			self._unlock()
			self.notifyStateChange()
			return True
		else:
			self._unlock()
			return False
		
	##
	# Methods to implement in sub classes
	##	
	def handleSignal(self, sig):
		"""
		Called when a signal is sent to this job.
		The implementation for the default job does nothing.
		
		@type  sig: string (in self.SIGNALS)
		@param sig: the signal sent to this job.
		"""	
		getLogger().warning("%s received signal %s, no handler implemented" % (str(self), sig))

	def prepare(self):
		"""
		Prepares a job for a run.
		Called in state INITIALIZING. At the end, if OK, should be switched to WAITING
		or ERROR in case of a preparation error.
		
		@raises PrepareException: in case of any preparatin error.
		@rtype: None
		"""
		pass
		
	def aboutToRun(self):
		"""
		Called by the scheduler when just about to call run() in a dedicated thread.
		
		Prepares the files that will be used for execution.
		In particular, enables to fill what is needed to provide a getLogFilename().
		"""
		pass
		
	def run(self, inputSession = {}):
		"""
		Called by the scheduler to run the job.
		Will be called in a specific thread, so your execution may take a while if needed.
		Just be sure to be able to stop it when receiving a SIGNAL_KILLED at least.
		
		@type  inputSession: dict of unicode of any object
		@param inputSession: the initial session variables to pass to the job. May be empty (but not None),
		                     overriding the default variable definitions as contained in job's metadata (if any).

		@rtype: integer
		@returns: the job _result
		"""
		self.setState(self.STATE_RUNNING)
		getLogger().warning("%s executed, but no execution handler implemented" % (str(self)))
		self.setState(self.STATE_COMPLETE)

	def getLog(self):
		"""
		Returns the current job's logs. 
		The result should be XML compliant. No prologue is required, however.
		
		@rtype: string (utf-8)
		@returns: the current job's logs, as an XML string. Returns None
		          if no log is available.
		"""		
		return None

	def cleanup(self):
		"""
		Called when the job is complete, regardless of its status.
		"""
		pass

################################################################################
# Job subclass: ATS
################################################################################

class AtsJob(Job):
	"""
	ATS Job.
	When ran, creates a TE from the ATS as a stand-alone Python scripts,
	the executes it through forking.
	
	Job signals are, for most of them, translated to Unix process signals.
	"""
	_type = "ats"

	def __init__(self, name, source, path):
		"""
		@type  name: string
		@type  source: string (utf-8)
		@param source: the complete ats file (containing metadata)
		
		@type  path: string (docroot path, for server-based source, or None (client-based source)
		"""
		Job.__init__(self, name)
		# string (as utf-8)
		self._source = source
		# The PID of the forked TE executable
		self._tePid = None

		self._path = path
		if self._path is None:
			# Fallback method for compatibility with old clients (Ws API < 1.2),
			# for which no path is provided by the client, even for server-based source jobs.
			#
			# So here we try to detect a repository path in its id/label/name:
			# We consider the atsPath to be /repository/ + the path indicated in
			# the ATS name. So the name (constructed by the client) should follow some rules 
			# to make it work correctly.
			self._path = '/%s/%s' % (ConfigManager.get('constants.repository'), '/'.join(self.getName().split('/')[:-1]))
		# Basic normalization
		if not self._path.startswith('/'):
			self._path = '/%s' % self._path
		
		# Some internal variables persisted to 
		# transit from prepare/aboutToRun/Run
		self._tePreparedPackageDirectory = None
		self._baseDocRootDirectory = None
		self._baseName = None
		self._baseDirectory = None
		self._tePackageDirectory = None
	
	def handleSignal(self, sig):
		getLogger().info("%s received signal %s" % (str(self), sig))
		
		state = self.getState()
		try:
			if sig == self.SIGNAL_KILL and state != self.STATE_KILLED and self._tePid:
				# Violent sigkill sent to the TE and all its processes (some probes may implement things that
				# lead to a fork with another sid or process group, hence not receiving their parent's signal)
				self.setState(self.STATE_KILLING)
				for pid in Tools.getChildrenPids(self._tePid):
					getLogger().info("Killing child process %s..." % pid)
					try:
						os.kill(pid, signal.SIGKILL)
					except Exception, e:
						getLogger().error("Unable to kill %d: %s" % (pid, str(e)))

			elif sig == self.SIGNAL_CANCEL and self._tePid:
				if state == self.STATE_PAUSED:
					self.setState(self.STATE_CANCELLING)
					# Need to send a SIGCONT before the SIGINT to take the sig int into account
					os.kill(self._tePid, signal.SIGCONT)
					os.kill(self._tePid, signal.SIGINT)
				elif state == self.STATE_RUNNING:
					self.setState(self.STATE_CANCELLING)
					os.kill(self._tePid, signal.SIGINT)
			elif sig == self.SIGNAL_CANCEL and state == self.STATE_WAITING:
				self.setState(self.STATE_CANCELLED)
				
			elif sig == self.SIGNAL_PAUSE and state == self.STATE_RUNNING and self._tePid:
				os.kill(self._tePid, signal.SIGSTOP)
				self.setState(self.STATE_PAUSED)

			elif sig == self.SIGNAL_RESUME and state == self.STATE_PAUSED and self._tePid:
				os.kill(self._tePid, signal.SIGCONT)
				self.setState(self.STATE_RUNNING)
			
			# action() implementation: the user performed the requested action
			elif sig == self.SIGNAL_ACTION_PERFORMED and state == self.STATE_RUNNING and self._tePid:
				os.kill(self._tePid, signal.SIGUSR1)
			
		except Exception, e:
			getLogger().error("%s: unable to handle signal %s: %s" % (str(self), sig, str(e)))

	def cleanup(self):
		getLogger().info("%s: cleaning up..." % (str(self)))
		# Delete the prepared TE, if any
		if self._tePreparedPackageDirectory:
			try:
				shutil.rmtree(self._tePreparedPackageDirectory, ignore_errors = True)
			except Exception, e:
				getLogger().warning("%s: unable to remove temporary TE package directory '%s': %s" % (str(self), self._tePreparedPackageDirectory, str(e)))

	def prepare(self):
		"""
		Prepare a job for a run
		Called in state INITIALIZING. At the end, if OK, should be switched to WAITING
		or ERROR in case of a preparation error.
		
		For an ATS, this:
		- verifies that the dependencies are found.
		- build the TE and its dependencies into a temporary TE directory tree
		- this temporary TE directory tree will be moved to /archives/ upon run().
		
		This avoids the user change any source code after submitting the job.
		
		@raises Exception: in case of any preparatin error.
		
		@rtype: None
		"""
		
		def handleError(code, desc):
			getLogger().error("%s: %s" % (str(self), desc))
			self.setResult(code)
			self.setState(self.STATE_ERROR)
			raise PrepareException(desc)
		
		# Build the TE

		getLogger().info("%s: resolving dependencies..." % str(self))
		try:
			deps = TEFactory.getDependencyFilenames(self._source, self._path)
		except Exception, e:
			desc = "unable to resolve dependencies: %s" % str(e)
			return handleError(25, desc)

		getLogger().info("%s: resolved deps:\n%s" % (str(self), deps))

		getLogger().info("%s: creating TE..." % str(self))
		te = TEFactory.createTestExecutable(self.getName(), self._source)
		
		# TODO: delegate TE check to the TE factory (so that if e need to use another builder that
		# build something else than a Python script, it contains its own checker)
		getLogger().info("%s: verifying TE..." % str(self))
		try:
			parser.suite(te).compile()
			compiler.parse(te)
		except SyntaxError, e:
			t = te.split('\n')
			line = t[e.lineno]
			context = '\n'.join([ "%s: %s" % (x, t[x]) for x in range(e.lineno-5, e.lineno+5)])
			desc = "syntax/parse error: %s:\n%s\ncontext:\n%s" % (str(e), line, context)
			return handleError(21, desc)
		except Exception, e:
			desc = "unable to check TE: %s" % (str(e))
			return handleError(22, desc)

		getLogger().info("%s: preparing TE files..." % str(self))
		# Now create a TE temporary package directory containing the prepared TE and all its dependencies.
		# Will be moved to archives/ upon run()
		self._tePreparedPackageDirectory = tempfile.mkdtemp()
		tePackageDirectory = self._tePreparedPackageDirectory

		# The TE bootstrap is in main_te.py
		teFilename = "%s/main_te.py" % (tePackageDirectory)
		try:
			f = open(teFilename, 'w')
			f.write(te)
			f.close()
		except Exception, e:
			desc = 'unable to write TE to "%s": %s' % (teFilename, str(e))
			return handleError(20, desc)
		
		# Copy dependencies to the TE base dir
		getLogger().info("%s: preparing dependencies..." % (str(self)))
		try:
			for filename in deps:
				# filename is a docroot-path
				# Target, local, absolute filename for the dep
				targetFilename = '%s/%s' % (tePackageDirectory, filename)

				depContent = FileSystemManager.instance().read(filename)
				# Alter the content (additional includes, etc)
				depContent = TEFactory.createDependency(depContent)

				# Create required directory structure, with __init__.py file, if needed
				currentdir = tePackageDirectory
				for d in filter(lambda x: x, filename.split('/')[:-1]):
					localdir = '%s/%s' % (currentdir, d)
					currentdir = localdir
					try:
						os.mkdir(localdir)
					except: 
						pass
					# Touch a __init__.py file
					getLogger().debug("Creating __init__.py in %s..." % localdir)
					f = open('%s/__init__.py' % localdir, 'w')
					f.close()

				# Now we can dump the module
				f = open(targetFilename, 'w')
				f.write(depContent)
				f.close()
		except Exception, e:
			desc = 'unable unable to create dependency %s to "%s": %s' % (filename, targetFilename, str(e))
			return handleError(20, desc)
		
		# OK, we're ready.
		self.setState(self.STATE_WAITING)

	def aboutToRun(self):
		"""
		Called by the scheduler when just about to call run() in a dedicated thread.
		
		Prepares the files that will be used for execution.
		In particular, enables to fill what is needed to provide a getLogFilename().
		"""
		# Create some paths related to the final TE tree in the docroot

		# docroot-path for all TE packages for this ATS
		self._baseDocRootDirectory = os.path.normpath("/%s/%s" % (ConfigManager.get("constants.archives"), self.getName()))
		# Base name for execution log and TE package dir
		# FIXME: possible name collisions if the same user schedules 2 same ATSes at the same time...
		self._basename = "%s_%s" % (time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time())), self.getUsername())
		# Corresponding absolute local path
		self._baseDirectory = os.path.normpath("%s%s" % (ConfigManager.get("testerman.document_root"), self._baseDocRootDirectory))
		# final TE package dir (absolute local path)
		self._tePackageDirectory = "%s/%s" % (self._baseDirectory, self._basename)
		# self._logFilename is a docroot-path for a retrieval via Ws
		self._logFilename = "%s/%s.log" % (self._baseDocRootDirectory, self._basename)

	def run(self, inputSession = {}):
		"""
		Prepares the TE, Starts a prepared TE, and only returns when it's over.
		
		inputSession contains parameters values that overrides default ones.
		The default ones are extracted (during the TE preparation) from the
		metadata embedded within the ATS source.
		
		The TE execution tree is this one (prepared by a call to self.prepare())
		execution root:
		%(docroot)/%(archives)/%(ats_name)/
		contains:
			%Y%m%d-%H%M%S_%(user).log : the execution logs
			%Y%m%d-%H%M%S_%(user) : directory containing the TE package:
				te_mtc.py : the main TE
				repository/... : the (userland) modules the TE depends on
				This directory is planned to be packaged to be executed on
				any Testerman environment. (it may still evolve until so)
		
		The TE execution is performed from the directory containing the TE package.
		The module search path is set to:
		- first the path of the ATS (for local ATSes, defaulted to 'repository') as a docroot-path,
		- then 'repository'
		- then the Testerman system include paths
		
		@type  inputSession: dict[unicode] of unicode
		@param inputSession: the override session parameters.
		
		@rtype: int
		@returns: the TE return code
		"""
		baseDocRootDirectory = self._baseDocRootDirectory
		baseDirectory = self._baseDirectory
		tePackageDirectory = self._tePackageDirectory
		basename = self._basename

		# Move the prepared, temporary TE folder tree to its final location in archives
		try:
			shutil.move(self._tePreparedPackageDirectory, tePackageDirectory)
			self._tePreparedPackageDirectory = None
		except Exception, e:
			getLogger().error('%s: unable to move prepared TE and its dependencies to their final locations: %s' % (str(self), str(e)))
			self.setResult(24)
			self.setState(self.STATE_ERROR)
			return self.getResult()

		# Prepare input/output session files
		inputSessionFilename = "%s/%s.input.session" % (tePackageDirectory, basename)
		outputSessionFilename = "%s/%s.output.session"  % (tePackageDirectory, basename)
		# Create the actual input session:
		# the default session, from metadata, overriden with user input session values.
		# FIXME: should we accept user input parameters that are not defined in default parameters, i.e.
		# in ATS signature ?
		# default session
		try:
			defaultSession = TEFactory.getDefaultSession(self._source)
			if defaultSession is None:
				getLogger().warning('%s: unable to extract default session from ats. Missing metadata ?' % (str(self)))
				defaultSession = {}
		except Exception, e:
			getLogger().error('%s: unable to extract ATS parameters from metadata: %s' % (str(self), str(e)))
			self.setResult(23)
			self.setState(self.STATE_ERROR)
			return self.getResult()
		
		# The merged input session
		mergedInputSession = {}
		for n, v in defaultSession.items():
			if inputSession.has_key(n):
				mergedInputSession[n] = inputSession[n]
			else:
				mergedInputSession[n] = v
		
		getLogger().info('%s: using merged input session:\n%s' % (str(self), '\n'.join([ '%s = %s (%s)' % (x, y, repr(y)) for x, y in mergedInputSession.items()])))
		
		# Dumps input session to the corresponding file
		try:
			dumpedInputSession = TEFactory.dumpSession(mergedInputSession)
			f = open(inputSessionFilename, 'w')
			f.write(dumpedInputSession)
			f.close()
		except Exception, e:
			getLogger().error("%s: unable to create input session file: %s" % (str(self), str(e)))
			self.setResult(24)
			self.setState(self.STATE_ERROR)
			return self.getResult()
		
		getLogger().info("%s: building TE command line..." % str(self))
		# teLogFilename is an absolute local path
		teLogFilename = "%s/%s.log" % (baseDirectory, basename)
		teFilename = "%s/main_te.py" % (tePackageDirectory)
		# module paths relative to the TE package dir
		modulePaths = [ self._path[1:], 'repository' ] # we strip the leading / of the atspath
		# Get the TE command line options
		cmd = TEFactory.createCommandLine(jobId = self.getId(), teFilename = teFilename, logFilename = teLogFilename, inputSessionFilename = inputSessionFilename, outputSessionFilename = outputSessionFilename, modulePaths = modulePaths)
		executable = cmd['executable']
		args = cmd['args']
		env = cmd['env']
		
		# Show a human readable command line for debug purposes
		cmdLine = '%s %s' % ( ' '.join(['%s=%s' % (x, y) for x, y in env.items()]), ' '.join(args))
		getLogger().info("%s: executing TE using:\n%s\nEnvironment variables:%s" % (str(self), cmdLine, '\n'.join(['%s=%s' % x for x in env.items()])))

		# Fork and run it
		try:
			pid = os.fork()
			if pid:
				# Wait for the child to finish
				self._tePid = pid
				self.setState(self.STATE_RUNNING)
				# actual retcode (< 256), killing signal, if any
				(retcode, sig) = divmod(os.waitpid(pid, 0)[1], 256)
				self._tePid = None
			else:
				# forked child: exec with the TE once moved to the correct dir
				os.chdir(tePackageDirectory)
				os.execve(executable, args, env)
				# Done with the child.
		except Exception, e:
			getLogger().error("%s: unable to execute TE: %s" % (str(self), str(e)))
			self._tePid = None
			self.setResult(23)
			self.setState(self.STATE_ERROR)
			# Clean input session filename
			try:
				os.unlink(inputSessionFilename)
			except Exception, e:
				getLogger().warning("%s: unable to delete input session file: %s" % (str(self), str(e)))
			return self.getResult()

		# Normal continuation, once the child has returned.
		if sig > 0:
			getLogger().info("%s: TE terminated with signal %d" % (str(self), sig))
			# In case of a kill, make sure we never return a "OK" retcode
			# For other signals, the retcode is already controlled by the TE that ensures specific retcodes.
			if sig == signal.SIGKILL:
				self.setResult(2)
				self.setState(self.STATE_KILLED)
			else:
				# Other signals (segfault, ...)
				self.setResult(3)
				self.setState(self.STATE_ERROR)
		else:
			getLogger().info("%s: TE returned, retcode %d" % (str(self), retcode))
			self.setResult(retcode)
			# Maps standard retcode to states
			if retcode == 0: # RETURN_CODE_OK
				self.setState(self.STATE_COMPLETE)
			elif retcode == 1: # RETURN_CODE_CANCELLED
				self.setState(self.STATE_CANCELLED)
			else: # Other errors
				self.setState(self.STATE_ERROR)
		
		# Read output session
		try:
			f = open(outputSessionFilename, 'r')
			self._outputSession = TEFactory.loadSession(f.read())
			f.close()
		except Exception, e:
			getLogger().warning("%s: unable to read output session file: %s" % (str(self), str(e)))

		# Clean input & output session filename
		try:
			os.unlink(inputSessionFilename)
		except Exception, e:
			getLogger().warning("%s: unable to delete input session file: %s" % (str(self), str(e)))
		try:
			os.unlink(outputSessionFilename)
		except Exception, e:
			getLogger().warning("%s: unable to delete output session file: %s" % (str(self), str(e)))
		
		return self.getResult()

	def getLog(self):
		"""
		Returns the current known log.
		"""
		if self._logFilename:
			# Why not use the FileSystemManager acccess instead of an absolute, local path ? 
			# Because of the file lock only ?
			absoluteLogFilename = os.path.normpath("%s%s" % (ConfigManager.get("testerman.document_root"), self._logFilename))
			f = open(absoluteLogFilename, 'r')
			fcntl.flock(f.fileno(), fcntl.LOCK_EX)
			res = '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n%s</ats>' % f.read()
			f.close()
			return res
		else:
			return '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n</ats>'
	

################################################################################
# Job subclass: Campaign
################################################################################

class CampaignJob(Job):
	"""
	Campaign Job.
	
	Job signals are, for most of them, forwarded to the current child job.
	
	Campaign state machine:
	to discuss. Should we map the campaign state with the current child job's ?
	"""
	_type = "campaign"

	def __init__(self, name, source, path):
		"""
		@type  name: string
		@type  source: string (utf-8)
		@param source: the complete campaign source file (containing metadata)
		"""
		Job.__init__(self, name)
		# string (as utf-8)
		self._source = source
		# The PID of the forked TE executable
		self._tePid = None

		self._path = path
		if self._path is None:
			# Fallback method for compatibility with old clients (Ws API < 1.2),
			# for which no path is provided by the client, even for server-based source jobs.
			#
			# So here we try to detect a repository path in its id/label/name:
			# We consider the atsPath to be /repository/ + the path indicated in
			# the ATS name. So the name (constructed by the client) should follow some rules 
			# to make it work correctly.
			self._path = '/%s/%s' % (ConfigManager.get('constants.repository'), '/'.join(self.getName().split('/')[:-1]))
		# Basic normalization
		if not self._path.startswith('/'):
			self._path = '/%s' % self._path
		
		self._absoluteLogFilename = None
	
	def handleSignal(self, sig):
		"""
		So, what should we do ?
		"""
		getLogger().info("%s received signal %s" % (str(self), sig))
		
		state = self.getState()
		try:
			if sig == self.SIGNAL_CANCEL:
				if state == self.STATE_WAITING:
					self.setState(self.STATE_CANCELLED)
				else:
					self.setState(self.STATE_CANCELLING)
			else:
				getLogger().warning("%s: received unhandled signal %s" % (str(self), sig))
			
		except Exception, e:
			getLogger().error("%s: unable to handle signal %s: %s" % (str(self), sig, str(e)))

	def prepare(self):
		"""
		Prepares the campaign, verifying the availability of each included job.

		During the campaign preparation, we just check that all child job sources
		are present within the directory.
		WARNING: we do not snapshot all ATSes and campaigns nor prepare them prior to 
		executing the campaign. 
		In particular, if an child ATS is changed after the campaign has been started
		or scheduled, before the child ATS is started, the updated ATS will be taken
		into account.
		"""
		# First step, parse
		getLogger().info("%s: parsing..." % str(self))
		try:
			self._parse()
		except Exception, e:
			desc = "%s: unable to prepare the campaign: %s" % (str(self), str(e))
			getLogger().error(desc)
			self.setResult(25) # Consider a dependency error ?
			self.setState(self.STATE_ERROR)
			raise PrepareException(e)
		
		getLogger().info("%s: parsed OK" % str(self))
		self.setState(self.STATE_WAITING)

	def aboutToRun(self):
		"""
		Prepares the files that will be used for execution.
		In particular, enables to fill what is needed to provide a getLogFilename().
		"""
		# docroot-path for all files related to this job
		baseDocRootDirectory = os.path.normpath("/%s/%s" % (ConfigManager.get("constants.archives"), self.getName()))
		# Corresponding absolute local path
		baseDirectory = os.path.normpath("%s%s" % (ConfigManager.get("testerman.document_root"), baseDocRootDirectory))
		# FIXME: possible name collisions if the same user schedules 2 same ATSes at the same time...
		basename = "%s_%s" % (time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time())), self.getUsername())
		self._logFilename = "%s/%s.log" % (baseDocRootDirectory, basename)
		self._absoluteLogFilename = "%s/%s.log" % (baseDirectory, basename)

		try:
			os.mkdir(baseDirectory)
		except: 
			pass
		
	def run(self, inputSession = {}):
		"""
		Prepares the campaign, starts it, and only returns when it's over.
		
		inputSession contains parameters values that overrides default ones.
		The default ones are extracted (during the campaign preparation) from the
		metadata embedded within the campaign source.
		
		A campaign is prepared/expanded to a collection of child jobs,
		that can be ATSes or campaigns.
		
		A campaign job has a dedicated execution directory:
		%(docroot)/%(archives)/%(campaign_name)/
		contains:
			%Y%m%d-%H%M%S_%(user).log : the main execution log
		
		Each ATS job created from this campaigns are prepared and executed as if they
		were executed separately.
		
		A campaign always schedules a child job for an immediate execution, i.e. no
		child job is prepared/scheduled in advance.
		
		@type  inputSession: dict[unicode] of unicode
		@param inputSession: the override session parameters.
		
		@rtype: int
		@returns: the campaign return code
		"""
		
		# Now, execute the child jobs
		self._logEvent('event', 'campaign-started', {'id': self._name})
		self.setState(self.STATE_RUNNING)
		self._run(callingJob = self, inputSession = inputSession)
		if self.getState() == self.STATE_RUNNING:
			self.setResult(0) # a campaign always returns OK for now. Unless cancelled, etc ?
			self.setState(self.STATE_COMPLETE)
		elif self.getState() == self.STATE_CANCELLING:
			self.setResult(1)
			self.setState(self.STATE_CANCELLED)
		self._logEvent('event', 'campaign-stopped', {'id': self._name, 'result': self.getResult()})
		
		return self.getResult()

	def toXml(self, element, attributes, value = ''):
		return u'<%s %s>%s</%s>' % (element, " ".join(map(lambda e: '%s="%s"' % (e[0], str(e[1])), attributes.items())), value, element)

	def _logEvent(self, level, event, attributes, logClass = 'event', value = ''):
		"""
		Sends a log event notification through Il.
		Will be dumped by Il server.
		"""
		attributes['class'] = logClass
		attributes['timestamp'] = time.time()
		xml = self.toXml(event, attributes, value)
		
		notification = Messages.Notification("LOG", self.getUri(), "Il", "1.0")
		if self._absoluteLogFilename:
			notification.setHeader("Log-Filename", self._absoluteLogFilename)
		notification.setHeader("Log-Class", level)
		notification.setHeader("Log-Timestamp", time.time())
		notification.setHeader("Content-Encoding", "utf-8")
		notification.setHeader("Content-Type", "application/xml")
		notification.setBody(xml.encode('utf-8'))
		EventManager.instance().handleIlNotification(notification)

	def _run(self, callingJob, inputSession, branch = Job.BRANCH_SUCCESS):
		"""
		Recursively called.
		"""
		if self.getState() != self.STATE_RUNNING:
			# We stop our loop/recursion (killed, cancelled, etc).
			return

		# Now, the child jobs according to the branch
		for job in callingJob._childBranches[branch]:
			instance().registerJob(job)

			getLogger().info("%s: preparing child job %s, invoked by %s, on branch %s" % (str(self), str(job), str(callingJob), branch))
			prepared = False
			try:
				job.prepare()
				prepared = True
			except Exception:
				prepared = False

			if prepared:
				getLogger().info("%s: starting child job %s, invoked by %s, on branch %s" % (str(self), str(job), str(callingJob), branch))
				# Prepare a new thread, execute the job
				job.aboutToRun()
				self._logEvent('core', '%s-started' % job.getType(), {'id': job.getName(), 'link': job.getLogFilename()}, logClass = 'core')
				jobThread = threading.Thread(target = lambda: job.run(inputSession))
				jobThread.start()
				# Now wait for the job to complete.
				jobThread.join()
				ret = job.getResult()
				self._logEvent('core', '%s-stopped' % job.getType(), {'id': job.getName(), 'link': job.getLogFilename(), 'result': ret}, logClass = 'core')
				getLogger().info("%s: started child job %s, invoked by %s, on branch %s returned %s" % (str(self), str(job), str(callingJob), branch, ret))
			else:
				ret = job.getResult()

			if ret == 0:
				nextBranch = self.BRANCH_SUCCESS
				nextInputSession = job.getOutputSession()
			else:
				nextBranch = self.BRANCH_ERROR
				# In case of an error, the output session may be empty. If empty, we use the initial session.
				nextInputSession = job.getOutputSession()
				if not nextInputSession:
					nextInputSession = inputSession

			self._run(job, nextInputSession, nextBranch)

	def _parse(self):
		"""
		Parses the source file, check that all referenced sources exist.
		
		A campaign format is a tree based on indentation:
		
		job
			job
			job
				job
		job
		
		The indentation is defined by the number of indent characters.
		Validindent characters are \t and ' '.
		
		a job line is formatted as:
		[* ]<type> <path>
		where:
		<type> is a keyword in 'ats', 'campaign' (for now)
		<path> is a relative (not starting with a /) or 
		       absolute path (/-starting) within the repository.
		the optional * indicates that the job should be executed if its parent
		returns a non-0 result. ('on error' branch).
		
		Comments are indicated with a #.
		"""
		getLogger().info("%s: parsing campaign file" % str(self))

		# The path of the campaign within the docroot.
		path = self._path
		
		indent = 0
		currentParent = self
		lastCreatedJob = None
		lc = 0
		for line in self._source.splitlines():
			lc += 1
			# Remove comments
			line = line.split('#', 1)[0].rstrip()
			if not line:
				continue # empty line
			m = re.match(r'(?P<indent>\s*)((?P<branch>\*)\s*)?(?P<type>\w+)\s+(?P<filename>.*)', line)
			if not m:
				raise Exception('Parse error at line %s: invalid line format' % lc)
			
			type_ = m.group('type')
			filename = m.group('filename')
			branch = m.group('branch') # may be none
			indentDiff = len(m.group('indent')) - indent
			indent = indent + indentDiff
			
			# Filename creation within the docroot
			if filename.startswith('/'):
				# absolute path within the *repository*
				filename = '/%s%s' % (ConfigManager.get('constants.repository'), filename)
			else:
				# just add the local campaign path
				filename = '%s/%s' % (path, filename)

			# Branch validation
			if branch in [ '*', 'on_error' ]: # * is an alias for the error branch
				branch = self.BRANCH_ERROR
			elif not branch or branch in ['on_success']:
				branch =  self.BRANCH_SUCCESS # the default branch
			else:
				raise Exception('Error at line %s: invalid branch (%s)' % (lc, branch))

			# Type validation
			if not type_ in [ 'ats', 'campaign' ]:
				raise Exception('Error at line %s: invalid job type (%s)' % (lc, type_))

			if indentDiff > 1:
				raise Exception('Parse error at line %s: invalid indentation (too deep)' % lc)
			# Get the current parent
			elif indentDiff == 1:
				# the current parent is the previous created job
				if not lastCreatedJob:
					raise Exception('Parse error at line %s: invalid indentation (invalid initial indentation)' % lc)
				else:
					currentParent = lastCreatedJob
			elif indentDiff == 0:
				# the current parent remains the parent
				pass
			else:
				# negative indentation. 
				for _ in range(abs(indentDiff)):
					currentParent = currentParent.getParent()
			
			# Now we can create our job.
			getLogger().debug('%s: creating child job based on file docroot:%s' % (str(self), filename))
			source = FileSystemManager.instance().read(filename)
			name = filename[len('/repository/'):] # TODO: clean this mess up. Not clean at all.
			jobpath = '/'.join(filename.split('/')[:-1])
			if source is None:
				raise Exception('File %s is not in the repository.' % name)
			if type_ == 'ats':
				job = AtsJob(name = name, source = source, path = jobpath)
			else: # campaign
				job = CampaignJob(name = name, source = source, path = jobpath)
			job.setUsername(self.getUsername())
			currentParent.addChild(job, branch)
			getLogger().info('%s: child job %s has been created, branch %s' % (str(self), str(job), branch))
			lastCreatedJob = job

		# OK, we're done with parsing and job preparation.
		getLogger().info('%s: fully prepared, all children found and created.' % str(self))

	def getLog(self):
		"""
		Returns the current known log.
		"""
		if self._logFilename:
			f = open(self._absoluteLogFilename, 'r')
			fcntl.flock(f.fileno(), fcntl.LOCK_EX)
			# FIXME: we generate a 'ats' root element. Is that correct ?
			res = '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n%s</ats>' % f.read()
			f.close()
			return res
		else:
			return '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n</ats>'

################################################################################
# The Scheduler Thread
################################################################################

class Scheduler(threading.Thread):
	"""
	A Background thread that regularly checks the main job queue for job to start (job in STATE_WAITING).
	
	We should have a dedicated heap for that.
	However, since we won't have thousands of waiting jobs, a first straightforward implementation
	may be enough.
	"""
	def __init__(self, manager):	
		threading.Thread.__init__(self)
		self._manager = manager
		self._stopEvent = threading.Event()
		self._notifyEvent = threading.Event()
	
	def run(self):
		getLogger().info("Job scheduler started.")
		delay = float(ConfigManager.get('ts.jobscheduler.interval', 1000)) / 1000.0
		while not self._stopEvent.isSet():
			self._notifyEvent.wait(delay)
			self._notifyEvent.clear()
			self.check()
		getLogger().info("Job scheduler stopped.")
	
	def check(self):
		jobs = self._manager.getWaitingJobs()
		for job in jobs:
			if job.getScheduledStartTime() < time.time():
				getLogger().info("Scheduler: starting new job: %s" % str(job))
				# Prepare a new thread, execute the job
				job.aboutToRun()
				jobThread = threading.Thread(target = lambda: job.run(job.getScheduledSession()))
				jobThread.start()

	def stop(self):
		self._stopEvent.set()
		self.join()
	
	def notify(self):
		self._notifyEvent.set()


class JobManager:
	"""
	A Main entry point to the job manager module.
	"""
	def __init__(self):
		self._mutex = threading.RLock()
		self._jobQueue = []
		self._scheduler = Scheduler(self)
	
	def start(self):
		self._scheduler.start()
	
	def stop(self):
		self._scheduler.stop()
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def registerJob(self, job):
		"""
		Register a new job in the queue.
		Do not update its state or do anything with it.
		Typically used by a campaign to register the child jobs it manages.
		"""
		self._lock()
		self._jobQueue.append(job)
		self._unlock()
	
	def submitJob(self, job):
		"""
		Submits a new job in the queue.
		@rtype: int
		@returns: the submitted job Id
		"""
		self.registerJob(job)
		# Initialize the job (i.e. prepare it)
		# Raises exceptions in case of an error
		try:
			job.prepare()
		except Exception, e:
			getLogger().warning("JobManager: new job submitted: %s, scheduled to start on %s, unable to initialize" % (str(job), time.strftime("%Y%m%d, at %H:%H:%S", time.localtime(job.getScheduledStartTime()))))
			# Forward to the caller
			raise e

		getLogger().info("JobManager: new job submitted: %s, scheduled to start on %s" % (str(job), time.strftime("%Y%m%d, at %H:%H:%S", time.localtime(job.getScheduledStartTime()))))
		# Wake up the scheduler. Maybe an instant run is here.
		self._scheduler.notify()
		return job.getId()
	
	def getWaitingJobs(self):
		"""
		Only extracts the waiting jobs subset from the queue.
		Useful for the scheduler.

		@rtype: list of Job instances
		@returns: the list of waiting jobs.
		"""
		self._lock()
		ret = filter(lambda x: x.getState() == Job.STATE_WAITING, self._jobQueue)
		self._unlock()
		return ret
	
	def getJobInfo(self, id_ = None):
		"""
		@type  id_: integer, or None
		@param id_: the jobId for which we request some info, or None if we want all.
		
		@rtype: list of dict
		@returns: a list of job dict representations. May be empty if the id_ was not found.
		"""
		ret = []
		self._lock()
		for job in self._jobQueue:
			if id_ is None or job.getId() == id_:
				ret.append(job.toDict())
		self._unlock()
		return ret
	
	def killAll(self):
		"""
		Kills all existing jobs.
		"""
		self._lock()
		for job in self._jobQueue:
			try:
				job.handleSignal(Job.SIGNAL_KILL)
			except:
				pass
		self._unlock()

	def getJob(self, id_):
		"""
		Internal only ?
		Gets a job based on its id.
		"""
		j = None
		self._lock()
		for job in self._jobQueue:
			if job.getId() == id_:
				j = job
				break
		self._unlock()
		return j
	
	def sendSignal(self, id_, signal):
		job = self.getJob(id_)
		if job:
			job.handleSignal(signal)
			return True
		else:
			return False

	def getJobLogFilename(self, id_):
		job = self.getJob(id_)		
		if job:
			return job.getLogFilename()
		else:
			return None
	
	def getJobLog(self, id_):
		job = self.getJob(id_)
		if job:
			return job.getLog()
		else:
			return None

	def rescheduleJob(self, id_, at):
		job = self.getJob(id_)
		if job:
			return job.reschedule(at)

TheJobManager = None

def instance():
	global TheJobManager
	if TheJobManager is None:
		TheJobManager = JobManager()
	return TheJobManager

def initialize():
	instance().start()

def finalize():
	getLogger().info("Killing all jobs...")
	instance().killAll()
	instance().stop()

