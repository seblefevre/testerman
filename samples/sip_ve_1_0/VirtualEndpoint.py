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

##
# Virtual Endpoint function-level API to the SIP Virtual Endpoint.
#
# Wraps the message-level API to some higher level, more convient
# functions to call from your Test Cases.
#
##

# Codec aliasing.
define_codec_alias('sipve', 'sip.basic')

# The SIP endpoint simulator behaviour
import VirtualEndpointBehaviour
# The message-level API
import ControlTemplates


def f_wait(timeout):
	t_wait = Timer(timeout, name = "Waiting")
	t_wait.start()
	t_wait.timeout()

def f_plug(control):
	"""
	Plugs the phone:
	starts listening on SIP port according to initialization parameters.
	"""
	control.send(ControlTemplates.plug())

def f_unplug(control):
	"""
	Unplugs the phone:
	stops listening on SIP port, stops all connections to the SUT.
	"""
	control.send(ControlTemplates.unplug())

def f_dialDtmf(control, signal, duration = 270):
	"""
	Sends a DTMF. Should be replaced by something like "press key".
	"""
	control.send(ControlTemplates.dtmf(signal, duration))

def f_placeCall(control, uri, **kwargs):
	"""
	Places a call to uri. A shortcut to a sequence of pressKey(...).
	Optional arguments are possible depending on the VE implementation in use.

	@type  uri: string
	@param uri: the uri to dial (with scheme, optional parameters, etc)
	@rtype: integer, or None
	@returns: the local call number (since the VE may support multi calls), or None if not able to place the call due to a local error.

	For SIP endpoints, valid keyword arguments are:
	headers = None,
	additionalHeaders = None, 
	timerBetween200OkandAck = None, 
	returnRtpPortChoosed = False, 
	slowStart = False
	@param headers: this argurment allows to overwrite SIP headers (already present), example: {'from': '<sip:d_user_1@fr.netcentrex.net>;tag=1'}
	@type headers: dict
	@param additionalHeaders: this argurment allows to add SIP headers, example: {'header_name': 'value' }
	@type additionalHeaders: dict
	@param timerBetween200OkandAck: timer to delay sending the ack after 200 ok
	@type timerBetween200OkandAck: in
	@param returnRtpPortChoosed: True/False [default = False] the function returns the rtp port choosed on True
	@type returnRtpPortChoosed: boolean
	@param slowStart: sdp offer in invite [ default = False ] 
	@type slowStart: Boolean
	
	@return: ( True/False , call-id choosed by the phone) or ( True/False , call-id choosed by the phone, rtp port choosed)
	@rtype: tuple
	"""
	headers = kwargs.get('headers', None)
	additionalHeaders = kwargs.get('additionalHeaders', None) 
	timerBetween200OkandAck = kwargs.get('timerBetween200OkandAck', None) 
	returnRtpPortChoosed = kwargs.get('returnRtpPortChoosed', False)
	slowStart = kwargs.get('slowStart', False)
	
	control.send(ControlTemplates.call( calledUri = uri, headers = headers, additionalHeaders = additionalHeaders,
		timerBetween200OkandAck = timerBetween200OkandAck, sdp = not slowStart))

	t	= Timer(1.000, "Place call local feedback")
	t.start()
	ret = StateManager(None)
	alt([
		[ control.RECEIVE(ControlTemplates.callId(id = extract(any(), 'id'))),
			lambda: t.stop(),
			lambda: ret.set(value('id')),
		],
		[ t.TIMEOUT,
			lambda: log('Unable to place a new call'),
		]
	])
	return ret.get()

def f_releaseCall(control, callId = 0, headers = None, additionalHeaders = None, timeout  = None, disp = None, cause = None, reason = None):
	"""
	Release a call.
	
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	
	@param headers: this argurment allows to overwrite SIP headers (already present), example: {'from': '<sip:d_user_1@fr.netcentrex.net>;tag=1'}
	@type headers: dict
	
	@param additionalHeaders: this argurment allows to add SIP headers, example: {'header_name': 'value' }
	@type additionalHeaders: dict

	@param timeout: max time to received disconnected event. (in ms)
	@type timeout: int

	@param disp: display in from header 
	@type disp: string
	
	@param cause: deprecated
	@type cause: string
	
	@param reason: reason header sip
	@type reason: string

	@return: return True or False 
	@rtype: None or Boolean
	"""
	control.send(ControlTemplates.hangUp(callId, headers = headers, additionalHeaders = additionalHeaders))
	# -> f_isDisconnected() instead ?
	if timeout != None:
		desc = {}
		if disp != None:
			desc.update({'display':  disp})
		if cause != None:
			reason = cause
		if reason != None:
			desc.update({'reason': reason})
		t = Timer(timeout, "watchdog for disconnected")
		t.start()
		bool = StateManager(False)
		alt([
			[ control.RECEIVE(ControlTemplates.isDisconnected(str(callId), descriptions = desc )),
				lambda: t.stop(),
				lambda: bool.set(True),
			],
			[ t.TIMEOUT,
				lambda: bool.set(False),
			]
		])
		return bool.get()

def f_releaseActiveCalls(control):
	"""
	Release all active calls 
	"""
	control.send(ControlTemplates.releaseActiveCalls())

def f_answerCall(control, callId):
	"""
	Answer a call.
	
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	"""	
	control.send(ControlTemplates.pickUp(callId))

def f_isIdle(control, callId, timeout):
	"""
	Checks if the phone is on idle state.
	
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	@param timeout: max time to received "is idle" event. (in ms)
	@type timeout: int
	
	@rtype: boolean
	@return: the Idle state 
	"""	
	t = Timer(timeout, "watchdog for idle")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE(ControlTemplates.isIdle(str(callId))),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
		]
	])
	return bool.get()

