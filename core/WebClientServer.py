#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008,2009,2010 Sebastien Lefevre and other contributors
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
# This is the WebClient Server module.
# This runs a web server to offer simple
# Testerman client capabilities through a web page,
# such as:
# browsing the repositories,
# execute an ATS
# display logs & ATS execution results, etc.
# 
#
# This has been implemented outside the embedded
# Testerman to be run on a different box.
#
##


import WebServer
import Tools
import ConfigManager
import TestermanClient

import logging
import BaseHTTPServer
import os.path
import socket
import select
import threading
import sys
import time
import optparse
import re


VERSION = '0.1.0'


DEFAULT_PAGE = "/index.vm"

cm = ConfigManager.instance()

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('WebClient')

class WebClientRequestHandlerMixIn(WebServer.BaseWebRequestHandlerMixIn):
	
	def _getClient(self):
		return self.server.getClient()

	def _getDebug(self):
		return self.server.getDebug()
	
	def handle_docroot(self, path):
		self._sendError(403)
	
	def handle_repository(self, path):
		"""
		Browse a particular folder.
		"""
		if not path:
			path = '/repository'

		path = os.path.normpath(path)
		
		if not path.startswith('/repository'):
			path = '/repository/' + path

		print "DEBUG: repository: %s" % path
		try:
			l = self._getClient().getDirectoryListing(path)
		except Exception, e:
			print "DEBUG: repository: %s" % e
			l = []

		if path > '/repository/':
			l = [ dict(name = '..', type = 'directory') ] + l

		print "DEBUG: repository result: %s" % l

		
		self._serveTemplate("repository.vm", context = dict(path = path, entries = l))
	

	def handle_ats(self, path):
		"""
		Display a page to view latest ATS execution and to execute the ATS.
		
		path is a testerman-document-root path to an ats.
		"""
		
		if not path:
			path = '/repository'
		path = os.path.normpath(path)
		if not path.startswith('/repository'):
			path = '/repository/' + path

		# Fetch available archived execution logs
		logs = []
		archivePath = '/archives/%s' % ('/'.join(path.split('/')[2:]))
		try:
			l = self._getClient().getDirectoryListing(archivePath)
		except Exception, e:
			print "DEBUG: repository: %s" % e
			l = []

		for entry in l:
			if entry['type'] == 'log':
				log = {}
				name = entry['name']
				filename = '%s/%s' % (archivePath, name)
				# According to the name, retrieve some additional info.
				m = re.match(r'([0-9-]+)_(.*)\.log', name)
				if m:
					date = m.group(1)
					username = m.group(2)
					log = dict(name = name, filename = filename, date = date, username = username)
					logs.append(log)
		
		logs.reverse()
		context = dict(path = path, logs = logs)
		
		self._serveTemplate("ats.vm", context = context)

	def handle_view_log(self, path):
		"""
		View the logs
		"""
		if not path:
			path = '/archives'
		path = os.path.normpath(path)
		if not path.startswith('/archives'):
			path = '/archives/' + path

		try:
			log = '<?xml version="1.0" encoding="utf-8" ?>\n'
			log += '<?xml-stylesheet type="text/xsl" href="log-simple.xsl"?>\n'
			log += '<ats>\n'
			log += self._getClient().getFile(path)
			log += '</ats>'
		except Exception, e:
			self._sendError(404)
			return

		self._sendContent(log, contentType = "application/xml")
	
	def handle_download_log(self, path):
		if not path:
			path = '/archives'
		path = os.path.normpath(path)
		if not path.startswith('/archives'):
			path = '/archives/' + path
		
		try:
			log = '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n'
			log += self._getClient().getFile(path)
			log += '</ats>'
		except Exception, e:
			self._sendError(404)
			return
		
		filename = os.path.split(path)[1] + '.xml'
		self._sendContent(log, contentType = "application/xml", asFilename = filename)
		

############################################################
# The HTTP Server
############################################################

class RequestHandler(WebClientRequestHandlerMixIn, BaseHTTPServer.BaseHTTPRequestHandler):
	pass

