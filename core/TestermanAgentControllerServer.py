#!/usr/bin/env python
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
# Back-to-back implementation: new Xa transactions are created on Ia requests.
#
# Error-management strategies: exception-based, not functional. Enables better error messages.
##

import CounterManager
import TestermanMessages as Messages
import TestermanNodes as Nodes
import Tools
import Versions

import logging
import optparse
import time
import threading


def getLogger():
	return logging.getLogger('TACS')

class TacsException(Exception):
	"""
	Exception raised in case of a "business logic" error - including normal ones, such as duplicated URIs, etc.
	"""
	def __init__(self, description, code = 501, reason = "TACS Internal Error"):
		Exception.__init__(self, description)
		self.code = code
		self.reason = reason

class XaException(Exception):
	"""
	Exception raised when something unexpected happens on Xa side (timeout, unsupported protocol options, missing parameters...)
	"""
	def __init__(self, description, code = 501, reason = "Xa Interface Error"):
		Exception.__init__(self, description)
		self.code = code
		self.reason = reason

class IaException(Exception):
	"""
	Exception raised when something unexpected happens on Ia side (timeout, unsupported protocol options, missing parameters...)
	"""
	def __init__(self, description, code = 501, reason = "Ia Interface Error"):
		Exception.__init__(self, description)
		self.code = code
		self.reason = reason