def f_isRegistered(control, timeout): 
	"""
	Check if the phone is registered.
	
	@param timeout: max time to received registered event. (in ms)
	@type timeout: int
	
	@return: return True or False 
	@rtype: boolean
	"""
	t = Timer(timeout, "watchdog for registered")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE(ControlTemplates.registered()),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
		]
	])
	return bool.get()

def f_isUnregistered(control, timeout): 
	"""
	Check if the phone is unregistered.
	
	@param timeout: max time to received not registered event. (in ms)
	@type timeout: int
	
	@return: return True or False 
	@rtype: boolean
	"""
	t = Timer(timeout, "watchdog for unregistered")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE(ControlTemplates.notRegistered() ),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
		]
	])
	return bool.get()

def f_isRinging(control, timeout, returnRtpPort = False, display = None, diversion = None, cli = None, pAssertedIdentity = None, requestUri = None, rtpPort = None):
	"""
	Check if a ringing event has been received in 'timeout' ms.
	
	@param timeout: max time to received the ringing event. (in ms)
	@type timeout: int
	@param returnRtpPort: [default = False]
	@type returnRtpPort: boolean
	@param display: display in from header 
	@type display: string
	@param diversion:
	@type diversion: string
	@param cli: call line identifier
	@type cli: string
	@param pAssertedIdentity:
	@type pAssertedIdentity: string
	@param requestUri:
	@type requestUri: string
	@param rtpPort:
	@type rtpPort: 
	
	@rtype: integer
	@returns: a callId if ringing, None otherwise.
	"""
	desc = {}
	if rtpPort != None:
		desc.update({'rtp-port':  rtpPort})
	if display != None:
		desc.update({'display': display})
	if diversion != None:
		desc.update({'diversion': diversion})
	if cli != None:
		desc.update({'cli': cli })
	if pAssertedIdentity != None:
		desc.update({'p-asserted-identity':  pAssertedIdentity})
	if requestUri != None:
		desc.update( {'request-uri': requestUri})

	t = Timer(timeout, "watchdog for ringing")
	t.start()
	ret = StateManager(None)
	alt([
		[ control.RECEIVE(ControlTemplates.isRinging(any(), descriptions = desc), 'msg'),
			lambda: t.stop(),
			lambda: ret.set(value('msg')['call-id']),
		],
		[ t.TIMEOUT,
		]
	])
	return ret.get()

def f_isReceivingRingbackTone(control, callId, timeout, cli = None, display = None, pAssertedIdentity = None): 
	"""
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	@param timeout: max time to received ringback tone event. (in ms)
	@type timeout: int
	@return: return True or False 
	@rtype: boolean
	
	@param display: display in from header 
	@type display: string
	@param cli: call line identifier
	@type cli: string
	@param pAssertedIdentity:
	@type pAssertedIdentity: string
	
	"""
	desc = {}
	if display != None:
		desc.update({'display': display})
	if cli != None:
		desc.update({'cli': cli })
	if pAssertedIdentity != None:
		desc.update({'p-asserted-identity':  pAssertedIdentity})
		
	t = Timer(timeout, "watchdog for ringback tone")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE(ControlTemplates.isRingBackTone(str(callId), descriptions = desc)),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
		]
	])
	return bool.get()

def f_isReceivingAudio(control, callId, timeout, ssrc = None, payloadType = None, fromIp = None, fromPort = None, reason = None):
	"""
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	@param timeout: max time to received subscribed  event. (in ms)
	@type timeout: int

	@rtype: boolean
	@returns: return True or False 

	@param ssrc: audioId
	@type ssrc: string
	@param payloadType: codec, example: 8
	@type payloadType: string
	@param fromIp: ip address
	@type fromIp: string
	@param fromPort: port
	@type fromPort: string
	@param reason: 
	@type reason: string
	"""	
	desc = {}
	if ssrc != None:
		desc.update({'ssrc': ssrc })
	if payloadType != None:
		desc.update({'payload-type': payloadType })	
	if fromIp != None:
		desc.update({'from-ip': fromIp })	
	if fromPort != None:
		desc.update({'from-port': fromPort })	
	if reason != None:
		desc.update({'reason': reason })	
	template = ControlTemplates.isReceivingRtp(callId = str(callId), description = desc)
	t = Timer(timeout, "watchdog receiving audio")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE(template),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
		]
	])
	return bool.get()

def f_createEndpoint(testcase, control, name, signallingTsiPort, mediaTsiPorts, **kwargs):
	"""
	Creates a new PTC running a SIP virtual endpoint simulator,
	connects its control port to control,
	
	
	@type  signallingTsiPort: tuple (tsiPort, string, integer)
	@param signallingTsiPort: the SIP test system interface port to use, with the IP address to use, the port to use
	@type  mediaTsiPorts: list of tuples (tsiPort, string, integer)
	@param mediaTsiPorts: a list of RTP test system interface ports to use, with their IP addresses and ports
	"""
	ptc = testcase.create(name = name)
	connect(control, ptc['control'])
	sipTsiPort, sipIp, sipPort = signallingTsiPort
	port_map(ptc['sip'], sipTsiPort)
	rtpIpPorts = []
	for i in range(len(mediaTsiPorts)):
		rtpTsiPort, rtpIp, rtpPort = mediaTsiPorts[i]
		port_map(ptc['rtp%s' % i], rtpTsiPort)
		rtpIpPorts.append((rtpIp, rtpPort))

	ptc.start(VirtualEndpointBehaviour.VirtualEndpoint(), name = name, sipSourceIp = sipIp, sipSourcePort = sipPort, rtpProbes = rtpIpPorts, **kwargs)
	return ptc


def f_isCallConnected(control, callId, timeout):
	"""
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	
	@param timeout: max time to received connected event. (in ms)
	@type timeout: int
	
	@return: return True or False 
	@rtype: boolean
	"""	
	t = Timer(timeout, "watchdog for connected")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE(ControlTemplates.isConnected(str(callId))),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
			lambda: bool.set(False),
		]
	])
	return bool.get()

