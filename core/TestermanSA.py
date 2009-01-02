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
# -*- coding: utf-8 -*-
# Testerman System Adapter implementation.
#
# Implements some of the SA-Provided TTCN-3 TRI interface:
# triSAReset()
# triEecuteTestCase()
# triSend()
# triMap()
# triUnmap()
#
# This file also implements the bridge between the SA and the Test Adapters.
# Test Adapters are called "probes" in Testerman wording.
# A probe is assigned to a tsiPort by a "binding".
# The binding is configurable when designing your System on with a test case
# should run.
# 
# When executing a TestCase, you should provide a TestAdapterConfiguration
# defining the bindings of tsi ports to actual test adapters.
# The TestAdapterConfiguration contains non-TTCN3 defined methods to configure
# its bindings.
##


import TestermanTTCN3 as Testerman 
import TestermanTCI
import TestermanAgentControllerClient as TACC
import TestermanMessages as Messages

################################################################################
# TRI constants
################################################################################

TR_Error = 0
TR_OK = 1


################################################################################
# The usual shortcuts
################################################################################

def log(msg):
	TestermanTCI.logInternal("SA: %s" % str(msg))


################################################################################
# Local exceptions
################################################################################

class ProbeException(Exception): pass

################################################################################
# The TRI interface
################################################################################

# Maintain the bindings between tsiPorts and probes
# Probe instance, indexed by tsiPortId
ProbeBindings = {}

def triSAReset():
	"""
	Disconnects all existing connections to the SUT.
	
	In our case, this is an opportunity to reset() all probes in use (implictly: by the current testcase).
	To call when a test case if over.
	"""
	for probe in ProbeBindings.values():
		try:
			probe.onTriSAReset()
		except Exception, e:
			log("triSAReset: error on probe %s during onTriSAReset(): %s" % (probe.getUri(), str(e)))
		if probe.isRemote():
			# Actually, we sould only do this on probes that were actually locked, i.e.
			# not necessarely all of them if we stop our testcase because we were not able
			# to lock them all...
			TACC.instance().unlockProbe(probe.getUri())
			unregisterWatchedProbe(probe)
	return TR_OK

def triExecuteTestCase(testCaseId, tsiPortList):
	"""
	Prepares all static connections to the SUT.
	
	tsiPortList is extracted from the System object on which the testcase is executed.
	
	For each port, we check that a binding exists.
	If not, we raise an exception.
	For each binding, we initialize it using Probe.onTriExecuteTestCase()
	
	@type  testCaseId: string
	@param testCaseId: the testcase name. Ignored in this implementation.
	@type  tsiPortList: list of strings
	@param tsiPortList: the list of tsiPortIds (as string).
	"""
	for tsiPortId in tsiPortList:
		if ProbeBindings.has_key(tsiPortId):
			probe = ProbeBindings[tsiPortId]
			if probe.isRemote():
				locked = TACC.instance().lockProbe(probe.getUri())
				if not locked:
					raise Testerman.TestermanException("Unable to reserve all probes for this test: %s is already in use" % (probe.getUri()))
				registerWatchedProbe(probe)
			try:
				probe.onTriExecuteTestCase()
			except Exception, e:
				log("triExecuteTestCase: error on probe %s onTriExecuteTestCase(): %s" % (probe.getUri(), str(e)))
		else:
			# No implementation available
			# TODO: provides a default impl ?
			# Maybe we should - but not yet
			raise Testerman.TestermanException("Missing binding for test system port '%s'. Please check your current Test Adapter Configuration." % tsiPortId)
			
	return TR_OK

