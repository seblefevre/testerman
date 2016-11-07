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
# HTTP codec.
##

import CodecManager

import re

HEADERLINE_REGEXP = re.compile(r'(?P<header>[a-zA-Z0-9_-]+)\s*:\s*(?P<value>.*)')
REQUESTLINE_REGEXP = re.compile(r'(?P<method>[a-zA-Z0-9_-]+)\s*(?P<url>[^\s]*)\s*(?P<version>[a-zA-Z0-9_/\.-]+)')
STATUSLINE_REGEXP = re.compile(r'(?P<version>[a-zA-Z0-9_/\.-]+)\s*(?P<status>[0-9]+)\s*(?P<reason>.*)')

def chunk(body):
	"""
	Chunks a body in one piece.
	"""
	return "%x\r\n%s\r\n0\r\n" % (len(body), body)


class HttpRequestCodec(CodecManager.IncrementalCodec):
	"""
	= Identification and Properties =
	
	Codec IDs: `http.request`

	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	|| header_encoding || string  || `'iso8859-1'` || Encoding to use to encode header values. ||

	= Overview =

	This codec enables to encode/decode HTTP 1.0/1.1 requests,
	and provides some built-in functionalities to manage low-level stuff such as
	content-lenght and transfer-encoding management. 

	== Encoding ==
	
	...

	This encoder automatically computes the content-length if not provided,
	unless a transfer-encoding was set explicitly to `chunked`. In this case,
	the body is automatically chunked (in a single piece).
	
	== Decoding ==
	
	...
	
	This is an incremental decoder.

	It automatically waits for a complete payload before passing it to
	your application, supporting content-length header (if present)
	or `chunked` transfer-encoding (the body is automatically reconstructed
	in this cae).
	
	Invalid or incomplete HTTP requests are not decoded.

	Upon decoding, all header names are transformed to lower caps so that
	a unified way of matching them may be used in your ATSes.
	
	== Availability ==

	All platforms.

	== Dependencies ==

	None.

	== See Also ==
	
	This codec is typically used with CodecHttpResponse (`http.response`).

	= TTCN-3 Type Equivalence =
	
	This codec encodes/decodes the following structure:
	{{{
	type record HttpRequest
	{
		charstring method optional, // default: GET
		charstring url optional, // default: /
		charstring version optional, // default: HTTP/1.1
		record { charstring <header name>* } headers optional, // default: {}
		charstring body optional, // default: ''
	}
	}}}
	"""
	def encode(self, template):
		method = template.get('method', 'GET')
		url = template.get('url', '/')
		version = template.get('version', 'HTTP/1.1')
		headers = template.get('headers', {})
		body = template.get('body', '')
		
		contentLengthAdded = False
		transferEncodingAdded = False
		
		ret = []
		ret.append('%s %s %s' % (method, url, version))
		
		chunked = False
		if self.getProperty('transfer_encoding', None) == "chunked":
			chunked = True
			
		for key, val in headers.items():
			if val is None:
				continue
			if key.lower() == 'content-length':
				contentLengthAdded = True
			if key.lower() == 'transfer-encoding':
				transferEncodingAdded = True
				if val == "chunked":
					chunked = True
				else:
					chunked = False
			ret.append(u'%s: %s' % (key, unicode(val)))

		if not contentLengthAdded and not chunked:
			bodyLength = 0
			if body:
				bodyLength = len(body)
			ret.append('Content-Length: %d' % bodyLength)
		
		if chunked and not transferEncodingAdded:
			ret.append('Transfer-Encoding: chunked')
		
		# Header values are encoded as iso8859-1. 
		# However 
		ret = map(lambda x: x.encode(self.getProperty('header_encoding', 'iso8859-1')), ret)
		
		ret.append('')
		
		if body:
			if chunked:
				ret.append(chunk(body))
			else:
				ret.append(body)
		else:		
			ret.append('')

		ret = '\r\n'.join(ret)
		return (ret, self.getSummary(template))

	def incrementalDecode(self, data, complete):
		"""
		Incremental decoder version:
		- detect missing bytes if a content-length is provided
		- able to decode Transfer-Encoding: chunked
		"""
		ret = {}
		# Make sure we have a complete request line before continuing
		if not '\r\n' in data:
			return self.needMoreData()
		lines = data.split('\r\n')
		
		# Request line
		m = REQUESTLINE_REGEXP.match(lines[0])
		if not m:
			raise Exception("Invalid request line (%s)"% lines[0])
		ret['method'] = m.group('method')
		ret['url'] = m.group('url')
		ret['version'] = m.group('version')
		ret['headers'] = {}
		
		# Header lines
		bodyStarted = False
		i = 1
		for header in lines[1:]:
			i += 1
			l = header.strip()
			if not header:
				bodyStarted = True
				break # reached body and its empty line
			m = HEADERLINE_REGEXP.match(l)
			if m:
				ret['headers'][m.group('header').lower()] = m.group('value')
			else:
				raise Exception("Invalid header in message (%s)" % str(l))
		
		if not bodyStarted:
			return self.needMoreData()
		
		# Body
		ret['body'] = ''
		
		encoding = ret['headers'].get('transfer-encoding', None)
		if encoding == 'chunked':
			# Chunked based
			# The chunksize is on a single line, in hexa
			try:
#				print "DEBUG: initial chunk size line: %s" % repr(lines[i])
				if not lines[i].strip():
					return self.needMoreData() # Let's wait for the chunk size in a next payload
				chunkSize = int(lines[i].strip(), 16)
#				print "DEBUG: initial chunk size: %s" % chunkSize
				
				remainingPayload = '\r\n'.join(lines[i+1:])
#				print "DEBUG: remaining payload: " + repr(remainingPayload)
				
				while chunkSize != 0:
					# OK, let's start consuming our chunk, exactly chunkSize characters,
					# then followed by an empty line, then possibly another chunksize, etc.
					chunk = remainingPayload[:chunkSize]
					if len(chunk) < chunkSize:
						return self.needMoreData()
					ret['body'] += chunk
					
#					print "DEBUG: added chunk:" + repr(chunk)
#					print "DEBUG: now the body is: " + repr(ret['body'])
					
					# Now check that we have an empty line
					remainingPayload = remainingPayload[chunkSize:]
					
					lines = remainingPayload.split('\r\n')
					if lines[0]:
						# should be an empty line... spurious data
						raise Exception("No chunk boundary at the end of the chunk. Invalid data.")
					if not lines[1]:
						# No next chunk size yet
						return self.needMoreData()
					else:
						chunkSize = int(lines[1].strip(), 16)
					remainingPayload = '\r\n'.join(lines[2:])
#					print "DEBUG: remaining payload: " + repr(remainingPayload)

			except IndexError:
				return self.needMoreData()
		
		else:
			# No chunk
			ret['body'] ="\r\n".join(lines[i:])
			# If Content-length present, additional check
			contentLength = ret['headers'].get('content-length', None)
			if contentLength is not None:
				cl = int(contentLength)
				bl = len(ret['body'])
				if bl < cl:
					return self.needMoreData()
				elif bl > cl:
					# Truncate the body
					ret['body'] = ret['body'][:cl]
		
		return self.decoded(ret, self.getSummary(ret))

	def getSummary(self, template):
		"""
		Returns the summary of the template representing an RTSP message.
		(meaningful, short, human-understandable description)
		"""
		return '%s %s' % (template.get('method', 'GET'), template['url'])
		
CodecManager.registerCodecClass('http.request', HttpRequestCodec)


