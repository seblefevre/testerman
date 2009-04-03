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
# GSM 03.40 / TS 23 040-650 SMS TPDU codecs
#
##

import CodecManager

from Telephony import string2tbcd, tbcd2string

class Doc:
	"""
	= Identification and Properties =
	
	Codec IDs: `sms.tpdu.*`
	 * `sms.tpdu.SMS-DELIVER`
	 * `sms.tpdu.SMS-DELIVER-REPORT`
	 * `sms.tpdu.SMS-SUBMIT` (not yet implemented)
	 * `sms.tpdu.SMS-SUBMIT-REPORT` (not yet implemented)
	 * `sms.tpdu.SMS-STATUS-REPORT` (not yet implemented)
	 * `sms.tpdu.SMS-COMMAND` (not yet implemented)
	
	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	
	= Overview =

	This collection of codecs
	encode/decode SM-TL (Short Message Transfer Layer) messages
	as defined in GSM 03.40 / TS 23 040-650 (Short Message Service TPDU).
	
	The TP-User-Data is not encoded or decoded explicitly, but transmitted transparently
	as an octetstring.[[BR]]
	As a consequence, the user is responsible for encoding a consistent message
	(correct Data-Coding-Scheme and User-Data-Length in accordance with the sent User-Data).
	
	== Decoding ==
	
	...
	
	== Encoding ==
	
	...

	== Availability ==

	All platforms.

	== Dependencies ==

	None.

	== See Also ==

	= TTCN-3 Types Equivalence =
	
	These codecs decode to/encode from the Testerman structures whose the TTCN-3 equivalent
	are types:
	 * `SmsDeliver` for codec `sms.tpdu.SMS-DELIVER`
	 * `SmsDeliverReport` for codec `sms.tpdu.SMS-DELIVER`
	 * `SmsSubmit` for codec `sms.tpdu.SMS-SUBMIT`
	 * `SmsSubmitReport` for codec `sms.tpdu.SMS-SUBMIT-REPORT`
	 * `SmsStatusReport` for codec `sms.tpdu.SMS-STATUS-REPORT`
	 * `SmsCommandReport` for codec `sms.tpdu.SMS-COMMAND`
	 
	{{{
	type record Address
	{
		enum { unknown, international, national,
		 networkSpecific, subscriber, alphanumeric,
		 abbreviated, reservedForExtension } typeOfNumber,
		enum { unknown, isdn, data, telex, serviceCentreSpecific,
		 serviceCentreSpecific6, national, private, ermes,
		 reserved} numberingPlanIdentification,
		charstring digits
	}
	
	type record Timestamp
	{
		integer (1..99) year,
		integer (1..12) month,
		integer (1..31) day,
		integer (0..23) hour,
		integer (0..59) minute,
		integer (0..59) second,
		integer (-48..48) timezone, // in quarters of an hour
	}
	
	type record SmsDeliver
	{
		boolean TP-More-Messages-to-Send
		boolean TP-Reply-Path
		boolean TP-User-Data-Header-Indicator optional, // default: false
		boolean TP-Status-Report-Indicaton optional, // default: false
		Address TP-Originating-Address,
		integer (0..255) TP-Protocol-Identifier,
		integer (0..255) TP-Data-Coding-Scheme,
		Timestamp TP-Service-Centre-Time-Stamp,
		// this is the application-level length to TP-UD, 
		// not the length of the encoded octetstring
		// When not provided, defaulted to 0
		integer TP-User-Data-Length optional, 
		octetstring TP-User-Data optional,
	}
	
	type record SmsDeliverReport
	{
		boolean TP-User-Data-Header-Indication optional,
		integer TP-Failure-Cause optional, // mandatory in SMS-DELIVER-REPORT for RP-ERROR
		boolean TP-Parameter-Indicator,
		integer (0..255) TP-Protocol-Identifier optional,
		integer (0..255) TP-Data-Coding-Scheme optional,
		// When not provided, defaulted to 0
		integer TP-User-Data-Length optional,
		octetstring TP-User-Data optional
	}
	
	type record SmsSubmit
	{
		boolean TP-Reject-Duplicates,
		enum { notPresent, absolute, enhanced, relative } TP-Validity-Period-Format,
		boolean TP-Reply-Path,
		boolean TP-User-Data-Header-Indicator optional,
		boolean TP-Status-Report-Request optional,
		integer TP-Message-Reference,
		Address TP-Destination-Address,
		integer (0..255) TP-Protocol-Identifier,
		integer (0..255) TP-Data-Coding-Scheme,
		union { Timestamp absolute, integer relative, 
		  octetstring(7) enhanced } TP-Validity-Period optional,
		integer TP-User-Data-Length,
		octetstring TP-User-Data optional,
	}
	
	type record SmsSubmitReport
	{
		boolean TP-User-Data-Header-Indication optional,
		integer (0..255) TP-Failure-Cause optional, // mandatory in SMS-SUBMIT-REPORT for RP-ACK
		boolean TP-Parameter-Indicator,
		Timestamp TP-Service-Centre-Time-Stamp,
		integer (0..255) TP-Protocol-Identifier optional,
		integer (0..255) TP-Data-Coding-Scheme optional,
		integer TP-User-Data-Length optional,
		octetstring TP-User-Data optional
	}
	
	type record SmsStatusReport
	{
		boolean TP-User-Data-Header-Indicaton optional,
		boolean TP-More-Messages-to-Send,
		integer (0..1) TP-Status-Report-Qualifier, // 0: result to a SMS-SUBMIT, 1: result to a SMS-COMMAND
		integer TP-Message-Reference,
		Address TP-Recipient-Address,
		Timestamp TP-Service-Centre-Time-Stamp,
		Timestamp TP-Discharge-Time
		integer (0..255) TP-Status,
		// no TP-Parameter-Indicator: automatically computed/used
		integer (0..255) TP-Protocol-Identifier optional,
		integer (0..255) TP-Data-Coding-Scheme optional,
		integer TP-User-Data-Length optional,
		octetstring TP-User-Data optional
	}
	
	type record SmsCommand
	{
		boolean TP-User-Data-Header-Indication optional,
		boolean TP-Status-Report-Request optional,
		integer (0..255) TP-Message-Reference,
		integer (0..255) TP-Protocol-Identifier,
		integer (0..255) TP-Command-Type,
		integer (0..255) TP-Message-Number,
		Address TP-Destination-Adress,
		integer TP-Command-Data-Length,
		octetstring TP-Command-Data optional
	}	
	}}}
	"""


