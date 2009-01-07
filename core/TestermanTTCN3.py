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
# Testerman default TTCN-3 Adapter.
# The main module that provides ATS with entry points to
# TTCN-3 logic.
#
##

import TestermanSA
import TestermanPA
import TestermanCD
from TestermanTCI import *

import time
import re
import threading


################################################################################
# Some general functions
# (non-TTCN3-related)
################################################################################

VERDICT_PASS = 'pass'
VERDICT_FAIL = 'fail'
VERDICT_ERROR = 'error'
VERDICT_INCONC = 'inconc'
VERDICT_NONE = 'none'

pass_ = VERDICT_PASS
fail_ = VERDICT_FAIL
error_ = VERDICT_ERROR
inconc_ = VERDICT_INCONC
none_ = VERDICT_NONE


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
	
# Contexts are general containers similar to TLS (Thread Local Storages).
# We don't use Python 2.4 TLS because they may evolve to something else than
# thread-based once node-based PTC execution is available.
_ContextMap = {} # a list of TLS, per thread ID
_ContextMapMutex = threading.RLock()

class TestermanContext:
	"""
	A Context store several info about the associated timers,
	test component, test case it belongs.
	Well, this is the local test component context at any time.
	
	TODO: this context may be distributed on any TestermanNode.
	"""
	def __init__(self):
		# Current timers
		self.timers = []
		# Current Test Component (a PTC or the MTC)
		self._tc = None
		# Current Test Case
		self._testcase = None
		# Current matched values for value()
		self._values = {}
	
	def getValues(self):
		return self._values
	
	def getValue(self, name):
		return self._values.get(name, None)
	
	def setValue(self, name, value):
		self._values[name] = value
	
	def getTc(self):
		return self._tc
	
	def setTc(self, tc):
		self._tc = tc
	
	def getTestCase(self):
		return self._testcase
	
	def setTestCase(self, testcase):
		self._testcase = testcase
	
def getLocalContext():
	"""
	Returns the current TC context.
	Creates a new one if it does not exist.
	Currently, "current" means "in the same thread", since
	we have one thread per TC. 
	Once TC are distributed over multiple TE nodes, the current
	context identification will be differed.
	
	@rtype: TestermanContext object
	@returns: the current TC context.
	"""
	global _ContextMap, _ContextMapMutex
	_ContextMapMutex.acquire()
	if _ContextMap.has_key(threading.currentThread()):
		context = _ContextMap[threading.currentThread()]
	else:
		context = TestermanContext()
		_ContextMap[threading.currentThread()] = context
	_ContextMapMutex.release()
	return context

def clearContextAndStopAllTimers():
	"""
	Clears the current contexts out of the memory.
	Also stops all existing timers in these contexts, if any.
	"""
	_ContextMapMutex.acquire()
	for (thr, context) in _ContextMap.items():
		for timer in context.timers:
			timer.stop()
	_ContextMap.clear()
	_ContextMapMutex.release()


################################################################################
# Some tools: StateManager (to implement alt-based state machines)
################################################################################

class StateManager:
	"""
	This object is a convenience object to:
	- set a value from a lambda (within a alt()) that can be retrieve
	from outside
	- as a side effect, enables to build state machines using alt() only
	(or almost).
	
	Ex:
	s = StateManager('idle')
	
	alt([
		[ lambda: s.get() == 'idle':
			control.RECEIVE(templateNewCall()),
			lambda: s.set('ringing'),
		],
		...
	])
	"""
	def __init__(self, state = None):
		self._state = state
	def get(self):
		return self._state
	def set(self, state):
		self._state = state


################################################################################
# Exceptions
################################################################################

# Implementation exception
class TestermanException(Exception): pass

# Control-oriented exceptions
class TestermanKillException(Exception): pass

class TestermanStopException(Exception):
	def __init__(self, retcode = None):
		"""
		Retcode is used as a return code for the ATS.
		"""
		self.retcode = retcode

class TestermanCancelException(Exception): pass

# Exception for TTCN-3 related problems
class TestermanTtcn3Exception(Exception): pass


################################################################################
# TTCN-3 Timers
################################################################################

class Timer:
	"""
	Almost straightforward implementation of TTCN-3 Timers.
	Same API.
	
	The actual timer low-level implementation lies in TestermanPA.
	"""
	def __init__(self, duration, name = None):
		self._name = name
		self._timerId = None
		self._defaultDuration = duration
		self._TIMEOUT_EVENT = { 'event': 'timeout', 'timer': self }
		if self._name is None:
			self._name = "timer_%d" % getNewId()
		
		self.TIMEOUT = (_getSystemQueue(), self._TIMEOUT_EVENT, None)
		getLocalContext().timers.append(self)
		self._tc = getLocalContext().getTc()

		logInternal("%s created" % str(self))
	
	def __str__(self):
		return self._name
	
	def _onTimeout(self):
		logTimerExpiry(tc = str(self._tc), id_ = str(self))
		# we post a message into the system component special port
		_postSystemEvent(self._TIMEOUT_EVENT)

	# TTCN-3 compliant interface

	def start(self, duration = None):
		"""
		Starts the timer, with its default duration is not set here.
		@type  duration: float, or None
		@param duration: the timer duration, in s (if provided)
		"""
		if self._timerId:
			self.stop()
			
		if duration is None:
			duration = self._defaultDuration
		
		if duration is None:
			raise TestermanTtcn3Exception("No duration set for this timer")

		self._timerId = getNewId()
		_registerTimer(self._timerId, self)
		TestermanPA.triStartTimer(self._timerId, duration)

		logTimerStarted(tc = str(self._tc), id_ = str(self), duration = duration)

	def stop(self):
		"""
		Stops the timer. Does nothing if it was not running.
		"""
		if self._timerId:
			TestermanPA.triStopTimer(self._timerId)
			_unregisterTimer(self._timerId)
			self._timerId = None
			logTimerStopped(tc = str(self._tc), id_ = str(self), runningTime = 0.0)

	def running(self):
		"""
		@rtype: bool
		@returns: True if the timer is running, False otherwise
		"""
		return TestermanPA.triTimerRunning(self._timerId)

	def timeout(self):
		"""
		Only returns when the timer expires.
		Immediately returns if the timer is not started.
		"""
		if self._timerId:
			alt([[self.TIMEOUT]])
		else:
			return

	def read(self):
		"""
		Returns the number of s (decimal) since last start, and 0 if not started.
		@rtype: float
		@returns: running duration
		"""
		# Efficient way:
		#if self._timerId:
		#	return (time.time() - self.startTime)
		#return 0
		# TTCN3 compliant way
		return TestermanPA.triReadTimer(self._timerId)
	
# Internal Timer management and TRI associations
_TimersLock = threading.RLock()
_Timers = {}

def _registerTimer(timerId, timer):
	_TimersLock.acquire()
	_Timers[timerId] = timer
	_TimersLock.release()

def _unregisterTimer(timerId):
	_TimersLock.acquire()
	if _Timers.has_key(timerId):
		del _Timers[timerId]
	_TimersLock.release()

def triTimeout(timerId):
	timer = None
	_TimersLock.acquire()
	if _Timers.has_key(timerId):
		timer = _Timers[timerId]
		del _Timers[timerId]	
	_TimersLock.release()
	if timer:
		timer._onTimeout()


################################################################################
# TTCN-3 Test Component (TC)
################################################################################