def triSend(componentId, tsiPortId, sutAddress, message):
	"""
	@type  componentId: string
	@param componentId: the name of the TC that sends the message (not used yet)
	@type  tsiPortId: string
	@param tsiPortId: the name of the system port from which we send the message. Must be bound to a test adapter.
	@type  sutAddress: test adapter/probe dependent
	@param sutAddress: test adapter/probe-dependent (IP address, URL, ...)
	@type  message: test adapter/probe-dependent, but valid "Testerman" message structure
	@param message: test adapter/probe-dependent message (already encoded through possible codecs)
	
	@rtype: integer
	@returns: TR_Error (1) if the probe resource was unavailable or cannot be found.
	          TR_OK (0) if the resource was correctly acquired.
	@throws: TestermanException, Exception
	"""
	# Look for a test adapter bound to this system port
	if not ProbeBindings.has_key(tsiPortId):
		raise Testerman.TestermanException("Internal error: trying to send a message through unbound test system port %s" % tsiPortId)

	# Test adapter found. Send the message through it.
	probe = ProbeBindings[tsiPortId]
	try:
		probe.send(message, sutAddress)
	except Exception, e:
		raise Testerman.TestermanException("Unable to send message through TSI port %s: " % tsiPortId + str(e))

	return TR_OK

# This is the map that is filled with triMap, unfilled with triUnmap, and that makes
# the associated between a tsiPortId and a PortImpl.
# number of mapping (int), indexed by the tsiPortId
TsiPortMappings = {}

def triMap(compPortId, tsiPortId):
	"""
	Associates a test component port to a test system interface port.
	At SA level, in this implementation, it means:
	- making sure that the tsiPort is bound, i.e. a test adapter implementation is attached to it,
	- establish dynamic connections to the SUT, if needed, through probe.onTriMap(), only for the
	  first mapping for this testcase.

	Still in this implementation, the TTCN3 level is responsible for managing the association
	between tsiPorts and tcPorts. So we won't manage it here.

	@type  compPortId: string
	@param compPortId: the TestComponentPort instance mapped to the tsiPort (for information only, we won't use it)
	@type  tsiPortId: string
	@param tsiPortId: the name of the port on the System.

	@rtype: integer
	@returns: TR_Error (1) in case of an error, TR_OK (0) if the probe was correctly released
	"""
	currentMappingCount = 0
	if TsiPortMappings.has_key(tsiPortId):
		currentMappingCount = TsiPortMappings[tsiPortId]

	if not currentMappingCount:
		# First mapping.
		# Check that a test adapter implementation exists for this tsiPort
		if not ProbeBindings.has_key(tsiPortId):
			raise Testerman.TestermanException("triMap: test system interface port %s is not bound no any implementation, and was likely not declared on your system/test adapter configuration." % tsiPortId)
		probe = ProbeBindings[tsiPortId]
		# Establish dynamic connections, if needed
		probe.onTriMap()
		
	currentMappingCount += 1
	TsiPortMappings[tsiPortId] = currentMappingCount
	
	log("triMap: %s mapping OK, existing binding" % tsiPortId)
	return TR_OK

def triUnmap(compPortId, tsiPortId):
	"""
	@type  compPortId: string
	@param compPortId: test component port name being unmapped
	@type  tsiPortId: string
	@param tsiPortId: the name of the system port to unmap
	"""
	if not TsiPortMappings.has_key(tsiPortId):
		# Attempt to unmap a non-mapped port.
		return TR_Error

	currentMappingCount = TsiPortMappings[tsiPortId]
	
	currentMappingCount -= 1
	if currentMappingCount == 0:
		# OK, we can release everything.
		del TsiPortMappings[tsiPortId]
		probe = ProbeBindings[tsiPortId]
		try:
			probe.onTriUnmap()
		except:
			pass
		log("triMap: %s unmapping OK, no more other mapping" % tsiPortId)
	else:
		TsiPortMappings[tsiPortId] = currentMappingCount
		log("triMap: %s unmapping OK, remaining mapping: %d" % (tsiPortId, currentMappingCount))
		
	return TR_OK


################################################################################
# General functions
################################################################################

def initialize(tacsAddress):
	"""
	Initializes the AgentController proxy (client).
	"""
	TACC.initialize("TE", tacsAddress)
	TACC.instance().setReceivedNotificationCallback(onReceivedNotification)
	TACC.instance().setLogNotificationCallback(onLogNotification)

