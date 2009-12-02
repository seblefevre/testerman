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
# Testerman PyAgent launcher.
#
##

import PyTestermanAgent as Agent

import optparse
import sys
import os
import time
import logging

def daemonize(pidFilename = None, stdout = None, stderr = None, displayPid = False):
	"""
	Daemonize.
	If pidFilename is provided, used to cat the daemon PID.
	stdout and stderr are file descriptors.
	
	@type  pidFilename: string, or None
	@param pidFilename: if provided, the filename to cat the pid to.
	@type  stdout: fd, or None
	@param stdout: if provided, the FD to redirect stdout to
	@type  stderr: fd, or None
	@param stderr: if provided, the FD to redirect stderr to
	
	@rtype: None
	@returns: None
	"""
	import resource
	try:
		# First fork
		pid = os.fork()
		if pid:
			# Exit the parent
			os._exit(0)
		
		# Create a new session
		os.setsid()
		
		# Second fork
		pid = os.fork()
		if pid:
			# Exit the original child
			os._exit(0)
		
		# Display some info before closing all std fds
		if displayPid:
			print "Agent started as daemon (pid %d)" % os.getpid()
			print "Use kill -SIGINT %d to stop the agent when needed." % os.getpid()

		# UMask
		os.umask(0)
		# Workding dir
		os.chdir("/")
	
		# We cat our pid to pidfile
		# (before chaging dir so that relative pidfilenames are possible)
		if pidFilename:
			try:
				f = open(pidFilename, 'w')
				f.write(str(os.getpid()))
				f.close()
			except:
				pass

		# Close file descriptors
		maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
		if maxfd == resource.RLIM_INFINITY:
			maxfd = 65536
		for fd in range(0, maxfd):
			# Only close TTYs, not files, etc
			try:
				os.ttyname(fd)
			except Exception, e:
				continue
			try:
				os.close(fd)
			except Exception, e:
				pass
		
		# Finally we redirect std fds
		if hasattr(os, "devnull"):
			devnull = os.devnull
		else:
			devnull = "/dev/null"
		n = os.open(devnull, os.O_RDWR)
		if stdout is not None: os.dup2(stdout, 1)
		else: os.dup2(n, 1)
		if stderr is not None: os.dup2(stderr, 2)
		else: os.dup2(n, 2)
		return os.getpid()

	except Exception, e:
		# What should we do ?...
		raise e


def main():
	Agent.Restarter.initialize()
	# Make sure that the current directory is in PYTHON path (for probe/plugins)
	localPath = os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__)))
	sys.path.append(localPath)

	parser = optparse.OptionParser(version = "Testerman PyAgent %s" % Agent.getVersion())
	parser.add_option("-c", "--controller", dest = "controllerIp", metavar = "ADDRESS", help = "set agent controller Xa IP address to ADDRESS (default: %default)", default = "127.0.0.1")
	if not sys.platform in [ 'win32', 'win64']:
		parser.add_option("-d", dest = "daemonize", action = "store_true", help = "daemonize (default: do not daemonize)", default = False)
	parser.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug mode on (default: %default)", default = False)
	parser.add_option("--deploy", dest = "probes", metavar = "PROBES", help = "automatically deploy PROBES on startup, format: name=type[,name=type]* (default: none)", default = "")
	parser.add_option("--local", dest = "localIp", metavar = "ADDRESS", help = "set local IP address to ADDRESS for XA connection (default: system-dependent)", default = "")
	parser.add_option("--log-filename", dest = "logFilename", metavar = "FILE", help = "set log filename to FILE (default: none used)", default = None)
	parser.add_option("--name", dest = "name", metavar = "NAME", help = "set agent name to NAME (default: automatically generated)", default = None)
	parser.add_option("-p", "--port", dest = "controllerPort", metavar = "PORT", help = "set agent controller Xa port address to PORT (default: %default)", default = 40000, type="int")
	if not sys.platform in [ 'win32', 'win64']:
		parser.add_option("--pid-filename", dest = "pidFilename", metavar = "FILE", help = "use FILE to dump the process PID when daemonizing (default: no pidfile)", default = None)
	parser.add_option("--probe-path", dest = "probePaths", metavar = "PATHS", help = "search for probe modules in PATHS, which is a comma-separated list of paths (default: %default)", default = os.path.normpath("%s/../plugins/probes" % localPath))
	parser.add_option("--codec-path", dest = "codecPaths", metavar = "PATHS", help = "search for codec modules in PATHS, which is a comma-separated list of paths (default: %default)", default = os.path.normpath("%s/../plugins/codecs" % localPath))

	(options, args) = parser.parse_args()

	if options.debug:
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', filename = options.logFilename)
	
	# Static initialization
	Agent.initialize(probePaths = options.probePaths.split(','), codecPaths = options.codecPaths.split(','))

	# Now we can daemonize if needed (and if supported)
	if not sys.platform in [ 'win32', 'win64']:
		if options.daemonize:
			if options.pidFilename:
				logging.getLogger('pyagent').info("Daemonizing, using pid file %s..." % options.pidFilename)
			else:
				logging.getLogger('pyagent').info("Daemonizing...")
			daemonize(pidFilename = options.pidFilename, displayPid = True)

	agent = Agent.Agent(name = options.name)
	agent.initialize(controllerAddress = (options.controllerIp, options.controllerPort), localAddress = (options.localIp, 0))
	agent.info("Starting agent...")
	agent.start()
	agent.info("Deploying initial probes...")
	# Let's deploy the probes provided on the CLI
	
	if options.probes:
		probes = options.probes.split(',')
		for p in probes:
			(name, type_) = p.split('=')
			# Actually this should be a probe deployment preparation.
			# The actual deployment should include the registration, and the registration is only possible if the agent is connected.
			try:
				agent.deployProbe(type_, name)
			except Exception, e:
				agent.warning("Unable to autodeploy %s as %s: %s" % (name, type_, str(e)))
	
	agent.info("Ready")

	try:
		while 1:
			time.sleep(0.1)
	except KeyboardInterrupt:	
		agent.info("Stopping agent on user interruption...")
		agent.stop()
	
	# When the agent stops() (Keyboard interrupt, etc)
	agent.finalize()
	agent.info("Done.")

if __name__ == "__main__":
	main()
