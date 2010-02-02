##
# -*- coding: utf-8 -*-
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
# This module is responsible for managing (mainly remote) probes, on the Testerman Server
# side only.
#
# - It enables dynamic probe deployment using ssh or on localhost.
# - Limitation: no ability to stop probes
#
##

import ConfigManager
import EventManager
import TestermanAgentControllerClient as TACC

import logging

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.ProbeManager')

class ProbeManager:
	"""
	TS-side manager for all probe- (and agent-) related events.
	"""
	def __init__(self):
		self._proxy = None
	
	def initialize(self):
		self._proxy = TACC.IaClient('TS.ProbeManager')
		address = (ConfigManager.get("tacs.ip"), ConfigManager.get("tacs.port"))
		# Register callbacks
		self._proxy.setProbeNotificationCallback(self._onProbeNotification)
		self._proxy.initialize(address)
		self._proxy.start()
		getLogger().info("Initializing: subscribing to probes")
		self._proxy.subscribe("system:probes")
	
	def finalize(self):
		self._proxy.stop()
		self._proxy.finalize()

	def _onProbeNotification(self, notification):
		"""
		Called on a new probe/agent notification from the TACS.
		"""
		getLogger().debug("New probe notification: %s" % str(notification))
		EventManager.instance().dispatchNotification(notification)

	def getRegisteredProbes(self):
		"""
		Returns a list of registered probes, proxying the info returned by the TACS.
		
		@rtype: list of dict{name: string, type: string, contact: string, locked: bool, uri: string}
		@returns: a list of registered probes with their names, types, contact (extracted from their agent),
		uri, and locking state
		"""
		res = []
		for entry in self._proxy.getRegisteredProbes():
			res.append({ 'name': entry['name'], 'type': entry['type'], 
			             'contact': entry['contact'], 'uri': entry['uri'], 'locked': entry['locked'], 'agent-uri': entry['agent-uri']})
		return res
	
	def getRegisteredAgents(self):
		res = []
		for entry in self._proxy.getRegisteredAgents():
			res.append({ 'name': entry['uri'][len('agent:'):], 'type': 'pyagent', # hardcoded for now 
			             'contact': entry['contact'], 'uri': entry['uri'], 'supported-probes': entry['supported-probes'], 'user-agent': entry['user-agent']})
		return res

	def deployAgent(self, type_, name, target, password = None):
		"""
		FFS.
		Deploys a new agent instance of agent type type_ on target via SSH.
		Available agents shoud be pyagent, cppagent (compiled for selected platforms), jagent, etc.
		There is one different package per agent type, and one particular command line to use.
		
		Constraints: the target must be reachable through SSH from the Testerman Server.
		"""
		pass

	def deployProbe(self, agentName, probeName, probeType):
		"""
		Deploys a probe on a running agent.
		The resulting probe URI will be probe:probeName@agentName.
		
		@type  agentName: string
		@param agentName: the name of the deployed agent (i.e. not its URI)
		@type  probeName: string
		@param probeName: the name of the probe to deploy
		@type  probeType: string
		@param probeType: the type of the probe to deploy. If 
		this type is not supported on the agent, returns False.
		
		@rtype: bool
		@returns: True if OK, False otherwise.
		"""
		probeUri = "probe:%s@%s" % (probeName, agentName)
		return self._proxy.deployProbe(probeUri, probeType)

	def undeployProbe(self, agentName, probeName):
		"""
		Undeploys a running probe whose uri is probe:probeName@agentName.
		
		@type  agentName: string
		@param agentName: the name of the deployed agent (i.e. not its URI)
		@type  probeName: string
		@param probeName: the name of the probe to undeploy
		
		@rtype: bool
		@returns: True if OK (already undeployed or undeployed successfully), False otherwise.
		"""
		probeUri = "probe:%s@%s" % (probeName, agentName)
		return self._proxy.undeployProbe(probeUri)

	def restartAgent(self, agentName):
		"""
		Restarts an agent whose uri is agent:agentName
		
		@type  agentName: string
		@param agentName: the name of the agent to restart (i.e. not its URI)
		
		@rtype: bool
		@returns: True if the restart request was correctly taken into account, False otherwise
		"""
		agentUri = "agent:%s" % (agentName)
		return self._proxy.restartAgent(agentUri)

	def updateAgent(self, agentName, branch = None, version = None):
		"""
		Requires an agent to update to version/branch (if provided), or to update to the
		latest version of branch (if provided), or to update to the latest version
		of its default branch (if no version/branch provided).
		
		@type  agentName: string
		@param agentName: the name of the agent to update (i.e. not its URI)
		@type  branch: string
		@param branch: a version branch (usually 'experimental', 'stable', ...)
		@type  version: string
		@param version: a valid version for the agent component
		
		@rtype: bool
		@returns: True if the restart request was correctly taken into account, False otherwise
		"""
		agentUri = "agent:%s" % (agentName)
		return self._proxy.updateAgent(agentUri)


TheProbeManager = None

def instance():
	global TheProbeManager
	if TheProbeManager is None:
		TheProbeManager = ProbeManager()
	return TheProbeManager

def initialize():
	instance().initialize()

def finalize():
	instance().finalize()		





