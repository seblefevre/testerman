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
# Event manager: a subscription engine to receive internal events from
# outside,
# also includes a Test Logging (TL) sub-system.
#
# Events are formatted as TestermanMessages (http/sip/and the likes format).
#
##

import ConfigManager
import CounterManager
import TestermanMessages as Messages
import TestermanNodes as Nodes
import Versions

import logging
import threading

class XcException(Exception):
	def __init__(self, description, code = 403, reason = "Invalid Xc request"):
		Exception.__init__(self, description)
		self.code = code
		self.reason = reason

class XcServer(Nodes.ListeningNode):
	def __init__(self, manager, xcAddress):
		Nodes.ListeningNode.__init__(self, "TS/Xc", "XcServer/%s" % Versions.getServerVersion())
		self._manager = manager
		self.initialize(xcAddress)

	def getLogger(self):
		return logging.getLogger('TS.XcServer')
	
	def onRequest(self, channel, transactionId, request):
		self.getLogger().warning("Unexpected request received, discarding")
	
	def onNotification(self, channel, notification):
		self.getLogger().debug("New notification received")
		method = notification.getMethod()
		uri = notification.getUri()
		if method == "SUBSCRIBE":
			self._manager.subscribe(channel, uri)
		elif method == "UNSUBSCRIBE":
			self._manager.unsubscribe(channel, uri)
		elif method == "MESSAGE":
			self._manager.dispatchNotification(notification)
		else:
			self.getLogger().warning("Received unsupported notification method: " + method)
	
	def onResponse(self, channel, transactionId, response):
		self.getLogger().warning("Unexpected asynchronous response received, discarding")

	def onConnection(self, channel):
		self._manager.registerXcClient(channel)

	def onDisconnection(self, channel):
		self._manager.unregisterXcClient(channel)
	

class IlException(Exception):
	def __init__(self, description, code = 403, reason = "Invalid Il request"):
		Exception.__init__(self, description)
		self.code = code
		self.reason = reason

class IlServer(Nodes.ListeningNode):
	def __init__(self, manager, ilAddress):
		Nodes.ListeningNode.__init__(self, "TS/Il", "IlServer/%s" % Versions.getServerVersion())
		self._manager = manager
		self.initialize(ilAddress)
	
	def getLogger(self):
		return logging.getLogger('TS.IlServer')

	def onRequest(self, channel, transactionId, request):
		self.getLogger().warning("Unexpected request received, discarding")
	
	def onNotification(self, channel, notification):
		self.getLogger().debug("New notification received")
		self._manager.handleIlNotification(notification)
	
	def onResponse(self, channel, transactionId, response):
		self.getLogger().warning("Unexpected asynchronous response received, discarding")

	

################################################################################
# TL dispatcher
# Keep tracks of currently registered Xc clients and forward them
# Il-received notifications.
################################################################################

