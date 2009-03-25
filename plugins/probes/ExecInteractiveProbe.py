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
import time
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
# The Interactive Exec Probe
##
class InteractiveExecProbe(ProbeImplementationManager.ProbeImplementation):
	"""

type union ExecCommand
{
	ExecuteCommand start,
	universal charstring input,
	int        signal,
}

type record ExecuteCommand
{
	charstring command,
	record of charstring patterns optional, // defaulted to [ .* ]
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

type charstring ErrorResponse;

type port ExecPortType message
{
	in  ExecCommand;
	out ExecStatus, OutputNotification;
}

	Properties:
	|| name || type || default || description ||
	|| `separator` || string || `None` || Should we notifies only complete lines based on this separator ? ||
	|| `timeout`|| real || `0.5` || maximum amount of time to wait for new data before notifying it whe no separator is used ||
	|| `encoding` || string || 'utf-8' || the encoding to use to turns the output to unicode ||

	Limitations:
	- No Windows platform support (for now)
	- Stderr is forwarded to stdout - no stream segregation
	- Interleaved stdout/stderr output are not garanteed to be delivered in the correct order
	
	Notes:
	- No need to make the executed program use unbuffered stdout.
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

import fcntl
import errno
import select

class Popen(subprocess.Popen):
	"""
	Subclassed to support non-blocking I/O.
	
	From http://code.activestate.com/recipes/440554
	
	WARNING: does not work with:
	- Windows (not yet)
	- Buffered programs
	"""
	def read_out(self, maxsize = None):
		return self._recv('stdout', maxsize)
	
	def read_err(self, maxsize = None):
		return self._recv('stderr', maxsize)
	
	def get_conn_maxsize(self, which, maxsize):
		if maxsize is None:
			maxsize = 1024
		elif maxsize < 1:
			maxsize = 1
		return getattr(self, which), maxsize
	
	def _close(self, which):
		getattr(self, which).close()
		setattr(self, which, None)
	
	def send_all(self, data):
		while data:
			written = self.send(data)
			data = data[written:]
	
	# Posix platform only - no windows support yet
	def send(self, data):
		if not self.stdin:
			return None
		_, w, _ = select.select([], [self.stdin], [], 0.5) # 500ms timeout
		if not w:
			return 0
		try:
			written = os.write(self.stdin.fileno(), data)
		except OSError, e:
			if e[0] == errno.EPIPE:
				return self._close('stdin')
			raise e
		return written

	def _recv(self, which, maxsize):
		conn, maxsize = self.get_conn_maxsize(which, maxsize)
		if conn is None:
			return None
		flags = fcntl.fcntl(conn, fcntl.F_GETFL)
		if not conn.closed:
			fcntl.fcntl(conn, fcntl.F_SETFL, flags | os.O_NONBLOCK)
		
		try:
			r, _, _ = select.select([conn], [], [], 0)
			if not r:
				return ''
			
			read = conn.read(maxsize)
			if not read:
				return self._close(which) # returns None
			
			if self.universal_newlines:
				read = self._translate_newlines(read)
			return read
		finally:
			if not conn.closed:
				fcntl.fcntl(conn, fcntl.F_SETFL, flags) # restore initial flags

	def read_out_err(self, timeout = 0.0, maxsize = None):
		connout, maxsizeout = self.get_conn_maxsize('stdout', maxsize)
		connerr, maxsizeerr = self.get_conn_maxsize('stderr', maxsize)
		flagsout = fcntl.fcntl(connout, fcntl.F_GETFL)
		flagserr = fcntl.fcntl(connerr, fcntl.F_GETFL)
		if not connout.closed:
			fcntl.fcntl(connout, fcntl.F_SETFL, flagsout | os.O_NONBLOCK)
		if not connerr.closed:
			fcntl.fcntl(connerr, fcntl.F_SETFL, flagserr | os.O_NONBLOCK)
		
		rlist = []
		if connout is not None:
			rlist.append(connout)
		if connerr is not None:
			rlist.append(connerr)
		
		try:
			r, _, _ = select.select(rlist, [], [], timeout)
			if not r:
				return ('', '')
			
			retout = None
			reterr = None
			if connout in r:
				read = connout.read(maxsizeout)
				if not read:
					retout = self._close('stdout') # returns None
				else:
					retout = read

			if connerr in r:
				read = connerr.read(maxsizeerr)
				if not read:
					reterr = self._close('stderr') # returns None
				else:
					reterr = read
			
			return (retout, reterr)
		finally:
			if not connout.closed:
				fcntl.fcntl(connout, fcntl.F_SETFL, flagsout) # restore initial flags
			if not connerr.closed:
				fcntl.fcntl(connerr, fcntl.F_SETFL, flagserr) # restore initial flags
		return (None, None)


# Experimental version to work around the buffered streams
import ssh.pexpect.pexpect as pexpect

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
			self._process = pexpect.spawn(self._command)
			self._process.setecho(False)
#			self._process = Popen(self._command, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
		except Exception, e:
			self._probe.triEnqueueMsg('Internal execution error: %s' % str(e))

		retcode = None
		"""
		while retcode is None:
			retcode = self._process.poll()
#			self._probe.getLogger().debug('Reading output...')
			stdout, stderr = self._process.read_out_err(self._timeout)
#			self._probe.getLogger().debug('Read output:\n%s\n%s' % (repr(stdout), repr(stderr)) )
			self.handleOutput(stdout, 'stdout')
			self.handleOutput(stderr, 'stderr')
			time.sleep(0.001)
		"""
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
#			self._process.send_all(input_.encode(self._encoding)) #self._process.stdin.write(input_)
			
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
					event = { 'stream': stream, 'output': buf } # Should we strip the line ?
					for k, v in m.groupdict().items():
						event['matched_%s' % k] = v
					self._probe.triEnqueueMsg(event)			
			buf = ''

ProbeImplementationManager.registerProbeImplementationClass("exec.interactive", InteractiveExecProbe)
