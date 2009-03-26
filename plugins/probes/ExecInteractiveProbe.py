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
import threading
import time
import sys
import glob
import re
import struct

import ssh.pexpect.pexpect as pexpect


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
# The Interactive Exec Probe
##
class InteractiveExecProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	= Identification and Properties =

	Probe Type ID: `exec.interactive`

	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	|| `separator` || string || `None` || should we notify only complete lines (or whatever) based on this separator ? ||
	|| `timeout`|| float || `0.5` || maximum amount of time to wait for new data before notifying of it, when no separator is used ||
	|| `encoding` || string || `'utf-8'` || the encoding to use to turns the output into unicode (also used to encode data sent to the started process) ||


	= Overview =

	This probe enables to execute a shell-based program interactively, i.e. start a program, be notified of what
	it outputs to standard output (stdout, stderr), send it some input or signals.
	
	Output can be notified on a per-line basis (or any separator - the separator is not included in the event 
	sent back to the userland) or a timeout basis (useful if the program does not outputs lines only, for instance
	prompts).
	
	This probe does not require the started program to use unbuffered stdout.
	
	Typical use cases include:
	 * CLI testing
	 * Program output watching, for instance something that can dump real-time traces to stdout, avoiding the use of
	combined `exec` (that executes a blocking program whose output is redirected to a temp file) and `file.watcher`
	(that watches the temp file created by the program we should watch the output from) probes.

	Basically you just specify a command to start that will be executed within a shell, providing an optional
	list of regular expressions the output must match before being sent to userland (a `egrep` equivalent).[[BR]]
	Whenever you output to stdout/stderr is detected, based on `separator` and `timeout` properties, it checks that
	it matches at least one of the regular expressions provided above before enqueing a `OutputNotification` message
	to userland. If the matched regular expression contains named groups, corresponding fields are automatically
	added in this message (as for the WatcherFileProbe).
	
	At any time, you may send some input to the started process using the `input` choice of the `InteractiveExecCommand`
	message (don't forget possible trailing carriage returns, as they are not sent automatically) or send a
	signal using its POSIX integer value and the `signal` choice of the `InteractiveExecCommand` message.
	
	When the process is over (for whatever reason), a `ExecStatus` message is enqueued, containing the execution status
	as a shell executing the command would have provided.
	
	Limitations:
	 * stderr output is currently reported within the stdout stream
	 * interleaved stdout/stderr output are not garanteed to be delivered in the correct order
	
	== Availability ==

	All POSIX platforms. Windows platforms are not supported.

	== Dependencies ==

	None.

	== See Also ==

	 * ExecProbe, a single shoot command, non-interactive execution.


	= TTCN-3 Types Equivalence =

	The test system interface port bound to such a probe complies with the `InteractiveExecPortType` port type as specified below:
	{{{
	type union InteractiveExecCommand
	{
		StartCommand start,
		universal charstring input,
		integer signal,
	}

	type record StartCommand
	{
		charstring command,
		record of charstring patterns optional, // defaulted to [ r'.*' ]
	}

	type record OutputNotification
	{
		universal charstring output,
		universal charstring matched_*,
		charstring stream, // 'stderr' or 'stdout'
	}

	type record ExecStatus
	{
		integer status,
	}

	type port InteractiveExecPortType message
	{
		in  InteractiveExecCommand;
		out ExecStatus, OutputNotification;
	}
	}}}

	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()
		self._execThread = None
		self.setDefaultProperty('separator', None)
		self.setDefaultProperty('timeout', 0.5)
		self.setDefaultProperty('encoding', 'utf-8')

	# ProbeImplementation reimplementation

	def onTriUnmap(self):
		self.getLogger().debug("onTriUnmap()")
		self.kill()

	def onTriMap(self):
		self.getLogger().debug("onTriMap()")
		self.kill()
	
	def onTriSAReset(self):
		self.getLogger().debug("onTriSAReset()")
	
	def onTriExecuteTestCase(self):
		self.getLogger().debug("onTriExecuteTestCase()")

	def onTriSend(self, message, sutAddress):
		"""
		"""
		self.getLogger().debug("onTriSend(%s, %s)" % (unicode(message), unicode(sutAddress)))

		if not (isinstance(message, tuple) or isinstance(message, list)) and not len(message) == 2:
			raise Exception("Invalid message format")
		
		cmd, args = message

		if cmd == 'start':
			self._checkArgs(args, [('patterns', [ r'.*' ]), ('command', None)])
			compiledPatterns = [ re.compile(x) for x in args['patterns']]
			self.startCommand(args['command'], compiledPatterns)
		elif cmd == 'signal':
			self.sendSignal(args)
		elif cmd == 'input':
			self.sendInput(args)
		else:
			raise Exception("Unsupported command (%s)" % cmd)
		
	# Specific implementation
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()			
	
	def kill(self):
		"""
		Kills an existing command, if any.
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

	def startCommand(self, command, compiledPatterns):
		"""
		Starts a command in a subprocess/thread.
		Returns immediately.
		"""
		self._lock()
		try:
			execThread = self._execThread
			if execThread:
				raise Exception("Another command is currently being executed. Please kill it first.")

			# Now start our dedicated thread.
			self._execThread = ExecThread(self, command, compiledPatterns)
			self._execThread.start()
		except Exception, e:
			self._unlock()
			raise e
		
		self._unlock()
	
	def sendSignal(self, signal):
		self._lock()
		execThread = self._execThread
		self._unlock()
		if execThread:
			self._execThread.sendSignal(signal)
		
	def sendInput(self, input_):
		self._lock()
		execThread = self._execThread
		self._unlock()
		if execThread:
			self._execThread.sendInput(input_)

	def _onExecThreadTerminated(self):
		"""
		Called by the ExecThread once over.
		"""
		self._lock()
		self._execThread = None
		self._unlock()


class ExecThread(threading.Thread):
	"""
	Executes a command in a subprocess, leaving std streams available for interactions.
	"""
	def __init__(self, probe, command, compiledPatterns):
		threading.Thread.__init__(self)
		self._probe = probe
		self._command = command
		self._patterns = compiledPatterns
		self._process = None
		self._mutex = threading.RLock()
		self._reportStatus = True
		self._stoppedEvent = threading.Event()
		self._buffer = { 'stdout': '', 'stderr': '' }
		self._separator = self._probe['separator']
		self._timeout = self._probe['timeout']
		if self._separator:
			self._timeout = 0.0
		self._encoding = self._probe['encoding']
	
	def run(self):
		self._probe.getLogger().debug("Starting command execution thread...")
		try:
			if isinstance(self._command, list):
				self._process = pexpect.spawn(self._command[0], self._command[1:])
			else: # Assume this is a string
				self._process = pexpect.spawn(self._command)
			self._process.setwinsize(24, 80)
		except Exception, e:
			self._probe.triEnqueueMsg('Internal execution error: %s' % ProbeImplementationManager.getBacktrace())

		retcode = None
		alive = True
		while alive:
			alive = self._process.isalive()
			try:
				r = self._process.read_nonblocking(1024, self._timeout)
				self.handleOutput(r, 'stdout')
			except:
				time.sleep(0.001)

		self._process.close()
		retcode = self._process.status
			
		self._process = None

		self._probe._onExecThreadTerminated()
		if self.getReportStatus():
			self._probe.triEnqueueMsg({ 'status': retcode })
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
	
	def sendSignal(self, s):
		if self._process:
			pid = self._process.pid
			pids = getChildrenPids(pid)
			self._probe.getLogger().info("Sending signal %s to process %s (%s) on user demand..." % (s, pid, pids))
			for p in pids:
				try:
					os.kill(p, s)
				except Exception, e:
					self._probe.getLogger().warning("Unable to send signal %s to process %s: %s" % (s, pid, str(e))) 
	
	def sendInput(self, input_):
		if self._process:
			self._probe.getLogger().debug("Sending input to process: %s" % repr(input_))

			data = input_.encode(self._encoding)
			while data:
				written = self._process.send(data)
				data = data[written:]
	
	def handleOutput(self, data, stream):
		if not data:
			return
		try:
			data = data.decode(self._encoding)
		except Exception, e:
			self._probe.getLogger().warning('Invalid encoding scheme on output %s (%s):\n%s' % (stream, str(e), repr(data)))
			return
		
		self._probe.getLogger().debug('Got some input on %s: (%s)' % (stream, repr(data))) 
		buf = self._buffer[stream]
		buf += data

		if self._separator:
			msgs = buf.split(self._separator)
			for msg in msgs[:-1]:
				for pattern in self._patterns:
					m = pattern.match(msg)
					if m:
						event = { 'stream': stream, 'output': msg }
						for k, v in m.groupdict().items():
							event['matched_%s' % k] = v
						self._probe.triEnqueueMsg(event)			
			buf = msgs[-1]
		else:
			# No separator management. Notifies things as is.
			for pattern in self._patterns:
				m = pattern.match(buf)
				if m:
					event = { 'stream': stream, 'output': buf }
					for k, v in m.groupdict().items():
						event['matched_%s' % k] = v
					self._probe.triEnqueueMsg(event)			
			buf = ''

ProbeImplementationManager.registerProbeImplementationClass("exec.interactive", InteractiveExecProbe)