def finalize():
	log("finalizing...")
	TACC.finalize()
	log("Finalized.")


################################################################################
# main Agent/Controller callback
################################################################################

WatchedProbes = {}

def registerWatchedProbe(probe):
	WatchedProbes[probe.getUri()] = probe

def unregisterWatchedProbe(probe):
	if WatchedProbes.has_key(probe.getUri()):
		del WatchedProbes[probe.getUri()]

def onLogNotification(probeUri, logClass, logInfo):
	probeUri = str(probeUri)
	try:
		# if we receive the notification, that's we subscribe for the probe - normally
		if not WatchedProbes.has_key(probeUri): 
			return

		if logClass == "system-sent":
			label = logInfo["label"]
			payload = logInfo["payload"]
			# TODO/FIXME: retrieve the tsiPort from the probeUri
			TestermanTCI.logSystemSent(tsiPort = probeUri, label = label, payload = payload)

		elif logClass == "system-received":
			label = logInfo["label"]
			payload = logInfo["payload"]
			# TODO/FIXME: retrieve the tsiPort from the probeUri
			TestermanTCI.logSystemReceived(tsiPort = probeUri, label = label, payload = payload)

	except Exception, e:
		log("Exception in onLogNotification: " + str(e))

def onReceivedNotification(probeUri, message, sutAddress):
	"""
	Called when receiving a RECEIVED event from a probe
	"""
	probeUri = str(probeUri)
	try:
		if WatchedProbes.has_key(probeUri):
			probe = WatchedProbes[probeUri]
			probe.onReceived(message, sutAddress)

	except Exception, e:
		log("Exception in onReceivedNotification: " + str(e))

################################################################################
# Test Adapters configuration management (bindings)
################################################################################

##
# Special, non TTCN3 class to configure Test Adapters.
#
# Declares the bindings between tsiPorts and TestAdapters (ie probes),
# with their optional configuration, if any.
##
class TestAdapterConfiguration(object):
	def __init__(self, name = None):
		self._name = name
		self._declaredBindings = {}

	def getTsiPortList(self):
		return self._declaredBindings.keys()
	
	def bindByUri(self, tsiPort, uri, type_, **kwargs):
		"""
		Simply *declares* a binding.
		The actual binding setup is deferred to _install().
		"""
		self._declareBinding(tsiPort, uri, type_, **kwargs)
	
	def bindByType(self, tsiPort, type_, **kwargs):
		"""
		Any location, "anonymous binding" - autodeploy ? or select an existing probe based on type_ ?
		"""
		pass

	def _declareBinding(self, tsiPort, uri, type_, **kwargs):
		if self._declaredBindings.has_key(tsiPort):
			raise Testerman.TestermanException("Test system interface port %s is already bound to a Test Adapter." % tsiPort)
		log("Declaring binding: test adapter %s for tsiPort %s..." % (uri, tsiPort))
		self._declaredBindings[tsiPort] = { 'uri': uri, 'parameters': kwargs, 'type': type_ }
	
	def _install(self):
		"""
		Installs bindings for current testcase(s).
		
		Actually checks that probes are deployed.
		
		@throws TestermanException if we are unable to find a valid test adapter matching uri and type_, or
		if we cannot autodeploy it.
		"""
		for tsiPort, binding in self._declaredBindings.items():
			log("Installing binding: test adapter %s for tsiPort %s..." % (binding['uri'], tsiPort))
			probe = createProbe(binding['uri'], binding['type'])

			for name, value in binding['parameters'].items():
				log(u"Setting parameter %s to %s for test adapter %s..." % (name, unicode(value), probe.getUri()))
				probe.setParameter(name, value)
			# Declare the binding in the current TTCN3 world
			bind(tsiPort, probe)

	def _uninstall(self):
		for tsiPort, binding in self._declaredBindings.items():
			log("Uninstalling binding: test adapter %s for tsiPort %s..." % (binding['uri'], tsiPort))
			unbind(tsiPort)