class TestComponent:
	"""
	Implements most of the TestComponent TTCN-3 interface.
	"""
	# TC states
	STATE_INACTIVE = 0
	STATE_RUNNING = 1
	STATE_KILLED = 2
	STATE_STOPPED = 3
	
	def __init__(self, name = None, alive = False):
		"""
		Creates a new Test Component (TC), that is theorically
		suitable for MTC or PTC.
		
		@type  name: string, or None
		@param name: the name of the component.
		@type  alive: bool
		@param alive: TTCN-3 alive parameter.
		"""
		self._name = name
		if not self._name:
			self._name = "tc_%d" % getNewId()

		self._mutex = threading.RLock()

		# exposed Ports, indexed by their name (string)
		self._ports = {}

		# The parent testcase (also present in current contex(), so - useful ?)
		self._testcase = None

		# Taints this TC as MTC or not
		self._mtc = False

		# (P)TC state
		self._state = self.STATE_INACTIVE
		# (P)TC aliveness
		self._alive = alive
		# PTC local verdict (not used for MTC for now...)
		self._verdict = VERDICT_NONE
		
		# Special internal events used by stop() and kill()
		self._STOP_COMMAND = { 'event': 'stop_ptc', 'ptc': self }
		self._KILL_COMMAND = { 'event': 'kill_ptc', 'ptc': self }
		
		# The event fired (through the system queue) when the TC is done()
		self._DONE_EVENT = { 'event': 'done', 'ptc': self }
		# ... and when it's killed()
		self._KILLED_EVENT = { 'event': 'killed', 'ptc': self }
		# The complete alt associated entries
		self.DONE = (_getSystemQueue(), self._DONE_EVENT, None)
		self.KILLED = (_getSystemQueue(), self._KILLED_EVENT, None)
		
		logTestComponentCreated(id_ = str(self))

	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def _setState(self, state):
		self._lock()
		self._state = state
		self._unlock()
		logInternal("%s switched its state to %s" % (str(self), str(state)))
	
	def _getState(self):
		self._lock()
		state = self._state
		self._unlock()
		return state

	def _finalize(self):
		"""
		Prepares the TC for discarding: purge all port queues.
		"""
		for port in self._ports.values():
			port._finalize()
	
	def _makeMtc(self, testcase):
		"""
		Flags this TC as being the MTC for the given testcase.
		To call when creating the MTC, i.e. when executing the testcase.
		"""
		self._mtc = True
		self._testcase = testcase
	
	def __str__(self):
		return self._name
	
	def __getitem__(self, name):
		"""
		Returns a port instance.
		@rtype: Port instance
		@returns: the port associated to portName.
		"""
		if not self._ports.has_key(name):
			self._ports[name] = Port(self, name)
		return self._ports[name]

	# Behaviour thread management

	def _start(self, behaviour, **kwargs):
		"""
		This method is called within the new PTC thread.
		Additional startup code, etc.
		"""
		logTestComponentStarted(id_ = str(self), behaviour = behaviour._name)
		try:
			getLocalContext().setTc(self)
			behaviour.execute(**kwargs)
			# Push the local verdict to the testcase
			self._updateTestCaseVerdict()

			self._doStop("PTC %s ended normally" % str(self))
			# Non-alive components are automatically killed by a stop.
			
		except TestermanStopException:
			# Push the local verdict to the testcase
			self._updateTestCaseVerdict()
			self._doStop("PTC %s stopped explicitly" % str(self))

		except TestermanKillException:
			# In this special case, we don't update the testcase verdict (violent death)
			self._doStop("PTC %s killed" % str(self))
			self._doKill()

		except Exception:
			# Non-control exception.
			self._setverdict(VERDICT_ERROR)
			self._updateTestCaseVerdict()
			logUser(tc = str(self), message = "PTC %s stopped on error:\n%s" % (str(self), getBacktrace()))
			self._doStop("PTC %s stopped on error" % str(self))
			# Kill it ?
			self._doKill()

	def _setverdict(self, verdict):
		"""
		Updates the local verdict only
		"""
		if verdict == VERDICT_ERROR and self._verdict != VERDICT_ERROR:
			self._verdict = verdict
			updated = True
		elif verdict == VERDICT_FAIL and self._verdict in [VERDICT_NONE, VERDICT_PASS, VERDICT_INCONC]:
			self._verdict = verdict
			updated = True
		elif verdict == VERDICT_INCONC and self._verdict in [VERDICT_NONE, VERDICT_PASS]:
			self._verdict = verdict
			updated = True
		elif verdict == VERDICT_PASS and self._verdict in [VERDICT_NONE]:
			self._verdict = verdict
			updated = True

		# Should we log the setverdict event if not actually updated ?
		# if updated:
		logVerdictUpdated(tc = str(self), verdict = self._verdict)

	def _getverdict(self):
		return self._verdict

	def _updateTestCaseVerdict(self):
		"""
		Pushes the local verdict to the testcase verdict.
		"""
		self._testcase.setverdict(self._verdict)

	def _doStop(self, message):
		"""
		Sets to stopped state, emit signals, additional transitions to killed, etc - if needed
		"""
		logTestComponentStopped(id_ = str(self), verdict = self._verdict, message = message)
		if not self._alive:
			if not self._getState() == self.STATE_KILLED:
				# According to TTCN-3, a stopped non-alive component is a killed component.
				# Direct transition to KILLED. Just emit the DONE event in the process.
				logTestComponentKilled(id_ = str(self), message = "PTC %s, non-alive, automatically killed after stop" % str(self))
				self._setState(self.STATE_KILLED)
				self._finalize()
				_postSystemEvent(self._DONE_EVENT)
				_postSystemEvent(self._KILLED_EVENT)
		else:
			if not self._getState() == self.STATE_STOPPED:
				# Alive components
				self._setState(self.STATE_STOPPED)
				_postSystemEvent(self._DONE_EVENT)
	
	def _doKill(self):
		"""
		Sets to killed state, emits killed signal, etc - if needed
		"""
		if self._getState() != self.STATE_KILLED:
			logTestComponentKilled(id_ = str(self), message = "killed")
			self._setState(self.STATE_KILLED)
			self._finalize()
			_postSystemEvent(self._KILLED_EVENT)

	def _raiseStopException(self):
		"""
		Wrapper function due to the fact that we cannot raise an exception in a lambda.
		"""
		raise TestermanStopException()
	
	def _raiseKillException(self):
		"""
		Wrapper function due to the fact that we cannot raise an exception in a lambda.
		"""
		raise TestermanKillException()

	def _getAltPrefix(self):
		"""
		Provides some additional messages to catch in a alt for internal reasons.
		In this case, this is to ensure that stop(), kill() generated events
		are correctly taken into account in any alt involving this TC,
		making sure that TC.alt()s are interruptible.
		"""
		return [
				[ (_getSystemQueue(), self._STOP_COMMAND, None), self._raiseStopException ],
				[ (_getSystemQueue(), self._KILL_COMMAND, None), self._raiseKillException ],
		]

	# TTCN-3 compliant interface

	def log(self, msg):
		logUser(tc = unicode(self), message = unicode(msg))

	def alive(self):
		"""
		TTCN-3 alive():
		For alive TC:
		Returns True is the TC is inactive, running, or stopped, 
		or false if killed.
		For non-alive TC:
		Returns True if the TC is inactive or running, False otherwise.

		@rtype: bool
		@returns: True if the component is alive, False otherwise.
		"""
		if self._mtc:
			return True

		if self._alive:
			return not (self._getState() == self.STATE_KILLED)

		return (self._getState() in [self.STATE_INACTIVE, self.STATE_RUNNING])

	def running(self):
		"""
		TTCN-3 running()
		Returns true if the TC is executing a behaviour.

		@rtype: bool
		@returns: True if the TC is running, False otherwise.
		"""
		if self._mtc:
			return True
		return (self._getState() == self.STATE_RUNNING)

	def start(self, behaviour, **kwargs):
		"""
		TTCN-3 start()
		Binds and runs a behaviour to a TC. 
		
		Starts the TC with behaviour, whose parameters are keyword args
		(passed to the user-implemented body()).
		
		Implementation note:
		normally we should go through the Component Handler to execute the behaviour
		on a possibly distributed PTC. 
		For now, this is just a (local) thread.
		
		@type  behaviour: a Behaviour object
		@param behaviour: the behaviour to bind to the PTC
		"""
		if self._mtc:
			# ignore start() on MTC
			return

		if not self.alive():
			raise TestermanTtcn3Exception("Invalid operation: you cannot start a behaviour on a PTC which is not alive anymore.")

		if self._getState() == self.STATE_RUNNING:
			raise TestermanTtcn3Exception("Invalid operation: you cannot start a behaviour on a running PTC.")

		logInternal("Starting %s..." % str(self))
		self._setState(self.STATE_RUNNING)
		# Attach the PTC to this behaviour
		behaviour._setPtc(self)
		
		behaviourThread = threading.Thread(target = self._start, args = (behaviour, ), kwargs = kwargs)
		behaviourThread.start()

	def stop(self):
		"""
		TTCN-3 stop()
		Stops the TC.

		On MTC, stops the testcase.
		On non-alive PTC, stops the PTC, which kills it.
		On alive PTC, stops the PTC. The PTC is then available for another start().
		"""
		if self._mtc:
			raise TestermanStopException()
		else:
			if self._getState() == self.STATE_RUNNING:
				logInternal("Stopping %s..." % str(self))
				# Let's post a system event to manage inter-thread communications
				_postSystemEvent(self._STOP_COMMAND)

	def kill(self):
		"""
		TTCN-3 kill()
		Kills a TC.
		
		Killing the MTC is equivalent to stop the testcase.
		Killing an alive-PTC makes it non-suitable for a new start().
		Supposed to free technical resources, but nothing to do in our implementation.
		"""
		if self._mtc:
			self._testcase.stop()
		else:
			if self._getState() == self.STATE_RUNNING:
				# Post our internal event to communicate with the PTC thread.
				_postSystemEvent(self._KILL_COMMAND)

	def done(self):
		"""
		TTCN-3 done()
		Waits for the TC termination (warning: no timeout).
		
		Only meaningful fot PTC.
		
		NB: use self.DONE instead of self.done() in an alt statement.
		"""
		# Immediately returns if the TC is not running (i.e. already 'done')
		if not self._getState() == self.STATE_RUNNING:
			return
		alt([[self.DONE]])


