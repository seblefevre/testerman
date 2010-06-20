#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2010 Sebastien Lefevre and other contributors
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
# Testerman (python) Agent installer.
#
# A standalone executable that connects to an Agent Controller
# and download a particular PyAgent version in a target directory.
##

import time
import os
import sys
import logging
import cStringIO as StringIO
import tarfile
import optparse
import Queue
import re
import base64
import zlib
import cPickle as pickle
import threading
import select
import socket

VERSION = "1.0.0"

def getVersion():
	return VERSION

# When served through the Testerman Server web pages,
# these defaults are overwritten on the fly
DEFAULT_TACS_IP = "127.0.0.1"
DEFAULT_TACS_PORT = 40000

################################################################################
# Imported from TestermanMessages
################################################################################


# Message separator.
# On reference perf tests, 8% faster when using \n instead of \r\n.
SEPARATOR = '\n'

URI_REGEXP = re.compile(r'(?P<scheme>[a-z]+):((?P<user>[a-zA-Z0-9_\.-]+)@)?(?P<domain>[a-zA-Z0-9_\./%-]+)')
HEADERLINE_REGEXP = re.compile(r'(?P<header>[a-zA-Z0-9_-]+)\s*:\s*(?P<value>.*)')
REQUESTLINE_REGEXP = re.compile(r'(?P<method>[a-zA-Z0-9_-]+)\s*(?P<uri>[^\s]*)\s*(?P<protocol>[a-zA-Z0-9_-]+)/(?P<version>[0-9\.]+)')
STATUSLINE_REGEXP = re.compile(r'(?P<status>[0-9]+)\s*(?P<reason>.*)')

class Messages:
	class Uri(object):
		"""
		Testerman URI object.

		Encode/decode uri of the form:
		<scheme>:[<user>@]<domain>
		"""
		def __init__(self, uri):
			self.scheme = None
			self.user = None
			self.domain = None
			self.parse(uri)

		def parse(self, uri):
			m = URI_REGEXP.match(uri)
			if not m:
				raise Exception("Invalid URI format (%s)" % uri)
			self.setScheme(m.group('scheme'))
			self.setDomain(m.group('domain'))
			self.setUser(m.group('user')) # allows setting it to None

		def setScheme(self, scheme):
			self.scheme = scheme

		def setUser(self, user):
			self.user = user

		def setDomain(self, domain):
			self.domain = domain

		def getScheme(self):
			return self.scheme

		def getUser(self):
			return self.user

		def getDomain(self):
			return self.domain

		def __str__(self):
			if self.user:
				return "%s:%s@%s" % (self.scheme, self.user, self.domain)
			else:
				return "%s:%s" % (self.scheme, self.domain)


	class Message(object):
		"""
		Base message implemented by Testerman messages
		(requests, notifications, responses)
		"""

		TYPE_REQUEST = "request"
		TYPE_NOTIFICATION = "notification"

		ENCODING_UTF8 = "utf-8"
		ENCODING_BASE64 = "base64"

		CONTENT_TYPE_PYTHON_PICKLE = "application/x-python-pickle" # specific type
		CONTENT_TYPE_GZIP = "application/x-gzip"

		def __init__(self):
			self.headers = {} # dict of str of unicode
			self.body = None # unicode or datastring

		def setHeader(self, header, value):
			if value is None:
				return
			if not isinstance(value, basestring):
				value = str(value)
			self.headers[header] = value.encode('utf-8')

		def getHeader(self, header):
			return self.headers.get(header, None)

		def setBody(self, body):
			"""
			Sets the body directly.
			"""
			self.body = body

		def setApplicationBody(self, body, profile = CONTENT_TYPE_PYTHON_PICKLE):
			"""
			Convenience function: encode the body, sets
			both Content-Encoding ad Content-Type as JSON or pickle encoding.
			"""
			if profile == self.CONTENT_TYPE_PYTHON_PICKLE:
				self.body = pickle.dumps(body)
				self.setContentEncoding(self.ENCODING_UTF8)
				self.setContentType(self.CONTENT_TYPE_PYTHON_PICKLE)
			elif profile == self.CONTENT_TYPE_GZIP:
				self.body = base64.encodestring(zlib.compress(body))
				self.setContentEncoding(self.ENCODING_BASE64)
				self.setContentType(self.CONTENT_TYPE_GZIP)
			else:
				raise Exception("Invalid application body encoding profile (%s)" % str(profile))

		def getBody(self):
			return self.body

		def isResponse(self):
			return False

		def isNotification(self):
			return False

		def isRequest(self):
			return False

		def getContentEncoding(self):
			return self.headers.get("Content-Encoding", self.ENCODING_UTF8)

		def getContentType(self):
			return self.headers.get("Content-Type", None)

		def setContentEncoding(self, encoding):
			self.headers["Content-Encoding"] = encoding

		def setContentType(self, contentType):
			self.headers["Content-Type"] = contentType

		def getApplicationBody(self):
			"""
			According to Content-Encoding and Content-Type, tries to decode the body.
			Returns the raw body if the content encoding or type were unknown.
			"""	
			contentType = self.getContentType()
			contentEncoding = self.getContentEncoding()

			# Raw body
			body = self.getBody()
			# First handle the encoding part
			if contentEncoding == self.ENCODING_UTF8:
				body = body.decode('utf-8')
			elif contentEncoding == self.ENCODING_BASE64:
				body = base64.decodestring(body)

			# Then turn the content type into something higher level
			if contentType == self.CONTENT_TYPE_PYTHON_PICKLE:
				ret = pickle.loads(self.getBody())
				return ret
			elif contentType == self.CONTENT_TYPE_GZIP:
				ret = zlib.decompress(body)
				return ret
			else:
				# No application decoding, but encoding decoding done.
				return body

		def getTransactionId(self):
			try:
				return int(self.headers["Transaction-Id"])
			except:
				return None


	class Request(Message):
		def __init__(self, method, uri, protocol, version):
			"""
			@type  uri: Uri
			"""
			Messages.Message.__init__(self)
			self.method = method
			if isinstance(uri, basestring):
				self.uri = Messages.Uri(uri)
			else:
				self.uri = uri
			self.protocol = protocol
			self.version = version
			self.setHeader('Type', Messages.Message.TYPE_REQUEST)

		def __str__(self):
			"""
			Encodes a message to a utf-8 string.
			The final \00 is not part of the message, but just a transport separator.
			"""
			ret = [ "%s %s %s/%s" % (self.method, str(self.uri), self.protocol, self.version) ]
			for (h, v) in self.headers.items():
				ret.append("%s: %s" % (h, v.encode('utf-8')))
			ret.append('')
			if self.body:
				if self.getContentEncoding() == self.ENCODING_UTF8:
					ret.append(self.body) #.encode('utf-8')
				else:
					ret.append(self.body)
			return SEPARATOR.join(ret)

		def getUri(self):
			return self.uri

		def getMethod(self):
			return self.method

		def getProtocol(self):
			return self.protocol

		def getVersion(self):
			return self.version

		def makeRequest(self):
			self.setHeader('Type', Messages.Message.TYPE_REQUEST)

		def makeNotification(self):
			self.setHeader('Type', Messages.Message.TYPE_NOTIFICATION)

		def isRequest(self):
			return self.headers.has_key("Type") and self.headers["Type"] == Messages.Message.TYPE_REQUEST

		def isNotification(self):
			return self.headers.has_key("Type") and self.headers["Type"] == Messages.Message.TYPE_NOTIFICATION


	class Notification(Request):
		def __init__(self, method, uri, protocol, version):
			Request.__init__(self, method, uri, protocol, version)
			self.makeNotification()

	class Response(Message):
		def __init__(self, statusCode, reasonPhrase):
			Messages.Message.__init__(self)
			self.statusCode = int(statusCode)
			self.reasonPhrase = reasonPhrase

		def __str__(self):
			"""
			Encodes a message to a utf-8 string.
			The final \00 is not part of the message, but just a transport separator.
			"""
			ret = [ "%s %s" % (str(self.statusCode), str(self.reasonPhrase)) ]
			for (h, v) in self.headers.items():
				ret.append("%s: %s" % (h, v.encode('utf-8')))
			ret.append("")
			if self.body:
				if self.getContentEncoding() == self.ENCODING_UTF8:
					ret.append(self.body) #.encode('utf-8')
				else:
					ret.append(self.body)
			return SEPARATOR.join(ret)

		def getStatusCode(self):
			return self.statusCode

		def getReasonPhrase(self):
			return self.reasonPhrase

		def isResponse(self):
			return True

