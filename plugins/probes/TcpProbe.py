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
# An TCP basic probe.
#
##

import ProbeImplementationManager

import select
import socket
import sys
import threading

class Connection:
	def __init__(self):
		self.socket = None
		self.incoming = False
		self.peerAddress = None
		self.buffer = ''

class TcpProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	type union NotificationType
	{
		any connectionNotification, // new incoming connection established
		charstring disconnectionNotification, // contains a human readable reason to the disconnection
		any connectionConfirm, // connection request OK
		charstring connectionError, // contains a human readable error after a connection request
	}
	
	type union RequestType
	{
		any connectionRequest, // request a new tcp-connection
		any disconnectionRequest, // request a disconnection. Except a disconnectionNotification later
	}
	
	type TcpProbePortType
	{
		in RequestType;
		out NotificationType;
		in, out octetstring;
	}
	
	Properties:
	|| `local_ip` || string || (empty - system assigned) || Local IP address to use when sending packets ||
	|| `local_port` || integer || 0 (system assigned) || Local port to use when sending packets ||
	|| `listening_ip` || string || 0.0.0.0 || Listening IP address, if listening mode is activated (see below) ||
	|| `listening_port` || integer || 0 || Set it to a non-zero port to start listening on mapping ||
	|| `size` || integer || 0 || Fixed-size packet strategy: if set to non-zero, only raises messages when `size` bytes have been received. All raised messages will hage this constant size. ||
	|| `separator` || string || None || Separator-based packet strategy: if set no a character or a string, only raises messages when `separator` has been encountered; this separator is assumed to be a packet separator, and is not included in the raised message. May be useful for, for instance, \x00-based packet protocols. ||
	|| `enable_notifications` || boolean || False || If set, you may get connection/disconnection notification and connectionConfirm/Error notification messages || ||
	|| `default_sut_address` || string (ip:port) || None || If set, used as a default SUT address if none provided by the user || ||
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

		try:
			# Split a ip:port to a (ip, port)
			t = sutAddress.split(':')
			addr = (t[0], int(t[1]))
		except:
			raise Exception("Invalid or missing SUT Address when sending a message")


		# First look for an existing connection
		conn = self._getConnection(addr)

		if (isinstance(message, tuple) or isinstance(message, list)) and len(message) == 2:
			cmd, _ = message
			if cmd == "connectionRequest":
				conn = self._connect(addr)
			elif cmd == "disconnectionRequest":
				self._disconnect(addr, "disconnected by local user")
			else:
				raise Exception("Unsupported request (%s)" % cmd)
		
		elif isinstance(message, basestring):
			if not conn:
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
	
	def _connect(self, to):
		"""
		Creates an TCP connection to the to address (ip, port),
		then registers the connection.
		"""
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
			sock.bind((self['local_ip'], self['local_port']))
			# Blocking (for now)
			sock.connect(to)
			conn = self._registerOutgoingConnection(sock, to)
		except Exception, e:
			if self['enable_notifications']:
				self.triEnqueueMsg(('connectionError', str(e)), "%s:%s" % to)
			else:
				raise e
		if self['enable_notifications']:
			self.triEnqueueMsg(('connectionConfirm', None), "%s:%s" % to)
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
		self.logSentPayload("TCP data", data)
		conn.socket.send(data)

	def _disconnect(self, addr, reason):
		self.getLogger().info("Disconnectiong from %s, reason: %s" % (addr, reason))
		self._lock()
		if addr in self._connections:
			conn = self._connections[addr]
			del self._connections[addr]
		self._unlock()

		conn.socket.close()
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
		addr = (self['listening_ip'], self['listening_port'])
		self.getLogger().info("Starting listening on %s" % (str(addr)))
		
		# Should be mutex-protected
		try:
			self._listeningSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
			self._listeningSocket.bind(addr)
			self._listeningSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self._listeningSocket.listen(10)
		except Exception, e:
			raise e
	
	def _stopListening(self):
		self._disconnectIncomingConnections()
		# Should be mutex-protected
		if self._listeningSocket:
			self.getLogger().info("Stopping listening...")
			self._listeningSocket.close()
			self._listeningSocket = None
	
	def _startPollingThread(self):
		if not self._pollingThread:
			self._pollingThread = PollingThread(self)
			self._pollingThread.start()

	def _stopPollingThread(self):
		if self._pollingThread:
			self._pollingThread.stop()
			self._pollingThread = None

	##
	# Interface to be plugable on a PollingThread
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
					self.logReceivedPayload("TCP data", msg)
					self.triEnqueueMsg(msg, "%s:%s" % addr)
			elif separator is not None:
				msgs = conn.buffer.split(separator)
				for msg in msgs[:-1]:
					self.logReceivedPayload("TCP data", msg)
					self.triEnqueueMsg(msg, "%s:%s" % addr)
				conn.buffer = msgs[-1]
			else:
				msg = conn.buffer
				conn.buffer = ''
				# No separator or size criteria -> send to userland what we received according to the tcp stack
				self.logReceivedPayload("TCP data", msg)
				self.triEnqueueMsg(msg, "%s:%s" % addr)

	def _onIncomingConnection(self, sock, addr):
		self._registerIncomingConnection(sock, addr)
		if self['enable_notifications']:
			self.triEnqueueMsg(('connectionNotification', None), "%s:%s" % addr)

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
							self._probe._onIncomingConnection(sock, addr)
							# Raise a new connection notification event - soon
						else:
							addr = s.getpeername()
							self._probe.getLogger().debug("New data to read from %s" % str(addr))
							data = s.recv(65535)
							if not data:
								self._probe.getLogger().debug("%s disconnected by peer" % str(addr))
								self._probe._disconnect(addr, reason = "disconnected by peer")
							else:
								# New received message.
								self._probe._feedData(addr, data)

					except Exception, e:
						self._probe.getLogger().warning("exception while polling active/listening sockets: %s" % str(e))
					
			except Exception, e:
				self._probe.getLogger().warning("exception while polling active/listening sockets: %s" % str(e))
				# Avoid 100% CPU usage when select() raised an error
				time.sleep(0.01)	
					


ProbeImplementationManager.registerProbeImplementationClass('tcp', TcpProbe)
