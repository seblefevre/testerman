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

class Probe:
	def __init__(self):
		self.__agent = None
		self.__name = None
		self.__type = None

	##
	# Functions to ensure correct Probe management by the Agent
	##

	def attachToAgent(self, agent, name, type_):
		self.__agent = agent
		self.__type = type_
		self.__name = name

	def getUri(self):
		return "probe:%s@%s" % (self.__name, self.__agent.getNodeName())
	
	def getName(self):
		return self.__name
	
	def getType(self):
		return self.__type
	
	def getAgent(self):
		return self.__agent
	
	##
	# Convenience functions provided to Probe implementors
	##
	
	def notifyReceived(self, message, sutAddress = None, profile = Messages.Message.CONTENT_TYPE_PYTHON_PICKLE):
		"""
		Creates a RECEIVED notification message over XA and sends it.
		
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
		msg = Messages.Notification(method = "RECEIVED", uri = self.getUri(), protocol = "Xa", version = "1.0")
		msg.setApplicationBody(message, profile)
		msg.setHeader("SUT-Address", sutAddress)
		msg.setHeader("Probe-Name", self.getName())
		return self.__agent.notify(msg)

	def logSentPayload(self, label, payload):
		"""
		Creates a LOG notification message over XA and sends it,
		for "sent" payload logging.
		
		@type  event: the event, any python type
		@param event: the event to raise.
		
		@rtype: boolean
		@returns: True in case of a success, False otherwise [but this is a notification...]
		"""
		msg = Messages.Notification(method = "LOG", uri = self.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Log-Class", "sent-payload")
		msg.setHeader("Probe-Name", self.getName())
		msg.setApplicationBody({'label': label, 'payload': payload})
		return self.__agent.notify(msg)
	
	def logReceivedPayload(self, label, payload):
		"""
		Creates a LOG notification message over XA and sends it,
		for "sent" payload logging.
		
		@type  event: the event, any python type
		@param event: the event to raise.
		
		@rtype: boolean
		@returns: True in case of a success, False otherwise [but this is a notification...]
		"""
		msg = Messages.Notification(method = "LOG", uri = self.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Log-Class", "received-payload")
		msg.setHeader("Probe-Name", self.getName())
		msg.setApplicationBody({'label': label, 'payload': payload})
		return self.__agent.notify(msg)
	
	def checkArgs(self, args, defaultValues = []):
		"""
		Checks that all mandatory arguments are present, based on default values.
		Adds default values for non-existing arguments in args.
		
		@type  defaultValues: list of tuple (string, <any>)
		@param defaultValues: list of default values and expected args in args as tuples (argname, defaultValue)
		                      If the default value is None, implies that argname is mandatory and must be provided
		                      in args.
		@type  args: dict[string] of <any>
		@param args: the provided arguments and their initial values.
		
		@throws: ProbeException in case of a missing mandatory argument.
		
		@rtype: None
		@returns: None
		"""
		try:
			missingArgs = []
			for (argName, defaultValue) in defaultValues:
				if not args.has_key(argName):
					if defaultValue is None:
						missingArgs.append(argName)
					else:
						args[argName] = defaultValue
			if not missingArgs:
				# OK
				return
			else:
				# Missing arguments
				raise ProbeException("Missing mandatory parameter(s): %s" % ', '.join(missingArgs))
		except Exception, e:
			self.debug("checkArgs: %s" % str(e))
			raise e

	##
	# To reimplement in your probe implementations
	##
	
	def onSend(self, message, sutAddress):
		"""
		@type  arg: depends on what was sent over XA by the probe stub
		@param arg: the arguments related to the SEND method invoked on the probe. 
		
		@rtype: None
		@returns: None
		
		@throws: ProbeException in case of probe-level errors
		"""
		raise ProbeException("Not implemented")
	
	def onReset(self):
		"""
		@rtype: None
		@returns: None

		@throws: ProbeException in case of probe-level errors
		"""
		raise ProbeException("Not implemented")
	
	def getLogger(self):
		return logging.getLogger('Agent.%s' % self.getName())
	
	def info(self, txt):
		self.getLogger().info(txt)

	def debug(self, txt):
		self.getLogger().debug(txt)

	def error(self, txt):
		self.getLogger().error(txt)

	def warning(self, txt):
		self.getLogger().warning(txt)
	

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
		self.debug("Sending a response:\n%s" % str(resp))
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
		self.info("Connected.")
		self.info("Registering agent...")
		self.channel = channel
		try:
			self.registerAgent()
		except Exception, e:
			self.error("Unable to register agent: " + str(e))
			self.error("Disconnecting for a later attempt")
			self.disconnect(self.channel)
			return
			
		self.info("Agent registered")
		self.info("Registering probes...")
		for probe in self.probes.values():
			try:
				self.registerProbe(probe)
			except Exception, e:
				self.warning("Unable to register probe %s (%s)" % (str(probe.getUri()), str(e)))

		self.info("Probes registered")
	
	def onDisconnection(self, channel):
		self.info("Disconnected")
		self.registered = False
		
	def onRequest(self, channel, transactionId, request):
		self.debug("Received a request:\n%s" % str(request))
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
					if method == "SEND":
						probe.onSend(request.getApplicationBody(), request.getHeader('SUT-Address'))
						self.response(transactionId, 200, "OK")
					elif method == "RESET":
						probe.onReset()
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
		self.warning("Received a notification, discarding:\n" + str(message))

	def onResponse(self, channel, transactionId, message):
		self.warning("Received an asynchronous response, discarding:\n" + str(message))

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
		self.info("Deploying probe %s, type %s..." % (name, type_))
		if not type_.startswith("remote."):
			type_ = "remote." + type_
		if not getProbeClasses().has_key(type_):
			raise Exception("No factory registered for probe type %s" % type_)
		
		if self.probes.has_key(name):
			raise Exception("A probe with this name is already deployed on this agent")

		probe = getProbeClasses()[type_]()
		probe.attachToAgent(self, name, type_)
		# We reference the probe as deployed, though the registration may fail...
		self.probes[name] = probe

		# We should raise exception in case of duplicated names, ...
		if self.registered:
			self.registerProbe(probe)
		else:
			self.info("Deferred probe registration: agent not registered yet.")

	def undeployProbe(self, name):
		"""
		Unregister an existing probe.
		Raises an exception in case of any error.
		"""
		self.info("Undeploying probe %s..." % (name))
		
		if not self.probes.has_key(name):
			raise Exception("Probe currently not deployed on this agent.")

		probe = self.probes[name]
		# Remove the probe, regardless of what happens next
		del self.probes[name]

		# We should raise exception in case of duplicated names, ...
		if self.registered:
			self.unregisterProbe(probe)
		else:
			self.info("No probe unregistration: agent not registered yet.")
	
	def registerProbe(self, probe):
		"""
		Sends a REGISTER request over XA to register the probe uri, type type_
		on the TACS.
		"""
		self.info("Registering probe %s, type %s, uri %s..." % (probe.getName(), probe.getType(), probe.getUri()))
		msg = Messages.Request(method = "REGISTER", uri = probe.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Probe-Type", probe.getType())
		msg.setHeader("Probe-Name", probe.getName())
		msg.setHeader("Agent-Uri", self.getUri())
		response = self.request(msg)
		if not response:
			raise Exception("Timeout")

		if response.getStatusCode() != 200:
			raise Exception("Unable to register: " + response.getReasonPhrase())
		self.info("Probe %s registered" % probe.getUri())
		
	def unregisterProbe(self, probe):
		"""
		Sends a UNREGISTER request over XA to register the probe uri, type type_
		on the TACS.
		"""
		self.info("Registering probe %s, type %s, uri %s..." % (probe.getName(), probe.getType(), probe.getUri()))
		msg = Messages.Request(method = "UNREGISTER", uri = probe.getUri(), protocol = "Xa", version = "1.0")
		msg.setHeader("Probe-Type", probe.getType())
		msg.setHeader("Probe-Name", probe.getName())
		response = self.request(msg)
		if not response:
			raise Exception("Timeout")

		if response.getStatusCode() != 200:
			raise Exception("Unable to unregister: " + response.getReasonPhrase())
		self.info("Probe %s unregistered" % probe.getUri())

	def registerAgent(self):
		self.registered = False
		req = Messages.Request(method = "REGISTER", uri = self.getUri(), protocol = "Xa", version = "1.0")
		# we should add a list of supported probe types, os, etc ?
		req.setHeader("Agent-Supported-Probe-Types", ','.join(getProbeClasses().keys()))
		response = self.request(req)
		if not response:
			raise Exception("Timeout")

		if response.getStatusCode() != 200:
			raise Exception("Unable to register: " + response.getReasonPhrase())

		self.registered = True
		self.info("Agent %s registered" % self.getUri())
		
		
		
	
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

# Contains the Class (python obj) of the probe, indexed by its probeType (probeId)
ProbeClasses = {}

def getProbeClasses():
	return ProbeClasses

def registerProbeClass(type_, class_):
	# For the internal registrations, all probe types are started with a remote.
	if not type_.startswith("remote."):
		type_ = "remote." + type_
	if ProbeClasses.has_key(type_):
		getLogger().warning("Not registering class for probe type %s: already registered" % type_)
	ProbeClasses[type_] = class_
	getLogger().info("%s type has been registered" % type_)

################################################################################
# Main
################################################################################

def initialize(probePaths = ["probes"], codecPaths = ["../codecs"]):
	# CodecManager logging diversion
	CodecManager.instance().setLogCallback(logging.getLogger("Agent.CD").debug)
	# Loading plugins: probes & codecs
	currentDir = os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__)))
	scanPlugins(["%s/%s" % (currentDir, x) for x in codecPaths], label = "codec")
	scanPlugins(["%s/%s" % (currentDir, x) for x in probePaths], label = "probe")