class Manager:
	"""
	The Manager manages the subscriptions.
	It is interfaces through the WebServices.
	"""
	def __init__(self, xcAddress, ilAddress):
		self._mutex = threading.RLock()
		self._xcServer = XcServer(self, xcAddress)
		self._ilServer = IlServer(self, ilAddress)
	
		# The subscription mapping is a list of Xc channels objects per uri (jobid:<id>, system:jobs, ...).
		self._subscriptions = {}
		self._xcClients = []
		
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def initialize(self):
		pass

	def finalize(self):
		pass

	def start(self):
		self.getLogger().info("Starting...")
		self._xcServer.start()
		self._ilServer.start()
		self.getLogger().info("Started")
	
	def stop(self):
		self.getLogger().info("Stopping...")
		self._xcServer.stop()
		self._xcServer.finalize()
		self._ilServer.stop()
		self._ilServer.finalize()
		self.getLogger().info("Stopped")
	
	def subscribe(self, channel, uri):
		uri = str(uri) # make sure we deal with URI strings, not URI objects
		self._lock()
		if not self._subscriptions.has_key(uri):
			self._subscriptions[uri] = [ channel ]
		else:
			if channel not in self._subscriptions[uri]:
				self._subscriptions[uri].append(channel)
		self._unlock()
		self.getLogger().info("channel %s subscribed to uri %s" % (str(channel), uri))
	
	def unsubscribe(self, channel, uri):
		uri = str(uri) # make sure we deal with URI strings, not URI objects
		self._lock()
		if not self._subscriptions.has_key(uri):
			self._unlock()
			self.getLogger().warning("Unsubscription attempt for a non-known uri. Discarding.")
			return

		if channel in self._subscriptions[uri]:
			self._subscriptions[uri].remove(channel)

		self.getLogger().info("channel %s unsubscribed from uri %s" % (str(channel), uri))
		
		# Garbage collecting:
		# The uri may be watched by anybody else
		if len(self._subscriptions[uri]) == 0:
			self.getLogger().info("Subscription without any other channel, garbage collecting it...")
			del self._subscriptions[uri]

		self._unlock()

	def registerXcClient(self, channel):
		self.getLogger().info("New channel %s connected on Xc" % str(channel))
		self._lock()
		self._xcClients.append(channel)
		self._unlock()
		CounterManager.instance().inc("server.ts.xcchannels.current")

	def unregisterXcClient(self, channel):
		self.getLogger().info("Client %s disconnected from Xc" % str(channel))
		self._lock()
		for (uri, clients) in self._subscriptions.items():
			if channel in clients:
				clients.remove(channel)
			# Garbage collection
			if len(clients) == 0:
				del self._subscriptions[uri]
		if channel in self._xcClients:
			self._xcClients.remove(channel)
		self._unlock()
		self.getLogger().debug("Client %s purged from Xc registered clients" % str(channel))
		CounterManager.instance().dec("server.ts.xcchannels.current")

	def dispatchNotification(self, notification):
		"""
		Forwards the notification to all subscribing clients.
		
		@type  notification: Notification message
		@param notification: the notification to forward to subscribed listeners
		"""
		uri = str(notification.getUri()) # make sure we deal with URI strings, not URI objects
		self.getLogger().debug("Dispatching notification on Xc for %s..." % uri)
		nbClients = 0
		self._lock()
		if not self._subscriptions.has_key(uri):
			self._unlock()
			return
		for channel in self._subscriptions[uri]:
			try:
				self._xcServer.sendNotification(channel, notification)
				nbClients += 1
			except:
				self.getLogger().warning("Unable to send event to a client")
		self._unlock()
		self.getLogger().debug("Notification dispatched to %d Xc clients" % nbClients)
	
	def getLogger(self):
		return logging.getLogger('TS.TL')

	def handleIlNotification(self, notification):
		method = notification.getMethod()
		if method == "LOG":
			# Add server-side/TL control here
			filename = notification.getHeader('Log-Filename')
			if filename:
				try:
					f = open(filename, 'a')
					f.write('%s\n' % notification.getBody())
					f.close()
				except Exception, e:
					self.getLogger().error("Unable to write log for %s: %s" % (notification.getUri(), str(e)))		
		else:
			self.getLogger().warning("Received unsupported notification method: " + method)

		# Dispath
		self.dispatchNotification(notification)


################################################################################
# Main module functions
################################################################################

TheManager = None

def initialize():
	"""
	Prepares a singleton instance of EventManager,
	initializes it,
	starts listening on Xc and Il interfaces.
	"""
	global TheManager
	xcAddress = (ConfigManager.get("interface.xc.ip"), ConfigManager.get("interface.xc.port"))
	ilAddress = (ConfigManager.get("interface.il.ip"), ConfigManager.get("interface.il.port"))
	TheManager = Manager(xcAddress, ilAddress)
	TheManager.initialize()
	TheManager.start()

def finalize():
	"""
	Stops listening on Xc and Il interfaces,
	frees resources.
	"""
	TheManager.stop()
	TheManager.finalize()
	
def instance():
	return TheManager
