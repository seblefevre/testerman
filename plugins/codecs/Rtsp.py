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
# RTSP codec.
##

import CodecManager

import re

HEADERLINE_REGEXP = re.compile(r'(?P<header>[a-zA-Z0-9_-]+)\s*:\s*(?P<value>.*)')
REQUESTLINE_REGEXP = re.compile(r'(?P<method>[a-zA-Z0-9_-]+)\s*(?P<uri>[^\s]*)\s*(?P<version>[a-zA-Z0-9_/\.-]+)')
STATUSLINE_REGEXP = re.compile(r'(?P<version>[a-zA-Z0-9_/\.-]+)\s*(?P<status>[0-9]+)\s*(?P<reason>.*)')


class RtspRequestCodec(CodecManager.Codec):
	"""
Identification and Properties
-----------------------------

Codec ID: ``rtsp.request`` and ``rtsp.response``

Properties:

+------------------+-----------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+
| name             | type      | default value   | description                                                                                                                           |
+==================+===========+=================+=======================================================================================================================================+
| ``lower_case``   | boolean   | ``False``       | decoding: transforms header names to lower case, making header name matching easier (when performing non-protocol oriented testing)   |
+------------------+-----------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ``version``      | string    | ``RTSP/1.0``    | encoding: the version to set in the request or response line, if not provided by the user                                             |
+------------------+-----------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+

Overview
--------

These two codecs encode/decode RTSP requests and responses respectively
from/to the following TTCN-3 equivalence types (optional fields are
always provided when decoding), as provided below.

During encoding, they automatically compute the content-length if not
provided as a header, and add it only if a body is present.

Content-Length verification is also performed on decoding
automatically. If the length is not valid, the decoding attempt fails.

These codecs are usually used with :doc:`the UDP probe <ProbeUdp>` to implement solutions that can test an RTSP implementation.

Availability
~~~~~~~~~~~~

All platforms.

Dependencies
~~~~~~~~~~~~

None.

TTCN-3 Types Equivalence
------------------------

::

  type record RtspRequest
  {
    charstring method,
    charstring uri,
    charstring version optional, // default: RTSP/1.0
    record { charstring <header name>* } headers optional, // default: {}
    charstring body optional, // default: ''
  }
  
  type record RtspResponse
  {
    charstring version optional, // default: RSTP/1.0
    integer status,
    charstring reason,
    record { charstring <header name>* } headers optional, // default: {}
    charstring body optional, // default: ''
  }

	"""
	def __init__(self):
		CodecManager.Codec.__init__(self)
		self.setDefaultProperty('lower_case', False)
		self.setDefaultProperty('version', 'RTSP/1.0')
	
	def encode(self, template):
		method = template.get('method')
		uri = template['uri']
		version = template.get('version', self['version'])
		headers = template.get('headers', {})
		body = template.get('body', '')
		
		contentLengthAdded = False
		ret = []
		ret.append('%s %s %s' % (method, uri, version))
		for key, val in headers.items():
			if val is None:
				continue
			if key.lower() == 'content-length':
				contentLengthAdded = True
			ret.append('%s: %s' % (key, str(val)))
		if not contentLengthAdded:
			bodyLength = 0
			if body:
				bodyLength = len(body)
			ret.append('Content-Length: %d' % bodyLength)
		ret.append('')
		if body:
			ret.append(body)
		
		ret.append('')

		ret = '\r\n'.join(ret)
		return (ret, self.getSummary(template))

	def decode(self, data):
		ret = {}
		lines = data.split('\r\n')
		m = REQUESTLINE_REGEXP.match(lines[0])
		if not m:
			raise Exception("Invalid request line")
		ret['method'] = m.group('method')
		ret['uri'] = m.group('uri')
		ret['version'] = m.group('version')
		ret['headers'] = {}
		
		i = 1
		for header in lines[1:]:
			i += 1
			l = header.strip()
			if not header:
				break # reached body
			m = HEADERLINE_REGEXP.match(l)
			if m:
				if self['lower_case']:
					ret['headers'][m.group('header').lower()] = m.group('value')
				else:
					ret['headers'][m.group('header')] = m.group('value')
			else:
				raise Exception("Invalid header in message (%s)" % str(l))
		
		ret['body'] = "\r\n".join(lines[i:])
		
		return (ret, self.getSummary(ret))

	def getSummary(self, template):
		"""
		Returns the summary of the template representing an RTSP message.
		(meaningful, short, human-understandable description)
		"""
		return template['method']


		
CodecManager.registerCodecClass('rtsp.request', RtspRequestCodec)


class RtspResponseCodec(CodecManager.Codec):
	"""
	See documentation in RtspRequestCodec.
	"""
	def __init__(self):
		CodecManager.Codec.__init__(self)
		self.setDefaultProperty('lower_case', False)
		self.setDefaultProperty('version', 'RTSP/1.0')
	
	def encode(self, template):
		status = template['status']
		reason = template['reason']
		version = template.get('version', self[version])
		headers = template.get('headers', {})
		body = template.get('body', '')
		
		contentLengthAdded = False
		ret = []
		ret.append('%s %s %s' % (str(status), reason, version))
		for key, val in headers.items():
			if val is None:
				continue
			if key.lower() == 'content-length':
				contentLengthAdded = True
			ret.append('%s: %s' % (key, str(val)))
		if not contentLengthAdded:
			bodyLength = 0
			if body:
				bodyLength = len(body)
				# Only add a content-length if we have a body
				ret.append('Content-Length: %d' % bodyLength)
		ret.append('')
		if body:
			ret.append(body)
		ret.append('')
		
		return ('\r\n'.join(ret), self.getSummary(template))

	def _getInsensitiveValue(self, headers, name):
		"""
		Case insensitive search on headers.
		Returns None if not found.
		"""
		for key, val in headers.items():
			if key.lower() == name:
				return val
		return None

	def decode(self, data):
		ret = {}
		lines = data.split('\r\n')
		m = STATUSLINE_REGEXP.match(lines[0])
		if not m:
			raise Exception("Invalid status line")
		ret['version'] = m.group('version')
		ret['status'] = int(m.group('status'))
		ret['reason'] = m.group('reason')
		ret['headers'] = {}
		
		i = 1
		for header in lines[1:]:
			i += 1
			l = header.strip()
			if not header:
				break # reached body and its empty line
			m = HEADERLINE_REGEXP.match(l)
			if m:
				if self['lower_case']:
					ret['headers'][m.group('header').lower()] = m.group('value')
				else:
					ret['headers'][m.group('header')] = m.group('value')
			else:
				raise Exception("Invalid header in message (%s)" % str(l))
		
		ret['body'] ="\r\n".join(lines[i:])
		
		contentLength = self._getInsensitiveValue(ret['headers'], 'content-length')
		if contentLength is not None:
			cl = int(contentLength)
			bl = len(ret['body'])
			if bl < cl:
				raise Exception('Missing bytes in body (content-length: %d, body length : %d)', (cl, bl))
			elif bl > cl:
				# Truncate the body
				ret['body'] = ret['body'][:cl]
		
		return (ret, self.getSummary(ret))

	def getSummary(self, template):
		"""
		Returns the summary of the template representing an RTSP message.
		(meaningful, short, human-understandable description)
		"""
		return '%s %s' % (template['status'], template['reason'])
		
CodecManager.registerCodecClass('rtsp.response', RtspResponseCodec)
		

