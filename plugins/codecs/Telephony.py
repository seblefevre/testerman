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
# Several simple codecs used in telephony systems.
#
##

import CodecManager


###############################################################################
# Telephony BCD
###############################################################################

def tbcd2string(tbcd):
	"""
	Returns an ascii string corresponding to telephony bcd buffer.
	
	Example: "\x21\xf3" -> "123"
	"""
	# Reads demi-byte - automatically stops when we found a non-digit
	digits = []
	for c in tbcd:
		d = ord(c) & 0x0f
		if d > 9:
			break
		digits.append(str(d))
		d = (ord(c) & 0xf0) >> 4
		if d > 9:
			break
		digits.append(str(d))
	return ''.join(digits)


def string2tbcd(digits, filler = 0x0f):
	"""
	Returns a buffer corresponding to the Telephoby BCD representation
	of digits, which is digits in a string.
	
	Example: "123" -> "\x21\xf3"
	"""
	bytes = []
	l = len(digits)
	i = 0
	while i < l:
		b = (ord(digits[i]) - ord('0')) & 0x0f
		i += 1
		if i == l:
			b |= filler << 4
		else:
			b |= ((ord(digits[i]) - ord('0')) & 0x0f) << 4
		i += 1
		bytes.append(b)	

	return ''.join(map(chr, bytes))


###############################################################################
# 7-bit Packet (3GPP TS 23.038, ...)
###############################################################################

def encode_7bitpacked(s):
	"""
	Encodes a 7-bit string (already in the correct alphabet)
	to a 7-bit packed buffer.
	
	Used for 7-bit SMS packing, USSD packing, CBS packing...
	
	For instance:

	One character in one octet:
	the bits numbers in the output are:
	7  6  5  4  3  2  1  0
	0  1a 1b 1c 1d 1e 1f 1g
	
	Two characters in two octets:
	7  6  5  4  3  2  1  0
	2g 1a 1b 1c 1d 1e 1f 1g
	0  0  2a 2b 2c 2d 2e 2f
	
	etc.
	 
	"""
	# available bits in the previous encoded byte: ranges from 0
	# (fully packed) to 7 (we will be able to inject a complete new 7-bit character)
	available_bits_in_previous_byte = 0
	ret = []
	for c in s:
		c = ord(c) & 0x7f # limit to 7 bit, left-pad with bit 0
		# some bits to inject in the previous byte ?
		if available_bits_in_previous_byte:
			ret[-1] = ret[-1] | (c << (8-available_bits_in_previous_byte) ) & 0xff

		if available_bits_in_previous_byte < 7:
			# and inject the others in the current byte if it was not enough
			ret.append(c >> available_bits_in_previous_byte & 0x7f)
			available_bits_in_previous_byte += 1
		else:
			# was 7. We packed the entire character in the previous byte,
			# nothing to add.
			available_bits_in_previous_byte = 0
	
	return ''.join(map(chr, ret))

def decode_7bitpacked(s):
	"""
	s is a 7-bit packed string.
	
	Decodes it to 8-bit characters.
	"""
	# nb of bits participating to the current caracter encoding
	# in the previous encoded byte.
	available_bits_in_previous_byte = 0
	ret = []
	i = 0
	while i < len(s):
		c = ord(s[i])
		lsb = 0x00 # least significant bits, from the previous byte
		if available_bits_in_previous_byte:
			# Let's extract the bits from the previous byte in s
			lsb = ((ord(s[i-1]) >> (8-available_bits_in_previous_byte)) & 0x7f)

		if available_bits_in_previous_byte < 7:
			# We have some additional bits in the current byte
			# (7-available_bits_in_previous_byte bits exactly)
			ret.append( ((c << available_bits_in_previous_byte) | lsb) & 0x7f)
			available_bits_in_previous_byte += 1
			i += 1 # next coding byte
		else:
			# No more coding bits in the current byte
			ret.append(lsb)
			available_bits_in_previous_byte = 0
			
	return ''.join(map(chr, ret))


###############################################################################
# Codecs
###############################################################################

class TbcdCodec(CodecManager.Codec):
	"""
	Converts a template:
	type charstring TbcdTemplate;
	
	Limitation: won't decode a TBCD correctly if a 0x00 filler is used.
	"""
	def __init__(self):
		CodecManager.Codec.__init__(self)
		self.setDefaultProperty('filler', 0x0f) # Usually 0x0f or 0x00
		
	def encode(self, template):
		"""
		Template is a string of human readable digits
		"""
		return (string2tbcd(template, self['filler']), template)
	
	def decode(self, data):
		ret = tbcd2string(data)
		return (ret, ret)

CodecManager.registerCodecClass('tbcd', TbcdCodec)


###############################################################################
# AddressString as used in GSM: 1 byte for NOA/NPI, then digits as TBCD strings
# cf GSM 09.02, AddressString ASN.1 definition.
###############################################################################

