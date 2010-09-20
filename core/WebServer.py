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
# Testerman Server - main.
#
##

import ConfigManager
import Tools
import Versions

import airspeed 

import logging
import BaseHTTPServer
import os.path
import socket
import base64

DEFAULT_PAGE = "/index.vm"


cm = ConfigManager.instance()

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('Web')


################################################################################
# Servable content types
################################################################################

# File extension to content-type mapping
ContentTypes = {
	'vm': 'text/html', # Velocity/airspeed templates
	'html': 'text/html',
	'htm': 'text/html',
	'jpg': 'image/jpeg',
	'jpe': 'image/jpeg',
	'jpeg': 'image/jpeg',
	'png': 'image/png',
	'gif': 'image/gif',
	'ico': 'image/x-icon',
	'xml': 'application/xml',
	'xsl': 'application/xml',
	'xsd': 'application/xml',
	'vcss': 'text/css', # Velocity/airspeed templates
	'css': 'text/css',
	'js': 'application/javascript',
	'txt': 'text/plain',
	'py': 'text/x-python',
	'tar': 'application/x-tar',
	'tgz': 'application/x-gtar',
}


class AuthenticationError(Exception):
	pass



################################################################################
# Main request handler: Application Dispatcher
################################################################################

class WebRequest:
	"""
	This is the object a WebApplication can interact with a client.
	It abstracts all the low-level stuff.
	"""
	def __init__(self, handler, path, contextRoot):
		self.__handler = handler
		# Normalize the path, making sure a path always start with a /.
		if not path.startswith('/'):
			path = '/' + path
		self.__path = path
		self.__contextRoot = contextRoot

	def getPath(self):
		"""
		Returns the path of the request, relative to the application context root.
		"""
		return self.__path

	def __str__(self):
		return "[%s] cr=%s local path=%s" % (self.getCommand(), self.getContextRoot(), self.getPath())

	def getRequestVersion(self):
		return self.__handler.request_version

	def getRawRequestLine(self):
		return self.__handler.requestline

	def getCommand(self):
		return self.__handler.command

	def getHeaders(self):
		return self.__handler.headers

	def getServerPath(self):
		"""
		Returns the path of the request as served by the server (incudes the context root)
		"""
		return self.__handler.path

	def getContextRoot(self):
		"""
		Returns the context root the request has been served in.
		"""
		return self.__contextRoot

	def getClientAddress(self):
		return self.__handler.client_address

	def write(self, t):
		return self.__handler.wfile.write(t)

	def sendError(self, code, message = None):
		return self.__handler.send_error(code, message)

	def sendResponse(self, code, message = None):
		return self.__handler.send_response(code, message)

	def sendHeader(self, keyword, value):
		return self.__handler.send_header(keyword, value)

	def endHeaders(self):
		return self.__handler.end_headers()


class WebApplicationDispatcherMixIn:
	"""
	This mixin request handler provides a do_GET implementation only,
	and is used to:
	- complete the XMLRPC request handler (that provides a do_POST implementation)
	  to handle basic component distribution system to a testerman server (on Ws interface)
	- to implement the Wc interface, providing Testerman clients features via
	  the web (called the WebClient).
	"""

	# Register applications in this map: context-root: WebApplicationClass
	# for instance: '/webclient': { 'class': WebClientApplication, 'parameters': { ... } }
	_applications = {}

	@classmethod
	def registerApplication(cls, contextRoot, applicationClass, **kwargs):
		"""
		Use this function to register a new web application.
		kwargs will be passed to your WebApplication subclass initializer.
		"""
		cls._applications[contextRoot] = dict(appclass = applicationClass, parameters = kwargs)

	def do_GET(self):
		"""
		Dispatches the request to a registered application.
		"""
		# Locate the application based on the initial request path.
		# This is a best matching on registered context roots.
		path = self.path
		if not path.startswith('/'):
			path = '/' + path
		
		# Matches the context root only on the "directory part" of the path
		p = os.path.split(self.path)[0]
		contextRoot = ''
		for cr in self._applications.keys():
			if p.startswith(cr) and len(cr) > len(contextRoot):
				contextRoot = cr

		application = self._applications.get(contextRoot)
		if application:
			webRequest = WebRequest(self, path = self.path[len(contextRoot):], contextRoot = contextRoot)
			app = application['appclass'](**application['parameters'])
			app.request = webRequest
			getLogger().debug("Forwarding request %s to %s" % (webRequest, app))
			return app.do_GET()
		else:
			self.send_error(404)
	

