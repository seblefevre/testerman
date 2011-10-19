# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2010,2011 Sebastien Lefevre and other contributors
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

import airspeed 

import logging
import os.path
import socket
import base64
import cgi
try:
	import hashlib
	shaclass = hashlib.sha1
except:
	import sha
	shaclass = sha.sha 

import struct
import time
import threading
import select

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

	def flush(self):
		return self.__handler.wfile.flush()

	def sendError(self, code, message = None):
		self.__handler.send_error(code, message)
		self.__handler.wfile.flush()

	def sendResponse(self, code, message = None):
		self.__handler.send_response(code, message)
		self.__handler.wfile.flush()

	def sendHeader(self, keyword, value):
		return self.__handler.send_header(keyword, value)

	def endHeaders(self):
		return self.__handler.end_headers()
	
	# Things to cleanup/refactor, used to prototype a websocket server
	def _getHandler(self):
		return self.__handler
		
	def read(self, size = -1):
		return self.__handler.rfile.read(size)

	def recv(self, size = 1024):
		return self.__handler.connection.recv(size)
	
	def setCloseCallback(self, cb):
		"""
		Make sure the callback is called when the connection is closed
		"""
		self._onClose = cb
		self.__handler.finish = self._finish

	def _finish(self):
		# Don't forget to do what the basic StreamRequestHandler does
		if not self.__handler.wfile.closed:
			self.__handler.wfile.flush()
		self.__handler.wfile.close()
		self.__handler.rfile.close()
		# Then, our addition
		try:
			self._onClose()
		except:
			pass
		


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

	# Runtime cache to avoid instantiating the same application (same context root) for each request	
	_applicationInstances = {}

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
		p = os.path.split(path)[0]
		contextRoot = ''
		for cr in self._applications.keys():
			if p.startswith(cr) and len(cr) > len(contextRoot):
				contextRoot = cr

		application = self._applications.get(contextRoot)
		if application:
			# check if we have already instanciated the app
#			app = self._applicationInstances.get(contextRoot)
#			if not app:
#				# First instance, put it into the cache
#				app = application['appclass'](**application['parameters'])
#				self._applicationInstances[contextRoot] = app
#		... then use a return app.do_GET(request) instead of a request injection

			app = application['appclass'](**application['parameters'])

			webRequest = WebRequest(self, path = path[len(contextRoot):], contextRoot = contextRoot)
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
	
	def __init__(self, documentRoot = '', debug = False, authenticationRealm = None, theme = "default"):
		self.request = None
		self._documentRoot = documentRoot
		self._debug = debug
		self._authenticationRealm = authenticationRealm
		self._theme = theme

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
	
	def _getClientAddress(self):
		return self.request.getClientAddress()

	def _isTemplate(self, path):
		"""
		Files with a 'secondary' extension are also checked:
		file.vm : template
		file.vm.ext : also a template
		"""
		name, ext = os.path.splitext(path)
		return (ext in ['.vm', '.vcss']) or (os.path.splitext(name)[1] in ['.vm', '.vcss'])
			
	
	def do_GET(self):
		try:
			self._authenticate()
		except AuthenticationError, e:
			self.request.sendResponse(401)
			self.request.sendHeader('WWW-Authenticate', 'Basic realm="%s"' % self._authenticationRealm)
			self.request.endHeaders()
			self.request.write('Authentication failure')
			self.request.flush()
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
				# Keyword arguments
				if args and '&' in args:
					args = cgi.parse_qs(args, True)
					# parse_qs always returns args as values lists.
					# We collapse those list into a single element or None if 1 or 0 elements are in it,
					# preserving only actual lists.
					for k, v in args.items():
						if len(v) == 0:
							args[k] = None
						elif len(v) == 1:
							args[k] = v[0]
					getattr(self, handler)(**args)
				# or raw string
				else:
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
				self.request.flush()

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
		self.request.flush()

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
		
		# Get the template and merge the context parameters		
		template = airspeed.Template(contents)
		defaultContext = self._getDefaultTemplateContext()
		if not context:
			context = {}
		for k in defaultContext:
			if not k in context:
				context[k] = defaultContext[k]
		
		# Apply the template
		output = template.merge(context)
		self.request.sendResponse(200)
		self.request.sendHeader('Content-Type', contentType + ';charset=utf-8')
		self.request.endHeaders()
		self.request.write(output.encode('utf-8'))
		self.request.flush()
	
	def _getDefaultTemplateContext(self):
		"""
		Returns a dict of values that will be made available for
		all templates.
		"""
		# All configuration and internal (transient) values
		ret = { 'config': {}, 'internal': {}}
		for v in cm.getVariables():
			ret['config'][v['key'].replace('.', '_')] = v['actual']
		for v in cm.getTransientVariables():
			ret['internal'][v['key'].replace('.', '_')] = v['value']

		ret['contextroot'] = self.request.getContextRoot()
		ret['theme'] = self._theme

		return ret


