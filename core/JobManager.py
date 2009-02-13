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
import signal
import sys
import threading
import time


################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.JobManager')

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
	Jobs are organized in trees, based on their _id and _parentId (int).
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
	STATE_INITIALIZING = "initializing"
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

	##
	# To reimplement in your own subclasses
	##
	_type = "undefined"

	def __init__(self, name):
		"""
		@type  name: string
		@param name: a friendly name for this job
		"""
		#: id is int
		self._id = getNewId()
		#: default parent: 'root' (id 0)
		self._parentId = 0
		#: Children Job instances are referenced here, too
		self._children = []
		self._name = name
		self._state = self.STATE_INITIALIZING
		self._scheduledStartTime = time.time() # By default, immediate execution
		#: the initial, input session variables.
		#: passed as actual input session to execute() by the scheduler,
		#: overriden by previous output sessions in case of campaign execution.
		self._scheduledSession = {}
		
		self._startTime = None
		self._stopTime = None
		
		#: the final job result status (int, 0 = OK)
		self._result = None
		#: the output, updated session variables after a complete execution
		self._outputSession = {}
		
		#: the associated log filename with this job (within the docroot - not an absolute path)
		self._logFilename = None
		
		self._username = None
		
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
	
	def getName(self):
		return self._name
	
	def setResult(self, result):
		self._result = result

	def getResult(self):
		return self._result
	
	def getLogFilename(self):
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
		

		# Dispatch notifications through the Event Manager
		jobDict = self.toDict()
		EventManager.instance().dispatchNotification(createJobEventNotification(self.getUri(), jobDict))
		EventManager.instance().dispatchNotification(createJobEventNotification('system:jobs', jobDict))

	def toDict(self):
		"""
		Returns job info as a dict
		"""
		runningTime = None		
		if self._stopTime:
			runningTime = self._stopTime - self._startTime
	
		ret = { 'id': self._id, 'name': self._name, 
		'start-time': self._startTime, 'stop-time': self._stopTime,
		'running-time': runningTime, 'parent-id': self._parentId,
		'state': self.getState(), 'result': self._result, 'type': self._type,
		'username': self._username, 'scheduled-at': self._scheduledStartTime }
		return ret
	
	def __str__(self):
		return "%s: %s (%s)" % (self._type, self._name, self.getUri())
	
	def getUri(self):
		"""
		Returns the job URI. Format: job:<id>

		@rtype: string
		@returns: the job URI.
		"""
		return "job:%s" % self._id
	
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
		TODO.
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

	def __init__(self, name, ats):
		"""
		@type  name: string
		@type  ats: string (utf-8)
		@param ats: the complete ats file (containing metadata)
		"""
		Job.__init__(self, name)
		# string (as utf-8)
		self._ats = ats
		# The PID of the forked TE executable
		self._tePid = None
	
	def handleSignal(self, sig):
		getLogger().info("%s received signal %s" % (str(self), sig))
		
		state = self.getState()
		try:
			if sig == self.SIGNAL_KILL and state != self.STATE_KILLED and self._tePid:
				# Violent sigkill sent to the TE and all its processes (some probes may implement things that
				# lead to a fork with another sid or process group, hence not receiving their parent's signal)
				self.setState(self.STATE_KILLING)
				for pid in Tools.getChildrenPids(self._tePid):
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

	def run(self, inputSession = {}):
		"""
		Prepares the TE, starts it, and only returns when it's over.
		
		inputSession contains parameters values that overrides default ones.
		The default ones are extracted (during the TE preparation) from the
		metadata embedded within the ATS source.
		
		The TE execution tree is this one:
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
	
		# Build the TE
		# TODO: (maybe): shoud we add a "preparing/compiling" state ?

		getLogger().info("%s: resolving dependencies..." % str(self))
		try:
			# (Dirty) trick: ATSes that are not saved in the repository have no atspath on it.
			# Unfortunately, there is no way to know if the ATS scheduled via Ws was on the
			# repo or was only a local file.
			# By default, we consider the atsPath to be /repository/ + the path indicated in
			# the ATS name. So the name (constructed by the client) should follow some rules 
			# to make it work correctly.
			atsPath = '/%s/%s' % (ConfigManager.get('constants.repository'), '/'.join(self.getName().split('/')[:-1]))
			deps = TEFactory.getDependencyFilenames(self._ats, atsPath)
		except Exception, e:
			getLogger().error("%s: unable to resolve dependencies: %s" % (str(self), str(e)))
			self.setResult(25)
			self.setState(self.STATE_ERROR)
			return self.getResult()
		getLogger().info("%s: resolved deps:\n%s" % (str(self), deps))

		getLogger().info("%s: creating TE..." % str(self))
		te = TEFactory.createTestExecutable(self.getName(), self._ats)
		
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
			getLogger().error("%s: syntax/parse error: %s:\n%s\ncontext:\n%s" % (str(self), str(e), line, context))
			self.setResult(21)
			self.setState(self.STATE_ERROR)
			return self.getResult()
		except Exception, e:
			getLogger().error("%s: unable to check TE: %s" % (str(self), str(e)))
			self.setResult(22)
			self.setState(self.STATE_ERROR)
			return self.getResult()

		getLogger().info("%s: preparing TE files..." % str(self))
		# relative path in $docroot
		baseDocRootDirectory = os.path.normpath("/%s/%s" % (ConfigManager.get("constants.archives"), self.getName()))
		# Corresponding absolute local path
		baseDirectory = os.path.normpath("%s%s" % (ConfigManager.get("testerman.document_root"), baseDocRootDirectory))
		# Base name for execution log and TE package dir
		basename = "%s_%s" % (time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time())), self.getUsername())
		# TE package dir (absolute local path)
		tePackageDirectory = "%s/%s" % (baseDirectory, basename)
		try:
			os.makedirs(tePackageDirectory)
		except:
			pass

		# self._logFilename is relative to the docroot for a retrieval via Ws
		self._logFilename = "%s/%s.log" % (baseDocRootDirectory, basename)
		# whereas logFilename is an absolute local path (execution)
		logFilename = "%s/%s.log" % (baseDirectory, basename)
		# The TE bootstrap is in main_te.py
		teFilename = "%s/main_te.py" % (tePackageDirectory)
		try:
			f = open(teFilename, 'w')
			f.write(te)
			f.close()
		except Exception, e:
			getLogger().error('%s: unable to write TE to "%s": %s' % (str(self), teFilename, str(e)))
			self.setResult(20)
			self.setState(self.STATE_ERROR)
			return self.getResult()
		
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
			getLogger().error('%s: unable to create dependency %s to "%s": %s' % (str(self), filename, targetFilename, str(e)))
			self.setResult(20)
			self.setState(self.STATE_ERROR)
			return self.getResult()

		# Prepare input/output session files
		baseSessionDirectory = ConfigManager.get('testerman.tmp_root')
		try:
			os.makedirs(baseSessionDirectory)
		except:
			pass
		inputSessionFilename = "%s/%s.input.session" % (baseSessionDirectory, basename)
		outputSessionFilename = "%s/%s.output.session"  % (baseSessionDirectory, basename)
		# Create the actual input session:
		# the default session, from metadata, overriden with user input session values.
		# FIXME: should we accept user input parameters that are not defined in default parameters, i.e.
		# in ATS ignature ?
		# default session
		try:
			defaultSession = TEFactory.getDefaultSession(self._ats)
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
		# module paths relative to the TE package dir
		modulePaths = [ atsPath[1:], 'repository' ] # we strip the leading / of the atspath
		# Get the TE command line options
		cmd = TEFactory.createCommandLine(jobId = self.getId(), teFilename = teFilename, logFilename = logFilename, inputSessionFilename = inputSessionFilename, outputSessionFilename = outputSessionFilename, modulePaths = modulePaths)
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
		TODO.
		"""
		if self._logFilename:
			absoluteLogFilename = os.path.normpath("%s%s" % (ConfigManager.get("testerman.document_root"), self._logFilename))
			f = open(absoluteLogFilename, 'r')
			fcntl.flock(f.fileno(), fcntl.LOCK_EX)
			res = '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n%s</ats>' % f.read()
			f.close()
			return res
		else:
			return '<?xml version="1.0" encoding="utf-8" ?><ats></ats>'
	
	
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
	
	def submitJob(self, job):
		"""
		Submit a new job in the queue.
		@rtype: int
		@returns: the submitted job Id
		"""
		self._lock()
		self._jobQueue.append(job)
		self._unlock()
		# Triggers the job state notification
		job.setState(Job.STATE_WAITING)
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

