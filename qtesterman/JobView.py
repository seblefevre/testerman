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


import Resources

import time

from PyQt4.Qt import *

import CommonWidgets

################################################################################
# Local Icon Cache
################################################################################

#: may be shared in a common file.
#: however, copying it locally enables more independent modules.
class IconCache:
	def __init__(self):
		self._icons = {}

	def icon(self, resource):
		if not self._icons.has_key(resource):
			self._icons[resource] = QIcon(resource)
		return self._icons[resource]

TheIconCache = IconCache()

def icon(resource):
	return TheIconCache.icon(resource)


################################################################################
# A date/time picker in a dialog, for rescheduling
################################################################################

class WRescheduleDialog(QDialog):
	"""
	Selected a date/time in a dialog
	"""
	def __init__(self, dateTime = None, parent = None):
		QDialog.__init__(self, parent)
		if dateTime is None:
			dateTime = QDateTime.currentDateTime()
		self.__createWidgets(dateTime)

	def __createWidgets(self, dateTime):	
		self.setWindowTitle("Reschedule a run")
		self.setWindowIcon(icon(':icons/testerman.png'))

		layout = QVBoxLayout()

		# Date picker
		self._dateTimePicker = CommonWidgets.WDateTimePicker()
		layout.addWidget(self._dateTimePicker)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self._okButton = QPushButton("Reschedule", self)
		self.connect(self._okButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self._okButton)
		self._cancelButton = QPushButton("Cancel", self)
		self.connect(self._cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self._cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def getScheduledTime(self):
		"""
		Returns the time as a integer (Python time)
		"""
		return self._dateTimePicker.selectedDateTime().toTime_t()


################################################################################
# Tree Widget Items
################################################################################

SECTIONS = [ 'id', 'name', 'state', 'result', 'username', 'type', 'start-time', 'running-time', 'scheduled-at' ]

class JobItem(QTreeWidgetItem):
	def __init__(self, jobInfo, parent = None):
		QTreeWidgetItem.__init__(self, parent)
		self._data = {}
		self.updateFromServer(jobInfo)
	
	def updateFromServer(self, jobInfo):
		"""
		Updates the item according to fresh info received from the server for this job.
		
		@type  jobInfo: dict
		@param jobInfo: dict, as received in a Xc JOB notification
		"""
		self._data = jobInfo
		i = 0
		for s in SECTIONS:
			value = jobInfo[s]
			if s in [ 'scheduled-at', 'start-time', 'stop-time' ]:
				if value: value = time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(value))
				else: value = ''
			elif s in [ 'running-time' ]:
				if value: value = "%2.2f" % value
				else: value = ''
			self.setData(i, Qt.DisplayRole, QVariant(value)) # instead of a setText, to preserve the data type
			i += 1
		
		# Update the icon according to the current state
		t = jobInfo['type']
		s = jobInfo['state']
		r = jobInfo['result']

		i = icon(':/icons/unknown.png')
		if s in [ 'waiting' ]:
			i = icon(':/icons/job-waiting.png')
		elif s in [ 'running' ]:
			i = icon(':/icons/job-running.png')
		elif s in [ 'killing', 'cancelling' ]:
			i = icon(':/icons/job-running.png')
		elif s in [ 'paused' ]:
			i = icon(':/icons/job-paused.png')
		elif s in [ 'complete' ] and r == 0:
			i = icon(':/icons/job-success.png')
		elif s in [ 'complete' ] and r > 0: # This case should not be possible
			i = icon(':/icons/job-warning.png')
		elif s in [ 'cancelled' ]:
			i = icon(':/icons/job-warning.png')
		elif s in [ 'error', 'killed' ]:
			i = icon(':/icons/job-error.png')
		self.setIcon(0, i)

	def getState(self):
		return self._data['state']
	
	def getId(self):
		return self._data['id']

	def getType(self):
		return self._data['type']

################################################################################
# Tree Widget
################################################################################

