# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 QTesterman contributors
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
# Real-time event monitor Qt object and associated control widget.
#
##

from PyQt4.Qt import *
import PyQt4.QtXml as QtXml

import time
import re

from Base import *


class EventMonitor(QObject):
	"""
	This QObject can emit events formatted as qt signals when subscribed events arrive.

	This is basically a Qt wrapper over the TestermanClient subscription model.
	Manages only one subscription at the time, i.e. you should have one EventMonitor object per subscription.

	emit:
	subscribedEvent : an event as been received, forwarded as is (i.e. as a TestermanClient.Notification)
	NB: these are "python" signals, without any () typing. (i.e. "subscribedEvent" instead of "subscribedEvent(Event)")
	"""
	def __init__(self, parent = None):
		QObject.__init__(self, parent)
		self.subscribedUri = None

	def subscribe(self, uri):
		"""
		perform a subscription for the provided uri.
		Returns True if the subscription was actually performed.
		"""
		if not uri:
			return

		if self.subscribedUri:
			self.unsubscribe()

		try:
			# NB: local IP address is only taken into account once, during the first subscription.
			getProxy().subscribe(uri, callback = self.onReceivedEvent)
			self.subscribedUri = uri
		except Exception, e:
			print("Unable to subscribe: %s" % str(e))
			return False

		return True

	def unsubscribe(self):
		"""
		Unsubscribe.
		Returns True if the unsubscription was actually performed;
		"""
		if not self.subscribedUri:
			return

		try:
			getProxy().unsubscribe(self.subscribedUri, callback = self.onReceivedEvent)
			self.subscribedUri = None
		except Exception, e:
			print("Unable to unsubscribe: %s" % str(e))
			return False

		return True

	def onReceivedEvent(self, event):
		"""
		Called when a, event has been received from the monitoring thread.
		This bouncing function is only here because the monitoring thread is not a QObject.
		"""
		# We bounce the event to switch threads
		self.emit(SIGNAL("subscribedEvent"), event)


################################################################################
# Event Monitor widget, for debug only
################################################################################

class WEventMonitorDock(QDockWidget):
	"""
	Dock wrapper over a WEventMonitor
	"""
	def __init__(self, parent):
		QDockWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWidget(WEventMonitor(self))
		self.setWindowTitle("Event Monitor")

class WEventMonitor(QWidget):
	"""
	Some controllers to control ans associated EventMonitor,
	and a textbox to display events.
	Used for debug/tests purposes only, useless for the actual purposes of QTesterman.
	"""
	def __init__(self, uri = 'system:ts', parent = None):
		QWidget.__init__(self, parent)
		self.eventMonitor = EventMonitor()
		self.uri = uri
		self.__createWidgets()

	def __createWidgets(self):
		layout = QVBoxLayout()

		# A top bar with the URI to subscribe
		topbar = QHBoxLayout()
		topbar.addWidget(QLabel("URI to monitor:"))
		self.uriLineEdit = QLineEdit(self.uri)
		topbar.addWidget(self.uriLineEdit)
		self.subscribeButton = QPushButton('Subscribe')
		self.connect(self.subscribeButton, SIGNAL("clicked()"), self.subscribe)
		topbar.addWidget(self.subscribeButton)
		layout.addLayout(topbar)

		# A text edit to display incoming events
		self.textEdit = QTextEdit()
		self.textEdit.setReadOnly(1)
		layout.addWidget(self.textEdit)
		layout.setMargin(0)

		self.connect(self.eventMonitor, SIGNAL("subscribedEvent"), self.appendEvent)

		self.setLayout(layout)

	def appendEvent(self, event):
		self.textEdit.append(str(event))

	def subscribe(self):
		if self.eventMonitor.subscribe(unicode(self.uriLineEdit.text())):
			self.subscribeButton.setText('Unsubscribe')
			self.disconnect(self.subscribeButton, SIGNAL("clicked()"), self.subscribe)
			self.connect(self.subscribeButton, SIGNAL("clicked()"), self.unsubscribe)

	def unsubscribe(self):
		if self.eventMonitor.unsubscribe():
			self.subscribeButton.setText('Subscribe')
			self.disconnect(self.subscribeButton, SIGNAL("clicked()"), self.unsubscribe)
			self.connect(self.subscribeButton, SIGNAL("clicked()"), self.subscribe)

