# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008,2009,2010 Sebastien Lefevre and other contributors
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
# Codec manager - view from the codecs (either for pyagent-based probes or TE)
#
# This is a common file to the core and pyagent, enabling the use
# of the same codecs implementations.
#
##


##
# Codec-related exceptions
##
class CodecNotFoundException(Exception): pass

##
# Utilities
##
def getBacktrace():
	"""
	Returns the current backtrace.
	"""
	import traceback
	import StringIO
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

##
# Main Codec Class to implement
##
class Codec:
	"""
	Codec base class for all codec plugins.
	Subclass it to create your own codec.
	"""

	# These constant are used for incremental decoding only.
	DECODING_ERROR = -2
	DECODING_NEED_MORE_DATA = -1
	DECODING_OK = 0

	def __init__(self):
		self._properties = {}
	
	# Internal use only: called from the CodecManager
	def _setProperty(self, name, value):
		"""
		This function is called by the codec manager or codec adapter
		to inject some properties into the codec instance.
		You should never call this.
		
		If you need to set default properties in your codec constructor,
		use setDefaultProperty() instead.
		
		@type  name: string
		@param name: the name of the property to set
		@type  value: obj
		@param value: its associated value
		"""
		self._properties[name] = value
	
	##
	# Provided for the codec implementor's convenience
	##
	def setDefaultProperty(self, name, value):
		"""
		Use this method to set a default value for your codec properties.
		
		Properties are codec parameters that can be customized by the
		user from the userland using the define_codec_alias Testerman function.
		Convenient to create multiple variants of the same codec
		(for instance, xml pretty printed or raw, etc).
		
		@type  name: string
		@param name: the name of the property to set
		@type  value: obj
		@param value: its associated default value
		"""
		self._properties[name] = value

	def getProperty(self, name, defaultValue = None):
		"""
		Use this method to get a property's value that may not have been
		set before (either by a setDefaultProperty or by the user when
		defining a codec alias).
		
		You may prefer __getitem__ to get a well known value
		if you don't need an inline defaut value capability.
		
		@type  name: string
		@param name: the name of the property you want the value from
		@type  defautValue: obj
		@param defaultVaue: a default value to return if the property was not set
		
		@rtype: obj
		@returns: the property's value, or the default value if not set
		"""
		return self._properties.get(name, defaultValue)
	
	def __getitem__(self, name):
		"""
		Convenience function. Same as above, without inline default value support.

		@type  name: string
		@param name: the name of the property you want the value from
		@rtype: obj
		@returns: the property's value, or None if not set
		"""
		return self._properties.get(name, None)
	
	def log(self, message):
		"""
		Call this function to log something.
		Depending on the codec adapter, leads to different log traces.
		- agent logger when the codec is used in a pyagent,
		- tli logger as "internal" class level when used in a TE
		
		@type  message: string/unicode
		@param message: the message to log
		"""
		instance().log(message)

	def incrementalDecode(self, data, complete):
		"""
		Provided for compatibility: so that non-incremental implementations
		can be called transparently from code that assumes that an
		incremental decoding method is available.
		
		Incremental decoders must reimplement this one,
		usually by subclassing IncrementalCodec instead of this class.
		"""
		try:
			(message, summary) = self.decode(data)
		except:
			return (self.DECODING_ERROR, 0, None, None)
		if message is None:
			return (self.DECODING_ERROR, 0, None, None)
		# We assume that the whole data was consumed.
		return (self.DECODING_OK, len(data), message, summary)
		

	# To reimplement in your own codecs

	def encode(self, template):
		"""
		To implement in your Codec subclass.
		
		Given a Testerman fully valuated message, try to encode it
		to an octetstring.
		
		You may raise exceptions in case of encoding errors.
		
		@type  template: obj
		@param template: a valid, fully valuated Testerman message
		
		@rtype: (string (as a buffer), string), or (None, None)
		@returns: (encoded payload, summary):
		  the encoded payload, or None in case of an error,
			and an optional summary indicating what has been encoded.
			This summary is typically < 20 characters, and should be
			meaningful in logs for a human analysis.
			For instance, it can be "INVITE", "HTTP POST", "SRIforSM Ack", ...
			If this summary is empty or None, it won't be taken into account.
		"""
		raise Exception("Encoding method not implemented")
	
	def decode(self, data):
		"""
		To implement in your Codec subclass.
		
		Try to decode some data to a Testerman message.
		The encoded payload is assumed to be exactly what the codec
		is supposed to consume - no more, no less.
		
		Use this for codecs that are likely to work with non-streamed transports,
		and called on well identified APDUs.
		
		You may raise exceptions in case of decoding errors.

		@type  data: string (as a buffer)
		@param data: the encoded payload
		
		@rtype: tuple (obj, string)
		@return: tuple (message, summary):
			message: the decoded message, or None in case of an error if you did not 
			raise an Exception
			summary: an optional summary indicating what has been decoded.
			This summary is typically < 20 characters, and should be
			meaningful in logs for a human analysis.
			For instance, it can be "INVITE", "HTTP POST", "SRIforSM Ack", ...
			If this summary is empty or None, it won't be taken into account.
		"""
		raise Exception("Decoding method not implemented")
	

