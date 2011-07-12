##
# This file is a part of the SIP Virtual Endpoint component for Testerman.
#
# (c) Denis Machard and other contributors.
##

"""

"""

import Sdp as sdp
import Rtp as rtp
import re
import time
import md5
import random
import SipTemplates as templateSipMessages
import ControlTemplates as templateControlMessages

VERSION = '1.0'	

## VIRTUAL ENDPOINT BEHAVIOUR ## 
class Libs:
	"""
	"""
	def getTagInFrom(self, fromHeader):
		"""
		
		@param fromHeader:
		@type fromHeader:
		"""
		if ';tag=' in fromHeader:
			tmp = fromHeader.split(';tag=')
			return tmp[1].split(';')[0]
		else:
			return ''
		
	def getBranchInVia(self, viaHeader):
		"""
		
		@param viaHeader:
		@type viaHeader:
		"""
		if ';branch=' in viaHeader:
			tmp = viaHeader.split(';branch=')
			return tmp[1].split(';')[0]
		else:
			return ''
	
	def getTagInTo(self, toHeader):
		"""
		
		@param toHeader:
		@type toHeader:
		"""
		if ';tag=' in toHeader:
			tmp = toHeader.split(';tag=')
			return tmp[1].split(';')[0]
		else:
			return ''
			
	def getCallIdNumberInCallId(self, callIdHeader):
		"""
		
		@param callIdHeader:
		@type callIdHeader:
		"""
		return callIdHeader.split('@')[0]
	
		
	def generateId(self, length = 30, choice = 'azertyuiopqsdfghjklmwxcvbn0123456789'):
		"""
		generate a random string according characters contained in choice which a length of 'length'
		
		@param length: length of the generated id
		@type length: int
		@param choice: a string of all possible characters in the generated id.
		@type choice: string
		
		@return: the generated id
		@rtype: string
		"""
		myId = ''
		for i in range(int(length)):
			myId += random.choice(choice)
		return myId
	
	def generateCallId(self):
		"""
		generate a random call-id number. The domain name is not added in the result.
		
		@return: the generated call-id
		@rtype: string
		"""	
		return str(self.generateId(choice = '0123456789ABCDEF'))
	
	def generateBranch(self):
		"""
		generate a random branch of via header. The fixed party of the branch is not added here.
		
		@return: the branch number
		@rtype: string
		"""	
		return str(self.generateId(length = 30,choice = '0123456789'))
	
	def generateTag(self):
		"""
		generate a random tag.
		
		@return: the tag number
		@rtype: string
		"""		
		return self.generateId(30)
	
	
	
	def generateChallengeResponse(self, p_username, p_password, p_realm, p_nonce, p_method, p_uri, p_cnonce, p_nc, p_qop, p_algo, p_body):
		"""
		Build the answer to the challenge according rfc2617
		
		@param p_username: username of the user
		@type p_username: string
		@param p_password: password of the user
		@type p_password: string
		@param p_realm: realm of the challenge. Provided by the '401' response
		@type p_realm: string
		@param p_nonce: nonce of the challenge. Provided by the '401' response
		@type p_nonce: string
		@param p_method: method of the initial request (for instance: REGISTER)
		@type p_method: string
		@param p_uri: uri of the initial request (including an eventually 'sip:')
		@type p_uri: string
		@param p_cnonce: a random id. 
		@type	p_cnonce: string
		@param p_nc: the nc value of the answer
		@type p_nc: string
		@param p_qop: quality of protection. Provided by the '401' response
		@type p_qop: string.
		@param p_algo: algorithm to use
		@type p_algo: string
		@param p_body: the body of the response, if exists
		@type p_body: string
		
		@return: the answer of the challenge.
		@rtype: string
		"""
		if (not p_algo or p_algo.upper() == "MD5"):
			a1 = p_username + ":" + p_realm + ":" + p_password # computeA1
		else: # MD5-sess
			a1 = self.md5sum (p_username + ":" + p_realm + ":" + p_password) + ":" + p_nonce + ":" + p_cnonce #computeA1md5sess 
		if (p_qop == "auth-int"):
			a2 = p_method + ":" + p_uri + ":" + self.md5sum(p_body) #computeA2AuthInt
		else:
			a2 = p_method + ":" + p_uri # computeA2 
		result = str(self.md5sum(a1)) + ":" + p_nonce + ":" + p_nc + ":" + p_cnonce + ":" + p_qop + ":" + self.md5sum(a2)
		return self.md5sum (result)
	
	def md5sum(self, message):
		"""
		Compute the md5 of a list of strings
		
		@param message: message
		@type message: string
		
		@return: MD5 of message
		"""
		return md5.md5(message).hexdigest()	
			
	def parseChallenge(self, p_challengeRequest):
		"""
		Parse the challenge provided in the 'www-authenticate' header of the 401 response.
		
		@param p_challengeRequest: the challenge provided in the 'www-authenticate' header of the 401 response.
		@type p_challengeRequest: string
		
		@return: a parsing of the challenge.
		@rtype: dict
		"""
		challenge = {}
		challenge['authScheme'] = 'Digest'
		for i in p_challengeRequest.split(' ')[1].split('\n'):
			challenge[i.split('=')[0]] = i.split('"')[1]
		return challenge
		
	def decodeHeaderContact(self, header):
		"""
		Decode a header Contact. Also applied to from and to headers.\n
		For instance: '
		"Marco Polo" <sip:marco@world.tour;user=phone>;expires=3600,sip:marco@127.0.0.1;q=0.7;q=0.3\\n<sip:bob@127.0.0.1> ' will be decoded as\n
		
		[{ 'uri': sip:marco@world.tour, 'display': "Marco Polo" , 'parameters-header': 'expires=3600;q=0.3', 'parameters-uri': 'user=phone' },
		 { 'uri':'sip:marco@127.0.0.1', 'parameters-uri': q=0.7 },
		 { 'uri': 'sip:bob@127.0.0.1', 'CRCL': True}
		]
		
		@param header: contact, from or to header.
		@type header: string
		@return: decoded header
		@rtype: list
		"""
		 # spliter les lignes
		 # spliter par virgule
		 # spliter par '<'
	def getCliInFrom(self, fromHeader):
		if 'user=phone' in fromHeader:
			if 'sip:' in fromHeader:
				temp = fromHeader.split('<sip:')[1]
				temp = temp.split('>')[0]
				if not '@' in temp:
					return None
				else:
					temp = temp.split('@')[0]
					if temp == 'anonymous':return 'anonymous'
					else:return temp
		else:
			if 'sip:' in fromHeader:
				temp = fromHeader.split('<sip:')[1]
			elif  'tel:' in fromHeader:	
				temp = fromHeader.split('<tel:')[1]
			temp = temp.split('>')[0]
			return temp
	def getIdMessage(self, fromHeader = None, toHeader = None, callId = None, cseq = None, branch = None):
			"""
			
			"""
			tagFrom = ''
			tagTo = ''
			cSeq = ''
			branchVia = ''
			callid = ''
			if cseq != None:
				cSeq = 'cseq=' + cseq.split(' ')[0]
			if branch != None:
				branchVia = self.getBranchInVia(branch) 
			if fromHeader != None:
				tagFrom = self.getTagInFrom(fromHeader)
			if toHeader != None:
				tagTo = self.getTagInTo(toHeader)
			if callId != None:
				callid = self.getCallIdNumberInCallId(callId)
			idCall = tagFrom + ';' + tagTo + ';' + callid + ';' + cSeq + ';' + branchVia
			return idCall	
class GenericResponse:
	"""
	"""
	def __init__(self, classImport):
		if classImport.getClassName() == 'Register':
			self.register = classImport
			self.ve = self.register.ve
		elif classImport.getClassName() == 'Subscription':
			self.subscription = classImport
			self.ve = self.subscription.ve
		elif classImport.getClassName() == 'Session':
			self.session = classImport
			self.ve = self.session.ve
	def analyse(self, msg):
		# 1xx
		if msg['__responsecode'].startswith('1') :
			self.analyse1xxResponseCode(msg)
		# 2xx
		elif msg['__responsecode'].startswith('2'):
			self.analyse2xxResponseCode(msg)
		# 3xx
		elif msg['__responsecode'].startswith('3'):
			self.analyse3xxResponseCode( msg)
		# 4xx
		elif msg['__responsecode'].startswith('4'):
			self.analyse4xxResponseCode( msg)
		# 5xx
		elif msg['__responsecode'].startswith('5'):
			self.analyse5xxResponseCode(msg)
		# 6xx
		elif msg['__responsecode'].startswith('6'):
			self.analyse6xxResponseCode(msg)	
		else: 
			self.ve.debug('response code unknown')	
	def analyse1xxResponseCode(self, msg):
		self.ve.debug(str(msg['__responsecode']) + ' not analysed <class> GenericResponse</class>')
	def analyse2xxResponseCode(self, msg):
		self.ve.debug(str(msg['__responsecode']) + ' not analysed <class> GenericResponse</class>')
	def analyse3xxResponseCode(self, msg):
		self.ve.debug(str(msg['__responsecode']) + ' not analysed <class> GenericResponse</class>')
	def analyse4xxResponseCode(self, msg):
		self.ve.debug(str(msg['__responsecode']) + ' not analysed <class> GenericResponse</class>')
	def analyse5xxResponseCode(self, msg):
		self.ve.debug(str(msg['__responsecode']) + ' not analysed <class> GenericResponse</class>')
	def analyse6xxResponseCode(self, msg):
		self.ve.debug(str(msg['__responsecode']) + ' not analysed <class> GenericResponse</class>')

class Context:
	"""
	"""
	def __init__(self, dialog):
		self.dialog = dialog
		self.remoteUri = None
		self.remoteTarget = ''
		self.remoteCseq = None
		self.remoteTag = None
		self.localUri = None
		self.localCseq = 0
		self.localRseq = 0
		self.localTag = None
		self.localBranch = None
		self.callId = None
		self.routeSet = None
		#
		self.remoteDisplay = None
		self.remoteDiversion = None
		self.callLineIdentifier = None
	def reset(self):
		self.remoteUri = None
		self.remoteTarget = ''
		self.remoteCseq = None
		self.remoteTag = None
		self.localUri = None
		self.localCseq = 0
		self.localRceq = 0
		self.localTag = None
		self.localBranch = None
		self.callId = None
		self.routeSet = None
		#
		self.remoteDisplay = None
		self.remoteDiversion = None
		self.callLineIdentifier = None
	def setLocalUri(self, puid, domain = None):
		if domain == None:
			self.localUri = str(puid)
		else:
			self.localUri = 'sip:' + str(puid) + '@' + str(domain)
	def setLocalTag(self, tag):
		self.localTag = tag
	def setCallId(self, id):
		self.callId = str(id)
	def initializeCallId(self):
		if self.dialog.callIdModeGen == 0:
			self.callId = str(genericFunctions.generateCallId())
		elif self.dialog.callIdModeGen == 1:
			self.callId = str(genericFunctions.generateCallId()) + '@' + self.dialog.ve.sipSourceIp
		elif self.dialog.callIdModeGen == 2:
			self.callId = str(genericFunctions.generateCallId()) + '@' + self.dialog.domain
		else:
			self.callId = str(genericFunctions.generateCallId())
	def incrLocalCseq(self):
		self.localCseq += 1	
	def incrLocalRseq(self):
		self.localRseq += 1	
	def setLocalBranch(self, branch):
		self.localBranch = branch	

	def setRemoteUri(self, uri):
		self.remoteUri = str(uri)
	def setRemoteTarget(self, uri):
		self.remoteTarget = str(uri)
	def setRemoteTag(self, tag):
		self.remoteTag = tag
	def setRemoteDisplay(self, display):
		self.remoteDisplay = display
	def setRemoteDiversion(self, diversion):
		self.remoteDiversion = diversion
	def setCallLineIdentifier(self, cli):
		self.callLineIdentifier = cli
	def buildRequestUri(self, calleeUri, domain, phone = True):
		"""
		"""
		pattern1 = re.compile(r'^[a-zA-Z]+:')
		if pattern1.match(calleeUri):
			return calleeUri
		else:
			pattern2 = re.compile(r'(^.*[a-zA-Z]+.*)|(^.*@.*)')
			if not pattern2.match(calleeUri):
				if phone == False:
					return 'sip:' + calleeUri + '@' + domain
				else:
					return 'sip:' + calleeUri + '@' + domain + ';user=phone'
			else:
				if '@' in calleeUri:
					return 'sip:' + calleeUri
				else:
					return 'sip:' + calleeUri + '@' + domain	
	def setRouteSet(self, routes):
		self.routeSet = routes
	def setRemoteCseq(self, cseq):
		self.remoteCseq = int(cseq)
		
	def reverseRecordRoute(self, route):
		"""
		reverse record routes
		
		@param route: record-route parameter raised by the SIP probe
		@type route: string
		
		@return: record routes reverse
		@rtype: string
		"""
		routes = route.replace('\n',',')
		routes = routes.split(',')
		routes.reverse()
		return ','.join(routes)
	def getToHeader(self):
		if self.remoteUri != None:
			if self.remoteTag != None:
				return '<' + self.remoteUri + '>;tag=' + self.remoteTag 
			else:
				return '<' + self.remoteUri + '>'
		else:
			return '<undefined>'
			
	def getFromHeader(self):
		if self.localUri != None:
			if self.localTag != None:
				return '<' + self.localUri + '>;tag=' + self.localTag
			else:
				return '<' + self.localUri + '>'
		else:
			return '<undefined>'
	def getRoutesAndRequestUri(self):
		"""
		Returns the route header to use in the request to send,
		based on the currently known route set for the dialog,
		Also returns the request URI to use in this request to send.
		"""
		if self.routeSet == None:
			requestUri = self.remoteTarget
			routes = None
		elif self.routeSet != None:
			routeOne = self.routeSet.splitlines()[0].split(',')[0].strip()
			if ';lr' in routeOne:
				# SL:
				#requestUri = self.remoteTarget
				requestUri = routeOne[1:-4] # route format: <sip:user@domain:port;lr>
				routes = self.routeSet	
			else:
				"""todo""" 
				requestUri = routeOne
				tmpRoute = self.routeSet.replace(routeOne,'',1)
				if tmpRoute.startswith(',') or tmpRoute.startswith('\n') :
					tmpRoute = tmpRoute[1:]
				routes = tmpRoute + ',' + self.remoteTarget	
		return routes, requestUri	
	def getRoutesAndRequestUriAndProxy(self):
		"""
		Returns the route header to use in the request to send,
		based on the currently known route set for the dialog,
		Also returns the request URI to use in this request to send.
		"""
		if self.routeSet == None:
			requestUri = self.remoteTarget
			routes = None
			proxy = None # must be constructed with self.contructProxyValue(requestUri)
		elif self.routeSet != None:
			routeOne = self.routeSet.splitlines()[0].split(',')[0].strip()
			if ';lr' in routeOne:
				# SL:
				#requestUri = self.remoteTarget
				proxy = routeOne.split('@')[1].split(';')[0] # route format: <sip:user@domain:port;lr>
				routes = self.routeSet # unchanged
				requestUri = self.remoteTarget # unchanged
			else:
				"""todo""" 
				requestUri = routeOne
				tmpRoute = self.routeSet.replace(routeOne,'',1)
				if tmpRoute.startswith(',') or tmpRoute.startswith('\n') :
					tmpRoute = tmpRoute[1:]
				routes = tmpRoute + ',' + self.remoteTarget
				proxy = None
		return routes, requestUri, proxy	

	


genericFunctions = Libs()	