class HttpServer(BaseHTTPServer.HTTPServer):
	allow_reuse_address = True
	def handle_request_with_timeout(self, timeout):
		"""
		A handle_request reimplementation, with a timeout support
		so that we can interrupt the server easily.
		"""
		r, w, e = select.select([self.socket], [], [], timeout)
		if r:
			self.handle_request()
	def setDocumentRoot(self, docroot):
		self._docroot = docroot
	
	def getDocumentRoot(self):
		return self._docroot
	
	def getClient(self):
		return self._client
	
	def setClient(self, client):
		self._client = client
	
	def setDebug(self, debug):
		self._debug = debug
	
	def getDebug(self):
		return self._debug

class HttpServerThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self._stopEvent = threading.Event()
		address = (cm.get("interface.wc.ip"), cm.get("interface.wc.port"))
		self._server = HttpServer(address, RequestHandler)
		self._server.setDocumentRoot(cm.get("testerman.webclient.document_root"))
		serverUrl = "http://%s:%s" % (cm.get("ts.ip"), cm.get("ts.port"))
		client = TestermanClient.Client(name = "Testerman WebClient", userAgent = "WebClient/%s" % VERSION, serverUrl = serverUrl)
		self._server.setClient(client)
		self._server.setDebug(cm.get("wcs.debug"))

	def run(self):
		getLogger().info("HTTP server started")
		try:
			while not self._stopEvent.isSet(): 
				self._server.handle_request_with_timeout(0.01)
		except Exception, e:
			getLogger().error("Exception in HTTP server thread: " + str(e))
		getLogger().info("HTTP server stopped")

	def stop(self):
		try:
			self._stopEvent.set()
			self.join()
		except Exception, e:
			getLogger().error("Unable to stop HTTP server gracefully: %s" % str(e))

################################################################################
# Testerman WebClient Server: Main
################################################################################

def getVersion():
	ret = "Testerman WebClient Server %s" % VERSION
	return ret

def main():
	server_root = os.path.abspath(os.path.dirname(sys.modules[globals()['__name__']].__file__))
	testerman_home = os.path.abspath("%s/.." % server_root)
	# Set transient values
	cm.set_transient("testerman.testerman_home", testerman_home)
	cm.set_transient("wcs.server_root", server_root)


	# Register persistent variables
	expandPath = lambda x: x and os.path.abspath(os.path.expandvars(os.path.expanduser(x)))
	splitPaths = lambda paths: [ expandPath(x) for x in paths.split(',')]
	cm.register("interface.wc.ip", "0.0.0.0")
	cm.register("interface.wc.port", 8888)
	cm.register("ts.ip", "127.0.0.1")
	cm.register("ts.port", 8080)
	cm.register("wcs.daemonize", False)
	cm.register("wcs.debug", False)
	cm.register("wcs.log_filename", "")
	cm.register("wcs.pid_filename", "")
	cm.register("testerman.var_root", "", xform = expandPath)
	cm.register("testerman.webclient.document_root", "%s/webclient" % testerman_home, xform = expandPath, dynamic = True)
	cm.register("testerman.administrator.name", "administrator", dynamic = True)
	cm.register("testerman.administrator.email", "testerman-admin@localhost", dynamic = True)


	parser = optparse.OptionParser(version = getVersion())

	group = optparse.OptionGroup(parser, "Basic Options")
	group.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug traces on")
	group.add_option("-d", dest = "daemonize", action = "store_true", help = "daemonize")
	group.add_option("-r", dest = "docRoot", metavar = "PATH", help = "use PATH as document root (default: %s)" % cm.get("testerman.document_root"))
	group.add_option("--log-filename", dest = "logFilename", metavar = "FILENAME", help = "write logs to FILENAME instead of stdout")
	group.add_option("--pid-filename", dest = "pidFilename", metavar = "FILENAME", help = "write the process PID to FILENAME when daemonizing (default: no pidfile)")
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "IPs and Ports Options")
	group.add_option("--wc-ip", dest = "wcIp", metavar = "ADDRESS", help = "set listening Wc IP address to ADDRESS (default: listening on all interfaces)")
	group.add_option("--wc-port", dest = "wcPort", metavar = "PORT", help = "set listening Wc port to PORT (default: %s)" % cm.get("interface.wc.port"), type = "int")
	group.add_option("--ts-ip", dest = "tsIp", metavar = "ADDRESS", help = "set TS Ws target IP address to ADDRESS (default: %s)" % cm.get("ts.ip"))
	group.add_option("--ts-port", dest = "tsPort", metavar = "PORT", help = "set TS Ws target port address to PORT (default: %s)" % cm.get("ts.port"), type = "int")
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "Advanced Options")
	group.add_option("-V", dest = "varDir", metavar = "PATH", help = "use PATH to persist Testerman Server runtime variables, such as the job queue. If not provided, no persistence occurs between restarts.")
	group.add_option("-C", "--conf-file", dest = "configurationFile", metavar = "FILENAME", help = "path to a configuration file. You may still use the command line options to override the values it contains.")
	group.add_option("--var", dest = "variables", metavar = "VARS", help = "set additional variables as VARS (format: key=value[,key=value]*)")
	parser.add_option_group(group)

	(options, args) = parser.parse_args()


	# Configuration 
	
	# Read the settings from the saved configuration, if any
	configFile = None
	# Provided on the command line ?
	if options.configurationFile is not None:
		configFile = options.configurationFile
	# No config file provided - fallback to $TESTERMAN_HOME/conf/testerman.conf if set and exists
	elif Tools.fileExists("%s/conf/testerman.conf" % testerman_home):
		configFile = "%s/conf/testerman.conf" % testerman_home
	
	cm.set_transient("wcs.configuration_filename", configFile)

	if configFile:
		try:
			cm.read(configFile)
		except Exception, e:
			print str(e)
			return 1


	# Now, override read settings with those set on explicit command line flags
	# (or their default values inherited from the ConfigManager default values)
	cm.set_user("interface.wc.ip", options.wcIp)
	cm.set_user("interface.wc.port", options.wcPort)
	cm.set_user("ts.ip", options.tsIp)
	cm.set_user("ts.port", options.tsPort)
	cm.set_user("wcs.daemonize", options.daemonize)
	cm.set_user("wcs.debug", options.debug)
	cm.set_user("wcs.log_filename", options.logFilename)
	cm.set_user("wcs.pid_filename", options.pidFilename)
	cm.set_user("testerman.var_root", options.varDir)
	if options.variables:
		for var in options.variables.split(','):
			try:
				(key, val) = var.split('=')
				cm.set_user(key, val)
			except:
				pass

	# Commit all provided values (construct actual values via registered xforms)
	cm.commit()

	# Compute/adjust actual variables where applies

	# If an explicit pid file was provided, use it. Otherwise, fallback to the var_root/ts.pid if possible.
	pidfile = cm.get("wcs.pid_filename")
	if not pidfile and cm.get("testerman.var_root"):
		# Set an actual value
		pidfile = cm.get("testerman.var_root") + "/wcs.pid"
		cm.set_actual("wcs.pid_filename", pidfile)

