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
# (c) Denis Machard, Benjamin Butel, and other contributors.
##

"""
Sip Message Templates according to RFCs 3261, 3262, 3265, 3311, 3515, 2676

@date: 2008/09/24
"""
# init or reset functions linked to probe sip
def initialize(srcIp, srcPort, t1):
	"""
	build the template message to send in order to initialize SIP probe.
	
	@param srcIp: bind IP address of probe SIP
	@type srcIp: string 
	@param srcPort: bind port of probe SIP
	@type srcPort: string
	@param t1: t1 in ms when waiting for response before re-emit request 
	@type t1: int
	
	@return: initialize template to send
	@rtype: dict
	"""
	return None # UDP commands ?
	return {'__type': 'init',
					't1' : int(t1),
					'listenport': srcPort,
					'bindip': srcIp,
					'bindport' : srcPort}

def deinitialize():
	"""
	build the template message to send in order to deinitialize SIP probe.
	
	@return: deinitialize template to send
	@rtype: dict
	"""
	return None # UDP commands one day ?
	return {'__type': 'abort'}


# basic requests or responses templates
def basicSendRequest(requestType, fromHeader, toHeader, callId, via, cseq, requestUri, maxForwards ):
	"""
	build the template message to send a basic request.
	
	@param requestType: SIP method. for instance: INVITE, REGISTER, BYE ...
	@type requestType: string 
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string	
	@return: basic request template to send
	@rtype: dict
	"""	
	return {'__type':'request', 
				'__message': requestType,
				'__requesturi': requestUri,
				'via':  via,
				'call-id': callId,
				'cseq':  cseq,
				'from': fromHeader,
				'to': toHeader,
				'max-forwards': maxForwards
				}
				