"""
	Implementation notes:
	TP-Message-Type-Indicator: coded according to the selected union arm.
	So, not present in the record.
	Values:
	sms-deliver: 0 (SC -> MS)
	sms-deliver-report: 0 ... (MS -> SC)
	sms-status-report: 2 (SC -> MS)
	sms-command: 2... (MS -> SC)
	sms-submit: 1 (MS -> SC)
	sms-submit-report (SC -> MS)
	reserved: 3
	
	so a choice is not really possible...
	
	TP-More-Messages-to-Send: boolean
	
	TP-Validity-Period-Format: default notPresent(0),
	possible other values relative(2), enhanced(1), absolute(3)
	
	TP-Status-Report-Indication: boolean
	
	TP-Status-Report-Request: boolean
	
	TP-Message-Reference: integer (0..255)
	
	
	TP-Status: integer (0..255)
	
	TP-User-Data-Length: implicitly managed by the codec for the TP-User-Data.
	
	TP-Reply-Path: boolean
	
	TP-Message-Number: integer (0..255)
	
	TP-Command-Type: integer (0..255)
"""		

# get: operate on a ord or an octetstring
# set: operate on a ord (when applicable)
def getMessageTypeIndicator(byte):
	return (byte & 0x03)

def setMessageTypeIndicator(byte, indicator):
	return (byte | (indicator & 0x03))

def getMoreMessagesToSend(byte):
	# bit 2
	if (byte & 0x04):
		return True
	else:
		return False

def setMoreMessagesToSend(byte, val):
	if val:
		return byte | 0x04
 	else:
		return byte & ~0x04

def getStatusReportIndication(byte):
	# bit 5
	if (byte & 0x20):
		return True
	else:
		return False

def setStatusReportIndication(byte, val):
	if val:
		return byte | 0x20
	else:
		return byte & ~0x20

def getUserDataHeaderIndicator(byte):
	# bit 6
	if (byte & 0x40):
		return True
	else:
		return False

def setUserDataHeaderIndicator(byte, val):
	if val:
		return byte | 0x40
 	else:
		return byte & ~0x40

def getReplyPath(byte):
	if (byte & 0x80):
		return True
	else:
		return False

