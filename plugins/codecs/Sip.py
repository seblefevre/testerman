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
# SIP codec.
#
# (Mostly) Follows the template structure as defined by
# TTCN-3 official SIP test suites:
# http://webapp.etsi.org/WorkProgram/Report_WorkItem.asp?WKI_ID=27294&curItemNr=1&totalNrItems=2&optDisplay=10&qSORT=HIGHVERSION&qETSI_ALL=&SearchPage=TRUE&qETSI_NUMBER=102+027-3&qINCLUDE_SUB_TB=True&qINCLUDE_MOVED_ON=&qSTOP_FLG=&qKEYWORD_BOOLEAN=&qSTOPPING_OUTDATED=&butSimple=Search&includeNonActiveTB=&includeSubProjectCode=&qREPORT_TYPE=
# File: SIP_TypesAndConf.ttcn
#
# Exceptions are documented with # Exception
##

"""
type record GenericParam {
  charstring id optional, // the parameter name
  charstring value optional // the parameter value
}
type set of GenericParam SemicolonParam_List;

type SemicolonParam_List AmpersandParam_List;

type SemicolonParam_List CommaParam_List;

type record HostPort {
  // "host" field changed to be optional: when tel-URI is used, it is
  // sent in the userInfo field of SipUrl; in this case the hostPort
  // field is present in SipUrl (mandatory field) but empty; hence both
  // the host and portField fields of hostPort shall be omitted
  charstring host optional, // hostname, IPv4 or IPv6
  integer port optional // represented as an integer
}

type record UserInfo {
  charstring user optional,
  charstring password optional
}

type record SipUrl {
  charstring scheme, // contains "sip:", "tel:", etc
  UserInfo userInfo optional,
  HostPort hostPort,
  SemicolonParam_List urlParameters optional,
  AmpersandParam_List headers optional
}

type record AcceptBody { // Not implemented in Testerman
  charstring mediaRange,
  SemicolonParam_List acceptParam optional
}

type set of AcceptBody AcceptBody_List; // Not implemented in Testerman

type record AlertInfoBody { // Not implemented in Testerman
  charstring url, // any URI
  SemicolonParam_List genericParams optional
}

type set of AlertInfoBody AlertInfoBody_List; // Not implemented in Testerman

type charstring CallidString;
type set of CallidString CallidString_List;

type record CallInfoBody { // NI in Testerman
  charstring url, // any URI
  SemicolonParam_List infoParams optional
}

type set of CallInfoBody CallInfoBody_List; // NI in Testerman

type union Challenge { // NI in Testerman
  CommaParam_List digestCln,
  OtherAuth otherChallenge
}

// NameAddr is used in From, To : contains a SIP Url + optional quoted display
// On encoding, always double-quoted and encoded to utf-8.
// On decoding, double-quotes, if any, are removed, and decoded to unicode.
type record NameAddr {
  charstring displayName optional,
  SipUrl sipUrl
}

type record ContactAddress {
  NameAddr addressField,
  SemicolonParam_List parameters optional
}

type set of ContactAddress ContactAddress_List;

type charstring ContentCoding;

type set of ContentCoding ContentCoding_List;

// [20.7, 20.28; RFC2616 14.35 RFC2617 1.2]
type union Credentials { // NI in Testerman
  CommaParam_List digestResponse,
  OtherAuth otherResponse
}

// [20.19, 20.23, 20.33]
type charstring DeltaSec; // NI in Testerman
// an external operation can handle this field
// [20.18]
type record ErrorInfoBody { // NI in Testerman
  charstring uri, // any URI
  SemicolonParam_List genericParams optional
}

// [20.18]
type set of ErrorInfoBody ErrorInfoBody_List; // NI in Testerman

// [20.3 RFC2616 14.4]
type record LanguageBody { // NI in Testerman
  charstring languageRange,
  SemicolonParam_List acceptParam optional
}

// [20.3 RFC2616 14.4]
type set of LanguageBody LanguageBody_List; // NI in Testerman

// [20.13; RFC2616 14.12]
type charstring LanguageTag;

// [20.13; RFC2616 14.12]
type set of LanguageTag LanguageTag_List;

// [20.5]
type set of charstring Method_List;

// [20.29, 20.32, 20.37, 20.40]
type charstring OptionTag;

// [20.29, 20.32, 20.37, 20.40]
type set of OptionTag OptionTag_List;

// [20.7, 20.27, 20.28, 20.44  ; RFC2616 14.33, 14.47; RFC2617 1.2]
type record OtherAuth { // NI in Testerman
  charstring authScheme,
  CommaParam_List authParams
}

type record Payload { // NI in Testerman
  integer payloadlength,
  charstring payloadvalue
}

// [20.30,20.34]
type record RouteBody {
  NameAddr nameAddr,
  SemicolonParam_List parameters optional
}

// [20.30,20.34]
type record of RouteBody RouteBody_List;

// [20.42]
type record SentProtocol {
  charstring protocolName,
  charstring protocolVersion,
  charstring transport
}

// [20.42]
type record ViaBody {
  SentProtocol sentProtocol,
  HostPort sentBy,
  SemicolonParam_List parameters optional
}

// [20.35, 20.41; RFC2616 14.43]
type charstring ServerVal;

// [20.35, 20.41; RFC2616 14.43]
type set of ServerVal ServerVal_List;

// [20.38]
type record TimeValue { // NI in Testerman
  integer majorDigit, // represented as an integer
  integer minorDigit optional // represented as an integer
}

// [20.43]
type union WarnAgent { // NI in Testerman
  HostPort hostPort,
  charstring pseudonym
}

// [20.43]
type record WarningValue { // NI in Testerman
  integer warnCode, // represented as an integer
  WarnAgent warnAgent,
  charstring warnText
}

// [20.43]
type set of WarningValue WarningValue_List;


// [20.1, RFC2616 14.1]
type record Accept {
  FieldName fieldName(ACCEPT_E),
  AcceptBody_List acceptArgs optional
}

// [20.2, RFC2616 14.3]
type record AcceptEncoding {
  FieldName fieldName(ACCEPT_ENCODING_E),
  ContentCoding_List contentCoding optional
}

// [20.3, RFC2616 14.4]
type record AcceptLanguage {
  FieldName fieldName(ACCEPT_LANGUAGE_E),
  LanguageBody_List languageBody optional
}

// [20.4]
type record AlertInfo {
  FieldName fieldName(ALERT_INFO_E),
  AlertInfoBody_List alertInfoBody optional
}

// [20.5]
type record Allow {
  FieldName fieldName(ALLOW_E),
  Method_List methods optional
}

// [20.6]
type record AuthenticationInfo {
  FieldName fieldName(AUTHENTICATION_INFO_E),
  CommaParam_List ainfo
}

// [20.7 RFC2617 3.2.2]
type record Authorization {
  FieldName fieldName(AUTHORIZATION_E),
  charstring body optional
}

// [20.8]
type record CallId {
  FieldName fieldName(CALL_ID_E) optional,
  CallidString callid optional
}

// [20.9]
type record CallInfo {
  FieldName fieldName(CALL_INFO_E),
  CallInfoBody_List callInfoBody optional
}

// [20.10]
type record Contact {
  FieldName fieldName(CONTACT_E),
  ContactBody contactBody
}

// [20.11]
type record ContentDisposition {
  FieldName fieldName(CONTENT_DISPOSITION_E),
  charstring dispositionType,
  SemicolonParam_List dispositionParams optional
}

// [20.12 RFC2616 14.11]
type record ContentEncoding {
  FieldName fieldName(CONTENT_ENCODING_E),
  ContentCoding_List contentCoding
}

// [20.13 RFC2616 14.12]
type record ContentLanguage {
  FieldName fieldName(CONTENT_LANGUAGE_E),
  LanguageTag_List languageTag
}

// [20.14]
type record ContentLength {
  FieldName fieldName(CONTENT_LENGTH_E),
  integer len // this field is represented as an integer
}

// [20.15]
type record ContentType {
  FieldName fieldName(CONTENT_TYPE_E),
  charstring mediaType optional
}

// [20.16]
type record CSeq {
  FieldName fieldName(CSEQ_E),
  integer seqNumber,
  // this field is represented as an integer
  charstring method
}

type record GenericHeader {
  FieldName fieldName,
	charstring fieldValue,
	record of charstring rawValues,
}

type union MessageHeader {
  Cseq CSeq,
	ContentType ContentType,
	...
	GenericHeader <GenericName>,
}

type set of MessageHeader MessageHeaders;

// Request-Line [7.1]
type record RequestLine {
  Method method,
  SipUrl requestUri,
  charstring sipVersion
}

// Status-Line [7.2]
type record StatusLine {
  charstring sipVersion,
  integer statusCode,
  charstring reasonPhrase
}

// Main templates to the codec
type record Request {
  RequestLine requestLine,
  MessageHeaders messageHeaders,
  charstring messageBody optional,
}

type record Response {
  StatusLine statusLine,
  MessageHeaders messsageHeaders,
  charstring messageBody optional,
}


"""

