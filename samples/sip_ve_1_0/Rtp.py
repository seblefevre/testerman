# __METADATA__BEGIN__
# <?xml version="1.0" encoding="utf-8" ?>
# <metadata version="1.0">
# <description>description</description>
# <prerequisites>prerequisites</prerequisites>
# <parameters>
# </parameters>
# </metadata>
# __METADATA__END__
##
# This file is a part of the SIP Virtual Endpoint component for Testerman.
#
# (c) Denis Machard and other contributors.
##

"""
This module enables to control one probe rtp. 
start/stop the probe; start/stop the rtp stream; start to play wav 

@date: 10/16/2008
"""

class Rtp:
	def __init__ (self, testCase, rtpPort, fromIp, fromPort, debug):
		"""
		Initialize the class Rtp
		
		@param testCase: ptc or mtc
		@param rtpPort: port mapped to a rtp binding
		@param fromIp: listening on ip 
		@type fromIp: string
		@param fromPort: listening on port
		@type fromPort: string
		@param debug: show logs
		@type debug: boolean
		"""
		self.rtpPort = rtpPort
		self.ipTo = None
		self.portTo = None
		self.fromIp = fromIp
		self.fromPort = int(fromPort)
		self.wav = None
		self.running = False
		self.sending = False
		self.debugMode = debug
		self.testCase = testCase # just to show logs
		
	def debug(self, text):
		"""
		This functions enables to show logs only when the debug is activated
		@param text: text information 
		@type text: string
		"""
		if self.debugMode:
			log(text)
			
	def reset(self):
		"""
		Reset the class and probe
		"""
		self.stopSending()
		self.stopListening()
		self.rtpPort = rtpPort
		self.ipTo = None
		self.portTo = None
		self.fromIp = fromIp
		self.fromPort = fromPort
		self.wav = None
		self.running = False
		self.sending = False
		
	def setPortFrom(self, port):
		"""
		@param port: 
		@type port:
		"""
		self.fromPort = int(port)
	def setIpTo (self, ip):
		"""
		Set the destination IP address
		
		@param ip: IP address (10.0.0.1)
		@type ip: string
		"""
		self.ipTo = ip
	
	def setPortTo (self, port):
		"""
		Set the destination port address
		
		@param port: UDP port (1 to 65536)
		@type port: string
		"""
		self.portTo = int(port)

	def startSending(self, codec, audioId):	
		"""
		Start to send rtp stream
		
		@param codec:
		@type codec:
		
		@param audioId:
		@type audioId:
		"""
		if self.sending == False:
			self.rtpPort.send( ('startSendingRtp', { 'toIp': self.ipTo, 
						'toPort': self.portTo,
						'fromIp': self.fromIp ,
						'fromPort': self.fromPort,
						'payloadType': codec ,
						'ssrc': audioId} ))
			self.sending = True
			self.debug('%s >> started sending RTP' % str(self.rtpPort) )
		
	
	def stopSending(self):
		"""
		Stop to send rtp stream
		"""
		if self.sending == True:
			self.rtpPort.send( ('stopSendingRtp', {}) )
			self.sending = False
			self.debug('%s >> stopped sending RTP' % str(self.rtpPort))
			
	def startListening(self):
		"""
		Start to listen on port UDP
		"""
		if self.running == False:
			self.rtpPort.send( ('startListeningRtp', { 'onPort': self.fromPort,
						'onIp': self.fromIp,
						'timeout': 0.500 } ))
			self.running = True
	def stopListening(self):
		"""
		Stop to listen on port UDP
		"""
		if self.running == True:
			self.rtpPort.send( ('stopListeningRtp', {} ) )
			self.running = False
			self.debug('%s >> stopped listening' % str(self.rtpPort))
		
	def playWavFile(self, resource, loopCount = 1): 
		"""
		Start to play a wave file
		
		@param resource: sample wave
		
		@param loop: the number of repeat play
		@type loop: integer
		"""
		self.rtpPort.send( ('play', { 'type': 'wav', 'payload': resource, 'loopCount': loopCount} ))
		self.debug('%s >> starting playing wav file' % str(self.rtpPort))			
