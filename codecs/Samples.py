##
# Sample codecs
##

import TestermanCD

import pickle
import base64

class PickleCodec(TestermanCD.Codec):
	def encode(self, template):
		return pickle.dumps(template)
	
	def decode(self, data):
		return pickle.loads(data)

TestermanCD.registerCodecClass('pickle', PickleCodec)

class Base64Codec(TestermanCD.Codec):
	def encode(self, template):
		return base64.encodestring(template)
	
	def decode(self, data):
		return base64.decodestring(data)

TestermanCD.registerCodecClass('base64', Base64Codec)