import CodecManager


import re

# This map contains a couple of (coder_function, decoder_function)
# indexed by the internal header name/identifier.
# This name is computed this way:
# - take the raw header from the message
# - remove all '-' separator
# - make sure that each 'word' starts with a cap.
# For instance: ContentLength, XSpecificHeader, ...
# Exception: CSeq.
# This name is used to create the record of headers in decoded message,
# while the actual field name on the wire is still kept in its fieldName
# sub-field.
#
# NB: this single identifier/name per header enables to create matching
# templates regardless of the actual header name case on the wire, while
# still having a look to what you actually received.
HeaderBodyCodecs = {}

# If you don't want to use the automatic header name/identifier generation
# explained above, you may want to explicitly provide this identifier,
# based on the received header in lower-case.
KnownHeaderNames = {
#	'cseq': 'CSeq', # when receiving cseq, Cseq, cSeq, CSeq, or whatever, create a record named CSeq
}

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
'Route',
'Via',
'Allow',
'AcceptEncoding',
'Supported',
'Unsupported',
'Require',
'ContentCoding',
'CallInfo',
'AlertInfo',
'Language',
'Accept',
]

def encode_GenericParam(p):
	if p.get('value', None) is not None:
		return "%s=%s" % (p['id'], p['value'])
	else:
		return p['id']
