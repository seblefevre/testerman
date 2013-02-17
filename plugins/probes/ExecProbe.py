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
# A probe that can execute a command locally.
# May be used as a replacement for machines that do not have
# an SSH server or whose remote accesses are not possible.
#
##

import ProbeImplementationManager

import os
import signal
import subprocess
import threading
import sys
import glob
import re
import struct

##
# Tools: get a whole process tree (as a flat list of pids)
##

def parseStatusFile_linux(filename):
	pid_ = None
	ppid_ = None
	try:
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
	except Exception, e:
		pass
	return (pid_, ppid_)

def parseStatusFile_solaris(filename):
	"""
	according to /usr/include/sys/procfs.h
	
	typedef struct pstatus {
        int     pr_flags;       /* flags (see below) */
        int     pr_nlwp;        /* number of active lwps in the process */
        pid_t   pr_pid;         /* process id */
        pid_t   pr_ppid;        /* parent process id */
	...
	}
	
	int are 64 or 32 depending on the platform...
	
	This implementation only support 64 bit (for now).
	"""
	pid_ = None
	ppid_ = None
	try:
		f = open(filename)
		buf = f.read()
		f.close()
		
		(_, _, pid_, ppid_) = struct.unpack('IIII', buf[:struct.calcsize('IIII')])
	except:
		pass
	return (pid_, ppid_)

def parseStatusFile(filename):
	"""
	Parse a /proc/<pid>/status file,
	according to the current OS.
	
	@rtype: tuple of int 
	@returns: pid, ppid (any of those may be None if not parsed)
	
	Supported:
	- Linux 2.6.x
	- Solaris
	"""
	if sys.platform in [ 'linux', 'linux2' ]:
		return parseStatusFile_linux(filename)
	elif sys.platform in [ 'sunos5' ]:
		return parseStatusFile_solaris(filename)
	else:
		return (None, None)

def getChildrenPids(pid):
	"""
	Retrieves all the children pids for a given pid, 
	including the pid itself as the first element of the returned list of PIDs

	Returns them as a list.
	
	WARNING: only Linux and Solaris-compatible for now,
	as it relies on /proc/<pid>/status pseudo file.
	
	@type  pid: int
	@param pid: the parent pid whose we should retrieve children
	
	@rtype: list of int
	@returns: first the pid itself, then its children's pids
	"""
	pids = [] # a list of current (pid, ppid)
	# Let's scan /proc/...
	# No other way to do it ?
	statusFilenames = glob.glob("/proc/[0-9]*/status")
	for filename in statusFilenames:
		try:
			pid_, ppid_ = parseStatusFile(filename)
			if pid_ and ppid_:
				pids.append( (pid_, ppid_) )
		except Exception, e:
			pass
	
	# Now let's construct the tree for the looked up pid
	ret = [ pid ]
	ppids = [ pid ]
	while ppids:
		currentPpid = ppids.pop()
		for (pid_, ppid_) in pids:
			if ppid_ == currentPpid:
				if pid_ not in ppids: ppids.append(pid_)
				if pid_ not in ret: ret.append(pid_)
	
	return ret

