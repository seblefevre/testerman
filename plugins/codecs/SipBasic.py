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
# Simplified SIP codec.
#
# The message structure is not as complex as for the SIP codec, as it
# is a flat dictionnary.
#
# Multi-values are decoded/encoded as a multi-line (\n-separated) single value.
##

"""
type record SipMessageType
{
	charstring __type, // "request" or "response"
	...
}


"""

import CodecManager


import re

# The compact forms for header name. You shoud map it to its non-compact form
# only (case-insensitive), as the above transformation still applies once
# the compact form has been "expanded".
CompactHeaderNames = {
'i': 'call-id',
'm': 'contact',
'e': 'content-encoding',
'l': 'content-length',
'c': 'content-type',
'f': 'from',
's': 'subject',
'k': 'supported',
't': 'to',
'v': 'via',
}

# By default, fields are considered monovalued when decoding them, 
# leading to a non-list associated value,
# but automatically turns to a list if actually multivalued on the wire.
# However, for some fields, we can force a multivalue structure even if 
# only one header line is present.
# So, if you want to consider some headers as multivaluable by default,
# insert its name/identifier in this list.
MultiValuedHeaders = [
'route',
'via',
'allow',
'accept-encoding',
'supported',
'unsupported',
'require',
'content-coding',
'call-info',
'alert-info',
'language',
'accept',
]

##
# Request Line
##
def encode_RequestLine(p):
	return "%s %s SIP/2.0" % (p['__message'], p['__requesturi'])

def decode_RequestLine(s):
	a, b, c = s.split(' ', 2)
	return dict(__message = a.strip(), __requesturi = b.strip(), __version = c.strip())

##
# Status Line
##
def encode_StatusLine(p):
	return "%s %s %s" % ('SIP/2.0', p['__responsecode'], p['__reasonphrase'])

def decode_StatusLine(s):
	a, b, c = s.split(' ', 2)
	return dict(__version = a.strip(), __responsecode = b.strip(), __reasonphrase = c.strip())

##
# Messages
##

def fieldNameToName(name):
	"""
	From a header name on the wire, returns the associated record entry name
	in the userland message.
	"""
	n = name.lower()
	# Search compact names
	if n in CompactHeaderNames:
		n = CompactHeaderNames[n]
	return n

def encodeHeader(name, fieldName, value):
	"""
	Actually writes the header.
	"""
	ret = []
	value = unicode(value)

	for v in value.split('\n'):
		if v.strip():
			ret.append('%s: %s' % (fieldName, v))

	return '\r\n'.join(ret)

def decodeMessage(s):
	"""
	s is a list of lines after the request/status line.
	Also contains a body.
	"""
	ret = {}
	s = s.split('\r\n')
	firstLine = s[0]
	if firstLine.startswith('SIP/'):
		ret['__type'] = 'response'
		ret.update(decode_StatusLine(firstLine))
	else:
		ret['__type'] = 'request'
		ret.update(decode_RequestLine(firstLine))

	headers = {}
	def addHeader(previousHeaderLine):
		# Split multivalued headers into multiple headers, if needed.

		s = previousHeaderLine.split(':', 1)
		fieldName = s[0].strip()
		encodedValue = s[1].strip()
		name = fieldNameToName(fieldName)
		if name in MultiValuedHeaders:
			encodedValues = filter(lambda x: x, map(lambda x: x.strip(), encodedValue.split(',')))
		else:
			encodedValues = [ encodedValue ]

		value = '\n'.join(encodedValues)

		if name in headers:
			# concatenate values
			headers[name] = headers[name] + '\n' + value
		else:
			headers[name] = value

	i = 1
	previousHeaderLine = None
	for line in s[i:]:
		if not line.strip():
			# reached the body
			i += 1
			if previousHeaderLine: addHeader(previousHeaderLine)
			break
		# Multiline support - value continuation
		elif line.startswith(' ') or line.startswith('\t'):
			if previousHeaderLine:
				previousHeaderLine += ' ' + line.strip()
		else:
			try:
				a, b = line.split(':', 1)
			except:
				raise Exception("Invalid header format: %s" % line)
			# Parse the previous header
			if previousHeaderLine: addHeader(previousHeaderLine)
			previousHeaderLine = line.strip()
		i += 1

	if s[i:]:
		body = '\r\n'.join(s[i:])
		ret['__body'] = body

	ret.update(headers)
	return ret

def encodeMessage(p):
	ret = []
	if p['__type'] == 'response':
		ret.append(encode_StatusLine(p))
	elif p['__type'] == 'request':
		ret.append(encode_RequestLine(p))
	else:
		raise Exception("Invalid message: not a response or request")
	# Now continue with the headers and body encoding.
	contentLengthWritten = False
	for name, value in p.items():
		if name.startswith('__'):
			continue
		if name == 'content-length':
			contentLengthWritten = True
		fieldName = name
		fieldValue = value
		ret.append(encodeHeader(name, fieldName, fieldValue))
	if not contentLengthWritten:
		ret.append(encodeHeader('content-length', 'content-length', len(p.get('__body', ''))))

	ret.append('')
	if '__body' in p and p['__body']:
		ret.append(p['__body'])
	return '\r\n'.join(ret)


##
# The Testerman codec interface to the codec
##

class SipBasicCodec(CodecManager.Codec):
	def encode(self, template):
		return encodeMessage(template)

	def decode(self, data):
		return decodeMessage(data)

if __name__ != '__main__':
	CodecManager.registerCodecClass('sip.basic', SipBasicCodec)