def encode_SemicolonParam_List(p):
	return ';'.join(map(encode_GenericParam, p))
def encode_AmpersandParam_List(p):
	return '&'.join(map(encode_GenericParam, p))
def encode_CommaParam_List(p):
	return ','.join(map(encode_GenericParam, p))

def decode_GenericParam(s):
	try:
		a, b = s.split('=', 1)
		return { 'id': a, 'value': b }
	except:
		return { 'id': s }
def decode_SemicolonParam_List(s):
	return map(decode_GenericParam, s.split(';'))
def decode_AmpersandParam_List(s):
	return map(decode_GenericParam, s.split('&'))
def decode_CommaParam_List(s):
	return map(decode_GenericParam, s.split(','))

def encode_HostPort(p):
	if p.get('port', None):
		return '%s:%s' % (p['host'], p['port'])
	else:
		return p['host']
def decode_HostPort(s):
	t = s.split(':')
	if len(t) == 2:
		return { 'host': t[0], 'port': int(t[1]) }
	else:
		return { 'host': s }

##
# UserInfo
##
def encode_UserInfo(p):
	if p.get('user', None) is not None:
		ret = p['user']
		if p.get('password', None) is not None:
			ret += ':%s' % p['password']
		return ret
	return ''
def decode_UserInfo(s):
	t = s.split(':', 1)
	if len(t) == 2:
		return { 'user': t[0], 'password': t[1] }
	else:
		return { 'user': s }

##
# SipUrl
##
def encode_SipUrl(p):
	ret = p['scheme']
	if 'userInfo' in p:
		userInfo = encode_UserInfo(p.get('userInfo'))
		if userInfo:
			ret += '%s@' % userInfo
	ret += encode_HostPort(p['hostPort'])
	if 'urlParameters' in p and p['urlParameters']:
		ret += ';' + encode_SemicolonParam_List(p['urlParameters'])
	# Headers ??
	return ret

def decode_SipUrl(s):
	p = {}
	t = s.split(':', 1)
	p['scheme'] = '%s:' % t[0]
	tt = t[1].split(';', 1)
	add = tt[0].split('@')
	if len(add) == 1:
		p['hostPort'] = decode_HostPort(add[0])
	else:
		p['userInfo'] = decode_UserInfo(add[0])
		p['hostPort'] = decode_HostPort(add[1])
	if len(tt) > 1:
		p['urlParameters'] = decode_SemicolonParam_List(tt[1])
	return p