##
# Main message creator from data
##
def parseMessage(data):
	"""
	Parses data into a Message (either a Notification, Request, Response, actually).
	Raises an exception in case of an invalid message.
	"""
	lines = data.split(SEPARATOR)

	# request line, for request and notifications
	m = REQUESTLINE_REGEXP.match(lines[0])
	if m:
		# This is a request
		message = Messages.Request(method = m.group('method').upper(), uri = Messages.Uri(m.group('uri')), protocol = m.group('protocol'), version = m.group('version'))

	else:
		m = STATUSLINE_REGEXP.match(lines[0])
		if not m:
			raise Exception("Invalid message first line (%s) - not a response, not a request" % str(lines[0]))
		# This is a response
		message = Messages.Response(statusCode = m.group('status'), reasonPhrase = m.group('reason'))

	# Common part: headers parsing, body parsing.
	i = 1
	for header in lines[1:]:
		i += 1
		l = header.strip()
		if not header:
			break # reached body
		m = HEADERLINE_REGEXP.match(l)
		if m:
			message.setHeader(m.group('header'), m.group('value').decode('utf-8'))
		else:
			raise Exception("Invalid header in message (%s)" % str(l))

	# Body - raw, no additional decoding or interpretation.
	# use getApplicationBody() for that.
	message.setBody(SEPARATOR.join(lines[i:]))

	# OK, we're done.
	return message


################################################################################
# Imported from TestermanNodes
################################################################################

KEEP_ALIVE_PDU = ''


class TcpPacketizerClientThread(threading.Thread):
	"""
	Simple TCP client that keeps reconnecting to a server.
	It also sends "packets" separated with a single terminator character, 
	and packetizes incoming stream, too.
	
	Once constructed, you may use:
		start()
		stop()
		send_packet(packet)
	from any thread,
	and reimplement:
		on_connection()
		on_disconnection()
		handle_packet(packet)
		log(txt)
	"""

	terminator = '\x00'

	def __init__(self, server_address, local_address = ('', 0), reconnection_interval = 1.0, inactivity_timeout = 30.0, keep_alive_interval = 20.0):
		"""
		The callback is called on new event: callback(event)
		"""
		threading.Thread.__init__(self)
		self.serverAddress = server_address
		self.localAddress = local_address

		self.stopEvent = threading.Event()
		self.reconnectInterval = reconnection_interval
		self.socket = None
		self.buf = ''
		self.queue = Queue.Queue(0)
		self.connected = False
		self.inactivity_timeout = inactivity_timeout
		self.last_activity_timestamp = time.time() # incoming activity only
		self.keep_alive_interval = keep_alive_interval
		self.last_keep_alive_timestamp = time.time()
		# a "control port" that is used to notify the low-level that
		# a message is ready to send (if the associated sending queue is not empty)
		# or just to exit our polling loop (stop notification).
		self.control_read, self.control_write = os.pipe()
		
	def __del__(self):
		os.close(self.control_read)
		os.close(self.control_write)

	def run(self):
		self.trace("Tcp client started, connecting from %s to %s" % (str(self.localAddress), str(self.serverAddress)))
		while not self.stopEvent.isSet():
			try:
				self.buf = ''
				# Keep connected
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.socket.bind(self.localAddress)
				self.socket.setblocking(False)
				try:
					self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
				except:
					# socket.SOL_TCP not defined in Jython (??)
					pass
				try:
					# Warning: Python 2.3+
					self.socket.settimeout(5.0)
				except:
					# Python 2.2 degraded support
					pass

				self.socket.connect(self.serverAddress)
				# Previous method to implement a timeout (was not working under windows, we got an error 10035 instead of a EINPROGRESS):
