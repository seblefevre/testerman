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
# -*- coding: utf-8 -*-
# Codec manager.
##

import TestermanTCI

def log(txt):
	TestermanTCI.logInternal("CD: " + txt)

class Codec:
	"""
	Codec base class
	"""
	def __init__(self):
		self._properties = {}
	
	def setProperty(self, name, value):
		self._properties[name] = value
	
	def getProperty(self, name, defaultValue = None):
		return self._properties.get(name, defaultValue)
	
	def __getitem__(self, name):
		return self._properties.get(name, None)
	
	def encode(self, template):
		return None
	
	def decode(self, template):
		return None


class CodecManager(object):
	def __init__(self):
		#: dict[codec/aliasname] = (codec class, params)
		self._codecs = {}
	
	def registerCodecClass(self, name, class_):
		if not self._codecs.has_key(name):
			self._codecs[name] = (class_, {})
			log("Registered codec class for %s" % name)
	
	def alias(self, name, codec, **kwargs):
		"""
		Configure a codec and alias it.
		Aliasing of configured codecs subclasses its properties, so
		that we can create different specialized configurations based on
		the same alias.
		"""
		if not self._codecs.has_key(codec):
			raise Exception("Unable to alias codec %s to %s: codec %s is not registered" % (codec, name, codec))
		(codecClass, properties) = self._codecs[name]
		mergedProperties = {}
		for n, p in properties.items():
			mergedProperties[n] = p
		for n, p in kwargs.items():
			mergedProperties[n] = p
		self._codecs[name] = (codecClass, mergedProperties)

	def _getCodecInstance(self, name):
		"""
		Creates and returns configured codec instance.
		"""
		if not self._codecs.has_key(name):
			return None
		else:
			codecClass, properties = self._codecs[name]
			c = codecClass()
			for n, p in properties.items():
				c.setProperty(n, p)
			return c
	
	def encode(self, name, template):
		# NB: we instantiate a codec each type to be thread safe and parallel
		codec = self._getCodecInstance(name)
		if codec:
			return codec.encode(template)
		else:
			# Unable to find the codec
			return None

	def decode(self, name, data):
		# NB: we instantiate a codec each type to be thread safe and parallel
		codec = self._getCodecInstance(name)
		if codec:
			return codec.decode(data)
		else:
			# Unable to find the codec
			return None


TheInstance = None

def instance():
	global TheInstance
	if TheInstance is None:
		TheInstance = CodecManager()
	return TheInstance

def alias(name, codec, **kwargs):
	"""
	Creates a configured codec with an alias.
	"""
	return instance().alias(name, codec, **kwargs)

def registerCodecClass(name, class_):
	log("Registering codec class %s ..." % name)
	return instance().registerCodecClass(name, class_)

def encode(name, template):
	"""
	@type  name: string
	@param name: the codec name
	@type  template: <any>
	@param template: the template to encode. Should match the codec requirements.
	
	@throws Exception in case of an encoding error
	
	@rtype: buffer, or None
	@returns: the encoded buffer, or None if the codec was not found.
	"""
	return instance().encode(name, template)

def decode(name, data):
	"""
	@type  name: string
	@param name: the codec name
	@type  data: buffer string
	@param data: the buffer to decode

	@rtype: <any>, or None
	@returns: the decoded message according to the codec, or None if the codec was not found.
	"""
	return instance().decode(name, data)