###############################################################################
# TTCN-3 Port
###############################################################################

class Port:
	"""
	TTCN-3 Port object.
	"""
	def __init__(self, tc, name = None):
		self._name = name
		if not self._name:
			self._name = "port_%d" % getNewId()
		self._mutex = threading.RLock()

		# The internal port's message queue
		self._messageQueue = []

		# The port state. Initially started, so that no start() is required.		
		self._started = True
		# associated test component.
		self._tc = tc

		# Ports connected to this port.
		# Whenever we send a message through this port, we actually enqueue the
		# message to each connected port's internal queue
		self._connectedPorts = []
		# The test system interface we are mapped to, if any.
		# In this case, _connectedPorts shall be empty.
		self._mappedTsiPort = None
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()

	def __str__(self):
		return "%s.%s" % (str(self._tc), self._name)
	
	def _finalize(self):
		# Disconnections, queue purge... useless since we won't use it anymore anyway.
		pass
	
	def _isMapped(self):
		if self._mappedTsiPort:
			return True
		else:
			return False
	
	def _isConnectedTo(self, port):
		return port in self._connectedPorts
	
	def _enqueue(self, message):
		# logInternal("%s enqueuing message, started %s" % (str(self), str(self._started)))
		if self._started:
			self._lock()
			self._messageQueue.append(message)
			self._unlock()
		# else not started: not enqueueing anything.

	# TTCN-3 compliant operations
	def send(self, message, sutAddress = None):
		"""
		Sends a message to the connected ports or the mapped port.
		
		@type  message: any structure
		@param message: the message to send through this port
		@type  sutAddress: string
		@param sutAddress: an optional SUT address, the meaning is mapped-tsiPort-specific.
		
		@rtype: bool
		@returns: True if the message has been sent (i.e. if the port has not been connected or mapped),
		          False if not (port stopped)
		"""
		logInternal("sending a message through %s" % str(self))
		if self._started:
			messageToLog = _expandTemplate(message)
			messageToSend = _encodeTemplate(message)

			# Mapped port first.
			if self._mappedTsiPort:
				logMessageSent(fromTc = str(self._tc), fromPort = self._name, toTc = "system", toPort = self._mappedTsiPort._name, message = messageToLog)
				self._mappedTsiPort.send(messageToSend, sutAddress)
			else:
				for port in self._connectedPorts:
					logMessageSent(fromTc = str(self._tc), fromPort = self._name, toTc = str(port._tc), toPort = port._name, message = messageToLog)
					port._enqueue(messageToSend)
			return True
		else:
			return False

	def receive(self, template = None, asValue = None):
		"""
		Waits (blocking) for template to be received on this port. 
		If asValue is provided, store the received message to it.
		
		@type  template: any structure valid for a template
		@param template: the template to match
		@type  asValue: string
		@param asValue: the name of the value() variable to store the received message to.
		"""
		if self._started:
			alt([[self.RECEIVE(template, asValue)]])

	def start(self):
		"""
		Starts the port (after purging its queue)
		"""
		self._lock()
		self._messageQueue = []
		self._unlock()
		self._started = True
		logInternal("%s started" % str(self))

	def stop(self):
		"""
		Stops the port, keeping it from receiving further messages.
		Current enqueue messages are kept.
		"""
		self._started = False
		logInternal("%s stopped" % str(self))

	def clear(self):
		"""
		Purges the internal queue, without stopping the port.
		"""
		self._lock()
		self._messageQueue = []
		self._unlock()
		logInternal("%s cleared" % str(self))

	def RECEIVE(self, template = None, asValue = None):
		"""
		Returns the event structure to use in alt()
		"""
		# TODO: more flexible internal representation for a alt clause event (dict ?)
		return (self, template, asValue)


###############################################################################
# TTCN-3 Behaviour
###############################################################################

class Behaviour:
	"""
	The class to subclass and whose body(self, args) must be implemented
	to run as a behaviour within a PTC.
	"""
	def __init__(self):
		self._name = self.__class__.__name__
		#: associated PTC
		self._ptc = None
	
	def __str__(self):
		return self._name

	def _setPtc(self, ptc):
		self._ptc = ptc

	def __getitem__(self, name):
		"""
		Convenience/Diversion to the associated PTC ports.
		"""
		return self._ptc[name]
	
	def setverdict(self, verdict):
		"""
		Diversion to the PTC setverdict.
		"""
		self._ptc._setverdict(verdict)
	
	def getverdict(self):
		"""
		Diversion to the PTC getverdict.
		"""
		return self._ptc._getverdict()

	def log(self, msg):
		"""
		Diversion to the associated PTC log.
		"""
		self._ptc.log(msg)

	# body does not exist in the base class, but must be implemented in the user class.
	
	def execute(self, **kwargs):
		"""
		Executes the body part.
		Or nothing if no body has been defined.
		"""
		body = getattr(self, 'body')
		if callable(body):
			body(**kwargs)
		

################################################################################
# TTCN-3 Testcase
################################################################################

class TestCase:
	"""
	Main TestCase class, representing a TTCN-3 testcase.
	"""
	def __init__(self, title = '', idSuffix = None):
		self._title = title
		self._idSuffix = idSuffix
		self._verdict = VERDICT_NONE
		self._description = self.__doc__
		self._mutex = threading.RLock()
		self._name = self.__class__.__name__
		# This is a list of the ptc created by/within this testcase.
		self._ptcs = []
		logTestcaseCreated(str(self), title = title)

		self._mtc = None
		self._system = None

		# Aliases, kept for compatibility
		self.system = None
		self.mtc = None
	
	def __str__(self):
		"""
		Returns the testcase identifier.
		"""
		if self._idSuffix is not None:
			return '%s_%s' % (self._name, self._idSuffix)
		else:
			return self._name

	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()

	def _createMtc(self):
		"""
		Creates the MTC component.
		"""
		tc = TestComponent(name = "mtc")
		tc._testcase = self
		tc._makeMtc(self)
		return tc
	
	def _finalize(self):
		"""
		Performs a test case finalization:
		- stop all PTCs
		- cleanup the system component (purge internal ports and TSI ports)
		- stop all timers
		- clear the TLS/Context associated to the testcase.
		- we should unmap all ports, though triSAReset will force it implicitly
		NB: triSAReset is called after this finalization, in execute()
		"""
		# Stops PTCs and wait for their completion.
		# 2 passes proven to be more efficient that ptc.stop() + done() in one pass
		for ptc in self._ptcs:
			ptc.stop()
		for ptc in self._ptcs:
			ptc.done()

		self._system._finalize()
		
		# Stop timers, purge the TLSes
		clearContextAndStopAllTimers()

	def setverdict(self, verdict):
		"""
		Sets the testcase verdict.
		
		TTCN-3 overwriting rules:
		fail > [ pass, inconc, none ]
		pass > none
		inconc > pass, none
		
		to sum it up: fail > inconc > pass.
		
		'error' overwrites them all.
		
		@type  verdict: string in [ "none", "pass", "fail", "inconc", "error" ]
		@param verdict: the new verdict
		"""
		updated = False
		self._lock()
		
		if verdict == VERDICT_ERROR and self._verdict != VERDICT_ERROR:
			self._verdict = verdict
			updated = True
		elif verdict == VERDICT_FAIL and self._verdict in [VERDICT_NONE, VERDICT_PASS, VERDICT_INCONC]:
			self._verdict = verdict
			updated = True
		elif verdict == VERDICT_INCONC and self._verdict in [VERDICT_NONE, VERDICT_PASS]:
			self._verdict = verdict
			updated = True
		elif verdict == VERDICT_PASS and self._verdict in [VERDICT_NONE]:
			self._verdict = verdict
			updated = True

		self._unlock()

		# Should we log the setverdict event if not actually updated ?
		# if updated:
		logVerdictUpdated(tc = str(self._mtc), verdict = self._verdict)

	def getverdict(self):
		"""
		Returns the current testcase verdict.
		@rtype: string in [ "none", "pass", "fail", "inconc", "error" ]
		@returns: the current verdict
		"""
		self._lock()
		ret = self._verdict
		self._unlock()
		return ret

	def setDescription(self, description):
		"""
		Sets an extended, possibly dynamic description for the testcase.
		By default, the description is the testcase autodoc.
		@type  description: unicode/string
		@param description: the description
		"""
		self._description = description
	
	def create(self, name = None, alive = False):
		"""
		Creates and returns a (P)TC.
		The resulting TC will be associated to the testcase.
		
		@type  name: string
		@param name: the name of the PTC. If None, the name is automaticall generated as tc_%d.
		@type  alive: bool
		@param alive: TTCN-3 TC alive parameter.
		
		@rtypes: TestComponent
		@returns: a new TestComponent.
		"""
		tc = TestComponent(name, alive)
		tc._testcase = self
		self._ptcs.append(tc)
		return tc
	
	# NB: No default implementation of body() since its signature would not be
	# matched by most testcases, anyway.
	# def body(self, ...)
	
	def execute(self, **kwargs):
		try:
			self._mtc = self._createMtc()
			self._system = SystemTestComponent()
			# Aliases kept for compatibility
			self.mtc = self._mtc
			self.system = self._system
			# Let's set global variables (system and mtc - only for convenience)
			# NB: won't work. Not in the same module as the TE...
