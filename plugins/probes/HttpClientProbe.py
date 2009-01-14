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
# A probe HTTP/HTTPS client behaviours (request/response)
##


import ProbeImplementationManager
import CodecManager

import threading
import socket
import select


class HttpClientProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	type record HttpRequest
	{
		charstring method optional, // default: 'GET'
		charstring url,
		record { charstring <header name>* } headers,
		charstring body optional, // default: ''
	}

	type record HttpResponse
	{
		integer status,
		charstring reason,
		charstring protocol,
		record { charstring <header name>* } headers,
		charstring body,
	}

	type port HttpClientPortType
	{
		in HttpRequest;
		out HttpResponse;
	}
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()
		self._httpThread = None
		self._httpConnection = None
		# Default test adapter parameters
		self.setDefaultParameter('maintain_connection', False)
		self.setDefaultParameter('version', 'HTTP/1.0')
		self.setDefaultParameter('auto_connect', False)
		self.setDefaultParameter('protocol', 'http')
		self.setDefaultParameter('host', 'localhost')
		self.setDefaultParameter('port', 80)
		self.setDefaultParameter('local_ip', '')

	# LocalProbe reimplementation)
	def onTriMap(self):
		if self['auto_connect']:
			self.connect()
	
	def onTriUnmap(self):
		self.reset()
	
	def onTriExecuteTestCase(self):
		# No static connections
		pass

	def onTriSAReset(self):
		# No static connections
		pass
	
	def onTriSend(self, message, sutAddress):
		try:
			# FIXME:
			# Should go to a configured codec instance instead.
			# (since we modify the message here...)
			if not message.has_key('version'):
				message['version'] = self['version']
			try:
				encodedMessage = CodecManager.encode('http.request', message)
			except Exception, e:
				raise ProbeImplementationManager.ProbeException('Invalid request message format: cannot encode HTTP request')
			
			# Connect if needed
			if not self.isConnected():
				self.connect()

			# Send our payload
			self._httpConnection.send(encodedMessage)
			self.logSentPayload(encodedMessage.split('\r\n')[0], encodedMessage)
			# Now wait for a response asynchronously
			self.waitResponse()
		except Exception, e:
			raise ProbeImplementationManager.ProbeException('Unable to send HTTP request: %s' % str(e))
				
			
	# Specific methods
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def connect(self):
		"""
		Tcp-connect to the host. Returns when we are ready to send something.
		"""
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		sock.bind((self['local_ip'], 0))
		sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
		# Blocking or not ?
		sock.connect((self['host'], self['port']))
		self._httpConnection = sock
	
	def isConnected(self):
		if self._httpConnection:
			return True
		else:
			return False
	
	def disconnect(self):
		if self._httpConnection:
			try:
				self._httpConnection.close()
			except:
				pass
		self._httpConnection = None
	
	def reset(self):
		if self._httpThread:
			self._httpThread.stop()
		self.disconnect()
		self._httpThread = None
	
	def waitResponse(self):
		"""
		Creates a thread, wait for the response.
		"""
		self._httpThread = ResponseThread(self, self._httpConnection)
		self._httpThread.start()

class ResponseThread(threading.Thread):
	def __init__(self, probe, socket):
		threading.Thread.__init__(self)
		self._probe = probe
		self._socket = socket
		self._stopEvent = threading.Event()
	
	def run(self):
		buf = ''
		while not self._stopEvent.isSet():
			try:
				r, w, e = select.select([self._socket], [], [], 0.1)
				if self._socket in r:
					read = self._socket.recv(1024*1024)
					buf += read
					# If we are in HTTP/1.0, we should wait for the connection close to decode our message,
					# since there is no chunk transfer encoding and content-length is not mandatory.
					if self._probe['version'] == 'HTTP/1.0' and read:
						# Still connected (i.e. we did not get our r + 0 byte signal
						continue
					
					decodedMessage = None
					try:
						self._probe.getLogger().debug('data received (bytes %d), decoding attempt...' % len(buf))
						decodedMessage = CodecManager.decode('http.response', buf)
					except Exception, e:
						# Incomplete message. Wait for more data.
						self._probe.getLogger().debug('unable to decode: %s' % str(e))
						pass
						
					if decodedMessage:
						self._probe.getLogger().debug('message decoded, enqueuing...')
						self._probe.logReceivedPayload(buf.split('\r\n')[0], buf)
						self._probe.triEnqueueMsg(decodedMessage)
						self._stopEvent.set()
			except Exception, e:
				self._probe.getLogger().error('Error while waiting for http response: %s' % str(e))
				self._stopEvent.set()
		if not self._probe['maintain_connection']:
			# Well, actually this should depends on the HTTP protocol version...
			self._probe.disconnect()
	
	def stop(self):
		self._stopEvent.set()
		self.join()
					
					
ProbeImplementationManager.registerProbeImplementationClass('http.client', HttpClientProbe)
		