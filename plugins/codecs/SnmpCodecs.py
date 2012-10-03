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
import ber.Snmpv2cAsn as Snmpv2cAsn

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
			return 'SNMP v1 %s' % (message['data'][0])
		except:
			return super.getSummary(message)

CodecManager.registerCodecClass('snmp.v1', Snmpv1Codec)


class Snmpv2cCodec(BerCodec.BerCodec):
	"""
	= Identification and Properties =
	
	Codec IDs: `snmp.v2c`
	
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
	PDU = Snmpv2cAsn.Message

	def getSummary(self, message):
		try:
			# message is a sequence (version, community, data = choice(...)).
			return 'SNMP v2c %s' % (message['data'][0])
		except:
			return super.getSummary(message)

CodecManager.registerCodecClass('snmp.v2c', Snmpv2cCodec)


if __name__ == '__main__':
	import binascii

	# A sample SNMP v1 trap, with one OctetString variable in it.
	trap1 = \
		"303a02010004067075626c6963a42d06052a030405064004c0c1c2c3020106020163430137301530130605330c0d0e0f040a74657374737472696e67"

	getRequest1 = \
		"302602010004067075626c6963a01902044ccdf1d1020100020100300b300906052a030405060500"

	getNextRequest1 = \
		"302602010004067075626c6963a11902046a11a75b020100020100300b300906052a030405060500"

	getResponse1 = \
		"302b02010004067075626c6963a21e020444ffe33e0201020201013010300e06052a03040506040568656c6c6f"

	setRequest1 = \
		"302b02010004067075626c6963a31e02040a523e7c0201000201003010300e06052a03040506040568656c6c6f"


	# A sample SNMP v2c trap, with one OctetString variable in it.
	trap2c = \
		"305902010104067075626c6963a74c020406307627020100020100303e300f06082b0601020101030043030e87bf3013060a2b06010603010104010006052a03040506301606092b060106030101050004094a7573742068657265"

	getRequest2c = \
		"302602010104067075626c6963a0190204031cd52c020100020100300b300906052a030405060500"

	getNextRequest2c = \
		"302602010104067075626c6963a11902047c32fce3020100020100300b300906052a030405060500"

	getResponse2c = \
		"307c02010104067075626c6963a26f02047c32fce30201000201003061305f06082b0601020101010004534c696e7578206c617572656c696e6520332e322e302d32342d67656e65726963202333372d5562756e747520534d5020576564204170722032352030383a34333a3232205554432032303132207838365f3634"

	setRequest2c = \
		"302b02010104067075626c6963a31e0204732d84ce0201000201003010300e06052a03040506040568656c6c6f"

	getResponse2cNoSuchObject = \
		"302602010104067075626c6963a2190204031cd52c020100020100300b300906052a030405068000"

	print 80*'-'
	print "Codec unit tests"
	print 80*'-'
	samples = [	
		('snmp.v1', trap1),
		('snmp.v1', getRequest1),
		('snmp.v1', getNextRequest1),
		('snmp.v1', setRequest1),
		('snmp.v1', getResponse1),
		('snmp.v2c', trap2c),
		('snmp.v2c', getRequest2c),
		('snmp.v2c', getNextRequest2c),
		('snmp.v2c', setRequest2c),
		('snmp.v2c', getResponse2c),
		('snmp.v2c', getResponse2cNoSuchObject),
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