#				ret = self.socket.connect_ex(self.serverAddress)
#				if ret > 0 and ret != errno.EINPROGRESS:
#					raise Exception("socket error %d (%s)" % (ret, os.strerror(ret)))
#				# We wait for the connection to be done
#				r, w, e = select.select( [ self.socket ], [ self.socket ], [], 5)
#				if not self.socket in w:
#					# Timeout while connecting.
#					# This is a bit useless. If we were not able to connect a first time in 5s, why will it be ok on a next attempt ?
#					# Anyway, this will send a SYN immediately again.
#					raise Exception("Connection timed out. Attempting reconnection...")
				# OK, we are connected. Let's raise our connection callback.
				self.trace("Connected.")
				self.connected = True
				self.on_connection()
				# Polling loop
				self.__main_receive_send_loop()
			except Exception, e:
				try:
					self.trace("Trying to reconnect in %ds..." % self.reconnectInterval)
					if self.connected:
						self.connected = False
						try:
							self.on_disconnection()
						except:
							pass
					time.sleep(self.reconnectInterval)
					self.socket.close()
				except:
					pass

		try:
			self.socket.close()
			if self.connected:
				self.connected = False
				self.on_disconnection()
		except:
			pass
		self.trace("Tcp client stopped.")

	def __main_receive_send_loop(self):
		self.last_keep_alive_timestamp = time.time()
		self.last_activity_timestamp = time.time()

		write_socket = []

		timeout = -1
		if self.inactivity_timeout:
			timeout = self.inactivity_timeout

		if self.keep_alive_interval and self.keep_alive_interval < timeout:
			timeout = self.keep_alive_interval

		while not self.stopEvent.isSet():
			try:
				if timeout >= 0:
					r, w, e = select.select([ self.socket, self.control_read ], write_socket, [ self.socket ], timeout)
				else:
					r, w, e = select.select([ self.socket, self.control_read ], write_socket, [ self.socket ])

				# Received an error from the network
				if self.socket in e:
					raise EOFError("Socket select error: disconnecting")

				# Received a message from the network
				if self.socket in r:
					read = self.socket.recv(65535)
					if not read:
						raise EOFError("Nothing to read on read event: disconnecting")
					self.last_activity_timestamp = time.time()
					self.buf = ''.join([self.buf, read]) # faster than += r
					self.__on_incoming_data()

				# Received a send or stop notification from the higher level layers
				if self.control_read in r:
					# Consume the notification(s), if any, to avoid a pipe overflow.
					os.read(self.control_read, 10000)
					# If the queue is not empty, we assume this is a send notification.
					# In this case, we first try to send messages now, not waiting for the next loop iteration
					# This way, we avoid leaving some important messages in the sending queue while
					# shutting down a TE (in particular). In such a case, we won't have a next iteration
					# as the stopEvent is already set.
					# The trade-off is that we can't wait forever here as we may have incoming messages
					# to consume.
					while not self.queue.empty():
						_, ready, error = select.select([], [ self.socket ], [ self.socket ], 0.01)
						if self.socket in error:
							raise EOFError("Socket select error when sending a message: disconnecting")
						elif self.socket in ready:
							try:
								message = self.queue.get(False)
								self.socket.sendall(message)
							except Queue.Empty:
								pass
							except Exception, e:
								self.trace("Unable to send message: " + str(e))
						else:
							# Not ready yet. Will perform a new attempt on next main loop iteration.
							# (which may never occur if we also set the stopEvent in the meantime)
							if not(self.socket in write_socket):
								write_socket.append(self.socket)
							break # do not spend more time trying to send any messages.
					
				# We have something to send, and during the previous loop iteration
				# we registered the socket in write mode to get notified when ready to
				# send the messages.		
				if self.socket in w:
					while not self.queue.empty():
						try:
							message = self.queue.get(False)
							self.socket.sendall(message)
						except Queue.Empty:
							pass
						except Exception, e:
							self.trace("Unable to send message: " + str(e))
					# No more enqueued messages to send - we don't need to wait for
					# the network socket to be writable anymore.
					write_socket = []
	
				current_time = time.time()

				if not r and not w and not e:
					# Check inactivity timeout 
					if self.inactivity_timeout:
						if current_time - self.last_activity_timestamp > self.inactivity_timeout:
							raise EOFError("Inactivity timeout: disconnecting")

					# Send (queue) a Keep-Alive if needed
					if self.keep_alive_interval:
						if current_time - self.last_keep_alive_timestamp > self.keep_alive_interval:
							self.last_keep_alive_timestamp = time.time()
							self.trace("Sending Keep Alive")
							self.send_packet(KEEP_ALIVE_PDU)

				timeout = -1
				if self.inactivity_timeout :
					tmp = self.inactivity_timeout - current_time - self.last_activity_timestamp
					if tmp >= 0:
						timeout = min(timeout, tmp)

				if self.keep_alive_interval:
					tmp = current_time - self.last_keep_alive_timestamp - self.keep_alive_interval
					if tmp >= 0:
						timeout = min(timeout, tmp)

			except EOFError, e:
				self.trace("Disconnected by peer.")
				raise e # We'll reconnect.

			except socket.error, e:
				self.trace("Low level error: " + str(e))
				raise e # We'll reconnect

			except Exception, e:
				self.trace("Exception in main pool for incoming data: " + str(e))
				pass

	def __on_incoming_data(self):
		pdus = self.buf.split(self.terminator)
		for pdu in pdus[:-1]:
			if not pdu == KEEP_ALIVE_PDU:
				self.handle_packet(pdu)
			else:
				self.trace("Received Keep Alive")
		self.buf = pdus[-1]

	def stop(self):
		self.stopEvent.set()
		# This will force our blocking select to wake up in our main loop
		os.write(self.control_write, 'b')
		self.join()

	def send_packet(self, packet):
		self.queue.put(packet + self.terminator)
		os.write(self.control_write, 'a')
	
	def disconnect(self):
		try:
			self.socket.close()
		except:
			pass

	##
	# Methods to reimplement (typically)
	##

	def handle_packet(self, packet):
		"""
		Called when a new packet arrived on the connection.
		You should not do nothing blocking in this function.
		Post a message somewhere to switch threads, if you need to.
		"""
		pass
	
	def on_connection(self):
		"""
		Called when the tcp connection to the server is established.
		You should not do nothing blocking in this function.
		Post a message somewhere to switch threads, if you need to.
		"""
		pass

	def on_disconnection(self):
		"""
		Called when the tcp connection to the server has been dropped,
		either by the local or the remote peer.
		You should not do nothing blocking in this function.
		Post a message somewhere to switch threads, if you need to.
		"""
		pass

	def trace(self, txt):
		"""
		Called whenever a debug trace should be dumped.
		"""
		pass

