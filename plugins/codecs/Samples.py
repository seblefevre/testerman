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
# Sample codecs
##

import CodecManager

import pickle
import base64
import json

class PickleCodec(CodecManager.Codec):
	def encode(self, template):
		return (pickle.dumps(template), 'pickle data')
	
	def decode(self, data):
		return (pickle.loads(data), None)

CodecManager.registerCodecClass('pickle', PickleCodec)

class Base64Codec(CodecManager.Codec):
	def encode(self, template):
		return (base64.encodestring(template), 'base64 data')
	
	def decode(self, data):
		return (base64.decodestring(data), None)

CodecManager.registerCodecClass('base64', Base64Codec)


class JsonCodec(CodecManager.Codec):
	def encode(self, template):
		return (json.dumps(template), 'json data')

	def decode(self, data):
		return (json.loads(data), None)

CodecManager.registerCodecClass('json', JsonCodec)