def basicReceivedRequest(method = None, callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a basic request.
	
	@param method: method of the received request. For instance, INVITE.
	@type method: string, any helium matching functions (like any(), regexp, ...)
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: basic request template to match
	@rtype: dict
	"""		
	msg = {'__type':'request'}
	if method != None:
		msg.update({'__message': method})
	if callId != None:
		msg.update({'call-id': callId})
	if fromHeader != None:
		msg.update({'from': fromHeader})
	if toHeader != None:
		msg.update({'to': toHeader})
	if cseq != None:
		msg.update({'cseq': cseq})		
	return msg
	
def basicSendResponse(responseCode, responsePhrase, fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a basic response.
	
	@param responseCode: Status code of the response. For sample '200'
	@type responseCode: string 
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string	
	@return: basic response template to send
	@rtype: dict
	"""
	
	msg = {'__type':'response', 
				'__responsecode': responseCode,
				'__reasonphrase': responsePhrase,
				'via':  via,
				'call-id': callId,
				'cseq':  cseq,
				'from': fromHeader,
				'to': toHeader,
				}	
	msg.update(moreHeaders)
	return msg
		
def basicReceivedResponse( status = None, reason = None, callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a basic response.
	
	@param status: code of the response
	@type status: string, int or any helium matching functions (like any(), regexp, ...)
	@param reason: reason phrase of the response
	@type reason: string, int or any helium matching functions (like any(), regexp, ...)
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: basic response template to match
	@rtype: dict
	"""		
	msg = {'__type':'response'}
	if status != None:
		msg.update({'__responsecode': status})
	if reason != None:
		msg.update({'__reasonphrase': reason})
	if callId != None:
		msg.update({'call-id': callId})
	if fromHeader != None:
		msg.update({'from': fromHeader})
	if toHeader != None:
		msg.update({'to': toHeader})
	if cseq != None:
		msg.update({'cseq': cseq})			
	return msg
		


# some requests template to send
def register(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a register
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	
	@return: register request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('REGISTER', fromHeader, toHeader, callId, via, cseq + ' REGISTER', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg

def invite(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send an invite
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	
	@return: invite request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('INVITE', fromHeader, toHeader, callId, via, cseq + ' INVITE', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
def inviteWithSdp(fromHeader, toHeader, callId, via, cseq, requestUri, sdp, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send an invite with a sdp offer
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param sdp: session description protocol. Invite body.
	@type sdp: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	
	@return: invite request with sdp offer template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('INVITE', fromHeader, toHeader, callId, via, cseq + ' INVITE', requestUri, maxforwards)
	msg.update({'content-type':'application/sdp','__body':sdp})
	msg.update(moreHeaders)
	return msg
def ack(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a ack
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	
	@return: ack request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('ACK', fromHeader, toHeader, callId, via, cseq + ' ACK', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
def ackWithSdp(fromHeader, toHeader, callId, via, cseq, requestUri, sdp, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send an ack with a sdp offer
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param sdp: session description protocol. Ack body.
	@type sdp: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	
	@return: ack request with sdp offer template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('ACK', fromHeader, toHeader, callId, via, cseq + ' ACK', requestUri, maxforwards)
	msg.update({'content-type':'application/sdp','__body':sdp})
	msg.update(moreHeaders)
	return msg
def cancel(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a cancel
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	
	@return: cancel request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('CANCEL', fromHeader, toHeader, callId, via, cseq + ' CANCEL', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
def bye(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a bye
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: bye request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('BYE', fromHeader, toHeader, callId, via, cseq + ' BYE', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
	
def info(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send an info
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: info request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('INFO', fromHeader, toHeader, callId, via, cseq + ' INFO', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
	
def prack(fromHeader, toHeader, callId, via, cseq, requestUri, rack, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a prack
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param rack: rack is the answer of a challenge done by a previous reliability response (100rel support)
	@type rack: string	
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: prack request template to send
	@rtype: dict
	"""	
	msg = basicSendRequest('PRACK', fromHeader, toHeader, callId, via, cseq + ' PRACK', requestUri, maxforwards)
	msg.update({'rack':rack})
	msg.update(moreHeaders)
	return msg
def prackWithSdp(fromHeader, toHeader, callId, via, cseq, requestUri, rack, sdp, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a prack
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param rack: rack is the answer of a challenge done by a previous reliability response (100rel support)
	@type rack: string
	@param sdp: session description protocol. Prack body.
	@type sdp: string	
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: prack request template to send
	@rtype: dict
	"""	
	msg = basicSendRequest('PRACK', fromHeader, toHeader, callId, via, cseq + ' PRACK', requestUri, maxforwards)
	msg.update({'rack':rack, 'content-type':'application/sdp','__body':sdp})
	msg.update(moreHeaders)
	return msg
def option(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send an option
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: option request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('OPTION', fromHeader, toHeader, callId, via, cseq + ' OPTION', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
def subscribe(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a subscribe
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: subscribe request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('SUBSCRIBE', fromHeader, toHeader, callId, via, cseq + ' SUBSCRIBE', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
def notify(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a notify
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: notify request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('NOTIFY', fromHeader, toHeader, callId, via, cseq + ' NOTIFY', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
def refer(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send a refer
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: refer request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('REFER', fromHeader, toHeader, callId, via, cseq + ' REFER', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
def update(fromHeader, toHeader, callId, via, cseq, requestUri, maxforwards = '70', moreHeaders = {}):
	"""
	build the template message to send an update
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' number value.
	@type cseq: string
	@param requestUri: 'request-uri' value used to build request-line
	@type requestUri: string
	@param maxForwards: 'max-forwards' header value
	@type maxForwards: string
	@param moreHeaders: additional headers to add to this register message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict
	@return: update request template to send
	@rtype: dict
	"""		
	msg = basicSendRequest('UPDATE', fromHeader, toHeader, callId, via, cseq + ' UPDATE', requestUri, maxforwards)
	msg.update(moreHeaders)
	return msg
	
# some requests template we can receive
def inviteReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an invite request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: invite template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'INVITE', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def inviteWithSdpReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an invite request with sdp.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: invite with sdp template to match
	@rtype: dict
	"""		
	msg =  basicReceivedRequest(method = 'INVITE', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
	msg.update({'content-type' : 'application/sdp'})
	return msg
def ackReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an ack request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: ack template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'ACK', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def ackWithSdpReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an ack request with sdp.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: ack with sdp template to match
	@rtype: dict
	"""		
	msg = basicReceivedRequest(method = 'ACK', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	msg.update({'content-type' : 'application/sdp'})
	return msg
def cancelReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a cancel request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: cancel template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'CANCEL', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def byeReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a bye request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: bye template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'BYE', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def infoReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an info request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: info template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'INFO', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def prackReceived(callId = None, fromHeader = None, toHeader = None , cseq = None, rack = None):
	"""
	build the template message to match a prack request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@param rack: rack of the received request.
	@type rack: string, any helium matching functions (like any(), regexp, ...)	
	@return: prack template to match
	@rtype: dict
	"""		
	msg = basicReceivedRequest(method = 'PRACK', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	if rack is not None:
		msg.update({'rack' : rack})
	return msg
	
def prackWithSdpReceived(callId = None, fromHeader = None, toHeader = None , cseq = None, rack = None):
	"""
	build the template message to match a prack request with sdp.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)	
	@param rack: rack of the received request.
	@type rack: string, any helium matching functions (like any(), regexp, ...)		
	@return: prack with sdp template to match
	@rtype: dict
	"""		
	msg = basicReceivedRequest(method = 'PRACK', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	msg.update({'content-type' : 'application/sdp'})
	if rack is not None:
		msg.update({'rack' : rack})	
	return msg
def optionReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an option request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: option template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'OPTION', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def subscribeReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a subscribe request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: subscribe template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'SUBSCRIBE', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)

def notifyReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a notify request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: notify template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'NOTIFY', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def referReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a refer request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: refer template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'REFER', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
def updateReceived(callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an update request.
	
	@param callId: callId of the received request.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received request.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received request.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received request.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)		
	@return: update template to match
	@rtype: dict
	"""		
	return basicReceivedRequest(method = 'UPDATE', callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
	
# some response template to send
def response100( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 100 Trying
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 100 trying template to send
	@rtype: dict
	"""
	msg = basicSendResponse('100', 'Trying', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response183( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 183 Session Progress
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 183 Session Progress template to send
	@rtype: dict
	"""
	msg = basicSendResponse('183', 'Session Progress', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response180( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 180 Ringing
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 180 Ringing template to send
	@rtype: dict
	"""
	msg = basicSendResponse('180', 'Ringing', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response200( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 200 Ok
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 200 Ok template to send
	@rtype: dict
	"""
	msg = basicSendResponse('200', 'Ok', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg	
def response200WithSdp( fromHeader, toHeader, callId, via, cseq, sdp, moreHeaders = {}):
	"""
	build the template message to send a 200 Ok with sdp
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param sdp: session description protocol. Ack body.
	@type sdp: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 200 Ok with sdp template to send
	@rtype: dict
	"""
	msg = basicSendResponse('200', 'Ok', fromHeader, toHeader, callId, via, cseq)
	msg.update({'content-type':'application/sdp','__body':sdp})	
	msg.update(moreHeaders)
	return msg
def response400( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 400 Bad Request
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 400 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('400', 'Bad Request', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
	
def response405( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 405 Method Not Allowed
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 405 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('405', 'Method Not Allowed', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response406( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 406 Not Acceptable Here
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 406 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('406', 'Not Acceptable Here', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response415( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 415 Unsupported Media Type
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 415 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('415', 'Unsupported Media Type', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response416( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 416 Unsupported URI Scheme
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 416 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('416', 'Unsupported URI Scheme', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response480( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 480 Temporarily Unavailable
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 480 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('480', 'Temporarily Unavailable', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response481( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 481 Call/Transaction Does Not Exist 
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 481 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('481', 'Call/Transaction Does Not Exist', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response486( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 486 Busy Here
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 486 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('486', 'Busy Here', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response487( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 487 Request Terminated
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 487 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('487', 'Request Terminated', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
	
def response488( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 488 Not Acceptable Here 
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 488 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('488', 'Not Acceptable Here ', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
	
def response500( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 500 Server Internal Error
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 500 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('500', 'Server Internal Error', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response501( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 501 Not Implemented
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 501 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('501', 'Not Implemented', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response603( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 603 Decline
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 603 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('603', 'Decline', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
def response606( fromHeader, toHeader, callId, via, cseq, moreHeaders = {}):
	"""
	build the template message to send a 606 Not Acceptable Here
	
	@param fromHeader: 'from' header value
	@type fromHeader: string
	@param toHeader: 'to' header value
	@type toHeader: string
	@param callId: 'callId' header value
	@type callId: string	
	@param via: 'via' header value
	@type via: string	
	@param cseq: 'cseq' header value.
	@type cseq: string
	@param moreHeaders: additional headers to add to this response message. Be careful, it may override some existed key like 'from' or 'to'
	@type moreHeaders: dict	
	@return: 606 template to send
	@rtype: dict
	"""
	msg = basicSendResponse('606', 'Not Acceptable', fromHeader, toHeader, callId, via, cseq)
	msg.update(moreHeaders)
	return msg
	
# some reponses template we can receive
def received1xxResponse( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 1xx response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 1xx response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = regexp(r'^[1].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def received1xxResponseWithSdp( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 1xx response with sdp
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 1xx response with sdp template to match
	@rtype: dict
	"""		
	msg = basicReceivedResponse( status = regexp(r'^[1].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	msg.update({'content-type' : 'application/sdp'})
	return msg
def received180Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 180 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 180 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '180', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def received180ResponseWithSdp( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 180 response with sdp
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 180 response with sdp template to match
	@rtype: dict
	"""		
	msg = basicReceivedResponse( status = '180', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	msg.update({'content-type' : 'application/sdp'})
	return msg
def received183Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 183 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 183 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '183', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def received183ResponseWithSdp( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 183 response with sdp
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 183 response with sdp template to match
	@rtype: dict
	"""		
	msg = basicReceivedResponse( status = '183', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	msg.update({'content-type' : 'application/sdp'})
	return msg	
def received2xxResponse( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 2xx response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 2xx response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = regexp(r'^[2].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def received2xxResponseWithSdp( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 2xx response with sdp
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 2xx response with sdp template to match
	@rtype: dict
	"""		
	msg = basicReceivedResponse( status = regexp(r'^[2].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	msg.update({'content-type' : 'application/sdp'})
	return msg
def received200Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 200 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 200 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '200', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
def received200ResponseWithSdp( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 200 response with sdp
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 200 response with sdp template to match
	@rtype: dict
	"""		
	msg = basicReceivedResponse( status = '200', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
	msg.update({'content-type' : 'application/sdp'})
	return msg
def received202Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 202 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 202 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '202', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
def received3xxResponse( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 3xx response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 3xx response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = regexp(r'^[3].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
def received4xxResponse( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 4xx response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 4xx response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = regexp(r'^[4].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def received401Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 401 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 401 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '401', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def received481Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 481 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 481 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '481', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
def received486Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 486 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 486 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '486', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
def received487Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 487 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 487 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '487', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)		
def received488Response( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 488 response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 488 response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = '488', reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)			
def received5xxResponse( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 5xx response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 5xx response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = regexp(r'^[5].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
def received6xxResponse( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match a 6xx response.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: 6xx response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = regexp(r'^[6].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)	
def receivedErrorResponse( callId = None, fromHeader = None, toHeader = None , cseq = None):
	"""
	build the template message to match an error response. Error responses are all 3xx, 4xx, 5xx and 6xx responses.
	
	@param callId: callId of the received response.
	@type callId: string, any helium matching functions (like any(), regexp, ...)	
	@param fromHeader: from of the received response.
	@type fromHeader: string, any helium matching functions (like any(), regexp, ...)
	@param toHeader: to of the received response.
	@type toHeader: string, any helium matching functions (like any(), regexp, ...)
	@param cseq: cseq of the received response.
	@type cseq: string, any helium matching functions (like any(), regexp, ...)			
	@return: error response template to match
	@rtype: dict
	"""		
	return basicReceivedResponse( status = regexp(r'^[3|4|5|6].*'), reason = any(), callId = callId, fromHeader = fromHeader, toHeader = toHeader , cseq = cseq)
