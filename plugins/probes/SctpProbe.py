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
# An SCTP basic probe.
#
##

import ProbeImplementationManager

import select
import socket
import sys
import threading

# WARNING: test only !!
#IPPROTO_SCTP = socket.IPPROTO_TCP

# socket does not contain this on all Python versions.
try:
	IPPROTO_SCTP = socket.IPPROTO_SCTP
except:
	IPPROTO_SCTP = 132

class Connection:
	def __init__(self):
		self.socket = None
		self.incoming = False
		self.peerAddress = None

class SctpProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	
	Properties:
	|| `local_ip` || string || (empty - system assigned) || Local IP address to use when sending packets ||
	|| `local_port` || integer || 0 (system assigned) || Local port to use when sending packets ||
	|| `listening_ip` || string || 0.0.0.0 || Listening IP address, if listening mode is activated (see below) ||
	|| `listening_port` || integer || 0 || Set it to a non-zero port to start listening on mapping ||
	|| `style` || string in 'tcp', 'udp' || 'tcp' || SCTP style: UDP (...) or TCP (stream)
	|| `` || || ||
	|| `` || || ||
	|| `` || || ||
	
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
		self.setDefaultProperty('style', 'tcp')
		self.setDefaultProperty('timeout', 0)
		self.setDefaultProperty('maxsize', 0)
		self.setDefaultProperty('separator', None)

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

		try:
			# Split a ip:port to a (ip, port)
			t = sutAddress.split(':')
			addr = (t[0], int(t[1]))
		except:
			raise Exception("Invalid or missing SUT Address when sending a message")

		# First look for an existing connection
		conn = self._getConnection(addr)

		if not conn:
			conn = self._connect(addr)

		# Now we can send our payload
		self._send(conn, message)
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def _connect(self, to):
		"""
		Creates an SCTP connection to the to address (ip, port),
		then registers the connection.
		"""
		style = socket.SOCK_STREAM
		if self['style'] == 'udp':
			style = socket.SOCK_SEQPACKET
		try:
			sock = socket.socket(socket.AF_INET, style, IPPROTO_SCTP)
			sock.bind((self['local_ip'], self['local_port']))
			# Blocking (for now)
			sock.connect(to)
			conn = self._registerOutgoingConnection(sock, to)
			# Connection notification ?
		except Exception, e:
			raise e
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
		self.logSentPayload("SCTP data", data)
		conn.socket.send(data)

	def _disconnect(self, addr, reason):
		self.getLogger().info("Disconnectiong from %s, reason: %s" % (addr, reason))
		self._lock()
		if addr in self._connections:
			conn = self._connections[addr]
			del self._connections[addr]
		self._unlock()

		conn.socket.close()
		# Disconnection notification ?
	
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
		self.getLogger().info("Starting listening on %s, using style %s" % (addr, self['style']))
		style = socket.SOCK_STREAM
		if self['style'] == 'udp':
			style = socket.SOCK_SEQPACKET
		
		# Should be mutex-protected
		try:
			self._listeningSocket = socket.socket(socket.AF_INET, style, IPPROTO_SCTP)
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
			# (maxsize, timeout, ...)
			self.logReceivedPayload("SCTP data", data)
			self.triEnqueueMsg(data, "%s:%s" % addr)


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
			listening = self._probe._getListeningSockets()
			active = self._probe._getActiveSockets()
			rset = listening + active
			
			r, w, e = select.select(rset, [], [], 0.001)
			for s in r:
				try:
					if s in listening:
						self._probe.getLogger().debug("Accepting a new connection")
						(sock, addr) = s.accept()
						self._probe._registerIncomingConnection(sock, addr)
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
					


ProbeImplementationManager.registerProbeImplementationClass('sctp', SctpProbe)
