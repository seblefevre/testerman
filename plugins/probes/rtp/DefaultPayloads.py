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
# Some default payloads for the RTP probe.
#
##

import binascii

import Tone

# Some sample sounds to use as default data source to stream

# For G711 alaw (a "random" tone)
G711A = 512*(''.join(Tone.generateTone(8000, 400)))


# For G711 ulaw (a "random" tone)
G711U = 512*(''.join(Tone.generateTone(8000, 200)))

# Default, for all other codecs
DEFAULT = 2048*'\x01'


PayloadMap = {
0: G711U, 
8: G711A,
} 

def getDefaultPayload(payloadType = None):
	"""
	Returns some default payload according to the payload type.
	
	@type  payloadType: integer
	@param payloadType: payload type
	
	@rtype: string (buffer)
	@returns: a default payload for the payload type.
	"""
	return PayloadMap.get(payloadType, DEFAULT)


