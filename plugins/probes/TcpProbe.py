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
# An TCP basic probe.
#
##

import ProbeImplementationManager
import CodecManager

import select
import socket
import sys
import threading
import time
import tempfile
import os

try:
	# SSL support only available starting from Python 2.6
	import ssl
except ImportError:
	pass

# A default 1024-bit key
DEFAULT_SSL_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQDixwQncELtZxYdgczRns7mtHPlbjbfU58qg4IVE6hX1BbOoaG+
Skkg4tRWRX1IRz21kgJR0dGeZMxpzBEbvljJRXzCDjDUSpXIjKxFXJDJJc6vxjON
nk0En3bifDeXCTumazYQYgECJOatR0RdgP3uqvNo5IRHcYxSZlZpLAUZ/QIDAQAB
AoGAeHaZaU3D75IL+F6j61H9vCVtTxmNwnIMIaw75HBNw2HhP6AyZ//T+skjXDSL
iWJ2kEXgP5BCVm5a+3QwPlmNlVTL7OoyxdM602NBYAkQM9Ws0Q72XXvO+t8BkUa4
PIiIBamnuk3N2+ollMT4+ydwJ8ED8B8v38mbXNVqySTr4g0CQQD6fywj9Lk+UYlH
5JVQnoCPM43qoTt2bS1mXh/MwhiwLh6QmiFj+VyKHQg/lgDO+IrQVN+J/mi7ezjN
Lt0zNb2DAkEA58JxY4yL1kd6abJcNJDZdGKQK5jvlG6KCFyBxBMZ0aAWA//gVS0G
9WUQJTypAfllHDVE5BJSzG2Lv9oO2l2yfwJAQ+fRqXWf+frUgj6/E3nEVA2fvSk0
G2iBVCzT5gf/9VKrSnvd7WId6frwz3v0gCb0SoGXj6r97UT8IvM/V7CLzQJAOBmh
SO+kieITh7JdD3xgpwOU0njaxZtcXlnGL6hP/6Y4rg8qRnP30z77gYgFgSzVhNaA
LpUg5cs+oNov7jvwEQJAMcbZQFqgvEcDQZMZsni7LHWA/vrdve52E116c2k7D+ue
0Y7pPAsMwmQyDRovHFuQhAVeoavWBy2Ktjua6qEHKA==
-----END RSA PRIVATE KEY-----"""

# With an associated self-signed certificate
DEFAULT_SSL_CERTIFICATE = \
"""-----BEGIN CERTIFICATE-----
MIICPTCCAaYCCQDP2Zlsj6TqTDANBgkqhkiG9w0BAQUFADBjMQswCQYDVQQGEwJG
UjERMA8GA1UECBMIR3Jlbm9ibGUxDzANBgNVBAcTBk1leWxhbjESMBAGA1UEChMJ
VGVzdGVybWFuMRwwGgYDVQQDExNzYW1wbGUudGVzdGVybWFuLmZyMB4XDTEwMDcx
MzE1NTMwNloXDTIwMDcxMDE1NTMwNlowYzELMAkGA1UEBhMCRlIxETAPBgNVBAgT
CEdyZW5vYmxlMQ8wDQYDVQQHEwZNZXlsYW4xEjAQBgNVBAoTCVRlc3Rlcm1hbjEc
MBoGA1UEAxMTc2FtcGxlLnRlc3Rlcm1hbi5mcjCBnzANBgkqhkiG9w0BAQEFAAOB
jQAwgYkCgYEA4scEJ3BC7WcWHYHM0Z7O5rRz5W4231OfKoOCFROoV9QWzqGhvkpJ
IOLUVkV9SEc9tZICUdHRnmTMacwRG75YyUV8wg4w1EqVyIysRVyQySXOr8YzjZ5N
BJ924nw3lwk7pms2EGIBAiTmrUdEXYD97qrzaOSER3GMUmZWaSwFGf0CAwEAATAN
BgkqhkiG9w0BAQUFAAOBgQDET13MT8ctRiuQkfCLO8D9iyKjT94FRe+ocPbUjOts
gjkrh5miH91MhabQrqEcwOArF+2yuakvfgdPP3KbHgBXDwtYg/+wqAj4e/74D6Ai
Ud0h6vHFVZreLZm7F1QNLpgUSrPxra2xkTiH7NxEMYlJheGCnJ4F6YP3IdKMUicZ
Og==
-----END CERTIFICATE-----"""

class Connection:
	def __init__(self):
		self.socket = None
		self.incoming = False
		self.peerAddress = None
		self.buffer = '' # raw buffer
		self.decodingBuffer = '' # accumulation of raw buffers for incremental decoding

class TcpProbe(ProbeImplementationManager.ProbeImplementation):
	"""