def bind(tsiPortId, probe):
	"""
	Non-TTCN3 / Pure Testerman function.
	
	Associates a tsiPort to a test adapter implementation, i.e. a probe.
	
	This is an association declaration.
	The actual binding, which probe locking, will occur when starting the testcase, through triExecuteTestCase.
	
	@type  tsiPortId: string
	@param tsiPortId: the tsi port name to bind
	@type  probe: Probe instance
	@param probe: the probe to bind to the port
	"""
	if ProbeBindings.has_key(tsiPortId):
		# Actually overring is not very important. But we keep the user from doing so 
		# to avoid "non-standard" cases that may be harder to troubleshoot
		raise Testerman.TestermanException("This system port (%s) is already bound to another probe. Please check your binding declarations." % tsiPortId)
	ProbeBindings[tsiPortId] = probe
	probe.bind(tsiPortId)
		
def unbind(tsiPortId):
	if ProbeBindings.has_key(tsiPortId):
		del ProbeBindings[tsiPortId]


################################################################################
# Probes (ie Test Adapters) management
################################################################################

class Probe:
	"""
	A Probe is a Test Adapter implementation that must be bound to a tsiPort
	prior to being accessed.
	
	A Probe is uniquely identified on the Testerman system by a URI:
	probe:<name>@<agent-name> for distributed probes,
	or
	probe:<name> for local probes (? to confirm).
	
	When setting up a binding, you actually binds a probe URI to the tsiPort.
	During this binding, we verify that the probe exists in the system, based on
	its URI + type.
	If it does not exists and can be deployed, we deploy it.
	If not, the binding setup fails with an exception.
	
	The actual probe locking (for distributed probes) only occurs on triMap, 
	however, not on setting up the binding.
	"""
	def __init__(self):
		self._type = None
		self._remote = False
		self._uri = None
		self._tsiPortId = None
		self._parameters = {}

	##
	# For Probe manager
	##
	def attachToUri(self, uri, type_):
		"""
		Local probes will accept the URI without any problem.
		Remote probes will check that a probe of their type actually exists on the TACS.
		If not, autodeploy ?
		"""
		self._uri = uri
		self._type = type_

	def bind(self, tsiPortId):
		self._tsiPortId = tsiPortId

	def isRemote(self):
		return self._remote
	
	def setParameter(self, name, value):
		self._parameters[name] = value

	##
	# Convenience functions for probe implementors
	##
	def getType(self):
		return self._type
	
	def getUri(self):
		return self._uri
	
	def __getitem__(self, name):
		return self._parameters.get(name, None)
	
	def enqueueMessage(self, message, sutAddress = None):
		"""
		Convenience function for probe implementors.
		
		@type  message: any Python object - must be a valid Testerman structure, however
		@param message: the message to enqueue to userland, i.e. to forward to mapped test component ports
		@type  sutAddress: string
		@param sutAddress: the originating source SUT address, if any.
		"""
		Testerman.triEnqueueMsg(tsiPortId = self._tsiPortId, sutAddress = None, componentId = None, message = message)

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
			raise e

	##
	# To reimplement
	##	
	def send(self, message, sutAddress):
		"""
		This method is called by triSend when we need to send
		a message through this test adapter.
		
		The test adapter/probe may encode the message,
		interpret it as a command, or anything else.
		
		@type  message: any
		@param message: the message to send.
		@type  sutAddress: string
		@param sutAddress: the SUT address to the message should be sent.
		                   The use and meaning if this parameter is
		                   test-adapter-dependent
		
		@throws: Exception or ProbeException in case of an error

		@rtype: None
		@returns: None
		"""
		# Default implementation: can't do anything, raise an error
		raise Exception("send() not implemented for this probe")

	def onReceived(self, message, sutAddress = None):
		"""
		Called when receiving a RECEIVED message from the remote implementation,
		or simple convenience function for local probe implementations.
		"""
		self.enqueueMessage(message, sutAddress)

	def onTriMap(self):
		"""
		Called whenever the probe is mapped.
		You may establish "dynamic" connections here, if any.
		"""
		pass
	
	def onTriUnmap(self):
		"""
		Called whenever the probe is unmapped.
		You typically have nothing to do here.
		You may disconnect "dynamic" connections here, if any.
		"""
		pass
	
	def onTriExecuteTestCase(self):
		"""
		Called when starting a testcase involving this probe.
		This is typically here that you can establish static connections, if any.
		"""
		pass
	
	def onTriSAReset(self):
		"""
		Called when a testcase if over.
		This is typically here that you can reset existing connections, if any.
		"""
		pass