class VirtualEndpoint(Behaviour):
	"""
	Endpoints behaviour, contains alt machine
	"""
	def body(self, name, sipSourceIp, sipSourcePort, rtpProbes, callIdModeGen = 2,
		codecs = [ 8 ], resourceWav = '', debug = False, t1 = 0.5, transactionTimerTimeout = None, veInstanceNumber = 0, 
		puid = 'testerman', display = 'Testerman VE', userAgent = 'SIP VE/%s' % VERSION, 
		reliabilityMode = 'not-supported', username = 'login', password = 'password', 
		userPhone = False, dndStatusCode = 486, dndReasonPhrase = 'Do not disturb',
		proxyIp = '127.0.0.1', proxyPort = 5060, domain = None):
		"""
		Starts the SIP Virtual Endpoint Simulator, and configures it.
		
		@param vars:
		@type vars: 
		"""
		# ports aliasing
		self.sip = self["sip"]
		self.control = self["control"]
		sip = self.sip
		control = self.control
		# Endpoint configuration variables
		self.nameEndpoint = name
		self.veInstanceNumber = veInstanceNumber
		self.sipSourceIp = sipSourceIp 
		self.sipSourcePort = str(sipSourcePort) 
		self.rtpProbes = rtpProbes
		self.callIdModeGen = callIdModeGen
		self.resourceWav = resourceWav	
		self.debugMode= debug
		
		self.codecsSupported = codecs
		self.earlyMedia = False
		self.t1 = t1
		self.playWav = False
		self.display = display
		self.puid = puid
		self.userAgentName = userAgent
		self.reliability = reliabilityMode # require, supported, not-supported
		self.username = username
		self.password = password
		self.userPhone = userPhone
		self.proxyIp = proxyIp
		self.proxyPort = str(proxyPort)
		self.dndResponseCode = str(dndStatusCode)
		self.dndResponsePhrase = dndReasonPhrase
		if domain:
			self.domain = domain
		else:
			self.domain = '%s:%s' % (self.proxyIp, self.proxyPort)
		
		self.proxy = '%s:%s' % (self.proxyIp, self.proxyPort)
		self.maxForwards = '70'
		self.autoResponseIncomingCalls = False
		self.autoRejectIncomingCalls = False
		self.allow =  'INVITE, BYE, CANCEL, ACK, PRACK, SUBSCRIBE, NOTIFY, INFO, UPDATE, REFER, OPTIONS'
		
		if transactionTimerTimeout:
			self.transactionTimerTimeout = transactionTimerTimeout 
		else:
			self.transactionTimerTimeout = 64 * self.t1 # in rfc, default value is 64*T1 => 32s. We decide to reduce it to 5s.
		self.accept = 'application/sdp' 
		self.lastRequestSent = None
		self.pAsssociatedUri = None
		
		# instance object class
		self.register = Register(self)
		self.sessions = Sessions(self)
		self.subscriptions = Subscriptions(self)
		
		#	state machine
		self.epState = StateManager("not-started")
		altArgs = []
		#!!!!!!!!!!! RTP EVENT START	!!!!!!!!!!!
		for i in range(len(self.rtpProbes)):
			altArgs.append(
				[ # receiving rtp
					self['rtp' + str(i)].RECEIVE( ('startedReceivingRtp', extract(any(), 'msg'))),	
					lambda tmp = str(i): control.send( templateControlMessages.isReceivingRtp(callId = tmp, description = value('msg')) ),	
					REPEAT,
				]
			)	
			altArgs.append(
				[ # stopped-receiving-rtp
					self['rtp' + str(i)].RECEIVE( ('stoppedReceivingRtp', extract(any(), 'msg'))),	
					lambda tmp = str(i): control.send( templateControlMessages.stoppedReceivingRtp(callId = tmp, description = value('msg')) ),	
					REPEAT,
				]
			)	
		#!!!!!!!!!!! RTP EVENT STOP	!!!!!!!!!!!
		altArgs.append(
			# Endpoint State: not-started. On boot, intialize the SIP probe
			[ lambda: self.epState.get() == "not-started", 
				control.RECEIVE( templateControlMessages.plug() ),
#				lambda: sip.send(with_('sipve', templateSipMessages.initialize(self.sipSourceIp, self.sipSourcePort, self.t1) ),
				lambda: control.send( templateControlMessages.isStarted(self.nameEndpoint) ),	
				lambda: self.setEpState("started"),
				REPEAT,
			]
		)
		altArgs.append(
			# Endpoint State: started. On shutdown, we deinitialize the SIP probe, then we stop the behaviour (exit the alt)
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.unplug() ),
				lambda: self.unplug()
			]
		)
		altArgs.append(
			# receive configure endpoint from mtc
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.configure(any()), 'config'),
				lambda: self.configure(value('config')['conf']),
				REPEAT,
			]
		)
		altArgs.append(
			# receive register endpoint from mtc
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.register(), 'register'),
				lambda: self.registerEndpoint(value('register')),
				REPEAT,
			]
		)
		altArgs.append(
			# receive unregister endpoint from mtc
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.unregister()),
				lambda: self.unregisterEndpoint(),
				REPEAT,
			]
		)
		altArgs.append(
			# receive subscribe endpoint from mtc
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.subscribe(any()), 'subscribe' ),
				lambda: self.subscribeTo( value('subscribe') ),
				REPEAT,
			]
		)
		altArgs.append(
			# receive unsubscribe endpoint from mtc
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.unsubscribe( any() ), 'unsubscribe'),
				lambda: self.unsubscribeTo( value('unsubscribe') ),
				REPEAT,
			]
		)
		altArgs.append(
			# receive pickUp endpoint from mtc
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.pickUp(any()), 'pickup'),
				lambda: self.pickUp(value('pickup')),
				REPEAT,
			]
		)
		altArgs.append(
			# receive hangUp endpoint from mtc
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.hangUp(any()), 'hangup' ),
				lambda: self.hangUp(value('hangup')),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive place call
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.call(any()), 'makecall' ),
				lambda: self.makeCall(value('makecall')),
				REPEAT,
			]
		)	
		altArgs.append(
			# play a wav file
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE(templateControlMessages.m_playWavFile(any(), any(), greater_than(1)), 'playwav' ),
				lambda: self.playWavFile(value('playwav')),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive show call logs
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.showCallLogs() ),
				lambda: self.sessions.getCallLogs(),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive show conf
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.showConf() ),
				lambda: self.getConf(),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive placing call on hold
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.onHold() ),
				lambda: self.placingOnHold(),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive transfert call
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.transfer(any(), any(),  any()), 'transfer' ),
				lambda: self.transfer(value('transfer')),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive transfert call
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.joinConference(any(), any(),  any()), 'join' ),
				lambda: self.joinConf(value('join')),
				REPEAT,
			]
		)
		altArgs.append(
			# receive retrieve call
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.retrieveCall(any()), 'retrieve' ),
				lambda: self.retrieveCall(value('retrieve')),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive reject call
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.reject(any()), 'reject' ),
				lambda: self.reject(value('reject')),
				REPEAT,
			]
		)	
		altArgs.append(
			# receive divert call
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.divert(any()), 'divert' ),
				lambda: self.reject(value('divert')),
				REPEAT,
			]
		)	
		altArgs.append(
			# register timer
			[ self.register.getRegistrationTimer().TIMEOUT,
				lambda:  self.register.registrationFailed(),
				REPEAT,
			]
		)
		altArgs.append(
			# receive dmtf
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.dtmf(any(), any() ), 'dtmf' ),
				lambda: self.dialDtmf(value('dtmf')),
				REPEAT,
			]
		)
		altArgs.append(
			# receive update
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.updateToSend(any()), 'update' ),
				lambda: self.updateSession(value('update')),
				REPEAT,
			]
		)
		altArgs.append(
			# receive releaseActiveCalls
			[ lambda: self.epState.get() == "started", 
				control.RECEIVE( templateControlMessages.releaseActiveCalls() ),
				lambda: self.hangUpActiceCalls(),
				REPEAT,
			]
		)		
		
		altArgs.append(
			# register timer
			[ self.register.getRegistrationExpiryTimer().TIMEOUT,
				lambda: self.register.sendRegister(),
				REPEAT,
			]
		)	
		#!!!!!!!!!!! REGISTER STOP	!!!!!!!!!!!
		altArgs.append(
			# incoming response 
			[ sip.RECEIVE( with_('sipve', lambda: templateSipMessages.basicReceivedResponse()), 'response'),
				lambda: self.incomingResponse(value('response')),
				REPEAT,
			]
		)
		altArgs.append(
			# incoming request
			[ sip.RECEIVE( with_('sipve', lambda: templateSipMessages.basicReceivedRequest()), 'request', sender = 'sender'),
				lambda: self.incomingRequest(value('request'), sender('sender')),
				REPEAT,
			]
		)
		#!!!!!!!!!!! START TIMERS CALL !!!!!!!!!!!!!!!
		for session in self.sessions.listSessions:
			tmp = session
			altArgs.append(
				# 1xxRel timer
				[ tmp.getRelTimer().TIMEOUT,
					lambda sess = tmp: sess.resend180Rel(),
					REPEAT,
				]
			)
			altArgs.append(
				# 200 ok timer
				[ tmp.getResponse200OkTimer().TIMEOUT,
					lambda sess = tmp: sess.resend200Ok(),
					REPEAT,
				]
			)
		#!!!!!!!!!!! STOP TIMERS CALL	!!!!!!!!!!!
		#!!!!!!!!!!! START TIMERS SUBSCRIPTION !!!!!!!!!!!!!!!
		for subcription in self.subscriptions.listSubscriptions:
			tmp = subcription
#			altArgs.append(
#				# 
#				[ tmp.getFinishedSubscribeTimer().TIMEOUT,
#					lambda sub = tmp: sub.reset(),
#					REPEAT,
#				]
#			)
			altArgs.append(
				# 
				[ tmp.getSubscriptionObjectExpiryTimer().TIMEOUT,
					lambda sub = tmp: sub.sendSubscribe(status = 'subscribe-refresh'),
					REPEAT,
				]
			)
		#!!!!!!!!!!! STOP TIMERS SUBSCRIPTION	!!!!!!!!!!!
		alt(altArgs)
##############################################
	def unplug(self):
		"""
		reset sip probe and all rtp probes
		"""
#		self.sip.send(with_('sipve', templateSipMessages.deinitialize() )
		self.sessions.resetAllSessions()
	def debug(self, text, level = None):
		if self.debugMode:
			log(str(text))
	def getConf(self):
		log = 'auto response call: %s\nauto reject call: %s\n' % (self.autoResponseIncomingCalls, self.autoRejectIncomingCalls)
		log +='play wave: %s\n100rel: %s' % (self.playWav, self.reliability)
		self.debug(log)
	def setEpState(self, state):
		self.epState.set(state)
		if self.debugMode:
			log('Virtual Endpoint state: ' + self.epState.get() )
			
	def configure(self, value):
		"""
		Configure the virtual endpoint SIP
	
		@param value: endpoint configuration
		@type value: dict
		"""
		parameters = ['puid', 'domain', 'user-phone', 'proxy', 'display',  \
									'dnd', 'play-wav', 'login', \
									'pwd', 'reliability', 'auto-accept-calls', 'useragent-name'\
									, 'early-media', 'dnd-response-code', 'dnd-reason-phrase'
									 ]
		isPresent= False
		for key in value.keys():
			for param in parameters:
				if key == param: 
					isPresent= True
			if not isPresent:
				self.debug('!!! parameter %s not available !!!' % key)
			isPresent= False
			
		# set puid	
		if value.has_key('puid'):
			self.puid = value['puid']
		
		
		
		# set display
		if value.has_key('display'):
			disp = str(value['display'])
			disp = disp.replace('"', '')
			disp = disp.replace('\'','')
			self.display = disp
			
		# set useragent name
		if value.has_key('useragent-name'):
			self.userAgentName = str(value['useragent-name'])
			
		# set user phone agent
		if value.has_key('user-phone'):
			self.userPhone = str(value['user-phone'])	

		# set proxy ip:port
		if value.has_key('proxy'):	
			if ':' in value['proxy']:
				tmp = value['proxy'].split(':')
				self.proxyIp = str(tmp[0])	
				self.proxyPort = str(tmp[1])	
			else:
				self.proxyIp = value['proxy']
				self.proxyPort = '5060'
			self.proxy = '%s:%s' % (self.proxyIp, self.proxyPort)
			# set domain
			if value.has_key('domain'):
				self.domain = str(value['domain'])
			else:
				self.domain = self.proxyIp + ':' + self.proxyPort

		# set auto response to incoming calls
		if value.has_key('auto-accept-calls'):
			rejectCallValue = [True, False]
			if value['auto-accept-calls'] in rejectCallValue :
				self.autoResponseIncomingCalls = value['auto-accept-calls']
			else:
				self.debug('keyword %s: value (%s) forbidden' % ('auto-accept-calls', value['auto-accept-calls']))
		
		# set auto reject to incoming calls		
		if value.has_key('dnd'):
			rejectCallValue = [True, False]
			if value['dnd'] in rejectCallValue :
				self.autoRejectIncomingCalls = value['dnd']
			else:
				self.debug('keyword %s: value (%s) forbidden' % ('dnd', value['dnd']))
		
		# personalize response code and reason phrase in dnd mode	
		if value.has_key('dnd-response-code'):
			self.dndResponseCode = str(value['dnd-response-code'])
			
		if value.has_key('dnd-reason-phrase'):	
			self.dndResponsePhrase = str(value['dnd-reason-phrase'])	
			
		# set play wav		
		if value.has_key('early-media'):
			earlyMediaValue = [True, False]
			if value['early-media'] in earlyMediaValue :
				self.earlyMedia = value['early-media']
				if self.earlyMedia == True:
					self.reliability = 'require'
			else:
				self.debug('keyword %s: value (%s) forbidden' % ('early-media', value['early-media']))
				
		# set play wav		
		if value.has_key('play-wav'):
			playWavValue = [True, False]
			if value['play-wav'] in playWavValue :
				self.playWav = value['play-wav']
			else:
				self.debug('keyword %s: value (%s) forbidden' % ('play-wav', value['play-wav']))
		
		# set username	
		if value.has_key('login'):
			self.username = str(value['login'])
		
		# set pasword
		if value.has_key('pwd'):
			self.password = str(value['pwd'])
		
		# set reliability
		if value.has_key('reliability'):
			reliabilityValue = ['require', 'supported', 'not-supported']
			if value['reliability'] in reliabilityValue :
				self.reliability = value['reliability']
			else:
				self.debug('keyword %s: value (%s) forbidden' % ('reliability', value['reliability']))

	def registerEndpoint(self, value):
		"""
		Register the phone
		"""
		if self.register.getState() != 'not-registered':
			self.debug('phone already registered or in progress')
		else:
			if value.has_key('expires'):
				if value['expires'] > 0:
					self.register.setExpire(int(value['expires']))
			self.register.sendRegister()

	def unregisterEndpoint(self):
		"""
		Unregister the phone
		"""
		self.register.setExpire('0')
		if self.register.getState() == 'not-registered':
			self.register.sendUnregisterBeforeRegister()
		elif self.register.getState() == 'registering':	
			self.control.send( templateControlMessages.registrationFailed('the phone is already unregistered or in progress') )
		else:
			self.register.sendRegister()
	def subscribeTo(self, value):
		sub = self.subscriptions.thisSubscriptionIsSupported(value)
		if sub != None:
			if sub.getState() in [ 'subscribing', 'subscribed' ] :
				self.debug('already subscribe or subscribing') 
			else:
				if value.has_key('expires'):
					sub.setExpire(value['expires'])
				if value.has_key('uri'):
					sub.sendSubscribe(value['uri'], 'subscribe')
				else:
					sub.sendSubscribe(value['service'], 'subscribe')
		else:
			self.debug('this subscription is not supported') 
	def unsubscribeTo(self, value):
		sub = self.subscriptions.thisSubscriptionIsSupported(value)
		if sub != None:
			if not( sub.getState() in [ 'subscribed' ]) :
				self.debug('service not subscribed') 
			else:
				sub.setExpire(0)
				sub.sendSubscribe(status = 'unsubscribe')
		else:
			self.debug('this subscription is not supported') 
	def makeCall(self, value):
		if self.isBusy() == True:
			self.debug('place a call forbidden, the virtual endpoint is proceeding an other invite') 
		else:
			connectedCall = self.sessions.getConnectedSessionObject()
			if connectedCall == None:
				freeCall = self.sessions.getFreeSessionObject()
				if freeCall == None:
					self.debug('place a call forbidden, max calls reached')
				else:
					if value['sdp'] == True:
						freeCall.sendInviteWithSdp(value)
					else:
						freeCall.sendInvite(value)
			else:
				self.debug('placing on hold the current call before place a new call')

	def reject(self, value):
		"""
		@param
		@type
		"""	
		callId = str(value['call-id'])
		session = self.sessions.getActiveSessionObjectBycallId(callId)
		if session == None:
			self.debug('call instance does not exist')
		elif session.getCallState() != 'incoming-call-processing':
			self.debug('reject is not allowed')
		else:
			defaultResponseCode = '603'
			defaultReasonPhrase = 'Decline'
			# divert
			if value.has_key('contact-to'):
				session.sendBasicResponse(code = value['code'], phrase = value['phrase'], request = session.initialRequest, contactOverwrite = value['contact-to'])
			else:
			#reject
				if value.has_key('code') and  value.has_key('phrase'):
					session.sendBasicResponse(code = value['code'], phrase = value['phrase'], request = session.initialRequest)
				elif value.has_key('code') and  not value.has_key('phrase'):
					session.sendBasicResponse(code = value['code'], phrase = defaultReasonPhrase, request = session.initialRequest)
				elif not value.has_key('code') and value.has_key('phrase'):
					session.sendBasicResponse(code = defaultResponseCode, phrase = value['phrase'], request = session.initialRequest)	
				else:
					session.sendBasicResponse(code = defaultResponseCode, phrase = defaultReasonPhrase, request = session.initialRequest)
			session.reset()
			
	def pickUp(self, value):
		"""
		@param
		@type
		"""		
		callId = str(value['call-id'])
		session = self.sessions.getSessionObjectBycallId(callId)
		if session == None:
			self.debug('call instance does not exist')
		elif session.getCallState() != 'incoming-call-processing':
			self.debug('pick-up is not allowed 1')
		elif session.getSipState() in ['ringing']:
			session.send200OkToInvite()		
		elif session.getSipState() in	['waiting-prack']:
			session.relTimer.setNewName('180 rel retransmission')
			session.relTimer.stop()
			session.setSipState('ringing')
			session.send200OkToInvite()	
		else:
			self.debug('pick-up is not allowed 2')
				
	def hangUp(self, value):
		"""
		@param
		@type
		"""
		callId = str(value['call-id'])
		session = self.sessions.getActiveSessionObjectBycallId(callId)
		if session == None:
			self.debug('call instance does not exist')
		else:
			if session.getSipState() == 'waiting-ack':
				session.setSipState('waiting-ack-byeing')
			if session.getSipState() == 'connected':	
				session.sendBye(value = value)
			elif session.getSipState() == 'waiting-100-trying':	
				session.setSipState('waiting-100-trying-cancelling')
			else:	
				if session.getSipState() == 'waiting-ack':
					session.sendBye(value = value)
				else:
					session.sendCancel(value = value)
					self.debug('canceled sent instead of a bye')
	def hangUpActiceCalls(self):
		activeSessions = self.sessions.getAllNotFreeSessionObject()
		if len(activeSessions) == 0 :
			self.debug('no active calls')
		else:
			for session in activeSessions:
				self.hangUp({'call-id': session.callId})
	def dialDtmf(self, value):
		connectedCall = self.sessions.getConnectedSessionObject()
		if connectedCall is None:
			self.debug('not call connected')
		else:
			connectedCall.sendInfo(value)

	def playWavFile(self, value):
		"""
		@param
		@type
		"""
		callId = str(value['callId'])
		session = self.sessions.getActiveSessionObjectBycallId(callId)
		if session == None:
			self.debug('call instance does not exist')
		else:
			if session.getSipState() == 'connected':	
				session.rtp.playWavFile(resource = value['resource'], loopCount = value['loopCount'])

	def placingOnHold( self ):
		connectedCall = self.sessions.getConnectedSessionObject()
		if connectedCall is None:
			self.debug('not call connected')
		else:
			connectedCall.sendReInviteWithSdp(placingOnHold = True)
	def retrieveCall( self, value):
		"""
		"""
		connectedCall = self.sessions.getConnectedSessionObject()
		if connectedCall == None:
			callId = str(value['call-id'])
			session = self.sessions.getSessionObjectBycallId(callId)
			if session == None:
				self.debug('call instance does not exist')
			elif session.getCallState() == 'on-hold':
				session.sendReInviteWithSdp(placingOnHold = False)
			else:
				self.debug('no call on hold ')
		else:
			self.debug('placing on hold the current call before retrieve')

	def transfer(self, value):
		callId = str(value['refer'])	
		session = self.sessions.getActiveSessionObjectBycallId(callId)
		if session != None:
				if isinstance( value['to'], str) or isinstance( value['to'], unicode):
					session.sendRefer( type =  value['type'], uri = value['to']	)
				else:
					sessionToTransfer = self.sessions.getActiveSessionObjectBycallId(str(value['to'])	)
					if sessionToTransfer != None:
						session.sendRefer( type = value['type'], sessionTo = sessionToTransfer	)
					else:
						self.debug('transfer is not allowed, call instance does not exist')
		else:
			self.debug('transfer is not allowed, call instance does not exist')
	def joinConf(self, value):
		callId = str(value['refer'])	
		session = self.sessions.getActiveSessionObjectBycallId(callId)
		if session != None:
				referTo = self.sessions.getActiveSessionObjectBycallId(str(value['to'])	)
				if referTo != None:
					session.sendRefer( type =  value['type'], uri = referTo.context.remoteTarget	)
				else:
					self.debug('transfer is not allowed, call instance does not exist')
		else:
			self.debug('transfer is not allowed, call instance does not exist')			
	def updateSession(self, value):
		callId = str(value['call-id'])
		session = self.sessions.getSessionObjectBycallId(callId)
		if session != None:
			session.sendUpdate(value)
		else:
			self.debug('call instance does not exist')
##############################################
	def incomingRequest(self, request, sender):
		# Add the IP packet source (ip:port)
		request['__source'] = sender
		if request['__message'] == 'INVITE':
			self.incomingInvite(request)
		elif request['__message'] == 'CANCEL':
			self.incomingCancel(request)
		elif request['__message'] == 'PRACK':
			self.incomingPrack(request)
		elif request['__message'] == 'NOTIFY':
			self.incomingNotify(request)
		elif request['__message'] == 'ACK':
			self.incomingAck(request)
		elif request['__message'] == 'BYE':
			self.incomingBye(request)
		elif request['__message'] == 'INFO':
			self.incomingInfo(request)
		elif request['__message'] == 'UPDATE':
			self.incomingUpdate(request)
		else:
			self.debug('request ' + request['__message'] + ' not yet supported')
			self.sendGenericResponse('200', 'OK', request)
	def incomingResponse(self, response):
		def dispatchResponse(response):
			register = self.register.identifyRegister(From = response['from'], Call = response['call-id'])
			if register != None:
				return register
			session = self.sessions.getSessionObject(From = response['from'], Call = response['call-id'])
			if session != None:
				return session
			subscribe = self.subscriptions.getSubscriptionObject(From = response['from'], Call = response['call-id'])
			if subscribe != None:
				return subscribe
			return None
		object = dispatchResponse(response)
		if object == None:
			self.debug(str(response['__responsecode']) + ' not analysed')
		else:
			object.analyseIncomingResponse(response)