#			globals()['mtc'] = self._mtc
#			globals()['system'] = self._system
			
			# Let's set the global context
			getLocalContext().setTc(self._mtc)
			getLocalContext().setTestCase(self)

			# Make sure no old system messages remain in queue
			_resetSystemQueue()
		
			logTestcaseStarted(str(self))

			# Initialize static connections
			# (and testerman bindings according to the system configuration)
			if getCurrentTestAdapterConfiguration():
				tsiPortList = getCurrentTestAdapterConfiguration()._getTsiPortList()
			else:
				tsiPortList = []
			TestermanSA.triExecuteTestCase(str(self), tsiPortList)

			# Call the body			
			body = getattr(self, 'body')
			if callable(body):
				body(**kwargs)
			
		except TestermanStopException:
			logInternal("Testcase explicitely stop()'d")

		except Exception:
			self.setverdict(VERDICT_ERROR)
			log("Testcase stopped on error:\n%s" % getBacktrace())
		
		try:
			self._finalize()
		except Exception:
			# Nothing particular to do in case of an error here...
			logInternal("Exception while finalizing testcase:\n%s" % getBacktrace())

		# Final static connection reset
		TestermanSA.triSAReset()

		# Reset the system queue (to do on start only ?)
		_resetSystemQueue()
		
		logTestcaseStopped(str(self), verdict = self._verdict, description = self._description)

		# Now check if we can continue or stop here if the ATS has been cancelled
		if _isAtsCancelled():
			raise TestermanCancelException()

		return self._verdict

	def log(self, message):
		"""
		Logging at testcase level is equivalent to logging at MTC level.
		We only support logging of simple messages.

		@type  message: unicode/string
		@param message: the message to log
		"""
		self._mtc.log(message)


###############################################################################
# System TC
###############################################################################

class SystemTestComponent:
	"""
	This is a special object interfacing the TRI, via its test system interface
	ports, to the TTCN-3 userland.
	
	Basically exposes Port-compatible objects for mapping/unmapping.
	These ports should be bound to a test adapter using a TestAdaterConfiguratin.
	
	There is one and only one system TC per testcase, automatically created.
	In TTCN-3, it is created from a system type definition, defining valid port
	names and types.
	In this implementation, valid ports are the one that have been bound to a
	test adapters, but there is no formal typing, as usual.
	"""
	def __init__(self):
		self._name = "system"
		# TestSystemInterfacePorts, identified by their names (string)
		self._tsiPorts = {}
		logTestComponentCreated(id_ = str(self))
	
	def __str__(self):
		return self._name

	def __getitem__(self, name):
		"""
		Returns (and creates, if needed) a tsi port instance.
		"""
		if not self._tsiPorts.has_key(name):
			self._tsiPorts[name] = TestSystemInterfacePort(name)
		return self._tsiPorts[name]

	def _finalize(self):
		"""
		Unmap all mapped tsi ports.
		"""
		for (name, tsiPort) in self._tsiPorts.items():
			for port in tsiPort._mappedPorts:
				port_unmap(port, tsiPort)
	
################################################################################
# Test System Interface Port
################################################################################

class TestSystemInterfacePort:
	"""
	This Port "specialization" (although this is not a Port subclass)
	interfaces the TRI with the userland.
	"""
	def __init__(self, name):
		self._name = name
		self._mappedPorts = []

	def __str__(self):
		return "system.%s" % self._name

	def _enqueue(self, message):
		"""
		Forwards an incoming message (from TRI) to the ports mapped to this tsi port.
		Called by triEnqueueMsg.
		"""
		for port in self._mappedPorts:
			logMessageSent(fromTc = "system", fromPort = self._name, toTc = str(port._tc), toPort = port._name, message = message)
			port._enqueue(message)

	def send(self, message, sutAddress):
		"""
		Specialized reimplementation.
		Calls the tri interface.
		
		The returned status is ignored for now.
		"""
		return TestermanSA.triSend(None, self._name, sutAddress, message)


################################################################################
# TTCN-3 primitives for Testcase and Control part
################################################################################

def stop(retcode = 0):
	"""
	Stops the current testcase or ATS, depending on where the instruction appears.
	
	When executed from a testcase/behaviour, stops the testcase/behaviour
	with the last known verdict. 'code' is ignored in this case.
	
	When used from the control part, stops the ATS, setting its result code to
	code, if provided.
	
	Implementation note: implemented as an exception, leading to the expected
	behaviour depending on the context.
	
	@type  retcode: integer
	@param retcode: the return code, only valid for Control part.
	
	TODO: 
	"""
	raise TestermanStopException(retcode)

def log(msg):
	"""
	Logs a user message.
	
	SUGGESTION: should we force a log at TC level only ? (using getLocalContext()
	it is easy to do so, but it can be convenient to have 2 log 'levels':
	- one attached a a component
	- an other one (this one) attached to a testcase (or... even to the control part).
	
	@type  msg: unicode or string
	@param msg: the message to log
	"""
	logUser(msg)

def connect(portA, portB):
	"""
	Connects portA and portB (symmetrical connection).
	Verifies basic TTCN-3 restrictions/constraints (but none regarding typing and allowed
	messages since we don't define any typing).
	
	Connections are bi-directional.
	
	@type  portA: Port
	@param portA: one of the port to connect.
	@type  portB: Port
	@param portB: the other port to connect.
	"""
	# Does not reconnect connected ports:
	if portA._isConnectedTo(portB): # The reciprocity should be True, too (normally)
		logInternal("Multiple connection attempts between %s and %s. Discarding." % (str(portA), str(portB)))
		return

	# TTCN-3 restriction: "A port that is mapped shall not be connected"
	if portA._isMapped() or portB._isMapped():
		raise TestermanTtcn3Exception("Cannot connect %s and %s: at least one of these ports is already mapped." % (str(portA), str(portB)))

	# TTCN-3 restriction: "A port owned by a component A shall not be connected with 2 or more ports owned by the same component"
	# TTCN-3 restriction: "A port owned by a component A shall not be connected with 2 or more ports owned by a component B"
	for port in portA._connectedPorts:
		if port._tc == portB._tc:
			raise TestermanTtcn3Exception("Cannot connect %s and %s: %s is already connected to %s" % (str(portA), str(portB), str(portA), str(port)))
	for port in portB._connectedPorts:
		if port._tc == portA._tc:
			raise TestermanTtcn3Exception("Cannot connect %s and %s: %s is already connected to %s" % (str(portA), str(portB), str(portB), str(port)))

	# OK, we can connect
	portA._connectedPorts.append(portB)
	portB._connectedPorts.append(portA)

def disconnect(portA, portB):
	"""
	Disconnects portA and portB.
	Does nothing if they are not connected.
	"""
	if portA in portB._connectedPorts:
		portB._connectedPorts.remove(portA)
	if portB in portA._connectedPorts:
		portA._connectedPorts.remove(portB)

# Map[tsiPort._name] = tsiPort 
# A system-wide/global view on the current mappings. A local view is also available on each tsiPort and on each Port.
# As for timers, enables triEnqueueMsg to retrieve a TestSystemInterfacePort instance based on an id used for tri.
_TsiPorts = {}
_TsiPortsLock = threading.RLock()