else:


	sets = [

	# Message
	('Message',
	decodeMessage, encodeMessage, [
"""INVITE sip:146127953@esg SIP/2.0
Via: SIP/2.0/UDP 172.16.4.238:57516;branch=z9hG4bK-d8754z-55019e456f11e949-1---d8754z-;rport
Max-Forwards: 70
Contact: <sip:seb@172.16.4.238:57516>
To: "146127953"<sip:146127953@esg>
From: "Seb"<sip:seb@esg>;tag=f4287c66
Call-ID: ZWYyY2M5OTNiZTkwNjE0NDU0ZmEzZmIwNzI4YmNjY2Q.
CSeq: 1 INVITE
Allow: INVITE, ACK,
Allow: CANCEL, OPTIONS, BYE, REFER, NOTIFY, MESSAGE, SUBSCRIBE, INFO
Content-Type: application/sdp
User-Agent: X-Lite release 1100l stamp 47546
Content-Length: 285

v=0
o=- 9 2 IN IP4 172.16.4.238
s=CounterPath X-Lite 3.0
c=IN IP4 172.16.4.238
t=0 0
m=audio 56352 RTP/AVP 0 8 101
a=alt:1 2 : GQ59frJT GVslSfEi 172.16.4.238 56352
a=alt:2 1 : +Pyo15J5 x+F0PCxX 192.168.42.3 56352
a=fmtp:101 0-15
a=rtpmap:101 telephone-event/8000
a=sendrecv
""".replace("\n", "\r\n"),
"""INVITE sip:146127953@172.16.110.142 SIP/2.0
Via: SIP/2.0/UDP 172.16.4.238:5060;branch=z9hG4bK8606A188A4651BD550F06BB83B25552C;rport
Via: SIP/2.0/UDP 172.16.4.238:57516;branch=z9hG4bK-d8754z-55019e456f11e949-1---d8754z-;rport
From: "Your Full Name" <sip:Username@172.16.4.238:5060>;tag=5D1166A000826DB42FF1E837CC985BEC
To: <sip:146127953@172.16.110.142>
Contact: <sip:Username@172.16.4.238:5060;transport=udp>
Call-ID: 2C5BBFEE64F4D62489DD111271ED9492@172.16.4.238
User-Agent: Kapanga Softphone Desktop 1.00/2175d+1232699808_0016447B0E9A_545543445209_00037ABE8AAE_00174274CF9B_005056C00001
Supported: timer, replaces
CSeq: 1 INVITE
Max-Forwards: 70
Session-Expires: 1800;refresher=uac
Content-Type: application/sdp
Content-Length: 386

v=0
o=Username 1232699815 1232700296 IN IP4 172.16.4.238
s=Kapanga [1232699815]
c=IN IP4 172.16.4.238
t=0 0
m=audio 5106 RTP/AVP 8 0 101
a=rtpmap:8 pcma/8000
a=sendrecv
a=rtcp:5107
a=maxptime:20
a=ptime:20
a=rtpmap:0 pcmu/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-15,36
m=video 5108 RTP/AVP 34
a=rtpmap:34 h263/90000
a=fmtp:34 QCIF=2
a=sendrecv
a=rtcp:5109
""".replace('\n', '\r\n'),

"""SIP/2.0 200 Ok
Call-ID: 2C5BBFEE64F4D62489DD111271ED9492@172.16.4.238
Content-Length: 321
Content-Type: application/sdp
CSeq: 1 INVITE
From: "Your Full Name" <sip:Username@172.16.4.238:5060>;tag=5D1166A000826DB42FF1E837CC985BEC
Supported: timer
Supported: replaces
To: sip:146127953@172.16.110.142;tag=68384732255484
Via: SIP/2.0/UDP 172.16.4.238:5060;branch=z9hG4bK8606A188A4651BD550F06BB83B25552C;received=172.16.4.238;rport=5060

v=0
o=Divaphone 749 1232704074 IN IP4 172.16.120.80
s=DivaphoneVoice
i=Divaphone DivaphoneVoice
c=IN IP4 172.16.120.80
t=0 0
m=audio 51626 RTP/AVP 8 101
a=rtpmap:8 pcma/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-15,32,36
a=ptime:20
a=maxptime:20
a=sendrecv
a=rtcp:51627
a=silenceSupp:off - - -
""".replace('\n', '\r\n'),

"""ACK sip:146127953@172.16.110.142 SIP/2.0
Via: SIP/2.0/UDP 172.16.4.238:5060;branch=z9hG4bK080812205B026985E371147050CA117F;rport
From: "Your Full Name" <sip:Username@172.16.4.238:5060>;tag=5D1166A000826DB42FF1E837CC985BEC
To: sip:146127953@172.16.110.142;tag=68384732255484
Contact: <sip:Username@172.16.4.238:5060;transport=udp>
Call-ID: 2C5BBFEE64F4D62489DD111271ED9492@172.16.4.238
User-Agent: Kapanga Softphone Desktop 1.00/2175d+1232699808_0016447B0E9A_545543445209_00037ABE8AAE_00174274CF9B_005056C00001
CSeq: 1 ACK
Max-Forwards: 70
Content-Length: 0

""".replace('\n', '\r\n'),
	]),
	]

	for (label, decode_f, encode_f, samples) in sets:
		print "======== %s =======" % label
		for s in samples:
			decoded = decode_f(s)
			print decoded
			reencoded = encode_f(decoded)
			print
			print "Reencoded: %s" % reencoded
			print "Original : %s" % s
			# assert (s == reencoded)
			print


	
