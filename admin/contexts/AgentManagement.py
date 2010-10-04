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
# Agent and probe management context for testerman-admin.
#
##


import TestermanClient

import os

##
# Context definition
##

from StructuredInteractiveShell import *

class AgentContext(CommandContext):
	"""
	This context is basically a wrapper over administration-oriented functions on TestermanClient.
	"""
	def __init__(self):
		CommandContext.__init__(self)
		self._client = None
		# Undeploy probe
		node = SequenceNode()
		node.addField("agent", "target agent", StringNode("agent name"))
		node.addField("probe", "probe to undeploy", StringNode("probe name"))
		self.addCommand("undeploy", "undeploy a probe", node, self.undeployProbe)

		# Deploy probe
		node = SequenceNode()
		node.addField("agent", "target agent", StringNode("agent name"))	
		node.addField("probe", "probe to deploy", StringNode("probe name"))		
		node.addField("type", "probe type", StringNode("probe type"))
		self.addCommand("deploy", "deploy a probe onto a running agent", node, self.deployProbe)

		# Update agent
		branches = EnumNode()
		branches.addChoice("stable", "stable version")
		branches.addChoice("testing", "testing version")
		branches.addChoice("experimental", "experimental version")
		node = SequenceNode()
		node.addField("agent", "target agent", StringNode("agent name"))
		node.addField("branch", "agent component branch (default: stable)", branches, optional = True)
		node.addField("version", "agent component version (default: latest in branch)", StringNode("component version"), optional = True)
		self.addCommand("update", "update an agent", node, self.updateAgent)

		# Restart agent		
		node = SequenceNode()
		node.addField("agent", "agent to restart", StringNode("agent name"))
		self.addCommand("restart", "restart an agent", node, self.restartAgent)

		# show
		node = ChoiceNode()
		node.addChoice("agent", "show details about an agent", StringNode("agent name"))
		node.addChoice("agents", "show registered agents")
		node.addChoice("probes", "show registered probes")
		node.addChoice("all", "show all registered distributed components")
		self.addCommand("show", "show various info", node, self.show)

	def _getClient(self):
		if not self._client:
			serverUrl = os.environ.get('TESTERMAN_SERVER')
			if not serverUrl:
				raise Exception("Sorry, no testerman server set (TESTERMAN_SERVER).")
			self._client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)
		return self._client

	def show(self, choice):
		name, value = choice
		if name == 'agent':
			return self.showAgent(value)
		elif name in [ 'agents', 'probes', 'all' ]:
			return self.showRegisteredComponents(name)

	def showRegisteredComponents(self, itemType):
		ret = {}
		headers = []
		if itemType == "agents":
			headers = [ ('name', 'Name'), ('uri', 'URI'), ('type', 'Type'), ('contact', 'Location'), ('user-agent', 'Version') ]
			ret = self._getClient().getRegisteredAgents()
		elif itemType == "probes":
			headers = [ ('name', 'Name'), ('uri', 'URI'), ('type', 'Type'), ('contact', 'Location'), ('user-agent', 'Version') ]
			ret = self._getClient().getRegisteredProbes()
		else:
			headers = [ ('uri', 'URI'), ('type', 'Type'), ('contact', 'Location'), ('user-agent', 'Version') ]
			ret = self._getClient().getRegisteredProbes() + self._getClient().getRegisteredAgents()

		self.printTable(headers, ret)

	def showAgent(self, agent):
		ret = {}
		headers = [ ('name', 'Name'), ('uri', 'URI'), ('type', 'Type'), ('contact', 'Location'), ('user-agent', 'Version'), ('supported-probes', 'Supported probes') ]
		ret = None
		for ag in self._getClient().getRegisteredAgents():
			if ag['name'] == agent:
				ret = ag
				ret['supported-probes'].sort()
				ret['supported-probes'] = '\n'.join(ret['supported-probes'])
		if not ret:
			self.notify("Agent %s not found." % agent)
		else:
			self.printForm(headers, ret)
		
	def undeployProbe(self, agent, probe):
		"""
		Undeploys probe:probeName@agentName
		"""
		self.notify("Undeploying probe %s on agent %s..." % (probe, agent))
		ret = self._getClient().undeployProbe(agent, probe)
		if not ret:
			self.notify("Unable to undeploy.")
		else:
			self.notify("Probe successfully undeployed.")

	def deployProbe(self, agent, probe, **kwargs):
		"""
		Deploys a new probe probe:probeName@agentName
		"""
		self.notify("Deploying probe %s on %s..." % (probe, agent))
		ret = self._getClient().deployProbe(agent, probe, kwargs['type'])
		if not ret:
			self.notify("Unable to deploy.")
		else:
			self.notify("Probe successfully deployed.")

	def restartAgent(self, agent):
		"""
		Restarts the agent agent:agentName
		"""
		self.notify("Restarting agent %s..." % agent)
		try:
			self._getClient().restartAgent(agent)
			self.notify("Agent successfully restarted.")
		except Exception, e:
			self.notify("Unable to restart this agent:\n%s" % str(e))

	def updateAgent(self, agent, branch = 'stable', version = None):
		"""
		Requests the agent agent:agentName to update
		"""
		self.notify("Updating agent %s..." % agent)
		try:
			self._getClient().updateAgent(agent, branch, version)
			self.notify("Agent successfully updated.")
			self.notify("Don't forget to restart it to take the update into account.")
		except Exception, e:
			self.notify("Unable to update this agent:\n%s" % str(e))