class WebSocketFrame:
	"""
	A WebSocket Frame (hybi10)
	"""
	def __init__(self, opcode, payload, maskingKey):
		self.opcode = opcode
		self.payload = ''
		# automatically apply masking key
		if maskingKey:
			index = 0
			for c in payload:
				self.payload += chr(ord(maskingKey[index % len(maskingKey)]) ^ ord(c))
				index += 1
		else:
			self.payload = payload


class WebSocketApplication:
	"""
	Base class to create a WebSocket server that can register into the
	WebApplicationDispatcherMixIn handler.
	
	This class manages the WebSocket handshake.
	
	You just have to inherit from it,
	then implement onMessage(msg) to handle an incoming message,
	and use send(msg) to send a message, or close() to close
	the connection.
	
	This is a minimalist implementation of a WebSocket server, not
	optimized at all, especially with regards to thread management.
	"""

	# If you want to authenticate your users, provide a realm
	#	and reimplement the authenticate() method.
	
	def __init__(self, debug = False, authenticationRealm = None):
		# the request is injected here when it is about to be processed by the application
		self.request = None
		self._debug = debug
		self._authenticationRealm = authenticationRealm
		self.username = None

	def __str__(self):
		return "WebSocket application"
	
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

	def _getDebug(self):
		return self._debug
	
	def _getClientAddress(self):
		return self.request.getClientAddress()

	def do_GET(self):
		# Is basic authentication supported for WebSocket ?
		try:
			self._authenticate()
		except AuthenticationError, e:
			self.request.sendResponse(401)
			self.request.sendHeader('WWW-Authenticate', 'Basic realm="%s"' % self._authenticationRealm)
			self.request.endHeaders()
			self.request.write('Authentication failure')
			self.request.flush()
			return
		
		getLogger().debug("WebSocket handshake handling")
		
		# WebSocket Handshake (version 8+ / draft-ietf-hybi-thewebsocketprotocol-16) [hybi10]
		wsKey1 = self.request.getHeaders().get('Sec-WebSocket-Key')
		host = self.request.getHeaders().get('Host')
		origin = self.request.getHeaders().get('Sec-WebSocket-Origin')
		
		path = self.request.getPath()

		wskey = wsKey1.replace(' ', '')
		GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
		
		token = base64.encodestring(shaclass(wskey + GUID).digest())

		getLogger().debug("Writing handshake response")

		self.request.sendResponse(101, "Switching Protocols")
		self.request.sendHeader('Upgrade', 'websocket')
		self.request.sendHeader('Connection', 'Upgrade')
		self.request.sendHeader('Sec-WebSocket-Accept', token)
#		self.request.endHeaders()
		self.request.flush() # apparently, this adds a \r\n. So no need to call endHeaders() first which does the same thing too
		
		self.request.setCloseCallback(self.onWsClose)

		# Ready		
		getLogger().info("WebSocket link connected from %s" % str(self._getClientAddress()))
		try:
			self.onWsOpen()
		except Exception, e:
			getLogger().error("WebSocket: userland error when handling onWsOpen(): %s" % str(e))
			self.wsClose()

		# Now, wait for new content, detect PDUs, send them to the onMessage handler

		# this code is probably to move into a WebSocketConnection class
		# Actually, this is the classic server loop that wait for events and/or send things.
		# To keep it simple (well, this is a server loop running inside the thread generated by another server loop :-),
		# incoming event handling will be synchronous only, within the server thread.
		h = self.request._getHandler()
		sock = h.connection
		
		self._stopEvent = threading.Event()
		self.buf = ''
		
		while not self._stopEvent.isSet():
			try:
				r, w, e = select.select([ sock ], [], [ sock ], 1)

				# Received an error from the network
				if sock in e:
					raise EOFError("WebSocket: Socket select error: disconnecting")
				
				# Received a message from the network
				if sock in r:
					read = sock.recv(65535)
					if not read:
						raise EOFError("Nothing to read on read event: disconnecting")
					self.buf = ''.join([self.buf, read]) # faster than += r
					self.__on_incoming_data()
				
			except EOFError, e:
				getLogger().info("WebSocket: Disconnected by peer.")
				self.wsClose()

			except socket.error, e:
				getLogger().error("WebSocket: Low level error: " + str(e))
				self.wsClose()

			except Exception, e:
				getLogger().error("WebSocket: Exception in main pool for incoming data: " + str(e))
				self.wsClose()


	def __parseFrames(self):
		"""
		Split the incoming raw Ws stream into Ws Frames.
		"""
		currentFrames = []

		index = 0

		while self.buf:
			try:
				B1 = ord(self.buf[index])
				fin = B1 & 0x80
				opcode = B1 & 0x0f
				B2 = ord(self.buf[index + 1])
				mask = B2 & 0x80
				length = B2 & 0x7f

				if length == 126:
					# length is a 16 bit value
					length = struct.unpack('>H', self.buf[index+2:index+4])
					index += 4
				elif length == 127:
					# length is a 64 bit value
					length = struct.unpack('>Q', self.buf[index+2:index+10])
					index += 10
				else: # standard length < 127
					index += 2

				maskingKey = None

				if mask:
					maskingKey = self.buf[index:index+4]
					index += 4