class IncrementalCodec(Codec):
	"""
	Same as above, but with incremental decoding capabilities:
	- the codec is able to consume only a part of the data to decode,
	  and tell the caller how many bytes were consumed
	  (either as correctly decoded or as garbage)
	- the codec is able to tell the caller that it needs more bytes to
	  complete its decoding.
	
	However, this is a stateless codec. It does not have to "wait for more data",
	as the next attempt will provide the same data plus additional one.
	
	Notice that incremental encoding is useless for Testerman, the user always
	provides a full payload to encode.
	
	If you chose to implement an incremental codec, you don't need to
	implement the decode(self, data) method of the standard Codec class.
	"""
	
	# Convenience functions related to incremental decoding only
	def decodingError(self):
		return (self.DECODING_ERROR, 0, None, None)
	
	def needMoreData(self, consumedBytes = 0):
		return (self.DECODING_NEED_MORE_DATA, consumedBytes, None, None)
	
	def decoded(self, decodedMessage, summary, consumedBytes = 0):
		return (self.DECODING_OK, consumedBytes, decodedMessage, summary)
	
	# Functions to implement
	def incrementalDecode(self, data, complete):
		"""
		To implement in your IncrementalCodec subclass.
		
		Try to decode some data to a Testerman message.
		The encoded payload passed in argument may be shorter than required
		by the codec.
		
		You may raise exceptions in case of decoding errors.
		However, if you just miss some bytes, please returns (-1, None)
		instead, so that we can feed you with a more complete payload
		on a next attempt.
		Your codec must be stateless. You don't have to "wait" for
		further data, the next attempt will provide you with the data
		you already analyzed (not optimized, but more simple to implement).
		
		@type  data: string (as a buffer)
		@param data: the encoded payload
		@type  complete: bool
		@param complete: set to true by the caller when no more data won't be available,
		false otherwise. When set to false, NEED_MORE_DATA as a meaning. Otherwise,
		this is interpreted as a DECODING_ERROR, as no more data won't be provided.
		Sometimes the codec needs to know if it could collect more data or not to
		know when it should stop its decoding.
		
		@rtype: tuple (int, int, obj, string)
		@return: tuple (status, consumedBytes, message, summary) where:
		  status = -2 (DECODING_ERROR): encoding error, and you did not want to use an exception
		  status = -1 (DECODING_NEED_MORE_DATA): payload too short, missing bytes to decode the message
			status = 0  (DECODING_OK): correctly decoded
			consumedSize: the number of bytes consumed in data. 
				If status == ERROR, the caller will then garbage/drop these bytes.
				If status == NEED_MORE_DATA, this returned value will be ignored, as you'll get a full
				data payload on next attempt.
				If status == OK, will remove these bytes from the data buffer. In this case, if consumedSize == 0,
				the whole data is assumed to be consumed (equiv to len(data)).
			message: the decoded message in case of status == OK. Ignored otherwise.
			summary: an optional summary indicating what has been decoded.
			This summary is typically < 20 characters, and should be
			meaningful in logs for a human analysis.
			For instance, it can be "INVITE", "HTTP POST", "SRIforSM Ack", ...
			If this summary is empty or None, it won't be taken into account.
			The summary is ignored if status < 0.
		"""
		raise Exception("Incremental decoding method not implemented")

	def decode(self, data):
		"""
		Turns an incremental decoder into something callable from a non-incremental feeder.
		"""
		(status, consumedSize, decodedMessage, summary) = self.incrementalDecode(data, complete = True)
		if status == self.DECODING_OK:
			return (decodedMessage, summary)
		else:
			return (None, None)