def port_map(port, tsiPort):
	"""
	TTCN-3 map()
	Maps a port to a test system interface port, verifying basic
	TTCN-3 restrictions.
	
	Interfaces to the triMap TRI operation.
	
	@type  port: Port
	@param port: the port to map
	@type  tsiPort: TestSystemInterfacePort
	@param tsiPort: the test system interface to map the port to
	"""
	# TTCN-3 restriction: "A port owned by a component A can only have a one-to-one connection with the test system"
	# TTCN-3 restriction: "A port that is connected shall not be mapped"
	if port._isMapped():
		raise TestermanTtcn3Exception("Cannot map %s to %s: %s is already mapped" % (str(port), str(tsiPort), str(port)))

	# Should we use a status or directly an exception ?...
	status = TestermanSA.triMap(port, tsiPort._name)
	if status == TestermanSA.TR_Error:
		raise TestermanTtcn3Exception("Cannot map %s to %s: triMap returned TR_Error, probably a missing binding" % (str(port), str(tsiPort._name)))
	
	# TRI local association, so that triEnqueueMsg can retrieve the associated tsiPort based on its name
	# (used as a tri id)
	_TsiPortsLock.acquire()
	_TsiPorts[tsiPort._name] = tsiPort
	_TsiPortsLock.release()
	# "Local" mapping
	port._mappedTsiPort = tsiPort
	tsiPort._mappedPorts.append(port)

def port_unmap(port, tsiPort):
	"""
	TTCN-3 unmap()
	Unmaps a mapped port.
	
	Does nothing if the port was not mapped to this tsiPort.

	@type  port: Port
	@param port: the port to unmap from the tsiPort
	@type  tsiPort: TestSystemInterfacePort
	@param tsiPort: the tsi port to unmap from the tsiPort
	"""
	# TRI call
	TestermanSA.triUnmap(port, tsiPort._name)
	# System-wide de-association
	_TsiPortsLock.acquire()
	if _TsiPorts.has_key(tsiPort._name):
		# We only remove the tsiport from the tri local mapping
		# if the tsi port is not used by any other port anymore.
		# Let's check this.
		# Perform our "local" deassociation
		port._mappedTsiPort = None
		if port in tsiPort._mappedPorts: 
			tsiPort._mappedPorts.remove(port)
		if tsiPort._mappedPorts == []:
			# OK, the tsiPort is not used anymore. We can remove it.
			del _TsiPorts[tsiPort._name]
	_TsiPortsLock.release()

################################################################################
# alt() management
################################################################################

def _setValue(name, message):
	"""
	Called by alt() to store a message to a variable.
	"""
	getLocalContext().setValue(name, message)

def value(name):
	"""
	Gets a value that was matched in a receive(..., 'asValue') or RECEIVE=(..., 'asValue'),
	where 'asValue' is the name of the value to retrieve.

	In TTCN-3, this is:
		port.receive(myTemplate) -> value myValue
		log("value" & myValue)

	Testerman equivalent:
		port.receive(myTemplate, 'myValue')
		log("value" + value('myValue'))
	
	@type  name: string
	@param name: the name of the value to retrieve
	
	@rtype: object, or None
	@returns: the matched value object, if any, or None if it was not matched or the value was not set.
	"""
	return getLocalContext().getValue(name)

def alt(alternatives):
	"""
	TTCN-3 alt(),
	with some minor modifications to make it more convenient (supposely).
	
	TTCN-3 syntax:
	alt {
		[] port.receive(template) {
			action1;
			action2;
			...
			}
		[ x > 0 ] port.receive {
			...
			}
		[] timer.timeout {
			...
			}
	}
	
	Testerman syntax:
	alt([
		[ port.RECEIVE(template),
			lambda: action1,
			lamdda: action2,
			...
			REPEAT, # or lambda: REPEAT
		],
		[ lambda: x > 0, port.RECEIVE(),
			...
		],
		[ timer.TIMEOUT,
			...
		]
	])
	
	i.e. alt is implemented as a function whose arguments are in undefined number (can be computed at runtime
	as a list and passed as the *args), called "alternatives",
	where is alternative is a list made of:
	- an optional guard. If present, detected because the first element of the alternative is callable().
	  In TTCN-3, the guard is mandatory, even if empty (and is actually not part of the alternative itself,
	  but just precedes it (and separate them).
	- the branch condition, which is currently implemented by a tuple (port, template, asValue) but
	  MUST be declared in userland through port.RECEIVE(template, asValue) or timer.TIMEOUT,
	  tc.DONE, tc.KILLED, etc (since the internal representation may change)
	- the associated branch actions, as the remaining list of elements in the alternative list.
	  They must be lambda or callable() to be executed only if the branch is selected.
	
	This implementation is not TTCN-3 compliant because:
	- it does not take a snapshot at each iteration, meaning that messages may arrives on port2 just
	  before analyzing it, while something arrives on port1 just after, leading to incorrect alt branching
	  in the case of port1.RECEIVE() is before port2.RECEIVE() (in "order of appearance")
	- altstep-branches are not implemented. Only timeout-, receiving-, killed-, done- branches are.
	- there is no mechanism to trigger an exception if the alt is completely blocked.
	  As a consequence, the user must carefully design his/her alt() (especially with watchdog timers)
	  or may risk a blocking call.
	- 'else' guard is not implemented
	- 'any' is not implemented
	
	
	Additional notes:
	- alt() is also used, in this implementation, to handle internal control messages
	  posted using the system queue. This is used to match timeout-, killed-, done- branches conditions,
		and to manage basic inter-tc control communications (inter thread posting) for tc.stop() and tc.killed().
	
	
	@type  alternatives: list of [ callable, (Port, any, string), callable, callable, ... ]
	@param alternatives: a list of alternatives, containing an optional callable as a guard,
	                     then a branch condition as (port, template, asValue),
	                     then 0..N callable as actions to perform if the branch is selected.

	The guard is detected if the first object in the list is callable. If it is, this is a guard. If not, no guard available.
	"""
	# Algorithm:
	# 1. First, we group alternatives per port (ordered).
	# 2. Then, we look messages port by port:
	#  2.1 Pop the first message in its queue (if any)
	#  2.2 Compare it to the templates contained in its associated alternative's conditions, once we checked that the guard was satisfied
	#  2.3 If we have a template match (the first one for the list of alternatives)
	#      - select the branch: execute the associated actions. If an action evaluates to STOP, stop executing further actions,
	#        and leave the alt. If one evaluates to REPEAT, stop executing further actions, and repeat the alt() from start.
	#        If we have no other actions to execute, leave the alt.
	#      If this is a mismatch, do nothing, just compare to the next alternative's conditions.
	#  2.4 in any case (even if we leave or repeat the alt, match or mismatch), the current popped message is consumed.
	# 3. Once we looped once without a match, repeat from 2 until we have a match.
	# 
	# The system queue is handled differently:
	# - unmatched messages are not consumed, but kept in the queue. This is not the case for "userland ports".
	# - REPEAT, STOP, are not supported for system queue events.

	# Gets some basic things to intercept whenever we enter an alt, such as STOP_COMMAND and KILL_COMMAND
	# through the system queue.	
	additionalInternalAlternatives = getLocalContext().getTc()._getAltPrefix()
	for a in additionalInternalAlternatives:
		alternatives.insert(0, a)
	
	# Step 1.
	# Alternatives per port
	portAlternatives = {}
	
	for alternative in alternatives:
		# Optional guard. Its presence is detected if the first element of the clause is callable.
		guard = None
		if callable(alternative[0]):
			guard = alternative[0]
			condition = alternative[1]
			actions = alternative[2:]
		else:
			guard = None # lambda: True ?
			condition = alternative[0]
			actions = alternative[1:]
		
		(port, template, asValue) = condition

 		if not portAlternatives.has_key(port):
			portAlternatives[port] = []
		portAlternatives[port].append((guard, template, asValue, actions))

	# Step 2.
	matchedInfo = None # tuple (guard, template, asValue, actions, message, decodedMessage)
	repeat = False
	while (not matchedInfo) or repeat:
		# Reset info in case of a repeat
		matchedInfo = None
		repeat = False

		for (port, alternatives) in portAlternatives.items():
			# Special handling for system queue
			if port is _getSystemQueue():
				port._lock()
				for message in port._messageQueue:
					for (guard, template, asValue, actions) in alternatives:
						# Guard is ignored for internal messages (we shouldn't have one, anyway)
						# Ignore the decoded message: must be the same as encoded for internal events.
						(match, _) = templateMatch(message, template)
						if match:
							matchedInfo = (guard, template, asValue, actions, message, None) # None: decodedMessage
							# Consume the message
							port._messageQueue.remove(message)
							# Exit the port alternative loop, with matchedInfo
							break
					if matchedInfo:
						# Exit the loop on messages directly.
						break
				port._unlock()
				if matchedInfo:
					(guard, template, asValue, actions, message, _) = matchedInfo
					# OK, we have some actions to trigger (outside the critical section)
					# According to the event type we matched, log it (or not)
					# system queue events are always formatted as a dict { 'event': string } and 'ptc' or 'timer' dependending on the event.
					branch = template['event']
					if branch == 'timeout':
						# timeout-branch selected
						logTimeoutBranchSelected(id_ = str(template['timer']))
					elif branch == 'done':
						# done-branch selected
						logDoneBranchSelected(id_ = str(template['ptc']))
					elif branch =='killed':
						# killed-branch selected
						logKilledBranchSelected(id_ = str(template['ptc']))
					else:
						# Other system messages are for internal purpose only and does not have TTCN-3 branch equivalent
						logInternal('system event received in system queue: %s' % repr(template))
					
					for action in actions:
						# Minimal command management for internal messages
						if callable(action):
							action()
				else:
					# no match, nothing to do.
					pass
				
			else:
				# This is a normal port. We always consume the popped message, 
				# support for STOP and REPEAT "keywords" in actions, etc.
				message = None
				port._lock()
				if port._messageQueue:
					# 2.1 Let's pop the first message in the queue (will be consumed whatever happens since not kept in queue)
					# FIXME: flawn implementation: we shoud not consume only one message per port per pass.
					# We should really take a "snapshot" (ie freezing ports) and considering timestamped messages...
					message = port._messageQueue[0]
					port._messageQueue = port._messageQueue[1:]
				port._unlock()
				if message is not None: # And what is we want to send "None" ? should be considered as a non-message, ie a non-send ?
					# 2.2: For each existing satisfied conditions for this port (x[0] is the guard)
					for (guard, template, asValue, actions) in filter(lambda x: (x[0] and x[0]()) or (x[0] is None), alternatives):
						(match, decodedMessage) = templateMatch(message, template)
						if not match:
							# 2.3 - Mismatch, we should log it.
							logTemplateMismatch(tc = port._tc, port = port._name, message = decodedMessage, template = _expandTemplate(template), encodedMessage = message)
						else:
							# 2.3 - Match
							matchedInfo = (guard, template, asValue, actions, message, decodedMessage)
							logTemplateMatch(tc = port._tc, port = port._name, message = decodedMessage, template = _expandTemplate(template), encodedMessage = message)
							# Store the message as value, if needed
							if asValue:
								_setValue(asValue, decodedMessage)
							# Then execute actions
							for action in actions:
								if callable(action):
									action = action()
								if action == REPEAT:
									repeat = True
									break
								elif action == STOP:
									return
							# Break the loop on guard-validated alternatives for this port
							break
					if matchedInfo:
						# We left the loop on guard-validated alternatives for this port because of a match,
						# Let's break the main loop on ports
						break
					else:
						# No match for this port: nothing to do
						pass
				else:
					# no message for this port: nothing to do
					pass
				
		# Little delay between two loops, forcing sched yield
		time.sleep(0.0001)

