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



def main():
	# Make sure that the current directory is in PYTHON path (for probe/plugins)
	sys.path.append(os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__))))

	parser = optparse.OptionParser(version = "Testerman PyAgent %s" % Agent.getVersion())
	parser.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug mode on (default: %default)", default = False)
	parser.add_option("--name", dest = "name", metavar = "NAME", help = "set agent name to NAME (default: automatically generated)", default = None)
	parser.add_option("-c", "--controller", dest = "controllerIp", metavar = "ADDRESS", help = "set agent controller Xa IP address to ADDRESS (default: %default)", default = "127.0.0.1")
	parser.add_option("-p", "--port", dest = "controllerPort", metavar = "PORT", help = "set agent controller Xa port address to PORT (default: %default)", default = 40000, type="int")
	parser.add_option("--deploy", dest = "probes", metavar = "PROBES", help = "automatically deploy PROBES on startup, format: name=type[,name=type]* (default: none)", default = "")
	parser.add_option("--local", dest = "localIp", metavar = "ADDRESS", help = "set local IP address to ADDRESS for XA connection (default: system-dependent)", default = "")
	parser.add_option("--probe-path", dest = "probePaths", metavar = "PATHS", help = "search for probe modules in PATHS, which is a comma-separated list of paths (default: %default)", default = "probes")
	parser.add_option("--codec-path", dest = "codecPaths", metavar = "PATHS", help = "search for codec modules in PATHS, which is a comma-separated list of paths (default: %default)", default = "../codecs")

	(options, args) = parser.parse_args()

	if options.debug:
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S')
	
	# Static initialization
	Agent.initialize(probePaths = options.probePaths.split(','), codecPaths = options.codecPaths.split(','))

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
