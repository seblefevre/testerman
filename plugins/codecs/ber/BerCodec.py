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
# BER codec stub.
#
# Enables to create BER-based codec once
# the corresponding protocol ASN.1 has been compiled.
#
##

import CodecManager

import BerAdapter
import asn1

class BerCodec(CodecManager.Codec):
	"""
	Just subclass this codec to create your own BER-based
	codec,
	and set the 'pdu' member class to the PDU that
	should be decoded to/encoded from.
	
	You may also reimplement getSummary if
	you have more accurate message summaries to provide.
	"""
	PDU = None
	
	def encode(self, template):
		summary = self.getSummary(template)
		e = asn1.encode(self.PDU, BerAdapter.fromTesterman(template))
		return (e, summary)
	
	def decode(self, data):
		d = BerAdapter.toTesterman(asn1.decode(self.PDU, data))	
		summary = self.getSummary(d)
		return (d, summary)
	
	def getSummary(self, message):
		"""
		You may reimplement this function to get
		a more accurate summary according to the userland PDU.
		@type  message: Testerman userland message
		@param message: decoded message corresponding to your PDU
		"""
		return str(self.PDU.__class__)

"""
# Example:

# TCAP Codec
# To compile TcapAsn: ./py_output.py asn/tcap.asn > TcapAsn.py


import CodecManager

import ber.BerCodec as BerCodec
import ber.TcapAsn as TcapAsn

class TcapCodec(BerCodec.BerCodec):
	PDU = TcapAsn.TCMessage

	def getSummary(self, message):
		try:
			# message is expected to be a choice (begin/end/continue...)
			return 'TCAP %s' % message[0]
		except:
			return super.getSummary(message)

CodecManager.registerCodecClass('tcap', TcapCodec)
"""