#	print Tools.formatTable([ ('key', 'Name'), ('format', 'Type'), ('dynamic', 'Dynamic'), ('default', 'Default value'), ('user', 'User value'), ('actual', 'Actual value')], cm.getVariables(), order = "key")

	# Logger initialization
	if cm.get("wcs.debug"):
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', filename = cm.get("ts.log_filename"))

	# Display startup info
	getLogger().info("Starting WebClient Server %s" % (VERSION))
	getLogger().info("WebClient         (Wc) listening on tcp://%s:%s" % (cm.get("interface.wc.ip"), cm.get("interface.wc.port")))
	getLogger().info("Using TS at tcp://%s:%s" % (cm.get("ts.ip"), cm.get("ts.port")))
	items = cm.getKeys()
	items.sort()
	for k in items:
		getLogger().info("Using %s = %s" % (str(k), cm.get(k)))

	# Now we can daemonize if needed
	if cm.get("wcs.daemonize"):
		if pidfile:
			getLogger().info("Daemonizing, using pid file %s..." % pidfile)
		else:
			getLogger().info("Daemonizing...")
		Tools.daemonize(pidFilename = pidfile, displayPid = True)


	# Main start
	cm.set_transient("wcs.pid", os.getpid())
	try:
		serverThread =HttpServerThread() # Ws server
		serverThread.start()
		getLogger().info("Started.")
		while 1:
			time.sleep(1)
	except KeyboardInterrupt:
		getLogger().info("Shutting down WebClient Server...")
	except Exception, e:
		sys.stderr.write("Unable to start server: %s\n" % str(e))
		getLogger().critical("Unable to start server: " + str(e))

	serverThread.stop()
	getLogger().info("Shut down.")
	logging.shutdown()
	Tools.cleanup(cm.get("wcs.pid_filename"))

if __name__ == "__main__":
	main()
