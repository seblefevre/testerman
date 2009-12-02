#!/usr/bin/env python
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
# Testerman Server - main.
#
##

import ConfigManager
import EventManager
import FileSystemManager
import JobManager
import ProbeManager
import Tools
import Versions
import WebServices

import logging
import optparse
import os
import select
import socket
import sys
import threading
import time
# XML-RPC support: locally modified SimpleXMLRPCServer
# to workaround a bug in the one distribued with Python < 2.5
# (allow_none=1 not taken into account to enable marshalling of None values).
# So the SimpleXMLRPCServer.dumps() has been overriden here.
import SimpleXMLRPCServer
import SocketServer

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS')

################################################################################
# XML-RPC: Ws Interface implementation
################################################################################

class XmlRpcServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
#class XmlRpcServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
	allow_reuse_address = True
	def handle_request_with_timeout(self, timeout):
		"""
		A handle_request reimplementation, with a timeout support
		so that we can interrupt the server easily.
		"""
		r, w, e = select.select([self.socket], [], [], timeout)
		if r:
			self.handle_request()

class XmlRpcServerThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self._stopEvent = threading.Event()
		address = (ConfigManager.get("interface.ws.ip"), ConfigManager.get("interface.ws.port"))
		self._server = XmlRpcServer(address, SimpleXMLRPCServer.SimpleXMLRPCRequestHandler)
		# We should be more selective...
		self._server.register_instance(WebServices)
		self._server.logRequests = False

	def run(self):
		getLogger().info("XML-RPC server started")
		try:
			while not self._stopEvent.isSet(): 
				self._server.handle_request_with_timeout(0.01)
		except Exception, e:
			getLogger().error("Exception in XMLRPC server thread: " + str(e))
		getLogger().info("XML-RPC server stopped")

	def stop(self):
		self._stopEvent.set()
		self.join()

################################################################################
# Testerman Server: Main
################################################################################

def getVersion():
	ret = "Testerman Server %s" % Versions.getServerVersion() + "\n" + \
				"API versions:\n Ws: %s\n Xc: %s" % (Versions.getWsVersion(), Versions.getXcVersion())
	return ret

def main():
	localPath = os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__)))

	parser = optparse.OptionParser(version = getVersion())
	group = optparse.OptionGroup(parser, "Basic Options")
	group.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug traces on (default: %default)", default = False)
	group.add_option("-d", dest = "daemonize", action = "store_true", help = "daemonize (default: do not daemonize)", default = False)
	group.add_option("-r", dest = "docRoot", metavar = "PATH", help = "set PATH as document root (default: %default)", default = "/tmp")
	group.add_option("--log-filename", dest = "logFilename", metavar = "FILE", help = "set log filename to FILE (default: none used)", default = None)
	group.add_option("--pid-filename", dest = "pidFilename", metavar = "FILE", help = "use FILE to dump the process PID when daemonizing (default: no pidfile)", default = None)
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "IPs and Ports Options")
	group.add_option("--ws-ip", dest = "wsIp", metavar = "ADDRESS", help = "set listening Ws IP address to ADDRESS (default: %default)", default = "")
	group.add_option("--ws-port", dest = "wsPort", metavar = "PORT", help = "set listening Ws port to PORT (default: %default)", default = 8080, type = "int")
	group.add_option("--xc-ip", dest = "xcIp", metavar = "ADDRESS", help = "set Xc service IP address to ADDRESS (default: Ws IP, or hostname resolution)", default = "")
	group.add_option("--xc-port", dest = "xcPort", metavar = "PORT", help = "set Xc service port to PORT (default: %default)", default = 8081, type = "int")
	group.add_option("--il-ip", dest = "ilIp", metavar = "ADDRESS", help = "set Il IP address to ADDRESS (default: %default)", default = "")
	group.add_option("--il-port", dest = "ilPort", metavar = "PORT", help = "set Il port address to PORT (default: %default)", default = 8082, type = "int")
	group.add_option("--ih-ip", dest = "ihIp", metavar = "ADDRESS", help = "set Ih IP address to ADDRESS (default: %default)", default = "")
	group.add_option("--ih-port", dest = "ihPort", metavar = "PORT", help = "set Ih port address to PORT (default: %default)", default = 8083, type = "int")
	group.add_option("--tacs-ip", dest = "tacsIp", metavar = "ADDRESS", help = "set TACS Ia target IP address to ADDRESS (default: %default)", default = "127.0.0.1")
	group.add_option("--tacs-port", dest = "tacsPort", metavar = "PORT", help = "set TACS Ia target port address to PORT (default: %default)", default = 8087, type = "int")
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "Advanced Options")
	group.add_option("-c", "--conf-dir", dest = "configurationDir", metavar = "PATH", help = "use PATH to save/restore Testerman Server configuration. Also used to persist some runtime variables, such as the job queue.", default = None)
	group.add_option("--probe-path", dest = "probePaths", metavar = "PATHS", help = "search for probe modules in PATHS, which is a comma-separated list of paths (default: %default)", default = os.path.normpath("%s/../plugins/probes" % localPath))
	group.add_option("--codec-path", dest = "codecPaths", metavar = "PATHS", help = "search for codec modules in PATHS, which is a comma-separated list of paths (default: %default)", default = os.path.normpath("%s/../plugins/codecs" % localPath))
	group.add_option("--var", dest = "variables", metavar = "VARS", help = "set additional variables as VARS (format: key=value[,key=value]*)", default = None)
	parser.add_option_group(group)

	(options, args) = parser.parse_args()
	
	# Attempt to read the settings from the saved configuration
