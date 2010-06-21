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
# A Testerman Node is a peer being able to send/receive testerman messages
# 
# This file provides a base node class that is responsible for
# the transaction part of the protocol.
#
# Two kinds of nodes are possible:
# listening nodes, and connecting nodes.
# The connecting nodes reconnects automatically in case of a disconnection.
#
#
# Layered structures:
# Network level:
# - send/receive packets (stream + packetizer)
# - passive keep-alive mechanism (regularly send a KA packet, incoming 
#   inactivity timeout to detect dropped connections)
# - provided by TcpPacketizerServerThread and TcpPacketizerClientThread.
# - must be reimplemented to provide several callbacks implementations.
# - these classes are not testerman-tainted and may be reused anywhere else.
# Connectors:
# - they are the combination of the untainted network level classes,
#   but implementing a specific Testerman interface IConnector.
# - ListeningConnectorThread, ConnectingConnectorThread
# - network handles (socket ids) are here renamed to 'channels'
# Transaction Manager, Node:
# - able to encode/decode Testerman Messages, managing transaction Ids,
#   retransmissions (when they are implemented), etc
# - provides high level function to send/receive messages and
#   execute synchronous requests on a remote node.
# - implemented in class BaseNode
# - plugged on a Connector (in fact, we plug a connector to it).
# - thread switcher ensuring that low levels are never blocked,
#   enables basic 're-entrance' (executing a request upon receiving a request)
#   without having to implement a state machine in your application code.
#
# High level nodes, Node subclasses with a prepared connector provided for
# convenience:
# - ConnectingNode, to implement Client nodes
# - ListeningNode, to implement Server nodes
##

import TestermanMessages as Messages

import threading
import select
import socket
import Queue
import SocketServer
import time
import os
import sys

KEEP_ALIVE_PDU = 'KA'

################################################################################
# Tools
################################################################################

def getBacktrace():
	import traceback
	import StringIO
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret


################################################################################
# Reusable Tcp client class
################################################################################

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
		
		self._windowsPlatform = (sys.platform.startswith('win'))
		if not self._windowsPlatform:
			# a "control port" that is used to notify the low-level that
			# a message is ready to send (if the associated sending queue is not empty)
			# or just to exit our polling loop (stop notification).
			self.control_read, self.control_write = os.pipe()
		
	def __del__(self):
		if not self._windowsPlatform:
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
					self.trace("Exception in main loop:\n" + getBacktrace())
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
		if self._windowsPlatform:
			return self.__main_receive_send_loop_win32()
		else:
			return self.__main_receive_send_loop_unix()

	def __main_receive_send_loop_unix(self):
		self.last_keep_alive_timestamp = time.time()
		self.last_activity_timestamp = time.time()

		write_socket = []

		timeout = -1
		if self.inactivity_timeout:
			timeout = self.inactivity_timeout

		if self.keep_alive_interval and (self.keep_alive_interval < timeout or timeout < 0):
			timeout = self.keep_alive_interval

		while not self.stopEvent.isSet():
			try:
#				self.trace("sleeping for at most %ss" % timeout)
				if timeout >= 0:
					r, w, e = select.select([ self.socket, self.control_read ], write_socket, [ self.socket ], timeout)
				else:
					r, w, e = select.select([ self.socket, self.control_read ], write_socket, [ self.socket ])

				current_time = time.time()

				# Received an error from the network
				if self.socket in e:
					raise EOFError("Socket select error: disconnecting")

				# Received a message from the network
				if self.socket in r:
					read = self.socket.recv(65535)
					if not read:
						raise EOFError("Nothing to read on read event: disconnecting")
					self.last_activity_timestamp = current_time
					self.buf = ''.join([self.buf, read]) # faster than += r
					self.__on_incoming_data()

				# select timeout - we post a keep_alive right now
				if not r and not w and not e:
					# Check inactivity timeout 
					if self.inactivity_timeout:
						if current_time - self.last_activity_timestamp > self.inactivity_timeout:
							raise EOFError("Inactivity timeout: disconnecting")

					# Send (queue) a Keep-Alive if needed
					if self.keep_alive_interval:
						if current_time - self.last_keep_alive_timestamp > self.keep_alive_interval:
							self.last_keep_alive_timestamp = current_time
							self.trace("Sending Keep Alive")
							self.send_packet(KEEP_ALIVE_PDU)
							# Make sure the KA will be sent during this iteration
							if not self.control_read in r:
								r.append(self.control_read)

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
	
				# Recompute the select timeout for the next iteration
				timeout = -1
				if self.inactivity_timeout:
					timeout = self.inactivity_timeout

				if self.keep_alive_interval:
					next_ka_in = self.last_keep_alive_timestamp + self.keep_alive_interval - current_time
					if next_ka_in < 0:
						# We missed one KA - just send it asap.
						timeout = 0
					elif timeout > 0:
						timeout = min(next_ka_in, timeout)
					else:
						timeout = next_ka_in

			except EOFError, e:
				self.trace("Disconnected by peer.")
				raise e # We'll reconnect.

			except socket.error, e:
				self.trace("Low level error: " + str(e))
				raise e # We'll reconnect

			except Exception, e:
				self.trace("Exception in main pool for incoming data: " + str(e))
				pass

	def __main_receive_send_loop_win32(self):
		"""
		This flavor currently does not use pipes to be notified
		that the sending queue is not empty.
		"""
		self.last_keep_alive_timestamp = time.time()
		self.last_activity_timestamp = time.time()
		while not self.stopEvent.isSet():
			try:
				# Check if we have incoming data
				r, w, e = select.select([ self.socket ], [], [ self.socket ], 0.001)
				if self.socket in e:
					raise EOFError("Socket select error: disconnecting")
				elif self.socket in r:
					read = self.socket.recv(65535)
					if not read:
						raise EOFError("Nothing to read on read event: disconnecting")
					self.last_activity_timestamp = time.time()
					self.buf = ''.join([self.buf, read]) # faster than += r
					self.__on_incoming_data()

				# Check inactivity timeout 
				elif self.inactivity_timeout:
					if time.time() - self.last_activity_timestamp > self.inactivity_timeout:
						raise EOFError("Inactivity timeout: disconnecting")

				# Send (queue) a Keep-Alive if needed
				if self.keep_alive_interval:
					if time.time() - self.last_keep_alive_timestamp > self.keep_alive_interval:
						self.last_keep_alive_timestamp = time.time()
						self.trace("Sending Keep Alive")
						self.send_packet(KEEP_ALIVE_PDU)

				# Send queued messages
				while not self.queue.empty():
					# Make sure we can send something. If not, keep the message for later attempt.
					r, w, e = select.select([ ], [ self.socket ], [ self.socket ], 0.001)
					if self.socket in e:
						raise EOFError("Socket select error when sending a message: disconnecting")
					elif self.socket in w:	
						try:
							message = self.queue.get(False)
							self.socket.sendall(message)
						except Queue.Empty:
							pass
						except Exception, e:
							self.trace("Unable to send message: " + str(e))
					else:
						# Not ready. Will perform a new attempt on next main loop iteration
						break

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
		if not self._windowsPlatform:
			# This will force our blocking select to wake up in our main loop
			os.write(self.control_write, 'b')
		self.join()

	def send_packet(self, packet):
		self.queue.put(packet + self.terminator)
		if not self._windowsPlatform:
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


