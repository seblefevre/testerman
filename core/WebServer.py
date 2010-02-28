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


################################################################################
# Template & static contents serving request handler
################################################################################

class WebRequestHandlerMixIn:
	"""
	This mixin request handler provides a do_GET implementation only,
	and is used to complete a XMLRPC request handler (providing a do_POST
	implementation).
	
	It can server the usual static contents as well as
	airspeed/velocity based templates.
	"""
	def _isTemplate(self, path):
		_, ext = os.path.splitext(path)
		return ext in ['.vm', '.vcss']
	
	def do_GET(self):
		if not self.path.startswith('/'):
			self.path = '/' + self.path

		if self.path == '/':
			self.path = DEFAULT_PAGE
		
		parsed = self.path.split('?', 1)
		if len(parsed) == 2:
			path, args = parsed[0], parsed[1]
		else:
			path, args = self.path, None

		print "DEBUG: %s, %s" % (path, args)

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
			if cm.get("ts.debug"):
				self.send_error(500, Tools.getBacktrace())
			else:
				self.send_error(500)

	def _serveFile(self, path):
		"""
		First checks that we have the right to serve the file,
		then serves it.
		"""
		docroot = cm.get("testerman.web.document_root")
		path = os.path.abspath("%s/%s" % (docroot, path))
		
		getLogger().debug("Requested file: %s" % path)
		
		if not path.startswith(docroot):
			# The query is outside the docroot. Forbidden.
			self._sendError(403)
			return

		self._rawServeFile(path)
		
	def _rawServeFile(self, path, asFilename = None):
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
			self.send_error(404)
		else:
			contentType = self._getContentType(path)
			if not contentType:
				# Unsupported media type
				self._sendError(415)
				return

			self.send_response(200)
			self.send_header('Content-Type', contentType)
			if asFilename:
				self.send_header('Content-Disposition', 'attachment; filename="%s"' % asFilename)
			self.end_headers()
			self.wfile.write(contents)

	def _sendError(self, code):
		"""
		Convenience function.
		"""
		self.send_error(code)

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

	##
	# Templates (airspeed based)
	##
	def _serveTemplate(self, path):
		docroot = cm.get("testerman.web.document_root")
		path = os.path.abspath("%s/%s" % (docroot, path))
		
		getLogger().debug("Requested template: %s" % path)
		
		if not path.startswith(docroot):
			# The query is outside the docroot. Forbidden.
			self._sendError(403)
			return
		
		self._rawServeTemplate(path)
	
	def _rawServeTemplate(self, path):
		try:
			f = open(path)
			contents = f.read()
			f.close()
		except:
			self.send_error(404)
			return

		contentType = self._getContentType(path)
		if not contentType:
			# Unsupported media type
			self._sendError(415)
			return
		
		# Apply the template
		template = airspeed.Template(contents)
		context = self._getDefaultTemplateContext()
		output = template.merge(context)
		self.send_response(200)
		self.send_header('Content-Type', contentType)
		self.end_headers()
		self.wfile.write(output)
	
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

		# Published components
		updateFile = '%s/updates.xml' % cm.get('testerman.document_root')
		um = UpdateMetadataWrapper(updateFile)
		try:
			ret['components'] = um.getComponentsList()
		except:
			if cm.get('ts.debug'):
				getLogger().error(Tools.getBacktrace())

		# More to come
		return ret

	##
	# Dynamic resources handlers
	##

	def handle_teapot(self, args):
		"""
		Test function.
		"""
		self.send_error(418)
	
	def handle_qtestermaninstaller(self, args):
		"""
		Sends the latest installer script to install QTesterman.
		"""
		installerPath = os.path.abspath("%s/qtesterman/Installer.py" % cm.get_transient("testerman.testerman_home"))
		# We should pre-configure the server Url on the fly
		self._rawServeFile(installerPath, asFilename = "QTesterman-Installer.py")
	
	def handle_docroot(self, path):
		"""
		Download a file from the testerman (not web) docroot
		"""

		docroot = cm.get("testerman.document_root")
		path = os.path.abspath("%s/%s" % (docroot, path))
		
		getLogger().debug("Requested file: %s" % path)
		
		if not path.startswith(docroot):
			# The query is outside the docroot. Forbidden.
			self._sendError(403)
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
