##
# SSH probe stub.
#
# Converts TSI messages to low-level messages over Ia/Xa
#
##

import TestermanSA
import TestermanAgentControllerClient as TACC

class SshProbeStub(TestermanSA.RemoteProbe):
	def __init__(self):
		TestermanSA.RemoteProbe.__init__(self)
	
	def onTriExecuteTestCase(self):
		pass
	
	def onTriSAReset(self):
		pass

	def onTriMap(self):
		self.reset()
	
	def onTriUnmap(self):
		self.reset()
	
	def send(self, message, sutAddress):
		"""
		Minimal conversion, and probe static parameters inclusion.
		"""
		if not isinstance(message, tuple) and not len(message) == 2:
			raise Exception("Invalid message format")
		
		cmd, value = message
		if cmd == 'execute':
			m = { 'cmd': 'execute', 'command': value, 'host': self['host'], 'username': self['username'], 'password': self['password'] }
		elif cmd == 'cancel':
			m = { 'cmd': 'cancel' }
		else:
			raise Exception("Invalid message format")
		
		TACC.instance().send(self.getUri(), m, sutAddress)
		
	def reset(self):
		TACC.instance().reset(self.getUri())
		
TestermanSA.registerProbeClass("remote.ssh", SshProbeStub)
