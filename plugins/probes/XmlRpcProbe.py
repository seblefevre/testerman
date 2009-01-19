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
# XML RPC client probe.
# 
##

import ProbeImplementationManager

import xmlrpclib

class ServerProxy(xmlrpclib.ServerProxy):
	"""
	Reimplemented to catch encoded payloads
	"""
	def __init__(self, probe, uri, transport=None, encoding=None, verbose=0,
        		 allow_none=0, use_datetime=0):
		xmlrpclib.ServerProxy.__init__(self, uri, transport, encoding, verbose, allow_none, use_datetime)
		self._probe = probe
		# establish a "logical" server connection

		# get the url
		import urllib
		type, uri = urllib.splittype(uri)
		if type not in ("http", "https"):
			raise IOError, "unsupported XML-RPC protocol"
		self.__host, self.__handler = urllib.splithost(uri)
		if not self.__handler:
			self.__handler = "/RPC2"

		if transport is None:
			if type == "https":
				transport = xmlrpclib.SafeTransport(use_datetime=use_datetime)
			else:
				transport = xmlrpclib.Transport(use_datetime=use_datetime)
		self.__transport = transport

		self.__encoding = encoding
		self.__verbose = verbose
		self.__allow_none = allow_none

	def __request(self, methodname, params):
		request = xmlrpclib.dumps(params, methodname, encoding=self.__encoding,
                		allow_none=self.__allow_none)
		self._probe.getLogger().debug("DEBUG: xml-rpc request: %s" % request)

		response = self.__transport.request(
			self.__host,
			self.__handler,
			request,
			verbose=self.__verbose
		)

		self._probe.getLogger().debug("DEBUG: xml-rpc response: %s" % response)

		if len(response) == 1:
				response = response[0]

		return response
	
	def __getattr__(self, name):
		# magic method dispatcher
		return xmlrpclib._Method(self.__request, name)


class XmlRpcClientProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	TODO: asynchronous implementation
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self.setDefaultProperty('server_url', 'http://localhost')
	
	def onTriMap(self):
		pass
	
	def onTriUnmap(self):
		pass
	
	def onTriSAReset(self):
		pass
	
	def onTriSend(self, message, sutAddress):
		try:
			(operation, args) = message
		except:
			raise Exception("Invalid message format")
		
		proxy = ServerProxy(self, self['server_url'])
	
		# The following code should be executed in a dedicated thread
		try:
			f = getattr(proxy, operation)
			if isinstance(args, list):
				ret = f(*args)
			elif isinstance(args, dict):
				ret = f(**args)
			else:
				ret = f(args)
			event = ('response', ret)
		except xmlrpclib.Fault, e:
			event = ('fault', { 'code': e.faultCode, 'string': e.faultString })
		# Raise other exceptions if needed
		
		self.triEnqueueMsg(event)
			
ProbeImplementationManager.registerProbeImplementationClass('xmlrpc.client', XmlRpcClientProbe)		

	
