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
# Testerman PyAgent stub.
# 
##


import TestermanMessages as Messages
import TestermanNodes as Nodes
import CodecManager
import ProbeImplementationManager

import time
import os
import sys
import threading
import logging


VERSION = "1.0.0"

################################################################################
# The usual tools
################################################################################

def getLogger():
	return logging.getLogger('Agent')

def getVersion():
	return VERSION

################################################################################
# Probe interface / sample implementation
################################################################################

class ProbeException(Exception):
	def __init__(self, label):
		Exception.__init__(self, label)

class ProbeImplementationAdapter(ProbeImplementationManager.IProbeImplementationAdapter):
	"""
	A Probe Implementation Adapter to host a ProbeImplementation in a PyAgent.
	"""
	def __init__(self, agent, name, type_, probeImplementation):
		self.__agent = agent
		self.__name = name
		self.__type = type_
		self.__probeImplementation = probeImplementation
		self.__probeImplementation._setAdapter(self)
		self.__parameters = {}

	##
	# IProbeImplementationAdapter
	##

	def setParameter(self, name, value):
		self.__parameters[name] = value

	def getUri(self):
		return "probe:%s@%s" % (self.__name, self.__agent.getNodeName())
	
	def getName(self):
		return self.__name
	
	def getType(self):
		return self.__type

	# Methods provided for the adapted Probe Implementation
	
	def triEnqueueMsg(self, message, sutAddress = None):
		self._triEnqueueMsg(message, sutAddress, profile = Messages.Message.CONTENT_TYPE_PYTHON_PICKLE)
	
	def _triEnqueueMsg(self, message, sutAddress, profile):
		"""
		Creates a TRI-ENQUEUE-MSG notification message over XA and sends it.
		
		You may select the encoding used for the body. The default, python/pickle,
		is safe and the preferred encoding when sending to the TACS.
		
		@type  event: the event, any python type
		@param event: the event to raise.
		@type  sutAddress: the sutAddress the message has been received from (if applicable)
		@param sutAddress: string
		@type  profile: enum in Messages.Message.CONTENT_TYPE*
		@param profile: the body encoding profile, as defined in Messages.Message
		
		@rtype: boolean
		@returns: True in case of a success, False otherwise [but this is a notification...]
		"""
		self.getLogger().debug("triEnqueueing to the TACS...")
		msg = Messages.Notification(method = "TRI-ENQUEUE-MSG", uri = self.getUri(), protocol = "Xa", version = "1.0")
		msg.setApplicationBody(message, profile)
		msg.setHeader("SUT-Address", sutAddress)
		msg.setHeader("Probe-Name", self.getName())
		return self.__agent.notify(msg)

	def logSentPayload(self, label, payload):
		"""
		Creates a LOG notification message over XA and sends it,
		for "sent" payload logging.
		
		@type  label: string
		@param label: a short description of the sent message
		@type  payload: string (as buffer)
		@param payload: the (raw) sent message
		
		@rtype: boolean
		@returns: True in case of a success, False otherwise [but this is a notification...]
		"""
		msg = Messages.Notification(method = "LOG", uri = self.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Log-Class", "system-sent")
		msg.setHeader("Probe-Name", self.getName())
		msg.setApplicationBody({'label': label, 'payload': payload}, profile = Messages.Message.CONTENT_TYPE_PYTHON_PICKLE)
		return self.__agent.notify(msg)
	
	def logReceivedPayload(self, label, payload):
		"""
		Creates a LOG notification message over XA and sends it,
		for "received" payload logging.
		
		@type  label: string
		@param label: a short description of the received message
		@type  payload: string (as buffer)
		@param payload: the (raw) received message
		
		@rtype: boolean
		@returns: True in case of a success, False otherwise [but this is a notification...]
		"""
		msg = Messages.Notification(method = "LOG", uri = self.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Log-Class", "system-received")
		msg.setHeader("Probe-Name", self.getName())
		msg.setApplicationBody({'label': label, 'payload': payload}, profile = Messages.Message.CONTENT_TYPE_PYTHON_PICKLE)
		return self.__agent.notify(msg)

	def getParameter(self, name, defaultValue):
		return self.__parameters.get(name, defaultValue)

	def getLogger(self):
		return logging.getLogger('Agent.%s' % self.getName())
	
	##
	# IProbe part implementation
	##
	
	def onTriSend(self, message, sutAddress):
		self.__probeImplementation.onTriSend(message, sutAddress)

	def onTriMap(self):
		self.__probeImplementation.onTriMap()

	def onTriUnmap(self):
		self.__probeImplementation.onTriUnmap()

	def onTriExecuteTestCase(self):
		self.__probeImplementation.onTriExecuteTestCase()

	def onTriSAReset(self):
		self.__probeImplementation.onTriSAReset()
		
	
	

################################################################################
# The Agent itself
################################################################################


class Agent(Nodes.ConnectingNode):
	def __init__(self, name = None):
		Nodes.ConnectingNode.__init__(self, name = name, userAgent = "PyTestermanAgent/%s" % getVersion())
		self.mutex = threading.RLock()
		#: Declared probes, indexed by their name
		self.probes = {}
		# Xa channel id to communicate with the TACS
		self.channel = None
		#: current agent registration status
		self.registered = False

	def getUri(self):
		return "agent:%s" % self.getNodeName()

	def getVersion(self):
		return getVersion()

	##
	# Convenience functions.
	##

	def notify(self, message):
		self.sendNotification(self.channel, message)
	
	def request(self, request):
		response = self.executeRequest(self.channel, request)
		return response
	
	def response(self, transactionId, status, reason, body = None):
		resp = Messages.Response(status, reason)
		if body:
			resp.setBody(body)
		self.getLogger().debug("Sending a response:\n%s" % str(resp))
		self.sendResponse(self.channel, transactionId, resp)

	##
	# ConnectingNode reimplementation
	##

	def getLogger(self):
		return getLogger()
	
	def info(self, txt):
		self.getLogger().info(txt)
	
	def debug(self, txt):
		self.getLogger().debug(txt)

	def error(self, txt):
		self.getLogger().error(txt)

	def warning(self, txt):
		self.getLogger().warning(txt)

	def onConnection(self, channel):
		self.getLogger().info("Connected.")
		self.getLogger().info("Registering agent...")
		self.channel = channel
		try:
			self.registerAgent()
		except Exception, e:
			self.getLogger().error("Unable to register agent: " + str(e))
			self.getLogger().error("Disconnecting for a later attempt")
			self.disconnect(self.channel)
			return
			
		self.getLogger().info("Agent registered")
		self.getLogger().info("Registering probes...")
		for probe in self.probes.values():
			try:
				self.registerProbe(probe)
			except Exception, e:
				self.getLogger().warning("Unable to register probe %s (%s)" % (str(probe.getUri()), str(e)))

		self.getLogger().info("Probes registered")
	
	def onDisconnection(self, channel):
		self.getLogger().info("Disconnected")
		self.registered = False
		
	def onRequest(self, channel, transactionId, request):
		self.getLogger().debug("Received a request:\n%s" % str(request))
		method = request.getMethod()
		uri = request.getUri()
		
		try:

			if uri.getScheme() == "agent":
				# Agent-level request
				if method == "DEPLOY":
					probeInfo = request.getApplicationBody()
					self.deployProbe(name = probeInfo['probe-name'], type_ = probeInfo['probe-type'])
					self.response(transactionId, 200, "OK")
				elif method == "UNDEPLOY":
					probeInfo = request.getApplicationBody()
					self.undeployProbe(name = probeInfo['probe-name'])
					self.response(transactionId, 200, "OK")
				elif method == "RESTART":
					self.response(transactionId, 501, "Not implemented")
				elif method == "KILL":
					self.response(transactionId, 501, "Not implemented")
				else:
					self.response(transactionId, 505, "Not supported")

			elif uri.getScheme() == "probe":
				# Probe-level request
				# Check correct 'routing'
				if uri.getDomain() != self.getNodeName():
					self.response(transactionId, 404, "Probe not found (incorrect agent)")
				# First, look for the probe.
				name = uri.getUser()
				probe = self.probes.get(name, None)
				if not probe:
					self.response(transactionId, 404, "Probe not found")
				else:
					if method == "TRI-SEND":
						probe.onTriSend(request.getApplicationBody(), request.getHeader('SUT-Address'))
						self.response(transactionId, 200, "OK")
					elif method == "TRI-SA-RESET":
						probe.onTriSAReset()
						self.response(transactionId, 200, "OK")
					elif method == "TRI-MAP":
						probe.onTriMap()
						self.response(transactionId, 200, "OK")
					elif method == "TRI-UNMAP":
						probe.onTriSAReset()
						self.response(transactionId, 200, "OK")
					elif method == "TRI-EXECUTE-TESTCASE":
						parameters = request.getApplicationBody()
						if parameters:
							for name, value in parameters.items():
								probe.setParameter(name, value)
						probe.onTriExecuteTestCase()
						self.response(transactionId, 200, "OK")
					else:
						self.response(transactionId, 505, "Not supported")

			else:
				# Other scheme
				self.response(transactionId, 505, "Not supported")			

		except ProbeException, e:
			self.response(transactionId, 516, "Probe error", str(e) + "\n" + Nodes.getBacktrace())

		except Exception, e:
			self.response(transactionId, 515, "Internal server error", str(e) + "\n" + Nodes.getBacktrace())
		
	def onNotification(self, channel, message):
		"""
		Notification: nothing to support in this Agent.
		"""
		self.getLogger().warning("Received a notification, discarding:\n" + str(message))

	def onResponse(self, channel, transactionId, message):
		self.getLogger().warning("Received an asynchronous response, discarding:\n" + str(message))

	def initialize(self, controllerAddress, localAddress):
		Nodes.ConnectingNode.initialize(self, controllerAddress, localAddress)

	##
	# Agent actual services implementation.
	##		
	
	def deployProbe(self, type_, name):
		"""
		Instantiates and registers a new probe.
		Raises an exception in case of any error.
		"""
		self.getLogger().info("Deploying probe %s, type %s..." % (name, type_))
		if not ProbeImplementationManager.getProbeImplementationClasses().has_key(type_):
			raise Exception("No factory registered for probe type %s" % type_)
		
		if self.probes.has_key(name):
			raise Exception("A probe with this name is already deployed on this agent")

		probeImplementation = ProbeImplementationManager.getProbeImplementationClasses()[type_]()
		probe = ProbeImplementationAdapter(self, name, type_, probeImplementation)
		# We reference the probe as deployed, though the registration may fail...
		self.probes[name] = probe

		# We should raise exception in case of duplicated names, ...
		if self.registered:
			self.registerProbe(probe)
		else:
			self.getLogger().info("Deferred probe registration: agent not registered yet.")

	def undeployProbe(self, name):
		"""
		Unregister an existing probe.
		Raises an exception in case of any error.
		"""
		self.getLogger().info("Undeploying probe %s..." % (name))
		
		if not self.probes.has_key(name):
			raise Exception("Probe currently not deployed on this agent.")

		probe = self.probes[name]
		# Remove the probe, regardless of what happens next
		del self.probes[name]

		# We should raise exception in case of duplicated names, ...
		if self.registered:
			self.unregisterProbe(probe)
		else:
			self.getLogger().info("No probe unregistration: agent not registered yet.")
	
	def registerProbe(self, probe):
		"""
		Sends a REGISTER request over XA to register the probe uri, type type_
		on the TACS.
		"""
		self.getLogger().info("Registering probe %s, type %s, uri %s..." % (probe.getName(), probe.getType(), probe.getUri()))
		msg = Messages.Request(method = "REGISTER", uri = probe.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Probe-Type", probe.getType())
		msg.setHeader("Probe-Name", probe.getName())
		msg.setHeader("Agent-Uri", self.getUri())
		response = self.request(msg)
		if not response:
			raise Exception("Timeout")

		if response.getStatusCode() != 200:
			raise Exception("Unable to register: " + response.getReasonPhrase())
		self.getLogger().info("Probe %s registered" % probe.getUri())
		
	def unregisterProbe(self, probe):
		"""
		Sends a UNREGISTER request over XA to register the probe uri, type type_
		on the TACS.
		"""
		self.getLogger().info("Registering probe %s, type %s, uri %s..." % (probe.getName(), probe.getType(), probe.getUri()))
		msg = Messages.Request(method = "UNREGISTER", uri = probe.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Probe-Type", probe.getType())
		msg.setHeader("Probe-Name", probe.getName())
		response = self.request(msg)
		if not response:
			raise Exception("Timeout")

		if response.getStatusCode() != 200:
			raise Exception("Unable to unregister: " + response.getReasonPhrase())
		self.getLogger().info("Probe %s unregistered" % probe.getUri())

	def registerAgent(self):
		self.registered = False
		req = Messages.Request(method = "REGISTER", uri = self.getUri(), protocol = "Xa", version = "1.0")
		# we should add a list of supported probe types, os, etc ?
		req.setHeader("Agent-Supported-Probe-Types", ','.join(ProbeImplementationManager.getProbeImplementationClasses().keys()))
		response = self.request(req)
		if not response:
			raise Exception("Timeout")

		if response.getStatusCode() != 200:
			raise Exception("Unable to register: " + response.getReasonPhrase())

		self.registered = True
		self.getLogger().info("Agent %s registered" % self.getUri())
		
		
		
	
################################################################################
# Probe implementations registration
################################################################################

def scanPlugins(paths, label):
	for path in paths:
		if not path in sys.path:
			sys.path.append(path)
	for path in paths:
		try:
			for m in os.listdir(path):
				if m.startswith('__init__') or not (os.path.isdir(path + '/' + m) or m.endswith('.py')) or m.startswith('.'):
					continue
				if m.endswith('.py'):
					m = m[:-3]
				try:
					__import__(m)
				except Exception, e:
					getLogger().warning("Unable to import %s %s: %s" % (m, label, str(e)))
		except Exception, e:
			getLogger().warning("Unable to scan %s path for %ss: %s" % (path, label, str(e)))

################################################################################
# Main
################################################################################

def initialize(probePaths = ["probes"], codecPaths = ["../codecs"]):
	# CodecManager logging diversion
	CodecManager.instance().setLogCallback(logging.getLogger("Agent.CD").debug)
	# ProbeImplementationManager logging diversion
	ProbeImplementationManager.setLogger(logging.getLogger("Agent"))
	# Loading plugins: probes & codecs
	currentDir = os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__)))
	scanPlugins(["%s/%s" % (currentDir, x) for x in codecPaths], label = "codec")
	scanPlugins(["%s/%s" % (currentDir, x) for x in probePaths], label = "probe")
