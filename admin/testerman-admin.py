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
#
# Can work in 2 disctinct modes:
# - managing a full testerman environment (by providing a testerman home dir):
#   in this mode, it is possible to start, stop, and configure
#   a server and a tacs.
#   The TESTERMAN_SERVER, TESTERMAN_DOCROOT are guessed from this HOME.
#
# - managing a testerman server only (by providing a server URL):
#   in this mode, this is not possible to control the server (start/stop) 
#   or to reconfigure it persistently.
#   Only runtime actions are allowed.
#   The TESTERMAN_DOCROOT is guessed by interrogating the TESTERMAN_SERVER.
#

# A cisco-like command-line shell with support for completion
# and parsing to value trees from syntax trees.
import StructuredInteractiveShell as SIS

import ConfigManager
import TestermanClient

# Administration modules
import contexts


import sys
import optparse
import os
import os.path
import subprocess

VERSION = "0.99.0"


class RootContext(SIS.CommandContext):
	def __init__(self):
		SIS.CommandContext.__init__(self)
		self._client = None

		self.addContext("component", "components management", contexts.ComponentContext())
		self.addContext("agent", "agents and probes management", contexts.AgentContext())
		self.addContext("job", "job management", contexts.JobContext())

		# Show
		orderChoice = SIS.EnumNode()
		orderChoice.addChoice("key", "order by key name")
		orderChoice.addChoice("format", "order by variable type")
		displayChoice = SIS.EnumNode()
		displayChoice.addChoice("no-default", "only display user and actual values")
		displayChoice.addChoice("all", "display default, user, and actual values")
		displayChoice.addChoice("details", "only display user and actual values with type info")
		showRunningConfigurationNode = SIS.SequenceNode()
		showRunningConfigurationNode.addField("order", "sort output by (default: key name)", orderChoice, optional = True)
		showRunningConfigurationNode.addField("display", "display mode (default: no-default)", displayChoice, optional = True)

		showTsNode = SIS.ChoiceNode()
		showTsNode.addChoice("running-configuration", "show running configuration", showRunningConfigurationNode)
		showTsNode.addChoice("internal-variables", "show internal variables")
		showTsNode.addChoice("status", "show testerman server status")
		
		showTacsNode = SIS.ChoiceNode()
		showTacsNode.addChoice("running-configuration", "show running configuration", showRunningConfigurationNode)
		showTacsNode.addChoice("internal-variables", "show internal variables")
		showTacsNode.addChoice("status", "show testerman agent controller server status")
		
		showNode = SIS.ChoiceNode()
		showNode.addChoice("server", "show testerman server related info", showTsNode)
		showNode.addChoice("tacs", "show agent controller server related info", showTacsNode)
		if self.hasHome(): showNode.addChoice("saved-configuration", "show the currently saved testerman configuration")
		showNode.addChoice("target", "show the currently managed testerman target")
		self.addCommand("show", "show various info", showNode, self.show)
		
		# start/stop/restart
		if self.hasHome():
			serverComponents = SIS.EnumNode()
			serverComponents.addChoice("ts", "testerman server")
			serverComponents.addChoice("tacs", "testerman agent controller server")
			serverComponents.addChoice("all", "both testerman server and agent controller server")
			self.addCommand("start", "start a server component, using the saved configuration", serverComponents, self.start)
			self.addCommand("stop", "stop a server component", serverComponents, self.stop)
			self.addCommand("restart", "restart a server component, using the saved configuration", serverComponents, self.restart)

	def hasHome(self):
		return os.environ.get('TESTERMAN_HOME')

	def _getClient(self):
		if not self._client:
			serverUrl = os.environ.get('TESTERMAN_SERVER')
			if not serverUrl:
				raise Exception("Sorry, no testerman server set (TESTERMAN_SERVER).")
			self._client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)

		return self._client

	def show(self, choice):
		name, value = choice
		if name == "saved-configuration":
			return self.showSavedConfiguration()
		elif name == "server":
			return self.showTs(value)
		elif name == "tacs":
			return self.showTacs(value)
		elif name == "target":
			return self.showTarget()
	
	def showTarget(self):
		self.notify("This Testerman admin session manages the following Testerman target:")
		if self.hasHome():
			self.notify(" Testerman installation located at: %s" % os.environ.get("TESTERMAN_HOME"))
			self.notify(" Configured to run a server at:     %s" % os.environ.get("TESTERMAN_SERVER"))
			self.notify(" Using document root:               %s" % os.environ.get("TESTERMAN_DOCROOT"))
		else:
			self.notify(" Testerman server running at:   %s" % os.environ.get("TESTERMAN_SERVER"))
			self.notify(" Currently using document root: %s" % os.environ.get("TESTERMAN_DOCROOT"))

	def showSavedConfiguration(self):
		home = os.environ.get("TESTERMAN_HOME")
		if not home:
			raise Exception("No Testerman installation found. Please check TESTERMAN_HOME.")

		cm = ConfigManager.ConfigManager()
		try:
			cm.read("%s/conf/testerman.conf" % home)
		except Exception, e:
			raise Exception("Unable to read saved configuration file: " + str(e))

		headers = [ ("key", "Variable Name"), ("value", "Value") ]
		values = []
		for k, v in cm.getValues().items():
			values.append(dict(key = k, value = v))
		values.sort()			
		
		self.printTable(headers, values)

	def showTs(self, value):
		name, value = value
		if name == 'running-configuration':
			return self.showRunningConfiguration(component = "ts", **value)
		elif name == 'internal-variables':
			return self.showInternalVariables(component = "ts")
		elif name == 'status':
			return self.tsStatus()

	def showTacs(self, value):
		name, value = value
		if name == 'running-configuration':
			return self.showRunningConfiguration(component = "tacs", **value)
		elif name == 'internal-variables':
			return self.showInternalVariables(component = "tacs")
		elif name == 'status':
			return self.tacsStatus()

	def showRunningConfiguration(self, component, order = "key", display = "no-default"):
		"""
		Displays persistent variables for a given component.
		"""
		if display == 'no-default':
			headers = [
				('key', 'Variable name'),
				('user', 'User-provided value'), ('actual', 'Actual value')
			]
		elif display == 'details':
			headers = [
				('key', 'Variable name'), ('format', 'Type'), 
				('dynamic', 'Dynamic'),
				('user', 'User-provided value'), ('actual', 'Actual value')
			]
		else: # all
			headers = [
				('key', 'Variable name'), ('format', 'Type'), 
				('dynamic', 'Dynamic'), ('default', 'Default value'), 
				('user', 'User-provided value'), ('actual', 'Actual value')
			]

		variables = self._getClient().getVariables(component)
		if variables:
			self.printTable(headers, variables["persistent"], order = order)

	def showInternalVariables(self, component, order = "key"):
		"""
		Displays internal (i.e. transient) variables for a given component.
		"""
		headers = [
			('key', 'Variable name'), ('value', 'Current value')
		]
		
		variables = self._getClient().getVariables(component)
		if variables:
			self.printTable(headers, variables["transient"], order = order)

	def start(self, component = "all"):
		if component == "all":
			components = [ "ts", "tacs" ]
		else:	
				components = [ component ]
				
		for c in components:		
			if c == "ts":
				if self.tsStart():
					return 1
			elif c == "tacs":
				if self.tacsStart():
					return 1
		return 0
		
	def tsStart(self):
		srcroot = os.environ.get("TESTERMAN_HOME")

		# Override doc root or use the one from the conf file ?
		# If we override it, we should also override the Ws ip:port to match TESTERMAN_SERVER...
		docroot = os.environ.get("TESTERMAN_DOCROOT")

		# First, check the status
		if self.tsProbe() >= 0:
			self.error("A Testerman server is already running at %s. Please stop it first." % os.environ.get("TESTERMAN_SERVER"))
			return 1
		
		self.notify("Starting Testerman server...")
		p = subprocess.Popen(["%s/core/TestermanServer.py" % srcroot, "-d", "-r", docroot], 
			env={"PYTHONPATH": "%s/common" % srcroot},
			stdout=None, 
			stderr=None)
		p.wait()
		if p.returncode == 0:
			self.notify("Testerman server started correctly.")
		return p.returncode
		
	def tacsStart(self):
		srcroot = os.environ.get("TESTERMAN_HOME")
		docroot = os.environ.get("TESTERMAN_DOCROOT")
		# First, check status (TODO)
		self.notify("Starting Testerman Agent Controller server...")
		p = subprocess.Popen(["%s/core/TestermanAgentControllerServer.py" % srcroot, "-d", "-r", docroot], 
			env={"PYTHONPATH": "%s/common" % srcroot},
			stdout=None, 
			stderr=None)
		p.wait()
		if p.returncode == 0:
			self.notify("Testerman Agent Controller server started correctly.")
		return p.returncode
		
	def stop(self, component = "all"):
		self.error("Not yet implemented.")

	def restart(self, component = "all"):
		self.error("Not yet implemented.")

	def tsStatus(self):
		"""
		Probes the Testerman server at $TESTERMAN_SERVER.
		Notice that it may be different than the URL configured in the
		saved configuration ($TESTERMAN_HOME/conf/testerman.conf)
		"""
		pid = self.tsProbe()
		if pid > 0:
			self.notify("Testerman server up and running at %s, pid %s" % (os.environ.get("TESTERMAN_SERVER"), pid))
			return 0
		else:
			self.notify("No Testerman server started at %s" % os.environ.get("TESTERMAN_SERVER"))
			return 1
	
	def tsProbe(self):
		"""
		Sends a probe to the server at $TESTERMAN_SERVER.
		Returns the pid (> 0) if OK.
		"""
		try:
			client = self._getClient()
			variables = client.getVariables("ts")["transient"]
			for val in variables:
				if val['key'] == "ts.pid":
					return val['value']
			return -1
		except Exception:
#			print SIS.getBacktrace()
			return -1

	def tacsStatus(self):
		self.error("Not yet implemented.")

def getVersion():
	return "Testerman Administration Console %s" % VERSION


def main():
	expandPath = lambda x: x and os.path.abspath(os.path.expandvars(os.path.expanduser(x)))

	# Command Line Options parsin
	parser = optparse.OptionParser(version = getVersion())
		
	group = optparse.OptionGroup(parser, "Basic Options")
	group.add_option("-t", "--target", dest = "target", metavar = "TARGET", help = "target to administrate. Either a path to a Testerman runtime directory (\"Testerman home\") or the URL of a Testerman server. When administrating a specific Testerman server by URL, some control functions (such as start/stop and configuration) may be disabled.", default = None)
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "Inline Command Execution Options")
	group.add_option("-c", "--context", dest = "context", metavar = "CONTEXT", help = "set the initial working context to CONTEXT (for instance, testerman/component). Also useful when used with --execute.", default = None)
	group.add_option("-e", "--execute", dest = "command", metavar = "COMMAND", help = "do not run an interactive shell. Instead, execute the command line provided here from the initial working context.", default = None)
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "Advanced Options")
	group.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug traces on (default: %default)", default = False)
	parser.add_option_group(group)

	(options, args) = parser.parse_args()


	if not options.target:
		print """Missing mandatory target. Please use -t <testerman_home> or -t <server_url>,
for instance:
  testerman-admin -t http://server:8080
  testerman-admin -t /path/to/testerman/installation"""
		sys.exit(1)


	# Now, compute values from the target.
	if options.target.startswith("http://"):
		serverUrl = options.target
		os.environ["TESTERMAN_SERVER"] = serverUrl
		# Now retrieve the docroot from the running server
		client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)
		try:
			for variable in client.getVariables("ts")['persistent']:
				if variable['key'] == 'testerman.document_root':
					docroot = variable['actual']
					print "Found running Testerman server, using document root: %s" % docroot
					os.environ["TESTERMAN_DOCROOT"] = docroot
					break
		except:
			print "Sorry, cannot find a running Testerman server at %s." % serverUrl
			sys.exit(1)
	
	else:
		# a Testerman home dir was provided.
		# Get all other values from the configuration file.
		home = expandPath(options.target)
		os.environ["TESTERMAN_HOME"] = home
		cm = ConfigManager.ConfigManager()
		try:
			cm.read("%s/conf/testerman.conf" % home)
			os.environ["TESTERMAN_DOCROOT"] = expandPath(cm.get("testerman.document_root"))
			ip = cm.get("interface.ws.ip")
			if not ip or ip == "0.0.0.0":
				ip = "localhost"
			os.environ["TESTERMAN_SERVER"] = "http://%s:%s" % (ip, cm.get("interface.ws.port"))
		except Exception, e:
			print "Invalid Testerman target - cannot find or read %s/conf/testerman.conf file." % home
			sys.exit(1)
		

	# Shell creation
	adminShell = SIS.CmdContextManagerAdapter("Welcome to Testerman Administration Console")
	adminShell.setDebug(options.debug)
	# Root context registration
	adminShell.registerRootContext("testerman", "testerman administration", RootContext())

	if options.context:
		adminShell.goTo(options.context)

	# Non-interactive mode
	if options.command:
		try:
			ret = adminShell.execute(options.command.split(' ')) # rough tokenization
		except Exception, e:
			print str(e)
			ret = -1

		sys.exit(ret)

	# Interactive mode
	else:
		try:
			adminShell.run()
		except SIS.ShellExit:
			print
			sys.exit(0)
		except KeyboardInterrupt:
			print
			sys.exit(0)
	

if __name__ == "__main__":
	main()
	