class WJobTreeWidget(QTreeWidget):
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self._client = None

		self.setWindowIcon(icon(":/icons/job-queue.png"))
		self.setWindowTitle('Job queue')
		
		self._labels = {
			'id': 'Job ID', 'state': 'State', 'parent-id': 'Parent', 'start-time': 'Started at', 
			'running-time': 'Run duration', 'scheduled-at': 'Scheduled start', 
			}
		self.setHeaderLabels([self._labels.get(x, x.title()) for x in SECTIONS])
		self.header().setResizeMode(0, QHeaderView.ResizeToContents)
		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
		self.connect(self, SIGNAL('jobNotification'), self.onJobNotification)
		
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
		self.updateFromServer(jobInfo)
	
	def refresh(self):
		try:
			queue = self._client.getJobQueue()
		except:
			queue = []
		
		self.clear()
		self._items = {} # JobItem indexed by its job id
		for jobInfo in queue:
			self.updateFromServer(jobInfo)

	def updateFromServer(self, jobInfo):
		"""
		Updates or creates an item corresponding to jobInfo.
		"""
		id_ = jobInfo['id']
		if not self._items.has_key(id_):
			# We should create a new item
			parentId = jobInfo['parent-id']
			if parentId == 0: # the root
				parent = self
			else:
				parent = self._items.get(parentId, None)
			if not parent:
				print "DEBUG: missing parent %s to create job node for job id %s" % (parentId, id_)
				return
			# We create a new item
			item = JobItem(jobInfo, parent)
			self._items[id_] = item
		else:
			item = self._items[id_]
			item.updateFromServer(jobInfo)

	def contextMenuEvent(self, event):
		item = self.itemAt(event.pos())
		
		menu = QMenu(self)
		
		if item:
			# Depending of the state, add several actions
			jobId = item.getId()
			state = item.getState()
			type_ = item.getType()
			if not state in [ 'waiting' ]:
				action = menu.addAction("View log...", lambda: self._viewLog(jobId))
				menu.addSeparator()
			if type_ == 'campaign':
				if state in [ 'running' ]:			
					action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))
				elif state in [ 'waiting' ]:
					action = menu.addAction("Start now", lambda: self._client.rescheduleJob(jobId, 0.0))
					action = menu.addAction("Reschedule...", lambda: self._reschedule(jobId))
					action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))
			else: # ATS
				if state in [ 'running' ]:			
					action = menu.addAction("Pause", lambda: self._sendSignal(jobId, 'pause'))
					action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))
					action = menu.addAction("Kill", lambda: self._sendSignal(jobId, 'kill'))
				elif state in [ 'paused' ]:
					action = menu.addAction("Resume", lambda: self._sendSignal(jobId, 'resume'))
					action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))
				elif state in [ 'waiting' ]:
					action = menu.addAction("Start now", lambda: self._client.rescheduleJob(jobId, 0.0))
					action = menu.addAction("Reschedule...", lambda: self._reschedule(jobId))
					action = menu.addAction("Cancel", lambda: self._sendSignal(jobId, 'cancel'))
				elif state in [ 'cancelling' ]:
					action = menu.addAction("Kill", lambda: self._sendSignal(jobId, 'kill'))

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
	
	def _reschedule(self, jobId):
		"""
		Displays a scheduling dialog.
		"""
		scheduleDialog = WRescheduleDialog(parent = self)
		scheduleDialog.setWindowTitle("Reschedule job %s" % jobId)
		if scheduleDialog.exec_() == QDialog.Accepted:
			scheduledTime = scheduleDialog.getScheduledTime()
			res = self._client.rescheduleJob(jobId, scheduledTime)

	def onItemActivated(self, item, col):
		if item:
			self._viewLog(item.getId())

# Basic test
if __name__ == "__main__":
	import sys
	import TestermanClient

	app = QApplication([])

	client = TestermanClient.Client("test", "JobQueue/1.0.0", serverUrl = "http://localhost:8080")
	client.startXc()
	
	w = WJobTreeWidget()
	w.show()
	w.setClient(client)
	
	app.exec_()
	client.stopXc()
	
