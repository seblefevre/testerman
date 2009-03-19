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
# TCAP (itu-t) Codec
# To compile TcapAsn: ./py_output.py asn/tcap.asn > TcapAsn.py
##

import CodecManager

import ber.BerCodec as BerCodec
import ber.MapAsn as MapAsn

# SMS management: SRI and MT Forward
class RoutingInfoForSM_ArgCodec(BerCodec.BerCodec):
	PDU = MapAsn.RoutingInfoForSM_Arg
CodecManager.registerCodecClass('map.RoutingInfoForSM_Arg', RoutingInfoForSM_ArgCodec)

class RoutingInfoForSM_ResCodec(BerCodec.BerCodec):
	PDU = MapAsn.RoutingInfoForSM_Res
CodecManager.registerCodecClass('map.RoutingInfoForSM_Res', RoutingInfoForSM_ResCodec)

class MT_ForwardSM_ResCodec(BerCodec.BerCodec):
	PDU = MapAsn.MT_ForwardSM_Res
CodecManager.registerCodecClass('map.MT_ForwardSM_Res', MT_ForwardSM_ResCodec)

class MT_ForwardSM_ArgCodec(BerCodec.BerCodec):
	PDU = MapAsn.MT_ForwardSM_Arg
CodecManager.registerCodecClass('map.MT_ForwardSM_Arg', MT_ForwardSM_ArgCodec)


if __name__ == '__main__':
	import binascii
	
	sendRoutingInfoForSMArg = \
	"30158007910026151101008101ff820791261010101010"

	print 80*'-'
	print "MAP (Phase 2) Codec unit tests"
	print 80*'-'
	samples = [	
		sendRoutingInfoForSMArg,
	]

	for s in samples:
		print
		print 80*'-'
		print "Testing: %s" % s
		s = binascii.unhexlify(s)
		(decoded, summary) = CodecManager.decode('map.RoutingInfoForSM_Arg', s)
		print "Decoded: %s\nSummary: %s" % (decoded, summary)
		(reencoded, summary) = CodecManager.encode('map.RoutingInfoForSM_Arg', decoded)
		print "Reencoded: %s\nSummary: %s" % (binascii.hexlify(reencoded), summary)
		print "Original : %s" % binascii.hexlify(s)
#		assert(s == reencoded)
	