##############################################
	def incomingUpdate(self, request):
		sdpIsPresent = self.checkingSdpPresent(request)
		session = self.sessions.getSessionObject( To = request['to'], Call = request['call-id'])
		if session != None:
			if sdpIsPresent:
				session.receivedUpdateWithSdp(request)
			else:
				session.receivedUpdate(request)
		else:
			self.debug('unknown update')
			self.sendGenericResponse('481', 'Call/Transaction Does Not Exist', request)	
	def incomingInfo(self, request):
		session = self.sessions.getSessionObject(From = request['from'], To = request['to'], Call = request['call-id'])
		if session != None:
			if session.getSipState() == 'connected':
				session.receivedInfo(request)
			else:
				self.sendGenericResponse('488', 'Not Acceptable Here ', request)	
		else:
			self.debug('unknown info')
			self.sendGenericResponse('481', 'Call/Transaction Does Not Exist', request)	
	def incomingPrack(self, request):
		sdpIsPresent = self.checkingSdpPresent(request)
		session = self.sessions.getSessionObject(From = request['from'], To = request['to'], Call = request['call-id'])
		if session != None:
			if session.getSipState() in ['waiting-prack'] :
				if not sdpIsPresent:
					session.receivedPrack(request)
				else:
					session.receivedPrackWithSdp(request)		
			else:
				self.sendGenericResponse('481', 'Call/Transaction Does Not Exist', request)
		else:
			self.debug('unknown prack')
			self.sendGenericResponse('481', 'Call/Transaction Does Not Exist', request)			

	def incomingBye(self, request):
		session = self.sessions.getSessionObject(From = request['from'], To = request['to'], Call = request['call-id'])
		if session != None:
			if session.getSipState() in ['connected', 'waiting-bye-response']:
				session.receivedBye(request)
			else:
				self.sendGenericResponse('488', 'Not Acceptable Here ', request)
		else:
			self.debug('unknown bye')
			self.sendGenericResponse('481', 'Call/Transaction Does Not Exist', request)

	def incomingCancel(self, request):
		session = self.sessions.getSessionObject(From = request['from'], Call = request['call-id'], Cseq = request['cseq'])
		if session != None:
			if session.getSipState() == 'ringing':
				session.receivedCancelToInvite(request)
			elif session.getInfoState() == 'waiting-info-response':
				session.receivedCancelToInfo(request)
			else:
				# incorrect implementation
				self.sendGenericResponse('200', 'OK', request)
		else:
			self.sendGenericResponse('481', 'Call/Transaction Does Not Exist', request)
			self.debug('cancel not analysed') 
	
	def incomingNotify(self, request):
		def dispatchNotify(request):
			subscription = self.subscriptions.getSubscriptionObject(From = request['from'], Call = request['call-id'], To = request['to'])
			if subscription != None:
				return subscription
			session = self.sessions.getSessionObject(From = request['from'], To = request['to'], Call = request['call-id'])
			if session != None:	
				return session
			return None	
		object = dispatchNotify(request)	
		if object == None:
			###### START ########
			# fix BMSC: generic response to notify
			state = request['subscription-state'].split(';')[0]
			if request.has_key('__body'): 
				body = request['__body']
			else: 
				self.debug('body empty')
				body = 'empty'
			desc = {}
			desc.update({'event-name': request['event']})
			desc.update({'subscription-state': state})
			desc.update({'body': body})
			self.control.send( templateControlMessages.notify(descriptions = desc) )
			self.sendGenericResponse('200', 'OK', request)
			###### STOP ########
		else:
			object.receivedNotify(request)

	def incomingAck(self, request):
		sdpIsPresent = self.checkingSdpPresent(request)
		session = self.sessions.getSessionObject( From = request['from'], To = request['to'], Call = request['call-id'])
		if session != None:
			if session.getSipState() in ['waiting-ack'] :
				if not sdpIsPresent:
					session.receivedAckToInvite(request)
				else:
					session.receivedAckWithSdpToInvite(request)
			elif session.getSipState() in ['waiting-ack-cancelling', 'waiting-ack-byeing', 'waiting-ack-error']:
				session.receivedAck(request)
			elif session.getSipState() in ['waiting-ack-reinvite', 'waiting-ack-error-reinvite']:
				if not sdpIsPresent:
					session.receivedAckToReInvite(request)
				else:
					session.receivedAckWithSdpToReInvite(request)
			elif session.getInfoState() == 'waiting-ack-cancelling-info':
				session.receivedAckToInfo(request)
		else:
			if self.lastRequestSent != None:
				if request['from'] == self.lastRequestSent['from'] and request['to'] == self.lastRequestSent['to'] and request['call-id'] == self.lastRequestSent['call-id']:
						self.debug('ack received to ' + str(self.lastRequestSent['__responsecode']))
				else:
						self.debug('ack not analysed')
			else:
				self.debug('ack not analysed')
	
	def incomingInvite(self, request):
		sdpIsPresent = self.checkingSdpPresent(request)
		if ';tag=' in request['to']:
			# received re-invite
			session = self.sessions.getSessionObject( From = request['from'], To = request['to'], Call = request['call-id'])
			if session != None:
#				reliability = self.checking100rel(request)
				if session.getSipState() in ['connected', 'transfer-in-progress'] :
					if sdpIsPresent:
						session.receivedReInviteWithSdp(request)
					else:
						session.receivedReInvite(request)
				else:
					retryvalue = str(int(random.randint(1,10)))
					self.sendGenericResponse('500', 'Server Internal Error', request, {'retry-after': retryvalue})
					self.debug('incoming invite rejected\nstate sip incorrect')
			else:
				self.sendGenericResponse('481', 'Call/Transaction Does Not Exist', request)
				self.debug('incoming invite rejected\nno matching session')
		else:
			# received a new invite
			freeCall = self.sessions.getFreeSessionObject() # if freeCall = None then max calls reached
			reliability = self.checking100rel(request)
			if reliability is None :
				self.control.send( templateControlMessages.info('Incoming invite rejected') )
			elif self.autoRejectIncomingCalls == True:
				self.sendGenericResponse( self.dndResponseCode, self.dndResponsePhrase, request)
				self.debug('incoming invite rejected\nthe virtual endpoint is configured to reject all incoming calls')
			elif self.isBusy() == True:
				self.sendGenericResponse('486', 'Busy Here', request)
				self.debug('incoming invite rejected\nthe virtual endpoint is proceeding an invite') 
			elif freeCall == None :
				self.sendGenericResponse('486', 'Busy Here', request)
				self.debug('incoming invite rejected\nsimulatenous max calls reached')
			else:
				connectedCall =  self.sessions.getConnectedSessionObject()
				if self.autoResponseIncomingCalls == True and connectedCall != None:
						self.autoResponseIncomingCalls = False
				# new call
				if sdpIsPresent:
					freeCall.receivedInviteWithSdp(request, reliability)
				else:
					freeCall.receivedInvite(request, reliability)
##############################################	
	def sendGenericResponse(self, code, reason, request, optionalHeaders = None):
		toHeader = request['to'] 
		fromHeader = request['from']
		callId = request['call-id']
		cseq = request['cseq']
		via = request['via']
		contact = '<sip:' + self.puid + '@' + self.sipSourceIp + ':' + self.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgentName,
								'allow': self.allow,
							}
		if optionalHeaders != None:
			headers.update(optionalHeaders)
		msg = templateSipMessages.basicSendResponse( code, reason, fromHeader, toHeader, callId, via, cseq, headers)
		self.sip.send(with_('sipve', msg), request['__source'])
		self.lastRequestSent = msg
		
##############################################	
	def checking100rel(self, request):
		# 100rel handling (rfc3262)
		if request.has_key('require') and '100rel' in request['require'] and self.reliability == 'not-supported':
			self.sendGenericResponse('420', 'Bad Extension', request, {'unsupported': '100rel'})
			return None
		elif self.reliability == 'require' and not ((request.has_key('require') and '100rel' in request['require']) or (request.has_key('supported') and '100rel' in request['supported'])):
			self.sendGenericResponse('421', 'Extension Required', request)
			return None
		elif request.has_key('require') and '100rel' in request['require'] and (self.reliability == 'supported' or self.reliability == 'require'):
			return True	
		elif request.has_key('supported') and '100rel' in request['supported'] and (self.reliability == 'supported' or self.reliability == 'require'):
			return True	
		else:
			return False
	def checkingSdpPresent(self, request):
		if request.has_key('content-type') and request['content-type'] != 'application/sdp': 
			self.sendGenericResponse('415', 'Unsupported Media Type', request, {'accept': self.accept})
		elif request.has_key('content-type') and request['content-type'] == 'application/sdp':
			return True
		else:
			return False
	def isBusy(self):
		for session in self.sessions.listSessions:
				if session.isSignaling():
					self.debug('busy')
					return True
		self.debug('not busy')
		return False

########### SUBSCRIPTIONS ##############
class Subscriptions:
	"""
	"""
	def __init__(self, ve):
		"""
		"""
		self.ve = ve
		mwiservice = MwiSubscription(self.ve)
		mwiservice.setParameters()
		registerSubscription = RegisterSupervisionSubscription(self.ve)
		registerSubscription.setParameters()
		dialogSubscription = DialogSupervisionSubscription(self.ve)
		dialogSubscription.setParameters()
		serviceSubscription = ServiceSupervisionSubscription(self.ve)
		serviceSubscription.setParameters()
		conferenceSubscription = ConferenceSubscription(self.ve)
		conferenceSubscription.setParameters()
		self.listSubscriptions = [mwiservice, registerSubscription, dialogSubscription, serviceSubscription, conferenceSubscription]
	def thisSubscriptionIsSupported(self, value):
		"""
		"""
		for sub in self.listSubscriptions:
			if sub.getNameService() == value['service']:
				return sub
		return None
	def getSubscriptionObject(self, From = None, To = None, Call = None,):
		id = genericFunctions.getIdMessage(fromHeader = From, toHeader = To, callId = Call )
		tag1, tag2, tag3, tag4, tag5 = id.split(';')
		for sub in self.listSubscriptions:
			if tag1 in sub.getId() and tag2 in sub.getId() and tag3 in sub.getId() and tag4 in sub.getId() and tag5 in sub.getId():
				return sub
		return None
	def getActiveSubscriptions(self):
		"""todo"""
	def getStateOfSubcription(self, service):
		"""todo"""
	def resetAllSubscriptions(self):
		"""todo"""

class GenericSubscription:
	"""
	"""
	def __init__(self, ve ):
		self.className = 'Subscription'
		self.ve = ve
		self.id = genericFunctions.getIdMessage()
		self.nameEvent = None
		self.nameService = None
		self.accept = None
		self.callIdModeGen = None
		self.expire = 86400
		self.display = None
		self.context = Context(self)
		self.userAgent = None
		self.proxyIp = None
		self.proxyPort = None
		self.domain = None
		self.state = StateManager('unsubscribed')
		self.subscriptionExpiryTimer =  Timer(2000, name = "Subscription refresh")
		# instance object class by sip method
		self.responseToSubscribe = ResponseToSubscribe(self)
	def getClassName(self):
		return self.className
	def getSubscriptionObjectExpiryTimer(self):
		"""
		return 
		"""
		return self.subscriptionExpiryTimer	
	def getFinishedSubscribeTimer(self):
		"""
		return 
		"""
		return self.finishedSubscribeTimer
	def getId(self):
		return self.id	
	def contructProxyValue(self, requestUri):
		proxy = requestUri
		if '@' in proxy:
			proxy = proxy.split('@')[1]
		if 'sip:' in proxy:	
			proxy = proxy.split('sip:')[1]
		proxy = proxy.split(';')[0].split(',')[0]
		regexp = re.compile(r'[a-zA-Z]+')
		if regexp.match(proxy):
			proxy = self.proxyIp + ':' + self.proxyPort
		return proxy
	def getNameService(self):
		return self.nameService
	def getNameEvent(self):
		return self.nameEvent
	def getState(self):
		"""
		"""
		return self.state.get()
	def setExpire(self, expire):
		self.expire = expire
		newExpire = int(int(self.expire)*1000*90/100) #refresh subscription at 90% of self.expire
		self.subscriptionExpiryTimer = Timer(newExpire, 'Subscription refresh set to (%s sec.)' % (newExpire/1000))
		
	def setState(self, state):
		"""
		"""
		self.state.set(state)
		self.ve.debug('subscription ' + str(self.nameEvent) + ' state: ' + self.state.get() )

	def initRegisterWithNewEndpointParameters(self):
		self.userAgent = self.ve.userAgentName
		self.proxyIp = self.ve.proxyIp
		self.proxyPort = self.ve.proxyPort
		self.puid = self.ve.puid
		self.domain = self.ve.domain
		self.userPhone = self.ve.userPhone
		self.display = self.ve.display
		self.callIdModeGen = self.ve.callIdModeGen
	def sendSubscribe(self, uri = None, status = None):
		# state updated
		self.setState('subscribing')
		if status == 'subscribe':	
			self.initRegisterWithNewEndpointParameters()
			self.context.setLocalUri( self.puid, self.domain )	
			self.context.initializeCallId()
			self.context.setRemoteUri( self.context.buildRequestUri(uri, self.domain) )
			self.context.setRemoteTarget( self.context.buildRequestUri(uri, self.domain) )
			self.context.setLocalTag( genericFunctions.generateTag() )
		self.context.setLocalBranch( genericFunctions.generateBranch() )
		self.context.incrLocalCseq()
		# create subscribe
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		toHeader = self.context.getToHeader()
		callId = self.context.callId
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + self.context.localBranch
		cseq = str(self.context.localCseq)
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		routes, requestUri = self.context.getRoutesAndRequestUri()	
		proxy = self.contructProxyValue(requestUri)
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy' : proxy,
								'event': self.nameEvent,
								'accept': self.accept,
								'expires': str(self.expire)
							}
		if routes != None:
			headers.update({'route':routes})
		self.ve.sip.send(with_('sipve', templateSipMessages.subscribe(fromHeader, toHeader, callId, via, cseq, requestUri, self.ve.maxForwards, headers)), proxy	)
		# update id 
		self.id = genericFunctions.getIdMessage(fromHeader = fromHeader, callId = callId)
		
	def reset(self):
		self.ve.debug('reset')
		self.className = 'Subscription'
		self.setState('unsubscribed')
		self.id = genericFunctions.getIdMessage()
		self.expire = 86400
		self.nameEvent = None
		self.accept = None
		self.nameService = None
		self.callIdModeGen = None
		self.subscriptionExpiryTimer =  Timer(2000, name = "Subscription refresh")
		
	def analyseIncomingResponse(self, response):
		cseq = response['cseq']
		cseqNumber = cseq.split(' ')[0]
		cseqMethod = cseq.split(' ')[1]
		if cseqNumber == str(self.context.localCseq):
			if cseqMethod == 'SUBSCRIBE':
				# update id 
				self.id = genericFunctions.getIdMessage(fromHeader = response['from'], toHeader = response['to'], callId = response['call-id'])
				# transfert to analyse
				self.responseToSubscribe.analyse(msg = response)
			else:
					self.ve.debug(str(response['__responsecode']) + ' received: method ' + cseqMethod + ' unknown')
		else:
			self.ve.debug(str(response['__responsecode']) + ' received : cseq not available in this dialog')
	
	def receivedNotify(self, request):
		if self.getState() in ['subscribed', 'subscribing']:	
			self.parseNotify(request)
		else:
			self.ve.debug('notify error')
	def parseNotify(self, notify):
		if notify.has_key('subscription-state'):
			self.send200Ok(notify)
			subState = notify['subscription-state'].split(';')
			state = notify['subscription-state'].split(';')[0]
			if len(subState) > 1:
				reason = notify['subscription-state'].split(';')[1]
			else:
				reason = None
			body = ''
			if notify.has_key('__body'):
				body = notify['__body']
			else:
				body = 'empty'
			desc = {}
			desc.update({'event-name': self.nameService})
			desc.update({'subscription-state': state})
			desc.update({'reason': reason})
			desc.update({'body': body})
			self.ve.control.send( templateControlMessages.notify(descriptions = desc))
			if state == 'terminated':
				self.ve.control.send( templateControlMessages.unsubscribeSuccessful(self.nameService))
				self.reset()
		else:
			self.ve.debug('error to parse notify, subscription-state header is mandatory')
	def send200Ok(self, request):
		toHeader = request['to'] 
		fromHeader = request['from']
		callId = request['call-id']
		cseq = request['cseq']
		via = request['via']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
							}
		msg = templateSipMessages.response200( fromHeader, toHeader, callId, via, cseq, headers)
		self.ve.sip.send(with_('sipve', msg), self.proxy )

class ResponseToSubscribe(GenericResponse):
	"""
	"""
	def analyse1xxResponseCode(self, msg):
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.subscription.setState('unsubscribed')
		self.ve.control.send( templateControlMessages.subscriptionFailed( self.subscription.nameEvent, msg['__reasonphrase']) )	
	def analyse2xxResponseCode(self, msg):
		if self.subscription.getState() in ['subscribing']:
			self.subscription.setState('subscribed')
			self.subscription.context.setRemoteTag( genericFunctions.getTagInTo(msg['to']) )
			if  msg.has_key('record-route'):	
				self.subscription.context.setRouteSet ( self.subscription.context.reverseRecordRoute( msg['record-route']) ) 
			if  msg.has_key('contact'):
				"""todo"""
				self.subscription.context.setRemoteTarget(  msg['contact'].split('>')[0].split('<')[1] )
			self.ve.control.send( templateControlMessages.subscribed(self.subscription.nameService))
			if msg.has_key('expires'):
				self.subscription.setExpire(int(msg['expires']))
			else:
				if msg.has_key('contact'):
					tmp = msg['contact'].split('expires=')
					if len(tmp) == 2:
						tmp = tmp[1].split(';')[0]
						self.subscription.setExpire(int(tmp))
			if self.subscription.expire != 0:
				self.subscription.subscriptionExpiryTimer.start()
	def analyse3xxResponseCode(self, msg):
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.subscription.setState('unsubscribed')
		self.ve.control.send( templateControlMessages.subscriptionFailed( self.subscription.nameEvent, msg['__reasonphrase']) )	
	def analyse4xxResponseCode(self, msg):
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		# 423
		if msg['__responsecode'] == '423':
			if msg.has_key('min-expires'):
				self.subscription.expire = msg['min-expires']
			else:
				self.ve.debug('min-expires header not present')
			self.subscription.sendSubscribe(status = 'refresh-subscribe')
		else:
			self.subscription.setState('unsubscribed')
			self.ve.control.send( templateControlMessages.subscriptionFailed( self.subscription.nameEvent, msg['__reasonphrase']) )	
	def analyse5xxResponseCode(self, msg):
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.subscription.setState('unsubscribed')
		self.ve.control.send( templateControlMessages.subscriptionFailed( self.subscription.nameEvent, msg['__reasonphrase']) )	
	def analyse6xxResponseCode(self, msg):
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.subscription.setState('unsubscribed')
		self.ve.control.send( templateControlMessages.subscriptionFailed( self.subscription.nameEvent, msg['__reasonphrase']) )	
class MwiSubscription(GenericSubscription):
	"""
	"""
	def setParameters(self):
		self.nameService = 'mwiservice'
		self.nameEvent = 'message-summary'
		self.accept = 'application/simple-message-summary' 
		self.ve.debug('subscription ' + self.nameEvent + ' state: ' + self.state.get() )

class RegisterSupervisionSubscription(GenericSubscription):
	"""
	Use for BSMC solution to supervise registration state.
	"""
	def setParameters(self):
		self.nameService = 'reg'
		self.nameEvent = 'reg'
		self.accept = 'application/reginfo+xml' 
		self.ve.debug('subscription ' + self.nameEvent + ' state: ' + self.state.get() )
class DialogSupervisionSubscription(GenericSubscription):
	"""
	Use for BSMC solution to supervise call state.
	"""
	def setParameters(self):
		self.nameService = 'dialog'
		self.nameEvent = 'dialog'
		self.accept = 'application/dialog-info+xml' 
		self.ve.debug('subscription ' + self.nameEvent + ' state: ' + self.state.get() )		