def f_isCallCancelled(control, callId, timeout, cause = None, reason = None):
	"""
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	
	@param timeout: max time to received cancel event. (in ms)
	@type timeout: int
	
	@param cause: deprecated
	@type cause: string
	
	@param reason: reason header sip
	@type reason: string
	
	@return: return True or False 
	@rtype: boolean
	"""
	if cause != None:
		reason = cause
	if reason != None:
		template = ControlTemplates.cancelReceived(str(callId), reason = reason)
	else:
		template = ControlTemplates.cancelReceived(str(callId))
	t = Timer(timeout, "watchdog for cancelled")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE( template ),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
			lambda: bool.set(False),
		]
	])
	return bool.get()

def f_isCallDisconnected(control, callId, timeout, disp = None, cause = None, reason = None):
	"""
	@param callId: instance of the call (return by functions "placeCall" or "isRinging")
	@type callId: int
	
	@param timeout: max time to received disconnected event. (in ms)
	@type timeout: int
	
	@param disp: display in from header 
	@type disp: string

	@param cause: deprecated
	@type cause: string
	
	@param reason: reason header sip
	@type reason: string
	
	@return: return True or False 
	@rtype: boolean
	"""
	desc = {}
	if disp != None:
		desc.update({'display':  disp})
	if cause != None:
		reason = cause
	if reason != None:
		desc.update({'reason': reason})
	t = Timer(timeout, "watchdog for disconnected")
	t.start()
	bool = StateManager(False)
	alt([
		[ control.RECEIVE(ControlTemplates.isDisconnected(str(callId), descriptions = desc)),
			lambda: t.stop(),
			lambda: bool.set(True),
		],
		[ t.TIMEOUT,
			lambda: bool.set(False),
		]
	])
	return bool.get()

def f_playWavFile(control, callId, resource, loopCount = 1):
	control.send(ControlTemplates.m_playWavFile(callId, resource, loopCount))