# Control "Keywords" for alt().
# May be used as is directly, in a lambda, or returned from an altstep or a function called
# from a lambda.
def REPEAT():
	return REPEAT

def STOP():
	return STOP


################################################################################
# System/internal queue
################################################################################

# The system/internal queue is implemented as 
# a special internal communication port, called the "system port",
# used as an internal messaging queue for implementation control, i.e.:
# - timeout management (timeout events are not associated to a particular port in TTCN3)
# - inter-TC control events (kill-, stop-, related operations)
#
# We use the messaging mechanism developed to manage TTCN-3 messages (alt, ports,
# etc) to implement, provision and read this message queue as well.
# System messages are handled in alt(), as if it were any other TTCN-3 message.

_SystemQueue = Port(tc = None, name = '__system_queue__')

def _getSystemQueue():
	return _SystemQueue

def _resetSystemQueue():
	"""
	Resets the system queue by restarting the implementing Port.
	"""
	_getSystemQueue().stop()
	_getSystemQueue().start()

def _postSystemEvent(event):
	"""
	Posts an event in the system bus
	"""
	_getSystemQueue()._enqueue(event)


################################################################################
# Test Adapter Configuration management - System Bindings management
################################################################################

# Actually, this is not a part of TTCN-3.
# Pure testerman "concept" to configure Test Adapters, i.e. probes to use.

_CurrentTestAdapterConfiguration = None
_AvailableTestAdapterConfigurations = {}

class TestAdapterConfiguration:
	def __init__(self, name):
		self._name = name
		self._tac = TestermanSA.TestAdapterConfiguration(name = name)
		registerAvailableTestAdapterConfiguration(name, self)
	
	def bindByUri(self, tsiPort, uri, type_, **kwargs):
		return self._tac.bindByUri(tsiPort, uri, type_, **kwargs)
	
	def _getTsiPortList(self):
		return self._tac.getTsiPortList()

def registerAvailableTestAdapterConfiguration(name, tac):
	_AvailableTestAdapterConfigurations[name] = tac

def useTestAdapterConfiguration(name):
	global _CurrentTestAdapterConfiguration
	if _CurrentTestAdapterConfiguration:
		_CurrentTestAdapterConfiguration._tac._uninstall()
	if _AvailableTestAdapterConfigurations.has_key(name):
		tac = _AvailableTestAdapterConfigurations[name]
		tac._tac._install()
		_CurrentTestAdapterConfiguration = tac
	else:
		raise TestermanException("Unknown Test Adapter Configuration %s" % name)

def getCurrentTestAdapterConfiguration():
	return _CurrentTestAdapterConfiguration	
	
	
################################################################################
# Template Conditions, i.e. Matching Mechanisms
################################################################################

class ConditionTemplate:
	"""
	This is a template proxy, like a CodecTemplate.
	
	Some conditions can work on other conditions (wildcards/conditions templates),
	some other ones are terminal and only works with fixed values
	(fully defined templates - no wildcards, no conditions)
	
	For instance, contains() can nest a condition on scalar (lower_than, ...),
	same for length(), (length(between(1, 3)), length(lower_than(2)), ...)
	but not things like between, lower_than, regexp, etc.
	"""
	def match(self, message):
		return True

##
# Terminal conditions
##

# Scalar conditions
class greater_than(ConditionTemplate):
	def __init__(self, value):
		self._value = value
	def match(self, message):
		try:
			return float(message) >= float(self._value)
		except:
			return False
	def __repr__(self):
		return "(>= %s)" % str(self._value)

class lower_than(ConditionTemplate):
	def __init__(self, value):
		self._value = value
	def match(self, message):
		try:
			return float(message) <= float(self._value)
		except:
			return False
	def __repr__(self):
		return "(<= %s)" % str(self._value)

class between(ConditionTemplate):
	def __init__(self, a, b):
		if a < b:
			self._a = a
			self._b = b
		else:
			self._a = b
			self._b = a
	def match(self, message):
		try:
			return float(message) <= float(self._b) and float(message) >= float(self._a)
		except:
			return False
	def __repr__(self):
		return "(between %s and %s)" % (str(self._a), str(self._b))

# Any
class any(ConditionTemplate):
	"""
	Following the TTCN-3 standard, equivalent to ?.
	- must be present
	- contains at least one element for dict/list/string
	"""
	def __init__(self):
		pass
	def match(self, message):
		if isinstance(message, (list, dict, basestring)):
			if message:
				return True
			else:
				return False
		# Primitives/non-constructed types (and tuple)
		return True
	def __repr__(self):
		return "(?)"

class any_or_none(ConditionTemplate):
	"""
	Equivalent to * in TTCN-3.
	Provided for convenience. Equivalent to 'None' in Testerman.
	- in a dict: any value if present
	- in a list: match any number of elements
	- as a value: any value
	"""
	def __init__(self):
		pass
	def match(self, message):
		return True
	def __repr__(self):
		return "(*)"

# Empty (list, string, dict)
class empty(ConditionTemplate):
	"""
	Applies to lists, strings, dict
	"""
	def __init__(self):
		pass
	def match(self, message):
		try:
			return len(message) == 0
		except:
			return False
	def __repr__(self):
		return "(empty)"

# String: regexp
class pattern(ConditionTemplate):
	def __init__(self, pattern):
		self._pattern = pattern
	def match(self, message):
		if re.search(self._pattern, message):
			return True
		return False
	def __repr__(self):
		return "(pattern %s)" % str(self._pattern)

class omit(ConditionTemplate):
	"""
	Special template.
	Use it when you want to be sure you did not receive
	an entry in a dict (a field in a record).
	Specially handled in _templateMatch since in case of matching,
	we are not supposed to call it.match().
	"""
	def __init__(self):
		pass
	def match(self, message):
		return False
	def __repr__(self):
		return "(omitted)"

class equals_to(ConditionTemplate):
	"""
	Case-insensitive equality.
	To remove ?
	"""
	def __init__(self, value):
		self._value = value
	def match(self, message):
		return unicode(message).lower() == unicode(self._value).lower()
	def __repr__(self):
		return "(=== %s)" % unicode(self._value)

