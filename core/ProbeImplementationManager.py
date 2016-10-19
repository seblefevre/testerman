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
# Probe Implementation Manager:
# registers Probe Implementations.
#
# May be used (once adapter)
# from a PyAgent or from the TE
# 
##

##
# Probe-related exceptions
##
class ProbeException(Exception): pass

##
# Utilities
##
import traceback
import StringIO
def getBacktrace():
	"""
	Returns the current backtrace.
	"""
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

##
# Main ProbeImplementation Class to implement
##
class ProbeImplementation:
	"""
	Base class for all probe implementation plugins.
	"""
	def __init__(self):
		self.__adapter = None
		self.__defaultProperties = {}
	
	# Internal use only
	def _setAdapter(self, adapter):
		# Called when the implementation is adapted
		self.__adapter = adapter
	
	# Provided to help implement your probe
	def _checkArgs(self, args, defaultValues = []):
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
	
	def _getBacktrace(self):
		"""
		Returns the current backtrace.
		"""
		backtrace = StringIO.StringIO()
		traceback.print_exc(None, backtrace)
		ret = backtrace.getvalue()
		backtrace.close()
		return ret
		
	def _getProperty(self, name, defaultValue = None):
		"""
		Returns a probe parameter, or a default value if not set.
		
		@type  name: string
		@param name: the name of the property
		@type  defaultValue: object
		@param defaultValue: the default value if the parameter is not set
		
		@rtype: object
		@returns: the parameter value, or the default value if not set
		"""
		return self.__adapter.getProperty(name, self.__defaultProperties.get(name, None))

	def setDefaultProperty(self, name, value):
		self.__defaultProperties[name] = value

	def __getitem__(self, name):
		return self._getProperty(name)

	def logSentPayload(self, label, payload, sutAddress = None):
		"""
		Calls this when you need to log a just sent message on the wire.
		
		@type  label: string
		@param label: a human-readable short description of what was sent
		@type  payload: buffer (as string)
		@param payload: the sent payload
		@type  sutAddress: string
		@param sutAddress: the destination SUT address
		"""
		self.__adapter.logSentPayload(label, payload, sutAddress)

	def logReceivedPayload(self, label, payload, sutAddress = None):
		"""
		Calls this when you need to log a just received message on the wire.
		
		@type  label: string
		@param label: a human-readable short description of what was sent
		@type  payload: buffer (as string)
		@param payload: the received payload
		@type  sutAddress: string
		@param sutAddress: the source SUT address
		"""
		self.__adapter.logReceivedPayload(label, payload, sutAddress)

	def getLogger(self):
		"""
		Calls this to get a logging.Logger() compliant instance to
		internally trace your code.
		
		In a TE adapter, all logs are redirected to a logInternal.
		In a PyAgent, redirected to the main logger, with filters.
		"""
		return self.__adapter.getLogger()

	def triEnqueueMsg(self, message, sutAddress = None):
		"""
		Calls this to enqueue a received message.
		
		@type  message: any Python object - must be a valid Testerman structure, however
		@param message: the message to enqueue to userland, i.e. to forward to mapped test component ports
		@type  sutAddress: string
		@param sutAddress: the originating source SUT address, if any.
		"""
		self.__adapter.triEnqueueMsg(message, sutAddress)

	# To implement in your probe - IProbe part
	
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

	def onTriSend(self, message, sutAddress):
		"""
		This method is called by triSend when we need to send
		a message through this test adapter.
		
		The test adapter/probe may encode the message,
		interpret it as a command, or anything else.
		
		Warning: to avoid blocking the testcase, you may return as soon
		as possible, possibly creating a thread to wait for a network
		response.
		
		@type  message: any
		@param message: the message to send.
		@type  sutAddress: string, or None
		@param sutAddress: the SUT address to the message should be sent.
		                   The use and meaning if this parameter is
		                   test-adapter-dependent
		
		@throws: Exception or ProbeException in case of an error

		@rtype: None
		@returns: None
		"""
		# Default implementation: can't do anything, raise an error
		raise Exception("send() not implemented for this probe")
	

class IProbeImplementationAdapter:
	"""
	Internal use only.
	Used to implement Implementation Adapters for PyAgent and TE.
	"""
	# Adapter Manager -> Adapter	
	def getUri(self): pass
	def getName(self): pass
	def getType(self): pass
	def setProperty(self, name, value): pass

	# IProbe part
	def onSend(self, message, sutAddress): pass
	def onTriMap(self): pass
	def onTriUnmap(self): pass
	def onTriExecuteTestCase(self): pass
	def onTriSAReset(self): pass

	# Impl -> Adapter: Adapter provided
	def logSentPayload(self, label, payload, sutAddress = None): pass
	def logReceivedPayload(self, label, payload, sutAddress = None): pass
	def getLogger(self): pass
	def getProperty(self, name, defaultValue): pass
	def triEnqueueMsg(self, message, sutAddress = None): pass


##
# Registration management
##

class DummyLogger:
	def warning(self, txt): pass
	def error(self, txt): pass
	def debug(self, txt): pass
	def critical(self, txt): pass
	def info(self, txt): pass

TheLogger = DummyLogger()

def setLogger(logger):
	# To call to set the global registration logger to something adapted
	global TheLogger
	TheLogger = logger

def getLogger():
	return TheLogger


# Contains the Class (python obj) of the probe implementation, indexed by its probeType (probeId)
ProbeImplementationClasses = {}

def getProbeImplementationClasses():
	return ProbeImplementationClasses

def registerProbeImplementationClass(type_, class_):
	if ProbeImplementationClasses.has_key(type_):
		getLogger().warning("Not registering class for probe type %s: already registered" % type_)
	ProbeImplementationClasses[type_] = class_
	getLogger().info("Probe class %s registered as probe type %s" % (class_.__name__, type_))
