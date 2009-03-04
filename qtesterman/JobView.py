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
# A Job Queue widget, displaying the server's job queue,
# enabling basic interaction with it:
# - signal management (send them to a job)
#
# Implemented as a model/view Qt Tree.
#
# Emits some signals to integrate additional logic
# (such as viewing logs)
#
##


import time

from PyQt4.Qt import *

import Resources

class IconCache:
	def __init__(self):
		self._icons = {}

	def icon(self, resource):
		if not self._icons.has_key(resource):
			self._icons[resource] = QIcon(resource)
		return self._icons[resource]


class JobQueueTreeModel(QAbstractItemModel):
	"""
	A Qt Model representation of the server's queue.
	
	Such a queue is actually a tree of jobs, where children
	for a particular jos are identified by their parent-id == the job id.
	"""
	def __init__(self, context, parent = None):
		"""
		Context, in our case, is the view.
		"""
		QAbstractItemModel.__init__(self, parent)
		self._context = context
		# Internally, we stick to a flat model, as retrieved by Ws.getJobQueue()
		self._queue = []
		# Same thing, indexed by the job id for better efficiency
		self._indexedQueue = {}
		# Sections to display in the tree. Must match existing dict entries in self._queue entries.
		self._sections = [ 'id', 'name', 'state', 'result', 'username', 'type', 'start-time', 'running-time', 'scheduled-at' ]
		self._sectionLabels = {'id': 'id', 'state': 'state', 'parent-id': 'parent', 'start-time': 'started at', 'running-time': 'running duration', 'scheduled-at': 'scheduled start' }
		
	def icon(self, resource):
		return self._context.icon(resource)
	
	def index(self, row, column, parentIndex):
		"""
		In this model implementation, we store the job-id into the modelIndex.internalId,
		the full job data, stored as a dict, can then be retrieved bia sef._indexedQueue[job-id].
		"""
		if not self.hasIndex(row, column, parentIndex):
			return QModelIndex()
		
		parentId = None
		
		if not parentIndex.isValid():
			parentId = 0 # the root job: id = 0
		else:
			parentId = parentIndex.internalId()
		
		# Now we scan the flat queue and gather childrens corresponding to the parent
		childrens = filter(lambda x: x['parent-id'] == parentId, self._queue)
		if row < len(childrens):
			return self.createIndex(row, column, childrens[row]['id'])
		else:
			# invalid child
			return QModelIndex()
		
	def flags(self, index):
		if not index.isValid():
			return 0
		return Qt.ItemIsEnabled | Qt.ItemIsSelectable
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return QVariant(self._sectionLabels.get(self._sections[section], self._sections[section]))
		return QVariant()
	
	def parent(self, index):
		"""
		Returns the modelIndex of the parent of index.
		For that purpose, we need to know its own parent, i.e. index's grand parent.
		"""
		if not index.isValid():
			return QModelIndex()

		itemId = index.internalId()
		
		if itemId == 0:
			# The root has no parent
			return QModelIndex()

		# Retrieves the item info
		# itemDict = filter(lambda x: x['id'] == itemId, self._queue)[0]
		itemDict = self._indexedQueue[itemId]
		parentId = itemDict['parent-id']
		
		if parentId == 0:
			# The parent is the root
			return self.createIndex(0, 0, 0)
		
		parentDict = filter(lambda x: x['id'] == parentId, self._queue)[0]
		# Need to get the row of the parent, ie its index in its parent list
		grandParentId = parentDict['parent-id']
		parentSiblingIds = map(lambda x: x['id'], filter(lambda x: x['parent-id'] == grandParentId, self._queue))
		parentRow = parentSiblingIds.index(parentId)
		
		return self.createIndex(parentRow, 0, parentId)
	
	def columnCount(self, parentIndex):
		# Fixed column count in this model.
		return len(self._sections)
		
	def rowCount(self, parentIndex):
		if parentIndex.isValid():
			itemId = parentIndex.internalId()
		else:
			# The parent is the root
			itemId = 0

		# Now let's count the number of children for this parent
		children = filter(lambda x: x['parent-id'] == itemId, self._queue)
		count = len(children)
		return count

	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		
		if role == Qt.DisplayRole:
			itemId = index.internalId()
			#itemDict = filter(lambda x: x['id'] == itemId, self._queue)[0]
			itemDict = self._indexedQueue[itemId]

			fieldId = self._sections[index.column()]
			value = itemDict[fieldId]

			# Some formatting
			if value is not None:
				if fieldId in [ 'scheduled-at', 'start-time', 'stop-time' ]:
					value = time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(value))
				elif fieldId in [ 'running-time' ]:
					value = "%2.2f" % value
			else:
				value = ''

			return QVariant(value)

		elif role == Qt.DecorationRole and index.column() == 0:
			# Icon computation according to job type, status, result
			itemId = index.internalId()
			itemDict = self._indexedQueue[itemId]
			t = itemDict['type']
			s = itemDict['state']
			r = itemDict['result']

			ret = self.icon(':/icons/unknown.png')
			
			if s in [ 'waiting' ]:
				ret = self.icon(':/icons/job-waiting.png')
			elif s in [ 'running' ]:
				ret = self.icon(':/icons/job-running.png')
			elif s in [ 'killing', 'cancelling' ]:
				ret = self.icon(':/icons/job-running.png')
			elif s in [ 'paused' ]:
				ret = self.icon(':/icons/job-paused.png')
			elif s in [ 'complete' ] and r == 0:
				ret = self.icon(':/icons/job-success.png')
			elif s in [ 'complete' ] and r > 0: # This case should not be possible
				ret = self.icon(':/icons/job-warning.png')
			elif s in [ 'cancelled' ]:
				ret = self.icon(':/icons/job-warning.png')
			elif s in [ 'error', 'killed' ]:
				ret = self.icon(':/icons/job-error.png')

			return QVariant(ret)
		
		else:
			return QVariant()
	
	##
	# Model specific
	##
	def updateQueue(self, queue):
		"""
		Replaces the existing queue with a fresh one.
		
		@type  queue: list of dicts (jobInfo)
		@param queue: the replacement queue
		"""