Identification and Properties
-----------------------------

Probe Type ID: ``tcp``

Properties:

.. csv-table::
   :header: "Name","Type","Default value","Description"
	 
   "``local_ip``","string","(empty - system assigned)","Local IP address to use when sending packets"
   "``local_port``","integer","``0`` (system assigned)","Local port to use when sending packets"
   "``listening_ip``","string","``0.0.0.0``","Listening IP address, if listening mode is activated (see below)"
   "``listening_port``","integer","``0``","Set it to a non-zero port to start listening on mapping"
   "``size``","integer","``0``","Fixed-size packet strategy: if set to non-zero, only raises messages when ``size`` bytes have been received. All raised messages will hage this constant size."
   "``separator``","string","``None``","Separator-based packet strategy: if set to a character or a string, only raises messages when ``separator`` has been encountered; this separator is assumed to be a packet separator, and is not included in the raised message. May be useful for, for instance, \\x00-based packet protocols."
   "``enable_notifications``","boolean","``False``","If set, you may get connection/disconnection notification and connectionConfirm/Error notification messages"
   "``default_sut_address``","string (ip:port)","``None``","If set, used as a default SUT address if none provided by the user"
   "``default_decoder``","string","``None``","If set, must be a valid codec name (aliases are currently not supported). This codec is then used to decode all incoming packets, and only the probe only raises an incoming message when the codec successfully decoded something. This is particular convenient when used with an incremental codec (such as ``'http.request'``) that will then be responsible for identifying the actual application PDU in the TCP stream."
   "``default_encoder``","string","``None``","If set, must be a valid codec name (aliases are currently not supported). This codec is then used to encode all outgoing packets, without a need to use it when sending the message through the port mapped to this probe."
   "``use_ssl``","boolean","``False``","If set, all outgoing and incoming traffic through is probe is transported over SSLv3. All TLS negotiations are performed by the probe. However, ..."
   "``ssl_key``","string","``None``","The SSL key to use if ``use_ssl``is set to ``True``. Contains a private key associated to ``ssl_certificate``, in base64 format. If not provided, a default sample private key is used."
   "``ssl_certificate``","string","``None``","The SSL certificate to use if ``use_ssl``is set to ``True``. Contains a certificate in PEM format that will be used when a certificate is needed by the probe connection(s). If not provided, a default one that matches the default private key, is used."
   "``connection_timeout``","float","``5.0``","The connection timeout, in s, when trying to connect to a remote party."
   "``auto_connect``","boolean","``True``","When sending a message, autoconnect to the provided address if there is no existing connections with this peer yet."

Overview
--------

This is a general purpose probe to transport anything over TCP, with basic control on connections/disconnections
(you can get optional incoming connection notifications or outgoing connection confirmations, or simply focus on payload exchanges),
and a basic support for SSL (v3).

Such a probe may be used as a base to test any protocol transported over TCP.

Combined with the ``http.request`` and ``http.response`` codecs, this is enough to test anything based on HTTP/HTTPS. You may also use the ``diameter`` or ``sua`` codec, actually any codec that comes
with an incremental decoding implementation. You just have to define such a codec as the ``default_decoder`` property (used to decode incoming stream) or the ``default_encoder`` property (used to
encode outgoing messages).

ADPU Identification
~~~~~~~~~~~~~~~~~~~