################################################################################
# Connectors (low-level tcp server or reconnecting client)
################################################################################

class IConnector:
	"""
	Connector interface.
	"""
	def __init__(self):
		self._onMessageCallback = None
		self._onTraceCallback = None
		self._onConnectionCallback = None
		self._onDisconnectionCallback = None
	
	def setConnectionCallback(self, callback):
		"""
		@type  callback: function (channel, message)
		@param callback: the callback to call when a channel is connected
		
		callback should not be blocking.
		"""
		self._onConnectionCallback = callback
	
	def setDisconnectionCallback(self, callback):
		"""
		@type  callback: function (channel, message)
		@param callback: the callback to call when a channel is disconnected
		
		callback should not be blocking.
		"""
		self._onDisconnectionCallback = callback

	def setMessageCallback(self, callback):
		"""
		@type  callback: function (channel, message)
		@param callback: the callback to call when receiving a message.
		
		callback should not be blocking.
		"""
		self._onMessageCallback = callback
	
	def setTraceCallback(self, callback):
		"""
		Sets a callback(string) callback for traces.
		"""
		self._onTraceCallback = callback

	def sendMessage(self, channel, message):
		"""
		Call this when you want to send a message (packet) through a (connected) channel.
		
		@type  message: string/buffer
		@param message: the raw message/packet to send.
		"""
		pass
		
	def disconnect(self, channel):
		"""
		Call this when you want to disconnected a (connected) channel.
		"""
		pass
	
	def getLocalAddress(self):
		"""
		Returns the local address (address, port)
		"""
		return ('', 0)

class ConnectingConnectorThread(TcpPacketizerClientThread, IConnector):
	"""
	A IConnector implementation as a reconnecting thread, based on the TcpPacketizerClientThread.
	
	When using such a connector, you should set up several callbacks to get low-level events:
	 setConnectionCallback(cb(channel))
	 setMessageCallback(cb(channel, TestermanMessages.Message))
	 setTracer(cb(string))
	"""
	def __init__(self, serverAddress, localAddress = None):
		TcpPacketizerClientThread.__init__(self, serverAddress, local_address = localAddress)
		IConnector.__init__(self)
	
	def on_connection(self):
		"""
		Reimplemented from TcpPacketizerClientThread
		"""
		if callable(self._onConnectionCallback):
			self._onConnectionCallback(0)

	def on_disconnection(self):
		"""
		Reimplemented from TcpPacketizerServerThread
		"""
		if callable(self._onDisconnectionCallback):
			self._onDisconnectionCallback(0)

	def handle_packet(self, packet):
		"""
		Reimplemented from TcpPacketizerClientThread
		"""
		# Tries to parse the packet.
		# If ok, raise it to higher levels.
		try:
			message = parseMessage(packet)
			if callable(self._onMessageCallback):
				self._onMessageCallback(0, message)
		except Exception, e:
			self.trace("Exception while reading message: " + str(e))
			pass

	def trace(self, txt):
		"""
		Reimplemented from TcpPacketizerClientThread
		"""
		if self._onTraceCallback:
			self._onTraceCallback(txt)

	def sendMessage(self, channel, message):
		"""
		Reimplemented for IConnector
		"""
		self.trace("sendMessage from ConnectingThread")
		self.send_packet(str(message))

	def disconnect(self, channel):
		return
		# disconnection is not clean at connector level, 
		# leading to a prematurate thread exit without a join().
		TcpPacketizerClientThread.disconnect(self)

	def getLocalAddress(self):
		ret = self.localAddress
		s = self.socket
		if s:
			try:
				ret = s.getsockname()
			except:
				pass
		return ret
	

################################################################################
# The Peer Node.
################################################################################

