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
import cStringIO as StringIO
import tarfile

VERSION = "1.1.1"

################################################################################
# Restarter/Reinitializer facility
################################################################################

class Restarter:
	"""
	Static class that enables to restart a python program at any time.
	
	Usage:
	call Restarter.initialize() as soon as your program is started, before 
	any other operations (in particular argv consumption, chdir)
	
	call Restarter.restart() when you're ready to restart/reinitialize your script.
	It will be executed with the same arguments, from the same path, with the same
	environment as the original one.
	"""
	env = None
	cwd = None
	executable = None
	argv = None
	
	def initialize():
		import os
		import sys
		Restarter.env = os.environ
		Restarter.argv = sys.argv
		Restarter.executable = sys.executable
		Restarter.cwd = os.getcwd()
	
	initialize = staticmethod(initialize)

	def restart():
		import os
		import sys
		args = [ Restarter.executable ] + Restarter.argv
		if sys.platform in [ 'win32', 'win64' ]:
			# we need to quote arguments containing spaces... why ?
			args = map(lambda arg: (' ' in arg and not arg.startswith('"')) and '"%s"' % arg or arg, args)
		os.chdir(Restarter.cwd)
		os.execvpe(Restarter.executable, args, Restarter.env)
		
	restart = staticmethod(restart)

################################################################################
# The usual tools
################################################################################

def getLogger():
	return logging.getLogger('Agent')

def getVersion():
	return VERSION


################################################################################
# Probe Adaptation
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
		self.__properties = {}

	##
	# IProbeImplementationAdapter
	##

	def setProperty(self, name, value):
		self.__properties[name] = value

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

	def getProperty(self, name, defaultValue):
		return self.__properties.get(name, defaultValue)

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
					self.response(transactionId, 200, "OK")
					self.getLogger().info("-- Unregistering --")
					self.unregisterAgent()
					self.getLogger().info("-- Restarting --")
					Restarter.restart()
				elif method == "UPDATE":
					self.getLogger().info("Updating...")
					args = request.getApplicationBody()
					if not args:
						args = {}
					# If a preferredVersion is provided, preferred branches, if provided, are ignored
					preferredVersion = args.get('version', None)
					preferredBranches = args.get('branches', [ 'stable' ])
					ret = self.updateAgent(preferredBranches, preferredVersion)
					self.getLogger().info("Update status: %s" % ret)
					self.response(transactionId, 200, "OK")
				elif method == "KILL":
					self.response(transactionId, 501, "Not implemented")
				else:
					self.getLogger().warning("Received unsupported agent method: %s" % method)
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
					elif method == "TRI-MAP":
						probe.onTriMap()
						self.response(transactionId, 200, "OK")
					elif method == "TRI-UNMAP":
						probe.onTriUnmap()
						self.response(transactionId, 200, "OK")
					elif method == "TRI-EXECUTE-TESTCASE":
						# Set the probe properties
						properties = request.getApplicationBody()
						if properties:
							for name, value in properties.items():
								probe.setProperty(name, value)
						probe.onTriExecuteTestCase()
						self.response(transactionId, 200, "OK")
					elif method == "TRI-SA-RESET":
						probe.onTriSAReset()
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

	def unregisterAgent(self):
		req = Messages.Request(method = "UNREGISTER", uri = self.getUri(), protocol = "Xa", version = "1.0")
		response = self.request(req)
		if not response:
			raise Exception("Timeout")

		if response.getStatusCode() != 200:
			raise Exception("Unable to unregister: " + response.getReasonPhrase())

		self.registered = False
		self.getLogger().info("Agent %s unregistered" % self.getUri())

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
		except:
			self.getLogger().warning("Unable to retrieve update metata on TACS")
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
		@param url: the url of the coponent archive to download, relative to the docroot
		"""
		# We retrieve the archive
		archive = self.getFile(url)
		if not archive:
			raise Exception("Archive file not found on server (%s)" % url)
		
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
				self.getLogger().debug("Unpacking %s into %s..." % (c.name, basepath))
				tfile.extract(c, basepath)
				# TODO: make sure to set write rights to allow future updates
				# os.chmod("%s/%s" % (basepath, c), ....)
			tfile.close()
		except Exception, e:
			archiveFileObject.close()
			raise Exception("Error while unpacking the update archive:\n%s" % str(e))

		archiveFileObject.close()

	def updateAgent(self, preferredBranches = [ 'stable' ], preferredVersion = None):
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
		currentVersion = VERSION
		# basepath is "pyagent/..", where pyagent is the name of the folder contained in the component package.
		basepath = os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__)))
	
		# Get the current available updates	
		updates = self.getComponentVersions(component, branches)
		if not updates:
			# No updates available - nothing to do
			self.getLogger().info("No updates available on this server.")
			return False
		self.getLogger().info("Available updates:\n%s" % "\n".join([ "%s (%s)" % (x['version'], x['branch']) for x in updates]))

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
				self.getLogger().info("Preferred version %s available. Updating." % preferredVersion)
			else:
				self.getLogger().warning("Preferred version %s not available as an update. Not updating." % preferredVersion)
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
				self.getLogger().info("New version available: %s, in branch %s. Updating." % (selectedVersion, selectedBranch))
			else:
				self.getLogger().info("No new version available. Not updating.")

		# OK, now if we have selected a version, let's update.		
		if url:
			try:
				self.installComponent(url, basepath)
			except Exception, e:
				raise Exception("Unable to install the update:\n%s\nContinuing with the current version." % str(e))
	
			self.getLogger().info("Agent updated from %s to %s (%s)" % (currentVersion, selectedVersion, selectedBranch))
			return True
		else:
			return False # No newer version available, or preferred version not available

		
		
		
	
################################################################################
# Probe implementations registration
################################################################################

def scanPlugins(paths, label):
	for path in paths:
		if not path in sys.path:
			sys.path.append(path)
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

def initialize(probePaths = ["plugins/probes"], codecPaths = ["plugins/codecs"]):
	# CodecManager logging diversion
	CodecManager.instance().setLogCallback(logging.getLogger("Agent.Codec").debug)
	# ProbeImplementationManager logging diversion
	ProbeImplementationManager.setLogger(logging.getLogger("Agent.Probe"))
	# Loading plugins: probes & codecs
	currentDir = os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__)))
	scanPlugins(["%s/%s" % (currentDir, x) for x in codecPaths], label = "codec")
	scanPlugins(["%s/%s" % (currentDir, x) for x in probePaths], label = "probe")