##
# Internal class - do not use
##
class CodecManager(object):
	"""
	A CodecManager is adapted according to the
	target context (a TE or a PyAgent) via the following methods:
	- setLogCallback(): enables to implement logging according to the target context
	"""
	def __init__(self):
		#: dict[codec/aliasname] = (codec class, params)
		self._codecs = {}
		self._logCallback = None
	
	def log(self, txt):
		if self._logCallback:
			self._logCallback(txt)
	
	def setLogCallback(self, cb):
		self._logCallback = cb
	
	def registerCodecClass(self, name, class_):
		if not self._codecs.has_key(name):
			self._codecs[name] = (class_, {})
			self.log("Codec class %s registered as codec %s" % (class_.__name__, name))
	
	def alias(self, name, codec, **kwargs):
		"""
		Configure a codec and alias it.
		Aliasing of configured codecs subclasses its properties, so
		that we can create different specialized configurations based on
		the same alias.
		"""
		if not self._codecs.has_key(codec):
			raise Exception("Unable to alias codec %s to %s: codec %s is not registered" % (codec, name, codec))
		(codecClass, properties) = self._codecs[codec]
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
				c._setProperty(n, p)
			return c
	
	def encode(self, name, template, **properties):
		# NB: we instantiate a codec each type to be thread safe and parallel.
		# This is not optimized, we may use a TLS one day.
		codec = self._getCodecInstance(name)
		if codec:
			for k, v in properties.items():
				codec._setProperty(k, v)
			return codec.encode(template)
		else:
			# Unable to find the codec
			raise CodecNotFoundException("Codec '%s' not found" % name)

	def decode(self, name, data,  **properties):
		# NB: we instantiate a codec each type to be thread safe and parallel
		codec = self._getCodecInstance(name)
		if codec:
			for k, v in properties.items():
				codec._setProperty(k, v)
			return codec.decode(data)
		else:
			# Unable to find the codec
			raise CodecNotFoundException("Codec '%s' not found" % name)

	def incrementalDecode(self, name, data, complete, **properties):
		# NB: we instantiate a codec each type to be thread safe and parallel
		codec = self._getCodecInstance(name)
		if codec:
			for k, v in properties.items():
				codec._setProperty(k, v)
			(ret, a, b, c) = codec.incrementalDecode(data, complete)
			# If the codec expects more data and we can't provide mode: decoding error
			if ret == codec.DECODING_NEED_MORE_DATA and complete:
				ret = codec.DECODING_ERROR
			return (ret, a, b, c)
		else:
			# Unable to find the codec
			raise CodecNotFoundException("Codec '%s' not found" % name)


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
	return instance().registerCodecClass(name, class_)

def encode(name, template, **properties):
	"""
	@type  name: string
	@param name: the codec name
	@type  template: <any>
	@param template: the template to encode. Should match the codec requirements.
	@type  properties: keyword args of objects
	@param properties: overriding properties for this encode call
	
	@throws Exception in case of an encoding error
	
	@rtype: buffer, or None
	@returns: the encoded buffer, or None if the codec was not found.
	"""
	return instance().encode(name, template, **properties)

def decode(name, data, **properties):
	"""
	@type  name: string
	@param name: the codec name
	@type  data: buffer string
	@param data: the buffer to decode
	@type  properties: keyword args of objects
	@param properties: overriding properties for this decode call

	@rtype: <any>, or None
	@returns: the decoded message according to the codec, or None if the codec was not found.
	"""
	return instance().decode(name, data, **properties)

def incrementalDecode(name, data, complete, **properties):
	"""
	@type  name: string
	@param name: the codec name
	@type  data: buffer string
	@param data: the buffer to decode
	@type  properties: keyword args of objects
	@param properties: overriding properties for this decode call

	@rtype: <any>, or None
	@returns: the decoded message according to the codec, or None if the codec was not found.
	"""
	return instance().incrementalDecode(name, data, complete, **properties)

