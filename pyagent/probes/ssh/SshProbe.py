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
# A probe managing SSH-based command executions.
##

import PyTestermanAgent as Agent

import sys
import os
import pexpect.pxssh
import threading

class SshProbe(Agent.Probe):
	"""

type union SshCommand
{
	charstring execute,
	anytype    cancel
}

type record SshResponse
{
	integer status,
	charstring output
}

type charstring ErrorResponse;

type port SshPortType message
{
	in  SshCommand;
	out SshResponse, ErrorResponse;
}

	"""
	def __init__(self):
		Agent.Probe.__init__(self)
		self._mutex = threading.RLock()
		self._sshThread = None

	# Probe reimplementation

	def onReset(self):
		self.getLogger().debug("onReset()")
		self.cancelCommand()

	def onSend(self, message, sutAddress):
		"""
		Internal SSH probe message:
		
		{ 'cmd': 'execute', 'command': string, 'host': string, 'username': string, 'password': string, [ 'timeout': float in s, 5.0 by default ] }
		{ 'cmd': 'cancel' }
		
		The timeout is the maximum amount of time allowed to connect and start executing the command.
		The command itself may last forever.
		
		"""
		self.getLogger().debug("onSend(%s, %s)" % (unicode(message), unicode(sutAddress)))
		try:
			self.checkArgs(message, [ ('cmd', None) ])
			cmd = message['cmd']

			if cmd == 'cancel':
				return self.cancelCommand()
			elif cmd == 'execute':
				self.checkArgs(message, [ ('command', None), ('host', None), ('username', None), ('password', None), ('timeout', 5.0) ])
				command = message['command']
				host = message['host']
				username = message['username']
				password = message['password']
				timeout = message['timeout']

				try:
					self.executeCommand(command, username, host, password, timeout)
				except Exception, e:
					self.notifyReceived(str(e))

		except Exception, e:
			raise Agent.ProbeException(str(e))
		
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
		sshThread = self._sshThread
		self._unlock()
		
		if sshThread:
			self.getLogger().debug('Cancelling...')
			try:
				sshThread.stop()
				sshThread.join(3.0)
				self.getLogger().debug('SSH thread stopped')
			except Exception, e:
				self.getLogger().error('Error while cancelling the pending SSH thread: %s' % str(e))
		# Nothing to do if no pending thread.

	def executeCommand(self, command, username, host, password, timeout):
		"""
		Executes a command.
		Only returns when the command has been started, or raises an exception on error.
		"""
		self._lock()
		try:
			sshThread = self._sshThread
			if sshThread:
				raise Exception("Another command is currently being executed. Please cancel it first.")

			# Make sure no askpass will be displayed
			if os.environ.has_key('DISPLAY'):
				del os.environ['DISPLAY']
			ssh = pexpect.pxssh.pxssh()

			if not ssh.login(host, username, password, login_timeout = timeout):
				raise Exception("Unable to login: incorrect password, unreachable host, timeout during negotiation")

			# OK, we're logged in.
			# Now start our dedicated thread.
			self._sshThread = SshThread(self, ssh, command)
		except Exception, e:
			self._unlock()
			raise e
		
		self._unlock()
		self._sshThread.start()

	def onSshThreadTerminated(self):
		self._lock()
		self._sshThread = None
		self._unlock()
	


class SshThread(threading.Thread):
	"""
	Executes a command through ssh in its own thread.
	Created and started on command execution, once the login phase was OK.
	"""
	def __init__(self, probe, ssh, command):
		threading.Thread.__init__(self)
		self._probe = probe
		self._command = command
		self._ssh = ssh
		self._stopEvent = threading.Event()
	
	def run(self):
		self._probe.getLogger().debug("Starting command execution thread...")
		output = None
		status = None
		try:
			self._ssh.sendline(self._command)
			# Wait for a command completion
			while not self._stopEvent.isSet():
				if self._ssh.prompt(0.1):
					# We got a completion
					output = '\n'.join(self._ssh.before.split('\n')[1:])
					self._ssh.sendline('echo $?')
					self._ssh.prompt()
					# 'before' contains: line 0: echo $? , line 1: the echo output
					status = int(self._ssh.before.split('\n')[1].strip())
					self._ssh.logout()
					break
		except Exception, e:
			self._probe.notifyReceived('Internal SSH error: %s' % str(e))
			
		if status is not None:
			# We stopped on command completion
			self._probe.notifyReceived({ 'status': status, 'output': output })
		# Otherwise, we stopped on cancel - nothing to raise.

		# Kill the ssh session, if still active for wathever reason
		try:
			self._ssh.terminate()
		except:
			pass
		self._probe.onSshThreadTerminated()
			

	def stop(self):
		self._stopEvent.set()


Agent.registerProbeClass("remote.ssh", SshProbe)