class ServiceSupervisionSubscription(GenericSubscription):
	"""
	Use for BSMC solution to supervise service state.
	"""
	def setParameters(self):
		self.nameService = 'ua-profile;profile-type=user'
		self.nameEvent = 'ua-profile;profile-type=user'
		self.accept = 'application/service-user-profile+xml' 
		self.ve.debug('subscription ' + self.nameEvent + ' state: ' + self.state.get() )
class ConferenceSubscription(GenericSubscription):
	"""
	"""
	def setParameters(self):
		self.nameService = 'conference'
		self.nameEvent = 'conference'
		self.accept = 'conference' 
		self.ve.debug('subscription ' + self.nameEvent + ' state: ' + self.state.get() )				
#############  REGISTER  ###############
class Register:
	"""
	This class manages the procedure of registration 
	"""
	def __init__(self, ve):
		"""
		@param ve: virtual endpoint sip (class Virtual_EndPoint)
		"""
		self.className = 'Register'
		self.ve = ve
		self.id = genericFunctions.getIdMessage()
		self.context = Context(self)
		self.proxyIp = None
		self.proxyPort = None
		self.callIdModeGen = None
		self.state = StateManager('not-registered')
		self.ve.debug('register state: ' + self.state.get() )
		self.username = None
		self.password = None
		self.expire = 3600 # seconds
		self.puid = None
		self.ncRegister = 1
		self.cNonce = None
		self.transactionTimer = self.ve.transactionTimerTimeout
		self.registrationTimer = Timer(self.transactionTimer, name = "Registering watchdog") # Time to respond to a REGISTER
		self.registrationExpiryTimer =  Timer(2.000, name = "Registration refresh")
		self.userAgent = None
		self.userPhone = None
		self.domain = None
		
		# instance object class by sip method
		self.responseToRegister = ResponseToRegister(self)
	def getClassName(self):
		return self.className
	def identifyRegister(self, From = None, Call = None,):
		id = genericFunctions.getIdMessage(fromHeader = From, callId = Call )
		tag1, tag2, tag3, tag4, tag5 = id.split(';')
		if tag1 in self.id and tag2 in self.id and tag3 in self.id and tag4 in self.id and tag5 in self.id:
			return self
		else:	
			return None
	def reset(self):
		"""
		"""
		self.className = 'Register'
		self.id = genericFunctions.getIdMessage()
		self.context.reset()
		self.expireRegister = 3600 # default 3600 seconds
		self.proxyIp = None
		self.proxyPort = None
		self.username = None
		self.password = None
		self.expire = 3600 # seconds
		self.puid = None
		self.ncRegister = 1
		self.cNonce = None
		self.callIdModeGen = None
		self.userAgent = None
		self.userPhone = None
		self.state = StateManager('not-registered')
		self.transactionTimer = self.ve.transactionTimerTimeout
		self.registrationTimer = Timer(self.transactionTimer, name = "Registering watchdog")
		self.registrationExpiryTimer =  Timer(2.000, name = "Registration refresh")
	def getRegistrationTimer(self):
		"""
		return registration timer
		"""
		return self.registrationTimer
		
	def getRegistrationExpiryTimer(self):
		"""
		return timer of registration refresh
		"""
		return self.registrationExpiryTimer	
		
	def getState(self):
		"""
		Return the state of register process (not-registered/registering/registered)
		"""
		return self.state.get()
	
	def getProxy(self):
		"""
		Return the IP address and port proxy concatenated
		"""
		return self.proxyIp + ':' + self.proxyPort
	
	def getNcRegister(self):
			"""
			"""
			temp = str(self.ncRegister)
			nb = 8 - len(temp)
			nc =''
			j = 0
			while j < nb:
				nc += '0'
				j += 1
			nc += temp
			return nc
	
	def setState(self, state):
		"""
		"""
		self.state.set(state)
		self.ve.debug('register state: ' + self.state.get() )
			
	def setExpire(self, expire):
		"""
		set the new expire value 
		
		@param expire:
		@type expire:
		"""
		self.expire = expire
		newExpire = int(int(self.expire)*1000*90/100) #refresh registration at 90% of self.expire
		self.registrationExpiryTimer = Timer(newExpire, 'Registration refresh (%s sec.)' % (newExpire/1000))
	def initRegisterWithNewEndpointParameters(self):
		self.userAgent = self.ve.userAgentName
		self.proxyIp = self.ve.proxyIp
		self.proxyPort = self.ve.proxyPort
		self.puid = self.ve.puid
		self.username = self.ve.username
		self.password = self.ve.password
		self.domain = self.ve.domain
		self.userPhone = self.ve.userPhone
		self.callIdModeGen = self.ve.callIdModeGen
		
	
	def sendUnregisterBeforeRegister(self):
		"""
		send register request
		"""
		self.initRegisterWithNewEndpointParameters()
		# create context
		self.context.setRemoteTarget('sip:' + self.proxyIp + ':' + self.proxyPort) 
		if self.userPhone: self.context.setLocalUri(self.puid , self.domain + ';user=phone')
		else: self.context.setLocalUri( self.puid , self.domain )
		if self.expire == '0':
			self.registrationExpiryTimer.setNewName('Registration refresh')
			self.registrationExpiryTimer.stop()
		self.context.incrLocalCseq()
		self.context.setLocalTag( genericFunctions.generateTag() )
		if self.context.callId == None:
			self.context.initializeCallId()
		# create register
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'
		proxy = self.proxyIp + ':' + self.proxyPort
		callid = self.context.callId
		cseq = str(self.context.localCseq)
		headers = { 'expires': self.expire,
								'user-agent': self.userAgent, 
								'max-forwards': self.ve.maxForwards, 
								'contact': contact,
								'proxy' : proxy,
								'allow': self.ve.allow
							}
		fromHeader = '<' + self.context.localUri + '>;tag=' + self.context.localTag 
		toHeader = '<' + self.context.localUri + '>'
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		self.ve.sip.send(with_('sipve', templateSipMessages.register(fromHeader, toHeader, callid, via, cseq, self.context.remoteTarget, self.ve.maxForwards, headers)), proxy	)					
		self.registrationTimer.setNewName("Registering watchdog (%s sec.)" % (int(self.transactionTimer)/1000) )
		self.registrationTimer.start()
		# state updated
		self.setState('registering')
		# update id 
		self.id = genericFunctions.getIdMessage(fromHeader = fromHeader, callId = callid)
	def sendRegister(self):
		"""
		send register request
		"""
		if self.expire != '0':
			self.initRegisterWithNewEndpointParameters()
		# create context
		self.context.setRemoteTarget('sip:' + self.domain) 
		if self.userPhone: self.context.setLocalUri(self.puid , self.domain + ';user=phone')
		else: self.context.setLocalUri( self.puid , self.domain )
		if self.expire == '0':
			self.registrationExpiryTimer.setNewName('Registration refresh')
			self.registrationExpiryTimer.stop()
		self.context.incrLocalCseq()
		self.context.setLocalTag( genericFunctions.generateTag() )
		if self.context.callId == None:
			self.context.initializeCallId()
		# create register
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'
		proxy = self.proxyIp + ':' + self.proxyPort
		callid = self.context.callId
		cseq = str(self.context.localCseq)
		headers = { 'expires': self.expire,
								'user-agent': self.userAgent, 
								'max-forwards': self.ve.maxForwards, 
								'contact': contact,
								'proxy' : proxy,
								'allow': self.ve.allow
							}
		fromHeader = '<' + self.context.localUri + '>;tag=' + self.context.localTag 
		toHeader = '<' + self.context.localUri + '>'
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		self.ve.sip.send(with_('sipve', templateSipMessages.register(fromHeader, toHeader, callid, via, cseq, self.context.remoteTarget, self.ve.maxForwards, headers)), proxy	)					
		self.registrationTimer.setNewName("Registering watchdog (%s sec.)" % (int(self.transactionTimer)/1000) )
		self.registrationTimer.start()
		# state updated
		self.setState('registering')
		# update id 
		self.id = genericFunctions.getIdMessage(fromHeader = fromHeader, callId = callid)
		
	def sendRegisterWithCredential(self, credential):
		"""
		send register request with challenge response
		
		@param credential:
		@type credential: 
		"""
		self.context.incrLocalCseq()
		self.context.setLocalTag( genericFunctions.generateTag() )
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'
		proxy = self.proxyIp + ':' + self.proxyPort
		callid = self.context.callId
		cseq = str(self.context.localCseq)
		headers = { 'expires': self.expire,
								'user-agent': self.userAgent, 
								'max-forwards': self.ve.maxForwards, 
								'contact': contact,
								'proxy' : proxy,
								'allow': self.ve.allow}
		headers.update(credential)
		fromHeader = '<' + self.context.localUri + '>;tag=' + self.context.localTag 
		toHeader = '<' + self.context.localUri + '>'
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		self.ve.sip.send(with_('sipve', templateSipMessages.register(fromHeader, toHeader, callid , via, cseq, self.context.remoteTarget, self.ve.maxForwards, headers)), proxy	)					
		self.registrationTimer.setNewName("Registering watchdog (%s sec.)" % (int(self.transactionTimer)/1000) )
		self.registrationTimer.start()
		# update id 
		self.id = genericFunctions.getIdMessage(fromHeader = fromHeader, callId = callid)
		
	def analyseIncomingResponse(self, response):
		"""
		received one response with xxx response code
		
		@param response:
		@type response: 
		"""
		cseq = response['cseq']
		cseqNumber = cseq.split(' ')[0]
		cseqMethod = cseq.split(' ')[1]
		if cseqNumber == str(self.context.localCseq):
			if cseqMethod == 'REGISTER':
				self.responseToRegister.analyse(msg = response)
			else:
					self.ve.debug(str(response['__responsecode']) + ' received: method ' + cseqMethod + ' unknown')
		else:
			self.ve.debug(str(response['__responsecode']) + ' received : cseq not available in this dialog')
	def registrationFailed(self):	
		"""
		This function is called when the registration timer is exceeded, raised one event to userland
		"""
		self.setState('not-registered')
		self.ve.control.send( templateControlMessages.registrationFailed('registration timer exceeded') )