##
# Non-terminal conditions
##
# Matching negation
class not_(ConditionTemplate):
	def __init__(self, template):
		self._template = template
	def match(self, message):
		(m, _) = templateMatch(message, self._template)
		return not m
	def __repr__(self):
		return "(not %s)" % str(self._template) # a recursive str(template) is needed - here it will work only for simple types/comparators.

class ifpresent(ConditionTemplate):
	def __init__(self, template):
		self._template = template
	def match(self, message):
		(m, _) = templateMatch(message, self._template)
		return m
	def __repr__(self):
		return "(%s, if present)" % unicode(self._template)

# Length attribute
class length(ConditionTemplate):
	def __init__(self, template):
		self._template = template
	def match(self, message):
		(m, _) = templateMatch(len(message), self._template)
		return m
	def __repr__(self):
		return "(length %s)" % unicode(self._template)

class superset(ConditionTemplate):
	"""
	contains at least each element of the value (1 or more times)
	(list only)
	"""
	def __init__(self, *templates):
		self._templates = templates
	def match(self, message):
		for tmplt in self._templates:
			ret = False
			for e in message:
				(ret, _) = templateMatch(e, tmplt)
				if ret: 
					# ok, tmplt is in message. Next template?
					break
			# sorry, tmplt is not in the message. This is not a superset.
			if not ret:
				return False
		# All tmplt in the message, at least once (the actual count is not computed)
		return True
	def __repr__(self):
		return "(superset of [%s])" % ', '.join([unicode(x) for x in self._templates])

class subset(ConditionTemplate):
	"""
	contains only elements from the template (1 or more times each)
	(list only)
	"""
	def __init__(self, *templates):
		self._templates = templates
	def match(self, message):
		for e in message:
			ret = False
			for tmplt in self._templates:
				(ret, _) = templateMatch(e, tmplt)
				if ret: 
					break
			if not ret:
				return False
		return True
	def __repr__(self):
		return "(subset of [%s])" % ', '.join([unicode(x) for x in self._templates])

class contains(ConditionTemplate):
	"""
	Dict/list/string content check
	As a consequence, a bit wider than superset(template)
	"""
	def __init__(self, template):
		self._template = template
	def match(self, message):
		# At least one match
		for element in message:
			(m, _) = templateMatch(element, self._template)
			if m:
				return True
		return False
	def __str__(self):
		return "(contains %s)" % unicode(self._template)

class in_(ConditionTemplate):
	"""
	'included in' a set/list of other templates
	
	This is a subset() for a single element. (mergeable with subset ?)
	"""
	def __init__(self, *template):
		# template is a list of templates (wildcards accepted)
		self._template = template
	def match(self, message):
		for element in self._template:
			(m, _) = templateMatch(message, element)
			if m:
				return True
		return False
	def __repr__(self):
		return "(in %s)" % unicode(self._template)

class complement(ConditionTemplate):
	"""
	'not included in a list'.
	The TTCN-3 equivalent is 'complement'.
	Equivalent to not_(in_)
	"""
	def __init__(self, *template):
		# template is a list of templates (wildcards accepted)
		self._template = template
	def match(self, message):
		for element in self._template:
			(m, _) = templateMatch(message, element)
			if m:
				return False
		return True
	def __repr__(self):
		return "(complements %s)" % unicode(self._template)

class and_(ConditionTemplate):
	"""
	And condition operator.
	"""
	def __init__(self, templateA, templateB):
		# template is a list of templates (wildcards accepted)
		self._templateA = templateA
		self._templateB = templateB
	def match(self, message):
		(m, _) = templateMatch(message, self._templateA)
		if m:
			return templateMatch(message, self._templateB)[0]
		return False
	def __repr__(self):
		return "(%s and %s)" % (unicode(self._templateA), unicode(self._templateB))
		
class or_(ConditionTemplate):
	"""
	Or condition operator.
	"""
	def __init__(self, templateA, templateB):
		# template is a list of templates (wildcards accepted)
		self._templateA = templateA
		self._templateB = templateB
	def match(self, message):
		(m, _) = templateMatch(message, self._templateA)
		if not m:
			return templateMatch(message, self._templateB)[0]
		return True
	def __repr__(self):
		return "(%s or %s)" % (unicode(self._templateA), unicode(self._templateB))
	
################################################################################
# "Global" Variables Management
################################################################################

# Session variables are external variables: can be set from outside,
# returned outside for ATS chaining.
# By convention, session variable names starts with 'PX_'
_SessionVariables = {}
# Ats variables are global variables for the ATS only.
# They are not exposed or provisioned to/from the outside world.
_AtsVariables = {}

_VariableMutex = threading.RLock()

def get_variable(name, defaultValue = None):
	# Fallback to defaultValue for invalid variable names ?
	ret = defaultValue
	_VariableMutex.acquire()
	if name.startswith('PX_'):
		ret = _SessionVariables.get(name, defaultValue)
	elif name.startswith('P_') :
		ret = _AtsVariables.get(name, defaultValue)
	_VariableMutex.release()
	return ret

def set_variable(name, value):
	_VariableMutex.acquire()
	if name.startswith('PX_'):
		_SessionVariables[name] = value
	elif name.startswith('P_'):
		_AtsVariables[name] = value
	_VariableMutex.release()

################################################################################
# codec management: 'with' support
################################################################################

# with_ behaviour:
# when used in a template to match, first decode the received payload, then
# "returns" the decoded message struct.
#
# when used in a template to send, first encode the struct, then "returns" the
# encoded message.

def _encodeTemplate(template):
	if isinstance(template, CodecTemplate):
		return template.encode()

	if isinstance(template, list):
		ret = []
		for e in template:
			ret.append(_encodeTemplate(e))
		return ret
		
	if isinstance(template, dict):
		ret = {}
		for k, v in template.items():
			ret[k] = _encodeTemplate(v)
		return ret
	
	if isinstance(template, tuple):
		return (template[0], _encodeTemplate(template[1]))
	
	return template
	

def _expandTemplate(template):
	if isinstance(template, CodecTemplate):
		return template.getTemplate()

	if isinstance(template, list):
		ret = []
		for e in template:
			ret.append(_expandTemplate(e))
		return ret
		
	if isinstance(template, dict):
		ret = {}
		for k, v in template.items():
			ret[k] = _expandTemplate(v)
		return ret
	
	if isinstance(template, tuple):
		return (template[0], _expandTemplate(template[1]))
	
	return template


class CodecTemplate:
	"""
	This is a proxy template class.
	"""
	def __init__(self, codec, template):
		self._codec = codec
		self._template = template
	
	def encode(self):
		# Recursive encoding:
		# first encode what should be encoded within the template,
		# then encode it
		try:
			ret = TestermanCD.encode(self._codec, _encodeTemplate(self._template))
		except Exception:
			raise TestermanException('Encoding error: could not encode message with codec %s:\n%s' % (self._codec, getBacktrace()))
		if ret is None:
			# Codec not found
			raise TestermanException('Encoding error: codec %s not found' % self._codec)
		else:
			return ret
	
	def getTemplate(self):
		# recursive expansion
		return _expandTemplate(self._template)
		
	def decode(self, encodedMessage):
		# NB: no recursive decoding: let the calling templateMatch calls decode when needed
		# This way, the codec only decodes what it knows how to decode, and has no need
		# to know what other codecs are available.
		try:
			ret = TestermanCD.decode(self._codec, encodedMessage)
		except Exception:
			# Unable to decode: leave the buffer as is
			return encodedMessage
		if ret is None:
			# Codec not found - leave the buffer as is
			return encodedMessage
		else:
			return ret
			
# The main alias - final one TBD (with_codec ?)
class with_(CodecTemplate):
	pass

################################################################################
# Template matching
################################################################################

def templateMatch(message, template):
	"""
	A simple wrapper over _templateMatch to catch possible internal exceptions.

	@type  message: any object
	@param message: the encoded message, as received (may be structured, too)
	@type  template: any object suitable for a template
	@param template: the template to match. may contain references to coders and conditions. They are evaluated on time.
		
	@rtype: (bool, object)
	@returns: (a, b) where a is True if match, False otherwise, b is the decoded message (partially decoded in case of decoding error ?)
	"""
	try:
		(ret, decodedMessage) = _templateMatch(message, template)
	except Exception:
		# Actually, this is for debug purposes
		logUser("Exception while trying to match a template:\n%s" % getBacktrace())
		return (False, message)
	return (ret, decodedMessage)

def match(message, template):
	"""
	TTCN-3 match function.
	"""
	return templateMatch(message, template)[0]