class TcpPacketizerServerThread(threading.Thread):
	"""
	Simple TCP server that listens on a particular address/port for new connections.
	It also sends separated with a single terminator character, 
	and packetizes incoming stream, too.

	Once constructed, you may use:
		start()
		stop()
		send_packet(client_address, packet)
	from any thread,
	and reimplement:
		on_connection(client_address)
		on_disconnection(client_address)
		handle_packet(client_address, packet)
		log(txt)
	"""
	class ListeningServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
		"""
		This inner class just redirects some high-level events to the
		TcpPacketizerServerThread instance.
		
		Contains a timeout'd handler to enable graceful shutdown of the server when needed.
		"""
		allow_reuse_address = True

		terminator = '\x00'
		def __init__(self, listening_address, request_handler, manager, inactivity_timeout = 30.0, keep_alive_interval = 20.0):
			SocketServer.TCPServer.__init__(self, listening_address, request_handler)
			self.manager = manager
			self.mutex = threading.RLock()
			self.clients = {} # client object per client_address
			self.inactivity_timeout = inactivity_timeout
			self.keep_alive_interval = keep_alive_interval
		
		def handle_packet(self, client, packet):
			self.manager.handle_packet(client.client_address, packet)
		
		def on_connection(self, client):
#			self.trace("[DEBUG] new client connected: " + str(client.client_address))
			self.mutex.acquire()
			self.clients[client.client_address] = client
			self.mutex.release()
			self.manager.on_connection(client.client_address)
		
		def on_disconnection(self, client):
#			self.trace("[DEBUG] client disconnected: " + str(client.client_address))
			self.mutex.acquire()
			try:
				del self.clients[client.client_address]
			except:
				pass
			self.mutex.release()
			self.manager.on_disconnection(client.client_address)
		
		def send_packet(self, client_address, packet):
#			self.trace("[DEBUG] sending packet to client: " + str(client_address))
			self.mutex.acquire()
			if self.clients.has_key(client_address):
				client = self.clients[client_address]
			else:
				client = None
			self.mutex.release()
			if client:
#				self.trace("[DEBUG] client found for: " + str(client_address))
				client.send_packet(packet)
		
		def trace(self, txt):
			self.manager.trace(txt)
		
		def stop(self):
			for client in self.clients.values():
				client.stop()

		def handle_request_with_timeout(self, timeout):
			"""
			a handle_request reimplementation, with a timeout support.
			Call this instead of the TCPServer.handle_request loop.
			It enables to stop the server gracefully when needed
			
			"""
			r, w, e = select.select([self.socket], [], [], timeout)
			if r:
				self.handle_request()
		
		
	class TcpPacketizerRequestHandler(SocketServer.BaseRequestHandler):
		"""
		This request handler is able to de-packetize incoming stream according to
		a single byte packet limiter character.
		For each packet, will raise a handle_packet(packet).
		You may send packets using send_packet(packet).
		
		The code is quite similar to TcpPacketizeClient(Thread).
		"""

		# The packet terminator
		terminator = '\x00'

		def __init__(self, request, client_address, server):
			self.stopEvent = threading.Event()
			self.buf = ''
			self.queue = Queue.Queue(0)
			self.socket = None
			self.last_activity_timestamp = time.time()
			self.last_keep_alive_timestamp = time.time()
			# a "control port" that is used to notify the low-level that
			# a message is ready to send (if the associated sending queue is not empty)
			# or just to exit our polling loop (stop notification).
			self.control_read, self.control_write = os.pipe()
			# The BaseRequestHandler.__init__ calls handle(); 
			# thus members should be initialized first.
			SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

		def __del__(self):
			os.close(self.control_read)
			os.close(self.control_write)

		def stop(self):
			"""
			Call this whenever you want to stop the client handling.
			"""
			self.stopEvent.set()
			os.write(self.control_write, 'b')

		def handle(self):
			"""
			RequestHandler reimplementation.
			"""
			self.socket = self.request
			self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
			self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
			while not self.stopEvent.isSet():
				try:
					self.__main_receive_send_loop()
				except Exception, e:
					# This means that the stream was broken
					print str(e)
					self.trace(str(e))
					self.stop()

		def __main_receive_send_loop(self):
			"""
			New internal method.
			"""
			self.last_keep_alive_timestamp = time.time()
			self.last_activity_timestamp = time.time()
			
			write_socket = []

			timeout = -1
			if self.server.inactivity_timeout:
				timeout = self.server.inactivity_timeout

			if self.server.keep_alive_interval and (self.server.keep_alive_interval < timeout or timeout < 0):
				timeout = self.server.keep_alive_interval

			while not self.stopEvent.isSet():