class BaseNode(object):
	"""
	A Transaction Manager.
	Also injects additional basic info (such as the user-agent, contact).
	
	Responsible for adding/checking transaction IDs in messages,
	manages retransmissions (not supported yet in the Testerman base protocol).
	
	Public:
	start()
	stop()
	setConnector(IConnector)
	initialize()
	finalize()
	getNodeName()
	getUserAgent()
	executeRequest()
	sendRequest()
	sendNotification()
	sendResponse()
	
	To reimplement in your own nodes:
	(it is safe to implement blocking behaviours if needed)
	onDisconnection
	onConnection
	onRequest
	onNotification
	onResponse
	
	"""
	
	class AdapterThread(threading.Thread):
		"""
		Thread Adaptation layer:
		when a message or event comes from the lower levels (connector/network layers),
		switch to another thread through this adapter so that event handlers
		can be blocking.
		"""
		def __init__(self):
			threading.Thread.__init__(self)
			self._queue = Queue.Queue(0)
			self._running = False

		def postCallback(self, cb):
			self._queue.put(cb)

		def run(self):
			self._running = True
			while self._running:
				try:
					cb = self._queue.get()
					cb()
				except Queue.Empty:
					pass
				except Exception, e:
					pass

		def _stop(self):
			self._running = False

		def stop(self):
			self.postCallback(self._stop)
			self.join()
	
	def __init__(self, name, userAgent):
		"""
		@type  connector: Connector
		"""
		self._connector = None
		self.__userAgent = userAgent
		self.__name = name
		self.__mutex = threading.RLock()
		self.__transactionId = 0
		self.__outgoingTransactions = {} # transactionId: { request, timestamp, channel, callback }
		self.__incomingTransactions = {} # transactionId: { request, timestamp, channel, callback }
		if self.__name is None:
			# Generates a unique name
			self.__name = "%d.%s" % (os.getpid(), socket.getfqdn())
		self.__adapterThread = None
		self.__adapterThread2 = None
		self.__started = False
	
	def __trace(self, txt):
		self.trace("[TransactionManager] " + txt)

	def __getNewTransactionId(self):
		self.__mutex.acquire()
		self.__transactionId += 1
		ret = self.__transactionId
		self.__mutex.release()
		return ret

	##
	# Thread switchers.
	# Thread policy to avoid reentrances without managing full state machines
	# at application levels:
	# - upon incoming event, we can execute one outgoing request (at the same time).
	# To do this, incoming events (connection, requests, notifications) are dispatched
	# in one thread, while responses are dispatched in another thread.
	##
	def __onConnection(self, channel):
		self.__adapterThread2.postCallback(lambda: self.onConnection(channel))

	def __onRequest(self, channel, transactionId, message):
		self.__adapterThread2.postCallback(lambda: self.onRequest(channel, transactionId, message))

	def __onNotification(self, channel, message):
		self.__adapterThread2.postCallback(lambda: self.onNotification(channel, message))

	def __onDisconnection(self, channel):
		self.__adapterThread.postCallback(lambda: self.onDisconnection(channel))

	def __onResponse(self, channel, transactionId, message):
		self.__adapterThread.postCallback(lambda: self.onResponse(channel, transactionId, message))

	def __onMessage(self, channel, message):
		if message.isRequest():
			transactionId = message.getTransactionId()
			self.__trace("%d <-- received request" % (transactionId))
			self.__trace("\n" + repr(message))
			self.__onRequest(channel, transactionId, message)
		elif message.isNotification():
			transactionId = message.getTransactionId()
			self.__trace("%d <-- received notification" % (transactionId))
			self.__trace("\n" + repr(message))
			self.__onNotification(channel, message)
		elif message.isResponse():
			transactionId = message.getTransactionId()
			self.__mutex.acquire()
			if self.__outgoingTransactions.has_key(transactionId):
				entry = self.__outgoingTransactions[transactionId]
				# Synchronous call ?
				if entry['event']:
					# Yes: notify the caller, let him purge the transaction with the response.
					self.__outgoingTransactions[transactionId]['response'] = message
					entry['event'].set()
				else:
					# No: purge the transaction, then call onResponse()
					del self.__outgoingTransactions[transactionId]
				self.__mutex.release()
				self.__trace("%d <-- received response - took %fs" % (transactionId, time.time() - entry['timestamp']))
				self.__trace("\n" + repr(message))
				if not entry['event']:
					self.__onResponse(channel, transactionId, message)
			else:
				self.__mutex.release()
				self.__trace("%d <-- response to unknown transaction ID - late response ?" % transactionId)
				self.__trace("\n" + repr(message))
				return
		else:
			self.__trace("Got an unknown message type - nothing to do")
	
	##
	# Protected
	##
	def _setConnector(self, connector):
		self._connector = connector
		self._connector.setMessageCallback(self.__onMessage)
		self._connector.setConnectionCallback(self.__onConnection)
		self._connector.setDisconnectionCallback(self.__onDisconnection)
		self._connector.setTraceCallback(lambda x: self.__trace("[connector] " + x))

	##
	# Public methods
	##
	def getUserAgent(self):
		return self.__userAgent

	def getContact(self):
		return self._connector.getLocalAddress()[0]
	
	def getNodeName(self):
		return self.__name
	
	def start(self):
		if not self.__started:
			self.trace("Starting node %s..." % self.getNodeName())
			self.__adapterThread = self.AdapterThread()
			self.__adapterThread.start()
			self.__adapterThread2 = self.AdapterThread()
			self.__adapterThread2.start()
			self._connector.start()
			self.__started = True
	
	def stop(self):
		if self.__started:
			self.trace("Stopping node %s..." % self.getNodeName())
			self._connector.stop()
			self.__adapterThread2.stop()
			self.__adapterThread.stop()
			self.__started = False

	def sendRequest(self, channel, request):
		"""
		Aynchronously sends a request.
		Finish the request preparation with the node and transaction-related stuff:
		- user agent, node name,
		- transaction ids
		- message type, etc
		Prepares to get a response for this request.
		
		@type  request: Messages.Request
		@param request: the request object to send. 
		"""
		# Generate a req ID
		transactionId = self.__getNewTransactionId()
		request.setHeader("Transaction-Id", transactionId)
		request.setHeader("User-Agent", self.getUserAgent())
		request.setHeader("Contact", self.getContact())
		# Register the request
		self.__mutex.acquire()
		self.__outgoingTransactions[transactionId] = { 'request': request, 'timestamp': time.time(), 'channel': channel, 'event': None }
		self.__mutex.release()
		# Send the message
		self.__trace("%d --> sending request" % (transactionId))
		self.__trace("\n" + str(request))
		self._connector.sendMessage(channel, request)
		return transactionId

	def executeRequest(self, channel, request, responseTimeout = 10.00):
		"""
		Synchronous request execution.
		During this execution, all incoming requests or responses are deferred
		until the request is complete (or timed out).
		"""
		self.__trace("--> preparing request")
		# Generate a req ID
		transactionId = self.__getNewTransactionId()
		request.setHeader("Transaction-Id", transactionId)
		request.setHeader("User-Agent", self.getUserAgent())
		request.setHeader("Contact", self.getContact())
		event = threading.Event()
		startTime = time.time()
		# Register the request
		self.__mutex.acquire()
		self.__outgoingTransactions[transactionId] = { 'request': request, 'timestamp': startTime, 'channel': channel, 'event': event }
		self.__mutex.release()
		# Send the message
		self.__trace("%d --> sending request" % (transactionId))
		self.__trace("\n" + str(request))
		self._connector.sendMessage(channel, request)
		self.__trace("%d --> sent request" % (transactionId))
		# Now, wait for the response.		

		# I tried several implementation here.
		
		# Implementation #1: clean event.wait(): ref test (perf_test.ats): 25s
		# event.wait(responseTimeout)
		# if event.isSet():
		
		# Implementation #2: using a dedicated reply queue instead of an event.
		# The response is directly posted in the queue - even not a need for
		# locking the outgoingTransactions map to retrieve it.
		# Yet, this is about 25s on perf_test.ats.

		# Implementation #3: ugly loop, waiting for the event: ref test (perf_test.ats): 20s
		timeout = False
		while (not event.isSet()) and (not timeout):
			time.sleep(0.00001)
			if (time.time() - startTime) >= responseTimeout:
				timeout = True
		if not timeout:
			self.__trace("%d --- response received" % (transactionId))
			self.__mutex.acquire()
			response = self.__outgoingTransactions[transactionId]['response']
			ts = self.__outgoingTransactions[transactionId]['timestamp']
			del self.__outgoingTransactions[transactionId]
			self.__mutex.release()
			self.__trace("%d === response received on time on synchronous request (took %fs)" % (transactionId, time.time() - ts))
			return response
		else:
			# Purge the transaction
			self.__mutex.acquire()
			del self.__outgoingTransactions[transactionId]
			self.__mutex.release()
			self.__trace("%d === timeout on synchronous request, purging" % transactionId)
			return None

	def isStarted(self):
		# To mutex-protect
		return self.__started

	def sendNotification(self, channel, notification):
		"""
		Sends a notification.
		"""
		if not self.isStarted():
			return
		# Generate a req ID (useless for notification ?)
		transactionId = self.__getNewTransactionId()
		notification.setHeader("Transaction-Id", transactionId)
		notification.setHeader("User-Agent", self.getUserAgent())
		notification.setHeader("Contact", self.getContact())
		notification.makeNotification()
		# No callback to register
		# Send the message
		self.__trace("%d --> sending notification" % (transactionId))
		self.__trace("\n" + repr(notification))
		self._connector.sendMessage(channel, notification)
	
	def sendResponse(self, channel, transactionId, response):
		"""
		Sends a response.
		"""
		# We should check that the incomingTransactions table still contain a corresponding request, etc
		response.setHeader("Transaction-Id", transactionId)
		response.setHeader("User-Agent", self.getUserAgent())
		response.setHeader("Contact", self.getContact())
		# Send the message
		self.__trace("%d --> sending response" % (transactionId))
		self.__trace("\n" + repr(response))
		self._connector.sendMessage(channel, response)
	
	def disconnect(self, channel):
		self._connector.disconnect(channel)

	def initialize(self):
		self.__mutex.acquire()
		self.__outgoingTransactions = {}
		self.__incomingTransactions = {}
		self.__mutex.release()
	
	def finalize(self):
		# Some stats ?
		pass

	##
	# To reimplement in an actual Node implementation.
	##			
	def trace(self, txt):
		pass
	
	def onResponse(self, channel, transactionId, response):
		pass
	
	def onRequest(self, channel, transactionId, request):
		pass
	
	def onNotification(self, channel, notification):
		pass

	def onConnection(self, channel):
		pass
	
	def onDisconnection(self, channel):
		pass