NatureOfAddresses = {
'unknown': 0,
'international': 1,
'national': 2,
'networkSpecific': 3,
'subscriber': 4,
'reserved': 5,
'abbreviated': 6,
'reservedForExtension': 7,
}

NumberingPlanIndicators = {
'unknown': 0,
'isdn': 1,
'data': 3,
'telex': 4,
'lmnp': 6,
'national': 8,
'private': 9,
'reserved': 15,
}

class AddressStringCodec(CodecManager.Codec):
	"""
	Converts a template:
	type record AddressStringTemplate
	{
		charstring digits,
		enum natureOfAddress optional, // defaulted to 'unknown'
		charstring numberingPlanIndicator optional, // defaulted to 'unknown'
	}
	
	natureOfAddress is a enum:
	unknown, international, national,
	networkSpecific, subscriber, reserved,
	abbreviated, reservedForExtension
	
	numberingPlanIndicator is a enum:
	unknown
	isdn
	data
	telex
	lmnp
	national
	private
	reserved
	
	Limitation: won't decode a TBCD correctly if a 0x00 filler is used.
	"""
	def __init__(self):
		CodecManager.Codec.__init__(self)
		self.setDefaultProperty('filler', 0x0f) # Usually 0x0f or 0x00
		
	def encode(self, template):
		noa = template['natureOfAddress']
		if isinstance(noa, basestring):
			noa = NatureOfAddresses.get(noa, None)
			if noa is None:
				raise Exception('Invalid natureOfAddress enum')
		elif isinstance(noa, int):
			if noa < 0 or noa > 7:
				raise Exception('Invalid natureOfAddress enum value')
		else:
			raise Exception('Invalid natureOfAddress')
	
		npi = template['numberingPlanIndicator']
		if isinstance(npi, basestring):
			npi = NumberingPlanIndicators.get(npi, None)
			if npi is None:
				raise Exception('Invalid numberingPlanIndicator enum')
		elif isinstance(npi, int):
			if npi < 0 or npi > 15:
				raise Exception('Invalid numberingPlanIndicator enum value')
		else:
			raise Exception('Invalid numberingPlanIndicator')
		
		
		ibyte = chr(0x80 | ((noa & 0x07) << 4) | (npi & 0x0f))
		
		digits = string2tbcd(template['digits'], self['filler'])
		return (ibyte + digits, template['digits'])
	
	def decode(self, data):
		ret = {}
		ibyte = ord(data[0])
		npi = ibyte & 0x0f
		noa = (ibyte >> 4) & 0x07
		for k, v in NatureOfAddresses.items():
			if v == noa:
				noa = k
		# else leave the integer value
		ret['natureOfAddress'] = noa
		for k, v in NumberingPlanIndicators.items():
			if v == npi:
				npi = k
		# else leave the integer value
		ret['numberingPlanIndicator'] = npi
	
		ret['digits'] = tbcd2string(data[1:])
		return (ret, ret['digits'])

CodecManager.registerCodecClass('gsm.AddressString', AddressStringCodec)


if __name__ == "__main__":
	import binascii

	def o(x):
		return binascii.unhexlify(x.replace(' ', ''))
	def oo(x):
		return binascii.hexlify(x)
	
	print 80*'-'
	print "TBCD Codec unit tests"
	print 80*'-'
	samples = [
		('\x21\xf3', "123"),
		('\x21\x43', "1234"),
	]

	for e, d in samples:
		print
		print 80*'-'
		(encoded, _) = CodecManager.encode('tbcd', d)
		print "encoded: %s (%s)" % (repr(encoded), oo(encoded))
		assert(encoded == e)
		(decoded, _) = CodecManager.decode('tbcd', e)
		print "decoded: %s" % repr(decoded)
		assert(decoded == d)

	print
	print 80*'-'
	print "GSM AddressString Codec unit tests"
	print 80*'-'
	samples = [
		('\x80\x21\xf3', { 'digits': "123", 'numberingPlanIndicator': 'unknown', 'natureOfAddress': 'unknown' }),
		('\x91\x21\x43', { 'digits': "1234", 'numberingPlanIndicator': 'isdn', 'natureOfAddress': 'international' }),
	]

	for e, d in samples:
		print
		print 80*'-'
		(encoded, _) = CodecManager.encode('gsm.AddressString', d)
		print "encoded: %s (%s)" % (repr(encoded), oo(encoded))
		assert(encoded == e)
		(decoded, _) = CodecManager.decode('gsm.AddressString', e)
		print "decoded: %s" % repr(decoded)
		assert(decoded == d)


	print
	print 80*'-'
	print "7-bit packed Codec unit tests"
	print 80*'-'
	tests = [
		('hellohello', o("e8329bfd4697d9ec37")),
	]
	
	for d, c in tests:
		print "Testing '%s':" % d
		e = encode_7bitpacked('hellohello')
		print "Encoded:  %s" % oo(e)
		print "Expected: %s" % oo(c)
		assert(e == c)
		rd = decode_7bitpacked(c)
		print "Decoded:  %s" % rd
		print "Expected: %s" % d
		assert(d == rd)