#	if not ConfigManager.read(options.configurationDir, "server.conf"):
#		# Set default values	
#		# standard paths within the document root. Actually, they shouldn't even be configurable.
#		ConfigManager.set("constants.repository", "repository")
#		ConfigManager.set("constants.archives", "archives")
#		ConfigManager.set("constants.modules", "modules")
#		ConfigManager.set("constants.components", "components")
#
#		ConfigManager.set("interface.ws.ip", options.wsIp)
#		ConfigManager.set("interface.ws.port", options.wsPort)
#		ConfigManager.set("interface.xc.ip", options.xcIp)
#		ConfigManager.set("interface.xc.port", options.xcPort)
#		ConfigManager.set("interface.il.ip", options.ilIp)
#		ConfigManager.set("interface.il.port", options.ilPort)
#		ConfigManager.set("interface.ih.ip", options.ihIp)
#		ConfigManager.set("interface.ih.port", options.ihPort)
#
#		ConfigManager.set("tacs.ip", options.tacsIp)
#		ConfigManager.set("tacs.port", options.tacsPort)
#
#		ConfigManager.set("ts.daemonize", options.daemonize)
#		ConfigManager.set("ts.debug", options.debug)
#		ConfigManager.set("ts.logfilename", options.logFilename)


	# Override loaded settings if needed
	
	# interfaces settings: listening interfaces
	ConfigManager.set("interface.ws.ip", options.wsIp)
	ConfigManager.set("interface.ws.port", options.wsPort)
	ConfigManager.set("interface.xc.ip", options.xcIp)
	ConfigManager.set("interface.xc.port", options.xcPort)
	if not options.xcIp: # Not provided ? defaults to ws
		ConfigManager.set("interface.xc.ip", options.wsIp)
	ip = ConfigManager.get("interface.xc.ip")
	if not ip or ip == '0.0.0.0': # Not fully qualified ? defaults to the hostname resolution.
		ConfigManager.set("interface.xc.ip", socket.gethostbyname(socket.gethostname()))
	ConfigManager.set("interface.il.ip", options.ilIp)
	ConfigManager.set("interface.il.port", options.ilPort)
	ConfigManager.set("interface.ih.ip", options.ihIp)
	ConfigManager.set("interface.ih.port", options.ihPort)
	# client interfaces
	ConfigManager.set("tacs.ip", options.tacsIp)
	ConfigManager.set("tacs.port", options.tacsPort)

	# standard paths within the document root. Actually, they shouldn't even be configurable.
	ConfigManager.set("constants.repository", "repository")
	ConfigManager.set("constants.archives", "archives")
	ConfigManager.set("constants.modules", "modules")
	ConfigManager.set("constants.components", "components")

	# ts.* : local testerman server variables
	ConfigManager.set("ts.daemonize", options.daemonize)
	ConfigManager.set("ts.debug", options.debug)
	ConfigManager.set("ts.logfilename", options.logFilename)

	# testerman.* global testerman variables (for all server components)
	# Document root, contains repository/archives/components/modules 'standard' paths
	ConfigManager.set("testerman.document_root", os.path.realpath(options.docRoot))
	# tmp root contains runtime temporary files (input/output sessions)
	ConfigManager.set("testerman.tmp_root", "/tmp")
	# main root root: the dir where core/TestermanServer.py is located
	root = os.path.normpath(os.path.realpath("%s/.." % os.path.dirname(sys.modules[globals()['__name__']].__file__)))
	ConfigManager.set("testerman.rootdir", root)
	ConfigManager.set("testerman.server_path", "%s/core" % root)
	# Typically overriden on command line
	if options.configurationDir:
		ConfigManager.set("testerman.configuration_path", options.configurationDir)

	# testerman.te.*: test executable-related variables
	# Interpreter for Python scripts
	ConfigManager.set("testerman.te.python.interpreter", "/usr/bin/python")
	# TTCN3 adaptation lib (enable the easy use of previous versions to keep script compatibility)
	ConfigManager.set("testerman.te.python.ttcn3module", "TestermanTTCN3")
	# the maximum dumpable payload in log (as a single value). Bigger payloads are truncated to this size, in bytes.
	ConfigManager.set("testerman.te.log.maxpayloadsize", 64*1024)

	# set the absolute codec/probe paths as normalized lists of paths
	ConfigManager.set("testerman.te.codec_paths", [ ((x.startswith('/') and x) or os.path.normpath(os.path.realpath('%s/%s' % (os.getcwd(), x)))) for x in options.codecPaths.split(',')])
	ConfigManager.set("testerman.te.probe_paths", [ ((x.startswith('/') and x) or os.path.normpath(os.path.realpath('%s/%s' % (os.getcwd(), x)))) for x in options.probePaths.split(',')])

	if options.variables:
		for var in options.variables.split(','):
			try:
				(key, val) = var.split('=')
				ConfigManager.set(key, val)
			except:
				pass

	# Logger initialization
	if options.debug:
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', filename = options.logFilename)

	# Display startup info
	getLogger().info("Starting Testerman Server %s" % (Versions.getServerVersion()))
	getLogger().info("Web Service       (Ws) listening on tcp://%s:%d" % (ConfigManager.get("interface.ws.ip"), ConfigManager.get("interface.ws.port")))
	getLogger().info("Client events     (Xc) listening on tcp://%s:%d" % (ConfigManager.get("interface.xc.ip"), ConfigManager.get("interface.xc.port")))
	getLogger().info("Log manager       (Il) listening on tcp://%s:%d" % (ConfigManager.get("interface.il.ip"), ConfigManager.get("interface.il.port")))
	getLogger().info("Component manager (Ih) listening on tcp://%s:%d" % (ConfigManager.get("interface.ih.ip"), ConfigManager.get("interface.ih.port")))
	getLogger().info("Using TACS at tcp/%s:%d" % (ConfigManager.get("tacs.ip"), ConfigManager.get("tacs.port")))
	items = ConfigManager.instance().getValues().items()
	items.sort()
	for (k, v) in items:
		getLogger().info("Using %s = %s" % (str(k), str(v)))

	# Now we can daemonize if needed
	if options.daemonize:
		if options.pidFilename:
			getLogger().info("Daemonizing, using pid file %s..." % options.pidFilename)
		else:
			getLogger().info("Daemonizing...")
		Tools.daemonize(pidFilename = options.pidFilename, displayPid = True)

	try:
		FileSystemManager.initialize()
		EventManager.initialize() # Xc server, Ih server [TSE:CH], Il server [TSE:TL]
		ProbeManager.initialize() # Ia client
		JobManager.initialize() # Job scheduler
		serverThread = XmlRpcServerThread() # Ws server
		serverThread.start()
	except Exception, e:
		print "Unable to start server: " + str(e)
		getLogger().critical("Unable to start server: " + str(e))
		# Stop anything we can
		try:
			serverThread.stop()
		except: pass
		try:
			JobManager.finalize()
		except: pass
		try:
			ProbeManager.finalize()
		except: pass
		try:
			EventManager.finalize()
		except: pass
		try:
			FileSystemManager.finalize()
		except: pass
		logging.shutdown()
		return

	getLogger().info("Started.")

	# The main loop
	try:
		while 1:
			time.sleep(1)
	except KeyboardInterrupt:
		getLogger().info("Shutting down Testerman Server...")

	getLogger().info("Stoppping XML-RPC server...")
	serverThread.stop()
	JobManager.finalize()
	ProbeManager.finalize()
	EventManager.finalize()
	getLogger().info("Done.")
	logging.shutdown()

if __name__ == "__main__":
	main()