################################################################################
# More high-level components
################################################################################

class ConnectingNode(BaseNode):
	"""
	Subclass this class if you want to create a client-oriented node.
	Just reimplement:
		onResponse(self, channel, transactionId, response)
		onRequest(self, channel, transactionId, request)
		onNotification(self, channel, notification)
	And possibly:
		onConnection(self, channel)
		onDisconnection(self, channel)
		
		trace(self, txt)
	
	You may then use:
		sendRequest(channel, request)
		sendResponse(channel, transactionId, response)
		sendNotification(channel, notification)
		
		initialize(serverAddress, localAddress)
		start()
		stop()
		finalize()
	"""
	def __init__(self, name, userAgent): # also manages protocol ?
		BaseNode.__init__(self, name, userAgent)
	
	def initialize(self, serverAddress, localAddress = ('', 0)):
		self.trace("Initializing connecting node %s: %s -> %s..." % (self.getNodeName(), localAddress, serverAddress))
		connector = ConnectingConnectorThread(serverAddress, localAddress)
		self._setConnector(connector)
		BaseNode.initialize(self)


def getBacktrace():
	import traceback
	import StringIO
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

################################################################################
# The Agent Installer
################################################################################

def getLogger():
	return logging.getLogger("PyAgent Installer")

class AgentInstaller(ConnectingNode):
	def __init__(self, name = None):
		ConnectingNode.__init__(self, name = name, userAgent = "PyTestermanAgentInstaller/%s" % getVersion())
		#: Declared probes, indexed by their name
		self.probes = {}
		# Xa channel id to communicate with the TACS
		self.channel = None
		#: current agent registration status
		self.registered = False

	def initialize(self, controllerAddress, localAddress):
		ConnectingNode.initialize(self, controllerAddress, localAddress)

	def getUri(self):
		return "agent:%s" % self.getNodeName()

	def request(self, request):
		response = self.executeRequest(self.channel, request)
		return response

	def getLogger(self):
		return getLogger()

	def getFile(self, url):
		"""
		"""
		self.getLogger().debug("Getting file %s..." % url)
		req = Messages.Request(method = "GET", uri = "system:tacs", protocol = "Xa", version = "1.0")
		req.setHeader('Path', url)
		response = self.request(req)
		if not response or response.getStatusCode() != 200:
			self.getLogger().debug("Getting file %s: request timeout or non-OK response code" % url)
			return None
		
		content = response.getApplicationBody()
		return content

	def getComponentVersions(self, component, branches = [ 'stable', 'testing', 'experimental' ]):
		"""
		Returns the available updates for a given component, with a basic filering on branches.
		
		Based on metadata stored into /updates.xml within the server's docroot:
		
		<updates>
			<update component="componentname" branch="stable" version="1.0.0" url="/components/componentname-1.0.0.tar">
				<!-- optional properties -->
				<property name="release_notes_url" value="/components/rn-1.0.0.txt />
				<!-- ... -->
			</update>
		</updates>
		
		@type  component: string
		@param component: the component identifier ("qtesterman", "pyagent", ...)
		@type  branches: list of strings in [ 'stable', 'testing', 'experimental' ], or None
		@param branches: the acceptable branches. If None, all branches are considered.
		
		@rtype: list of dict{'version': string, 'branch': string, 'url': string, 'properties': dict[string] of strings}
		@returns: versions info, as list ordered from the newer to the older. The url is a relative path from the docroot, suitable
		          for a subsequent getFile() to get the update archive.
		"""
		updates = None
		try:
			updates = self.getFile("/updates.xml")
			self.getLogger().debug("Updates file:\n%s" % updates)
		except Exception, e:
			self.getLogger().warning("Unable to fetch update metadata from TACS")
			print getBacktrace()
			return []
		if updates is None:
			return []
		
		
		ret = []
		# Now, parse the updates metadata
		import xml.dom.minidom
		import operator
		try:
		
			doc = xml.dom.minidom.parseString(updates)
			rootNode = doc.documentElement
			for node in rootNode.getElementsByTagName('update'):
				c = None
				branch = None
				version = None
				url = None
				if node.attributes.has_key('component'):
					c = node.attributes.get('component').value
				if node.attributes.has_key('branch'):
					branch = node.attributes.get('branch').value
				if node.attributes.has_key('version'):
					version = node.attributes.get('version').value
				if node.attributes.has_key('url'):
					url = node.attributes.get('url').value

				if c and c == component and url and version and (not branches or branch in branches):
					# Valid version detected. Add it to our return result
					entry = {'version': version, 'branch': branch, 'url': url, 'properties': {}}
					# Don't forget to add optional update properties
					for p in node.getElementsByTagName('property'):
						if p.attributes.has_key('name') and p.attribute.has_key('value'):
							entry['properties'][p.attributes['name']] = p.attributes['value']
					ret.append(entry)
		except Exception, e:
			self.getLogger().warning("Error while parsing update metadata file: %s" % str(e))
			ret = []

		# Sort the results
		ret.sort(key = operator.itemgetter('version'))
		ret.reverse()
		return ret

	def installComponent(self, url, basepath):
		"""
		Downloads the component file referenced by url, and installs it in basepath.
		
		@type  url: string
		@type  basepath: unicode string
		@param url: the url of the component archive to download, relative to the docroot
		"""
		# We retrieve the archive
		archive = self.getFile(url)
		if not archive:
			raise Exception("Archive file not found on server (%s)" % url)
		
		if not os.path.lexists(basepath):
			try:
				os.makedirs(basepath)
			except Exception, e:
				raise Exception("Unable to create the installation directory (%s): %s" % (basepath, e))
		
		# We untar it into the current directory.
		archiveFileObject = StringIO.StringIO(archive)
		try:
			tfile = tarfile.TarFile.open('any', 'r', archiveFileObject)
			contents = tfile.getmembers()
			# untar each file into the qtesterman directory

			for c in contents:
				# Let's remove the first level of directory ("patch -p1")
				c.name = '/'.join(c.name.split('/')[1:])
				if not c.name:
					self.getLogger().warning("Invalid file in archive: not under a root folder")
					continue
				self.getLogger().debug("Installing %s into %s..." % (c.name, basepath))
				tfile.extract(c, basepath)
				# TODO: make sure to set write rights to allow future updates
				# os.chmod("%s/%s" % (basepath, c), ....)
			tfile.close()
		except Exception, e:
			archiveFileObject.close()
			raise Exception("Error while unpacking the update archive:\n%s" % str(e))

		archiveFileObject.close()
		self.getLogger().info("Successfully installed.")

	def installAgent(self, installDir = "/tmp", preferredBranches = [ 'stable' ], preferredVersion = None):
		"""
		Updates the agent to preferredVersion (if provided), or to the latest version 
		available in preferredBranches. If preferredBranches is not provided (empty or None),
		all branches are taken into account.

		@throws exceptions
		@type  preferredBranches: list of strings
		@param preferredBranches: the branches in which we should look for newer versions.
		                          Not taken into account if a preferredVersion is provided.
		@type  preferredVersion: string
		@param preferredVersion: a preferred version to update to (format: A.B.C).

		@rtype: bool
		@returns: True if the component was updated. False otherwise.
		"""
		component = 'pyagent'
		if preferredVersion:
			branches = None
		else:
			branches = preferredBranches
		currentVersion = "0.0.0"

		basepath = os.path.normpath(os.path.realpath(installDir))
	
		# Get the current available updates	
		updates = self.getComponentVersions(component, branches)
		if not updates:
			# No updates available - nothing to do
			self.getLogger().info("No agent package available on this server.")
			return False
		self.getLogger().info("Available agents:\n%s" % "\n".join([ "%s (%s)" % (x['version'], x['branch']) for x in updates]))

		# Select the update to apply according to branches/preferredVersion
		url = None
		selectedVersion = None
		selectedBranch = None
		
		if preferredVersion:
			# Let's check if the version is available
			v = filter(lambda x: x['version'] == preferredVersion, updates)
			if v:
				url = v[0]['url']
				selectedVersion = v[0]['version'] # == preferredVersion
				selectedBranch = v[0]['branch']
				self.getLogger().info("Preferred version %s available. Installing it." % preferredVersion)
			else:
				self.getLogger().warning("Preferred version %s is not available. Cannot install it." % preferredVersion)
		else:
			# No preferred version: take the most recent one in the selected branches
			# Let's check if we have a better version than the current one
			# Versions rules
			# A.B.C < A+n.b.c
			# A.B.C < A.B+n.c
			# A.B.C < A.B.C+n
			# (ie when comparing A.B.C and a.b.c, lexicographic order is ok)
			if not currentVersion or (currentVersion < updates[0]['version']):
				selectedVersion = updates[0]['version']
				url = updates[0]['url']
				selectedBranch = updates[0]['branch']
				self.getLogger().info("New version available: %s, in branch %s. Installing." % (selectedVersion, selectedBranch))
			else:
				self.getLogger().info("No new version available. Not installing.")

		# OK, now if we have selected a version, let's update.		
		if url:
			try:
				self.installComponent(url, basepath)
			except Exception, e:
				raise Exception("Unable to install the update:\n%s" % str(e))
	
			self.getLogger().info("Agent %s (%s) has been installed." % (selectedVersion, selectedBranch))
			return True
		else:
			return False # No newer version available, or preferred version not available

	def onConnection(self, channel):
		"""
		Callback called upon connection.
		Returns the update status to the install caller via the response queue.
		"""
		self.getLogger().info("Connected.")
		self.getLogger().info("Trying to update...")
		try:
			ret = self.installAgent(installDir = self._installDir, preferredBranches = self._branches, preferredVersion = self._preferredVersion)
			self._responseQueue.put(ret)
		except Exception, e:
			self.getLogger().error("Unable to update: %s" % e)
			self._responseQueue.put(False)

	def install(self, installDir, branches, preferredVersion, timeout = 60):
		"""
		Synchronous function that run the agent, waits for the update on connection to complete,
		and returns the update status.
		"""
		self._installDir = installDir
		self._branches = None
		if branches:
			self._branches = branches.split(',')
		self._preferredVersion = preferredVersion
		self._responseQueue = Queue.Queue()
		self.start()
		try:
			# Implemented as a loop to make it user-interruptible.
			i = 0
			ret = None
			while i < timeout and ret is None:
				try:
					ret = self._responseQueue.get(True, 1.0) 
				except Queue.Empty:
					ret = None
				i += 1
			if ret is None:
				self.getLogger().error("Timeout while installing the package from the server.")
				ret = False
		except KeyboardInterrupt:
			self.getLogger().info("Aborting installation...")
			ret = False
		self.stop()
		return ret


