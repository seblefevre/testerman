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
An Encoder/Decoder of SDP messages + a function to negotiate codecs 

@date: 12/29/2008
"""

class Sdp:
	def __init__ (self, versionSdp, versionIp, userName, sessionName):
		"""
		Initialize the class Sdp 
		
		@param versionSdp: 0 or more
		@type versionSdp: string
		
		@param versionIp: IP4 / IP6
		@type versionIp: string
		
		@param userName: owner
		@type userName: string
		
		@param sessionName: session name 
		@type sessionName: string
		"""
		self.versionIp = versionIp
		self.versionSdp = versionSdp
		self.sessionId = '1'
		self.sessionVersion = '1'
		self.userName = userName
		self.sessionName = sessionName
		self.codecMap = { 0: 'PCMU/8000',
											3: 'GSM/8000',
											4: 'G723/8000',
											8: 'PCMA/8000', 
											18: 'G729/8000',
											34: 'H263/90000',
											97: 'H264/90000',
											99: 'H263-1998/90000',
											100: 'MP4V-ES/90000',
											101: 'telephone-event/8000'
										}
		self.protos = ['RTP/AVP']
		self.defaultCodec = 'PCMA/8000'
		self.codecsSupported = None
		# sdp template
		self.sdpOffer = None
		self.sdpOfferNull = None
		self.sdpAnswer = None
		self.sdpAnswerReInvite = None
		#
		self.sdpOfferReceived = False
		self.sdpOfferSended = False
		self.sdpAnswerReceived = False
		self.sdpAnswerSended = False
		self.sdpReceived = None
		self.portUsed = None
		self.ipUsed = None
		
	def setSdpAnswerSended(self):
		self.sdpAnswerSended = True
	def setSdpOfferReceived(self):
		self.sdpOfferReceived = True
	def setSdpOfferSended(self):
		self.sdpOfferSended = True
	def setSdpTemplate(self, ip, port, codecs):
		self.codecsSupported = codecs
		self.portUsed = port
		self.ipUsed = ip
		self.sdpOffer = { 'ownerAddress': str(ip),
											'connectionAddress': str(ip),
											'sessionAttribute': 'sendrecv',
											'mediaDescription': [ { '__type': 'audio',
																							'__port': int(port),
																							'__proto':  'RTP/AVP',
																							'__codecs': codecs
																						}
																					] 
										}
		self.sdpOfferNull = { 'ownerAddress': str(ip),
											'connectionAddress': '0.0.0.0',
											'mediaDescription': [ { '__type': 'audio',
																							'__port': int(port),
																							'__proto':  'RTP/AVP',
																							'__codecs': codecs,
																							'__attribute':'sendonly'
																						}
																					] 
										}	
		self.sdpAnswer = { 'ownerAddress': str(ip),
											'connectionAddress': str(ip),
											'sessionAttribute': 'sendrecv',
											'mediaDescription': [] 
										}		
		self.sdpAnswerReInvite = { 'ownerAddress': str(ip),
																'connectionAddress': str(ip),
																'sessionAttribute': 'sendrecv',
																'mediaDescription': [] 
															}		
	def decodeSdpAndNegociateCodec(self, sdp):
		self.resetSdpAnswer()
		sdpNegociated = False
		self.sdpAnswerReceived = True
		self.sdpReceived = sdp
		sdpDecoded = self.decode(sdp)
		if sdpDecoded.has_key('mediaDescription'):
			if len(sdpDecoded['mediaDescription']) > 0:
				for media in sdpDecoded['mediaDescription']:
						if sdpNegociated == False:
							sdpNegociated = True
							portToSend = media['__port']
							codecChoosed = self.negotiatesCodec(self.codecsSupported, media['__codecs'])	
							if codecChoosed != None:
								self.sdpAnswer['mediaDescription'].append({ '__type': 'audio',
																												'__port': self.portUsed,
																												'__proto':  'RTP/AVP',
																												'__codecs': [codecChoosed]
																											})
								self.sdpAnswerReInvite['mediaDescription'].append({ '__type': 'audio',
																												'__port': self.portUsed,
																												'__proto':  'RTP/AVP',
																												'__codecs': [codecChoosed]
																											})
							else:
								return None, None, None
						else:
							self.sdpAnswer['mediaDescription'].append({ '__type': media['__type'],
																												'__port': 0,
																												'__proto':  media['__proto'],
																												'__codecs': media['__codecs']
																											})
							self.sdpAnswerReInvite['mediaDescription'].append({ '__type': media['__type'],
																												'__port': 0,
																												'__proto':  media['__proto'],
																												'__codecs': media['__codecs']
																											})
			else:
				return None, None, None
		else:
			return None, None, None
		if sdpNegociated == False:
			return None, None, None
		else:
			return codecChoosed, sdpDecoded['connectionAddress'], portToSend
	def getSdpOffer(self, type = None):
		self.sdpOfferSended = True
		if type == 'Null':
			return self.encode(self.sdpOfferNull)
		else:
			return self.encode(self.sdpOffer)
	def getSdpAnswer(self):
			return self.encode(self.sdpAnswer)
	def getSdpAnswerReInvite(self):
		return self.encode(self.sdpAnswerReInvite)
	def resetSdpAnswer(self):
		self.sdpAnswer['mediaDescription'] =  [] 
		self.sdpAnswerReInvite['mediaDescription'] = [] 
	def reset(self):
		self.sdpOfferReceived = False
		self.sdpOfferSended = False
		self.sdpAnswerReceived = False
		self.sdpAnswerSended = False
		self.sdpReceived = None

	def decode (self, sdp):
		"""
		Decode a sdp text message to a python dictionnary

		@type	sdp: string
		@param	sdp: sdp payload (raw text)

		@return: a sdp message (dictionnary python)
		@rtype: dict
		"""
		data = {}
		media = False
		mediaDescription = []
		lines = sdp.splitlines()
		i = 1
		
		for line in lines:
			if line.startswith('v='):
				tmp = line[2:].split(' ')
				if tmp[0] != self.versionSdp:
					raise  Exception('Sdp version not supported!')
			if line.startswith('o='): 
				tmp = line[2:].split(' ')
				if tmp[4] != self.versionIp:
					raise  Exception('Incorrect ip version!')
				data.update({'ownerAddress': tmp[5]})	
			if line.startswith('c='): 
				tmp = line[2:].split(' ')
				if tmp[1] != self.versionIp:
					raise  Exception('Incorrect ip version!')
				data.update({'connectionAddress': tmp[2]})			
			if line.startswith('a='): 
				tmp = line[2:].split(' ')
				if media == True:
					if tmp[0] == 'sendonly' or tmp[0] == 'recvonly':
						dico.update({'__attribute': tmp[0]})
				else:
					data.update({'sessionAttribute': tmp[0]})
			if line.startswith('m='):
				if media == True:
					mediaDescription.append(dico)
				media = True
				tmp = line[2:].split(' ')
				codec = tmp[3:]
				codec = map(lambda x: int(x), codec)
				isPresent = False
				for proto in self.protos:
					if tmp[2] == proto:
						isPresent = True
				if isPresent == False:
					raise Exception('protocol not supported: %s' % str(tmp[2]))
				dico = {'__type':tmp[0],'__port':tmp[1], '__codecs':codec,'__proto': tmp[2]}	
			if i == len(lines):
				if media == True:
					mediaDescription.append(dico)
					media = False
			data.update({'mediaDescription': mediaDescription})
			i += 1
		
		return data

	def encode (self, sdp):
		
		"""
		Encode SDP dictionnary message to SDP text message

		@type	sdp: dict
		@param	sdp: a sdp message (dictionnary python) \n
		example: 	sdpDesc = { 'ownerAddress': '10.0.0.1', 'connectionAddress': '0.0.0.0', 'sessionAttribute':'directive:active', 
		'mediaDescription': [ {'__type': 'audio', '__port': 30900, '__codecs': [8,0,18], '__proto':  'RPT/AVP'} ] }

		@return: payload SDP (text)
		@rtype: string
		"""
		mediaDescription = ''
		
		if not (isinstance(sdp,(dict))): raise Exception('A dictionary is required!')
		if not sdp.has_key('mediaDescription'): raise  Exception('<mediaDescription> is mandatory')
		if not sdp.has_key('ownerAddress'): raise  Exception('<ownerAddress> is mandatory')
		if not sdp.has_key('connectionAddress'): raise  Exception('<connectionAddress> is mandatory')
		
		nbMedia = len(sdp['mediaDescription'])
		i = 0
		for media in sdp['mediaDescription'] :
			i = i + 1
			mediaAttribute = ''
			mediaFormat = ''
			if not media.has_key('__codecs'): raise  Exception('<__codecs> is mandatory')
			if not media.has_key('__proto'): raise  Exception('<__proto> is mandatory')
			if not media.has_key('__type'): raise  Exception('<__type> is mandatory')
			if not media.has_key('__port'): raise  Exception('<__port> is mandatory')
			isPresent = False
			for proto in self.protos:
				if media['__proto'] == proto:
					isPresent = True
			if isPresent == False:
				raise Exception('protocol not supported: %s' % str(media['__proto']))
					
			media['__codecs'] = map(lambda x: int(x), media['__codecs'])
			for codec in media['__codecs'] :
				mediaFormat += ' ' + str(codec)
				if self.codecMap.has_key(codec):
					details = self.codecMap[codec]
				else:
					details = self.defaultCodec
				mediaAttribute += 'a=rtpmap:%s %s\r\n' % (str(codec), details)	
				if codec == 101:
					mediaAttribute += 'a=fmtp:101 0-11,16\r\n'
			
			mediaDescription += 'm=%s %s %s%s\r\n' % (media['__type'], media['__port'],  media['__proto'], mediaFormat)
			mediaDescription += mediaAttribute
			if media.has_key('__attribute'):
				mediaDescription += 'a=%s\r\n' % (media['__attribute'])
			mediaDescription = mediaDescription.rstrip("\r\n")
			if i != nbMedia:
				mediaDescription += '\r\n'
		sdpMessage = 'v=%s\r\n' % self.versionSdp
		sdpMessage = sdpMessage + 'o=%s %s %s IN %s %s\r\n' % (self.userName, self.sessionId, self.sessionVersion, self.versionIp, sdp['ownerAddress'])
		sdpMessage = sdpMessage + 's=%s\r\n' % self.sessionName
		sdpMessage = sdpMessage + 'c=IN %s %s\r\n' % (self.versionIp,sdp['connectionAddress'])
		sdpMessage = sdpMessage + 't=0 0\r\n'
		if sdp.has_key('sessionAttribute'):
			sdpMessage = sdpMessage + 'a=%s\r\n' % sdp['sessionAttribute']
		sdpMessage = sdpMessage + '%s\r\n' % mediaDescription
		return sdpMessage
		
	def negotiatesCodec(self, codecsSupported, codecsReceived):
		"""
		This function enables to negociate codecs 
		
		@param codecsSupported: example [8,0]
		@type codecsSupported: list
		
		@param codecsReceived: example [8, 18, 0]
		@type codecsReceived: list
		
		@return: codec choosed
		@rtype: integer
		"""
		codecChoosed = None
		for codecReceived in codecsReceived:
			for codecSupported in codecsSupported:
				if codecReceived == codecSupported:
					codecChoosed = codecSupported
					return codecChoosed
		return codecChoosed