################################################################################
# Template & static contents serving request handler
################################################################################

class WebApplication:
	"""
	Base class to create a "Web Application" that can register into the
	WebApplicationDispatcherMixIn handler.

	It can server the usual static contents as well as
	airspeed/velocity based templates, and is able to manage a basic authentication.
	"""

	# If you want to authenticate your users, provide a realm
	#	and reimplement the authenticate() method.
	
	def __init__(self, documentRoot = '', debug = False, authenticationRealm = None):
		self.request = None
		self._documentRoot = documentRoot
		self._debug = debug
		self._authenticationRealm = authenticationRealm

	def authenticate(self, username, password):
		return True
	
	def _authenticate(self):
		self.username = None
		if not self._authenticationRealm:
			return

		authorization = self.request.getHeaders().get('authorization')
		if not authorization:
			raise AuthenticationError('Authentication required')
		kind, data = authorization.split(' ')
		if not kind == 'Basic':
			raise AuthenticationError('Unsupported authentication type')
		
		username, password = base64.decodestring(data).split(':', 1)
		if not self.authenticate(username, password):
			raise AuthenticationError('Authentication failure')

		getLogger().info("Authenticated as user %s" % (username))	
		self.username = username

	def _getDocumentRoot(self):
		return self._documentRoot
	
	def _getDebug(self):
		return self._debug
	
	def _getClient(self):
		return self.request.getClient()

	def _isTemplate(self, path):
		_, ext = os.path.splitext(path)
		return ext in ['.vm', '.vcss']
	
	def do_GET(self):
		try:
			self._authenticate()
		except AuthenticationError, e:
			self.request.sendResponse(401)
			self.request.sendHeader('WWW-Authenticate', 'Basic realm="%s"' % self._authenticationRealm)
			self.request.endHeaders()
			self.request.write('Authentication failure')
			return

		path = self.request.getPath()
		
		if path == '/':
			path = DEFAULT_PAGE
		
		parsed = path.split('?', 1)
		if len(parsed) == 2:
			path, args = parsed[0], parsed[1]
		else:
			path, args = path, None

		try:
			handler = 'handle_%s' % path[1:]
			# If we have a specific handler to serve the request, call it.
			if hasattr(self, handler):
				getLogger().debug("Requested dynamic resource: %s" % path[1:])
				getattr(self, handler)(args)
			# Airspeed template ?
			elif self._isTemplate(path):
				getLogger().debug("Requested airspeed template: %s" % path[1:])
				self._serveTemplate(path)
			# Fallback to serving files (static contents)
			else:
				getLogger().debug("Requested static file: %s" % path[1:])
				self._serveFile(path)
		except Exception:
			if self._getDebug():
				self.request.sendError(500, Tools.getBacktrace())
			else:
				self.request.sendError(500)

	def _serveFile(self, path):
		"""
		First checks that we have the right to serve the file,
		then serves it.
		"""
		path = os.path.abspath("%s/%s" % (self._getDocumentRoot(), path))
		
		getLogger().debug("Requested file: %s" % path)
		
		if not path.startswith(self._getDocumentRoot()):
			# The query is outside the web docroot. Forbidden.
			self.request.sendError(403)
			return

		self._rawServeFile(path)
		
	def _rawServeFile(self, path, asFilename = None, xform = None):
		"""
		Serves the file without additional verifications.
		If asFilename is set, sends the file as attachment.
		"""
		# Check if the file exists
		try:
			f = open(path)
			contents = f.read()
			f.close()
		except:
			self.request.sendError(404)
		else:
			try:
				if xform:
					contents = xform(contents)
			except:
				# Internal transformation error
				self.request.sendError(500)
			else:
				contentType = self._getContentType(path)
				if not contentType:
					# Unsupported media type
					self.request.sendError(415)
					return

				self.request.sendResponse(200)
				self.request.sendHeader('Content-Type', contentType)
				if asFilename:
					self.request.sendHeader('Content-Disposition', 'attachment; filename="%s"' % asFilename)
				self.request.endHeaders()
				self.request.write(contents)

	def _getContentType(self, path):
		"""
		Returns the content-type/mime-type associated to the
		file to serve.
		"""
		_, ext = os.path.splitext(path)
		if ext:
			return ContentTypes.get(ext[1:])
		else:
			return None

	def _sendContent(self, txt, contentType = "text/plain", asFilename = None):
		"""
		Convenience function.
		"""
		self.request.sendResponse(200)
		self.request.sendHeader('Content-Type', contentType)
		if asFilename:
			self.request.sendHeader('Content-Disposition', 'attachment; filename="%s"' % asFilename)
		self.request.endHeaders()
		self.request.write(txt)

	##
	# Templates (airspeed based)
	##
	def _serveTemplate(self, path, context = None):
		path = os.path.abspath("%s/%s" % (self._getDocumentRoot(), path))
		
		getLogger().debug("Requested template: %s" % path)
		
		if not path.startswith(self._getDocumentRoot()):
			# The query is outside the web docroot. Forbidden.
			self.request.sendError(403)
			return
		
		self._rawServeTemplate(path, context)
	
	def _rawServeTemplate(self, path, context = None):
		"""
		Serves a template, applying the context or
		a default context if none is provided.
		This DOES NOT check that the template is in the
		web document root.
		
		@param path: absolute path to the template to serve
		@type  path: string
		@param context: the context to apply to the template.
		@type  context: dict
		"""
		try:
			f = open(path)
			contents = f.read()
			f.close()
		except:
			self.request.sendError(404)
			return

		contentType = self._getContentType(path)
		if not contentType:
			# Unsupported media type
			self.request.sendError(415)
			return
		
		# Apply the template
		template = airspeed.Template(contents)
		if context is None:
			context = self._getDefaultTemplateContext()
		
		context['contextroot'] = self.request.getContextRoot()
		
		output = template.merge(context)
		self.request.sendResponse(200)
		self.request.sendHeader('Content-Type', contentType)
		self.request.endHeaders()
		self.request.write(output)
	
	def _getDefaultTemplateContext(self):
		"""
		Returns a dict of values that will be made available for
		all templates.
		"""
		# All configuration and internal (transient) values
		ret = { 'context-root': self.request.getContextRoot(), 'config': {}, 'internal': {}}
		for v in cm.getVariables():
			ret['config'][v['key'].replace('.', '_')] = v['actual']
		for v in cm.getTransientVariables():
			ret['internal'][v['key'].replace('.', '_')] = v['value']

		# Published components
		if cm.get('testerman.document_root'):
			updateFile = '%s/updates.xml' % cm.get('testerman.document_root')
			um = UpdateMetadataWrapper(updateFile)
			try:
				ret['components'] = um.getComponentsList()
			except:
				if self._getDebug():
					getLogger().error(Tools.getBacktrace())

		# More to come
		return ret


