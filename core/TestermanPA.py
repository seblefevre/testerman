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
# -*- coding: utf-8 -*-
# First implementation:
# Using Threading.Timer.
# Not scalable (max ~ 30 timers).
#
# Testerman TRI implementation - Platform Interface part.
#
##


import TestermanTCI
import TestermanTTCN3 as Testerman

import threading
import signal
import os
import re
import glob
import time


TRI_OK = 1
TRI_Error = 0

def log(message):
	TestermanTCI.logInternal("PA: %s" % str(message))



PaMutex = None

CurrentTimers = {} # { 'timer': threading.Timer, 'start': timestamp } indexed by the TE timerId

def _lock():
	PaMutex.acquire()

def _unlock():
	PaMutex.release()

def _onTimeout(timerId):
	_lock()
	if not CurrentTimers.has_key(timerId):
		_unlock()
		log("Timeout received on unexisting timerId. Ignoring")
		return
	del CurrentTimers[timerId]
	_unlock()
	Testerman.triTimeout(timerId)

################################################################################
# tri interface: PA-provided (TE -> PA)
################################################################################

def triPAReset():
	"""
	Returns 1 (TRI_OK) or 0 (TRI_Error)
	"""
	return TRI_OK

def triStartTimer(timerId, duration):
	"""
	Returns 1 (TRI_OK) or 0 (TRI_Error)
	"""
	log("triStartTimer(%s, duration %f)" % (str(timerId), duration))
	
	# We should check that timerId is not already used
	_lock()
	
	t = threading.Timer(duration, lambda: _onTimeout(timerId))
	CurrentTimers[timerId] = { 'timer': t, 'start': time.time() }
	_unlock()
	t.start()
	
	return TRI_OK
	
def triStopTimer(timerId):
	"""
	Returns 1 (TRI_OK) or 0 (TRI_Error)
	"""
	_lock()
	if not CurrentTimers.has_key(timerId):
		_unlock()
		return TRI_Error
	try:
		CurrentTimers[timerId].cancel()
	except:
		pass
	del CurrentTimers[timerId]
	_unlock()
	return TRI_OK

def triTimerRunning(timerId):
	"""
	@rtype: bool
	@returns: True if the timer is started
	"""
	ret = False
	_lock()
	if CurrentTimers.has_key(timerId):
		ret = True
	_unlock()
	return ret

def triReadTimer(timerId):
	"""
	@rtype: float
	@returns: the number of s since timer start
	"""
	ret = 0.0
	_lock()
	if CurrentTimers.has_key(timerId):
		ret = time.time() - CurrentTimers[timerId]['start']
	_unlock()
	return ret


################################################################################
# Platform Adapter tools
################################################################################


def getChildrenPids(pid, includeParent = False):
	"""
	Convenience function: retrieves all the children pids for a pid, including the pid itself.
	Returns them at a list.
	"""

	pids = [] # a list of current (pid, ppid)
	# Let's scan /proc/...
	# No other way to do it ?
	statusFilenames = glob.glob("/proc/[0-9]*/status")
	for filename in statusFilenames:
		try:
			pid_ = None
			ppid_ = None
			f = open(filename)
			lines = f.readlines()
			f.close()
			for line in lines:
				if not pid_:
					m = re.match(r'Pid:\s+(.*)', line)
					if m:
						pid_ = int(m.group(1))
				elif not ppid_:
					m = re.match(r'PPid:\s+(.*)', line)
					if m:
						ppid_ = int(m.group(1))
				elif ppid_ and pid_:
					break
			if pid_ and ppid_:
				pids.append( (pid_, ppid_) )
		except:
			pass
	
#	print "DEBUG: list of current process ids: " + str(pids)
	
	# Now let's construct the tree for the looked up pid
	if includeParent:
		ret = [ pid ]
	else:
		ret = []

	ppids = [ pid ]
	
	while ppids:
		currentPpid = ppids.pop()
		for (pid_, ppid_) in pids:
			if ppid_ == currentPpid:
				if pid_ not in ppids: ppids.append(pid_)
				if pid_ not in ret: ret.append(pid_)
	
#	print "DEBUG: global list of children: " + str(ret)
	return ret

def killChildren():
	"""
	Kill all its own children.
	Useful to make sure, at the end of a TE, that no subprocesses remain
	(may be created by some local probes).
	"""
	for pid in getChildrenPids(os.getpid(), includeParent = False):
		try:
			print "DEBUG: %d killing %d..." % (os.getpid(), pid)
			os.kill(pid, signal.SIGKILL)
		except:
			pass
	

################################################################################
# General Functions
################################################################################

def initialize():
	"""
	Initialize the PA
	"""
	global PaMutex

	log("Initializating PA...")
	PaMutex = threading.RLock()	
	log("PA initialized")
	
def finalize():
	"""
	TODO
	"""
	log("finalizing timer engine...")
	log("timer engine finalized.")
	

