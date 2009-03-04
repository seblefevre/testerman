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
# An agent/probe viewer.
#
# Implemented as a model/view Qt Tree.
#
##

import Resources

from PyQt4.Qt import *

#: may be shared in a common file.
#: however, copying it locally enables more independent modules.
class IconCache:
	def __init__(self):
		self._icons = {}

	def icon(self, resource):
		if not self._icons.has_key(resource):
			self._icons[resource] = QIcon(resource)
		return self._icons[resource]


################################################################################
# Qt Model
################################################################################

class AgentItem(QStandardItem):
	def __init__(self, uri):
		QStandardItem.__init__(self)
		self.setText(uri[len('agent:'):])
	
class ProbeItem(QStandardItem):
	def __init__(self, uri):
		QStandardItem.__init__(self)
		self.setText(uri.split('@')[0][len('probe:'):])

class AgentModel(QStandardItemModel):
	def __init__(self, context, parent = None):
		QStandardItemModel.__init__(self, parent)
		self._context = context
		self._items = {} # standard items, per uri
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			if section == 0:
				return QVariant("Name")
			elif section == 1:
				return QVariant("Type")
			elif section == 2:
				return QVariant("Contact")
			elif section == 3:
				return QVariant("URI")
			else:
				return QVariant()
		return QVariant()
	
	def flags(self, index):
		if not index.isValid():
			return 0
		return Qt.ItemIsEnabled | Qt.ItemIsSelectable

	##
	# Addons
	##
	def icon(self, resource):
		return self._context.icon(resource)

	def refresh(self):
		"""
		Refreshes the whole tree through invalidation.
		"""
		self.emit(SIGNAL('layoutAboutToBeChanged()'))

		self.clear()
		self._items.clear()
		# Construct the whole tree
		try:
			probes = self._context.getClient().getRegisteredProbes()
			agents = self._context.getClient().getRegisteredAgents()
			for agent in agents:
				self.addAgent(agent)
			for probe in probes:
				self.addProbe(probe)
		except:
			# Ws error, etc.
			pass

		self.emit(SIGNAL('layoutChanged()'))

	def lockProbe(self, uri):
		if self._items.has_key(uri):
			self._items[uri].setIcon(self.icon(':/icons/probe-locked.png'))

	def unlockProbe(self, uri):
		if self._items.has_key(uri):
			self._items[uri].setIcon(self.icon(':/icons/probe-unlocked.png'))

	def addAgent(self, agentInfo):
		uri = agentInfo['uri']
		agentItem = AgentItem(uri)
		agentItem.setIcon(self.icon(':/icons/agent.png'))
		self.appendRow([ agentItem, QStandardItem(agentInfo['user-agent']), QStandardItem(agentInfo['contact']), QStandardItem(uri) ])
		self._items[uri] = agentItem
	
	def removeAgent(self, uri):
		if self._items.has_key(uri):
			self.takeRow(self._items[uri].row())
	
	def addProbe(self, probeInfo):
		agentUri = probeInfo['agent-uri']
		uri = probeInfo['uri']
		if self._items.has_key(agentUri):
			agentItem = self._items[agentUri]
			if probeInfo['locked']:
				icon = self.icon(':/icons/probe-locked.png')
			else:
				icon = self.icon(':/icons/probe-unlocked.png')
			probeItem = ProbeItem(uri)
			probeItem.setIcon(icon)
			agentItem.appendRow([ probeItem, QStandardItem(probeInfo['type']), QStandardItem(probeInfo['contact']), QStandardItem(uri) ])
			self._items[uri] = probeItem
		
	def removeProbe(self, uri):
		if self._items.has_key(uri):
			probeItem = self._items[uri]
			probeItem.parent().takeRow(probeItem.row())
	
	def isProbe(self, index):
		if index.isValid():
			return isinstance(self.itemFromIndex(index), ProbeItem)
		return False

	def isAgent(self, index):
		if index.isValid():
			return isinstance(self.itemFromIndex(index), AgentItem)
		return False


################################################################################
# Tree View interfacing the Model
################################################################################

class WAgentView(QTreeView):
	"""
	A tree view based on the model.
	
	Configurable to serve as a simple file system view,
	or an enhanced view gathering contextual information according to the viewed
	object (execution history on an ats, expanded packages, etc)
	"""
	def __init__(self, path = '/', parent = None):
		QTreeView.__init__(self, parent)
		self._client = None
		self._path = path
		self._iconCache = IconCache()
		self.setWindowIcon(self.icon(':/icons/probe-manager.png'))
		self.setWindowTitle('Probe manager')
		#: need to keep a local reference to the model, or it will be GC'd by Python
		self._model = AgentModel(context = self)
		self.setModel(self._model)
		self.connect(self, SIGNAL('probeNotification'), self.onProbeNotification)
		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.setSortingEnabled(True)
	
	def setClient(self, client):
		"""
		Attaches a Testerman client instance.
		"""
		self._client = client
		self._client.subscribe('system:probes', self._onProbeNotification)
		self.refresh()

	def _onProbeNotification(self, notification):
		"""
		Bouncing to Qt world.
		"""
		self.emit(SIGNAL('probeNotification'), notification)
	
	def onProbeNotification(self, notification):
		"""
		@type  notification: TestermanMessages.Notification
		@param notification: a new PROBE-EVENT notification from the server.
		"""
		if notification.getMethod() == 'PROBE-EVENT':
			# Forward the update to the model.
			event = notification.getApplicationBody()
			reason = notification.getHeader('Reason')
			print "DEBUG: " + reason
			
			if reason == "agent-registered":
				self.model().addAgent(event)
			elif reason == "probe-registered":
				self.model().addProbe(event)
			elif reason == "agent-unregistered":
				self.model().removeAgent(event['uri'])
			elif reason == "probe-unregistered":
				self.model().removeProbe(event['uri'])
			elif reason == "probe-locked":
				self.model().lockProbe(event['uri'])
			elif reason == "probe-unlocked":
				self.model().unlockProbe(event['uri'])
	
	def refresh(self):
		model = self.model()
		if model:
			model.refresh()
		self.expandAll()

	def contextMenuEvent(self, event):
		index = self.indexAt(event.pos())
		
		menu = QMenu(self)
		
		if index.isValid():
			# Depending of the node, add several actions
			if self.model().isAgent(index):
				action = menu.addAction("Deploy new probe...", lambda: self._deployProbe(index))
				action.setEnabled(False)

			elif self.model().isProbe(index):
				action = menu.addAction("Undeploy", lambda: self._undeployProbe(index))
				action.setEnabled(False)

			menu.addSeparator()
		
		# In any case, general action
		menu.addAction("Refresh all", self.refresh)
		
		menu.popup(event.globalPos())
		
	def _deployProbe(self, index):
		pass
	
	def _undeployProbe(self, index):
		pass
				
	##
	# ViewContext
	##
	def getClient(self):
		return self._client	

	def icon(self, resource):
		return self._iconCache.icon(resource)


# Basic test
if __name__ == "__main__":
	import sys
	import TestermanClient

	app = QApplication([])

	client = TestermanClient.Client("test", "AgentView/1.0.0", serverUrl = "http://localhost:8080")
	client.startXc()
	
	w = WAgentView()
	w.show()
	w.setClient(client)
	
	app.exec_()
	client.stopXc()


	
