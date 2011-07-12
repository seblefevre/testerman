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
Virtual SIP Endpoint template control messages.
"""

##
# To clean up. Correct actions and events. Remove meta events and "questions" in templates.
##
def m_playWavFile(callId, resource, loopCount = 1):
	"""Sends this message to play a WAV file. The endpoint must be sending RTP."""
	return { 'action': 'play-wav', 'callId': callId, 'resource': resource, 'loopCount': loopCount }


# actions
def callId(id = None, portRtpChoosed = None): 
	tmp = { 'event': 'call id and rtp port selected', 'call-id': id}
	if portRtpChoosed != None:
		tmp.update( {'rtp-port': portRtpChoosed})
	return tmp
def dtmf( signal = None, duration = None): 
	return { 'action': 'dtmf', 'signal': signal, 'duration': duration}
#
def plug(): return { 'action': 'initialize'}
def plugAll(endpoints, timeout): return { 'action': 'initialize', 'endpoints':endpoints, 'timeout': timeout}
def isStarted(name): return { 'event': 'is started', 'name': name}
def isStopped(name): return { 'event': 'is stopped', 'name': name}
def areStarted(): return { 'event': 'all endpoints are started'}
def areStopped(): return { 'event': 'all endpoints are stopped'}
def unplug(): return { 'action': 'deinitialize' }
def unplugAll(endpoints, timeout): return { 'action': 'deinitialize', 'timeout': timeout,'endpoints':endpoints}
#
def configure(conf): return { 'action': 'configure', 'conf': conf}
def configureAll(endpoints, conf): return { 'action': 'configure', 'conf': conf,'endpoints':endpoints}
#
def areUnregistered(): return { 'event': 'all endpoints are unregistered'}
def areRegistered(): return { 'event': 'all endpoints are registered'}
def register(expires = None): 
	tmp = { 'action': 'register'}
	if expires != None:
		tmp.update({'expires': expires })
	return tmp
def registerAll(endpoints, timeout, args): 
	tmp = { 'action': 'register all', 'timeout': timeout,'endpoints':endpoints, 'args': args}
	return tmp	
def unregister(): return { 'action': 'unregister'}
def unregisterAll(endpoints, timeout): return { 'action': 'unregister', 'timeout': timeout,'endpoints':endpoints  }
def registered(pAsssociatedUri = None): 
	tmp =	{'event': 'phone registered'}
	if pAsssociatedUri != None:
		pAsssociatedUri = pAsssociatedUri.splitlines()
		tmp.update({'p-asssociated-uri': pAsssociatedUri})
	return tmp
def notRegistered(): return {'event': 'phone not registered'}
#
def subscribe(service, expires = None, uri = None): 
	tmp = { 'action': 'subscribe', 'service': service}
	if expires != None:
		tmp.update( {'expires': expires})
	if uri != None:
		tmp.update( {'uri': uri})
	return tmp
def unsubscribe(service): return { 'action': 'unsubscribe', 'service': service }
def onHold(): return { 'action': 'placing connected call on hold' }
def retrieveCall(callId): return { 'action': 'retrieve call', 'call-id': callId }
def pickUp(callId): return { 'action': 'pick-up',  'call-id': callId}
def hangUp(callId, headers = None, additionalHeaders = None): 
	tmp = {'action':'hang-up',  'call-id': callId}
	if headers != None:
		tmp.update({'headers': headers})
	if additionalHeaders != None:
		tmp.update({'additional-headers': additionalHeaders})	
	return tmp
def call(calledUri, headers = None, additionalHeaders = None, timerBetween200OkandAck = None, sdp = None): 
	tmp = { 'action': 'call', 'called-uri': calledUri}
	if headers != None:
		tmp.update({'headers': headers})
	if additionalHeaders != None:
		tmp.update({'additional-headers': additionalHeaders})	
	if timerBetween200OkandAck != None:
		tmp.update({'timer-between-200ok-ack': timerBetween200OkandAck})	
	if sdp != None:
		tmp.update({'sdp': sdp})	
	return tmp
def showCallLogs(): return  {'action':'show call logs'}
def showConf(): return {'action':'show configuration'}
def transfer(refer, to, type): 
	return { 'action': 'transfer', 'refer': refer, 'to': to, 'type': type}
def joinConference(refer, to, type): 
	return { 'action': 'join', 'refer': refer, 'to': to, 'type': type}
def transferSuccessful(callId) : return {'event': 'transfer successful', 'call-id': callId}
def transferAccepted(callId) : return {'event': 'transfer accepted', 'call-id': callId}
def transferFailed(callId) : return {'event': 'transfer failed', 'call-id': callId}
def eventUpdate(callId, descriptions) : 
	tmp = {'event': 'update received', 'call-id': str(callId)}
	tmp.update(descriptions)
	return tmp

def eventDtmf(signal, duration): 
	tmp =  {'event': 'dtmf'}
	if signal != None:
		tmp.update({'signal': signal})
	if duration != None:
		tmp.update({'duration': duration})
	return tmp
def dtmfDialed(): return {'event': 'dtmf dialed'}
def notify(descriptions): 
	tmp = {'event': 'notify received'}
	tmp.update(descriptions)
	return tmp
	
#
def unsubscribeSuccessful(service): return {'event': 'unsubscribe successful', 'service': service}
def subscribed(service): return {'event': 'subscribed', 'service': service}
def subscriptionFailed(service, reason): return  {'event': 'subscription failed', 'service': service, 'reason': reason}
def unsubscriptionFailed(service, reason): return  {'event': 'unsubscription failed', 'service': service, 'reason': reason}
#
def referFailed(reason): return  {'event': 'refer failed', 'reason': reason}
def registrationFailed(reason): return  {'event': 'registration failed', 'reason': reason}
def isOnHold(callId): return {'event': 'the call is on hold', 'call-id': callId}
#
def isRinging(callId, descriptions): 
	tmp = {'event': 'ringing', 'call-id': callId}
	tmp.update(descriptions)
	return tmp
def areRingingAll(endpoints, timeout, args): return { 'action': 'are ringing ?', 'endpoints': endpoints, 'timeout': timeout, 'args': args }
def areRinging(data):return {'event': 'endpoints are ringing', 'data': data }
#
def isRingBackTone(callId, descriptions= {}): 
	tmp =	{'action': 'ringback tone', 'call-id':callId } 
	tmp.update(descriptions)
	return tmp
	
#	
#def isRingBackTone(callId, pAssertedIdentity = None): 
#	tmp = {'event': 'ringback tone', 'call-id': callId }
#	if pAssertedIdentity != None:
#		tmp.update( {'p-asserted-identity': pAssertedIdentity })
#	return tmp
def configurationFailed(reason): return { 'event': 'configuration failed', 'reason': reason }
#
def isConnected(callId): return {'event': 'The call is connected', 'call-id': callId }
def areConnectedAll(endpoints, timeout): return { 'action': 'are connected ?', 'endpoints': endpoints, 'timeout': timeout }
def areConnected(): return {'event': 'endpoints are connected' }
#
def isReliabilitySuccessful(callId): return {'event': 'reliability successful', 'call-id': str(callId) }
#
def isDisconnected(callId, descriptions = {}):
	tmp = {'event': 'The call is disconnected', 'call-id': callId }
	tmp.update(descriptions)
	return tmp
def areCallDisconnectedAll(endpoints, timeout, args):
	return { 'action': 'calls are disconnected ?', 'endpoints': endpoints, 'timeout': timeout, 'args': args}
def areDisconnected(): return {'event': 'calls are disconnected' }
#
def areConnectedAndReceivingAudioAll(endpoints, timeout, args):
	return { 'action': 'are connected and receiving audio ?', 'endpoints': endpoints, 'timeout': timeout, 'args': args}
def areConnectedAndAudio(): return {'event': 'endpoints are connected and receiving audio' }
#
def isReceivingRtp(callId, description): 
	template = { 'event': 'started-receiving-rtp', 'call-id': callId }
	if description.has_key('ssrc') and not ( hasattr(description['ssrc'], 'eval') and  callable(description['ssrc'].eval) ) :
			description['ssrc'] = int(description['ssrc'])
	if description.has_key('payload-type') and not ( hasattr(description['payload-type'], 'eval') and  callable(description['payload-type'].eval) ) :
		description['payload-type'] = int(description['payload-type'])
	if description.has_key('from-port') and not ( hasattr(description['from-port'], 'eval') and  callable(description['from-port'].eval) ) :
		description['from-port'] = int(description['from-port'])	
			
	template.update(description)
	return template
def areReceivingAudioAll(endpoints, timeout, args):
	return { 'action': 'are receiving audio ?', 'endpoints': endpoints, 'timeout': timeout, 'args': args}
def areReceivingAudio(): return {'event': 'endpoints are receiving one stream audio' }
#
def retransmissionFinished(message): return { 'event': 'retransmission finished', 'retransmission': message }
def stoppedReceivingRtp(callId, description):
	template =  { 'event': 'stopped receiving rtp stream', 'call-id': callId}
	if description.has_key('reason'):
			template.update({'reason': description['reason'] })	
	return template
def error(descriptions): 
	tmp = { 'event': 'error'}
	tmp.update(descriptions)
	return tmp
def info(reason): return { 'event': 'info', 'reason': reason }
def negociationCodecFailed(callId): return { 'event': 'codec negociation failed', 'call-id': str(callId) }
def infoReceived(callId, application, body):
	return { 'event': 'info received ', 'call-id': callId, 'body': body, 'application' : application}
def cancelReceived(callId, reason = None):
	tmp = {'event': 'cancel received'}
	if reason != None:
		tmp.update({'reason': reason})
	return tmp
def isCancelled(callId): return { 'event': 'the call has been cancelled', 'call-id': str(callId)}
def callLogs(dialed, missed, received, failed): 
	return {'event': 'call logs', 'dialed': str(dialed), 'missed': str(missed), 'received': str(received), 'failed': str(failed) }
def prackReceived(callId): return {'event': 'prack received', 'call-id': str(callId) }
#
def isIdle(callId): return {'event': 'idle', 'call-id': str(callId) } 
def areIdleAll(endpoints, timeout): return {'event': 'are idle ?', 'endpoints': endpoints, 'timeout': timeout } 
def areIdle(): return {'event': 'idle' }
# 
def haveReceivedAudioInterruptionAll(endpoints, timeout, args):
	return { 'action': 'have received audio interruption ?', 'endpoints': endpoints, 'timeout': timeout, 'args': args} 
def haveReceivedAudioInterruption(): return {'event': 'endpoints have received audio interruption' }
#
def releaseActiveCalls(): return {'action': 'release active calls' }
def releaseActiveCallsAll(endpoints): return {'action': 'release active calls of each endpoints', 'endpoints': endpoints } 
#
def isCallUpdated(callId): return {'event': 'session updated', 'call-id': str(callId) } 
def areUpdatedAndReceivingAudioAll(endpoints, timeout, args):
	return { 'action': 'are updated and receiving audio ?', 'endpoints': endpoints, 'timeout': timeout, 'args': args}
def areUpdatedAndAudio(): return {'event': 'endpoints are updated and receiving audio' }
# 
def divert(callId, descriptions= {}): 
	tmp =	{'action': 'divert', 'call-id':callId } 
	tmp.update(descriptions)
	return tmp
def reject(callId, descriptions= {}): 
	tmp =	{'action': 'reject', 'call-id':callId } 	
	tmp.update(descriptions)
	return tmp
def updateToSend(callId, descriptions = {}): 
	tmp =	{'action': 'update', 'call-id':callId } 	
	tmp.update(descriptions)
	return tmp

def isUpdated(callId): return {'event': 'session updated', 'call-id': callId }