The probe first waits for ``size`` bytes (if the ``size`` property is set) or (exclusively) for the ``separator`` character(s) (is the ``separator`` property is set).
If none of those properties are set, the probe only considers what it read in the stream (which is system-dependent).

Then, the default decoder, if set, tries to decode this first raw segment. If it needs more input, it waits for the next raw segment. If multiple APDUs are detected, multiple incoming messages are raised.
If undecodable data is detected, the raw segment is ignored.

If no decoder is set, the raw segment is raised as raw data.

Basic SSL Support
~~~~~~~~~~~~~~~~~

When the property ``use_ssl`` is set to True, the probe automatically performs SSL negotiations after a TCP connection (probe as a client) or when accepting a new incoming connection (as a server).

If ``enable_notifications`` is True, the ``connectionConfirm`` message will contain the server's certificate in DER format. The ``connectionNotification`` message is planned
to contain the client's certificate as well, but it is currently not possible to force the (server side) probe to request it.

In addition, received certificates are not validated, and hostnames are not verified.

This probe offers very little control on these negotiations and is not meant to test SSL-level stuff (for instance, how a SUT implemented SSL itself).
This support is provided as a convenience to interact with a SUT through higher-level protocols that have been ported over SSL (HTTP, SIP, ...).

When using this probe as a server in SSL mode, if you don't provide the ``ssl_key`` and ``ssl_certificate`` parameters, a default pair is used.
The default certificate is::

  -----BEGIN CERTIFICATE-----
  MIICPTCCAaYCCQDP2Zlsj6TqTDANBgkqhkiG9w0BAQUFADBjMQswCQYDVQQGEwJG
  UjERMA8GA1UECBMIR3Jlbm9ibGUxDzANBgNVBAcTBk1leWxhbjESMBAGA1UEChMJ
  VGVzdGVybWFuMRwwGgYDVQQDExNzYW1wbGUudGVzdGVybWFuLmZyMB4XDTEwMDcx
  MzE1NTMwNloXDTIwMDcxMDE1NTMwNlowYzELMAkGA1UEBhMCRlIxETAPBgNVBAgT
  CEdyZW5vYmxlMQ8wDQYDVQQHEwZNZXlsYW4xEjAQBgNVBAoTCVRlc3Rlcm1hbjEc
  MBoGA1UEAxMTc2FtcGxlLnRlc3Rlcm1hbi5mcjCBnzANBgkqhkiG9w0BAQEFAAOB
  jQAwgYkCgYEA4scEJ3BC7WcWHYHM0Z7O5rRz5W4231OfKoOCFROoV9QWzqGhvkpJ
  IOLUVkV9SEc9tZICUdHRnmTMacwRG75YyUV8wg4w1EqVyIysRVyQySXOr8YzjZ5N
  BJ924nw3lwk7pms2EGIBAiTmrUdEXYD97qrzaOSER3GMUmZWaSwFGf0CAwEAATAN
  BgkqhkiG9w0BAQUFAAOBgQDET13MT8ctRiuQkfCLO8D9iyKjT94FRe+ocPbUjOts
  gjkrh5miH91MhabQrqEcwOArF+2yuakvfgdPP3KbHgBXDwtYg/+wqAj4e/74D6Ai
  Ud0h6vHFVZreLZm7F1QNLpgUSrPxra2xkTiH7NxEMYlJheGCnJ4F6YP3IdKMUicZ
  Og==
  -----END CERTIFICATE-----

Availability
~~~~~~~~~~~~

All platforms. However, SSL support depends on the Python SSL module, provided by default with Python 2.6 and later on Unix platforms.

Dependencies
~~~~~~~~~~~~

None.

See Also
~~~~~~~~

Other transport-oriented probes:

* :doc:`ProbeSctp`
* :doc:`ProbeUdp`

TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the ``TransportProbePortType`` port type as specified below:

