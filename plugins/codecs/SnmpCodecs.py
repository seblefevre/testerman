# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2012 Sebastien Lefevre and other contributors
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
# SNMP v1 codecs.
# To compile Snmpv1Asn: ./py_output.py --explicit asn/RFC1157-SMI.asn > Snmpv1Asn.py
##

import CodecManager

import ber.BerCodec as BerCodec
import ber.Snmpv1Asn as Snmpv1Asn

class Snmpv1Codec(BerCodec.BerCodec):
	"""
	= Identification and Properties =
	
	Codec IDs: `snmp.v1`
	
	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	
	= Overview =
	
	== Decoding ==
	
	...
	
	== Encoding ==
	
	...

	== Availability ==

	All platforms.

	== Dependencies ==

	None.

	== See Also ==
	
	The mapping between ASN.1 and Testerman structures is documented [Asn1ToTesterman here].

	"""
	PDU = Snmpv1Asn.Message

	def getSummary(self, message):
		try:
			# message is a sequence (version, community, data = choice(...)).
			return 'SNMP v%s %s' % (int(message['version'])+1, message['data'][0])
		except:
			return super.getSummary(message)

CodecManager.registerCodecClass('snmp.v1', Snmpv1Codec)



if __name__ == '__main__':
	import binascii

	# A sample SNMP v1 trap, with one OctetString variable in it.
	trap = \
		"303a02010004067075626c6963a42d06052a030405064004c0c1c2c3020106020163430137301530130605330c0d0e0f040a74657374737472696e67"

	getRequest = \
		"302602010004067075626c6963a01902044ccdf1d1020100020100300b300906052a030405060500"

	getNextRequest = \
		"302602010004067075626c6963a11902046a11a75b020100020100300b300906052a030405060500"

	getResponse = \
		"302b02010004067075626c6963a21e020444ffe33e0201020201013010300e06052a03040506040568656c6c6f"

	setRequest = \
		"302b02010004067075626c6963a31e02040a523e7c0201000201003010300e06052a03040506040568656c6c6f"

	print 80*'-'
	print "Codec unit tests"
	print 80*'-'
	samples = [	
		('snmp.v1', trap),
		('snmp.v1', getRequest),
		('snmp.v1', getNextRequest),
		('snmp.v1', setRequest),
		('snmp.v1', getResponse),
	]

	for pdu, s in samples:
		print
		print 80*'-'
		print "Testing: %s" % s
		s = binascii.unhexlify(s)
		(decoded, summary) = CodecManager.decode(pdu, s)
		print "Decoded: %s\nSummary: %s" % (decoded, summary)
		(reencoded, summary) = CodecManager.encode(pdu, decoded)
		print "Reencoded: %s\nSummary: %s" % (binascii.hexlify(reencoded), summary)
		print "Original : %s" % binascii.hexlify(s)
		assert(s == reencoded)
		(redecoded, summary) = CodecManager.decode(pdu, reencoded)
		print "Decoded: %s\nSummary: %s" % (redecoded, summary)
		assert(redecoded == decoded)
