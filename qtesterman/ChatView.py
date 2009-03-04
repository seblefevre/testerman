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
# A simple chat component based on Xc interface.
#
##

from PyQt4.Qt import *

DEFAULT_CHANNEL = 'testerman'

class WChatView(QWidget):
	"""
	The chat component is basically a 
	read-only text view, displaying events,
	and an input line edit.
	
	Single channel for the server (for now).
	
	Commands are irc-like:
	/who : display who is connected
	/me
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

		self._client = QApplication.instance().client()
		self._channel = None
		self._connected = False

		self.setWindowTitle('Chat room')
		
		layout = QVBoxLayout()
		self._mainView = QTextEdit()
		self._mainView.setReadOnly(True)
		layout.addWidget(self._mainView)
		self._inputLineEdit = QLineEdit()
		layout.addWidget(self._inputLineEdit)
		self.connect(self._inputLineEdit, SIGNAL("returnPressed()"), self.onInputEntered)
		layout.setMargin(0)
		self.setLayout(layout)
		
		self.connect(QApplication.instance(), SIGNAL("testermanXcConnected()"), self.onConnected)
		self.connect(QApplication.instance(), SIGNAL("testermanXcDisconnected()"), self.onDisconnected)
		self.connect(self, SIGNAL("chatNotification"), self.onChatNotification)
		
		self.join(DEFAULT_CHANNEL)

		self.synchronizeOnServerStatus()

	def join(self, channel):
		if channel != self._channel:
			if self._channel:
				uri = 'chat:%s' % self._channel
				self._client.unsubscribe(uri, self._onChatNotification)
			self._channel = channel
			uri = 'chat:%s' % self._channel
			self._client.subscribe(uri, self._onChatNotification)
	
	def _onChatNotification(self, notification):
		"""
		Bouncing to Qt world.
		"""
		self.emit(SIGNAL('chatNotification'), notification)
	
	def onChatNotification(self, notification):
		method = notification.getMethod()
		if method == 'MESSAGE':
			msg = notification.getApplicationBody()
			username = notification.getHeader('Username')
			self.displayUserMessage(username, msg)
	
	def displayUserMessage(self, username, msg):
		
		if username == QApplication.instance().username():
			prefix = '<span style="color: purple; font-weight: bold">%s</span>' % username
		else:
			prefix = '<b>%s</b>' % username
		content = msg.replace('\r', '').replace('\n', '<br>').replace('\t', 4*'&nbsp;')
		text = '%s: %s' % (prefix, content)
		self._mainView.append(text)
	
	def displaySystemEvent(self, msg):
		text = '<i>%s</i>' % msg
		self._mainView.append(text)
	
	def displayUserEvent(self, msg):
		text = '<b>%s</b>' % msg
		self._mainView.append(text)
	
	def onInputEntered(self):
		if self._connected:
			self.sendMessage(unicode(Qt.escape(self._inputLineEdit.text())))
			self._inputLineEdit.clear()
		else:
			self.displaySystemEvent("You are not connected to any server")
		
	def sendMessage(self, text):
		uri = 'chat:%s' % self._channel
		self._client.notify('MESSAGE', uri, text, headers = { 'Username': unicode(QApplication.instance().username()) })

	def onConnected(self):
		self.displaySystemEvent("You have joined #%s on %s" % (self._channel, QApplication.instance().serverUrl().toString()))
		self._connected = True
	
	def onDisconnected(self):
		self.displaySystemEvent("Disconnected")
		self._connected = False
	
	def synchronizeOnServerStatus(self):
		if QApplication.instance().isXcConnected():
			self.onConnected()
		else:
			self.onDisconnected()


################################################################################
# A Dock
################################################################################

class WChatViewDock(QDockWidget):
	def __init__(self, parent):
		QDockWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self._chatView = WChatView(self)
		self.setWidget(self._chatView)
		self.setWindowTitle("Chat room")