##
# The Exec Probe
##
class ExecProbe(ProbeImplementationManager.ProbeImplementation):
	"""
Identification and Properties
-----------------------------

Probe Type ID: ``exec``

Properties:

.. csv-table::
   :header: "Name","Type","Default value","Description"

   "``shell``","string","``None``","The shell to use when executing the command line. On Unixes, this is defaulted to ``/bin/sh``, on Windows, this is the shell as specified via the COMSPEC environment variable."

Overview
--------

This probe implements a single shot command execution interface (the same as ProbeSsh) for locally executed
commands.

Basically you just specify a command to execute that will be executed within a shell, and you get a response
once its execution is over. The response contains both an integer return code and the whole command output.

If you consider the command execution is too long (no response received), you can cancel it at any time from the
userland. Such a cancellation terminates all the subprocess tree with a SIGKILL signal on POSIX platforms,
and a SIGTERM to the started process (not all its subtree) on Windows. Once cancelled, you should not expect
a command response anymore.

No interaction is possible during the command execution.

Notes:

 * when starting daemons from this probe, make sure that your daemon correctly closes standard output, otherwise
   the probe never detects the command as being complete.

Availability
~~~~~~~~~~~~

All platforms. Tested on Linux (kernel 2.6), Solaris 8, Solaris 10.

Dependencies
~~~~~~~~~~~~

None.

See Also
~~~~~~~~

 * :doc:`ProbeSsh`, implementing the same port type for execution through SSH (avoiding the installation of an agent
   on the target machine)
 * :doc:`ProbeExecInteractive`, to run a command line program and interact with it (CLI testing, etc)

TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the ``ExecPortType`` port type as specified below:

::

  type union ExecCommand
  {
    charstring execute,
    anytype    cancel
  }
  
  type record ExecResponse
  {
    integer status,
    charstring output
  }
  
  type charstring ErrorResponse;
  
  type port ExecPortType message
  {
    in  ExecCommand;
    out ExecResponse, ErrorResponse;
  }
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()
		self._execThread = None
		self.setDefaultProperty("shell", None)

	# ProbeImplementation reimplementation

	def onTriUnmap(self):
		self.getLogger().debug("onTriUnmap()")
		self.cancelCommand()

	def onTriMap(self):
		self.getLogger().debug("onTriMap()")
		self.cancelCommand()
	
	def onTriSAReset(self):
		self.getLogger().debug("onTriSAReset()")
	
	def onTriExecuteTestCase(self):
		self.getLogger().debug("onTriExecuteTestCase()")

	def onTriSend(self, message, sutAddress):
		"""
		Internal probe message:
		
		{ 'cmd': 'execute', 'command': string, 'host': string, 'username': string, 'password': string, [ 'timeout': float in s, 5.0 by default ] }
		{ 'cmd': 'cancel' }
		
		The timeout is the maximum amount of time allowed to connect and start executing the command.
		The command itself may last forever.
		
		"""
		self.getLogger().debug("onTriSend(%s, %s)" % (unicode(message), unicode(sutAddress)))

		if not (isinstance(message, tuple) or isinstance(message, list)) and not len(message) == 2:
			raise Exception("Invalid message format")
		
		cmd, value = message
		if cmd == 'execute':
			m = { 'cmd': 'execute', 'command': value }
		elif cmd == 'cancel':
			m = { 'cmd': 'cancel' }
		else:
			raise Exception("Invalid message format")

		try:
			self._checkArgs(m, [ ('cmd', None) ])
			cmd = m['cmd']

			if cmd == 'cancel':
				return self.cancelCommand()
			elif cmd == 'execute':
				self._checkArgs(m, [ ('command', None) ])
				command = m['command']

				try:
					self.executeCommand(command)
				except Exception, e:
					self.triEnqueueMsg(str(e))

		except Exception, e:
			raise ProbeImplementationManager.ProbeException(self._getBacktrace())
		
	# Specific implementation
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()			
	
	def cancelCommand(self):
		"""
		Cancels an existing command, if any.
		Does nothing if no pending command.
		"""
		self._lock()
		execThread = self._execThread
		self._unlock()
		
		if execThread:
			self.getLogger().debug('Cancelling...')
			try:
				execThread.stop()
				self.getLogger().info('Execution thread stopped')
			except Exception, e:
				self.getLogger().error('Error while cancelling the pending execution thread: %s' % str(e))
		# Nothing to do if no pending thread.
		self.getLogger().debug('execThread is now %s' % self._execThread)

	def executeCommand(self, command):
		"""
		Executes a command.
		Returns immediately.
		"""
		self._lock()
		try:
			execThread = self._execThread
			if execThread:
				raise Exception("Another command is currently being executed. Please cancel it first.")

			# Now start our dedicated thread.
			self._execThread = ExecThread(self, command)
			self._execThread.start()
		except Exception, e:
			self._unlock()
			raise e
		
		self._unlock()

	def _onExecThreadTerminated(self):
		"""
		Called by the ExecThread once over.
		"""
		self._lock()
		self._execThread = None
		self._unlock()
	


class ExecThread(threading.Thread):
	"""
	Executes a command through ssh in its own thread.
	Created and started on command execution, once the login phase was OK.
	"""
	def __init__(self, probe, command):
		threading.Thread.__init__(self)
		self._probe = probe
		self._command = command
		self._process = None
		self._mutex = threading.RLock()
		self._reportStatus = True
		self._stoppedEvent = threading.Event()
	
	def run(self):
		self._probe.getLogger().debug("Starting command execution thread...")
		output = None
		status = None
		try:
			self._process = subprocess.Popen(self._command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, executable=self._probe["shell"])
			output, _ = self._process.communicate()
			status = self._process.returncode
		except Exception, e:
			self._probe.triEnqueueMsg('Internal execution error: %s' % str(e))
		
		self._process = None

		self._probe._onExecThreadTerminated()
		if self.getReportStatus():
			self._probe.triEnqueueMsg({ 'status': status, 'output': output })
		self._stoppedEvent.set()

	def getReportStatus(self):
		self._mutex.acquire()
		r = self._reportStatus
		self._mutex.release()
		return r
	
	def setReportStatus(self, r):
		self._mutex.acquire()
		self._reportStatus = r
		self._mutex.release()
		
	def stop(self):
		# When explicitely stopped, we should not send a status/output back.
		if self._process:
			self.setReportStatus(False)
			pid = self._process.pid
			pids = getChildrenPids(pid)
			self._probe.getLogger().info("Killing process %s (%s) on user demand..." % (pid, pids))
			s = signal.SIGKILL
			if sys.platform in [ 'win32', 'win64' ]:
				s = signal.SIGTERM
			for p in pids:
				try:
					os.kill(p, s)
				except Exception, e:
					self._probe.getLogger().warning("Unable to kill process %s: %s" % (pid, str(e))) 
		# And we should wait for a notification indicating that the process
		# has died...
		# We wait at most 1s. Maybe the process was not killed
		# (in case of blocking IO for instance), but this should be rare cases
		# and this will lead to an error later in next command execution.
		# So the user wil figure it out soon.
		self._stoppedEvent.wait(1.0)
		


ProbeImplementationManager.registerProbeImplementationClass("exec", ExecProbe)