##
# Accept header
##
def decode_AcceptBody(s): raise NotImplemented
def encode_AcceptBody(s): raise NotImplemented

##
# Alert-Info header
##
def decode_AlertInfoBody(s): raise NotImplemented
def encode_AlertInfoBody(p): raise NotImplemented

##
# Call-Info header
##
def decode_CallInfoBody(s): raise NotImplemented
def encode_CallInfoBody(p): raise NotImplemented

##
# Challenger header
##
def decode_Challenge(s): raise NotImplemented
def encode_Challenge(p): raise NotImplemented

##
# NameAddr (used in From, To header)
##
def encode_NameAddr(p):
	if "displayName" in p:
		return '"%s" <%s>' % (p['displayName'].encode('utf-8'), encode_SipUrl(p['sipUrl']))
	return encode_SipUrl(p['sipUrl'])
def decode_NameAddr(s):
	url = s
	m = re.match(r'(?P<display>.*)\<(?P<url>.*)\>', s)
	if m:
		url = m.group('url')
		display = m.group('display').strip()
		if display:
			if display[0] == '"':
				display = display[1:-1]
			return { 'displayName': display.decode('utf-8'), 'sipUrl': decode_SipUrl(url) }
	return { 'sipUrl': decode_SipUrl(url) }

def encode_FromTo(p):
	"""
	Similar to NameAddr, but may contain additional ;-parameters in p['parameters'].
	"""
	ret = encode_NameAddr(p)
	if 'parameters' in p:
		if 'displayName' in p:
			ret += ';%s' % encode_SemicolonParam_List(p['parameters'])
		else:
			ret = "<%s>;%s" % (ret, encode_SemicolonParam_List(p['parameters']))
	return ret

def decode_FromTo(s):
	"""
	Similar to NameAddr, but may contain additional ;-parameters in p['parameters'].
	"""
	ret = {}
	m = re.match(r'(?P<display>.*)\<(?P<url>.*)\>(?P<params>.*)', s)
	if m:
		url = m.group('url')
		ret['sipUrl'] = decode_SipUrl(url)
		params = m.group('params').strip()
		if params.startswith(';'):
			params = decode_SemicolonParam_List(params[1:])
			if params:
				ret['parameters'] = params

		display = m.group('display').strip()
		if display:
			if display[0] == '"':
				display = display[1:-1]
			ret['displayName'] = display.decode('utf-8')
	else:
		# sip:something@something;branch=... -> ;branch is not an URI parameter
		# while: <sip:something@something;branch=...>;branch=... will lead to one URI parameter and one FromTo param
		t = s.split(';', 1)
		ret['sipUrl'] = decode_SipUrl(t[0])
		if len(t) > 1:
			if t[1]:
				ret['parameters'] = decode_SemicolonParam_List(t[1])
	return ret


HeaderBodyCodecs['From'] = (encode_FromTo, decode_FromTo)
HeaderBodyCodecs['To'] = (encode_FromTo, decode_FromTo)

##
# ContactAddress
##
def encode_ContactAddress(p):
	ret = "<%s>" % encode_NameAddr(p['addressField'])
	if p.get('parameters', []):
		ret += ";%s" % encode_SemicolonParam_List(p['parameters'])
	return ret

def decode_ContactAddress(s):
	m = re.match(r'\<(?P<address>.+)\>(?P<params>.*)', s)
	if s:
		ret = { 'addressField': decode_NameAddr(m.group('address')) }
		params = m.group('params')
		if len(params) > 1 and params[0] == ';': # contains at least one char after the ;
			ret['parameters'] = decode_SemicolonParam_List(params[1:])
		return ret
	else:
		raise Exception("Invalid Contact Address format: %s" % s)

HeaderBodyCodecs['Contact'] = (encode_ContactAddress, decode_ContactAddress)

##
# Route header
##
def encode_RouteBody(p):
	ret = "<%s>" % encode_NameAddr(p['addressField'])
	if p.get('parameters', []):
		ret += ";%s" % encode_SemicolonParam_List(p['parameters'])
	return ret