class XaServer(Nodes.ListeningNode):
	"""
	Xa side:
	
	Agent -> TACS:
	 R REGISTER
	 R UNREGISTER
	 N LOG
	
	TACS -> Agent:
	 R DEPLOY
	 R UNDEPLOY
	 R RESTART
	 R KILL
	
	Probe -> TACS:
	 N LOG
	 N TRI-ENQUEUE-MSG
	
	TACS -> Probe:
	 R TRI-SEND
	 R TRI-SA-RESET
	 R TRI-EXECUTE-TESTCASE
	 R TRI-UNMAP
	 R TRI-MAP
	
	"""
	def __init__(self, controller, xaAddress):
		Nodes.ListeningNode.__init__(self, "TACS/Xa", "XaServer/%s" % Versions.getAgentControllerVersion())
		self._controller = controller
		self.initialize(xaAddress)
	
	def getLogger(self):
		return logging.getLogger('TACS.XaServer')

	def onRequest(self, channel, transactionId, request):
		self.getLogger().debug("New request received")
		try:
			method = request.getMethod()

			if method == "REGISTER":
				if request.getUri().getScheme() == "agent":
					# This is an Agent-level registration - throws TacsException
					self._controller.registerAgent(channel, request.getUri(), request.getHeader("Contact"), request.getHeader("Agent-Supported-Probe-Types").split(','), request.getHeader('User-Agent'))
					self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
				elif request.getUri().getScheme() == "probe":
					# This is a probe-level registration - throws TacsException
					self._controller.registerProbe(channel, request.getUri(), request.getHeader("Contact"), request.getHeader("Probe-Name"), request.getHeader("Probe-Type"), request.getHeader('Agent-Uri'))
					self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
				else:
					raise XaException("Unsupported URI scheme for registration")

			elif method == "UNREGISTER":
				if request.getUri().getScheme() == "agent":
					# This is an Agent-level unregistration - throws TacsException
					self._controller.unregisterAgent(channel)
					self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
				elif request.getUri().getScheme() == "probe":
					# This is a probe-level unregistration - throws TacsException
					self._controller.unregisterProbe(channel, request.getUri())
					self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
				else:
					raise XaException("Unsupported URI scheme for unregistration")
			else:
				raise XaException("Unsupported method", 505, "Not Supported")

		except TacsException, e:
			resp = Messages.Response(e.code, e.reason)
			resp.setBody(str(e))
			self.sendResponse(channel, transactionId, resp)

		except XaException, e:
			resp = Messages.Response(e.code, e.reason)
			resp.setBody(str(e))
			self.sendResponse(channel, transactionId, resp)

		except Exception, e:
			resp = Messages.Response(501, "Internal server error")
			resp.setBody(str(e) + "\n" + Nodes.getBacktrace())
			self.sendResponse(channel, transactionId, resp)
	
	def onNotification(self, channel, notification):
		self.getLogger().debug("New notification received:\n%s" % str(notification))
		method = notification.getMethod()
		if method == "LOG":
			self._controller.onLog(channel, notification)
		elif method == "TRI-ENQUEUE-MSG":
			self._controller.onTriEnqueueMsg(channel, notification)
		else:
			self.getLogger().info("Received unsupported notification method: " + method)
	
	def onResponse(self, channel, transactionId, response):
		self.getLogger().warning("Received an unexpected asynchronous response")

	# TACS -> Probes

	def triSend(self, channel, request):
		"""
		@type request: TestermanMessages.Request
		"""
		resp = self.executeRequest(channel, request)
		if not resp:
			raise XaException("Timeout while waiting for TRI-SEND response from probe %s" % request.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("TRI-SEND from probe %s returned %d %s" % (request.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))

	def triExecuteTestCase(self, channel, request):
		"""
		@type request: TestermanMessages.Request
		"""
		resp = self.executeRequest(channel, request)
		if not resp:
			raise XaException("Timeout while waiting for TRI-EXECUTE-TESTCASE response from probe %s" % request.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("TRI-EXECUTE-TESTCASE from probe %s returned %d %s" % (request.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))

	def triMap(self, channel, uri):
		"""
		Constructs a reset request, execute it.
		"""
		req = Messages.Request(method = "TRI-MAP", uri = uri, protocol = "XA", version = Versions.getXaVersion())
		resp = self.executeRequest(channel, req)
		if not resp:
			raise XaException("Timeout while waiting for TRI-MAP response from probe %s" % req.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("TRI-MAP from probe %s returned %d %s" % (req.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))

	def triUnmap(self, channel, uri):
		"""
		Constructs a reset request, execute it.
		"""
		req = Messages.Request(method = "TRI-UNMAP", uri = uri, protocol = "XA", version = Versions.getXaVersion())
		resp = self.executeRequest(channel, req)
		if not resp:
			raise XaException("Timeout while waiting for TRI-UNMAP response from probe %s" % req.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("TRI-UNMAP from probe %s returned %d %s" % (req.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))

	def triSAReset(self, channel, uri):
		"""
		Constructs a reset request, execute it.
		"""
		req = Messages.Request(method = "TRI-SA-RESET", uri = uri, protocol = "XA", version = Versions.getXaVersion())
		resp = self.executeRequest(channel, req)
		if not resp:
			raise XaException("Timeout while waiting for TRI-SA-RESET response from probe %s" % req.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("TRI-SA-RESET from probe %s returned %d %s" % (req.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))

	# TACS -> Agents
	
	def kill(self, channel, uri):
		req = Messages.Request(method = "KILL", uri = uri, protocol = "XA", version = Versions.getXaVersion())
		resp = self.executeRequest(channel, req)
		if not resp:
			raise XaException("Timeout while waiting for KILL response from agent %s" % req.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("KILL from agent %s returned %d %s" % (req.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))
	
	def restart(self, channel, uri):
		raise XaException("agent RESTART not implemented yet")
	
	def deploy(self, channel, agentUri, probeName, probeType):
		req = Messages.Request(method = "DEPLOY", uri = agentUri, protocol = "XA", version = Versions.getXaVersion())
		req.setApplicationBody({'probe-type': probeType, 'probe-name': probeName})
		resp = self.executeRequest(channel, req)
		if not resp:
			raise XaException("Timeout while waiting for DEPLOY response from agent %s" % req.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("DEPLOY from agent %s returned %d %s" % (req.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))
	
	def undeploy(self, channel, agentUri, probeName):
		req = Messages.Request(method = "UNDEPLOY", uri = agentUri, protocol = "XA", version = Versions.getXaVersion())
		req.setApplicationBody({'probe-name': probeName})
		resp = self.executeRequest(channel, req)
		if not resp:
			raise XaException("Timeout while waiting for UNDEPLOY response from agent %s" % req.getUri())
		if resp.getStatusCode() != 200:
			raise XaException("UNDEPLOY from agent %s returned %d %s" % (req.getUri(), resp.getStatusCode(), resp.getReasonPhrase()))

	# Technical callbacks
	
	def onConnection(self, channel):
		self.getLogger().info("%s connected" % str(channel))

	def onDisconnection(self, channel):
		self.getLogger().info("%s disconnected" % str(channel))
		self._controller.unregisterAgent(channel)


	
class IaServer(Nodes.ListeningNode):
	"""
	Ia side:
	
	TE/TS -> TACS (system:tacs):
	 R LOCK
	 R UNLOCK
	 N SUBSCRIBE
	 N UNSUBSCRIBE
	 R GET-PROBES
	 R GET-AGENTS
	 R GET-PROBE

	TE -> Probe via TACS:
	 R TRI-SEND
	 R TRI-EXECUTE-TESTCASE
	 R TRI-UNMAP
	 R TRI-MAP
	
	TE/TS -> Agent via TACS:
	 R DEPLOY
	 R UNDEPLOY

	TACS -> TE/TS:
	 N PROBE
	
	Probe -> TE/TS via TACS:
	 N LOG
	 N TRI-ENQUEUE-MSG
	 
	"""
	def __init__(self, controller, iaAddress):
		Nodes.ListeningNode.__init__(self, "TACS/Ia", "IaServer/%s" % Versions.getAgentControllerVersion())
		self._controller = controller
		self.initialize(iaAddress)
	
	def getLogger(self):
		return logging.getLogger('TACS.IaServer')
	
	def onRequest(self, channel, transactionId, request):
		self.getLogger().debug("New request received:\n%s" % str(request))
		try:
			method = request.getMethod()
			# Probe-targeted requests
			if method == "TRI-EXECUTE-TESTCASE":
				# Forward the body as is, with possible parameters
				self._controller.triExecuteTestCase(request.getUri(), request)
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "TRI-SEND":
				# Probe send - we forward the body as is, with the original encoding and type.
				self._controller.triSend(request.getUri(), request)
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "TRI-SA-RESET":
				self._controller.triSaReset(request.getUri())
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "TRI-MAP":
				self._controller.triMap(request.getUri())
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "TRI-UNMAP":
				self._controller.triUnmap(request.getUri())
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))

			# TACS-targeted requests
			elif method == "LOCK":
				self._controller.lockProbe(channel, request.getHeader('Probe-Uri'))
				response = Messages.Response(200, "OK")
				self.sendResponse(channel, transactionId, response)
			elif method == "UNLOCK":
				self._controller.unlockProbe(channel, request.getHeader('Probe-Uri'))
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "GET-PROBES":
				probes = self._controller.getRegisteredProbes()
				resp = Messages.Response(200, "OK")
				resp.setApplicationBody(probes)
				self.sendResponse(channel, transactionId, resp)
			elif method == "GET-AGENTS":
				probes = self._controller.getRegisteredAgents()
				resp = Messages.Response(200, "OK")
				resp.setApplicationBody(probes)
				self.sendResponse(channel, transactionId, resp)
			elif method == "GET-PROBE":
				probeUri = request.getHeader('Probe-Uri')
				info = self._controller.getProbeInfo(probeUri)
				if info:
					resp = Messages.Response(200, "OK")
					resp.setApplicationBody(info)
				else:
					resp = Messages.Response(404, "Not found")
				self.sendResponse(channel, transactionId, resp)
			elif method == "DEPLOY":
				probeInfo = request.getApplicationBody()
				agentUri = request.getHeader('Agent-Uri')
				self._controller.deployProbe(agentUri = agentUri, probeName = probeInfo['probe-name'], probeType = probeInfo['probe-type'])
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "UNDEPLOY":
				probeInfo = request.getApplicationBody()
				agentUri = request.getHeader('Agent-Uri')
				self._controller.undeployProbe(agentUri = agentUri, probeName = probeInfo['probe-name'])
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "SUBSCRIBE": # Notification or Request ??
				self._controller.subscribe(channel, request.getUri())
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			elif method == "UNSUBSCRIBE": # Notification or Request ??
				self._controller.unsubscribe(channel, request.getUri())
				self.sendResponse(channel, transactionId, Messages.Response(200, "OK"))
			else:
				raise IaException("Unsupported method", 505, "Not Supported")

		except TacsException, e:
			resp = Messages.Response(e.code, e.reason)
			resp.setBody(str(e))
			self.sendResponse(channel, transactionId, resp)

		except IaException, e:
			resp = Messages.Response(e.code, e.reason)
			resp.setBody(str(e))
			self.sendResponse(channel, transactionId, resp)

		except XaException, e:
			resp = Messages.Response(e.code, e.reason)
			resp.setBody(str(e))
			self.sendResponse(channel, transactionId, resp)

		except Exception, e:
			resp = Messages.Response(501, "Internal server error")
			resp.setBody(str(e) + "\n" + Nodes.getBacktrace())
			self.sendResponse(channel, transactionId, resp)
	
	def onNotification(self, channel, notification):
		self.getLogger().debug("New notification received:\n%s" % str(notification))
		try:
			method = notification.getMethod()
			uri = notification.getUri()
			if method == "SUBSCRIBE":
				self._controller.subscribe(channel, uri)
			elif method == "UNSUBSCRIBE":
				self._controller.unsubscribe(channel, uri)
			else:
				self.getLogger().info("Received unsupported notification method: " + method)
		except Exception, e:
			self.getLogger().error("While handling notification: " + str(e))
	
	def onResponse(self, channel, transactionId, response):
		# We should not receive any asynchronous response on Ia
		self.getLogger().warning("Received an unexpected asynchronous response")

	# Not used - to remove ?
	def forwardResponse(self, channel, transactionId, response):
		"""
		@type request: TestermanMessages.Response
		"""
		self.sendResponse(channel, transactionId, response)

	def onConnection(self, channel):
		self.getLogger().info("%s connected" % str(channel))
		self._controller.registerIaClient(channel)

	def onDisconnection(self, channel):
		self.getLogger().info("%s disconnected" % str(channel))
		self._controller.unregisterIaClient(channel)

class Controller(object):
	"""
	A Controller is a simple translator between Ia and Xa.
	
	This is basically a mapper between channels and URIs, managing:
	- agent/probe tree structures according to Xa/REGISTERs
	- event subscriptions on Ia side
	
	When sending sends/reset to probes, simply forward the request (stateless proxy mode, no B2B at all) 
	according to probe.uri -> Xa/channel mapping constructed via Xa/REGISTERs
	It also forwards the response back, asynchronously, to the requester over Ia.
	
	When receiving a LOG or EVENT notifications from Xa, forwards it to Ia clients that SUBSCRIBE for the
	corresponding (probe) URIs.
	[step 1]: notifications are forwarded to ALL Ia clients.
	
	"""
	
	def __init__(self, xaAddress, iaAddress):
		self._mutex = threading.RLock()
		self._xaServer = XaServer(self, xaAddress)
		self._iaServer = IaServer(self, iaAddress)
		self._agents = {}
		self._probes = {}

		# The subscription mapping is a list of Ia channels per uri (probe:<id>, system:probes, ...).
		self._subscriptions = {}
		self._iaClients = []
	
	def getLogger(self):
		return logging.getLogger('TACS.Controller')

	def start(self):
		self._xaServer.start()
		self._iaServer.start()
	
	def stop(self):
		self._xaServer.stop()
		self._xaServer.finalize()
		self._iaServer.stop()
		self._iaServer.finalize()

	def initialize(self):
		pass
	
	def finalize(self):
		pass			
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()

	##
	# Agent registration
	##
	def registerAgent(self, channel, uri, contact, supportedProbes, userAgent):
		"""
		@type supportedProbes: list of strings
		"""
		uri = str(uri)
		self._lock()
		self._agents[uri] = { 'channel': channel, 'uri': uri, 'contact': contact, 'supported-probes': supportedProbes, 'user-agent': userAgent }
		self._unlock()
		# Now sends an event over Ia to notify the new agent
		notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
		notification.setHeader("Reason", "agent-registered")
		notification.setApplicationBody({ 'uri': uri, 'user-agent': userAgent, 'supported-probes': supportedProbes, 'contact': contact })
		self._dispatchNotification(notification)
		self.getLogger().info("Agent %s registered" % uri)
		
	def unregisterAgent(self, channel):
		"""
		Look for agent and probes tables and purge them according to their channel.
		"""
		a = None
		p = []
		self._lock()
		for agent in self._agents.values():
			if agent['channel'] == channel:
				a = agent
				del self._agents[agent['uri']]
		for probe in self._probes.values():
			if probe['channel'] == channel:
				p.append(probe)
				del self._probes[probe['uri']]
		self._unlock()
		for probe in p:
			self.getLogger().info("Probe %s unregistered" % probe['uri'])
			# Now sends an event over Ia
			notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
			notification.setHeader("Reason", "probe-unregistered")
			notification.setApplicationBody({ 'uri': probe['uri'] })
			self._dispatchNotification(notification)
		if a:
			self.getLogger().info("Agent %s unregistered" % a['uri'])
			# Agent disconnected, send a notification on Ia subscribers
			notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
			notification.setHeader("Reason", "agent-unregistered")
			notification.setApplicationBody({ 'uri': a['uri'] })
			self._dispatchNotification(notification)

	##
	# Probe registration
	##
	def registerProbe(self, channel, uri, contact, name, probeType, agentUri):
		"""
		"""
		uri = str(uri)
		# We should look for the managing agent first.
		self._lock()
		self._probes[uri] = { 'channel': channel, 'uri': uri, 'type': probeType, 'name': name, 'contact': contact, 'locks': {}, 'agent-uri': agentUri } # locks is a dict[channel] of anything (used as an indexed list of channels)
		self._unlock()
		self.getLogger().info("Probe %s registered" % uri)
		# Now sends an event over Ia
		notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
		notification.setHeader("Reason", "probe-registered")
		notification.setApplicationBody({ 'uri': uri, 'type': probeType, 'name': name, 'contact': contact, 'agent-uri': agentUri, 'locked': False })
		self._dispatchNotification(notification)
		self.getLogger().debug("Probe registration complete.")

	def unregisterProbe(self, channel, uri):
		uri = str(uri)
		# We should look for the managing agent first.
		probe = None
		self._lock()
		if self._probes.has_key(uri):
			probe = self._probes[uri]
			del self._probes[uri]
		self._unlock()
		if probe:
			self.getLogger().info("Probe %s unregistered" % uri)

		# Now sends an event over Ia
		notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
		notification.setHeader("Reason", "probe-unregistered")
		notification.setApplicationBody({ 'uri': uri, 'type': probe['type'], 'name': probe['name'], 'contact': probe['contact'], 'agent-uri': probe['agent-uri'] })
		self._dispatchNotification(notification)

	##
	# Ia subscriptions
	##
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
			self.getLogger().info("Unsubscription attempt for a non-known uri. Discarding.")
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

	def registerIaClient(self, channel):
		self._lock()
		self._iaClients.append(channel)
		self._unlock()
		CounterManager.instance().inc("server.tacs.iachannels.current")

	def unregisterIaClient(self, channel):
		"""
		Unregister an Ia client connection:
		- purge its subscriptions, if any,
		- purge its probe locks, if any,
		- remove it from the known clients.
		"""
		self._lock()
		for (uri, clients) in self._subscriptions.items():
			if channel in clients:
				clients.remove(channel)
			# Garbage collection
			if len(clients) == 0:
				del self._subscriptions[uri]
		if channel in self._iaClients:
			self._iaClients.remove(channel)
		# Locks
		unlockedUris = []
		for probe in self._probes.values():
			if probe['locks'].has_key(channel):
				del probe['locks'][channel]
				# Keep it for unlocking notification outside the critical section
				unlockedUris.append(probe['uri'])
		self._unlock()

		for uri in unlockedUris:		
			self.getLogger().info("channel %s unlocked probe %s (on channel disconnection)" % (str(channel), uri))
			# Now sends an event over Ia to notify the new state
			notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
			notification.setHeader("Reason", "probe-unlocked")
			notification.setApplicationBody({ 'uri': uri })
			self._dispatchNotification(notification)
		
		CounterManager.instance().dec("server.tacs.iachannels.current")

	def _dispatchNotification(self, notification):
		"""
		Forwards the notification to all subscribing clients.

		@type  notification: Notification message
		@param notification: the notification to forward to subscribed listeners
		"""
		uri = str(notification.getUri()) # make sure we deal with URI strings, not URI objects
		self.getLogger().debug("Dispatching notification on Ia for %s..." % uri)
		nbClients = 0
		self._lock()
		if not self._subscriptions.has_key(uri):
			self._unlock()
			return
		for channel in self._subscriptions[uri]:
			try:
				self._iaServer.sendNotification(channel, notification)
				nbClients += 1
			except:
				self.getLogger().warning("Unable to send a notification to a client")
		self._unlock()
		self.getLogger().debug("Notification dispatched to %d Ia clients" % nbClients)
	
	##
	# TACS Northbound API (exposed through Ia)
	##
	def triSAReset(self, uri):
		uri = str(uri)
		probe = None
		self._lock()
		if self._probes.has_key(uri):
			probe = self._probes[uri]
		self._unlock()
		if probe:
			self._xaServer.triSAReset(probe['channel'], probe['uri'])
		else:
			raise TacsException("Probe %s not available on controller" % uri)

	def triUnmap(self, uri):
		uri = str(uri)
		probe = None
		self._lock()
		if self._probes.has_key(uri):
			probe = self._probes[uri]
		self._unlock()
		if probe:
			self._xaServer.triUnmap(probe['channel'], probe['uri'])
		else:
			raise TacsException("Probe %s not available on controller" % uri)

	def triMap(self, uri):
		uri = str(uri)
		probe = None
		self._lock()
		if self._probes.has_key(uri):
			probe = self._probes[uri]
		self._unlock()
		if probe:
			self._xaServer.triMap(probe['channel'], probe['uri'])
		else:
			raise TacsException("Probe %s not available on controller" % uri)

	def getRegisteredProbes(self):
		ret = []
		self._lock()
		for probe in self._probes.values():
			self.getLogger().info('probe locking: ' + str(probe['locks']))
			ret.append({ 'agent-uri': probe['agent-uri'], 'uri': probe['uri'], 'type': probe['type'], 'name': probe['name'], 'contact': probe['contact'], 'locked': (probe['locks'] != {}) })
		self._unlock()
		return ret
	
	def getProbeInfo(self, uri):
		info = None
		self._lock()
		if self._probes.has_key(uri):
			probe = self._probes[uri]
			info = { 'agent-uri': probe['agent-uri'], 'uri': probe['uri'], 'type': probe['type'], 'name': probe['name'], 'contact': probe['contact'], 'locked': (probe['locks'] != {}) }
		self._unlock()
		return info

	def getRegisteredAgents(self):
		ret = []
		self._lock()
		for agent in self._agents.values():
			ret.append({ 'uri': agent['uri'], 'supported-probes': agent['supported-probes'], 'contact': agent['contact'], 'user-agent': agent['user-agent'] })
		self._unlock()
		return ret
	
	def lockProbe(self, channel, probeUri):
		"""
		Verifies that the probe is available (ie registered and not locked by another channel).
		If it's ok, lock the probe for this channel.
		Locks are purged on UNLOCK from the same channel or on channel disconnection.

		Automatic associated events unsubscription.
		
		NB: flaw: if a locked probe is unregistered then re-registered, its lock disappears.
		"""
		self._lock()
		if self._probes.has_key(probeUri):
			probe = self._probes[probeUri]
			if not probe['locks'] or channel in probe['locks']: # accept re-locking
				probe['locks'][channel] = True
				self._unlock()
				self.getLogger().info("channel %s locked probe %s" % (str(channel), probe['uri']))
				# Automatic subscription for the probe if the lock is OK
				self.subscribe(channel, probe['uri'])

				# Now sends an event over Ia to notify the new state
				notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
				notification.setHeader("Reason", "probe-locked")
				notification.setApplicationBody({ 'uri': probe['uri'] })
				self._dispatchNotification(notification)
				
				return True
			else:
				self._unlock()
				raise TacsException("", 404, "Probe Already Locked")
		self._unlock()
		raise TacsException("", 404, "Probe Not Found")

	def unlockProbe(self, channel, probeUri):
		"""
		Verifies that the unlocker is the one which lock the probe, then unlocks it.
		Automatic associated events unsubscription.
		"""
		self._lock()
		# Check that the probe is locked by this channel
		if self._probes.has_key(probeUri):
			probe = self._probes[probeUri]
			if channel in probe['locks']:
				del probe['locks'][channel]
				self._unlock()
				self.getLogger().info("channel %s unlocked probe %s" % (str(channel), probe['uri']))
				# Automatic unsubscription for the probe if the unlock is OK
				self.unsubscribe(channel, probe['uri'])

				# Now sends an event over Ia to notify the new state
				notification = Messages.Notification("PROBE-EVENT", "system:probes", "Ia", "1.0")
				notification.setHeader("Reason", "probe-unlocked")
				notification.setApplicationBody({ 'uri': probe['uri'] })
				self._dispatchNotification(notification)
				return True
			else:
				self._unlock()
				raise TacsException("", 403, "Probe Not Locked by This Client")
		self._unlock()
		raise TacsException("", 404, "Probe Not Found")

	def triSend(self, uri, request):
		"""
		Forwards a TRI-SEND operation, expect a response.
		"""
		uri = str(uri)
		probe = None
		self._lock()
		if self._probes.has_key(uri):
			probe = self._probes[uri]
		self._unlock()
		
		if probe:
			# FIXME: what do we rewrite the message ??
			req = Messages.Request("TRI-SEND", uri, "Xa", "1.0")
			req.setHeader("SUT-Address", request.getHeader("SUT-Address"))
			req.setContentType(request.getContentType())
			req.setContentEncoding(request.getContentEncoding())
			req.setBody(request.getBody())
			self._xaServer.triSend(probe['channel'], req)
		else:
			raise TacsException("Probe %s not available on controller" % uri)

	def triExecuteTestCase(self, uri, request):
		"""
		Forwards a TRI-SEND operation, expect a response.
		"""
		uri = str(uri)
		probe = None
		self._lock()
		if self._probes.has_key(uri):
			probe = self._probes[uri]
		self._unlock()
		
		if probe:
			# FIXME: what do we rewrite the message ??
			req = Messages.Request("TRI-EXECUTE-TESTCASE", uri, "Xa", "1.0")
			req.setContentType(request.getContentType())
			req.setContentEncoding(request.getContentEncoding())
			req.setBody(request.getBody())
			self._xaServer.triExecuteTestCase(probe['channel'], req)
		else:
			raise TacsException("Probe %s not available on controller" % uri)

	def deployProbe(self, agentUri, probeName, probeType):
		"""
		Forwards a DEPLOY operation, expects a response.
		"""
		uri = str(agentUri)
		agent = None
		self.getLogger().info("Deploying probe %s, type %s on %s" % (probeName, probeType, uri))
		self._lock()
		if self._agents.has_key(uri):
			agent = self._agents[uri]
		self._unlock()
		
		if agent:
			# Check that probeName is not already deployed on this agent
			# TODO (NB: the agent is able to check it locally, too)
			# Check that agent supports this probeType (the agent is also able to check it locally)
			if not probeType in agent['supported-probes']:
				raise TacsException("Agent %s does not support the probe type %s" % (uri, probeType))
			self._xaServer.deploy(channel = agent['channel'], agentUri = uri, probeName = probeName, probeType = probeType)
		else:
			raise TacsException("Agent %s not available on controller" % uri)

	def undeployProbe(self, agentUri, probeName):
		"""
		Forwards a UNDEPLOY operation, expects a response.
		"""
		uri = str(agentUri)
		agent = None
		self.getLogger().info("Undeploying probe %s, on %s" % (probeName, uri))
		self._lock()
		if self._agents.has_key(uri):
			agent = self._agents[uri]
		self._unlock()
		
		if agent:
			# Check that probeName is already deployed on this agent
			# TODO (NB: the agent is able to check it locally, too)
			self._xaServer.undeploy(channel = agent['channel'], agentUri = uri, probeName = probeName)
		else:
			raise TacsException("Agent %s not available on controller" % uri)

	##
	# Technical callbacks
	##
	def onTriEnqueueMsg(self, channel, notification):
		"""
		Forward from Xa to Ia (to probe's subscribers)
		"""
		self._dispatchNotification(notification)
	
	def onLog(self, channel, notification):
		"""
		Forward to subscribers for the probe
		"""
		self._dispatchNotification(notification)

def main():
	parser = optparse.OptionParser(version = "Testerman Agent Controller Server %s" % Versions.getAgentControllerVersion())
	parser.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug traces on (default: %default)", default = False)
	parser.add_option("-d", dest = "daemonize", action = "store_true", help = "daemonize (default: do not daemonize)", default = False)
	parser.add_option("--ia-ip", dest = "iaIp", metavar = "ADDRESS", help = "set listening Ia IP address to ADDRESS (default: %default)", default = "127.0.0.1")
	parser.add_option("--ia-port", dest = "iaPort", metavar = "PORT", help = "set listening Ia port to PORT (default: %default)", default = 8087, type="int")
	parser.add_option("--xa-ip", dest = "xaIp", metavar = "ADDRESS", help = "set listening Xa IP address to ADDRESS (default: %default)", default = "0.0.0.0")
	parser.add_option("--xa-port", dest = "xaPort", metavar = "PORT", help = "set listening Xa port to PORT (default: %default)", default = 40000, type="int")
	parser.add_option("--log-filename", dest = "logFilename", metavar = "FILE", help = "set log filename to FILE (default: output to stdout)", default = None)
	parser.add_option("--pid-filename", dest = "pidFilename", metavar = "FILE", help = "use FILE to dump the process PID when daemonizing (default: no pidfile)", default = None)

	(options, args) = parser.parse_args()

	# Initialize logger
	if options.debug:
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', filename = options.logFilename)
	
	# Display startup info
	getLogger().info("Starting Testerman Agent Controller Server %s" % (Versions.getAgentControllerVersion()))
	getLogger().info("Agent interface    (Xa) listening on tcp://%s:%d" % (options.xaIp, options.xaPort))
	getLogger().info("Internal interface (Ia) listening on tcp://%s:%d" % (options.iaIp, options.iaPort))

	# Now we can daemonize if needed
	if options.daemonize:
		if options.pidFilename:
			getLogger().info("Daemonizing, using pid file %s..." % options.pidFilename)
		else:
			getLogger().info("Daemonizing...")
		Tools.daemonize(pidFilename = options.pidFilename, displayPid = True)

	try:
		controller = Controller(xaAddress = (options.xaIp, options.xaPort), iaAddress = (options.iaIp, options.iaPort))
		controller.start()
	except Exception, e:
		print "Unable to start server: " + str(e)
		getLogger().critical("Unable to start server: " + str(e))
		try:
			controller.stop()
		except: pass
		logging.shutdown()
		return
		
	controller.getLogger().info("Started.")

	try:
		while 1:
			time.sleep(0.1)
	except KeyboardInterrupt:	
		getLogger().info("Shutting down Testerman Agent Controller...")
		controller.stop()
	
	# When the controller stops() (Keyboard interrupt, etc)
	controller.finalize()
	getLogger().info("Done.")
	logging.shutdown()

if __name__ == "__main__":
	main()
