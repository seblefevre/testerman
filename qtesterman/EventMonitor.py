##
# -*- coding: utf-8 -*-
#
# Real-time event monitor Qt object and associated control widget.
#
# $Id$
##

import PyQt4.Qt as qt
import PyQt4.QtXml as QtXml

import time
import re

from Base import *


class EventMonitor(qt.QObject):
	"""
	This QObject can emit events formatted as qt signals when subscribed events arrive.

	This is basically a Qt wrapper over the TestermanClient subscription model.
	Manages only one subscription at the time, i.e. you should have one EventMonitor object per subscription.

	emit:
	subscribedEvent : an event as been received, forwarded as is (i.e. as a TestermanClient.Notification)
	NB: these are "python" signals, without any () typing. (i.e. "subscribedEvent" instead of "subscribedEvent(Event)")
	"""
	def __init__(self, parent = None):
		qt.QObject.__init__(self, parent)
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
		self.emit(qt.SIGNAL("subscribedEvent"), event)


################################################################################
# Event Monitor widget, for debug only
################################################################################

class WEventMonitorDock(qt.QDockWidget):
	"""
	Dock wrapper over a WEventMonitor
	"""
	def __init__(self, parent):
		qt.QDockWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWidget(WEventMonitor(self))
		self.setWindowTitle("Event Monitor")

class WEventMonitor(qt.QWidget):
	"""
	Some controllers to control ans associated EventMonitor,
	and a textbox to display events.
	Used for debug/tests purposes only, useless for the actual purposes of QTesterman.
	"""
	def __init__(self, uri = 'system:ts', parent = None):
		qt.QWidget.__init__(self, parent)
		self.eventMonitor = EventMonitor()
		self.uri = uri
		self.__createWidgets()

	def __createWidgets(self):
		layout = qt.QVBoxLayout()

		# A top bar with the URI to subscribe
		topbar = qt.QHBoxLayout()
		topbar.addWidget(qt.QLabel("URI to monitor:"))
		self.uriLineEdit = qt.QLineEdit(self.uri)
		topbar.addWidget(self.uriLineEdit)
		self.subscribeButton = qt.QPushButton('Subscribe')
		self.connect(self.subscribeButton, qt.SIGNAL("clicked()"), self.subscribe)
		topbar.addWidget(self.subscribeButton)
		layout.addLayout(topbar)

		# A text edit to display incoming events
		self.textEdit = qt.QTextEdit()
		self.textEdit.setReadOnly(1)
		layout.addWidget(self.textEdit)
		layout.setMargin(0)

		self.connect(self.eventMonitor, qt.SIGNAL("subscribedEvent"), self.appendEvent)

		self.setLayout(layout)

	def appendEvent(self, event):
		self.textEdit.append(str(event))

	def subscribe(self):
		if self.eventMonitor.subscribe(unicode(self.uriLineEdit.text())):
			self.subscribeButton.setText('Unsubscribe')
			self.disconnect(self.subscribeButton, qt.SIGNAL("clicked()"), self.subscribe)
			self.connect(self.subscribeButton, qt.SIGNAL("clicked()"), self.unsubscribe)

	def unsubscribe(self):
		if self.eventMonitor.unsubscribe():
			self.subscribeButton.setText('Subscribe')
			self.disconnect(self.subscribeButton, qt.SIGNAL("clicked()"), self.unsubscribe)
			self.connect(self.subscribeButton, qt.SIGNAL("clicked()"), self.subscribe)