class ResponseToRegister(GenericResponse):
	"""
	"""
	def analyse2xxResponseCode(self, msg):
		if self.register.state.get() == 'registering':
			if self.register.expire == '0':
				self.ve.control.send( templateControlMessages.notRegistered() )
				self.register.registrationTimer.stop()
				self.register.reset()
			else:
				if msg.has_key('p-associated-uri'):
					self.ve.pAsssociatedUri = msg['p-associated-uri']
				self.ve.control.send( templateControlMessages.registered(self.ve.pAsssociatedUri) )
				self.register.registrationTimer.stop()
				self.register.setState('registered')
				
				if msg.has_key('expires'):
					self.register.setExpire(msg['expires'])
				else:
					if msg.has_key('contact'):
						tmp = msg['contact'].split('expires=')
						if len(tmp) == 2:
							tmp = tmp[1].split(';')[0]
							self.register.setExpire(int(tmp))
				self.register.registrationExpiryTimer.start()
		else:
			self.ve.debug( 'received response in register state: ' + self.register.state.get() )
	def analyse1xxResponseCode(self, msg):
		self.register.setState('not-registered')
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.register.registrationTimer.stop()	
		self.ve.control.send( templateControlMessages.registrationFailed( msg['__reasonphrase']) )	
	def analyse3xxResponseCode(self, msg):
		self.session.setState('not-registered')
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.session.registrationTimer.stop()	
		self.ve.control.send( templateControlMessages.registrationFailed( msg['__reasonphrase']) )	
	def analyse4xxResponseCode(self, msg):
		if self.register.state.get() == 'registering':
			desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			if msg['__responsecode'] == '401':
				self.register.registrationTimer.stop()
				if self.register.username == 'undefined' or self.register.password == 'undefined':
					self.ve.control.send( templateControlMessages.registrationFailed('credintial (login/pwd) not configured') ) 
				else:
					self.register.cNonce = genericFunctions.generateId(8)
					challenge = genericFunctions.parseChallenge(msg['www-authenticate'])
					algo = None
					body = None
					if challenge.has_key('realm') and challenge.has_key('nonce'):
						if challenge.has_key('algorithm'):
							algo = challenge['algorithm']
						challengeCompute = genericFunctions.generateChallengeResponse(self.register.username, self.register.password, challenge['realm'], challenge['nonce'], "REGISTER", 'sip:' + self.register.getProxy(), self.register.cNonce, self.register.getNcRegister(), challenge['qop'], algo, body) 
						challengeResponse = {'Authorization' : 'Digest username="' + self.register.username + '", realm="' + challenge['realm'] + '", nonce="' + challenge['nonce'] + '", uri="sip:' + self.register.getProxy() + '", response="' + challengeCompute + '", algorithm=MD5' + ', qop=' + challenge['qop'] + ', cnonce="' + self.register.cNonce + '", nc=' + self.register.getNcRegister()}
						self.register.ncRegister += 1
						self.register.sendRegisterWithCredential(challengeResponse)
			
			# 423
			elif msg['__responsecode'] == '423':
				self.register.registrationTimer.stop()
				self.register.expire = msg['min-expires']
				self.register.sendRegister()
			else:
				self.register.registrationTimer.stop()	
				self.ve.control.send( templateControlMessages.registrationFailed( msg['__reasonphrase']) )
		else:
			self.ve.debug( 'received response in register state: ' + self.register.state.get() )	
	def analyse5xxResponseCode(self, msg):
		self.register.setState('not-registered')
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.register.registrationTimer.stop()	
		self.ve.control.send( templateControlMessages.registrationFailed( msg['__reasonphrase']) )	
	def analyse6xxResponseCode(self, msg):
		self.register.setState('not-registered')
		desc = { 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
		self.ve.control.send( templateControlMessages.error(descriptions = desc) )
		self.register.registrationTimer.stop()	
		self.ve.control.send( templateControlMessages.registrationFailed( msg['__reasonphrase']) )	
#############  SESSIONS  ###############
class Sessions:
	"""
	"""
	def __init__(self, ve):
		self.ve = ve
		self.nbSessions =  len(self.ve.rtpProbes)
		self.listSessions = []
		for i in range(self.nbSessions):
			callObject = Session(self.ve, self.ve['rtp'+str(i)], self.ve.rtpProbes[i], str(i) ) # ve, behavior rtp port, rtp probe, instance
			self.listSessions.append(callObject)
		# call logs
		self.dialedCalls = [] 
		self.missedCalls = [] 
		self.receivedCalls = [] 
		self.failedCalls = [] 

	def getSessionObject(self, From = None, To = None, Call = None, Cseq = None, Branch = None):
		id = genericFunctions.getIdMessage(fromHeader = From, toHeader = To, callId = Call, cseq = Cseq, branch = Branch )
		tag1, tag2, tag3, tag4, tag5 = id.split(';')
		for session in self.listSessions:
			if tag1 in session.getId() and tag2 in session.getId() and tag3 in session.getId() and tag4 in session.getId() and tag5 in session.getId():
				return session
		return None
	def getSessionObjectBycallId(self, instance):
		for session in self.listSessions:
			if session.callId == instance:
				return session
		return None
	def getCallLogs(self):
		self.ve.control.send( templateControlMessages.callLogs(len(self.dialedCalls), len(self.missedCalls), len(self.receivedCalls), len(self.failedCalls)) )
#		if self.ve.debugMode:
		missedCallLogs = ''
		dialledCallLogs = ''
		receivedCallLogs = ''
		failedCallLogs = ''
		if len(self.missedCalls) == 0:
			missedCallLogs = 'none'
		else:
			for call in self.missedCalls:
				missedCallLogs = missedCallLogs + '%s: caller: %s, no answered for: %.1f sec.\n' % (str(call['timestamp']), str(call['uri']), call['duration-call'])
		if len(self.dialedCalls) == 0:
			dialledCallLogs = 'none'
		else:
			for call in self.dialedCalls:
				dialledCallLogs = dialledCallLogs + '%s: called: %s, duration call: %.1f sec., duration connected: %.1f sec.\n' % (str(call['timestamp']), str(call['uri']), call['duration-call'], call['duration-connected'])	
		if len(self.receivedCalls) == 0:
			receivedCallLogs = 'none'
		else:
			for call in self.receivedCalls:
				receivedCallLogs = receivedCallLogs + '%s: caller: %s, duration call:%.1f sec., duration connected: %.1f sec.\n' % (str(call['timestamp']), str(call['uri']), call['duration-call'], call['duration-connected'])	
		if len(self.failedCalls) == 0:
			failedCallLogs = 'none'
		else:
			for call in self.failedCalls:
				failedCallLogs = failedCallLogs + '%s: called: %s, duration call: %.1f sec.\n' % (str(call['timestamp']), str(call['uri']), call['duration-call'])	
		self.ve.log('Missed calls:\n' + str(missedCallLogs))
		self.ve.log('Received calls:\n' + str(receivedCallLogs))
		self.ve.log('Dialed calls:\n' + str(dialledCallLogs))	
		self.ve.log('Failed calls:\n' + str(failedCallLogs))				
	def getActiveSessionObjectBycallId(self, instance):
		"""
	
		"""
		for session in self.listSessions:
			if session.callId == instance and session.getCallState() in ["connected", "on-hold", "outcoming-call-processing", "incoming-call-processing"]:
				return session
		return None
	def getActiveSessionObject(self):
		"""
		a call is actived if its state is connected or processing
		"""
		for session in self.listSessions:
			if session.getCallState() in ["connected", "outcoming-call-processing", "incoming-call-processing"]:
				return session
		return None
	def getStateOfSession(self, callId):
		"""todo"""
	def getConnectedSessionObject(self):
		"""
		a call is actived if its state is connected
		"""
		for session in self.listSessions:
			if session.getCallState() == 'connected':
				return session
		return None
	def getFreeSessionObject(self):
		"""
		@return:
		@rtype: 
		"""
		for session in self.listSessions:
			if session.getId() == genericFunctions.getIdMessage():
				return session
		return None
	def getAllNotFreeSessionObject(self):
		lst = []
		for session in self.listSessions:
			if session.getId() != genericFunctions.getIdMessage():
				lst.append(session)
		return lst
	def resetAllSessions(self):
		for session in self.listSessions:
			session.reset()
		self.ve.control.send( templateControlMessages.isStopped(self.ve.nameEndpoint))

class SessionLogs:
	"""
	Start/stop call logs
	"""
	def __init__(self, ve):
		"""
		@param behaviourEndpoint: virtual endpoint sip (class Virtual_EndPoint)
		"""
		self.ve = ve
		self.callLog = { 'uri': None,'timestamp': None,
									   'invite': None, '200Ok': None,
									   'duration-connected': 0 , 'duration-call': 0 , 
									   'type': None
				}
					
	def reset(self):
		"""
		"""
		self.callLog = { 'uri': None,'timestamp': None,
										 'invite': None,'200Ok': None,
										 'duration-connected': 0 ,
										 'duration-call': 0 , 
										 'type': None
										}
										
	def start(self, uri, status):
		"""
		@param uri: caller or called
		@type uri: string
		@param status: 'dialed' or 'received' call
		@type status: string
		"""
		self.ve.debug('start call duration')
		self.callLog['uri'] = str(uri)
		self.callLog['timestamp'] = str(time.strftime("%Y/%m/%d %H:%M", time.localtime(time.time())))
		self.callLog['type'] = str(status)
	
	def setStatus(self, status):
		"""
		@param status:
		@type status:
		"""
		self.callLog['type'] = status	
	
	def set200OkTimestamp(self):	
		"""
		"""
		self.callLog['200Ok'] = time.time()
	
	def setInviteTimestamp(self):	
		"""
		"""
		self.callLog['invite'] = time.time()
	
	def setDurationConnected(self):
		"""
	
		"""
		if self.callLog['200Ok'] != None:
			self.callLog['duration-connected'] = time.time() - self.callLog['200Ok']
	
	def stop(self):
		"""
		raised call logs to the virtual endpoint
		"""
		self.ve.debug('stop call duration')
		self.callLog['duration-call'] = time.time() - self.callLog['invite']
		if self.callLog['type'] =='failed':
			self.ve.sessions.failedCalls.append(self.callLog)
		if self.callLog['type'] =='dialed':
			self.ve.sessions.dialedCalls.append(self.callLog)
		if self.callLog['type'] == 'missed':
			self.ve.sessions.missedCalls.append(self.callLog)
		if self.callLog['type'] == 'received':
			self.ve.sessions.receivedCalls.append(self.callLog)

class Session:
	"""
	This class manages the status of one call incoming or outcoming
	"""
	def __init__(self, ve, port, probeRtp, callId):
		"""
		@param ve: virtual endpoint sip (class Virtual_EndPoint)
		"""
		self.className = 'Session'
		self.ve = ve
		self.id = genericFunctions.getIdMessage()
		self.callIdModeGen = None
		self.callId = callId
		self.callState = StateManager('idle')
		self.sipState = StateManager('idle')
		self.referState = StateManager('idle')
		self.infoState = StateManager('idle')
		self.ve.debug('call: ' + str(self.callId) + ' >> sip state: ' + self.sipState.get() )
		self.ve.debug('call: ' + str(self.callId) + ' >> call state: ' + self.callState.get() )
		self.ve.debug('call: ' + str(self.callId) + ' >> refer state: ' + self.referState.get() )
		self.ve.debug('call: ' + str(self.callId) + ' >> info state: ' + self.infoState.get() )
		self.reliability = None
		self.reliabilityIn = None
		self.earlyMedia = None
		self.domain = None
		self.puid = None
		self.initialRequest = None
		self.infoRequest = None # An INFO request MAY be cancelled.
		self.secondRequest = None
		self.codecSupported = None
		self.codecChoosed = None
		self.audioId = int(str(self.ve.veInstanceNumber) + str(self.callId))
		# The proxy is where we are supposed to send a new request for the call.
		self.proxyIp = None
		self.proxyPort = None
		# The responsePeer is where we are supposed to send the response to a request (actually,
		# could be different from one incoming request to another one, so managing a global one
		# for the session is not a good idea. However, will work as a first approximation)
		# This info should be extracted from the Via request header. However, we'll use the
		# source packet IP:port of the incoming request instead.
		self.responsePeerIp = None
		self.responsePeerPort = None
		
		self.sdp = sdp.Sdp(versionSdp = '0', versionIp = 'IP4', userName = '-', sessionName = 'testerman')
		self.probeRtpIp, self.probeRtpPort = probeRtp
		self.rtp = rtp.Rtp(self.ve,  port, self.probeRtpIp , self.probeRtpPort, self.ve.debugMode )
		self.display = None
		self.logs = SessionLogs(self.ve)
		self.context = Context(self)
		self.requestToResend = None
		self.reInviteSended = False
		self.placingOnHold = False
		self.incomingCall = None
		self.pAssertedIdentity = None
		self.slowStart = None
		# refer
		self.typeOfTransfer = None
		self.referToUri = None
		self.sessionRefer = None
		# instance object class by sip method
		self.responseToInvite = ResponseToInvite(self)
		self.responseToReInvite = ResponseToReInvite(self)
		self.responseToBye = ResponseToBye(self)
		self.responseToCancel = ResponseToCancel(self)
		self.responseToPrack = ResponseToPrack(self)
		self.responseToAck = ResponseToAck(self)
		self.responseToRefer = ResponseToRefer(self)
		self.responseToInfo = ResponseToInfo(self)
		self.responseToUpdate = ResponseToUpdate(self)
		# timers
		self.timerBetween200andAckValue = None
		self.nbRetranmissionMax = 2
		self.nbRetranmission = 0
		self.initialTimeout = 2.000
		self.nextTimeout = 2.000
		self.relTimer = Timer(self.initialTimeout, name = "180 rel retransmission %s sec." % (self.initialTimeout/1000))
		self.response200Timer = Timer(self.initialTimeout, name = "200 ok retransmission %s sec." % (self.initialTimeout/1000))
	def getId(self):
		return self.id
	def getClassName(self):
		return self.className	
	def initSessionWithNewEndpointParameters(self):
		self.callIdModeGen = self.ve.callIdModeGen
		self.codecSupported = self.ve.codecsSupported
		self.userAgent = self.ve.userAgentName
		self.puid = self.ve.puid
		self.proxyIp = self.ve.proxyIp
		self.proxyPort = self.ve.proxyPort
		self.proxy = '%s:%s' % (self.proxyIp, self.proxyPort)
		self.domain = self.ve.domain
		self.display = self.ve.display
		self.reliability = self.ve.reliability
		self.earlyMedia = self.ve.earlyMedia
		self.autoResponse = self.ve.autoResponseIncomingCalls
		if self.probeRtpPort == None:
				#self.probeRtpPort = getFreePort(self.probeRtpIp, ttl=10, start=40000, length=10000)
				if self.probeRtpPort == None:
					self.probeRtpPort = 10000
				self.rtp.setPortFrom(self.probeRtpPort)
		self.sdp.setSdpTemplate( ip = self.probeRtpIp, port = self.probeRtpPort, codecs = self.codecSupported )		
	def reset(self):
		self.rtp.stopSending()
		self.rtp.stopListening()
		self.id = genericFunctions.getIdMessage()
		self.callState = StateManager('idle')
		self.sipState = StateManager('idle')
		self.referState = StateManager('idle')
		self.infoState = StateManager('idle')
		self.ve.debug('call: ' + str(self.callId) + ' >> sip state: ' + self.sipState.get() )
		self.ve.debug('call: ' + str(self.callId) + ' >> call state: ' + self.callState.get() )
		self.ve.debug('call: ' + str(self.callId) + ' >> refer state: ' + self.referState.get() )
		self.ve.debug('call: ' + str(self.callId) + ' >> info state: ' + self.infoState.get() )
		self.context.reset()
		self.logs.reset()
		self.reliability = None
		self.reliabilityIn = None
		self.callIdModeGen = None
		self.domain = None
		self.puid = None
		self.initialRequest = None
		self.secondRequest = None
		self.codecChoosed = None
		self.codecSupported = None
		self.audioId = int(str(self.ve.veInstanceNumber) + str(self.callId))
		self.proxyIp = None
		self.proxyPort = None
		self.display = None
		self.requestToResend = None
		self.reInviteSended = False
		self.placingOnHold = False
		self.incomingCall = None
		self.pAssertedIdentity = None
		self.slowStart = None
		# refer
		self.sessionRefer = None
		self.typeOfTransfer = None
		self.referToUri = None
		#
		self.ve.control.send( templateControlMessages.isIdle(self.callId))
		
	def isSignaling(self):
		if not self.sipState.get() in ['connected', 'idle']: return True
		else: return False

	def getRelTimer(self):
		"""
		return rel timer
		"""
		return self.relTimer
	def getResponse200OkTimer(self):
		"""
		return 200 ok timer
		"""
		return self.response200Timer
	def setCallState(self, state):
		self.callState.set(state)
		self.ve.debug('call: ' + str(self.callId) + ' >> call state: ' + self.callState.get() )		
	def setInfoState(self, state):
		self.infoState.set(state)
		self.ve.debug('call: ' + str(self.callId) + ' >> info state: ' + self.infoState.get() )	
	def setSipState(self, state):
		self.sipState.set(state)
		self.ve.debug('call: ' + str(self.callId) + ' >> sip state: ' + self.sipState.get() )
	def setReferState(self, state):
		self.referState.set(state)
		self.ve.debug('call: ' + str(self.callId) + ' >> refer state: ' + self.referState.get() )
	def getInfoState(self):
		return self.infoState.get()
	def getReferState(self):
		return self.referState.get()
	def getCallState(self):
		return self.callState.get()
	def getSipState(self):
		return self.sipState.get()
	def getResponsePeer(self):
		return '%s:%s' % (self.responsePeerIp, self.responsePeerPort)
	def setResponsePeer(self, ipPort):
		self.responsePeerIp, self.responsePeerPort = ipPort.split(':', 1)

	def contructProxyValue(self, requestUri):
		proxy = requestUri
		if '@' in proxy:
			proxy = proxy.split('@')[1]
		if 'sip:' in proxy:	
			proxy = proxy.split('sip:')[1]
		proxy = proxy.split(';')[0].split(',')[0]
		regexp = re.compile(r'[a-zA-Z]+')
		if regexp.match(proxy):
			proxy = self.proxyIp + ':' + self.proxyPort
		return proxy
		
	def analyseIncomingResponse(self, response):
		cseq = response['cseq']
		cseqMethod = cseq.split(' ')[1]
		if cseq == self.initialRequest['cseq']:
			if cseqMethod == 'INVITE':
				if self.reInviteSended == True:
					self.responseToReInvite.analyse(msg = response)
				else:
					self.responseToInvite.analyse(msg = response)
			else:
				self.ve.debug(str(response['__responsecode']) + ' received: method ' + cseqMethod + ' unknown')
		elif self.secondRequest != None and cseq == self.secondRequest['cseq'] :
			if cseqMethod == 'BYE':
				self.responseToBye.analyse(msg = response)
			elif cseqMethod == 'CANCEL':
				self.responseToCancel.analyse(msg = response)
			elif cseqMethod == 'PRACK':
				self.responseToPrack.analyse(msg = response)
			elif cseqMethod == 'ACK':
				self.responseToAck.analyse(msg = response)
			elif cseqMethod == 'REFER':
				self.responseToRefer.analyse(msg = response)
			elif cseqMethod == 'INFO':
				self.responseToInfo.analyse(msg = response)
			elif cseqMethod == 'UPDATE':
				self.responseToUpdate.analyse(msg = response)
			else:
				self.ve.debug(str(response['__responsecode']) + ' received: method ' + cseqMethod + ' unknown')
		else:
			self.ve.debug(str(response['__responsecode']) + ' received : cseq not available in this dialog') 
	#######################
	def sendInfo(self, value):
		toHeader = self.context.getToHeader()
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		callId = self.context.callId
		self.context.incrLocalCseq()
		cseq = str(self.context.localCseq)
		routes, requestUri = self.context.getRoutesAndRequestUri()	
		proxy = self.contructProxyValue(requestUri)
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy,
								'content-type': 'application/dtmf-relay',
								'__body': 'Signal=' + str(value['signal']) + '\r\nDuration=' + str(value['duration']) + '\r\n'
							}
		if routes != None:
			headers.update({'route':routes})
		message = templateSipMessages.info(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers) 
		self.sendSipMessageExceptInvite( message, proxy )
		# state changed
		self.setInfoState('waiting-info-response')
	def sendReInviteWithSdp(self, placingOnHold):
		
		self.placingOnHold = placingOnHold
		self.context.incrLocalCseq()
		# create invite
		if self.incomingCall == True:
			contact = '<' + self.context.remoteUri + '>'
		else:
			contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		self.context.setLocalBranch( genericFunctions.generateBranch() )
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
				fromHeader = '"' + self.display + '" ' + fromHeader
		toHeader = self.context.getToHeader()
		callId = self.context.callId
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + self.context.localBranch
		cseq = str(self.context.localCseq)
		routes, requestUri = self.context.getRoutesAndRequestUri()	
		proxy = self.contructProxyValue(requestUri)
		headers = { 'contact': contact,
									'user-agent': self.userAgent,
									'allow': self.ve.allow,
									'proxy' : proxy,
									'content-type': 'application/sdp'
								}
		if self.placingOnHold == True: 
			headers.update({'__body': self.sdp.getSdpOffer(type = 'Null')})
		else: 
			headers.update({'__body': self.sdp.getSdpOffer()})
		if routes != None:
			headers.update({'route':routes})
		if self.reliability == 'require':
			headers.update({'require': '100rel'})
		elif self.reliability == 'supported':
			headers.update({'supported': '100rel'})
		message = templateSipMessages.invite(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers)							
		self.ve.sip.send(with_('sipve',message), proxy)
		self.initialRequest = message
		# update id of call (self.calls)
		self.id = genericFunctions.getIdMessage(fromHeader = message['from'],  toHeader = message['to'], callId = message['call-id'])
		# update state call and sip
		self.setSipState('waiting-response-reinvite')
		self.reInviteSended = True
	def sendInvite(self, value):
		self.incomingCall = False
		self.slowStart = not(value['sdp'])
		self.sdp.reset()
		if value.has_key('timer-between-200ok-ack'):
			self.timerBetween200andAckValue = value['timer-between-200ok-ack']
		# update local parameters
		self.initSessionWithNewEndpointParameters()
		# call logs
		self.logs.start(value['called-uri'], 'dialed')
		self.logs.setInviteTimestamp()
		# create context
		self.context.setLocalUri( self.puid, self.domain )
		self.context.setLocalTag( genericFunctions.generateTag() )
		self.context.initializeCallId()
		self.context.incrLocalCseq()
		self.context.setLocalBranch( genericFunctions.generateBranch() )
		self.context.setRemoteUri( self.context.buildRequestUri(value['called-uri'], self.domain) )
		self.context.setRemoteTarget( self.context.buildRequestUri(value['called-uri'], self.domain) ) 
		# create invite
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		toHeader = self.context.getToHeader()
		callId = self.context.callId
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + self.context.localBranch
		cseq = str(self.context.localCseq)
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		proxy = self.proxyIp + ':' + self.proxyPort
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy' : proxy,
							}
		if self.reliability == 'require':
			headers.update({'require': '100rel'})
		elif self.reliability == 'supported':
			headers.update({'supported': '100rel'})
		message = templateSipMessages.invite(fromHeader, toHeader, callId, via, cseq, self.context.remoteUri, maxforwards = self.ve.maxForwards, moreHeaders = headers)							
		# update headers
		if value.has_key('headers'):
			for (key, content) in value['headers'].items():
				key = key.lower()
				content = str(content)
				message.udpate({key:content})
			if not ('tag=' in message['from']):
				message['from'] = message['from'] + ';tag=' + self.context.localTag
			elif 'tag=' in message['from'] :
				self.context.localTag = genericFunctions.getTagInFrom(message['from'])
		# update additional Headers
		if value.has_key('additional-headers'):
			for (key, content) in value['additional-headers'].items():
				key = key.lower()
				content = str(content)
				if message.has_key(key):
						message[key] += "\n" + content
				else:
					message[key] = content
		# update id of call (self.calls)
		self.id = genericFunctions.getIdMessage(fromHeader = message['from'], callId = message['call-id'])
		# send invite
		self.initialRequest = message
		self.ve.sip.send(with_('sipve',message), proxy)
		# update state call and sip
		self.setCallState('outcoming-call-processing')
		self.setSipState('waiting-100-trying')
		# start to listening rtp 	
		self.rtp.startListening()
		self.ve.control.send( templateControlMessages.callId(self.callId, self.probeRtpPort) )
	def sendInviteWithSdp(self, value):
		self.incomingCall = False
		self.slowStart = not(value['sdp'])
		self.sdp.reset()
		if value.has_key('timer-between-200ok-ack'):
			self.timerBetween200andAckValue = value['timer-between-200ok-ack']
		# update local parameters
		self.initSessionWithNewEndpointParameters()
		# call logs
		self.logs.start(value['called-uri'], 'dialed')
		self.logs.setInviteTimestamp()
		# create context
		self.context.setLocalUri( self.puid, self.domain )
		self.context.setLocalTag( genericFunctions.generateTag() )
		self.context.initializeCallId()
		self.context.incrLocalCseq()
		self.context.setLocalBranch( genericFunctions.generateBranch() )
		self.context.setRemoteUri( self.context.buildRequestUri(value['called-uri'], self.domain) )
		self.context.setRemoteTarget( self.context.buildRequestUri(value['called-uri'], self.domain) ) 
		# create invite
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		toHeader = self.context.getToHeader()
		callId = self.context.callId
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + self.context.localBranch
		cseq = str(self.context.localCseq)
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		proxy = self.proxyIp + ':' + self.proxyPort
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy' : proxy,
								'content-type': 'application/sdp',
								'__body': self.sdp.getSdpOffer()
							}
		self.sdp.setSdpOfferSended()
		if self.reliability == 'require':
			headers.update({'require': '100rel'})
		elif self.reliability == 'supported':
			headers.update({'supported': '100rel'})
		message = templateSipMessages.invite(fromHeader, toHeader, callId, via, cseq, self.context.remoteUri, maxforwards = self.ve.maxForwards, moreHeaders = headers)							
		# update headers
		if value.has_key('headers'):
			for (key, content) in value['headers'].items():
				key = key.lower()
				content = str(content)
				message.update({key:content})
			if not ('tag=' in message['from']):
				message['from'] = message['from'] + ';tag=' + self.context.localTag
			elif 'tag=' in message['from'] :
				self.context.localTag = genericFunctions.getTagInFrom(message['from'])
		# update additional Headers
		if value.has_key('additional-headers'):
			for (key, content) in value['additional-headers'].items():
				key = key.lower()
				content = str(content)
				if message.has_key(key):
						message[key] += "\n" + content
				else:
					message[key] = content
		# update id of call (self.calls)
		self.id = genericFunctions.getIdMessage(fromHeader = message['from'], callId = message['call-id'])
		# send invite
		self.initialRequest = message
		self.ve.sip.send(with_('sipve',message), proxy)
		# update state call and sip
		self.setCallState('outcoming-call-processing')
		self.setSipState('waiting-100-trying')
		# start to listening rtp 	
		self.rtp.startListening()
		self.ve.control.send( templateControlMessages.callId(self.callId, self.probeRtpPort) )
		
	def sendPrack(self, rseq, cseq):
		rseq = rseq + ' ' + cseq
		toHeader = self.context.getToHeader()
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		callId = self.context.callId
		self.context.incrLocalCseq()
		cseq = str(self.context.localCseq)
		routes, requestUri = self.context.getRoutesAndRequestUri()	
		proxy = self.contructProxyValue(requestUri)
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy
							}
		if routes != None:
			headers.update({'route':routes})
		tmp = templateSipMessages.prack(fromHeader, toHeader, callId, via, cseq, requestUri, rseq, maxforwards = self.ve.maxForwards, moreHeaders = headers)
		self.requestToResend = tmp
		self.sendSipMessageExceptInvite( tmp, proxy )
		self.setSipState('waiting-prack-response')
	def sendPrackWithSdp(self, rseq, cseq):
		rseq = rseq + ' ' + cseq
		toHeader = self.context.getToHeader()
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		callId = self.context.callId
		self.context.incrLocalCseq()
		cseq = str(self.context.localCseq)
		routes, requestUri = self.context.getRoutesAndRequestUri()	
		proxy = self.contructProxyValue(requestUri)
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy
							}
		if routes != None:
			headers.update({'route':routes})
		if self.sdp.sdpOfferSended == True:
			self.sdp.setSdpAnswerSended()
			headers.update({'content-type': 'application/sdp'})
			headers.update({'__body': self.sdp.getSdpAnswer()})					
		else:
			self.sdp.setSdpOfferSended()
			headers.update({'content-type': 'application/sdp'})
			headers.update({'__body': self.sdp.getSdpOffer()})		
		tmp = templateSipMessages.prack(fromHeader, toHeader, callId, via, cseq, requestUri, rseq, maxforwards = self.ve.maxForwards, moreHeaders = headers)
		self.requestToResend = tmp
		self.sendSipMessageExceptInvite( tmp, proxy )
		self.setSipState('waiting-prack-response')
	def sendCancel(self, value = None):
		toHeader = self.initialRequest['to']
		requestUri = self.initialRequest['__requesturi']
		fromHeader = self.initialRequest['from']
		callId = self.initialRequest['call-id']
		cseq = self.initialRequest['cseq'].split(' ')[0]
		via = self.initialRequest['via']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		proxy = self.contructProxyValue(requestUri)
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy
							}
		message = templateSipMessages.cancel(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers)
		if value != None:
			# update headers
			if value.has_key('headers'):
				for (key, content) in value['headers'].items():
					key = key.lower()
					content = str(content)
					message.update({key:content})
				if not ('tag=' in message['from']):
					message['from'] = message['from'] + ';tag=' + self.context.localTag
				elif 'tag=' in message['from'] :
					self.context.localTag = genericFunctions.getTagInFrom(message['from'])
			# update additional Headers
			if value.has_key('additional-headers'):
				for (key, content) in value['additional-headers'].items():
					key = key.lower()
					content = str(content)
					if message.has_key(key):
							message[key] += "\n" + content
					else:
						message[key] = content		
		self.sendSipMessageExceptInvite( message, proxy )
		# stop rtp media
		self.rtp.stopSending()
		self.rtp.stopListening()
		# state changed
		self.setSipState('waiting-cancel-response')
	def sendAckToReInvite(self, error = False):
		toHeader = self.context.getToHeader()
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		callId = self.context.callId
		cseq = str(self.initialRequest['cseq'].split(' ')[0])
		routes, requestUri = self.context.getRoutesAndRequestUri()	
		proxy = self.contructProxyValue(requestUri)
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy
							}			
		if routes != None:
			headers.update({'route':routes})
		self.sendSipMessageExceptInvite( templateSipMessages.ack(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers), proxy )
		if error == False:
			if self.placingOnHold == True:
				self.rtp.stopSending()
				# state changed
				self.setCallState('on-hold')
				self.setSipState('connected')
				self.ve.control.send( templateControlMessages.isOnHold(self.callId) )
			elif self.placingOnHold == False:
				self.rtp.stopSending()
				self.startSendingRtp()
				# state changed
				self.setCallState('connected')
				self.setSipState('connected')
				self.ve.control.send( templateControlMessages.isCallUpdated(self.callId) )
		else:
			self.setSipState('connected')
			self.ve.debug('reinvite rejected')
	def sendAckToInvite(self):
		toHeader = self.context.getToHeader()
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		callId = self.context.callId
		cseq = str(self.initialRequest['cseq'].split(' ')[0])
		# The ACK must be sent according to the loose routes. 
		routes, requestUri, proxy = self.context.getRoutesAndRequestUriAndProxy()
		if not proxy:
			proxy = self.contructProxyValue(requestUri)
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy
							}	
		if routes != None:
			headers.update({'route':routes})
		if self.slowStart == True:
			if not self.reliability in ['require', 'supported' ]:
				self.sdp.setSdpAnswerSended()
				headers.update({'content-type': 'application/sdp'})
				headers.update({'__body': self.sdp.getSdpAnswer()})
		self.sendSipMessageExceptInvite( templateSipMessages.ack(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers), proxy )
		self.ve.control.send( templateControlMessages.isConnected(self.callId) )
		# state changed
		self.setCallState('connected')
		self.setSipState('connected')
	def sendBye(self, value = None):
		# callLog
		self.logs.setDurationConnected()
		# create bye
		toHeader = self.context.getToHeader()
		fromHeader = self.context.getFromHeader()
		if self.display != 'undefined':
			fromHeader = '"' + self.display + '" ' + fromHeader
		callId = self.context.callId
		self.context.incrLocalCseq()
		cseq = str(self.context.localCseq)
		# SL: ??? why requestUri ? routes + contact should be OK, and the next hop should
		# be either the route or the request URI...
		routes, requestUri, proxy = self.context.getRoutesAndRequestUriAndProxy()	
		if not proxy:
			proxy = self.contructProxyValue(requestUri)
		via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy
							}
		if routes != None:
			headers.update({'route':routes})
		message = templateSipMessages.bye(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers)
		if value != None:
			# update headers
			if value.has_key('headers'):
				for (key, content) in value['headers'].items():
					key = key.lower()
					content = str(content)
					message.update({key:content})
				if not ('tag=' in message['from']):
					message['from'] = message['from'] + ';tag=' + self.context.localTag
				elif 'tag=' in message['from'] :
					self.context.localTag = genericFunctions.getTagInFrom(message['from'])
			# update additional Headers
			if value.has_key('additional-headers'):
				for (key, content) in value['additional-headers'].items():
					key = key.lower()
					content = str(content)
					if message.has_key(key):
							message[key] += "\n" + content
					else:
						message[key] = content
		self.sendSipMessageExceptInvite( message, proxy )
		# stop rtp media
		self.rtp.stopSending()
		self.rtp.stopListening()
		# state changed
		self.setCallState('finishing')
		self.setSipState('waiting-bye-response')
	def sendUpdate(self, value):
		if value['sdp'] == True :
			toHeader = self.context.getToHeader()
			fromHeader = self.context.getFromHeader()
			if self.display != 'undefined':
				fromHeader = '"' + self.display + '" ' + fromHeader
			callId = self.context.callId
			self.context.incrLocalCseq()
			cseq = str(self.context.localCseq)
			routes, requestUri = self.context.getRoutesAndRequestUri()	
			proxy = self.contructProxyValue(requestUri)
			via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
			contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
			headers = { 'contact': contact,
									'user-agent': self.userAgent,
									'allow': self.ve.allow,
									'proxy': proxy,
									'content-type': 'application/sdp'
								}
			if self.sdp.sdpOfferReceived == False:
				self.sdp.setSdpOfferSended()
				headers.update({'__body': self.sdp.getSdpOffer()})
			else:
				self.sdp.setSdpAnswerSended()
				headers.update({'__body': self.sdp.getSdpAnswer()})		
			if routes != None:
				headers.update({'route':routes})
			message = templateSipMessages.update(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers) 
			self.sendSipMessageExceptInvite( message, proxy )
			# state changed
			self.setSipState('waiting-response-update')
		else:
			toHeader = self.context.getToHeader()
			fromHeader = self.context.getFromHeader()
			if self.display != 'undefined':
				fromHeader = '"' + self.display + '" ' + fromHeader
			callId = self.context.callId
			self.context.incrLocalCseq()
			cseq = str(self.context.localCseq)
			routes, requestUri = self.context.getRoutesAndRequestUri()	
			proxy = self.contructProxyValue(requestUri)
			via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
			contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
			headers = { 'contact': contact,
									'user-agent': self.userAgent,
									'allow': self.ve.allow,
									'proxy': proxy
								}
			if routes != None:
				headers.update({'route':routes})
			message = templateSipMessages.update(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers) 
			self.sendSipMessageExceptInvite( message, proxy )
			# state changed
			self.setInfoState('waiting-response-update')
	def sendAck(self, msg):
		toHeader = msg['to']
		callId = self.context.callId
		cseq = str(self.initialRequest['cseq'].split(' ')[0])
		via = self.initialRequest['via']
		requestUri = self.initialRequest['__requesturi']
		fromHeader = self.initialRequest['from']
		proxy = self.contructProxyValue(requestUri)
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
								'proxy': proxy
							}
		self.sendSipMessageExceptInvite( templateSipMessages.ack(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers), proxy )
		self.logs.setStatus('failed')
		self.logs.stop()
		self.reset()
	def sendRefer(self, type,  uri = None, sessionTo = None):
		status = False
		if uri != None:
			self.referTo = self.context.buildRequestUri(uri, self.domain, phone = False)
			status = True
		elif sessionTo != None:
			if sessionTo.context.remoteUri != None:
				if ';user=phone' in sessionTo.context.remoteUri:
					self.referTo = sessionTo.context.remoteUri.split(';user=phone')[0]
				else:
					self.referTo = sessionTo.context.remoteUri
				self.referTo += '?Replaces=' + sessionTo.context.callId.replace('@', '%40')
				if sessionTo.context.remoteTag != None and sessionTo.context.localTag != None:
					self.referTo += '%3Bto-tag%3D' + sessionTo.context.remoteTag  + '%3Bfrom-tag%3D' + sessionTo.context.localTag
					status = True
				elif sessionTo.context.remoteTag != None and sessionTo.context.localTag == None:
					self.referTo += '%3Bto-tag%3D' + sessionTo.context.remoteTag
					status = True
				elif sessionTo.context.remoteTag == None and sessionTo.context.localTag != None:
					self.referTo += '%3Bfrom-tag%3D' + sessionTo.context.localTag
					status = True
				else:
					self.ve.debug('error to send a refer')
			else:
				self.ve.debug('error to send a refer')
		if status == True:
			self.typeOfTransfer = type
			# create refer
			toHeader = self.context.getToHeader()
			fromHeader = self.context.getFromHeader()
			if self.display != 'undefined':
				fromHeader = '"' + self.display + '" ' + fromHeader
			callId = self.context.callId
			self.context.incrLocalCseq()
			cseq = str(self.context.localCseq)
			routes, requestUri = self.context.getRoutesAndRequestUri()	
			proxy = self.contructProxyValue(requestUri)
			via = 'SIP/2.0/UDP ' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + ';branch=z9hG4bK' + genericFunctions.generateBranch()
			contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
			headers = { 'contact': contact,
									'user-agent': self.userAgent,
									'proxy': proxy,
									'refer-to': '<' + self.referTo + '>',
									'referred-by': '<' + self.context.localUri + '>'
								}
			if routes != None:
				headers.update({'route':routes})
			self.sendSipMessageExceptInvite( templateSipMessages.refer(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = self.ve.maxForwards, moreHeaders = headers), proxy )
			# state changed
			self.setReferState('waiting-refer-response')
				
	def send200OkToInvite(self):
		# call logs
		self.logs.set200OkTimestamp()
		# contruct response
		toHeader = self.initialRequest['to'] + ';tag=' + self.context.localTag
		fromHeader = self.initialRequest['from']
		callId = self.initialRequest['call-id']
		cseq = self.initialRequest['cseq']
		via = self.initialRequest['via']
		# When sending a response, we ignore the Via header to get the next IP:port host.
		# Instead, we reply on the same ip:port as we received the request from.
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow}
		# added sdp answer to 200 ok
		if self.earlyMedia == False :
			if self.reliabilityIn == False:
				if self.sdp.sdpOfferReceived == True:
					body = self.sdp.getSdpAnswer()
				else:
					body = self.sdp.getSdpOffer()
				headers.update({'content-type': 'application/sdp', '__body': body})
		if self.initialRequest.has_key('record-route'):
			headers.update({'record-route':self.initialRequest['record-route']})
		response = templateSipMessages.response200(fromHeader, toHeader, callId, via, cseq, headers)
		self.requestToResend = response
		self.ve.sip.send(with_('sipve', response), self.initialRequest['__source'])
		# update call key in calls
		self.id = genericFunctions.getIdMessage(fromHeader = response['from'], toHeader = response['to'], callId = response['call-id'])
		# state changed
		self.setSipState('waiting-ack')
		self.response200Timer.start()
	def sendBasicResponse(self, code, phrase, request, contactOverwrite = None):
		# create response
		toHeader = request['to'] 
		fromHeader = request['from']
		callId = request['call-id']
		cseq = request['cseq']
		via = request['via']
		if contactOverwrite != None:
			contact = '<' + self.context.buildRequestUri( contactOverwrite, self.domain) + '>'
		else:
			contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
							}
		msg = templateSipMessages.basicSendResponse( code, phrase, fromHeader, toHeader, callId, via, cseq, headers)
		self.ve.sip.send(with_('sipve', msg), request['__source'])	
	#######################
	def resend200Ok(self):
		if self.getSipState() == 'connected':
			self.ve.control.send( templateControlMessages.retransmissionFinished("200 ok") )
		else:
			if self.nbRetranmission < self.nbRetranmissionMax:
				self.nbRetranmission += 1
				if self.requestToResend != None : 
					self.ve.sip.send(with_('sipve', self.requestToResend), self.proxy)
				else:
					self.ve.debug('request to resend is empty')
				self.nextTimeout += int(self.nextTimeout * self.nbRetranmission * 0.3)
				self.response200Timer = Timer(self.nextTimeout, '200 ok retransmission %s sec.' % (self.nextTimeout))
				self.response200Timer.start()
			else:
				self.ve.control.send( templateControlMessages.retransmissionFinished("200 ok") )
				self.sendBye()
	def resend180Rel(self):
		if self.nbRetranmission < self.nbRetranmissionMax:
			self.nbRetranmission += 1
			if self.requestToResend != None : 
				self.ve.sip.send(with_('sipve', self.requestToResend) , self.proxy)
			else:
				self.ve.debug('request to resend is empty')
			self.nextTimeout += int(self.nextTimeout * self.nbRetranmission * 0.3)
			self.relTimer = Timer(self.nextTimeout, '180 retransmission %s sec.' % (self.nextTimeout))
			self.relTimer.start()
		else:
			self.ve.control.send( templateControlMessages.retransmissionFinished("180 rel") )
	#######################
	def receivedUpdate(self, update):
		# update context
		if update.has_key('contact'):
			self.context.setRemoteTarget( update['contact'].split('>')[0][1:] )
		desc = {}
		if update.has_key('from-display'):
			self.context.setRemoteDisplay( update['from-display'])
			desc.update({'display':self.context.remoteDisplay})
		if update.has_key('p-asserted-identity'):
			self.pAssertedIdentity = update['p-asserted-identity']
			desc.update({'p-asserted-identity':self.pAssertedIdentity})
		desc.update( {'cli': genericFunctions.getCliInFrom(update['from']) } )
		self.ve.control.send( templateControlMessages.eventUpdate(callId = self.callId, descriptions = desc) )
		# send 200 ok to update
		self.sendBasicResponse('200', 'OK', update)
	def receivedUpdateWithSdp(self, update):
		# update context
		if update.has_key('contact'):
			self.context.setRemoteTarget( update['contact'].split('>')[0][1:] )
		desc = {}
		if update.has_key('from-display'):
			self.context.setRemoteDisplay( update['from-display'])
			desc.update({'display':self.context.remoteDisplay})
		if update.has_key('p-asserted-identity'):
			self.pAssertedIdentity = update['p-asserted-identity']
			desc.update({'p-asserted-identity':self.pAssertedIdentity})
		desc.update( {'cli': genericFunctions.getCliInFrom(update['from']) } )
		self.ve.control.send( templateControlMessages.eventUpdate(callId = self.callId, descriptions = desc) )
		# send 200 ok to update
		self.sdp.setSdpOfferReceived()
		self.codecChoosed, ip, port = self.sdp.decodeSdpAndNegociateCodec(update['__body'])
		if self.codecChoosed == None:
			self.ve.debug('negociation codec failed')
			self.ve.sip.send(with_('sipve', templateSipMessages.response606(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
			self.setSipState('waiting-ack-error')
		else:
			self.rtp.setIpTo(ip)
			self.rtp.setPortTo(port)
			self.rtp.stopSending()
			if self.earlyMedia == True :
					self.startSendingRtp()
			# send 200Ok with sdp answer 
			toHeader = update['to'] 
			fromHeader = update['from']
			callId = update['call-id']
			cseq = update['cseq']
			via = update['via']
			contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
			headers = { 'contact': contact,
									'user-agent': self.userAgent,
									'allow': self.ve.allow,
								}
			if self.sdp.sdpOfferReceived == True:
				body = self.sdp.getSdpAnswer()
			headers.update({'content-type': 'application/sdp', '__body': body})
			msg = templateSipMessages.basicSendResponse( '200', 'OK', fromHeader, toHeader, callId, via, cseq, headers)
			self.ve.sip.send(with_('sipve', msg), self.proxy )		
	def receivedInfo(self, info):
		if info.has_key('content-type') and info['content-type'] == 'application/dtmf-relay':
			if info.has_key('__body'):
				# parse body
				body = info['__body']
				body = body.splitlines()
				signal = None
				duration = None
				for i in body:
					if i.startswith('Signal')	:
						signal = i.split('=')[1]
					if i.startswith('Duration')	:
						duration = i.split('=')[1]
			else:
				self.ve.debug('body not present!')
			self.ve.control.send( templateControlMessages.eventDtmf(signal, duration)) 
		else:
			if info.has_key('__body'):
				body = info['__body']
			else:
				body = 'empty'
			self.ve.control.send( templateControlMessages.infoReceived( self.callId, info['content-type'], body) )
		# send 200 ok to notify
		self.sendBasicResponse('200', 'OK', info)
	def receivedNotify(self, notify):
		if self.getReferState() in ['transfer-in-progress', 'waiting-refer-response' ]:
			if notify.has_key('subscription-state'):
				state = notify['subscription-state'].split(';')[0]
				if notify.has_key('__body'): 
					body = notify['__body']
				else: 
					self.ve.debug('body empty')
					body = 'empty'
				desc = {}
				desc.update({'event-name': notify['event']})
				desc.update({'subscription-state': state})
				desc.update({'body': body})
				desc.update({'call-id': str(self.callId)})
				self.ve.control.send( templateControlMessages.notify(descriptions = desc)) 
				# send 200 ok to notify
				toHeader = notify['to'] 
				fromHeader = notify['from']
				callId = notify['call-id']
				cseq = notify['cseq']
				via = notify['via']
				contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
				headers = { 'contact': contact,
										'user-agent': self.userAgent,
										'allow': self.ve.allow,
									}
				msg = templateSipMessages.response200( fromHeader, toHeader, callId, via, cseq, headers)
				self.ve.sip.send(with_('sipve', msg), self.proxy )
				# parse body
				if body != 'empty':
					bodyParsed = body.split(' ')[1]
					if bodyParsed.startswith('1') and  self.typeOfTransfer == 'blind':
						self.ve.debug('blind transfer activated')
						self.ve.control.send( templateControlMessages.transferSuccessful(self.callId))
						self.sendBye()
					elif bodyParsed.startswith('2')	and self.typeOfTransfer == 'attendant':
						self.ve.debug('attendant transfer activated')	
						self.ve.control.send( templateControlMessages.transferSuccessful(self.callId))
						self.setCallState('connected')	
						self.sendBye()
					elif bodyParsed.startswith('4') :
						self.ve.control.send( templateControlMessages.transferFailed(self.callId))
						self.setReferState('idle')
					elif bodyParsed.startswith('5') :
						self.ve.control.send( templateControlMessages.transferFailed(self.callId))
						self.setReferState('idle')
					elif 	bodyParsed.startswith('6') :
						self.ve.control.send( templateControlMessages.transferFailed(self.callId))
						self.setReferState('idle')
					else:
						"""todo"""
			else:
				self.ve.debug('error to parse notify, subscription-state header is mandatory')	
		else:
			self.ve.debug('notify received in sip state ' + str(self.getReferState()) + ': not analysed' )	
			self.ve.sendGenericResponse('488', 'Not Acceptable Here', notify)
	def receivedPrack(self, prack):
		if self.getSipState() == 'waiting-prack':
			if self.earlyMedia == True:
				self.relTimer.setNewName('183 rel retransmission')
			else:
				self.relTimer.setNewName('180 rel retransmission')
			self.relTimer.stop()
			if prack['rack'] == str(self.context.localRseq) + ' ' + self.initialRequest['cseq']:
				# send bacic 200 ok to prack
				if 	self.sdp.sdpAnswerSended  == True:
					self.rtp.startListening()
					self.startSendingRtp()
				self.sendBasicResponse( '200', 'OK', prack)
				# state changed
				self.setSipState('ringing')
				self.ve.control.send( templateControlMessages.prackReceived( self.callId ) )
				
			else:
				# send 481 to prack
				self.sendBasicResponse( '481', 'Call/Transaction Does Not Exist', prack)	
		else:
			self.ve.debug('prack received in sip state ' + str(self.getSipState()) + ': not analysed' )
	def receivedPrackWithSdp(self, prack):
		if self.getSipState() == 'waiting-prack':
			if self.earlyMedia == True:
				self.relTimer.setNewName('183 rel retransmission')
			else:
				self.relTimer.setNewName('180 rel retransmission')
			self.relTimer.stop()
			if prack['rack'] == str(self.context.localRseq) + ' ' + self.initialRequest['cseq']:
				# send bacic 200 ok to prack
				if 	self.sdp.sdpOfferSended  == True:
					# sdp processing (decode + chooses codec)
					self.codecChoosed, ip, port = self.sdp.decodeSdpAndNegociateCodec(prack['__body'])
					if self.codecChoosed == None:
						self.ve.debug('negociation codec failed')
						self.sendBye()
					else:
						self.rtp.setIpTo(ip)
						self.rtp.setPortTo(port)
						self.rtp.startListening()
				self.sendBasicResponse( '200', 'OK', prack)
				# state changed
				self.setSipState('ringing')
				self.ve.control.send( templateControlMessages.prackReceived( self.callId ) )
			else:
				# send 481 to prack
				self.sendBasicResponse( '481', 'Call/Transaction Does Not Exist', prack)
		else:
			self.ve.debug('prack received in sip state ' + str(self.getSipState()) + ': not analysed' )
	def receivedReInviteWithSdp(self, reinvite):
		# update context
		if reinvite.has_key('contact'):
			self.context.setRemoteTarget( reinvite['contact'].split('>')[0][1:] )
		# create response to invite
		fromHeader = reinvite['from']
		toHeader = reinvite['to']
		callId = self.context.callId
		via = reinvite['via']
		cseq = reinvite['cseq']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow}
		if reinvite.has_key('record-route'):
			headers.update({'record-route':self.context.routeSet})
		# update session sdp
		self.codecChoosed, ip, port = self.sdp.decodeSdpAndNegociateCodec(reinvite['__body'])
		if self.codecChoosed == None:
			self.ve.debug('negociation codec failed')
			self.ve.sip.send(with_('sipve', templateSipMessages.response606(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
			self.setSipState('waiting-ack-error-reinvite')
		else:
			self.initialRequest = reinvite
			# stop media
			self.rtp.stopSending()
			self.rtp.setIpTo(ip)
			self.rtp.setPortTo(port)
			# added sdp answer to 200 ok
			headers.update({'content-type': 'application/sdp'})
			headers.update({'__body': self.sdp.getSdpAnswerReInvite()})
			self.requestToResend = templateSipMessages.response200(fromHeader, toHeader, callId, via, cseq, headers)
			self.ve.sip.send(with_('sipve', self.requestToResend), self.proxy )
			self.response200Timer.start()
			# state changed
			self.setSipState('waiting-ack-reinvite')
			
	def receivedReInvite(self, reinvite):
		# update context
		if reinvite.has_key('contact'):
			self.context.setRemoteTarget( reinvite['contact'].split('>')[0][1:] )
		# stop media
		self.sdpReceived = None
		# create response to invite
		fromHeader = reinvite['from']
		toHeader = reinvite['to']
		callId = self.context.callId
		via = reinvite['via']
		cseq = reinvite['cseq']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow}
		# added sdp answer to 200 ok
		self.sdp.setSdpOfferSended()
		headers.update({'content-type': 'application/sdp'})
		headers.update({'__body': self.sdp.getSdpOffer()})	
		if reinvite.has_key('record-route'):
			headers.update({'record-route':self.context.routeSet})
		self.requestToResend = templateSipMessages.response200(fromHeader, toHeader, callId, via, cseq, headers)
		self.ve.sip.send(with_('sipve', self.requestToResend), self.proxy )
		self.response200Timer.start()
		# state changed
		self.setSipState('waiting-ack-reinvite')
			
	def receivedInvite(self, invite, reliability):
		self.incomingCall = True
		self.reliabilityIn = reliability
		self.sdp.reset()
		# update local parameters
		self.initSessionWithNewEndpointParameters()
		# call logs
		self.logs.start(str(invite['from']).split('>')[0].split('<')[1], 'received')
		self.logs.setInviteTimestamp()
		# state changed
		self.setCallState('incoming-call-processing')
		self.setSipState('ringing')
		# create context
		if invite.has_key('record-route'):
			self.context.setRouteSet( invite['record-route'])
		if invite.has_key('from-display'):
			self.context.setRemoteDisplay( invite['from-display'])
		if invite.has_key('diversion'):
			self.context.setRemoteDiversion( invite['diversion'])	
		if invite.has_key('p-asserted-identity'):
			self.pAssertedIdentity = invite['p-asserted-identity']
		if invite.has_key('contact'):
			self.context.setRemoteTarget( invite['contact'].split('>')[0][1:] )
		#
		self.context.setCallId( invite['call-id'])	
		self.context.setRemoteCseq( invite['cseq'].split(' ')[0] )		
		self.context.setRemoteTag( genericFunctions.getTagInFrom(invite['from']) )
		self.context.setRemoteUri( invite['from'].split('<')[1].split('>')[0] )
		self.context.setLocalUri( invite['to'].split('<')[1].split('>')[0] )
		self.context.setLocalTag( genericFunctions.generateTag() )
		self.context.setCallLineIdentifier( genericFunctions.getCliInFrom(invite['from']))
		self.initialRequest = invite
		# message
		fromHeader = invite['from']
		toHeader = invite['to']
		callId = self.context.callId
		via = invite['via']
		cseq = invite['cseq']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow }
		if invite.has_key('record-route'):
			headers.update({'record-route':self.context.routeSet})
		# processing
		desc = {}
		if self.probeRtpPort != None:
			desc.update({'rtp-port':  self.probeRtpPort})
		if self.context.remoteDisplay != None:
			desc.update({'display':  self.context.remoteDisplay})
		if self.context.remoteDiversion != None:
			desc.update({'diversion':  self.context.remoteDiversion})
		if self.context.callLineIdentifier != None:
			desc.update({'cli':  self.context.callLineIdentifier})
		if self.pAssertedIdentity != None:
			desc.update({'p-asserted-identity':  self.pAssertedIdentity})
		if 'sip:' in invite['__requesturi']:
			desc.update( {'request-uri':invite['__requesturi'].split('sip:')[1].split('@')[0]})
		else:
			desc.update( {'request-uri':invite['__requesturi'].split('tel:')[1].split('@')[0]})
		if self.autoResponse == True:
			toHeader = invite['to'] + ';tag=' + self.context.localTag
			self.ve.debug("auto response on incoming call")
			self.ve.control.send( templateControlMessages.isRinging(self.callId, descriptions = desc) )
			self.send200OkToInvite()
		else:
			self.ve.sip.send(with_('sipve', templateSipMessages.response100(fromHeader, toHeader, callId, via, cseq, headers)), invite['__source'] )
			toHeader = invite['to'] + ';tag=' + self.context.localTag
			# prack
			if reliability == True:
				self.context.incrLocalRseq()
				headers.update({'rseq':self.context.localRseq})
				headers.update({'require': '100rel'})
				# added sdp answer
				self.sdp.setSdpOfferSended()
				headers.update({'content-type': 'application/sdp'})
				headers.update({'__body': self.sdp.getSdpOffer()})
				self.setSipState('waiting-prack')
				self.relTimer.start()
			if self.earlyMedia == True:
				self.requestToResend = templateSipMessages.response183(fromHeader, toHeader, callId, via, cseq, headers)
			else:
				self.requestToResend  = templateSipMessages.response180(fromHeader, toHeader, callId, via, cseq, headers)
			self.ve.sip.send(with_('sipve', self.requestToResend), invite['__source'] )
			self.ve.control.send( templateControlMessages.isRinging(self.callId, descriptions = desc ) )
		# update id call
		self.id = genericFunctions.getIdMessage(fromHeader = fromHeader, toHeader = toHeader, callId = callId, cseq = cseq)
			
	def receivedInviteWithSdp(self, invite, reliability):
		self.incomingCall = True
		self.reliabilityIn = reliability
		self.sdp.reset()
		# update local parameters
		self.initSessionWithNewEndpointParameters()
		# call logs
		self.logs.start( str(invite['from']).split('>')[0].split('<')[1] , 'received')
		self.logs.setInviteTimestamp()
		# state changed
		self.setCallState('incoming-call-processing')
		self.setSipState('ringing')
		# create context
		if invite.has_key('record-route'):
			self.context.setRouteSet( invite['record-route'])
		if invite.has_key('from-display'):
			self.context.setRemoteDisplay( invite['from-display'])
		if invite.has_key('diversion'):
			self.context.setRemoteDiversion( invite['diversion'])		
		if invite.has_key('p-asserted-identity'):
			self.pAssertedIdentity = invite['p-asserted-identity']	
		if invite.has_key('contact'):
			self.context.setRemoteTarget( invite['contact'].split('>')[0][1:] )
		self.context.setCallId( invite['call-id'])	
		self.context.setRemoteCseq( invite['cseq'].split(' ')[0] )		
		self.context.setRemoteTag( genericFunctions.getTagInFrom(invite['from']) )
		self.context.setRemoteUri( invite['from'].split('<')[1].split('>')[0] )
		self.context.setLocalUri( invite['to'].split('<')[1].split('>')[0] )
		self.context.setLocalTag( genericFunctions.generateTag() )	
		self.context.setCallLineIdentifier( genericFunctions.getCliInFrom(invite['from']))
		self.initialRequest = invite
		# create response to invite
		fromHeader = invite['from']
		toHeader = invite['to']
		callId = self.context.callId
		via = invite['via']
		cseq = invite['cseq']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								}#'user-agent': self.userAgent,}
								#'allow': self.ve.allow}
		if invite.has_key('record-route'):
			headers.update({'record-route':self.context.routeSet})
		desc = {}
		if self.probeRtpPort != None:
			desc.update({'rtp-port':  self.probeRtpPort})
		if self.context.remoteDisplay != None:
			desc.update({'display':  self.context.remoteDisplay})
		if self.context.remoteDiversion != None:
			desc.update({'diversion':  self.context.remoteDiversion})
		if self.context.callLineIdentifier != None:
			desc.update({'cli':  self.context.callLineIdentifier})
		if self.pAssertedIdentity != None:
			desc.update({'p-asserted-identity':  self.pAssertedIdentity})
		if 'sip:' in invite['__requesturi']:
			desc.update( {'request-uri':invite['__requesturi'].split('sip:')[1].split('@')[0]})
		else:
			desc.update( {'request-uri':invite['__requesturi'].split('tel:')[1].split('@')[0]})
		# sdp processing (decode + chooses codec)
		self.sdp.setSdpOfferReceived()
		self.codecChoosed, ip, port = self.sdp.decodeSdpAndNegociateCodec(invite['__body'])
		if self.codecChoosed == None:
			self.ve.debug('negociation codec failed')
			self.ve.sip.send(with_('sipve', templateSipMessages.response606(fromHeader, toHeader, callId, via, cseq, headers)), invite['__source'] )
			self.setSipState('waiting-ack-error')
		else:
			self.rtp.setIpTo(ip)
			self.rtp.setPortTo(port)
			self.rtp.startListening()
			# Processing
			if self.autoResponse == True:
				toHeader = invite['to'] + ';tag=' + self.context.localTag
				self.ve.debug("auto response on incoming call")
				self.ve.control.send( templateControlMessages.isRinging(self.callId, descriptions = desc) )
				self.send200OkToInvite()
			else:
				self.ve.sip.send(with_('sipve', templateSipMessages.response100(fromHeader, toHeader, callId, via, cseq, headers)), invite['__source'] )
				toHeader = invite['to'] + ';tag=' + self.context.localTag
				# prack
				if reliability == True:
					self.context.incrLocalRseq()
					headers.update({'rseq':self.context.localRseq})
					headers.update({'require': '100rel'})
					# added sdp answer
					self.sdp.setSdpAnswerSended()
					headers.update({'content-type': 'application/sdp'})
					headers.update({'__body': self.sdp.getSdpAnswer()})
					self.setSipState('waiting-prack')
					self.relTimer.start()
				if self.earlyMedia == True:
					self.requestToResend = templateSipMessages.response183(fromHeader, toHeader, callId, via, cseq, headers)
				else:
					self.requestToResend = templateSipMessages.response180(fromHeader, toHeader, callId, via, cseq, headers)
				self.ve.sip.send(with_('sipve', self.requestToResend), invite['__source'] )
				self.ve.control.send( templateControlMessages.isRinging(self.callId, descriptions = desc) )
		# update id call
		self.id = genericFunctions.getIdMessage(fromHeader = fromHeader, toHeader = toHeader, callId = callId, cseq = cseq)
		
	def receivedBye(self, request):
		# callLog
		self.logs.setDurationConnected()
		self.logs.stop()
		if request.has_key('from-display'):
			self.context.setRemoteDisplay( request['from-display'])
		cause = None
		if request.has_key('reason'):
			cause = request['reason']
		desc = {}
		if cause != None:
			desc.update({'reason':cause})
		if self.context.remoteDisplay != None:
			desc.update({'display': self.context.remoteDisplay })
		# send 200 ok to bye
		self.sendBasicResponse('200', 'OK', request)
		#
		self.rtp.stopSending()
		self.rtp.stopListening()
		self.ve.control.send( templateControlMessages.isDisconnected(self.callId, descriptions = desc) )
		self.reset()
	def receivedAckToInfo(self, request):	
		if self.getInfoState() == 'waiting-ack-cancelling-info' :
			self.setInfoState('idle')
		else:
			self.ve.debug('ack received in info state ' + str(self.getInfoState()) + ': not analysed' )		
	def receivedAckToReInvite(self, request):	
		if self.getSipState() == 'waiting-ack-reinvite':
			self.response200Timer.stop()
			self.startSendingRtp()
			self.setCallState('connected')
			self.setSipState('connected')
			self.ve.control.send( templateControlMessages.isCallUpdated(self.callId) )
		elif self.getSipState() == 'waiting-ack-error-reinvite' :
			self.setSipState('connected')
		else:
			self.ve.debug('ack received in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def receivedAckWithSdpToReInvite(self, request):		
		if self.getSipState() == 'waiting-ack-reinvite':
			self.response200Timer.stop()
			# sdp processing (decode + chooses codec)
			self.codecChoosed, ip, port = self.sdp.decodeSdpAndNegociateCodec(request['__body'])
			if self.codecChoosed == None:
				self.ve.debug('negociation codec failed')
				self.ve.sip.send(with_('sipve', templateSipMessages.response606(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
				self.setSipState('waiting-ack-error-reinvite')
			else:
				self.rtp.setIpTo(ip)
				self.rtp.setPortTo(port)
				self.rtp.stopSending()
				self.startSendingRtp()
				# state changed
				self.setCallState('connected')
				self.setSipState('connected')
				self.ve.control.send( templateControlMessages.isCallUpdated(self.callId) )
		elif self.getSipState() == 'waiting-ack-error-reinvite' :
			self.setSipState('connected')
		else:
			self.ve.debug('ack received in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def receivedAckToInvite(self, request):	
		if self.getSipState() == 'waiting-ack':
			self.response200Timer.stop()
			# state changed
			self.setCallState('connected')
			self.setSipState('connected')
			self.ve.control.send( templateControlMessages.isConnected(self.callId) )
			if self.sdp.sdpReceived != None:
				self.rtp.startListening()
				self.startSendingRtp()
				self.sdp.reset()
			else:
				self.ve.debug('no sdp session received') 
				self.sendBye()
		else:
			self.ve.debug('ack received in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
			
	def receivedAckWithSdpToInvite(self, request):
		if self.getSipState() == 'waiting-ack':
			self.response200Timer.stop()
			# state changed
			self.setCallState('connected')
			self.setSipState('connected')	
			self.ve.control.send( templateControlMessages.isConnected(self.callId) )
			if self.sdp.sdpAnswerReceived == False:
				# sdp processing (decode + chooses codec)
				self.codecChoosed, ip, port = self.sdp.decodeSdpAndNegociateCodec(request['__body'])
				if self.codecChoosed == None:
					self.ve.debug('negociation codec failed')
					self.sendBye()
				else:
					self.rtp.setIpTo(ip)
					self.rtp.setPortTo(port)
					self.rtp.startListening()
					self.startSendingRtp()
					self.sdp.reset()
			else:
				self.ve.debug('received ack with sdp but sdp negociation already done')
		else:
			self.ve.debug('ack received in sip state ' + str(self.getSipState()) + ': not analysed' )			
	def receivedAck(self, request):
		if self.getSipState() == 'waiting-ack-byeing' :
			self.sendBye()
		elif self.getSipState() == 'waiting-ack-cancelling' :
			self.logs.setStatus('missed')
			self.logs.stop()
			self.ve.control.send( templateControlMessages.isCancelled(self.callId) )
			self.reset()
		elif self.getSipState() == 'waiting-ack-error' :
			self.reset()	
		else:
			self.ve.debug('ack received in sip state ' + str(self.getSipState()) + ': not analysed' )	
	
	def receivedCancelToInfo(self, request):
		toHeader = request['to'] 
		fromHeader = request['from']
		callId = request['call-id']
		cseq = request['cseq']
		via = request['via']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
							}
		if request['cseq'].split(' ')[0] == self.infoRequest['cseq'].split(' ')[0]:
			if self.getInfoState() in ['waitin-info-response'] :
				cause = None
				if request.has_key('reason'):
					cause = request['reason']
				self.ve.control.send( templateControlMessages.cancelReceived(self.callId, reason = cause) )
				# send 200 ok
				self.ve.sip.send(with_('sipve', templateSipMessages.response200(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
				# send 487
				toHeader = request['to'] 
				fromHeader = self.infoRequest['from']
				callId = self.infoRequest['call-id']
				cseq = self.infoRequest['cseq']
				via = self.infoRequest['via']
				contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
				headers = { 'contact': contact,
										'user-agent': self.userAgent,
										'allow': self.ve.allow,
									}
				self.ve.sip.send(with_('sipve', templateSipMessages.response487(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
				# update state
				self.setInfoState('waiting-ack-cancelling-info')
			else:
				# send 488
				self.ve.sip.send(with_('sipve', templateSipMessages.response488(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
		else:
			# send 400
			self.ve.sip.send(with_('sipve', templateSipMessages.response400(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
	def receivedCancelToInvite(self, request):
		toHeader = request['to'] 
		fromHeader = request['from']
		callId = request['call-id']
		cseq = request['cseq']
		via = request['via']
		contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
		headers = { 'contact': contact,
								'user-agent': self.userAgent,
								'allow': self.ve.allow,
							}
		if request['cseq'].split(' ')[0] == self.initialRequest['cseq'].split(' ')[0]:
			
			if self.getSipState() in ['ringing'] :
				cause = None
				if request.has_key('reason'):
					cause = request['reason']
				self.ve.control.send( templateControlMessages.cancelReceived(self.callId, reason = cause) )
				# send 200 ok
				self.ve.sip.send(with_('sipve', templateSipMessages.response200(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
				# stop rtp media
				self.rtp.stopListening()
				self.rtp.stopSending()
				# send 487
				fromHeader = self.initialRequest['from']
				callId = self.initialRequest['call-id']
				cseq = self.initialRequest['cseq']
				via = self.initialRequest['via']
				contact = '<sip:' + self.puid + '@' + self.ve.sipSourceIp + ':' + self.ve.sipSourcePort + '>'	
				headers = { 'contact': contact,
										'user-agent': self.userAgent,
										'allow': self.ve.allow,
									}
				self.ve.sip.send(with_('sipve', templateSipMessages.response487(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
				# update state
				self.setSipState('waiting-ack-cancelling')
			elif self.getSipState() in ['waiting-ack', 'waiting-ack-byeing', 'waiting-ack-error' ] :
				# send 200 ok
				self.ve.sip.send(with_('sipve', templateSipMessages.response200(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
			else:
				# send 488
				self.ve.sip.send(with_('sipve', templateSipMessages.response488(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
		else:
			# send 400
			self.ve.sip.send(with_('sipve', templateSipMessages.response400(fromHeader, toHeader, callId, via, cseq, headers)), self.proxy )
		
	########################
	def startSendingRtp(self):
		"""
		
		"""
		if self.ve.playWav == True:
			self.rtp.startSending(self.codecChoosed, self.audioId)
			if self.ve.resourceWav != None:
				self.rtp.startPlayWav(self.ve.resourceWav)
			else:
				self.ve.control.send( templateControlMessages.configurationFailed(reason = 'The resource wav is not present!') )
		else:
			self.rtp.startSending(self.codecChoosed, self.audioId)
	def sendSipMessageExceptInvite(self, msg, proxy):
		self.secondRequest = msg
		if not ':' in proxy:
			# Add the default proxy port
			proxy = proxy + ':5060'
		self.ve.sip.send(with_('sipve', msg), proxy)
class ResponseToInvite(GenericResponse):
	"""
	"""
	def analyse1xxResponseCode(self, msg):
		# received 100
		if msg['__responsecode'] == '100':		
			self.received100Trying(msg)
		else:
		# received other response code	
			if msg.has_key('content-type') and msg['content-type'] == 'application/sdp':
				self.received1xxExcept100WithSdp(msg)
			else:
				self.received1xxExcept100(msg) # may be stop timer for invite todo	
	def received1xxExcept100(self, response):
		if self.session.getSipState() in ['ringback-tone', "waiting-100-trying"] :
			self.session.context.setRemoteTag( genericFunctions.getTagInTo(response['to']) )
			self.session.context.setCallLineIdentifier( genericFunctions.getCliInFrom(response['from']))
			if response.has_key('from-display'):
				self.session.context.setRemoteDisplay( response['from-display'])
			if response.has_key('p-asserted-identity'):
				self.session.pAssertedIdentity = response['p-asserted-identity']	
			if response.has_key('record-route'):	
				self.session.context.setRouteSet ( self.session.context.reverseRecordRoute(response['record-route']) ) 
			if response.has_key('contact'):
				"""todo""" 
				self.session.context.setRemoteTarget( response['contact'].split('>')[0].split('<')[1] )
			self.session.setSipState('ringback-tone')
			
			desc = {}
			if self.session.context.remoteDisplay != None:
				desc.update({'display':  self.session.context.remoteDisplay})
			if self.session.context.callLineIdentifier != None:
				desc.update({'cli':  self.session.context.callLineIdentifier})
			if self.session.pAssertedIdentity != None:
				desc.update({'p-asserted-identity':  self.session.pAssertedIdentity})
			self.ve.control.send( templateControlMessages.isRingBackTone(self.session.callId,descriptions = desc))
			# prack
			if self.session.reliability == 'require':
				if response.has_key('require') and '100rel' in response['require']:
					if response.has_key('rseq'):
						self.session.sendPrack(response['rseq'], response['cseq'])
					else:
						self.session.sendCancel()
						self.ve.control.send( templateControlMessages.info(str(response['__responsecode']) + ' received with a \'require\' header setted to 100rel and no rseq is presented.') )						
				else:
					self.session.sendCancel()
					self.ve.control.send( templateControlMessages.info(str(response['__responsecode']) + ' received without any \'require\' headers setted to 100rel') )						
			elif self.session.reliability == 'supported':
				if response.has_key('require') and '100rel' in response['require']:
					if response.has_key('rseq'):
						self.session.sendPrack( response['rseq'], response['cseq'] )
					else:
						self.session.sendCancel()
						self.ve.control.send( templateControlMessages.info(str(response['__responsecode']) + ' received with a \'require\' header setted to 100rel and no rseq is presented.') )											
				else:
					self.ve.debug(str(response['__responsecode']) + ' received: nothing to do about prack')		
			else:
				self.ve.debug(str(response['__responsecode']) + ' received: nothing to do about prack')				
	def received1xxExcept100WithSdp(self, response):
		if self.session.getSipState() in ['ringback-tone', "waiting-100-trying"] :
			self.session.context.setRemoteTag( genericFunctions.getTagInTo(response['to']) )
			self.session.context.setCallLineIdentifier( genericFunctions.getCliInFrom(response['from']))
			if response.has_key('from-display'):
				self.session.context.setRemoteDisplay( response['from-display'])
			if response.has_key('p-asserted-identity'):
				self.session.pAssertedIdentity = response['p-asserted-identity']	
			if response.has_key('record-route'):	
				self.session.context.setRouteSet( self.session.context.reverseRecordRoute(response['record-route']) )
			if response.has_key('contact'):
				"""todo""" 
				self.session.context.setRemoteTarget( response['contact'].split('>')[0].split('<')[1] )
			self.session.setSipState('ringback-tone')
			desc = {}
			if self.session.context.remoteDisplay != None:
				desc.update({'display':  self.session.context.remoteDisplay})
			if self.session.context.callLineIdentifier != None:
				desc.update({'cli':  self.session.context.callLineIdentifier})
			if self.session.pAssertedIdentity != None:
				desc.update({'p-asserted-identity':  self.session.pAssertedIdentity})
			self.ve.control.send( templateControlMessages.isRingBackTone(self.session.callId,descriptions = desc))
			# prack 
			if response.has_key('rseq') :
				if self.session.slowStart == False:
					self.session.sendPrack( response['rseq'], response['cseq'] )
				else:
					self.session.sendPrackWithSdp( response['rseq'], response['cseq'] )
			else:
				"""todo""" #cancel
		if self.session.sdp.sdpAnswerReceived == False:
			self.session.codecChoosed, ip, port = self.session.sdp.decodeSdpAndNegociateCodec(response['__body'])
			if self.session.codecChoosed == None:
				# negociation failed => cancel
				self.session.sendCancel()
				self.ve.control.send( templateControlMessages.negociationCodecFailed(self.callId) ) 
			else:
				self.session.rtp.setIpTo(ip)
				self.session.rtp.setPortTo(port)
				self.session.rtp.startListening()
				self.session.startSendingRtp()
		else:
			self.ve.debug('SDP ignored because other sdp is taken account.\nRTP stream is already started.')
				
	def received100Trying(self, response):
		if self.session.getSipState() == 'waiting-100-trying':
			self.session.setSipState('ringback-tone')
		elif self.session.getSipState() == 'waiting-100-trying-to-cancel':
			self.session.sendCancel()
	def analyse2xxResponseCode(self, msg):
		if msg.has_key('content-type') and msg['content-type'] == 'application/sdp':
			self.received2xxWithSdp(msg)
		else:
			self.received2xx(msg)
	def received2xx(self, response):
		# call logs
		self.session.logs.set200OkTimestamp()
		# 
		if self.session.getSipState() in ['ringback-tone', "waiting-100-trying"]:
			self.session.context.setRemoteTag( genericFunctions.getTagInTo(response['to']) )
			if response.has_key('p-asserted-identity'):
				self.session.pAssertedIdentity = response['p-asserted-identity']	
			if response.has_key('record-route'):	
				self.session.context.setRouteSet ( self.session.context.reverseRecordRoute(response['record-route']) ) 
			if response.has_key('contact'):
				"""todo""" 
				self.session.context.setRemoteTarget( response['contact'].split('>')[0].split('<')[1] )
			# update call key in calls
			self.session.id = genericFunctions.getIdMessage(fromHeader = response['from'], toHeader = response['to'], callId = response['call-id'])
			if self.session.sdp.sdpReceived == None:
				self.ve.debug('no sdp provided by callee')
				self.session.sendAckToInvite()
				self.session.sendBye()
			else:
				self.session.sendAckToInvite()
		elif self.session.getSipState() == 'waiting-cancelled':
			self.ve.debug('cancelled ignored by callee')
			self.session.sendAckToInvite()
			self.session.sendBye()
		else:
			self.ve.debug('response ' + str(response['__responsecode']) + ' received to a invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def received2xxWithSdp(self, response):		
		# call logs
		self.session.logs.set200OkTimestamp()
		# 
		if self.session.getSipState() in ['ringback-tone', "waiting-100-trying"]:
			self.session.context.setRemoteTag( genericFunctions.getTagInTo(response['to']) )
			if response.has_key('p-asserted-identity'):
				self.session.pAssertedIdentity = response['p-asserted-identity']	
			if response.has_key('record-route'):	
				self.session.context.setRouteSet ( self.session.context.reverseRecordRoute(response['record-route']) ) 
			if response.has_key('contact'):
				"""todo""" 
				self.session.context.setRemoteTarget( response['contact'].split('>')[0].split('<')[1] )
			# update call key in calls
			self.session.id = genericFunctions.getIdMessage(fromHeader = response['from'], toHeader = response['to'], callId = response['call-id'])
			# negociation codec
			if self.session.sdp.sdpAnswerReceived == False:
				self.session.codecChoosed, ip, port = self.session.sdp.decodeSdpAndNegociateCodec(response['__body'])
				if self.session.codecChoosed == None:
					# Negociation failed => ack + bye
					self.ve.control.send( templateControlMessages.negociationCodecFailed(self.session.callId))
					self.session.sendAckToInvite()
					self.session.sendBye()
				else:
					# Negociation success => ack
					if self.session.timerBetween200andAckValue != None:
						t = Timer(int(self.session.timerBetween200andAckValue))
						t.start()
						alt([[ t.TIMEOUT ]])
						self.timerBetween200andAckValue = None
					self.session.sendAckToInvite()
					self.session.rtp.setIpTo(ip)
					self.session.rtp.setPortTo(port)
					self.session.rtp.startListening()
					self.session.startSendingRtp()
					self.session.sdp.reset()
			else:
				self.ve.debug('SDP ignored because other sdp is taken account.\nRTP stream is already started.')
				self.session.sendAckToInvite()
		elif  self.session.getSipState() == 'waiting-cancelled':
			self.ve.debug('cancelled ignored by callee')
			self.session.sendAckToInvite()
			self.session.sendBye()
	def analyse3xxResponseCode(self, msg):
		if self.session.getSipState() in ['ringback-tone', 'waiting-100-trying', 'waiting-cancelled'] :
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.session.sendAck(msg)
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse4xxResponseCode(self, msg):
		if self.session.getSipState() in ['ringback-tone', 'waiting-100-trying', 'waiting-cancelled'] :
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.session.sendAck(msg)
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse5xxResponseCode(self, msg):
		if self.session.getSipState() in ['ringback-tone', 'waiting-100-trying', 'waiting-cancelled'] :
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.session.sendAck(msg)
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse6xxResponseCode(self, msg):
		if self.session.getSipState() in ['ringback-tone', 'waiting-100-trying', 'waiting-cancelled'] :
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.session.sendAck(msg)
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )	

class ResponseToBye(GenericResponse):
	"""
	"""
	def analyse2xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-bye-response':
			# call logs
			self.session.logs.stop()
			# reset session
			self.ve.control.send( templateControlMessages.isDisconnected(self.session.callId) )
			self.session.reset()
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a bye in sip state ' + str(self.session.getSipState()) + ': not analysed' )
	def analyse3xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-bye-response':
			# call logs
			self.session.logs.stop()
			# reset session
			self.ve.control.send( templateControlMessages.isDisconnected(self.session.callId) )
			self.session.reset()
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a bye in sip state ' + str(self.session.getSipState()) + ': not analysed' )
	def analyse4xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-bye-response':
			# call logs
			self.session.logs.stop()
			# reset session
			self.ve.control.send( templateControlMessages.isDisconnected(self.session.callId) )
			self.session.reset()
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a bye in sip state ' + str(self.session.getSipState()) + ': not analysed' )
	def analyse5xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-bye-response':
			# call logs
			self.session.logs.stop()
			# reset session
			self.ve.control.send( templateControlMessages.isDisconnected(self.session.callId) )
			self.session.reset()
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a bye in sip state ' + str(self.session.getSipState()) + ': not analysed' )
	def analyse6xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-bye-response':
			# call logs
			self.session.logs.stop()
			# reset session
			self.ve.control.send( templateControlMessages.isDisconnected(self.session.callId) )
			self.session.reset()
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a bye in sip state ' + str(self.session.getSipState()) + ': not analysed' )	

class ResponseToCancel(GenericResponse):
	"""
	"""
	def analyse2xxResponseCode(self, msg):	
		if self.session.getSipState() == 'waiting-cancel-response':
				self.ve.debug('cancel request taken care')
				self.session.setSipState('waiting-cancelled')
		else:
				self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a cancel in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse3xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-cancel-response':
				self.ve.debug('cancel request not taken care')
				self.session.setSipState('waiting-cancelled')
		else:
				self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a cancel in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse4xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-cancel-response':
				self.ve.debug('cancel request not taken care')
				self.session.setSipState('waiting-cancelled')
		else:
				self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a cancel in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse5xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-cancel-response':
				self.ve.debug('cancel request not taken care')
				self.session.setSipState('waiting-cancelled')
		else:
				self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a cancel in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse6xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-cancel-response':
				self.ve.debug('cancel request not taken care')
				self.session.setSipState('waiting-cancelled')
		else:
				self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a cancel in sip state ' + str(self.session.getSipState()) + ': not analysed' )	

class ResponseToPrack(GenericResponse):
	"""
	"""
	def analyse2xxResponseCode(self, msg):	
		if self.session.getSipState() == 'waiting-prack-response':
			if msg.has_key('record-route'):	
				self.session.context.setRouteSet ( self.session.context.reverseRecordRoute(msg['record-route']) ) 
			if msg.has_key('contact'):
				"""todo""" 
				self.session.context.setRemoteTarget( msg['contact'].split('>')[0].split('<')[1] )
			self.session.setSipState('ringback-tone')
			self.ve.control.send( templateControlMessages.isReliabilitySuccessful(self.session.callId) )
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a prack in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse4xxResponseCode(self, msg):
		if self.session.getSipState() == 'waiting-prack-response':
			"""todo"""

class ResponseToAck(GenericResponse):
	"""todo"""

class ResponseToRefer(GenericResponse):
	"""
	"""
	def analyse1xxResponseCode(self, msg):
		if self.session.getReferState() in ['waiting-refer-response']:
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.ve.control.send( templateControlMessages.transferFailed((self.session.callId)) )
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a refer in refer state ' + str(self.session.getReferState()) + ': not analysed' )	
	def analyse2xxResponseCode(self, msg):
		if self.session.getReferState() in ['waiting-refer-response' ]:
			self.session.setReferState('transfer-in-progress')
			self.ve.control.send( templateControlMessages.transferAccepted(self.session.callId))
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a refer in refer state ' + str(self.session.getReferState()) + ': not analysed' )	
	def analyse3xxResponseCode(self, msg):
		if self.session.getReferState() in ['waiting-refer-response']:
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.ve.control.send( templateControlMessages.transferFailed((self.session.callId)) )
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a refer in refer state ' + str(self.session.getReferState()) + ': not analysed' )	
	def analyse4xxResponseCode(self, msg):
		if self.session.getReferState() in ['waiting-refer-response' ]:
			if msg['__responsecode'] in ['481', '408']:
				self.session.sendBye()
			else:
				desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
				self.ve.control.send( templateControlMessages.error(descriptions = desc) )
				self.ve.control.send( templateControlMessages.transferFailed(self.session.callId))
				self.session.setReferState('idle')
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a refer in refer state ' + str(self.session.getReferState()) + ': not analysed' )	
	def analyse5xxResponseCode(self, msg):
		if self.session.getReferState() in ['waiting-refer-response']:
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.ve.control.send( templateControlMessages.transferFailed((self.session.callId)) )
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a refer in refer state ' + str(self.session.getReferState()) + ': not analysed' )	
	def analyse6xxResponseCode(self, msg):
		if self.session.getReferState() in ['waiting-refer-response']:
			desc = { 'call-id': str(self.session.callId), 'code': msg['__responsecode'] , 'phrase': msg['__reasonphrase'] }
			self.ve.control.send( templateControlMessages.error(descriptions = desc) )
			self.ve.control.send( templateControlMessages.transferFailed((self.session.callId)) )
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a refer in refer state ' + str(self.session.getReferState()) + ': not analysed' )	
class ResponseToInfo(GenericResponse):
	def analyse2xxResponseCode(self, msg):
		if self.session.getInfoState() == 'waiting-info-response':
			self.ve.control.send( templateControlMessages.dtmfDialed() )
			self.session.setInfoState('idle')
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a info in info state ' + str(self.session.getSipState()) + ': not analysed' )	
class ResponseToReInvite(GenericResponse):
	"""
	"""
	def analyse1xxResponseCode(self, msg):
		"""todo"""
	def analyse2xxResponseCode(self, msg):
		self.session.reInviteSended = False
		if msg.has_key('content-type') and msg['content-type'] == 'application/sdp':
			self.received2xxWithSdp(msg)
		else:
			self.received2xx(msg)
	def received2xx(self, response):
		"""todo"""
		self.ve.debug('not yet implemented')
	def received2xxWithSdp(self, response):	
		# update call key in calls
		if self.session.getSipState() in ['waiting-response-reinvite']:
			# update id call
			self.id = genericFunctions.getIdMessage(fromHeader = response['from'], toHeader = response['to'], callId = response['call-id'])
			self.session.codecChoosed, ip, port = self.session.sdp.decodeSdpAndNegociateCodec(response['__body'])
			if self.session.codecChoosed == None:
				self.ve.control.send( templateControlMessages.negociationCodecFailed(self.session.callId))
				self.session.sendAckToReInvite()
			else:
				self.session.rtp.setIpTo(ip)
				self.session.rtp.setPortTo(port)
			self.session.sendAckToReInvite()
		else:
			self.ve.debug('response ' + str(response['__responsecode']) + ' received to a re-invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
	def analyse4xxResponseCode(self, msg):
		if self.session.getSipState() in ['waiting-response-reinvite']:
			self.session.sendAckToReInvite(error = True)
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a re-invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )		
	def analyse5xxResponseCode(self, msg):
		if self.session.getSipState() in ['waiting-response-reinvite']:
			self.session.sendAckToReInvite(error = True)
		else:
			self.ve.debug('response ' + str(msg['__responsecode']) + ' received to a re-invite in sip state ' + str(self.session.getSipState()) + ': not analysed' )	
class ResponseToUpdate(GenericResponse):
	"""
	"""
	def analyse2xxResponseCode(self, msg):
		self.ve.control.send( templateControlMessages.isUpdated(self.session.callId) )
		if msg.has_key('content-type') and msg['content-type'] == 'application/sdp':
			self.received2xxWithSdp(msg)
		else:
			self.received2xx(msg)
	def received2xx(self, response):
		"""todo"""
		self.ve.debug('not yet implemented')
	def received2xxWithSdp(self, response):	
		# update call key in calls
		if self.session.getSipState() in ['waiting-response-update']:
			if self.session.getCallState() == 'connected':
				self.session.setSipState('connected')
			elif self.session.getCallState() in ['outcoming-call-processing', 'incoming-call-processing']:
				self.session.setSipState('ringback-tone')
			self.session.codecChoosed, ip, port = self.session.sdp.decodeSdpAndNegociateCodec(response['__body'])
			if self.session.codecChoosed == None:
				# Negociation failed 
				self.ve.control.send( templateControlMessages.negociationCodecFailed(self.callId))
				self.session.sendCancel()
			else:
				# Negociation success 
				self.session.rtp.setIpTo(ip)
				self.session.rtp.setPortTo(port)
				self.session.rtp.stopSending()
				if self.session.earlyMedia == True :
					self.session.startSendingRtp()
		else:
			self.ve.debug('response ' + str(response['__responsecode']) + ' received to a update in sip state ' + str(self.session.getSipState()) + ': not analysed' )	

# alias
class VirtualEndPointBehaviour(VirtualEndpoint): pass