#				print 80*"#"
#				print "Ws Frame:"
#				print "final: %s" % bool(fin)
#				print "opcode: %x" % opcode
#				print "length: %s" % length
#				print "masked: %s" % bool(mask)
#				print "maskingKey: %s" % repr(maskingKey)

				# No extension negotiated. What remains is the payload.
				payload = self.buf[index:index+length]
				if len(payload) < length:
					getLogger().debug("Missing bytes in websocket frame (got %s, expected %s)" % (len(payload), length))
					break

				currentFrames.append(WebSocketFrame(opcode, payload, maskingKey))

				self.buf = self.buf[index+length:]
			except IndexError:
				getLogger().debug("Missing data Ws stream into frames")
				# not enough data yet
				return currentFrames
			except Exception, e:
				getLogger().debug("Exception while splitting Ws stream into frames: %s" % Tools.getBacktrace())
				return currentFrames

		return currentFrames		


	def __on_incoming_data(self):
		"""
		In (version 8+ / draft-ietf-hybi-thewebsocketprotocol-16 / hybi10)
		data framing is no longer as simple as \xff / \x00 separators.
		
		Byte 0:
		FIN, RSV1, RSV2, RSV3, Opcode(4)
		Byte 1:
		Mask(1), Length(7), possibly continued on next 16 or 64 bits)
		"""
		
		# TODO: support for fragmented frames
		# TODO: support for ping frames
		
		for frame in self.__parseFrames():
			if frame.opcode == 8:
				getLogger().debug("WebSocket: received connection close frame - disconnecting")
				self.wsClose()
				return
			
			elif frame.opcode in [1, 2]:
				getLogger().debug("WebSocket: received message:\n%s" % repr(frame.payload))
				
				if not frame.payload:
					getLogger().debug("WebSocket: received empty payload - disconnecting") # This is not WebSocket RFC compliant, I guess...
					self.wsClose()
					return
				
				try:
					self.onWsMessage(frame.payload)
				except Exception, e:
					getLogger().error("WebSocket: userland exception while handling message:\n%s\n%s" % (repr(msg), Tools.getBacktrace()))
			
			else:
				getLogger().warning("WebSocket: received unsupported frame, opcode %s" % frame.opcode)



	##
	# To reimplement in subclasses
	##

	def onWsMessage(self, msg):
		pass
	
	def onWsClose(self):
		getLogger().info("WebSocket link disconnected from %s" % str(self._getClientAddress()))
	
	def onWsOpen(self):
		pass
	
	##
	# Convenience functions for sub-classes implementing an actual websocket app
	##
	
	def wsSend(self, msg):
		"""
		Create and send a 'WebSocket frame' (hybi10).
		"""
		opcode = 1 # text
		
		b1 = 0x80 | (opcode & 0x0f) # FIN + opcode
		payload_len = len(msg)
		if payload_len <= 125:
			header = struct.pack('>BB', b1, payload_len)
		elif payload_len > 125 and payload_len < 65536:
			header = struct.pack('>BBH', b1, 126, payload_len)
		elif payload_len >= 65536:
			header = struct.pack('>BBQ', b1, 127, payload_len)

		buf = header + msg
		self.request.write(buf)
		self.request.flush()

	def wsClose(self):
		"""
		Close the websocket link
		"""
		self._stopEvent.set()