def setReplyPath(byte, val):
	if val:
		return byte | 0x80
	else:
		return byte & ~0x80

TypeOfNumber = {
'unknown': 0,
'international': 1,
'national': 2,
'networkSpecific': 3,
'subscriber': 4,
'alphanumeric': 5,
'abbreviated': 6,
'reservedForExtension': 7
}
		 
NumberingPlanIndication = {
'unknown': 0,
'isdn': 1,
'data': 3,
'telex': 4,
'serviceCentreSpecific5': 5,
'serviceCentreSpecific6': 6,
'national': 8,
'private': 9,
'ermes': 10,
'reserved': 15,
}

def decodeAddress(data):
	"""
	Reads an address from a octetstring that 
	starts with the number of digits, then the ton/npi byte, followed by n TBCD digits
	"""
	ret = {}
	l = ord(data[0]) # number of useful semi-octet in digits.
	ibyte = ord(data[1])
	npi = ibyte & 0x0f
	ton = (ibyte >> 4) & 0x07
	for k, v in TypeOfNumber.items():
		if v == ton:
			ton = k
	# else leave the integer value
	ret['typeOfNumber'] = ton
	for k, v in NumberingPlanIndication.items():
		if v == npi:
			npi = k
	# else leave the integer value
	ret['numberingPlanIndication'] = npi

	ret['digits'] = tbcd2string(data[2:])[:l]
	return ret

def encodeAddress(template):
	"""
	encode the dict template as an Address.
	The result is an octetstring including the length byte.
	"""
	ton = template['typeOfNumber']
	if isinstance(ton, basestring):
		ton = TypeOfNumber.get(ton, None)
		if ton is None:
			raise Exception('Invalid typeOfNumber enum')
	elif isinstance(ton, int):
		if ton < 0 or ton > 7:
			raise Exception('Invalid typeOfNumber enum value')
	else:
		raise Exception('Invalid typeOfNumber')

	npi = template['numberingPlanIndication']
	if isinstance(npi, basestring):
		npi = NumberingPlanIndication.get(npi, None)
		if npi is None:
			raise Exception('Invalid numberingPlanIndication enum')
	elif isinstance(npi, int):
		if npi < 0 or npi > 15:
			raise Exception('Invalid numberingPlanIndication enum value')
	else:
		raise Exception('Invalid numberingPlanIndicator')

	ibyte = chr(0x80 | ((ton & 0x07) << 4) | (npi & 0x0f))

	digits = string2tbcd(template['digits'], 0x0f)
	return (chr(len(template['digits'])) + ibyte + digits)

def tbcd2int(byte):
	# The first bit is used to sign the result
	b = ((byte & 0x70) >> 4) + 10 * (byte & 0x0f)
	if byte & 0x80:
		return -b
	else:
		return b

def tbcd2uint(byte):
	return ((byte & 0xf0) >> 4) + 10 * (byte & 0x0f)

def uint2tbcd(i):
	a, b = divmod(i, 10)
	return (a & 0x0f) | ((b & 0x0f) << 4)

def int2tbcd(i):
	a, b = divmod(i, 10)
	r = (a & 0x07) | ((b & 0x0f) << 4)
	if i < 0:
		return r | 0x80
	else:
		return r

def decodeTimestamp(data):
	"""
	Decode a YYMMDDhhmmsstz timestamp to a dict.
	"""
	# Everything is coded in tbcd.
	ret = {}
	ret['year'] = tbcd2uint(ord(data[0]))
	ret['month'] = tbcd2uint(ord(data[1]))
	ret['day'] = tbcd2uint(ord(data[2]))
	ret['hour'] = tbcd2uint(ord(data[3]))
	ret['minute'] = tbcd2uint(ord(data[4]))
	ret['second'] = tbcd2uint(ord(data[5]))
	# tz: in quarters of an hour, signed
	ret['timezone'] = tbcd2int(ord(data[6]))
	return ret

def encodeTimestamp(ts):
	ret = []
	ret.append(chr(uint2tbcd(ts['year'])))
	ret.append(chr(uint2tbcd(ts['month'])))
	ret.append(chr(uint2tbcd(ts['day'])))
	ret.append(chr(uint2tbcd(ts['hour'])))
	ret.append(chr(uint2tbcd(ts['minute'])))
	ret.append(chr(uint2tbcd(ts['second'])))
	ret.append(chr(int2tbcd(ts['timezone'])))
	return ''.join(ret)

