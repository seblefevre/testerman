#!/usr/bin/env python
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
# Testerman server-side administration console.
#
# A centralized interactive shell for common administration tasks.
#
##

# A cisco-like command-line shell with support for completion
# and parsing to value trees from syntax trees.
import CiscoInteractiveShell

# Administration modules
import contexts


import sys
import optparse
import os
import os.path


VERSION = "0.0.5"


def getVersion():
	return "Testerman Administration Console %s" % VERSION


def main():

	parser = optparse.OptionParser(version = getVersion())
	parser.add_option("-r", dest = "docRoot", metavar = "PATH", help = "set document root to PATH (default: %default). Alternatively, you may set the TESTERMAN_DOCROOT environment variable.", default = os.environ.get("TESTERMAN_DOCROOT", '.'))
	parser.add_option("-S", dest = "sourceRoot", metavar = "PATH", help = "set Testerman source root to PATH. Useful to publish experimental components from source.", default = None)
	parser.add_option("-s", "--server", dest = "serverUrl", metavar = "URL", help = "use URL as Testerman server URL (default: %default). Alternatively, you may set the TESTERMAN_SERVER environment variable. ", default = os.environ.get("TESTERMAN_SERVER", "http://localhost:8080"))
	parser.add_option("-c", "--context", dest = "context", metavar = "CONTEXT", help = "set the initial working context to CONTEXT. Also useful when used with --execute.", default = None)
	parser.add_option("-e", "--execute", dest = "command", metavar = "COMMAND", help = "do not run an interactive shell. Instead, execute the command line provided here from the initial working context.", default = None)
	parser.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug traces on (default: %default)", default = False)

	(options, args) = parser.parse_args()

	if options.docRoot: os.environ["TESTERMAN_DOCROOT"] = os.path.realpath(options.docRoot)
	if options.sourceRoot: os.environ["TESTERMAN_SRCROOT"] = os.path.realpath(options.sourceRoot)
	if options.serverUrl: os.environ["TESTERMAN_SERVER"] = options.serverUrl

	# Shell creation
	adminShell = CiscoInteractiveShell.CmdContextManagerAdapter("Welcome to Testerman Administration Console")
	adminShell.setDebug(options.debug)
	
	# Root context
	rootContext = adminShell.createRootContext("testerman", "testerman administration")
	rootContext.addContext("component", "components management", contexts.ComponentContext())
	rootContext.addContext("agent", "agents and probes management", contexts.AgentContext())

	if options.context:
		adminShell.goTo(options.context)

	# Non-interactive mode
	if options.command:
		ok = True
		try:
			adminShell.execute(options.command.split(' ')) # rough tokenization
		except Exception, e:
			print str(e)
			ok = False

		sys.exit(ok and 0 or 1)

	# Interactive mode
	else:
		try:
			adminShell.run()
		except CiscoInteractiveShell.ShellExit:
			print
			sys.exit(0)
		except KeyboardInterrupt:
			print
			sys.exit(0)
	

if __name__ == "__main__":
	main()
	