class LocalProbe(Probe): pass

class RemoteProbe(Probe):
	def __init__(self):
		Probe.__init__(self)
		self._remote = True
	
	def attachToUri(self, uri, type_):
		"""
		Check if such a probe already exists on the controller.
		"""
		info = TACC.instance().getProbeInfo(uri)
		if info:
			# Check type
			if type_ and info['type'] != type_:
				raise Testerman.TestermanException("Unable to use probe %s as %s: such a probe is deployed, but its type is %s" % (uri, self._type, info['type']))
			# OK (discarded type or valid type)
			self._uri = uri
			self._type = type_
		elif type_:
			# Autodeployment attempt
			ret = TACC.instance().deployProbe(uri, type_)
			if not ret:
				raise Testerman.TestermanException("Unable to autodeploy %s as %s." % (uri, self._type))
			# Autodeployment OK.
			self._uri = uri
			self._type = type_
		else:
			raise Testerman.TestermanException("Unable to use probe %s: not deployed, no type given, no autodeployment possible." % (uri))


# A default Remote Probe stub implementation, forwarding everything to
# the remote probe, performing reset on map/unmap.
class DefaultRemoteProbe(RemoteProbe):
	def onTriExecuteTestCase(self):
		self.reset()
	
	def onTriSAReset(self):
		self.reset()
	
	def reset(self):
		TACC.instance().reset(self.getUri())
	
	def send(self, message, sutAddress):
		TACC.instance().send(self.getUri(), message, sutAddress)


################################################################################
# Probe as plugins management
################################################################################

#: indexed by their types
RegisteredProbeClasses = {}

def registerProbeClass(type_, probeClass):
	if not RegisteredProbeClasses.has_key(type_):
		RegisteredProbeClasses[type_] = probeClass
		log("registerProbeClass: probe type %s registered" % type_)
	else:
		log("registerProbeClass: probe type %s already registered: discarding" % type_)

def createProbe(uri, type_):
	"""
	Instantiates a new Test Adapter (i.e. a Probe instance) from type_, uri.
	
	If the uri if of the form name@agent, we look for a remote type, prefixing the
	provided type with a "remote." to look for actually implemented type.
	If it does not, this is a local implementation, and we prefix the type with
	"local." (uri form: probe:name)
	
	@type  uri: string
	@param uri: a valid probe uri (probe:name or probe:name@agent)
	@type  type_: string
	@param type_: the test adapter implementation type.
	              Should not start with "remote." or "local.", as the
	              prefix is automatically added based on the uri format.

	@rtype: Probe
	@returns: a new probe instance, unconfigured, or None if no
	          implementation factory was found.
	"""
	# Derive the actual implementation identifier from the uri + given type
	u = Messages.Uri(uri)
	if u.getUser():
		# Remote implementation
		type_ = "remote.%s" % (type_)
	else:
		# Local implementation
		type_ = "local.%s" % (type_)
	
	probeClass = None
	# Let's check the type
	# Explicitly defined ?
	if RegisteredProbeClasses.has_key(type_):
		probeClass = RegisteredProbeClasses[type_]
	# if not, let's use the default remote probe implementation if the probe is remote
	elif type_.startswith('remote.'):
		probeClass = DefaultRemoteProbe

	if probeClass:
		probe = probeClass()
		# May raise an exception if the attachment is not feasible.
		probe.attachToUri(uri, type_)
		return probe
	# Otherwise, nothing to do.
	else:
		raise Testerman.TestermanException("No registered factory for test adapter/probe type %s" % type_)
	
	return None