def decodeSmsDeliver(data):
	"""
	Decodes a SMS-DELIVER message.
	Verifies the TP-MPI.
	
	@type  data: buffer/string
	@param data: the data to decode
	"""
	ret = {}
	try:
		offset = 0
		# 1st octet: TP-MTI, TP-MMS, TP-RP, TP-UDHI, TP-SRI
		c = ord(data[offset])
		mti = getMessageTypeIndicator(c)
		if mti != 0:
			raise Exception("Invalid TP-Message-Type-Indicator: expected 0 (SMS-DELIVER), got %s" % mti)
		ret['TP-More-Messages-to-Send'] = getMoreMessagesToSend(c)
		ret['TP-Reply-Path'] = getReplyPath(c)
		ret['TP-User-Data-Header-Indicator'] = getUserDataHeaderIndicator(c)
		ret['TP-Status-Report-Indication'] = getStatusReportIndication(c)
		# the first byte of the address contains the number of useful semi-octet.
		# We should add the byte coding this len and the subsequent npi/ton byte
		offset += 1
		addrlen = ((ord(data[1]) + 1) / 2) + 1 + 1 
		ret['TP-Originating-Address'] = decodeAddress(data[offset:offset+addrlen])
		offset += addrlen
		ret['TP-Protocol-Identifier'] = ord(data[offset])
		offset += 1
		ret['TP-Data-Coding-Scheme'] = ord(data[offset])
		offset += 1
		ret['TP-Service-Centre-Time-Stamp'] = decodeTimestamp(data[offset:offset+7])
		offset += 7
		ret['TP-User-Data-Length'] = ord(data[offset])
		offset += 1
		ret['TP-User-Data'] = data[offset:]
		return ret
	except IndexError:
		raise Exception('Invalid SMS-DELIVER message: too short')

def encodeSmsDeliver(template):
	ret = []
	c = 0x00
	c = setMessageTypeIndicator(c, 0) # SMS-DELIVER
	c = setMoreMessagesToSend(c, template.get('TP-More-Messages-to-Send', False))
	c = setReplyPath(c, template.get('TP-Reply-Path', False))
	c = setUserDataHeaderIndicator(c, template.get('TP-User-Data-Header-Indicator', False))
	c = setStatusReportIndication(c, template.get('TP-Status-Report-Indication', False))
	ret.append(chr(c))
	ret.append(encodeAddress(template['TP-Originating-Address']))
	ret.append(chr(template['TP-Protocol-Identifier']))
	ret.append(chr(template['TP-Data-Coding-Scheme']))
	ret.append(encodeTimestamp(template['TP-Service-Centre-Time-Stamp']))
	l = template.get('TP-User-Data-Length', 0)
	ret.append(chr(l))
	ud = template.get('TP-User-Data', None)
	if ud:
		ret.append(template['TP-User-Data'])
	
	return ''.join(ret)

##
# SMS-DELIVER
##		
class SmsTpduSmsDeliverCodec(CodecManager.Codec):
	def __init__(self):
		CodecManager.Codec.__init__(self)

	def encode(self, template):
		return (encodeSmsDeliver(template), 'SMS-DELIVER')

	def decode(self, data):
		return (decodeSmsDeliver(data), 'SMS-DELIVER')

CodecManager.registerCodecClass('sms.tpdu.SMS-DELIVER', SmsTpduSmsDeliverCodec)


if __name__ == '__main__':
	import binascii
	def o(x):
		return binascii.unhexlify(x.replace(' ', ''))

	def oo(x):
		return binascii.hexlify(x)
	
	tpduSmsDeliver = "04039177f70010901091215571406fd3373b2c4fcf41311828168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1582c168bc562b1584c36a3d500"
	
	print 80*'-'
	print "SMS TPDU SM-TL Codec unit tests"
	print 80*'-'
	samples = [	
		('sms.tpdu.SMS-DELIVER', tpduSmsDeliver),
	]

	for pdu, s in samples:
		print
		print 80*'-'
		print "Testing: %s" % s
		s = o(s)
		(decoded, summary) = CodecManager.decode(pdu, s)
		print "Decoded: %s\nSummary: %s" % (decoded, summary)
		(reencoded, summary) = CodecManager.encode(pdu, decoded)
		print "Reencoded: %s\nSummary: %s" % (oo(reencoded), summary)
		print "Original : %s" % oo(s)
		assert(s == reencoded)