def decode_RouteBody(s):
	m = re.match(r'\<(?P<address>.+)\>(?P<params>.*)', s)
	if s:
		ret = { 'nameAddr': decode_NameAddr(m.group('address')) }
		params = m.group('params')
		if len(params) > 1 and params[0] == ';': # contains at least one char after the ;
			ret['parameters'] = decode_SemicolonParam_List(params[1:])
		return ret
	else:
		raise Exception("Invalid Route format: %s" % s)

HeaderBodyCodecs['Route'] = (encode_RouteBody, decode_RouteBody)

##
# Via header
##
def encode_SentProtocol(p):
	return "%s/%s/%s" % (p['protocolName'], p['protocolVersion'], p['transport'])

def decode_SentProtocol(s):
	a, b, c = s.split('/')
	return dict(protocolName = a, protocolVersion = b, transport = c)

def encode_ViaBody(p):
	# SIP/2.0/UDP 172.16.4.238:5060;branch=z9hG4bK8606A188A4651BD550F06BB83B25552C;rport
	ret = "%s %s" % (encode_SentProtocol(p['sentProtocol']), encode_HostPort(p['sentBy']))
	params = p.get('parameters', [])
	if params:
		ret += ";%s" % encode_SemicolonParam_List(params)
	return ret

def decode_ViaBody(s):
	a, b = s.split(' ', 1)
	ret = dict(sentProtocol = decode_SentProtocol(a))
	c = b.split(';', 1)
	ret['sentBy'] = decode_HostPort(c[0])
	if len(c) > 1:
		ret['parameters'] = decode_SemicolonParam_List(c[1])
	return ret

HeaderBodyCodecs['Via'] = (encode_ViaBody, decode_ViaBody)

##
# CSeq header
##
def decode_CSeq(s):
	a, b = s.split(' ')
	seqNumber = int(a.strip())
	method = b.strip()
	return dict(seqNumber = seqNumber, method = method)

def encode_CSeq(p):
	return "%s %s" % (p['seqNumber'], p['method'])

HeaderBodyCodecs['Cseq'] = (encode_CSeq, decode_CSeq)

def generic_header_body_coder(value):
	return unicode(value).encode('utf-8')

def generic_header_body_decoder(value):
	return value.decode('utf-8')

def integer_header_body_coder(value):
	return str(value)

def integer_header_body_decoder(value):
	return int(value)

HeaderBodyCodecs['MaxForwards'] = (integer_header_body_coder, integer_header_body_decoder)
HeaderBodyCodecs['ContentLength'] = (integer_header_body_coder, integer_header_body_decoder)

##
# Request Line
##
def encode_RequestLine(p):
	return "%s %s %s" % (p['method'], encode_SipUrl(p['requestUri']), p['sipVersion'])

def decode_RequestLine(s):
	a, b, c = s.split(' ', 2)
	return dict(method = a.strip(), requestUri = decode_SipUrl(b.strip()), sipVersion = c.strip())

##
# Status Line
##
def encode_StatusLine(p):
	return "%s %s %s" % (p['sipVersion'], p['statusCode'], p['reasonPhrase'])

def decode_StatusLine(s):
	a, b, c = s.split(' ', 2)
	return dict(sipVersion = a.strip(), statusCode = int(b.strip()), reasonPhrase = c.strip())

##
# Messages
##

def fieldNameToName(name):
	n = name.lower()
	# Search compact names
	if n in CompactHeaderNames:
		n = CompactHeaderNames[n]
	# Now, convert a header name to an internal identifier
	# (the one as defined in the TTCN-3 SIP suite, or a dynamically generated one)
	return KnownHeaderNames.get(n, n.replace('-', ' ').title().replace(' ', ''))

def getHeaderBodyCodecs(name):
	"""
	Returns a tuple of functions: (coder, decoder)
	for the header body.
	signatures:
		decoder(string)
		coder(dict, or tuple, or.. dependending on the entity to manage)
	"""
	return HeaderBodyCodecs.get(name, (generic_header_body_coder, generic_header_body_decoder))

