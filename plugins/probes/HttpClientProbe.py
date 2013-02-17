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
Identification and Properties
-----------------------------

Probe Type ID: ``tcp``

Properties:

.. csv-table::
   :header: "Name","Type","Default value","Description"

   "``local_ip``","string","(empty - system assigned)","Local IP address to use when sending HTTP requests."
   "``local_port``","integer","``0`` (system assigned)","Local port to use when sending HTTP requests."
   "``host``","string","``localhost``","The HTTP server's hostname or IP address."
   "``port``","integer","``80``","The HTTP server's port."
   "``version``","string","``HTTP/1.0``","The HTTP version to use in requests."
   "``protocol``","string","``http``","The HTTP variant:``http`` or ``https``. For now, only ``http`` is supported."
   "``maintain_connection``","boolean","``False``","If set to True and HTTP version is 1.1, the probe keeps the tcp connection opened once a response has been received, until the server closes it."
   "``connection_timeout``","float","``5.0``","The connection timeout, in s, when trying to connect to a remote party."

Overview
--------

This probe acts as a simple HTTP client and is fully based on :doc:`ProbeTcp` with :doc:`HTTP codecs <CodecHttp>`.

It can be used to connect to an HTTP server, send and receive requests at low-level. This client won't follow HTTP redirections, enable authentication, or anything fancy.
However, it is able to maintain the TCP connection between requests (set ``maintain_connection`` to ``True``) and 
manageq a connection timeout to automatically fails the probe after a given delay (see the ``connection_timeout`` property).

For HTTPS connectivity, you should consider using :doc:`ProbeTcp` with :doc:`HTTP codecs <CodecHttp>` as default codecs instead.

Availability
~~~~~~~~~~~~

All platforms.

Dependencies
~~~~~~~~~~~~

None.

See Also
~~~~~~~~

Instead of using the probe, you may consider a :doc:`ProbeTcp` with some :doc:`HTTP codecs <CodecHttp>` set as default encoder/decoders, which offer
a greater control and support HTTPS as well (with ``use_ssl`` set to ``True``).


TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the ``HttpClientPortType`` port type as specified below:

::

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
		self.setDefaultProperty('maintain_connection', False)
		self.setDefaultProperty('version', 'HTTP/1.0')
		self.setDefaultProperty('auto_connect', False)
		self.setDefaultProperty('protocol', 'http')
		self.setDefaultProperty('host', 'localhost')
		self.setDefaultProperty('port', 80)
		self.setDefaultProperty('local_ip', '')
		self.setDefaultProperty('connection_timeout', 5.0)

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
				(encodedMessage, summary) = CodecManager.encode('http.request', message)
			except Exception, e:
				raise ProbeImplementationManager.ProbeException('Invalid request message format: cannot encode HTTP request:\n%s' % ProbeImplementationManager.getBacktrace())
			
			# Connect if needed
			if not self.isConnected():
				self.connect()

			# Send our payload
			self._httpConnection.send(encodedMessage)
			self.logSentPayload(summary, encodedMessage, "%s:%s" % self._httpConnection.getpeername())
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
		sock.settimeout(float(self['connection_timeout']))
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
					
					decodedMessage = None

					self._probe.getLogger().debug('data received (bytes %d), decoding attempt...' % len(buf))
					# If we are not disconnected, notify that the codec can still expect more data (complete = False)
					(status, _, decodedMessage, summary) = CodecManager.incrementalDecode('http.response', buf, complete = (not read))

					if status == CodecManager.IncrementalCodec.DECODING_NEED_MORE_DATA:
						if not read:
							# We are disconnected.
							raise Exception('Unable to decode response: additional data required, but connection lost')
						else:
							# Just wait
							self._probe.getLogger().info('Waiting for additional data...')
					elif status == CodecManager.IncrementalCodec.DECODING_ERROR:
						raise Exception('Unable to decode response: decoding error')
					else:
						# DECODING_OK
						fromAddr = "%s:%s" % (self._probe['host'], self._probe['port'])
						self._probe.getLogger().debug('message decoded, enqueuing...')
						self._probe.logReceivedPayload(summary, buf, fromAddr)
						self._probe.triEnqueueMsg(decodedMessage, fromAddr)
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
		