def main():
	parser = optparse.OptionParser(version = "Testerman PyAgent Installer %s" % getVersion())
	parser.add_option("-c", "--controller", dest = "controllerIp", metavar = "ADDRESS", help = "set agent controller Xa IP address to ADDRESS (default: %default)", default = DEFAULT_TACS_IP)
	parser.add_option("-p", "--port", dest = "controllerPort", metavar = "PORT", help = "set agent controller Xa port address to PORT (default: %default)", default = DEFAULT_TACS_PORT, type="int")
	parser.add_option("--local", dest = "localIp", metavar = "ADDRESS", help = "set local IP address to ADDRESS for XA connection (default: system-dependent)", default = "")

	parser.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug mode on (default: %default)", default = False)
	parser.add_option("--install-to", dest = "installDir", metavar = "INSTALL_DIR", help = "install the pyagent into INSTALL_DIR (default: current working dir)", default = ".")
	parser.add_option("--branch", dest = "branch", metavar = "BRANCH", help = "install the latest version from this branch (default: %default)", default = "stable")
	parser.add_option("--force-version", dest = "version", metavar = "VERSION", help = "install a specific version. If not set, the latest version in the selected branches is installed. If set the --branch parameter is ignored.", default = None)

	(options, args) = parser.parse_args()

	if options.debug:
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S')

	installer = AgentInstaller(name = "installer")
	installer.initialize(controllerAddress = (options.controllerIp, options.controllerPort), localAddress = (options.localIp, 0))
	getLogger().info("Trying to install a Testerman PyAgent from %s:%s..." % (options.controllerIp, options.controllerPort))
	ret = installer.install(installDir = options.installDir, branches = options.branch, preferredVersion = options.version)
	if ret:
		if not sys.platform in [ 'win32', 'win64']:
			getLogger().info("""You can now start the installed agent with:
%s/testerman-agent.py -c %s -p %s
Don't forget to add additional command line options, such as --name <name>.""" % (options.installDir, options.controllerIp, options.controllerPort))
		status = 0
	else:
		getLogger().error("Unable to install the agent.")
		status = 1

	installer.finalize()

	sys.exit(status)

if __name__ == '__main__':
	main()

