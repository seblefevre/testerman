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

from CiscoInteractiveShell import *

class AgentContext(CommandContext):
	"""
	This context is basically a wrapper over administration-oriented functions on TestermanClient.
	"""
	def __init__(self):
		CommandContext.__init__(self)
		self._client = None
		# Undeploy probe
		node = SequenceNode()
		node.addField("agent", "agent name", StringNode())
		node.addField("probe", "probe name", StringNode())
		self.addCommand("undeploy", "undeploy a probe", node, self.undeployProbe)

		# Deploy probe
		node = SequenceNode()
		node.addField("agent", "agent name", StringNode())
		node.addField("probe", "probe name", StringNode())
		node.addField("type", "probe type", StringNode())
		self.addCommand("deploy", "deploy a probe onto a running agent", node, self.deployProbe)

		# Restart agent		
		node = SequenceNode()
		node.addField("agent", "agent name", StringNode())
		self.addCommand("restart", "restart an agent", node, self.restartAgent)

		# Agent info
		node = SequenceNode()
		node.addField("agent", "agent name", StringNode())
		self.addCommand("show", "display additional details about an agent", node, self.showAgent)

		# Update agent		
		node = SequenceNode()
		node.addField("agent", "agent name", StringNode())
		node.addField("branch", "agent component branch (default: stable)", ChoiceNode().addChoices([("stable", "stable agent branch", NullNode()), ("testing", "testing agent branch", NullNode()), ("experimental", "experimental agent branch", NullNode())]), optional = True)
		node.addField("version", "agent component version (default: latest in branch)", StringNode(), optional = True)
		self.addCommand("update", "update an agent", node, self.updateAgent)

		# list command		
		listableItems = ChoiceNode()
		listableItems.addChoice("agents", "registered agents only", NullNode())
		listableItems.addChoice("probes", "registered probes only", NullNode())
		listableItems.addChoice("all", "all registered distributed components", NullNode())
		self.addCommand("list", "list registered distributed components", listableItems, self.listRegisteredComponents)

	def _getClient(self):
		if not self._client:
			serverUrl = os.environ.get('TESTERMAN_SERVER')
			if not serverUrl:
				raise Exception("Sorry, no testerman server set (TESTERMAN_SERVER).")
			self._client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)

		return self._client

	def listRegisteredComponents(self, itemType):
		ret = {}
		headers = []
		if itemType[0] == "agents":
			headers = [ ('name', 'name'), ('uri', 'uri'), ('type', 'type'), ('contact', 'location'), ('user-agent', 'version') ]
			ret = self._getClient().getRegisteredAgents()
		elif itemType[0] == "probes":
			headers = [ ('name', 'name'), ('uri', 'uri'), ('type', 'type'), ('contact', 'location'), ('user-agent', 'version') ]
			ret = self._getClient().getRegisteredProbes()
		else:
			headers = [ ('uri', 'uri'), ('type', 'type'), ('contact', 'location'), ('user-agent', 'version') ]
			ret = self._getClient().getRegisteredProbes() + self._getClient().getRegisteredAgents()

		self.printTable(headers, ret)

	def showAgent(self, agent):
		ret = {}
		headers = [ ('name', 'name'), ('uri', 'uri'), ('type', 'type'), ('contact', 'location'), ('user-agent', 'version'), ('supported-probes', 'supported probes') ]
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
		ret = self._getClient().restartAgent(agent)
		if not ret:
			self.notify("Unable to restart this agent.")
		else:
			self.notify("Agent successfully restarted.")

	def updateAgent(self, agent, branch = (None, None), version = None):
		"""
		Requests the agent agent:agentName to update
		"""
		self.notify("Updating agent %s..." % agent)
		ret = self._getClient().updateAgent(agent, branch[1], version)
		if not ret:
			self.notify("Unable to update this agent.")
		else:
			self.notify("Agent successfully updated.")
			self.notify("Don't forget to restart it to take the update into account.")

