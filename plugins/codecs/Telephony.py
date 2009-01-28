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


##
# Telephony BCD
##

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
		return string2tbcd(template, self['filler'])
	
	def decode(self, data):
		return tbcd2string(data)

CodecManager.registerCodecClass('tbcd', TbcdCodec)



if __name__ == "__main__":
	import binascii
	
	print "TBCD unit tests"
	print 80*'-'
	samples = [
		('\x21\xf3', "123"),
		('\x21\x43', "1234"),
	]

	for e, d in samples:
		encoded = CodecManager.encode('tbcd', d)
		print "encoded: %s (%s)" % (repr(encoded), binascii.hexlify(encoded))
		assert(encoded == e)
		decoded = CodecManager.decode('tbcd', e)
		print "decoded: %s" % repr(decoded)
		assert(decoded == d)

