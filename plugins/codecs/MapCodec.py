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
# MAP (2+) Codec
# To compile MapAsn: cd ber && ./py_output.py asn/AMP-All.asn > MapAsn.py
##

import CodecManager

import ber.BerCodec as BerCodec
import ber.MapAsn as MapAsn

# SMS management: SRI and MT Forward
class RoutingInfoForSM_ArgCodec(BerCodec.BerCodec):
	PDU = MapAsn.RoutingInfoForSM_Arg
	def getSummary(self, message): return 'RoutingInfoForSM-Arg'
CodecManager.registerCodecClass('map.RoutingInfoForSM-Arg', RoutingInfoForSM_ArgCodec)

class RoutingInfoForSM_ResCodec(BerCodec.BerCodec):
	PDU = MapAsn.RoutingInfoForSM_Res
	def getSummary(self, message): return 'RoutingInfoForSM-Res'
CodecManager.registerCodecClass('map.RoutingInfoForSM-Res', RoutingInfoForSM_ResCodec)

class MT_ForwardSM_ArgCodec(BerCodec.BerCodec):
	PDU = MapAsn.MT_ForwardSM_Arg
	def getSummary(self, message): return 'MT-ForwardSM-Arg'
CodecManager.registerCodecClass('map.MT-ForwardSM-Arg', MT_ForwardSM_ArgCodec)

class MT_ForwardSM_ResCodec(BerCodec.BerCodec):
	PDU = MapAsn.MT_ForwardSM_Res
	def getSummary(self, message): return 'MT-ForwardSM-Res'
CodecManager.registerCodecClass('map.MT-ForwardSM-Res', MT_ForwardSM_ResCodec)

class MO_ForwardSM_ArgCodec(BerCodec.BerCodec):
	PDU = MapAsn.MO_ForwardSM_Arg
	def getSummary(self, message): return 'MO-ForwardSM-Arg'
CodecManager.registerCodecClass('map.MO-ForwardSM-Arg', MO_ForwardSM_ArgCodec)

class MO_ForwardSM_ResCodec(BerCodec.BerCodec):
	PDU = MapAsn.MO_ForwardSM_Res
	def getSummary(self, message): return 'MO-ForwardSM-Res'
CodecManager.registerCodecClass('map.MO-ForwardSM-Res', MO_ForwardSM_ResCodec)

class DialoguePDUCodec(BerCodec.BerCodec):
	PDU = MapAsn.DialoguePDU
	def getSummary(self, message): return 'DialoguePDU'
CodecManager.registerCodecClass('map.DialoguePDU', DialoguePDUCodec)

if __name__ == '__main__':
	import binascii
	def o(x):
		return binascii.unhexlify(x.replace(' ', ''))
	
	sendRoutingInfoForSMArg = \
	"30158007910026151101008101ff820791261010101010"

	print 80*'-'
	print "MAP (Phase 2+) Codec unit tests"
	print 80*'-'
	samples = [	
		sendRoutingInfoForSMArg,
	]

	for s in samples:
		print
		print 80*'-'
		print "Testing: %s" % s
		s = binascii.unhexlify(s)
		(decoded, summary) = CodecManager.decode('map.RoutingInfoForSM-Arg', s)
		print "Decoded: %s\nSummary: %s" % (decoded, summary)
		(reencoded, summary) = CodecManager.encode('map.RoutingInfoForSM-Arg', decoded)
		print "Reencoded: %s\nSummary: %s" % (binascii.hexlify(reencoded), summary)
		print "Original : %s" % binascii.hexlify(s)
		assert(s == reencoded)
	

	print
	print 80*'-'
	print "Direct encoding testing"
	# Explicit encoding test
	sriSmRes = { 
		'imsi': '\x91\x10\x32\x54',
		'locationInfoWithLMSI': {
			'lmsi': '\x01\x02\x03\x04',
			'networkNode-Number': '\x91\x22\x22\x22\x22\x22',
		}
	}
	print "Encoding sendRoutingInfoForSM Res:"
	encoded, summary = CodecManager.encode('map.RoutingInfoForSM-Res', sriSmRes)
	print binascii.hexlify(encoded)
	decoded, summary = CodecManager.decode('map.RoutingInfoForSM-Res', encoded)
	print "Redecoded sendRoutingInfoForSM Res:"
	print repr(decoded)
	assert(decoded == sriSmRes)
	
