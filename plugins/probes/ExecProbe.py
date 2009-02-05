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

class ExecProbe(ProbeImplementationManager.ProbeImplementation):
	"""

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

	Properties:
	None for now (user/uid one day ?)

	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()
		self._execThread = None

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
		self._stoppedEvent = threading.Event()
	
	def run(self):
		self._probe.getLogger().debug("Starting command execution thread...")
		output = None
		status = None
		try:
			self._process = subprocess.Popen(self._command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
			output, _ = self._process.communicate()
			status = self._process.returncode
		except Exception, e:
			self._probe.triEnqueueMsg('Internal execution error: %s' % str(e))
		
		self._process = None
		self._probe.triEnqueueMsg({ 'status': status, 'output': output })

		self._stoppedEvent.set()
		self._probe._onExecThreadTerminated()
			
	def stop(self):
		if self._process:
			os.kill(self._process.pid, signal.SIGKILL)
		# And we should wait for a notification indicating that the process
		# has died...
		# We wait at most 1s. Maybe the process was not killed
		# (in case of blocking IO for instance), but this should be rare cases
		# and this will lead to an error later in next command execution.
		# So the user wil figure it out soon.
		self._stoppedEvent.wait(1.0)
		


ProbeImplementationManager.registerProbeImplementationClass("exec", ExecProbe)