::

  type union NotificationType
  {
    record { octetstring certificate optional } connectionNotification, // new incoming connection established
    charstring disconnectionNotification, // contains a human readable reason to the disconnection
    record { octetstring certificate optional } connectionConfirm, // connection request OK
    charstring connectionError, // contains a human readable error after a connection request
  }
  
  type union RequestType
  {
    any connectionRequest, // request a new tcp-connection
    any disconnectionRequest, // request a disconnection. Except a disconnectionNotification later
  }
  
  type TransportProbePortType
  {
    in RequestType;
    out NotificationType;
    in, out octetstring;
    out any; // if the default_decoder is used, the raised structure is the decoder's output
    in any; // if the default_encoder is used
  }
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()

		self._listeningSocket = None
		self._connections = {} # Connections() indexed by peer address (ip, port)
		self._pollingThread = None
		self.setDefaultProperty('local_ip', '')
		self.setDefaultProperty('local_port', 0)
		self.setDefaultProperty('listening_port', 0) # 0 means: not listening
		self.setDefaultProperty('listening_ip', '')
		self.setDefaultProperty('timeout', 0) # Not supported for now - this packetization criterium would be "raise a packet after N ms of inactivity on the socket"
		self.setDefaultProperty('size', 0)
		self.setDefaultProperty('separator', None)
		self.setDefaultProperty('enable_notifications', False)
		self.setDefaultProperty('default_sut_address', None)
		self.setDefaultProperty('default_decoder', None)
		self.setDefaultProperty('default_encoder', None)
		self.setDefaultProperty('use_ssl', None)
		self.setDefaultProperty('ssl_key', DEFAULT_SSL_PRIVATE_KEY)
		self.setDefaultProperty('ssl_certificate', DEFAULT_SSL_CERTIFICATE)
		self.setDefaultProperty('connection_timeout', 5.0)
		self.setDefaultProperty('auto_connect', True)
	
	# ProbeImplementation reimplementation
	def onTriMap(self):
		self._reset()
		# Should we start listening here ??
		port = self['listening_port']
		if port:
			self._startListening()
		self._startPollingThread()
	
	def onTriUnmap(self):
		self._reset()
	
	def onTriSAReset(self):
		self._reset()
	
	def onTriExecuteTestCase(self):
		self._reset()

	# Specific implementation
	def _reset(self):	
		self._stopPollingThread()
		self._stopListening()
		self._disconnectOutgoingConnections()

	def _checkSutAddress(self, sutAddress):
		try:
			# Split a ip:port to a (ip, port)
			t = sutAddress.split(':')
			addr = (socket.gethostbyname(t[0]), int(t[1]))
			return addr
		except:
			raise Exception("Invalid, unresolvable, or missing SUT Address when sending a message")

	def onTriSend(self, message, sutAddress):
		# First implementation level: no notification/connection explicit management.
		# We send a message. If not connected yet, connect first.

		# First fallback if the user did not provide a SUT address:
		# default SUT address (useful for outgoing connections)
		if not sutAddress:
			sutAddress = self['default_sut_address']
		
		# Second fallback, useful for servers with a single incoming connection
		if not sutAddress:
			self._lock()
			conns = self._connections.values()
			if len(conns) == 1:
				# A single connection exist. Auto select it.
				sutAddress = "%s:%s" % conns[0].peerAddress
			self._unlock()

		if (isinstance(message, tuple) or isinstance(message, list)) and len(message) == 2:
			cmd, _ = message
			if cmd == "connectionRequest":
				addr = self._checkSutAddress(sutAddress)
				conn = self._connect(addr)
			elif cmd == "disconnectionRequest":
				addr = self._checkSutAddress(sutAddress)
				self._disconnect(addr, "disconnected by local user")
			elif cmd == "stopListening":
				self._stopListening()
			elif cmd == "startListening":
				self._startListening()
			elif cmd == "disconnectAll":
				self._disconnectOutgoingConnections()
				self._disconnectIncomingConnections()
			elif self['default_encoder']:
				addr = self._checkSutAddress(sutAddress)
				conn = self._getConnection(addr)
				# send the message
				if not conn and self['auto_connect']:
					conn = self._connect(addr)
				if conn:
					# Now we can send our payload
					self._send(conn, message)
			else:
				raise Exception("Unsupported request (%s)" % cmd)
		
		elif isinstance(message, basestring) or self['default_encoder']:
			addr = self._checkSutAddress(sutAddress)
			conn = self._getConnection(addr)
			if not conn and self['auto_connect']:
				conn = self._connect(addr)
			if conn:
				# Now we can send our payload
				self._send(conn, message)
		
		else:
			raise Exception("Unsupported message type")
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def _toSsl(self, sock, serverSide):
		try:
			keyfile = None
			certfile = None

			ssl_key = self['ssl_key']
			if ssl_key:
				(tmpkey, keyfile) = tempfile.mkstemp()
				tmpkey = os.fdopen(tmpkey, 'w')
				if not ssl_key.startswith('--'):
					tmpkey.write('-----BEGIN RSA PRIVATE KEY-----\n')
					tmpkey.write(ssl_key + '\n')
					tmpkey.write('-----END RSA PRIVATE KEY-----\n')
				else:
					tmpkey.write(ssl_key)
				tmpkey.close()

			ssl_certificate = self['ssl_certificate']
			if ssl_certificate:
				(tmpcert, certfile) = tempfile.mkstemp()
				tmpcert = os.fdopen(tmpcert, 'w')
				tmpcert.write(ssl_certificate)
				tmpcert.close()

			s = ssl.wrap_socket(sock, keyfile = keyfile, certfile = certfile, server_side = serverSide)
			if keyfile:
				try:
					os.remove(keyfile)
				except:
					pass
			if certfile:
				try:
					os.remove(certfile)
				except:
					pass
			return s
		except ssl.SSLError, e:
			if keyfile:
				try:
					os.remove(keyfile)
				except:
					pass
			if certfile:
				try:
					os.remove(certfile)
				except:
					pass
			raise Exception("SSL Error: %s" % e)

	def _connect(self, to):
		"""
		Creates an TCP connection to the to address (ip, port),
		then registers the connection.
		"""
		self.getLogger().info("Connecting to %s..." % str(to))
		conn = None
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
			sock.bind((self['local_ip'], self['local_port']))
			sock.settimeout(float(self['connection_timeout']))
			# Blocking connection (for now)
			# FIXME: make connection asynchronous so that userland timers can work
			sock.connect(to)
			if self['use_ssl']:
				sock = self._toSsl(sock, serverSide = False)
				self.getLogger().debug("SSL client socket initialized.")
			conn = self._registerOutgoingConnection(sock, to)
		except Exception, e:
			self.getLogger().info("Connection to %s failed: %s" % (str(to), str(e)))
			if self['enable_notifications']:
				self.triEnqueueMsg(('connectionError', str(e)), "%s:%s" % to)
			else:
				raise e
		if conn and self['enable_notifications']:
			args = {}
			if self['use_ssl']:
				args = { 'certificate': sock.getpeercert(binary_form = True) }
			self.triEnqueueMsg(('connectionConfirm', args), "%s:%s" % to)
		if conn:
			self.getLogger().info("Connected to %s" % str(to))
		return conn
	
	def _registerOutgoingConnection(self, sock, addr):
		c = Connection()
		c.socket = sock
		c.peerAddress = addr
		c.incoming = False
		self._lock()
		self._connections[addr] = c
		self._unlock()
		return c
	
	def _registerIncomingConnection(self, sock, addr):
		c = Connection()
		c.socket = sock
		c.peerAddress = addr
		c.incoming = True
		self._lock()
		self._connections[addr] = c
		self._unlock()
		return c
	
	def _getConnection(self, peerAddress):
		conn = None
		self._lock()
		if self._connections.has_key(peerAddress):
			conn = self._connections[peerAddress]
		self._unlock()
		return conn
	
	def _send(self, conn, data):
		encoder = self['default_encoder']
		if encoder:
			try:
				(data, summary) = CodecManager.encode(encoder, data)
			except Exception:
				raise ProbeImplementationManager.ProbeException('Cannot encode outgoing message using defaut encoder:\n%s' % ProbeImplementationManager.getBacktrace())
			self.logSentPayload(summary, data, "%s:%s" % conn.socket.getpeername())
		else:
			self.logSentPayload("TCP data", data, "%s:%s" % conn.socket.getpeername())
		conn.socket.send(data)

	def _disconnect(self, addr, reason):
		self.getLogger().info("Disconnectiong from %s, reason: %s" % (addr, reason))
		conn = None
		self._lock()
		if addr in self._connections:
			conn = self._connections[addr]
			del self._connections[addr]
		self._unlock()

		if conn:
			try:
				conn.socket.close()
			except Exception, e:
				self.getLogger().warning("Unable to close socket from %s: %s" % (addr, str(e)))
		# Disconnection notification
		if self['enable_notifications']:
			self.triEnqueueMsg(('disconnectionNotification', reason), "%s:%s" % addr)
	
	def _disconnectIncomingConnections(self):
		self._lock()
		connections = self._connections.values()
		self._unlock()
		
		for conn in connections:
			if conn.incoming:
				self._disconnect(conn.peerAddress, reason = 'disconnected by local user')
	
	def _disconnectOutgoingConnections(self):
		self._lock()
		connections = self._connections.values()
		self._unlock()
		
		for conn in connections:
			if not conn.incoming:
				self._disconnect(conn.peerAddress, reason = 'disconnected by local user')
	
	def _startListening(self):
		if self['use_ssl']:
			try:
				ssl
			except:
				raise Exception("SSL Support is not available on this host. It requires Python 2.6+.")
	
		addr = (self['listening_ip'], self['listening_port'])
		self.getLogger().info("Starting listening on %s" % (str(addr)))
		
		# Should be mutex-protected
		self._lock()
		try:
			self._listeningSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
			self._listeningSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self._listeningSocket.bind(addr)
			self._listeningSocket.listen(10)
		except Exception, e:
			self._unlock()
			raise e
		self._unlock()
	
	def _stopListening(self):
		self._disconnectIncomingConnections()
		# Should be mutex-protected
		self._lock()
		try:
			if self._listeningSocket:
				self.getLogger().info("Stopping listening...")
				self._listeningSocket.close()
				self._listeningSocket = None
				self.getLogger().info("Stopped listening")
		except Exception, e:
			pass
		self._unlock()
	
	def _startPollingThread(self):
		if not self._pollingThread:
			self._pollingThread = PollingThread(self)
			self._pollingThread.start()

	def _stopPollingThread(self):
		if self._pollingThread:
			self._pollingThread.stop()
			self._pollingThread = None

	##
	# Interface to be pluggable on a PollingThread
	##
	def _getListeningSockets(self):
		sockets = []
		self._lock()
		if self._listeningSocket:
			sockets.append(self._listeningSocket)
		self._unlock()
		return sockets
	
	def _getActiveSockets(self):
		self._lock()
		sockets = [conn.socket for conn in self._connections.values()]
		self._unlock()
		return sockets
		
	def _feedData(self, addr, data):
		conn = self._getConnection(addr)
		if not conn:
			self.getLogger().warning("Received data from %s, which is not a known connection" % str(addr))
		else:
			# We are suppose to check for packetization criteria here
			# (size, timeout, separator)
			conn.buffer += data
			msg = None
			
			size = self['size']
			separator = self['separator']

			if size:
				while len(conn.buffer) >= size:
					msg = conn.buffer[:size]
					conn.buffer = conn.buffer[size+1:]
					self._preEnqueueMsg(conn, msg, "%s:%s" % addr, disconnected = (data == ''))

			elif separator is not None:
				msgs = conn.buffer.split(separator)
				for msg in msgs[:-1]:
					self._preEnqueueMsg(conn, msg, "%s:%s" % addr, disconnected = (data == ''))

				conn.buffer = msgs[-1]
			else:
				msg = conn.buffer
				conn.buffer = ''
				# No separator or size criteria -> send to userland what we received according to the tcp stack
				self._preEnqueueMsg(conn, msg, "%s:%s" % addr, disconnected = (data == ''))

	def _preEnqueueMsg(self, conn, msg, addr, disconnected):
		decoder = self['default_decoder']
		if decoder:
			buf = conn.decodingBuffer + msg
			# Loop on multiple possible APDUs
			while buf:
				(status, consumedSize, decodedMessage, summary) = CodecManager.incrementalDecode(decoder, buf, complete = disconnected)
				if status == CodecManager.IncrementalCodec.DECODING_NEED_MORE_DATA:
					# Do nothing. Just wait for new raw segments.
					self.getLogger().info("Waiting for more raw segments to complete incremental decoding (using codec %s)." % decoder)
					conn.decodingBuffer = buf
					break
				elif status == CodecManager.IncrementalCodec.DECODING_OK:
					if consumedSize == 0:
						consumedSize = len(buf)
					# Store what was not consumed for later
					conn.decodingBuffer = buf[consumedSize:]
					# And raise the decoded message
					self.logReceivedPayload(summary, buf[:consumedSize], addr)
					self.triEnqueueMsg(decodedMessage, addr)
					# make sure we update the local loop buffer, too
					buf = conn.decodingBuffer 
				else: # status == CodecManager.IncrementalCodec.DECODING_ERROR:
					self.getLogger().error("Unable to decode raw data with the default decoder (codec %s). Ignoring the segment." % decoder)
					break

		else: # No default decoder
			if not disconnected:
				# disconnected is set if and only if the new data is empty - don't send this empty message
				self.logReceivedPayload("TCP data", msg, addr)
				self.triEnqueueMsg(msg, addr)
	
	def _onIncomingConnection(self, sock, addr):
		self._registerIncomingConnection(sock, addr)
		if self['enable_notifications']:
			args = {}
			if self['use_ssl']:
				c = sock.getpeercert(binary_form = True)
				if c:
					args = { 'certificate': c }
			self.triEnqueueMsg(('connectionNotification', args), "%s:%s" % addr)