# TODO
#
#	def register(self, timeout  = None, expires = None):
#		"""
#		Register with proxy (refresh registration is automaticaly activated)
#
#		@param timeout: max time to received registered event. (in ms)
#		@type timeout: int
#		
#		@param expires: "expires" value (header sip) default 3600
#		@type expires: int
#		
#		@return: True or False
#		@rtype: boolean
#		"""
#		self.control.send( ControlTemplates.register(expires) )
#		if timeout != None:
#			t = Timer(timeout, "watchdog for registered")
#			t.start()
#			bool = StateManager(False)
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.registered() ),
#					lambda: t.stop(),
#					lambda: bool.set(True),
#				],
#				[ t.TIMEOUT,
#					lambda: bool.set(False),
#				]
#			])
#			return bool.get()
#			
#	def unregister(self, timeout = None):
#		"""
#		Unregister the phone
#		
#		@param timeout: max time to received not registered event. (in ms)
#		@type timeout: int
#
#		@return: True or False
#		@rtype: boolean
#		"""
#		self.control.send( ControlTemplates.unregister() )
#		if timeout != None:
#			t = Timer(timeout, "watchdog for unregistered")
#			t.start()
#			bool = StateManager(False)
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.notRegistered() ),
#					lambda: t.stop(),
#					lambda: bool.set(True),
#				],
#				[ t.TIMEOUT,
#					lambda: bool.set(False),
#				]
#			])
#			return bool.get()
#	def dialDtmf(self, signal, duration = None):
#		"""
#		Send DTMF as INFO method
#		
#		@param signal: 
#		@type signal: 
#		
#		@param duration: (default 270ms)
#		@type duration: string
#		
#		@rtype: None
#		"""
#		if duration == None:
#			duration = '270'
#		self.control.send( ControlTemplates.dtmf(signal, duration ) )
#	def subscribe(self, service, timeout = None, expires = None, uri = None):
#		"""
#		@param timeout: max time to received subscribed event. (in ms)
#		@type timeout: int
#		
#		@param expires: "expires" value (header sip)
#		@type expires: int
#		
#		@param service: available (mwiservice)
#		@type service: string
#		
#		@param uri: contact to subscribe service
#		@type uri: string
#		
#		@return: True or False
#		@rtype: boolean
#		"""
#		self.control.send( ControlTemplates.subscribe(service, expires, uri) )	
#		if timeout != None:
#			t = Timer(timeout, "watchdog for subscribe")
#			t.start()
#			bool = StateManager(False)
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.subscribed(service) ) ,
#					lambda: t.stop(),
#					lambda: bool.set(True),
#				],
#				[ t.TIMEOUT,
#					lambda: bool.set(False),
#				]
#			])
#			return bool.get()
#	def unsubscribe(self, service, timeout, reason = None):
#		"""
#		@param timeout: max time to received unsubscribed event. (in ms)
#		@type timeout: int
#
#		@param service: available (mwiservice)
#		@type service: string
#		
#		@param reason: 
#		@type reason: string
#		
#		@return: True or False
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#				
#		self.control.send( ControlTemplates.unsubscribe(service) )
#		desc = {}
#		desc.update({'event-name': service})
#		desc.update({'subscription-state': 'terminated'})
#		if reason != None:
#			desc.update({'reason': reason})
#			
#		events = [ False, False ]
#		#	state machine
#		t = Timer(timeout, "watchdog for unsubscribe and notify")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.subscribed(service) ),
#				lambda: updateEvents(0),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.subscribed(service) ),
#				lambda: updateEvents(0),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.notify(descriptions = desc) ),
#				lambda: updateEvents(1),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.notify(descriptions = desc) ),
#				lambda: updateEvents(1),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)	
#		return rslt.get()
#			
#			
#	def divertCall(self, callId, divertUri):
#		"""
#		Diverts the call (callid) to (contactTo)
#		
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param divertUri: uri to contact
#		@type divertUri: string or virtual endpoint object
#		"""
#		if isinstance(divertUri, VirtualEndPoint ):
#			uriTo = divertUri.puid + '@' + divertUri.domain
#		else:
#			uriTo = divertUri
#		desc = {}
#		desc.update({'code': '302', 'phrase': 'Moved Temporarily', 'contact-to': uriTo })
#		self.control.send( ControlTemplates.divert(callId, descriptions = desc))
#	def rejectCall(self, callId, responseCode = None, reasonPhrase = None):
#		"""
#		Reject a call with 603 decline.
#		
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		param responseCode: default = '603'
#		@type responseCode: string
#		
#		param reasonPhrase: default = 'Decline'
#		@type reasonPhrase: string
#		
#		@rtype: None
#		"""	
#		desc = {}
#		if responseCode != None:
#			desc.update({'code': str(responseCode)})
#		if reasonPhrase != None:
#			desc.update({'phrase': str(reasonPhrase)})	
#		self.control.send( ControlTemplates.reject(callId, descriptions = desc))
#	def transferCallAllInOne(self, refer, to, type, timeout):
#		"""
#		Placing the active call on hold and transfer after
#		
#		@param refer: call to transfer
#		@type refer: int
#		
#		@param to: target
#		@type to: int or string (uri)
#		
#		@param type: 'blind' or 'attendant'
#		@type type: string 
#		@param timeout: max time to received "is on hold" event. (in ms)
#		@type timeout: int
#		"""
#		self.placingCallOnHold()
#		if self.isCallOnHoldAndReceivedAudioInterruption(callId = refer, timeout = timeout):
#			self.transferCall( refer = refer, to = to, type = type)
#	def transferCall(self, refer, to , type): 
#		"""
#		Transfer 
#		
#		@param refer: call to transfer
#		@type refer: int
#		
#		@param to: target
#		@type to: int or string (uri)
#		
#		@param type: 'blind' or 'attendant'
#		@type type: string 
#		
#		@rtype: None
#		"""
#		self.control.send( ControlTemplates.transfer( refer, to, type) )
#	def placingCallOnHold(self, timeout = None) : 
#		"""
#		Placing the active call on hold.
#		
#		@param timeout: max time to received "is on hold" event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False only if timeout is present
#		@rtype: boolean or None
#		"""
#		self.control.send( ControlTemplates.onHold() )
#		if timeout != None:
#			t = Timer(timeout, "watchdog for placing on hold")
#			t.start()
#			bool = StateManager(False)
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.isOnHold(any()) ),
#					lambda: t.stop(),
#					lambda: bool.set(True),
#				],
#				[ t.TIMEOUT,
#					lambda: bool.set(False),
#				]
#			])
#			return bool.get()
#	def retrieveCall (self, callId): 
#		"""
#		Retrieve a call
#		
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@rtype: None
#		"""
#		self.control.send( ControlTemplates.retrieveCall(callId))
#	
#	def createAndJoinConferenceAllInOne (self, callIds, timeout, uri = None, headers = None, additionalHeaders = None):
#		"""
#		
#		"""
#		idConf = self.createConference(uri = uri, headers = headers, additionalHeaders = additionalHeaders)
#		if self.isCallConnected(callId = idConf, timeout = timeout):
#			for id in callIds:
#				self.joinConference(callId = id, confId = idConf)
#			
#	def createConference(self, uri = None, headers = None, additionalHeaders = None, returnRtpPortChoosed = False):
#		"""
#		Place a call at the conference brigde
#		
#		@param uri: uri to contact (default = Conf-Factory)
#		@type uri: string or virtual endpoint object
#		
#		@param headers: this argurment allows to overwrite SIP headers (already present), example: {'from': '<sip:d_user_1@fr.netcentrex.net>;tag=1'}
#		@type headers: dict
#		
#		@param additionalHeaders: this argurment allows to add SIP headers, example: {'header_name': 'value' }
#		@type additionalHeaders: dict
#		
#		@param returnRtpPortChoosed: True/False [default = False] the function returns the rtp port choosed on True
#		@type returnRtpPortChoosed: boolean
#		
#		@return: ( True/False , call-id choosed by the phone) or ( True/False , call-id choosed by the phone, rtp port choosed)
#		@rtype: tuple
#		"""
#		def setValue(self, val):
#			self.call = val['call-id']
#			self.rtpPortChoosed = val['rtp-port']
#		
#		if uri != None:
#			uriTo = uri
#		else:
#			uriTo = 'Conf-Factory'
#		self.control.send( ControlTemplates.call( calledUri = uriTo, headers = headers, additionalHeaders = additionalHeaders , timerBetween200OkandAck = None, sdp = True) )
#		
#		self.call = None
#		self.rtpPortChoosed = None
#		t	= Timer(1000, "watchdog to return call id")
#		t.start()
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.callId(id = any(), portRtpChoosed = any()), 'id' ),
#				lambda: t.stop(),
#				lambda: setValue(self, value('id')),
#			],
#			[ t.TIMEOUT,
#				lambda: log('Error to return a call id, ptc stopped'),
#				lambda: self.ptc.stop()
#			]
#		])
#		if self.call == None:
#			return self.call
#		else:
#			if returnRtpPortChoosed == True:
#				return int(self.call), int(self.rtpPortChoosed)
#			else:
#				return int(self.call)
#	def joinConference(self, callId, confId):
#		"""
#		Join user (callId) at the conference (confId)
#		
#		@param callId: instance of the call (return by functions "placeCall")
#		@type callId: int
#		
#		@param confId: instance of the conference call (return by function "createConference")
#		@type confId: int
#		"""
#		self.control.send( ControlTemplates.joinConference( refer = callId, to = confId, type = 'attendant') )
#	def updateSession(self, callId, timeout, sdpOffer = True):
#		"""
#		experimental
#		"""
#		desc = {}
#		desc.update( {'sdp':sdpOffer} )
#		template = ControlTemplates.updateToSend(callId, descriptions = desc)
#		self.control.send( template )
#		t = Timer(timeout, "watchdog to update session")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.isUpdated(any()) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#
#	def isRegistered(self, timeout): 
#		"""
#		Check if the phone is registered.
#		
#		@param timeout: max time to received registered event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		t = Timer(timeout, "watchdog for registered")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.registered() ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	
#	def isUnregistered(self, timeout): 
#		"""
#		Check if the phone is unregistered.
#		
#		@param timeout: max time to received not registered event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		t = Timer(timeout, "watchdog for unregistered")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.notRegistered() ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	
#
#	def isCallConnectedAndReceivingAudio(self, callId, timeout, ssrc = None, payloadType = None, fromIp = None, fromPort = None, reason = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received connected and receiving audio events. (in ms)
#		@type timeout: int
#		
#		@param ssrc: audioId
#		@type ssrc: string
#		
#		@param payloadType: codec, example: 8
#		@type payloadType: string
#		
#		@param fromIp: ip address
#		@type fromIp: string
#		
#		@param fromPort: port
#		@type fromPort: string
#		
#		@param reason: 
#		@type reason: string
#		
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#				
#		events = [ False, False ]
#		
#		desc = {}
#		if ssrc != None:
#			desc.update({'ssrc': ssrc })
#		if payloadType != None:
#			desc.update({'payload-type': payloadType })	
#		if fromIp != None:
#			desc.update({'from-ip': fromIp })	
#		if fromPort != None:
#			desc.update({'from-port': fromPort })	
#		if reason != None:
#			desc.update({'reason': reason })	
#		#	state machine
#		t = Timer(timeout, "watchdog, connected and receiving audio")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.isConnected(str(callId))  ),
#				lambda: updateEvents(0),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isConnected(str(callId)) ),
#				lambda: updateEvents(0),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE(  ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#				lambda: updateEvents(1),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#				lambda: updateEvents(1),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)			
#		return rslt.get()
#
#	def isConferenceCreated (self, callId, timeout):
#		"""
#		@param callId: 
#		@type callId: int
#		
#		@param timeout: max time to received connected event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		t = Timer(timeout, "watchdog for connected")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.isConnected(str(callId)) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isCallConnected (self, callId, timeout):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received connected event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		t = Timer(timeout, "watchdog for connected")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.isConnected(str(callId)) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isCallCancelled (self, callId, timeout, cause = None, reason = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received cancel event. (in ms)
#		@type timeout: int
#		
#		@param cause: deprecated
#		@type cause: string
#		
#		@param reason: reason header sip
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		if cause != None:
#			reason = cause
#		if reason != None:
#			template = ControlTemplates.cancelReceived(str(callId), reason = reason)
#		else:
#			template = ControlTemplates.cancelReceived(str(callId))
#		t = Timer(timeout, "watchdog for cancelled")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( template ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#
#	def isCallDisconnected (self, callId, timeout, disp = None, cause = None, reason = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received disconnected event. (in ms)
#		@type timeout: int
#		
#		@param disp: display in from header 
#		@type disp: string
#
#		@param cause: deprecated
#		@type cause: string
#		
#		@param reason: reason header sip
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		desc = {}
#		if disp != None:
#			desc.update({'display':  disp})
#		if cause != None:
#			reason = cause
#		if reason != None:
#			desc.update({'reason': reason})
#		t = Timer(timeout, "watchdog for disconnected")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.isDisconnected(str(callId), descriptions = desc ) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isCallOnHold (self, callId, timeout):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received "is on hold" event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		t = Timer(timeout, "watchdog for placing on hold")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.isOnHold(str(callId)) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isCallUpdated(self, callId, timeout):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received "call updated" event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		t = Timer(timeout, "watchdog to receive session updated event")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.isCallUpdated(str(callId)) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isCallUpdatedAndHasReceivedAudioInterruptionAndIsReceivingAudio(self, callId, timeout, ssrc = None, payloadType = None, fromIp = None, fromPort = None, reason = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received "is on hold" , "audio interruption" and "is receiving audio" events. (in ms)
#		@type timeout: int
#		
#		@param ssrc: audioId
#		@type ssrc: string
#		
#		@param payloadType: codec, example: 8
#		@type payloadType: string
#		
#		@param fromIp: ip address
#		@type fromIp: string
#		
#		@param fromPort: port
#		@type fromPort: string
#		
#		@param reason: 
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i, nameEvent = None):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#				if nameEvent != None:
#					eventsOrder.append(nameEvent)
#			else:
#				events.append(False)
#					
#		events = [ False, False, False]
#		eventsOrder = []
#		
#		desc = {}
#		if ssrc != None:
#			desc.update({'ssrc': ssrc })
#		if payloadType != None:
#			desc.update({'payload-type': payloadType })	
#		if fromIp != None:
#			desc.update({'from-ip': fromIp })	
#		if fromPort != None:
#			desc.update({'from-port': fromPort })	
#		if reason != None:
#			desc.update({'reason': reason })	
#		template = ControlTemplates.isReceivingRtp(callId = str(callId), description = desc)
#		
#		
#		#	state machine
#		t = Timer(timeout, "watchdog for session updated, audio interruption and new stream audio")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = {}) ),
#				lambda: updateEvents(0, 'audio-interruption'),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = {}) ),
#				lambda: updateEvents(0, 'audio-interruption'),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#				lambda: updateEvents(1, 'receiving-audio'),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#				lambda: updateEvents(1, 'receiving-audio'),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				 self.control.RECEIVE( ControlTemplates.isCallUpdated(str(callId)) ),
#				lambda: updateEvents(2),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isCallUpdated(str(callId)) ),
#				lambda: updateEvents(2),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)			
#		
#		if len(eventsOrder) != 2: 
#			return False
#		else:
#			if eventsOrder.index('audio-interruption') == 0 and eventsOrder.index('receiving-audio') == 1:
#				return rslt.get()
#			else:
#				return False
#	def isCallUpdatedAndHasReceivedAudioInterruption(self, callId, timeout, reason = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param reason: 
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i, nameEvent = None):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#					
#		events = [ False, False]
#		
#		desc = {}
#		if reason != None:
#			desc.update({'reason': reason })	
#		template = ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = desc)
#		
#		#	state machine
#		t = Timer(timeout, "watchdog for session updated, audio interruption")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( template ),
#				lambda: updateEvents(0),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( template ),
#				lambda: updateEvents(0),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				 self.control.RECEIVE( ControlTemplates.isCallUpdated(str(callId)) ),
#				lambda: updateEvents(1),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isCallUpdated(str(callId)) ),
#				lambda: updateEvents(1),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)			
#		return rslt.get()
#		
#	def isCallUpdatedAndReceivingAudio(self, callId, timeout, ssrc = None, payloadType = None, fromIp = None, fromPort = None, reason = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received updated and receiving audio events. (in ms)
#		@type timeout: int
#		
#		@param ssrc: audioId
#		@type ssrc: string
#		
#		@param payloadType: codec, example: 8
#		@type payloadType: string
#		
#		@param fromIp: ip address
#		@type fromIp: string
#		
#		@param fromPort: port
#		@type fromPort: string
#		
#		@param reason: 
#		@type reason: string
#		
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#		events = [ False, False ]
#		
#		desc = {}
#		if ssrc != None:
#			desc.update({'ssrc': ssrc })
#		if payloadType != None:
#			desc.update({'payload-type': payloadType })	
#		if fromIp != None:
#			desc.update({'from-ip': fromIp })	
#		if fromPort != None:
#			desc.update({'from-port': fromPort })	
#		if reason != None:
#			desc.update({'reason': reason })	
#		#	state machine
#		t = Timer(timeout, "watchdog, updated and receiving audio")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.isCallUpdated(str(callId))  ),
#				lambda: updateEvents(0),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isCallUpdated(str(callId)) ),
#				lambda: updateEvents(0),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE(  ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#				lambda: updateEvents(1),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#				lambda: updateEvents(1),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)			
#		return rslt.get()
#	def isCallTransferred(self, callId, timeout): 
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received transfer successful event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		t = Timer(timeout, "watchdog for transfer")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.transferSuccessful(str(callId)) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isCallTransferAccepted(self, callId, timeout): 
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received transfer accepted event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		t = Timer(timeout, "watchdog for transfer")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.transferAccepted(str(callId)) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isSubscribed(self, timeout, service = None):
#		"""
#		@param service: (mwiservice)
#		@type service: string
#		
#		@param timeout: max time to received subscribed  event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		if service == None:
#			template = ControlTemplates.subscribed(any())
#		else:
#			template = ControlTemplates.subscribed(service)
#		t = Timer(timeout, "watchdog for suscribe")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( template ) ,
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isUnsubscribed(self, timeout, service = None):
#		"""
#		@param service: (mwiservice)
#		@type service: string
#		
#		@param timeout: max time to received unsubscribed successful event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		if service == None:
#			template = ControlTemplates.unsubscribeSuccessful(any())
#		else:
#			template = ControlTemplates.unsubscribeSuccessful(service)
#		t = Timer(timeout, "watchdog for unsuscribe")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( template ) ,
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def isReceivingAudio(self, callId, timeout, ssrc = None, payloadType = None, fromIp = None, fromPort = None, reason = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received subscribed  event. (in ms)
#		@type timeout: int
#		
#		@param ssrc: audioId
#		@type ssrc: string
#		
#		@param payloadType: codec, example: 8
#		@type payloadType: string
#		
#		@param fromIp: ip address
#		@type fromIp: string
#		
#		@param fromPort: port
#		@type fromPort: string
#		
#		@param reason: 
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		desc = {}
#		if ssrc != None:
#			desc.update({'ssrc': ssrc })
#		if payloadType != None:
#			desc.update({'payload-type': payloadType })	
#		if fromIp != None:
#			desc.update({'from-ip': fromIp })	
#		if fromPort != None:
#			desc.update({'from-port': fromPort })	
#		if reason != None:
#			desc.update({'reason': reason })	
#		template = ControlTemplates.isReceivingRtp(callId = str(callId), description = desc)
#		t = Timer(timeout, "watchdog receiving audio")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( template ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#
#	def hasReceivedNotify(self, timeout, callId = None, nameEvent = None, state = None, body = None, reason = None):
#		"""
#		@param timeout: max time to received notify event. (in ms)
#		@type timeout: int
#		
#		@param state: active/terminated
#		@type state: string
#		
#		@param body: 
#		@type body: string
#		
#		@param nameEvent: 
#		@type nameEvent: string
#		
#		@param reason: 
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		
#		desc = {}
#		if callId != None:
#			desc.update({'call-id': str(callId)})
#		if state != None:
#			desc.update({'subscription-state':  state})
#		if nameEvent != None:
#			desc.update({'event-name':  nameEvent})
#		if body != None:
#			desc.update({'body':  body})	
#		if reason != None:
#			desc.update({'reason':  reason})	
#		t = Timer(timeout, "watchdog to receive notify")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.notify(descriptions = desc) , 'notify' ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#
#	def hasReceivedUpdate(self, callId, timeout, display = None, pAssertedIdentity =  None, cli = None):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received update event. (in ms)
#		@type timeout: int
#		
#		@param display:
#		@type display: string
#		
#		@param cli:
#		@type cli: string
#		
#		@param pAssertedIdentity:
#		@type pAssertedIdentity: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		desc = {}
#		if cli != None:
#			desc.update({'cli': cli })
#		if display != None:
#			desc.update({'display':  display})
#		if pAssertedIdentity != None:
#			desc.update({'p-asserted-identity': pAssertedIdentity})
#			
#		t = Timer(timeout, "watchdog for receive update")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.eventUpdate(str(callId), descriptions = desc) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	def hasReceivedPrack(self, callId, timeout):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received prack event. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		t = Timer(timeout, "watchdog for receive prack")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.prackReceived( str(callId)) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#		
#	def hasReceivedAudioInterruption (self, callId, timeout, reason = None): 
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received stream stopped event. (in ms)
#		@type timeout: int
#		
#		@param reason: 
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""	
#		desc = {}
#		if reason != None:
#			desc.update({'reason': reason })	
#		template = ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = desc)
#		t = Timer(timeout, "audio interruption")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( template ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	
#
#
#	def hasReceivedErrorMessage(self, timeout, callId = None, responseCode = None, reasonPhrase = None):
#		"""
#		@param timeout: max time to received error event. (in ms)
#		@type timeout: int
#		
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param responseCode: 
#		@type responseCode: string or function
#		
#		@param reasonPhrase: 
#		@type reasonPhrase: string or function
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		desc = {}
#		if callId != None:
#			desc.update({'call-id': str(callId)})
#		if responseCode != None:
#			desc.update({'code':  responseCode})
#		if reasonPhrase != None:
#			desc.update({'phrase': reasonPhrase})
#		t = Timer(timeout, "wathdog to receive error")
#		t.start()
#		bool = StateManager(False)
#		alt([
#			[ self.control.RECEIVE( ControlTemplates.error(descriptions = desc) ),
#				lambda: t.stop(),
#				lambda: bool.set(True),
#			],
#			[ t.TIMEOUT,
#				lambda: bool.set(False),
#			]
#		])
#		return bool.get()
#	
#	def isCallOnHoldAndReceivedAudioInterruption(self, callId, timeout, noOrder = True, reason = None): 
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received "is on hold" event and after stream stopped event. (in ms)
#		@type timeout: int
#		
#		@param reason: 
#		@type reason: string
#		
#		@param noOrder: checking events in arrival order [default = True]
#		@type noOrder: boolean
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#				
#		desc = {}
#		if reason != None:
#			desc.update({'reason': reason })
#		
#		if 	noOrder == False:
#			t1 = Timer(timeout, "watchdog for placing on hold")
#			t2 = Timer(timeout, "audio checking timeout")
#			t1.start()
#			bool = StateManager(False)
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.isOnHold(str(callId)) ),
#					lambda: t1.stop(),
#					lambda: t2.start(),
#				],
#				[ t1.TIMEOUT,
#					lambda: bool.set(False),
#				]
#			])
#	
#			
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = desc) ),
#					lambda: t2.stop(),
#					lambda: bool.set(True),
#				],
#				[ t2.TIMEOUT,
#					lambda: bool.set(False),
#				]
#			])
#			return bool.get()
#		else:
#			events = [ False, False ]
#			#	state machine
#			t = Timer(timeout, "watchdog for placing on hold and audio interruption")
#			bool = StateManager(False)
#			rslt = StateManager(False)
#			altArgs = []
#			altArgs.append(
#				[ #
#					lambda: bool.get() == False,
#					self.control.RECEIVE( ControlTemplates.isOnHold(str(callId)) ),
#					lambda: updateEvents(0),
#					REPEAT,
#				]
#			)	
#			altArgs.append(
#				[ # 
#					lambda : bool.get() == True,
#					self.control.RECEIVE( ControlTemplates.isOnHold(str(callId)) ),
#					lambda: updateEvents(0),
#					lambda: t.stop(),
#					lambda: rslt.set(True)
#				]
#			)	
#			altArgs.append(
#				[ #
#					lambda: bool.get() == False,
#					self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = desc) ),
#					lambda: updateEvents(1),
#					REPEAT,
#				]
#			)	
#			altArgs.append(
#				[ # 
#					lambda : bool.get() == True,
#					self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = desc) ),
#					lambda: updateEvents(1),
#					lambda: t.stop(),
#					lambda: rslt.set(True)
#				]
#			)	
#			altArgs.append(
#				[ t.TIMEOUT,
#					lambda: rslt.set(False)
#				]
#			)	
#			t.start()
#			alt(altArgs)			
#			return rslt.get()
#	def hasReceivedAudioInterruptionAndReceivingNewAudio(self, callId, timeout, noOrder = True, ssrc = None, payloadType = None, fromIp = None, fromPort = None, reason = None ):
#		"""
#		@param callId: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callId: int
#		
#		@param timeout: max time to received "audio interruption" and "is receiving audio" events. (in ms)
#		@type timeout: int
#		
#		@param noOrder: checking events in arrival order [default = True]
#		@type noOrder: boolean
#		
#		@param ssrc: audioId
#		@type ssrc: string
#		
#		@param payloadType: codec, example: 8
#		@type payloadType: string
#		
#		@param fromIp: ip address
#		@type fromIp: string
#		
#		@param fromPort: port
#		@type fromPort: string
#		
#		@param reason: 
#		@type reason: string
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#				
#		desc = {}
#		if ssrc != None:
#			desc.update({'ssrc': ssrc })
#		if payloadType != None:
#			desc.update({'payload-type': payloadType })	
#		if fromIp != None:
#			desc.update({'from-ip': fromIp })	
#		if fromPort != None:
#			desc.update({'from-port': fromPort })	
#		if reason != None:
#			desc.update({'reason': reason })	
#
#		if 	noOrder == False:
#			t1 = Timer(timeout, "audio interruption checking timeout")
#			t2 = Timer(timeout, "new stream timeout")
#			t1.start()
#			rslt = StateManager(False)
#			bool = StateManager(False)
#	
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = {}) ),
#					lambda: t1.stop(),
#					lambda: t2.start(),
#				],
#				[ t1.TIMEOUT,
#					lambda: rslt.set(False),
#				]
#			])
#			alt([
#				[ self.control.RECEIVE( ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#					lambda: t2.stop(),
#					lambda: rslt.set(True),
#				],
#				[ t2.TIMEOUT,
#					lambda: rslt.set(False),
#				]
#			])
#			return rslt.get()
#		else:
#			events = [ False, False ]
#			#	state machine
#			t = Timer(timeout, "watchdog audio interruption and new stream")
#			bool = StateManager(False)
#			rslt = StateManager(False)
#			altArgs = []
#			altArgs.append(
#				[ #
#					lambda: bool.get() == False,
#					self.control.RECEIVE( ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#					lambda: updateEvents(0),
#					REPEAT,
#				]
#			)	
#			altArgs.append(
#				[ # 
#					lambda : bool.get() == True,
#					self.control.RECEIVE( ControlTemplates.isReceivingRtp(callId = str(callId), description = desc) ),
#					lambda: updateEvents(0),
#					lambda: t.stop(),
#					lambda: rslt.set(True)
#				]
#			)	
#			altArgs.append(
#				[ #
#					lambda: bool.get() == False,
#					self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = {}) ),
#					lambda: updateEvents(1),
#					REPEAT,
#				]
#			)	
#			altArgs.append(
#				[ # 
#					lambda : bool.get() == True,
#					self.control.RECEIVE( ControlTemplates.stoppedReceivingRtp(callId = str(callId), description = {}) ),
#					lambda: updateEvents(1),
#					lambda: t.stop(),
#					lambda: rslt.set(True)
#				]
#			)	
#			altArgs.append(
#				[ t.TIMEOUT,
#					lambda: rslt.set(False)
#				]
#			)	
#			t.start()
#			alt(altArgs)			
#			return rslt.get()
#	def isCallTransferredAndCancelled(self, callIdRefer, callIdCancelled, timeout):
#		"""
#		
#		@param callIdRefer: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callIdRefer: int
#		
#		@param callIdCancelled: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callIdCancelled: int
#		
#		@param timeout: max time to received "transfer successful" and "487 INVITE" events. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#		events = [ False, False ]
#		#	state machine
#		t = Timer(timeout, "watchdog, transfert successful and cancelled")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.transferSuccessful(str(callIdRefer))),
#				lambda: updateEvents(0),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.transferSuccessful(str(callIdRefer)) ),
#				lambda: updateEvents(0),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE(  ControlTemplates.error(descriptions =  {'call-id': str(callIdCancelled), 'code': '487'}  ) ),
#				lambda: updateEvents(1),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.error(descriptions = {'call-id': str(callIdCancelled), 'code': '487'} ) ),
#				lambda: updateEvents(1),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)			
#		return rslt.get()
#	def isCallTransferredAndDisconnected(self, callIdRefer, callIdDisconnected, timeout):
#		"""
#		
#		@param callIdRefer: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callIdRefer: int
#		
#		@param callIdDisconnected: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callIdDisconnected: int
#		
#		@param timeout: max time to received "transfer successful" and "is call disconnected" events. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#		events = [ False, False ]
#		#	state machine
#		t = Timer(timeout, "watchdog, transfert successful and disconnected")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.transferSuccessful(str(callIdRefer))),
#				lambda: updateEvents(0),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.transferSuccessful(str(callIdRefer)) ),
#				lambda: updateEvents(0),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE(  ControlTemplates.isDisconnected(str(callIdDisconnected), descriptions =  {}  ) ),
#				lambda: updateEvents(1),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isDisconnected(str(callIdDisconnected), descriptions = {} ) ),
#				lambda: updateEvents(1),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)			
#		return rslt.get()
#	def isUserJoinedToConferenceAndDisconnected(self, callId, timeout):
#		"""	
#		@param callIdRefer: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callIdRefer: int
#		
#		@param callIdDisconnected: instance of the call (return by functions "placeCall" or "isRinging")
#		@type callIdDisconnected: int
#		
#		@param timeout: max time to received "user joined successful" and "is call disconnected" events. (in ms)
#		@type timeout: int
#		
#		@return: return True or False 
#		@rtype: boolean
#		"""
#		def updateEvents(i):
#			if events[i] == False:	
#				events[i] = True
#				if events.count(False) == 1:
#					bool.set(True)
#			else:
#				events.append(False)
#		events = [ False, False ]
#		#	state machine
#		t = Timer(timeout, "watchdog, user joined successful and disconnected")
#		bool = StateManager(False)
#		rslt = StateManager(False)
#		altArgs = []
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE( ControlTemplates.transferSuccessful(str(callId))),
#				lambda: updateEvents(0),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.transferSuccessful(str(callId)) ),
#				lambda: updateEvents(0),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ #
#				lambda: bool.get() == False,
#				self.control.RECEIVE(  ControlTemplates.isDisconnected(str(callId), descriptions =  {}  ) ),
#				lambda: updateEvents(1),
#				REPEAT,
#			]
#		)	
#		altArgs.append(
#			[ # 
#				lambda : bool.get() == True,
#				self.control.RECEIVE( ControlTemplates.isDisconnected(str(callId), descriptions = {} ) ),
#				lambda: updateEvents(1),
#				lambda: t.stop(),
#				lambda: rslt.set(True)
#			]
#		)	
#		altArgs.append(
#			[ t.TIMEOUT,
#				lambda: rslt.set(False)
#			]
#		)	
#		t.start()
#		alt(altArgs)			
#		return rslt.get()