#				self.trace("sleeping for at most %ss" % timeout)
				if timeout >= 0:
					r, w, e = select.select([ self.socket, self.control_read ], write_socket, [ self.socket ], timeout)
				else:
					r, w, e = select.select([ self.socket, self.control_read ], write_socket, [ self.socket ])

				current_time = time.time()

				if self.socket in e:
					print "eee"
					raise EOFError("Socket select error: disconnecting")

				if self.socket in r:
					read = self.socket.recv(65535)
					if not read:
						raise EOFError("Nothing to read on read event: disconnecting")
					self.last_activity_timestamp = current_time
					self.buf = ''.join([self.buf, read]) # faster than += r
					self.__on_incoming_data()

				if not r and not w and not e:
					# Check inactivity timeout 
					if self.server.inactivity_timeout:
						if current_time - self.last_activity_timestamp > self.server.inactivity_timeout:
							raise EOFError("Inactivity timeout: disconnecting")

					# Send (queue) a Keep-Alive if needed
					if self.server.keep_alive_interval:
						if current_time - self.last_keep_alive_timestamp > self.server.keep_alive_interval:
							self.last_keep_alive_timestamp = current_time
							self.trace("Sending Keep Alive")
							self.send_packet(KEEP_ALIVE_PDU)
							# Make sure the KA will be sent during this iteration
							if not self.control_read in r:
								r.append(self.control_read)

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
						except IOError, e:
							self.trace("IOError while sending a packet to client (%s) - disconnecting" % str(e))
							self.stop()
						except Exception, e:
							self.trace("Unable to send message: %s" % str(e))
					# No more enqueued messages to send - we don't need to wait for
					# the network socket to be writable anymore.
					write_socket = []

				# Recompute the select timeout for the next iteration
				timeout = -1
				if self.server.inactivity_timeout:
					timeout = self.server.inactivity_timeout

				if self.server.keep_alive_interval:
					next_ka_in = self.last_keep_alive_timestamp + self.server.keep_alive_interval - current_time
					if next_ka_in < 0:
						# We missed one KA - just send it asap.
						timeout = 0
					elif timeout > 0:
						timeout = min(next_ka_in, timeout)
					else:
						timeout = next_ka_in

	
		def __on_incoming_data(self):
			"""
			New internal method.
			"""
			# self.buf contains all received data.
			# Let's check if we can consume them, i.e. PDUs/packets are available.
			pdus = self.buf.split(self.terminator)
			for pdu in pdus[:-1]:
				if not pdu == KEEP_ALIVE_PDU:
					self.handle_packet(pdu)
				else:
					self.trace("Received Keep Alive")
			self.buf = pdus[-1]

		def send_packet(self, packet):
			"""
			New method.
			Sends a packet with the terminator.
			"""
			# Asynchronous send.
			self.queue.put(packet + self.terminator)
			os.write(self.control_write, 'a')

		def handle_packet(self, packet):
			"""
			RequestHandler reimplementation
			"""
			self.server.handle_packet(self, packet)
		
		def setup(self):
			"""
			RequestHandler reimplementation
			"""
			self.trace("new connection")
			self.server.on_connection(self)
		
		def finish(self):
			"""
			RequestHandler reimplementation
			"""
			self.stop()
			SocketServer.BaseRequestHandler.finish(self)
			self.server.on_disconnection(self)
			self.trace("disconnected")
		
		def trace(self, txt):
			self.server.trace("[tcphandler] %s %s" % (str(self.client_address), txt))


	def __init__(self, listening_address, inactivity_timeout = 30.0, keep_alive_interval = 20.0):
		threading.Thread.__init__(self)
		self.stopEvent = threading.Event()
		self.listening_address = listening_address
		self.server = self.ListeningServer(self.listening_address, self.TcpPacketizerRequestHandler, self, inactivity_timeout, keep_alive_interval)

	def run(self):
		self.trace("Tcp server started, listening on %s" % (str(self.listening_address)))
		while not self.stopEvent.isSet():
			self.server.handle_request_with_timeout(0.1)
		self.server.stop()
	
	def stop(self):
		self.stopEvent.set()
		self.join()
	
	def send_packet(self, client_address, packet):
		self.server.send_packet(client_address, packet)
	
	##
	# To reimplement
	##
	def on_connection(self, client_address):
		"""
		Called when a new client is connected.
		You should not do nothing blocking in this function.
		Post a message somewhere to switch threads, if you need to.
		"""
		pass
	
	def on_disconnection(self, client_address):
		"""
		Called when a new client is disconnected, either by the
		local or the remote peer.
		You should not do nothing blocking in this function.
		Post a message somewhere to switch threads, if you need to.
		"""
		pass
	
	def handle_packet(self, client_address, packet):
		"""
		Called when a new packet is arrived from a client.
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
	
class ListeningConnectorThread(TcpPacketizerServerThread, IConnector):
	"""
	A IConnector implementation as a listening server.
	
	When using such a connector, you should set up several callbacks to get 
	low-level events:
	 setConnectionCallback(cb(channel))
	 setDisconnectionCallback(cb(channel))
	 setMessageCallback(cb(channel, TestermanMessages.Message))
	 setTracer(cb(string))
	"""	
	def __init__(self, listeningAddress, inactivityTimeout = 30.0):
		TcpPacketizerServerThread.__init__(self, listeningAddress, inactivityTimeout)
		IConnector.__init__(self)
		self._contact = listeningAddress

	def on_connection(self, client_address):
		"""
		Reimplemented from TcpPacketizerServerThread
		"""
		if callable(self._onConnectionCallback):
			self._onConnectionCallback(client_address)

	def on_disconnection(self, client_address):
		"""
		Reimplemented from TcpPacketizerServerThread
		"""
		if callable(self._onDisconnectionCallback):
			self._onDisconnectionCallback(client_address)

	def handle_packet(self, client_address, packet):
		"""
		Reimplemented from TcpPacketizerServerThread
		"""
		# Tries to parse the packet.
		# If ok, raise it to higher levels.
		try:
			message = Messages.parse(packet)
			if callable(self._onMessageCallback):
				self._onMessageCallback(client_address, message)
		except Exception, e:
			self.trace("Exception while reading message: " + str(e))
			pass

	def trace(self, txt):
		"""
		Reimplemented from TcpPacketizerServerThread
		"""
		if self._onTraceCallback:
			self._onTraceCallback(txt)

	def sendMessage(self, channel, message):
		"""
		Reimplemented for IConnector
		"""
		self.send_packet(channel, str(message))

# TODO
#	def disconnect(self, channel):
#		TcpPacketizerServerThread.disconnect(self)

	def getLocalAddress(self):
		return self._contact
	

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
		self.trace("connected to server %s (client address %s)" % (str(self.serverAddress), str(self.localAddress)))
		if callable(self._onConnectionCallback):
			self._onConnectionCallback(0)

	def on_disconnection(self):
		"""
		Reimplemented from TcpPacketizerServerThread
		"""
		self.trace("disconnected from server %s (client address %s)" % (str(self.serverAddress), str(self.localAddress)))
		if callable(self._onDisconnectionCallback):
			self._onDisconnectionCallback(0)

	def handle_packet(self, packet):
		"""
		Reimplemented from TcpPacketizerClientThread
		"""
		# Tries to parse the packet.
		# If ok, raise it to higher levels.
		try:
			message = Messages.parse(packet)
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
	
class ListeningNode(BaseNode):
	"""
	Subclass this class if you want to create a server-oriented node.
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
		
		initialize(listeningAddress)
		start()
		stop()
		finalize()
	"""
	def __init__(self, name, userAgent): # also manages protocol ?
		BaseNode.__init__(self, name, userAgent)
	
	def initialize(self, listeningAddress):
		self.trace("Initializing listening node %s on %s..." % (self.getNodeName(), listeningAddress))
		connector = ListeningConnectorThread(listeningAddress)
		self._setConnector(connector)
		BaseNode.initialize(self)