def encodeHeader(name, fieldName, value):
	"""
	Actually writes the header.
	"""
	ret = []
	# Look for a header body decoder based on name
	coder, decoder = getHeaderBodyCodecs(name)

	if isinstance(value, list):
		for v in value:
			# Multi values - for now, not configurable. Only one value per line.
			ret.append('%s: %s' % (fieldName, coder(v)))
	else:
		ret.append('%s: %s' % (fieldName, coder(value)))

	return '\r\n'.join(ret)

def decodeHeaderBody(value, name):
	"""
	Decodes a "header body", i.e. a field value,
	for the header whose the internal name/identifier is name.
	"""
	coder, decoder = getHeaderBodyCodecs(name)
	decodedValue = decoder(value)
	return decodedValue

def decodeMessage(s):
	"""
	s is a list of lines after the request/status line.
	Also contains a body.
	"""
	ret = {}
	s = s.split('\r\n')
	firstLine = s[0]
	if firstLine.startswith('SIP/'):
		ret['statusLine'] = decode_StatusLine(firstLine)
	else:
		ret['requestLine'] = decode_RequestLine(firstLine)

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

		decodedValues = map(lambda x: decodeHeaderBody(x, name), encodedValues)

		if len(decodedValues) == 1:
			value = decodedValues[0]
		else:
			value = decodedValues

		if name in headers:
			# Already exists. Already a list ? if not, turns it to a list
			v = headers[name]['fieldValue']
			if not isinstance(v, list):
				headers[name]['fieldValue'] = [v]
			if isinstance(value, list):
				for val in value:
					headers[name]['fieldValue'].append(val)
			else:
				headers[name]['fieldValue'].append(value)
			# In any case, add the raw value as a list
			headers[name]['rawValues'] += encodedValues
		else:
			# First header line - if the header is supposed to be multivalued,
			# creates it as a list, always.
			if name in MultiValuedHeaders:
				headers[name] = { 'fieldName': fieldName, 'fieldValue': isinstance(value, list) and value or [ value ] }
			else:
				headers[name] = { 'fieldName': fieldName, 'fieldValue': value }

			# In any case, add the raw value as a list
			headers[name]['rawValues'] = encodedValues

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
		ret['messageBody'] = body

	ret['messageHeaders'] = headers
	return ret

def encodeMessage(p):
	ret = []
	if 'statusLine' in p:
		ret.append(encode_StatusLine(p['statusLine']))
	elif 'requestLine' in p:
		ret.append(encode_RequestLine(p['requestLine']))
	else:
		raise Exception("Invalid message: not a response or request")
	# Now continue with the headers and body encoding.
	contentLengthWritten = False
	for name, value in p['messageHeaders'].items():
		if name == 'ContentLength':
			contentLengthWritten = True
		fieldName = value['fieldName']
		fieldValue = value['fieldValue']
		ret.append(encodeHeader(name, fieldName, fieldValue))
	if not contentLengthWritten:
		ret.append(encodeHeader('ContentLength', 'Content-Length', len(p.get('messageBody', ''))))

	ret.append('')
	if 'messageBody' in p and p['messageBody']:
		ret.append(p['messageBody'])
	return '\r\n'.join(ret)


##
# The Testerman codec interface to the codec
##

class SipCodec(CodecManager.Codec):
	def encode(self, template):
		return encodeMessage(template)

	def decode(self, data):
		return decodeMessage(data)

if __name__ != '__main__':
	CodecManager.registerCodecClass('sip', SipCodec)

else:


	sets = [

	# NameAddr
	("NameAddr",
	decode_NameAddr, encode_NameAddr, [
	'sip:user@domain',
	'sip:123@domain;user=phone',
	'tel:12345',
	'<sip:user@domain>',
	'<sip:123@domain;user=phone>',
	'<tel:12345>',
	'user1 <sip:user@domain>',
#	'"User One"<sip:123@domain;user=phone>',
	'"User One" <tel:12345>',
	'"Your Name Here" <sip:12232323@127.0.0.1:5060;user=phone>',
	]),
	# ContactAddress
	('ContactAddress',
	decode_ContactAddress, encode_ContactAddress, [
	'<sip:seb@172.16.4.238:57516>',
	'<sip:Username@172.16.4.238:5060;transport=udp>',
	'<sip:seb@172.16.4.238:57516>;param=value',
	]),
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

	for (label, decode_f, encode_f, samples) in sets[2:]:
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


	