class TestermanWebApplication(WebApplication):
	"""
	This application completes the base one with dynamic resources
	handlers implementations.
	
	Used to serve GET requests over the Ws interface, to
	download installers, component, and offer other
	server-oriented services.
	"""
	##
	# Dynamic resources handlers
	##

	def handle_teapot(self, args):
		"""
		Test function.
		"""
		self.request.sendError(418)
	
	def handle_qtestermaninstaller(self, args):
		"""
		Sends the latest installer script to install QTesterman.
		Substitute a default server/port on the fly.
		"""
		def xform(source):
			# The Ws connection url could be constructed from multipe sources:
			# - the HTTP 1.1 host header, if any
			# - the web connection IP address (self.connection.getsockname())
			#   but this is an IP address and not very friendly. However, it will always
			#   work, as the web listener is the same as for the Ws interface.
			# - from a dedicated configuration variable so that the admin
			#   can set a valid, resolvable hostname to connect to the server instead of an IP address.
			# - using the interface.ws.port and the local hostname, but this hostname
			#   may not be resolved by the client. However, we'll opt for this option as a fallback for now
			#   (more user friendly, and the chances that the hostname cannot be resolved or
			#   resolved to an incorrect IP/interfaces are low - let me know if you have the need
			#   for the second option instead).
			if "host" in self.request.getHeaders():
				url = 'http://%s' % self.request.getHeaders()["host"]
			else:
				url = 'http://%s:%s' % (socket.gethostname(), cm.get("interface.ws.port"))
			return source.replace('DEFAULT_SERVER_URL = "http://localhost:8080"', 'DEFAULT_SERVER_URL = %s' % repr(url))

		installerPath = os.path.abspath("%s/qtesterman/Installer.py" % cm.get_transient("testerman.testerman_home"))
		# We should pre-configure the server Url on the fly
		self._rawServeFile(installerPath, asFilename = "QTesterman-Installer.py", xform = xform)
	
	def handle_pyagentinstaller(self, args):
		"""
		Sends the latest installer script to install a PyAgent.
		Substitute a default server/port on the fly.
		"""
		def xform(source):
			return source.replace('DEFAULT_TACS_IP = "127.0.0.1"', 'DEFAULT_TACS_IP = %s' % repr(cm.get("interface.xa.ip"))).replace(
			'DEFAULT_TACS_PORT = 40000', 'DEFAULT_TACS_PORT = %s' % repr(int(cm.get("interface.xa.port"))))
		
		installerPath = os.path.abspath("%s/pyagent/agent-installer.py" % cm.get_transient("testerman.testerman_home"))
		# We should pre-configure the server Url on the fly
		self._rawServeFile(installerPath, asFilename = "agent-installer.py", xform = xform)

	def handle_docroot(self, path):
		"""
		Download a file from the testerman (not web) docroot
		"""

		path = os.path.abspath("%s/%s" % (cm.get('testerman.document_root'), path))
		
		getLogger().debug("Requested file: %s" % path)
		
		if not path.startswith(cm.get('testerman.document_root')):
			# The query is outside the testerman docroot. Forbidden.
			self.request.sendError(403)
			return

		self._rawServeFile(path, asFilename = os.path.basename(path))



###############################################################################
# updates.xml reader
###############################################################################

import xml.dom.minidom

class UpdateMetadataWrapper:
	"""
	A class to manage several actions on the updates.xml
	"""
	def __init__(self, filename):
		self._filename = filename
		self._docroot = os.path.split(self._filename)[0]

	def getComponentsList(self):
		"""
		Returns the currently published components and their status.
		"""
		f = open(self._filename, 'r')
		content = ''.join([x.strip() for x in f.readlines()])
		f.close()

		ret = []
		
		doc = xml.dom.minidom.parseString(content)
		for e in doc.firstChild.getElementsByTagName('update'):
			version = e.attributes['version'].value
			component = e.attributes['component'].value
			branch = e.attributes['branch'].value
			url = e.attributes['url'].value
			ret.append(dict(version = version, component = component, branch = branch, archive = url))

		# Ordered by component, then version
		ret.sort(lambda x, y: cmp((x.get('component'), x.get('version')), (y.get('component'), y.get('version'))))
		
		return ret
