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
# HTTP codec.
##

import CodecManager

import re

HEADERLINE_REGEXP = re.compile(r'(?P<header>[a-zA-Z0-9_-]+)\s*:\s*(?P<value>.*)')
REQUESTLINE_REGEXP = re.compile(r'(?P<method>[a-zA-Z0-9_-]+)\s*(?P<url>[^\s]*)\s*(?P<version>[a-zA-Z0-9_/\.-]+)')
STATUSLINE_REGEXP = re.compile(r'(?P<version>[a-zA-Z0-9_/\.-]+)\s*(?P<status>[0-9]+)\s*(?P<reason>.*)')


class HttpRequestCodec(CodecManager.Codec):
	"""
	Encode/decode from to:
	
	type record HttpRequest
	{
		charstring method,
		charstring url,
		charstring version optional, // default: HTTP/1.1
		record { charstring <header name>* } headers optional, // default: {}
		charstring body optional, // default: ''
	}
	
	Automatically computes the content-length if not provided.
	
	When decoded, all header names are transformed to lower caps.
	"""
	def encode(self, template):
		method = template.get('method', 'GET')
		url = template['url']
		version = template.get('version', 'HTTP/1.1')
		headers = template.get('headers', {})
		body = template.get('body', '')
		
		contentLengthAdded = False
		ret = []
		ret.append('%s %s %s' % (method, url, version))
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
		ret['url'] = m.group('url')
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
				ret['headers'][m.group('header').lower()] = m.group('value')
			else:
				raise Exception("Invalid header in message (%s)" % str(l))
		
		ret['body'] = "\r\n".join(lines[i:])
		
		return (ret, self.getSummary(ret))

	def getSummary(self, template):
		"""
		Returns the summary of the template representing an RTSP message.
		(meaningful, short, human-understandable description)
		"""
		return '%s %s' % (template.get('method', 'GET'), template['url'])
		
CodecManager.registerCodecClass('http.request', HttpRequestCodec)

class HttpResponseCodec(CodecManager.Codec):
	"""
	Encode/decode from to:
	
	type record HttpResponse
	{
		charstring version optional, // default: HTTP/1.1
		integer status,
		charstring reason,
		record { charstring <header name>* } headers optional, // default: {}
		charstring body optional, // default: ''
	}
	
	Automatically computes the content-length if not provided.
	
	When decoded, all header names are transformed to lower caps.
	"""
	def encode(self, template):
		status = template['status']
		reason = template['reason']
		version = template.get('version', 'HTTP/1.1')
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
			ret.append('Content-Length: %d' % bodyLength)
		ret.append('')
		if body:
			ret.append(body)
		ret.append('')
		
		return ('\r\n'.join(ret), self.getSummary(template))

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
				ret['headers'][m.group('header').lower()] = m.group('value')
			else:
				raise Exception("Invalid header in message (%s)" % str(l))
		
		self.log('remaining lines: ' + unicode(lines[i:]))
		
		ret['body'] ="\r\n".join(lines[i:])
		
		contentLength = ret['headers'].get('content-length', None)
		self.log('content length: ' + str(contentLength))
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
		
CodecManager.registerCodecClass('http.response', HttpResponseCodec)
		