class HttpResponseCodec(CodecManager.IncrementalCodec):
	"""
	= Identification and Properties =
	
	Codec IDs: `http.response`

	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	|| header_encoding || string  || `'iso8859-1'` || Encoding to use to encode header values. ||

	= Overview =

	This codec enables to encode/decode HTTP 1.0/1.1 responses,
	and provides some built-in functionalities to manage low-level stuff such as
	content-lenght and transfer-encoding management. 

	== Encoding ==
	
	...

	This encoder automatically computes the content-length if not provided,
	unless a transfer-encoding was set explicitly to `chunked`. In this case,
	the body is automatically chunked (in a single piece).
	
	== Decoding ==
	
	...
	
	This is an incremental decoder.

	It automatically waits for a complete payload before passing it to
	your application, supporting content-length header (if present)
	or `chunked` transfer-encoding (the body is automatically reconstructed
	in this cae).
	
	Invalid or incomplete HTTP responses are not decoded.

	Upon decoding, all header names are transformed to lower caps so that
	a unified way of matching them may be used in your ATSes.

	== Availability ==

	All platforms.

	== Dependencies ==

	None.

	== See Also ==
	
	This codec is typically used with CodecHttpRequest (`http.request`).

	= TTCN-3 Type Equivalence =
	
	This codec encodes/decodes the following structure:
	{{{	
	type record HttpResponse
	{
		charstring version optional, // default: HTTP/1.1
		integer status,
		charstring reason,
		record { charstring <header name>* } headers optional, // default: {}
		charstring body optional, // default: ''
	}
	}}}
	"""
	def encode(self, template):
		status = template['status']
		reason = template['reason']
		version = template.get('version', 'HTTP/1.1')
		headers = template.get('headers', {})
		body = template.get('body', '')
		
		contentLengthAdded = False
		transferEncodingAdded = False

		ret = []
		ret.append('%s %s %s' % (version, str(status), reason))

		chunked = False
		if self.getProperty('transfer_encoding', None) == "chunked":
			chunked = True

		for key, val in headers.items():
			if val is None:
				continue
			if key.lower() == 'content-length':
				contentLengthAdded = True
			if key.lower() == 'transfer-encoding':
				transferEncodingAdded = True
				if val.lower() == "chunked":
					chunked = True
				else:
					chunked = False
			ret.append(u'%s: %s' % (key, unicode(val)))

		if not contentLengthAdded and not chunked:
			bodyLength = 0
			if body:
				bodyLength = len(body)
			ret.append('Content-Length: %d' % bodyLength)
		
		if chunked and not transferEncodingAdded:
			ret.append('Transfer-Encoding: chunked')
		
		# Header values are encoded as iso8859-1. 
		# However 
		ret = map(lambda x: x.encode(self.getProperty('header_encoding', 'iso8859-1')), ret)

		ret.append('')

		if body:
			if chunked:
				ret.append(chunk(body))
			else:
				ret.append(body)
		else:
			ret.append('')
		
		return ('\r\n'.join(ret), self.getSummary(template))

	def incrementalDecode(self, data, complete):
		"""
		Incremental decoder version:
		- detect missing bytes if a content-length is provided
		- able to decode Transfer-Encoding: chunked
		"""
		ret = {}
		lines = data.split('\r\n')
		
		# Status line
		m = STATUSLINE_REGEXP.match(lines[0])
		if not m:
			raise Exception("Invalid status line")
		ret['version'] = m.group('version')
		ret['status'] = int(m.group('status'))
		ret['reason'] = m.group('reason')
		ret['headers'] = {}
		
		# Header lines
		bodyStarted = False
		i = 1
		for header in lines[1:]:
			i += 1
			l = header.strip()
			if not header:
				bodyStarted = True
				break # reached body and its empty line
			m = HEADERLINE_REGEXP.match(l)
			if m:
				ret['headers'][m.group('header').lower()] = m.group('value')
			else:
				raise Exception("Invalid header in message (%s)" % str(l))
		
		if not bodyStarted:
			return self.needMoreData()
		
		# Body
		ret['body'] = ''
		
		encoding = ret['headers'].get('transfer-encoding', None)
		if encoding == 'chunked':
			# Chunked based
			# The chunksize is on a single line, in hexa
			try:
#				print "DEBUG: initial chunk size line: %s" % repr(lines[i])
				if not lines[i].strip():
					return self.needMoreData() # Let's wait for the chunk size in a next payload
				chunkSize = int(lines[i].strip(), 16)
#				print "DEBUG: initial chunk size: %s" % chunkSize
				
				remainingPayload = '\r\n'.join(lines[i+1:])
#				print "DEBUG: remaining payload: " + repr(remainingPayload)
				
				while chunkSize != 0:
					# OK, let's start consuming our chunk, exactly chunkSize characters,
					# then followed by an empty line, then possibly another chunksize, etc.
					chunk = remainingPayload[:chunkSize]
					if len(chunk) < chunkSize:
						return self.needMoreData()
					ret['body'] += chunk
					
#					print "DEBUG: added chunk:" + repr(chunk)
#					print "DEBUG: now the body is: " + repr(ret['body'])
					
					# Now check that we have an empty line
					remainingPayload = remainingPayload[chunkSize:]
					
					lines = remainingPayload.split('\r\n')
					if lines[0]:
						# should be an empty line... spurious data
						raise Exception("No chunk boundary at the end of the chunk. Invalid data.")
					if not lines[1]:
						# No next chunk size yet
						return self.needMoreData()
					else:
						chunkSize = int(lines[1].strip(), 16)
					remainingPayload = '\r\n'.join(lines[2:])
#					print "DEBUG: remaining payload: " + repr(remainingPayload)

			except IndexError:
				return self.needMoreData()
		
		else:
			# No chunk
			ret['body'] ="\r\n".join(lines[i:])
			# If Content-length present, additional check
			contentLength = ret['headers'].get('content-length', None)
			if contentLength is not None:
				cl = int(contentLength)
				bl = len(ret['body'])
				if bl < cl:
					return self.needMoreData()
				elif bl > cl:
					# Truncate the body
					ret['body'] = ret['body'][:cl]
			else:
				# No chunk, no content-length: maybe this is normal (204, 304 and 1xx) or we wait until the end of the connection if we can
				if not complete and not (ret['status'] in [204, 304] or ret['status'] <= 199):
					return self.needMoreData()
		
		return self.decoded(ret, self.getSummary(ret))

	def getSummary(self, template):
		"""
		Returns the summary of the template representing an RTSP message.
		(meaningful, short, human-understandable description)
		"""
		return '%s %s' % (template['status'], template['reason'])
		
CodecManager.registerCodecClass('http.response', HttpResponseCodec)
		


if __name__ == '__main__':
	import binascii
	def o(x):
		return binascii.unhexlify(x.replace(' ', ''))
	
	httpResponse10 = """HTTP/1.0 200 OK
Content-Type: text/plain
Content-Length: 18

This is some data.
"""

	httpResponse11 = """HTTP/1.1 200 OK
Content-Type: text/plain
Transfer-Encoding: chunked

25
This is the data in the first chunk

1C
and this is the second one

0
"""

	print 80*'-'
	print "HTTP Codec unit tests"
	print 80*'-'
	samples = [	
		('http.response', '\r\n'.join(httpResponse10.splitlines())),
		('http.response', '\r\n'.join(httpResponse11.splitlines())),
	]

	for codec, s in samples:
		print
		print 80*'-'
		print "Testing:\n%s" % s
		(_, _, decoded, summary) = CodecManager.incrementalDecode(codec, s, complete = True)
		print "Decoded:\n%s\nSummary: %s" % (decoded, summary)
		(reencoded, summary) = CodecManager.encode(codec, decoded)
		print "Reencoded:\n%s\nSummary: %s" % (reencoded, summary)
		print "Original :\n%s" % s

