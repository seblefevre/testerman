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
import shutil
import glob
import subprocess
import StringIO
import signal
import time

VERSION = "0.99.0"


import TestermanNodes
import TestermanMessages
class IaClient(TestermanNodes.ConnectingNode):
	"""
	A lightweight Ia Client to monitor the TACS.
	Normal TACS commands are routed through the Testerman Server
	directly (via a usual Ws Testerman Cient)
	"""
	def __init__(self, serverAddress):
		TestermanNodes.ConnectingNode.__init__(self, "testerman-admin", "IaClient")
		self.initialize(serverAddress)
		
	def getVariables(self, timeout = 1.0):
		self.start()
		request = TestermanMessages.Request("GET-VARIABLES", "system:tacs", "Ia", "1.0")
		response = self.executeRequest(0, request, responseTimeout = timeout)
		self.stop()
		if response and response.getStatusCode() == 200:
			return response.getApplicationBody()
		else:
			return None


def makedir(path):
	if not os.path.exists(path):
		os.makedirs(path, mode = 0755)

class RootContext(SIS.CommandContext):
	def __init__(self):
		SIS.CommandContext.__init__(self)
		self._client = None

		self.addContext("components", "components management", contexts.ComponentContext())
		self.addContext("agents", "agents and probes management", contexts.AgentContext())
		self.addContext("jobs", "job management", contexts.JobContext())

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

		# Quick status
		self.addCommand("status", "testerman process status", SIS.NullNode(), self.status)
		
		# start/stop/restart
		if self.hasHome():
			serverComponents = SIS.EnumNode()
			serverComponents.addChoice("server", "testerman server")
			serverComponents.addChoice("tacs", "testerman agent controller server")
			serverComponents.addChoice("all", "both testerman server and agent controller server")
			self.addCommand("start", "start a server component, using the saved configuration", serverComponents, self.start)
			self.addCommand("stop", "stop a server component", serverComponents, self.stop)
			self.addCommand("restart", "restart a server component, using the saved configuration", serverComponents, self.restart)

		# setup
		if self.hasHome():
			setupNode = SIS.ChoiceNode()
			setupNode.addChoice("document-root", "initialize a defaut document root, installing samples")
			self.addCommand("setup", "set up a Testerman environment", setupNode, self.setup)

	def hasHome(self):
		return os.environ.get('TESTERMAN_HOME')

	def _getClient(self):
		if not self._client:
			serverUrl = os.environ.get('TESTERMAN_SERVER')
			if not serverUrl:
				raise Exception("Sorry, no testerman server set (TESTERMAN_SERVER).")
			self._client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)

		return self._client

	def setup(self, choice):
		name, value = choice
		if name == "document-root":
			return self.setupDocroot()
		
	def setupDocroot(self):
		"""
		Sets up / reinitializes the document root.
		This creates the default directories in it (and the docroot itself if needed)
		and copy the samples from the home dir.
		"""
		docroot = os.environ.get("TESTERMAN_DOCROOT")
		self.notify("Setting up document root %s..." % docroot)
		self.notify("Creating default directories...")
		try:
			makedir(docroot)
			makedir("%s/repository" % docroot)
			makedir("%s/updates" % docroot)
			makedir("%s/archives" % docroot)
			makedir("%s/repository/samples" % docroot)
		except Exception, e:
			self.error("An error occured while creating directories: " + str(e))
			return 1
		self.notify("Copying samples...")
		try:
			srcroot = os.environ.get("TESTERMAN_HOME")
			for f in glob.glob("%s/samples/*.ats" % srcroot):
				shutil.copy(f, "%s/repository/samples" % docroot)
			for f in glob.glob("%s/samples/*.campaign" % srcroot):
				shutil.copy(f, "%s/repository/samples" % docroot)
		except Exception, e:
			self.error("An error occured while copying samples: " + str(e))
			return 1
		self.notify("Done")
		return 0

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
			self.notify(" Using TACS at:                     %s" % os.environ.get("TESTERMAN_TACS"))
		else:
			self.notify(" Testerman server running at:   %s" % os.environ.get("TESTERMAN_SERVER"))
			self.notify(" Currently using document root: %s" % os.environ.get("TESTERMAN_DOCROOT"))
			self.notify(" Currently using TACS at:       %s" % os.environ.get("TESTERMAN_TACS"))

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
		if component == "server":
			return self.tsStart()
		elif component == "tacs":
			return self.tacsStart()
		elif component == "all":
			ret = self.tsStart()
			if not ret:
				return self.tacsStart()
			else:
				return ret
		else:
			return -1

	def tsStart(self):
		srcroot = os.environ.get("TESTERMAN_HOME")

		# Override doc root or use the one from the conf file ?
		# If we override it, we should also override the Ws ip:port to match TESTERMAN_SERVER...
		docroot = os.environ.get("TESTERMAN_DOCROOT")

		# First, check the status
		if self.tsProbe() >= 0:
			self.error("A Testerman server is already running at %s. Please stop it first." % os.environ.get("TESTERMAN_SERVER"))
			return -1
		
		self.notify("Starting Testerman server...")
		p = subprocess.Popen(["%s/core/TestermanServer.py" % srcroot, "-d", "-r", docroot], 
			env={"PYTHONPATH": "%s/common" % srcroot},
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE)
		p.wait()
		if p.returncode == 0:
			self.notify("Testerman server started correctly.")
		else:
			self.error("Unable to start Testerman server.")
		return p.returncode
		
	def tacsStart(self):
		srcroot = os.environ.get("TESTERMAN_HOME")
		docroot = os.environ.get("TESTERMAN_DOCROOT")

		# First, check the status
		if self.tacsProbe() >= 0:
			self.error("A Testerman Agent Controller server is already running at %s. Please stop it first." % os.environ.get("TESTERMAN_TACS"))
			return -1

		self.notify("Starting Testerman Agent Controller server...")
		p = subprocess.Popen(["%s/core/TestermanAgentControllerServer.py" % srcroot, "-d", "-r", docroot], 
			env={"PYTHONPATH": "%s/common" % srcroot},
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE)
		p.wait()
		if p.returncode == 0:
			self.notify("Testerman Agent Controller server started correctly.")
		else:
			self.error("Unable to start Testerman Agent Controller server.")
		return p.returncode

	def doStop(self, component, probeFunction, timeout = 5.0):
		pid = probeFunction()
		if pid > 0:
			self.notify("Stopping %s..." % component)
			os.kill(pid, signal.SIGINT)
			start = time.time()
			while self.tsProbe() > 0 and time.time() < start + timeout:
				time.sleep(0.5)
			if self.tsProbe() > 0:
				self.notify("Unable to stop %s gracefully." % component)
				return -1
			else:
				self.notify("Stopped.")
				return 0
		else:
			self.notify("%s is not running." % component)
			return 0
		
	def stop(self, component = "all"):
		tsStop = lambda: self.doStop(component = "Testerman server", probeFunction = self.tsProbe, timeout = 5.0)
		tacsStop = lambda: self.doStop(component = "Testerman Agent Controller server", probeFunction = self.tacsProbe, timeout = 5.0)
		if component == "server":
			return tsStop()
		elif component == "tacs":
			return tacsStop()
		elif component == "all":
			# Stop whatever we can
			ret = 0
			if tsStop(): ret = -1
			if tacsStop(): ret = -1
			return ret
		else:
			return -1

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
			return -1
	
	def tsProbe(self):
		"""
		Sends a probe to the server at $TESTERMAN_SERVER.
		Returns the pid (> 0) if it is running.
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
		pid = self.tacsProbe()
		if pid > 0:
			self.notify("Testerman Agent Controller Server up and running at %s (management interface), pid %s" % (os.environ.get("TESTERMAN_TACS"), pid))
			return 0
		else:
			self.notify("No Testerman Agent Controller server started at %s" % os.environ.get("TESTERMAN_TACS"))
			return 1

	def tacsProbe(self):
		"""
		Sends a probe to the server to its Ia interface.
		Returns the pid (> 0) if it is running.
		"""
		try:
			ip, port = os.environ.get("TESTERMAN_TACS").split(':')
			client = IaClient((ip, int(port)))
			variables = client.getVariables()["transient"]
			for val in variables:
				if val['key'] == "tacs.pid":
					return val['value']
			return -1
		except Exception:
#			print SIS.getBacktrace()
			return -1
	
	def status(self):
		headers = [ ('component', 'Component'), ('address', 'Management Address'), ('status', 'Status'), ('pid', 'PID')  ]
		rows = []
		pid = self.tsProbe()
		if pid > 0:
			rows.append(dict(component = 'server', status = 'running', pid = pid, address = os.environ.get("TESTERMAN_SERVER")))
		else:
			rows.append(dict(component = 'server', status = 'offline', address = os.environ.get("TESTERMAN_SERVER")))
		pid = self.tacsProbe()
		if pid > 0:
			rows.append(dict(component = 'tacs', status = 'running', pid = pid, address = os.environ.get("TESTERMAN_TACS")))
		else:
			rows.append(dict(component = 'tacs', status = 'offline', address = os.environ.get("TESTERMAN_TACS")))
		self.printTable(headers, rows, order = 'component')


################################################################################
# Main
################################################################################


def getVersion():
	return "Testerman Administration Console %s" % VERSION


def main():
	expandPath = lambda x: x and os.path.abspath(os.path.expandvars(os.path.expanduser(x)))

	# Command Line Options parsin
	parser = optparse.OptionParser(version = getVersion())
		
	group = optparse.OptionGroup(parser, "Basic Options")
	group.add_option("-t", "--target", dest = "target", metavar = "TARGET", help = "target to administrate. Either a path to a Testerman runtime directory (\"Testerman home\") or the URL of a Testerman server. When administrating a specific Testerman server by URL, some control functions (such as start/stop and configuration) may be disabled.", default = None)
	group.add_option("-r", dest = "docroot", metavar = "DOCUMENT_ROOT", help = "force to use DOCUMENT_ROOT as the document root. This overrides the document root auto-detection from the target.", default = None)
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


	# According to the target, autodetect docroot/servers info

	# Managed target: a running server
	if options.target.startswith("http://"):
		serverUrl = options.target
		os.environ["TESTERMAN_SERVER"] = serverUrl
		# Now retrieve the docroot from the running server
		client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)
		
		# Detect settings from the running Testerman server
		try:
			docroot, tacs_ip, tacs_port = None, None, None
			for variable in client.getVariables("ts")['persistent']:
				if variable['key'] == 'testerman.document_root':
					docroot = variable['actual']
				elif variable['key'] == 'tacs.ip':
					tacs_ip = variable['actual']
				elif variable['key'] == 'tacs.port':
					tacs_port = variable['actual']
		except:
			print "Sorry, cannot find a running Testerman server at %s." % serverUrl
			sys.exit(1)

		if not docroot or not tacs_ip or not tacs_port:
			print "Sorry, the Testerman server running at %s cannot be managed (missing a mandatory configuration variable)."
			sys.exit(-1)
		
		os.environ["TESTERMAN_DOCROOT"] = docroot
		os.environ["TESTERMAN_TACS"] = "%s:%s" % (tacs_ip, tacs_port)

		print "Found running Testerman server, using document root: %s" % docroot

		# Forced docroot overrides the autodetection
		if options.docroot:
			os.environ["TESTERMAN_DOCROOT"] = docroot
	

	# Managed target: a complete runtime environment.
	else:
		# a Testerman home dir was provided.
		# Get all other values from the configuration file.
		home = expandPath(options.target)
		os.environ["TESTERMAN_HOME"] = home
		cm = ConfigManager.ConfigManager()
		try:
			cm.read("%s/conf/testerman.conf" % home)
		except Exception, e:
			print "Invalid Testerman target - cannot find or read %s/conf/testerman.conf file." % home
			sys.exit(1)

		# Detect settings from the configuration file
		os.environ["TESTERMAN_DOCROOT"] = expandPath(cm.get("testerman.document_root"))
		ip = cm.get("interface.ws.ip", "")
		if not ip or ip == "0.0.0.0":
			ip = "localhost"
		os.environ["TESTERMAN_SERVER"] = "http://%s:%s" % (ip, cm.get("interface.ws.port", 8080))
		os.environ["TESTERMAN_TACS"] = "%s:%s" % (cm.get("tacs.ip", "127.0.0.1"), cm.get("tacs.port", 8087))

		# Forced docroot overrides the autodetection
		if options.docroot:
			os.environ["TESTERMAN_DOCROOT"] = options.docroot
		
		# Also check if we have a running server
		serverUrl = os.environ["TESTERMAN_SERVER"]
		docroot = os.environ["TESTERMAN_DOCROOT"]
		client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)
		try:
			for variable in client.getVariables("ts")['transient']:
				if variable['key'] == 'testerman.testerman_home':
					runningHome = expandPath(variable['value'])
					if home != runningHome:
						print "WARNING: another Testerman server is already running using the configured URL (%s), located in %s" % (serverUrl, runningHome)
					break
			for variable in client.getVariables("ts")['persistent']:
				if variable['key'] == 'testerman.document_root':
					runningDocroot = expandPath(variable['actual'])
					if docroot != runningDocroot:
						print "WARNING: a Testerman server is already running using the configured URL (%s), but using a different document root (%s) as the one that will be managed by this session (%s)" % (serverUrl, runningDocroot, docroot)
					break
		except:
			pass
		

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
	