def _templateMatch(message, template):
	"""
	Returns True if the message matches the template.
	Includes calls to decoders and comparators if present in template.
	
	@type  message: any python object, valid for a Testerman fully qualified message
	@param message: the message to match
	@type  template: any python object, valid for a Testerman template: may contains template proxies such as CodecTemplates and ConditionTemplates.
	@param template: the template to verify against the message
	
	@rtype: tuple (bool, object)
	@returns: (a, b) where a is the matching status (True/False), and b the decoded message (same type as @param message)
	"""
	# Support for dynamic templates
	if callable(template):
		template = template()

	# Match all
	if template is None:
		return (True, message)
	
	# CodecTemplate proxy template
	if isinstance(template, CodecTemplate):
		# Let's see if we can first decode the message
		try:
			decodedMessage = template.decode(message)
		except Exception, e:
			logInternal("mismatch: unable to decode message part with codec %s: %s" % (template._codec, str(e) + getBacktrace()))
			return (False, message)
		# TODO: handle decoding error here ?
		logInternal("_templateMatch: message part decoded with codec %s: %s" % (template._codec, repr(decodedMessage)))
		# Now match the decoded message against the proxied template (not expanded, because it should contain other proxies, if any)
		return _templateMatch(decodedMessage, template._template)
	
	# Structured type: dict
	# all entries in template dict must match ; extra message entries are ignored (but kept in "decoded dict")
	if isinstance(template, dict):
		if not isinstance(message, dict):
			logInternal("mistmatch: expected a dict")
			return (False, message)
		# Existing entries in template dict must be matched (excepting 'omit' entries, which must not be present...)
		decodedDict = {}
		result = True
		for key, tmplt in template.items():
			# any value or none, ie '*'
			if tmplt is None:
				continue
			if message.has_key(key):
				(ret, decodedField) = _templateMatch(message[key], tmplt)
				decodedDict[key] = decodedField
				if not ret:
					logInternal("mistmatch: mismatched dict entry %s" % unicode(key))
					result = False
					# continue to traverse the dict to perform "maximum" message decoding
			elif isinstance(tmplt, (omit, any_or_none, ifpresent)):
				# if the missing keys are omit(), that's ok.
				logInternal("omit: omitted value not found, or optional value not found. Great.")
				continue
			else:
				# if it's something else, missing key, so no match.
				logInternal("mistmatch: missing dict entry %s" % unicode(key))
				result = False
		# Now, add message keys that were not in template to the decoded dict
		for key, m in message.items():
			if not key in template:
				decodedDict[key] = m
		return (result, decodedDict)
	
	# Structured type: tuple (choice, value)
	# Must be the same choice name (ie tupe[0]) and matching value
	if isinstance(template, tuple):
		if not isinstance(message, tuple):
			logInternal("mistmatch: expected a tuple")
			return (False, message)
		# Check choice
		if not message[0] == template[0]:
			logInternal("mistmatch: tuple choice differs (message: %s, template %s)" % (unicode(message[0]), unicode(template[0])))
			return (False, message)
		# Check value
		(ret, decoded) = _templateMatch(message[1], template[1])
		return (ret, (message[0], decoded))

	# Structured type: list
	# This is a one-to-one exact match, ordered.
	# as a consequence, the same number of elements in template and message are expected,
	# unless we have some * in template.
	if isinstance(template, list):
		if not isinstance(message, list):
			logInternal("mistmatch: expected a list")
			return (False, message)
		
		# Wildcard (*) support:
		# match(message, *|template) =
		#  matched = False
		#  i = 0
		#  while not matched and message[i:]:
		#   matched = match(message[i:], template)
		(result, decodedList) = _templateMatch_list(message, template)
		return (result, decodedList)

		"""		
		decodedList = []
		# Ordered matching. All elements in templates must be matched, in the correct order.
		result = True
		i = 0
		messageLen = len(message)
		for tmplt in template:
			if i < messageLen:
				m = message[i]
				(ret, decodedEntry) = _templateMatch(m, tmplt)
				if not ret:
					# Not matched. Stop here.
					result = False
					decodedList.append(decodedEntry)
					logInternal("mistmatch: lists stopped matching at element %d" % i)
					# but still continue to display the complete message attempt in log
					# break
				else:
					# OK, first template element matched.
					# Continue with the next elements of both lists
					decodedList.append(decodedEntry)
				i += 1
			else:
				# We consumed our message
				break
		if not result or i < len(template):
			logInternal("mismatch: not all templates were matched")
			result = False
		else:
			result = True
		return (result, decodedList)
		"""

	# conditions: proxied templates	
	if isinstance(template, ConditionTemplate):
		# TODO: ConditionTemplate.match() should returns a decoded message, too
		return (template.match(message), message)
	
	# Simple types
	return (message == template, message)


def _templateMatch_list(message, template):
	"""
	both message and template are lists.
	
	Semi-recursive implementation.
	De-resursived on wildcard * only.
	"""
#	logInternal("Trying to match %s with %s" % (unicode(message), unicode(template)))
	# match(message, *|template) =
	#  matched = False
	#  i = 0
	#  while not matched and message[i:]:
	#   matched = match(message[i:], template)
	
	# [] can only be matched by [], [ * ]
	if not message:
		if not template or (len(template) == 1 and isinstance(template[0], any_or_none)):
#			logInternal("_templateMatch_list matched: [] against [] or [*]")
			return (True, [])
		else:
			return (False, [])

	# message not empty.
	if not template:
		# ... but template is
#		logInternal("_templateMatch_list mismatched: %s against %s" % (unicode(message), unicode(template)))
		return (False, message)
		
	th, tt = (template[0], template[1:])
	mh, mt = (message[0], message[1:])
	if isinstance(th, any_or_none):
		if not tt:
#			logInternal("_templateMatch_list matched: %s against %s ([*])" % (unicode(message), unicode(template)))
			return (True, message)
		matched = False
		decodedList = None
		i = 0
		while not matched and message[i:]:
			(matched, decodedList) = _templateMatch_list(message[i:], tt)
			i += 1
#		logInternal("_templateMatch_list res %s: %s against %s ([*])" % (matched, unicode(message), unicode(template)))
		return (matched, decodedList)
	else:
		# Recursive approach:
		# we match the same element first element, and the trailing list should match, too
		decodedList = []
		result = True
		(ret, decoded) = _templateMatch(mh, th)
		decodedList.append(decoded)
		if not ret:
#			logInternal("_templateMatch_list mismatched on first element: %s against %s " % (unicode(message), unicode(template)))
			result = False
			# Complete with undecoded message
			decodedList += mt
		else:
#			logInternal("_templateMatch_list matched on first element: %s against %s " % (unicode(message), unicode(template)))
			(ret, decoded) = _templateMatch_list(mt, tt)
			result = ret
			decodedList += decoded

#		logInternal("_templateMatch_list res %s: %s against %s ([*])" % (result, unicode(message), unicode(template)))
		return (result, decodedList)

################################################################################
# TRI interface - TE provided
################################################################################

def triEnqueueMsg(tsiPortId, sutAddress = None, componentId = None, message = None):
	"""
	TRI interface: TE provided.
	Enqueues a TRI-received message to the userland (i.e. the TE world).
	
	We retrieve the corresponding tsiPort and its mapped ports thanks to the tsiPortId,
	used as a key.
	
	@type  tsiPortId: string
	@param tsiPortId: the name of the test system interface port.
	@type  sutAddress: string
	@param sutAddress: the sutAddress the message arrives from
	@type  componentId: string
	@param componentId: the name of ?? (dest test component ?) - not used.
	@type  message: any valid testerman message
	@param message: the received message to enqueue to userland
	"""
	tsiPort = None
	_TsiPortsLock.acquire()
	if _TsiPorts.has_key(tsiPortId):
		tsiPort = _TsiPorts[tsiPortId]
	_TsiPortsLock.release()
	
	if tsiPort:
		logInternal("triEnqueueMsg: received a message for tsiPort %s. Enqueing it." % str(tsiPort))
		tsiPort._enqueue(message)
	else:
		# Late message ? just discard it.
		logInternal("triEnqueueMsg: received a message for unmapped tsiPort %s. Not delivering to userland, discarding." % str(tsiPortId))


################################################################################
# ATS Cancellation management
################################################################################

_AtsCancelled = False

def _cancel():
	"""
	Called when receiving a SIGINT by the TE.
	Flags a global variable so that the test case stops once the current testcase
	is over.
	"""
	global _AtsCancelled
	_AtsCancelled = True
	
def _isAtsCancelled():
	"""
	Returns True if the ATS is cancelled: we should not execute new testcases,
	but raise a TestermanCancelException instead.
	"""
	return _AtsCancelled
