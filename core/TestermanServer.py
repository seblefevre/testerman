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

	# Set default values	
	
	# standard paths within the document root. Actually, they shouldn't even be configurable.
	ConfigManager.set("constants.repository", "repository")
	ConfigManager.set("constants.archives", "archives")
	ConfigManager.set("constants.modules", "modules")
	ConfigManager.set("constants.components", "components")
	ConfigManager.set("interface.ws.ip", "0.0.0.0")
	ConfigManager.set("interface.ws.port", 8080)
	ConfigManager.set("interface.xc.ip", "0.0.0.0")
	ConfigManager.set("interface.xc.port", 8081)
	ConfigManager.set("interface.il.ip", "0.0.0.0")
	ConfigManager.set("interface.il.port", 8082)
	ConfigManager.set("interface.ih.ip", "0.0.0.0")
	ConfigManager.set("interface.ih.port", 8083)
	ConfigManager.set("tacs.ip", "127.0.0.1")
	ConfigManager.set("tacs.port", 8087)
	ConfigManager.set("ts.daemonize", False)
	ConfigManager.set("ts.debug", False)
	ConfigManager.set("ts.log_filename", "")
	ConfigManager.set("ts.pid_filename", "")
	ConfigManager.set("testerman.document_root", "/tmp")
	ConfigManager.set("testerman.tmp_root", "/tmp")
	ConfigManager.set("testerman.configuration_path", "")
	# testerman.te.*: test executable-related variables
	ConfigManager.set("testerman.te.codec_paths", os.path.normpath("%s/../plugins/codecs" % localPath))
	ConfigManager.set("testerman.te.probe_paths", os.path.normpath("%s/../plugins/probes" % localPath))
	ConfigManager.set("testerman.te.python.interpreter", "/usr/bin/python")
	ConfigManager.set("testerman.te.python.ttcn3module", "TestermanTTCN3") # TTCN3 adaptation lib (enable the easy use of previous versions to keep script compatibility)
	ConfigManager.set("testerman.te.log.max_payload_size", 64*1024) # the maximum dumpable payload in log (as a single value). Bigger payloads are truncated to this size, in bytes.


	parser = optparse.OptionParser(version = getVersion())

	group = optparse.OptionGroup(parser, "Basic Options")
	group.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug traces on (default: %default)", default = ConfigManager.get("ts.debug"))
	group.add_option("-d", dest = "daemonize", action = "store_true", help = "daemonize (default: do not daemonize)", default = ConfigManager.get("ts.daemonize"))
	group.add_option("-r", dest = "docRoot", metavar = "PATH", help = "set PATH as document root (default: %default)", default = ConfigManager.get("testerman.document_root"))
	group.add_option("--log-filename", dest = "logFilename", metavar = "FILENAME", help = "set log filename to FILENAME (default: none used)", default = ConfigManager.get("ts.logfilename"))
	group.add_option("--pid-filename", dest = "pidFilename", metavar = "FILENAME", help = "use FILENAME to dump the process PID when daemonizing (default: no pidfile)", default = ConfigManager.get("ts.pidfilename"))
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "IPs and Ports Options")
	group.add_option("--ws-ip", dest = "wsIp", metavar = "ADDRESS", help = "set listening Ws IP address to ADDRESS (default: %default)", default = ConfigManager.get("interface.ws.ip"))
	group.add_option("--ws-port", dest = "wsPort", metavar = "PORT", help = "set listening Ws port to PORT (default: %default)", default = ConfigManager.get("interface.ws.port"), type = "int")
	group.add_option("--xc-ip", dest = "xcIp", metavar = "ADDRESS", help = "set Xc service IP address to ADDRESS (default: Ws IP, or hostname resolution)")
	group.add_option("--xc-port", dest = "xcPort", metavar = "PORT", help = "set Xc service port to PORT (default: %default)", default = ConfigManager.get("interface.xc.port"), type = "int")
	group.add_option("--il-ip", dest = "ilIp", metavar = "ADDRESS", help = "set Il IP address to ADDRESS (default: %default)", default = ConfigManager.get("interface.il.ip"))
	group.add_option("--il-port", dest = "ilPort", metavar = "PORT", help = "set Il port address to PORT (default: %default)", default = ConfigManager.get("interface.il.port"), type = "int")
	group.add_option("--ih-ip", dest = "ihIp", metavar = "ADDRESS", help = "set Ih IP address to ADDRESS (default: %default)", default = ConfigManager.get("interface.ih.ip"))
	group.add_option("--ih-port", dest = "ihPort", metavar = "PORT", help = "set Ih port address to PORT (default: %default)", default = ConfigManager.get("interface.ih.port"), type = "int")
	group.add_option("--tacs-ip", dest = "tacsIp", metavar = "ADDRESS", help = "set TACS Ia target IP address to ADDRESS (default: %default)", default = ConfigManager.get("tacs.ip"))
	group.add_option("--tacs-port", dest = "tacsPort", metavar = "PORT", help = "set TACS Ia target port address to PORT (default: %default)", default = ConfigManager.get("tacs.port"), type = "int")
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "Advanced Options")
	group.add_option("-c", "--conf-dir", dest = "configurationDir", metavar = "PATH", help = "use PATH to save/restore Testerman Server configuration. Also used to persist some runtime variables, such as the job queue.", default = ConfigManager.get("testerman.configuration_path"))
	group.add_option("--conf-file", dest = "configurationFile", metavar = "FILENAME", help = "path to a configuration file. You may still use the command line options to override most of the values it contains.", default = None)
	group.add_option("--codec-path", dest = "codecPaths", metavar = "PATHS", help = "search for codec modules in PATHS, which is a comma-separated list of paths (default: %default)", default = ConfigManager.get("testerman.te.codec_paths"))
	group.add_option("--probe-path", dest = "probePaths", metavar = "PATHS", help = "search for probe modules in PATHS, which is a comma-separated list of paths (default: %default)", default = ConfigManager.get("testerman.te.probe_paths"))
	group.add_option("--var", dest = "variables", metavar = "VARS", help = "set additional variables as VARS (format: key=value[,key=value]*)", default = None)
	parser.add_option_group(group)

	(options, args) = parser.parse_args()


	# Configuration 
		
	# Read the settings from the saved configuration, if any
	if options.configurationFile:
		try:
			ConfigManager.instance().read(options.configurationFile)
		except Exception, e:
			print str(e)
			return 1
			

	# Now, override read settings with those set on explicit command line flags (or their default values inherited from the ConfigManager default values)
	ConfigManager.set("interface.ws.ip", options.wsIp)
	ConfigManager.set("interface.ws.port", options.wsPort)
	ConfigManager.set("interface.xc.ip", options.xcIp)
	ConfigManager.set("interface.xc.port", options.xcPort)
	if not options.xcIp: ConfigManager.set("interface.xc.ip", options.wsIp) # Not provided ? defaults to ws
	ip = ConfigManager.get("interface.xc.ip")
	if not ip or ip == '0.0.0.0': ConfigManager.set("interface.xc.ip", socket.gethostbyname(socket.gethostname())) # Not fully qualified ? defaults to the hostname resolution.
	ConfigManager.set("interface.il.ip", options.ilIp)
	ConfigManager.set("interface.il.port", options.ilPort)
	ConfigManager.set("interface.ih.ip", options.ihIp)
	ConfigManager.set("interface.ih.port", options.ihPort)
	# client interfaces
	ConfigManager.set("tacs.ip", options.tacsIp)
	ConfigManager.set("tacs.port", options.tacsPort)
	# ts.* : local testerman server variables
	ConfigManager.set("ts.daemonize", options.daemonize)
	ConfigManager.set("ts.debug", options.debug)
	ConfigManager.set("ts.log_filename", options.logFilename)
	ConfigManager.set("ts.pid_filename", options.pidFilename)
	# testerman.* global testerman variables (for all server components)
	# Document root, contains repository/archives/components/modules 'standard' paths
	ConfigManager.set("testerman.document_root", os.path.realpath(options.docRoot))
	# main root root: the dir where core/TestermanServer.py is located
	root = os.path.normpath(os.path.realpath("%s/.." % os.path.dirname(sys.modules[globals()['__name__']].__file__)))
	ConfigManager.set("testerman.rootdir", root)
	ConfigManager.set("testerman.server_path", "%s/core" % root)
	ConfigManager.set("testerman.configuration_path", options.configurationDir)
	# set the absolute codec/probe paths as normalized lists of paths
	ConfigManager.set("testerman.te.codec_paths", [ ((x.startswith('/') and x) or os.path.normpath(os.path.realpath('%s/%s' % (os.getcwd(), x)))) for x in options.codecPaths.split(',')])
	ConfigManager.set("testerman.te.probe_paths", [ ((x.startswith('/') and x) or os.path.normpath(os.path.realpath('%s/%s' % (os.getcwd(), x)))) for x in options.probePaths.split(',')])

	# set user-defined variables
	if options.variables:
		for var in options.variables.split(','):
			try:
				(key, val) = var.split('=')
				ConfigManager.set(key, val)
			except:
				pass

	# Logger initialization
	if ConfigManager.get_bool("ts.debug"):
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', filename = ConfigManager.get_bool("ts.log_filename"))

	# Display startup info
	getLogger().info("Starting Testerman Server %s" % (Versions.getServerVersion()))
	getLogger().info("Web Service       (Ws) listening on tcp://%s:%s" % (ConfigManager.get("interface.ws.ip"), ConfigManager.get("interface.ws.port")))
	getLogger().info("Client events     (Xc) listening on tcp://%s:%s" % (ConfigManager.get("interface.xc.ip"), ConfigManager.get("interface.xc.port")))
	getLogger().info("Log manager       (Il) listening on tcp://%s:%s" % (ConfigManager.get("interface.il.ip"), ConfigManager.get("interface.il.port")))
	getLogger().info("Component manager (Ih) listening on tcp://%s:%s" % (ConfigManager.get("interface.ih.ip"), ConfigManager.get("interface.ih.port")))
	getLogger().info("Using TACS at tcp://%s:%s" % (ConfigManager.get("tacs.ip"), ConfigManager.get("tacs.port")))
	items = ConfigManager.instance().getValues().items()
	items.sort()
	for (k, v) in items:
		getLogger().info("Using %s = %s" % (str(k), str(v)))

	# Now we can daemonize if needed
	pidfile = ConfigManager.get("ts.pid_filename")
	if ConfigManager.get_bool("ts.daemonize"):
		if pidfile:
			getLogger().info("Daemonizing, using pid file %s..." % pidfile)
		else:
			getLogger().info("Daemonizing...")
		Tools.daemonize(pidFilename = pidfile, displayPid = True)

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
		# Stop everything we can
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
		Tools.cleanup(ConfigManager.get("ts.pid_filename"))
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
	Tools.cleanup(pidfile)

if __name__ == "__main__":
	main()