#		self.emit(SIGNAL('layoutAboutToBeChanged()'))
		self._queue = queue
		self._indexedQueue.clear()
		for d in self._queue:
			self._indexedQueue[d['id']] = d
		self.reset()
#		self.emit(SIGNAL('layoutChanged()'))
	
	def updateJobInfo(self, jobInfo):
		"""
		Updates (or add) a job with jobInfo data.
		
		@type  jobInfo: a dict{'id': integer, 'name': string, ....}
		@param jobInfo: the new info to take into account.
		"""
		# Quick and dirty approach: update the internal queue,
		# reconstruct the model. Not optimal at all.
		updated = False
		queue = []
		for info in self._queue:
			if info['id'] == jobInfo['id']:
				queue.append(jobInfo)
				updated = True
			else:
				queue.append(info)
		if not updated:
			# New job
			queue.append(jobInfo)
		
		# We should be more incremental.
		# For large job list, this could be a real bottleneck.
		self.updateQueue(queue)

	def getId(self, index):
		"""
		Returns the job ID for a particular index.
		"""
		if not index.isValid():
			return None
		
		itemId = index.internalId()
		itemDict = self._indexedQueue[itemId]
		return itemDict['id']	

	def getState(self, index):
		"""
		Returns the job state for a particular index.
		"""
		if not index.isValid():
			return None
		
		itemId = index.internalId()
		itemDict = self._indexedQueue[itemId]
		return itemDict['state']	

			

class WJobView(QTreeView):
	"""
	@emits: showLog(int jobId)
	"""
	def __init__(self, parent = None):
		QTreeView.__init__(self, parent)
		self._client = None
		self._iconCache = IconCache()
		self.setWindowIcon(self.icon(":/icons/job-queue.png"))
		self.setWindowTitle('Job queue')

		#: need to keep a local reference to the model, or it will be GC'd by Python ?
		model = JobQueueTreeModel(context = self, parent = self)
		self.setModel(model)
		self.connect(self, SIGNAL('jobNotification'), self.onJobNotification)

		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.setSortingEnabled(True)

	def icon(self, resource):
		return self._iconCache.icon(resource)
	
	def setClient(self, client):
		"""
		Attaches a Testerman client instance.
		"""
		self._client = client
		self._client.subscribe('system:jobs', self._onJobNotification)
		self.refresh()

	def getClient(self):
		return self._client
	
	def _onJobNotification(self, notification):
		"""
		Bouncing to Qt world.
		"""
		self.emit(SIGNAL('jobNotification'), notification)
	
	def onJobNotification(self, notification):
		"""
		@type  notification: TestermanMessages.Notification
		@param notification: a new JOB-EVENT notification from the server.
		"""
		if not notification.getMethod() == 'JOB-EVENT':
			return
		# Forward the job update to the model.
		jobInfo = notification.getApplicationBody()
		self.model().updateJobInfo(jobInfo)
	
	def refresh(self):
		try:
			queue = self._client.getJobQueue()
		except:
			queue = []
		self.model().updateQueue(queue)
		
	def contextMenuEvent(self, event):
		index = self.indexAt(event.pos())
		
		menu = QMenu(self)
		
		if index.isValid():
			# Depending of the state, add several actions
			jobId = self.model().getId(index)
			state = self.model().getState(index)
			action = menu.addAction("View log...", lambda: self._viewLog(jobId))
			menu.addSeparator()
			if state in [ 'running' ]:			
				action = menu.addAction("Pause", lambda: self._sendSignal(jobId, 'pause'))
				action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))
				action = menu.addAction("Kill", lambda: self._sendSignal(jobId, 'kill'))
			elif state in [ 'paused' ]:
				action = menu.addAction("Resume", lambda: self._sendSignal(jobId, 'resume'))
				action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))
			elif state in [ 'waiting' ]:
				action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))

			menu.addSeparator()
		
		# In any case, general action
		menu.addAction("Refresh all", self.refresh)
		
		menu.popup(event.globalPos())

	def _sendSignal(self, jobId, signal):
		try:
			self._client.sendSignal(jobId, signal)	
		except Exception, e:
			print "DEBUG: " + str(e)

	def _viewLog(self, jobId):
		self.emit(SIGNAL('showLog(int)'), jobId)	

# Basic test
if __name__ == "__main__":
	import sys
	import TestermanClient

	app = QApplication([])

	client = TestermanClient.Client("test", "JobQueue/1.0.0", serverUrl = "http://localhost:8080")
	client.startXc()
	
	w = WJobView()
	w.show()
	w.setClient(client)
	
	app.exec_()
	client.stopXc()
	