class PollingThread(threading.Thread):
	"""
	This is a worker thread that pools all existing
	connections, based on their sockets.
	It also waits for incoming connections on listening sockets.
	
	These sockets are extracted from the probe when needed, that's why
	the probe implements the following interface:
		_getListeningSockets()
		_getActiveSockets()
		_disconnect(addr)
		_registerIncomingConnection(sock, addr)
	"""
	def __init__(self, probe):
		threading.Thread.__init__(self)
		self._probe = probe
		self._stopEvent = threading.Event()
	
	def stop(self):
		self._stopEvent.set()
		self.join()
	
	def run(self):
		# Main poll loop
		while not self._stopEvent.isSet():
			try:
				listening = self._probe._getListeningSockets()
				active = self._probe._getActiveSockets()
				rset = listening + active

				r, w, e = select.select(rset, [], [], 0.001)
				for s in r:
					try:
						if s in listening:
							self._probe.getLogger().debug("Accepting a new connection")
							(sock, addr) = s.accept()
							if self._probe['use_ssl']:
								sock = self._probe._toSsl(sock, serverSide = True)
							self._probe._onIncomingConnection(sock, addr)
							# Raise a new connection notification event - soon
						else:
							addr = s.getpeername()
							self._probe.getLogger().debug("New data to read from %s" % str(addr))
							data = s.recv(65535)
							if not data:
								self._probe.getLogger().debug("%s disconnected by peer" % str(addr))
								self._probe._feedData(addr, '') # notify the feeder that we won't have more data
								self._probe._disconnect(addr, reason = "disconnected by peer")
							else:
								# New received message.
								self._probe._feedData(addr, data)

					except Exception, e:
						self._probe.getLogger().warning("exception while polling active/listening sockets: %s" % str(e) + ProbeImplementationManager.getBacktrace())
					
			except Exception, e:
				self._probe.getLogger().warning("exception while polling active/listening sockets: %s" % str(e))
				# Avoid 100% CPU usage when select() raises an error
				time.sleep(0.01)	
					


ProbeImplementationManager.registerProbeImplementationClass('tcp', TcpProbe)
