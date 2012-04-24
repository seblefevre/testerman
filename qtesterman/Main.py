# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009-2011 QTesterman contributors
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
# Main Window/Widget
#
##

from PyQt4.Qt import *
from PyQt4 import QtXml

import sys
import os
import os.path
import getopt

import TestermanClient

from Base import *
from CommonWidgets import *

import AutoUpdate
import ProbeManager
import Logger
import JobManager
import RemoteBrowsers
import DocumentPropertyEditor
import PluginManager
import Plugin
import OutlineView
import ChatView
import Preferences
import DocumentManager
import LogViewer

# FIXME: editors should be loaded as "plugins"
# The Editors module contains a reference to QScintilla.
# We'll let the main application code display an error
# dialog if the import fails.

try:
	import Editors
except Exception, e:
	log(str(e))


################################################################################
# TestermanClient.Client wrapper
################################################################################

class QTestermanClient(QObject, TestermanClient.Client):
	"""
	QObjectization of a TestermanClient.Client class.
	Emits signals when connected/disconnected from Xc interface.
	"""
	def __init__(self, userAgent, serverUrl, parent = None):
		QObject.__init__(self, parent)
		TestermanClient.Client.__init__(self, "qtesterman", "QTesterman/" + getClientVersion(), serverUrl)
	
	def onConnection(self, channel):
		"""
		Reimplemented from TestermanClient.Client
		"""
		TestermanClient.Client.onConnection(self, channel)
		self.emit(SIGNAL("xcConnected()"))

	def onDisconnection(self, channel):
		"""
		Reimplemented from TestermanClient.Client
		"""
		TestermanClient.Client.onDisconnection(self, channel)
		self.emit(SIGNAL("xcDisconnected()"))
	

################################################################################
# Specialized QApplication
################################################################################

class QTestermanApplication(QApplication):
	"""
	TestermanClient application:
	a QApplication that embeds a plain Python TestermanClient to offer
	a more Qt-like interface,
	and with additional addons:
	- application-wide variable management (get/set)
	- icon proxy
	
	The Testerman-client facet provides:
	- a way to switch server
	- emit signals when the server has been updated, connected, disconnected
	
	emits:
	testermanServerUpdated(QUrl url)
	testermanXcConnected() # Xc connected
	testermanXcDisconnected() # Xc disconnected
	testermanWsUnavailable() # Ws unreachable
	testermanWsAvailable() # Ws works
	"""
	def __init__(self, args):
		QApplication.__init__(self, args)

		# Application variables
		self.__vars = {}
		# Icon cache
		self.__iconsCache = {}
		# The embedded testerman client
		self.__testermanClient = None
		self._username = None
		self._xcConnected = False
		self._splash = None # splashscreen
		self._serverUrl = None # QUrl

	def icon(self, resource):
		"""
		Gets a new icon. 
		Retrieved from cache if the resource does not exist yet.

		@type  resource: string/unicode
		@param resource: the resource identifier ("resource:/....ico", etc)

		@rtype: QIcon
		@returns: the QIcon corresponding to the resource.
		"""
		if not self.__iconsCache.has_key(resource):
			self.__iconsCache[resource] = QIcon(resource)
		return self.__iconsCache[resource]

	def get(self, key, default = None):
		"""
		Returns the value of an application variable.
		@type  key: string
		@param key: the name of the variable
		
		@rtype: object
		@returns: the value associated to the variable, or the default
		          value if not set.
		"""
		return self.__vars.get(key, default)

	def set(self, key, value):
		"""
		Sets an application variable.
		
		@type  key: string
		@param key: the name of the variable
		@type  value: object
		@param value: the value to assign to the application variable
		"""
		self.__vars[key] = value

	def client(self):
		"""
		Returns the embedded TestermanClient.
		@rtype: TestermanClient.Client instance
		@returns: the embedded Testerman client.
		"""
		return self.__testermanClient

	def setUsername(self, username):
		"""
		Sets the username to use for Testerman server interactions.
		
		@type  username: QString
		@param username: the username
		"""
		self._username = username

	def username(self):
		"""
		@rtype: QString
		@returns: the current username for the session
		"""
		return self._username

	def serverUrl(self):
		"""
		Returns the current server URL.
		
		@rtype: QUrl
		@returns: the curent server URL
		"""
		return self._serverUrl
		
	def setServerUrl(self, url, force = False):
		"""
		Sets the Testerman server, url.
		Automatically tries to connect to its Xc interface.
		
		@type  url: QUrl
		@param url: the new server url
		@type  force: bool
		@param force: if set, reconnects to the server if the url is the same.
		              Otherwise, does nothing if the server is unchanged.
		
		If the new url is the same as the current one, a reconnection occurs.
		
		emit:
		testermanServerUpdated(QUrl url)

		You should expect a xcConnectionUpdated(QString state) signal regarding
		the Xc interface.
		"""
		
		if not force and self._serverUrl == url:
			log("Not setting server to %s: same server" % url.toString())
			return
		
		log("Setting server to %s" % url.toString())
		self._serverUrl = url

		# Translated to string, for the plain underlying Python TestermanClient.Client class
		serverUrl = "http://%s:%s" % (url.host(), url.port(8080))

		if not self.__testermanClient:
			self.__testermanClient = QTestermanClient("QTesterman/" + getClientVersion(), serverUrl = serverUrl, parent = self)
			self.connect(self.__testermanClient, SIGNAL("xcConnected()"), self.onXcConnected)
			self.connect(self.__testermanClient, SIGNAL("xcDisconnected()"), self.onXcDisconnected)
		else:	
			self.__testermanClient.stopXc()
			self.__testermanClient.setServerUrl(serverUrl)

		# Reference this last used url in persistent settings
		settings = QSettings()		
		lasturl = settings.setValue('connection/lasturl', QVariant(url.toString()))

		# Let's emit our signal
		self.emit(SIGNAL('testermanServerUpdated(QUrl)'), url)

		# Finally, starts the Xc interface
		ret = self.__testermanClient.startXc()
		if not ret:
			self.emit(SIGNAL('testermanWsUnavailable()'))
		else:
			self.emit(SIGNAL('testermanWsAvailable()'))

	def onXcConnected(self):
		"""
		Forwards the signal as a higher-level signal.
		"""
		self.emit(SIGNAL('testermanXcConnected()'))
		log("Connected to Xc")
		self._xcConnected = True
	
	def onXcDisconnected(self):
		"""
		Forwards the signal as a higher-level signal.
		"""
		self.emit(SIGNAL('testermanXcDisconnected()'))
		log("Disconnected from Xc")
		self._xcConnected = False
	
	def isXcConnected(self):
		return self._xcConnected
	
	def notifyInitializationProgress(self, message):
		"""
		To call when the application wants to inform the user
		of a new initialization steps.
		The current implementation is updating a message on a splashcreen.
		
		@type  message: string/QString
		@param message: the message to display
		"""
		self._splash.showMessage(message)
		self.processEvents()
	
	def showSplashScreen(self):
		"""
		Creates and show a splash screen.
		"""
		pixmap = QPixmap(":images/splash.png").scaled(QSize(500, 300), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
		self._splash = QSplashScreen(pixmap)
		self._splash.showMessage("Initializing...")
		self._splash.show()
		self.processEvents()
	
	def finishSplashScreen(self, window):
		self._splash.finish(window)
		self._splash = None
	


################################################################################
# Server Status Widget
################################################################################

class WServerStatusIndicator(QWidget):
	"""
	This widget displays a visual indicator regarding the server connection
	(Xc interface + basic Ws status).
	Enables fast server switching, too.
	
	The status is 3-state:
	- error: Ws interface failed. The server was not reachable at the time we switched to it.
	- warning: Xc interface not connected. We keep retrying to connect to it. 
	  In the meanwhile, real time logs and notifications won't be available.
	- ok: Xc interface up and running. This implies Ws is OK, too.
	
	Valid transitions:
	error -> ok
	warning -> error
	warning -> ok (Xc recovered)
	ok -> warning (Xc dropped)
	
	In particular, error -> warning is not possible.
	FIXME: we should manage a "Ws connection state" correctly, with regular retries if needed.
	Going from error to warning is quite possible when rediscovering a server that
	announces an Xc address that is still not reachable from the client (or due to firewalls).
	TODO: embed this Ws state management within the TestermanClient.Client, QTestermanClient,
	or QTestermanApplication

	
	NB: for now, the TestermanClient does not pool for Ws link check regularly.
	That's why we won't go from error to ok or warning without an explicit resynchronisation
	attempt by the user.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		# A label with the server url,
		# an icon indicating the status (connected/disconnected/reconnecting...)

		layout = QHBoxLayout()
		layout.setMargin(0)
				
		self._okPixmap = QApplication.instance().icon(':icons/server-ok').pixmap(16)
		self._warningPixmap = QApplication.instance().icon(':icons/server-warning').pixmap(16)
		self._errorPixmap = QApplication.instance().icon(':icons/server-error').pixmap(16)
		self._undefinedPixmap = QApplication.instance().icon(':icons/server-undefined').pixmap(16)

		self._state = None

		self._statusLabel = QLabel(self)
		self._statusLabel.setPixmap(self._undefinedPixmap)
		layout.addWidget(self._statusLabel)
		self.setLayout(layout)

		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		
		self.connect(QApplication.instance(), SIGNAL('testermanXcConnected()'), self.onConnected)
		self.connect(QApplication.instance(), SIGNAL('testermanXcDisconnected()'), self.onDisconnected)
		self.connect(QApplication.instance(), SIGNAL('testermanServerUpdated(QUrl)'), self.onServerUpdated)
		self.connect(QApplication.instance(), SIGNAL('testermanWsUnavailable()'), self.onServerError)
		
		self.synchronizeOnServerStatus()
	
	def onServerUpdated(self, url):
		self._statusLabel.setToolTip("Current server: %s" % url.toString())
	
	def onConnected(self):
		self._statusLabel.setPixmap(self._okPixmap)
		self._state = 'ok'

	def onDisconnected(self):
		if self._state in [ 'ok' ]:
			self._state = 'warning'
			self._statusLabel.setPixmap(self._warningPixmap)

	def onServerError(self):
		self._state = 'error'
		self._statusLabel.setPixmap(self._errorPixmap)
		
	def synchronizeOnServerStatus(self):
		if QApplication.instance().isXcConnected():
			self.onConnected()
		else:
			self.onDisconnected()
		self.onServerUpdated(QApplication.instance().serverUrl())

	def contextMenuEvent(self, event):
		"""
		Displays a fast server switching menu.
		"""
		menu = QMenu(self)
		fastSwitchMenu = menu.addMenu("Switch to server")
	
		currentUrl = QApplication.instance().serverUrl()
		# Current known servers
		settings = QSettings()
		urllist = settings.value('connection/urllist', QVariant(QStringList(QString('http://localhost:8080')))).toStringList()
		for stringUrl in urllist:
			url = QUrl(stringUrl)
			if url != currentUrl:
				fastSwitchMenu.addAction(stringUrl, lambda url=url: QApplication.instance().setServerUrl(url))

		# View resynchronizations (normally automatic once reconnected)
		menu.addAction("Resynchronize", lambda: QApplication.instance().setServerUrl(currentUrl, force = True))
		menu.popup(event.globalPos())


################################################################################
# About Dialog
################################################################################

class WAboutDialog(QDialog):
	"""
	Simple about dialog with a graphical banner.
	"""
	def __init__(self, parent): # the parent is the main window
		QDialog.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("About %s" % getClientName())
		self.setWindowIcon(icon(':icons/testerman-icon'))

		licenseText = "This software is licensed under the General Public License 2.0"
		authorsText = """Maintainer:
Sebastien Lefevre <seb.lefevre@gmail.com>

Based on a major contribution by
Comverse - Converged IP Commmunications"""
		thanksText = """Qt Software
		
Riverbank Computing

eServGlobal

Anevia
"""

		layout = QVBoxLayout()
		layout.setMargin(0)

		# A Splash image
		splash = QLabel()
		pixmap = QPixmap(":images/splash-banner.png")#.scaled(QSize(500, 300), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
		splash.setPixmap(pixmap)
		layout.addWidget(splash)

		# Product/version
		label = QLabel()
		label.setText("<b>%s %s</b><br />A Qt client for Testerman" % (getClientName(), getClientVersion()))
		label.setAlignment(Qt.AlignCenter)
		layout.addWidget(label)
		
		# Tab with the usual license/authors/thanks
		tab = QTabWidget()
		licenseTextEdit = QTextEdit()
		licenseTextEdit.setPlainText(licenseText)
		licenseTextEdit.setReadOnly(True)
		tab.addTab(licenseTextEdit, "License")
		authorsTextEdit = QTextEdit()
		authorsTextEdit.setPlainText(authorsText)
		authorsTextEdit.setReadOnly(True)
		tab.addTab(authorsTextEdit, "Authors")
		thanksTextEdit = QTextEdit()
		thanksTextEdit.setPlainText(thanksText)
		thanksTextEdit.setReadOnly(True)
		tab.addTab(thanksTextEdit, "Thanks to")
		layout.addWidget(tab)

		# Buttons
		buttonLayout = QHBoxLayout()
		self.okButton = QPushButton("Close", self)
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addStretch()
		buttonLayout.addWidget(self.okButton)
		buttonLayout.setMargin(4)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)


################################################################################
# Connection Dialog
################################################################################

class WConnectionDialog(QDialog):
	"""
	Displayed on startup: banner + prompt to enter a server url + login
	"""
	def __init__(self, parent): # the parent is the main window
		QDialog.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("Testerman login")
		self.setWindowIcon(icon(':icons/testerman-icon'))
		self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
		
		layout = QVBoxLayout()
		layout.setMargin(0)

		# A Banner
		splash = QLabel()
		pixmap = QPixmap(":images/splash-banner.png")#.scaled(QSize(500, 300), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
		splash.setPixmap(pixmap)
		layout.addWidget(splash)
		self.setMaximumWidth(pixmap.width())

		# WConnectionSetting part
		self.connectionSettings = Preferences.WConnectionSettings()
		layout.addWidget(self.connectionSettings)
		
		# Buttons
		buttonLayout = QHBoxLayout()
		self.okButton = QPushButton("Login", self)
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		self.cancelButton = QPushButton("Cancel", self)
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addStretch()
		buttonLayout.addWidget(self.okButton)
		buttonLayout.addWidget(self.cancelButton)
		buttonLayout.setMargin(4)

		layout.addLayout(buttonLayout)
		self.setLayout(layout)

	def accept(self):
		"""
		QDialog reimplementation.
		"""
		if self.connectionSettings.validate():
			self.connectionSettings.updateModel()
			QDialog.accept(self)


################################################################################
# Main Status Bar
################################################################################

class WMainStatusBar(QStatusBar):
	"""
	The status bar contains several sections:
	- the default one, for information messages
	- the current file location (url)
	- the current cursor position (line col)
	- the server status indicator (with fast server switching support)
	"""
	def __init__(self, parent = None):
		QStatusBar.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self._fileLocation = QLabel(self)
		self._fileLocation.setMargin(2)
		self.addPermanentWidget(self._fileLocation)
		self._lineColLabel = QLabel(self)
		self._lineColLabel.setMargin(2)
		self.addPermanentWidget(self._lineColLabel)
		self._serverStatusIndicator = WServerStatusIndicator(self)
		self.addPermanentWidget(self._serverStatusIndicator)

	def setLineCol(self, line, col):
		self._lineColLabel.setText("Line: %d Col: %d" % (line, col))

	def setFileLocation(self, url):
		if url:
			self._fileLocation.setText(url.toString())
		else:
			self._fileLocation.setText('')


################################################################################
# Main window, with docks support
################################################################################

class WMainWindow(QMainWindow):
	"""
	Main Window class.
	"""
	
	# The standard view
	PERSPECTIVE_DEFAULT = "default"
	# A view where the central widget is maximized
	PERSPECTIVE_MAXIMIZED = "maximized"
	# More to come - maybe
	
	def __init__(self, parent = None):
		QMainWindow.__init__(self, parent)
		QApplication.instance().set('gui.mainwindow', self)
		
		self._firstShow = True

		QApplication.instance().notifyInitializationProgress("Initializing widgets...")
		self.__createWidgets()
		QApplication.instance().notifyInitializationProgress("Initializing actions...")
		self.createActions()
		QApplication.instance().notifyInitializationProgress("Initializing toolbars...")
		self.createToolBars()
		QApplication.instance().notifyInitializationProgress("Initializing menus...")
		self.createMenus()
		QApplication.instance().notifyInitializationProgress("Restoring user settings...")
		self.readSettings()

		# List of QString
		self.previousUrlsToRetry = []
		
		self._perspectives = {}
		self._currentPerspective = self.PERSPECTIVE_DEFAULT
		self._initialPerspective = self._currentPerspective

		QApplication.instance().notifyInitializationProgress("Ready")

	def showEvent(self, event):
		"""
		Reimplemlented from QWidget/QMainWindow.
		"""
		QMainWindow.showEvent(self, event)
		
		if self._firstShow:
			self._firstShow = False
			# Refresh browsers
			self.repositoryBrowserDock.refresh()

			# Re-open files
			if not self.reopenLastUrls():
				# No file re-opened, create a default document (ATS)
				self.documentManager.newAts()

			self.saveOpenUrls()
			self.connect(self.documentManager, SIGNAL("documentUrlsUpdated()"), self.saveOpenUrls)

			# Then MOTD
			self.showMessageOfTheDay()
			

	def focusInEvent(self, event):
		"""
		TODO: makes this work. Currently such an event does not seem to be sent to a MainWindow.

		Virtual protected override: whenever the window gets a focus back, we check if a the current file has not been updated.
		"""
		log("focusInEvent, reason %d" % event.reason())
		if event.reason() == Qt.ActiveWindowFocusReason:
			self.documentManager.checkForCurrentDocumentUpdates()
		return QMainWindow.focusInEvent(self, event)

	def saveOpenUrls(self):
		"""
		Saves the currently open URLs into the application settings.
		Also includes URLs that were not successfully reopened
		this time but that we should try to reopen on next startup.
		"""
		urlList = QStringList()
		for url in self.previousUrlsToRetry:
			urlList.append(url)
		for url in self.documentManager.getOpenUrls():
			if not url in urlList:
				urlList.append(url)

		settings = QSettings()
		settings.setValue('mru/urllist', QVariant(urlList))

	def reopenLastUrls(self):
		"""
		Get the last open Urls from the application settings, and try to open them.
		In case of an error, propose to keep trying to reopen it on next startup, or not.
		"""
		somethingReopened = False
		# Read the settings
		settings = QSettings()
		reopenOnStartup = settings.value('mru/reopenOnStartup', QVariant(True)).toBool()
		if not reopenOnStartup:
			return False
		urlList = settings.value('mru/urllist', QVariant(QStringList())).toStringList()
		for url in urlList:
			url = QUrl(url)
			log("reopening %s" % url.toString())
			if not self.documentManager.openUrl(url):
				if QMessageBox.question(self, getClientName(),
					"Unable to open %s, the file may have been deleted, moved, or is not available on this server. Do you want to keep trying to open it on next startup ?" % unicode(url.toString()),
					QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
					self.previousUrlsToRetry.append(url.toString())
			else:
				somethingReopened = True
		return somethingReopened

	def __createWidgets(self):
		# Registered dock widgets
		self._docks = []
		try:
			# Log window
			self._logWindow = Logger.WLogger(self)
			self._logWindow.setWindowFlags(Qt.Window)

			# The central things
			QApplication.instance().notifyInitializationProgress("Initializing main window...")
			self.setWindowTitle(getClientName() + ' ' + getClientVersion())
			self.setWindowIcon(icon(':/icons/testerman-icon'))
			
			# Enable left side docks to maximize to full height
			# (useful for file browsers, etc)
			self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
			self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
			# But keep right side the 'normal' way, enabling expanding horizontal docks (top/bottom) instead
			# self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
			# self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
			self.setDockNestingEnabled(True)

			QApplication.instance().notifyInitializationProgress("Initializing document manager...")
			self.documentManager = DocumentManager.WDocumentManager(self)
			self.setCentralWidget(self.documentManager)
			QApplication.instance().set('gui.documentmanager', self.documentManager)

			# Acceptable docks
			QApplication.instance().notifyInitializationProgress("Initializing remote browsers...")
			self.repositoryBrowserDock = RemoteBrowsers.WRepositoryBrowsingDock(self)
			self.repositoryBrowserDock.setObjectName("repositoryBrowserDock")
			self.addDockWidget(Qt.LeftDockWidgetArea, self.repositoryBrowserDock)
			self._docks.append(self.repositoryBrowserDock)

#			QApplication.instance().notifyInitializationProgress("Initializing script properties editor...")
#			self.documentPropertyEditorDock = DocumentPropertyEditor.WScriptPropertiesEditorDock(self.documentManager.tab, self)
#			self.documentPropertyEditorDock.setObjectName("scriptPropertyEditorDock") # this scriptPropertyEditorDock name is kept for settings compatibility
#			self.addDockWidget(Qt.LeftDockWidgetArea, self.documentPropertyEditorDock)
#			self._docks.append(self.documentPropertyEditorDock)

			QApplication.instance().notifyInitializationProgress("Initializing job manager...")
			self.jobManagerDock = JobManager.WJobManagerDock(self)
			self.jobManagerDock.setObjectName("jobManagerDock")
			self.addDockWidget(Qt.RightDockWidgetArea, self.jobManagerDock)
			self._docks.append(self.jobManagerDock)

			QApplication.instance().notifyInitializationProgress("Initializing probe manager...")
			self.probeManagerDock = ProbeManager.WProbeManagerDock(self)
			self.probeManagerDock.setObjectName("probeManagerDock")
			self.addDockWidget(Qt.RightDockWidgetArea, self.probeManagerDock)
			self._docks.append(self.probeManagerDock)

			QApplication.instance().notifyInitializationProgress("Initializing outline view...")
			self.outlineViewDock = OutlineView.WOutlineViewDock(self.documentManager.tab, self)
			self.outlineViewDock.setObjectName("outlineViewDock")
			self.addDockWidget(Qt.RightDockWidgetArea, self.outlineViewDock)
			self._docks.append(self.outlineViewDock)
			QApplication.instance().set("gui.outlineview", self.outlineViewDock.getOutlineView())

			QApplication.instance().notifyInitializationProgress("Initializing chat component...")
			self.chatViewDock = ChatView.WChatViewDock(self)
			self.chatViewDock.setObjectName("chatViewDock")
			self.addDockWidget(Qt.LeftDockWidgetArea, self.chatViewDock)
			self._docks.append(self.chatViewDock)

			# Status bar
			self.statusBar = WMainStatusBar()
			self.setStatusBar(self.statusBar)
			QApplication.instance().set("gui.statusbar", self.statusBar)
			self.statusBar.showMessage("Welcome to Testerman.", 5000)

		except Exception, e:
			log("Warning: unable to create a widget: %s" % str(e))
			import TestermanNodes
			log(TestermanNodes.getBacktrace())
			sys.exit(1)

	def createActions(self):
		"""
		Create all the application actions
		"""
		# File/General actions
		self.newAction = TestermanAction(self, "&New ATS", self.documentManager.newAts, "Create a new ATS", "Ctrl+N")
		self.newAction.setIcon(icon(':/icons/file-new.png'))
		self.newCampaignAction = TestermanAction(self, "New &campaign", self.documentManager.newCampaign, "Create a new campaign")
		self.newCampaignAction.setIcon(icon(':/icons/campaign-new.png'))
		self.newModuleAction = TestermanAction(self, "New &module", self.documentManager.newModule, "Create a new module")
		self.newModuleAction.setIcon(icon(':/icons/module-new.png'))
		self.openAction = TestermanAction(self, "&Open...", self.open, "Open an existing document", "Ctrl+O")
		self.openAction.setIcon(icon(':/icons/file-open.png'))
		self.reloadAction = TestermanAction(self, "&Reload", self.reload, "Reload the current document", "F5")
		self.saveAction = TestermanAction(self, "&Save", self.save, "Save the current document to its current location", "Ctrl+S")
		self.saveAction.setIcon(icon(':/icons/file-save.png'))
		self.saveAsAction = TestermanAction(self, "Save &as...", self.saveAs, "Save the current document as on the local computer", "Ctrl+Shift+S")
		self.saveAsAction.setIcon(icon(':/icons/file-save-as.png'))
		self.closeAction = TestermanAction(self, "&Close", self.close, "Close the current tab", "Ctrl+W")
		self.closeAction.setIcon(icon(':/icons/file-close.png'))
		self.quitAction = TestermanAction(self, "&Quit", self.quit, "Quit", "Ctrl+Q")
		self.quitAction.setIcon(icon(':/icons/exit.png'))
		self.saveToRepositoryAsAction = TestermanAction(self, "&Save to repository as...", self.saveToRepositoryAs, "Save the current document to the Testerman repository as", "Ctrl+Shift+R")
		self.saveToRepositoryAsAction.setIcon(icon(':/icons/save-to-repository.png'))
		self.saveLocalCopyAsAction = TestermanAction(self, "Save a &local copy...", self.saveLocalCopyAs, "Save a copy of the current document on the local computer")
		self.saveLocalCopyAsAction.setIcon(icon(':/icons/file-save-copy.png'))
		self.openLogAction = TestermanAction(self, "Open &log file...", self.openLog, "Open a log file in the log analyzer")
#		self.openLogAction.setIcon(icon(':/icons/file-open.png'))

		# Edit
		self.replaceAction = TestermanAction(self, "Searc&h/Replace", self.replace, "Search and/or replace text in the document", "Ctrl+R")

		# Windows
		self.toggleProcessWindowAction = self.jobManagerDock.toggleViewAction()
		self.toggleProcessWindowAction.setShortcut("Ctrl+Shift+P")
		self.toggleProcessWindowAction.setToolTip("Show/hide job manager")
		self.toggleProcessWindowAction.setIcon(icon(':/icons/job-manager.png'))
		self.toggleRepositoryWindowAction = self.repositoryBrowserDock.toggleViewAction()
		self.toggleRepositoryWindowAction.setShortcut("Ctrl+Shift+B")
		self.toggleRepositoryWindowAction.setIcon(icon(':/icons/browser'))
		self.toggleRepositoryWindowAction.setToolTip("Show/hide Testerman repository browser")
#		self.toggleDocumentPropertyWindowAction = self.documentPropertyEditorDock.toggleViewAction()
#		self.toggleDocumentPropertyWindowAction.setShortcut("Ctrl+Shift+K")
#		self.toggleDocumentPropertyWindowAction.setIcon(icon(':/icons/list.png'))
#		self.toggleDocumentPropertyWindowAction.setToolTip("Show/hide document property editor")
		self.toggleProbeManagerWindowAction = self.probeManagerDock.toggleViewAction()
		self.toggleProbeManagerWindowAction.setShortcut("Ctrl+Shift+M")
		self.toggleProbeManagerWindowAction.setIcon(icon(':/icons/probe-manager.png'))
		self.toggleProbeManagerWindowAction.setToolTip("Show/hide probe manager")
		self.toggleOutlineWindowAction = self.outlineViewDock.toggleViewAction()
		self.toggleOutlineWindowAction.setShortcut("Ctrl+Shift+O")
		self.toggleOutlineWindowAction.setIcon(icon(':/icons/outline-view'))
		self.toggleOutlineWindowAction.setToolTip("Show/hide outline")
		self.toggleChatWindowAction = self.chatViewDock.toggleViewAction()
		self.toggleChatWindowAction.setShortcut("Ctrl+Shift+C")
		self.toggleChatWindowAction.setIcon(icon(':/icons/chat-room'))
		self.toggleChatWindowAction.setToolTip("Show/hide chat room")

		self.toggleFullScreenAction = TestermanAction(self, "&Toggle Full Screen mode", self.toggleFullScreen, "Toggle Full Screen mode")
		self.toggleFullScreenAction.setShortcut("Ctrl+Shift+F")

		# Configuration
		self.preferencesAction = TestermanAction(self, "&Preferences...", self.preferences, "Configure your client preferences")
		self.preferencesAction.setIcon(icon(':/icons/configure.png'))

		# Help/About
		self.aboutAction = TestermanAction(self, "&About...", self.about, "About this Testerman Client")
		self.releasesNoteAction = TestermanAction(self, "Release &Notes...", self.releaseNotes, "Display " + getClientName() + " release notes")
		self.aboutQtAction = TestermanAction(self, "About &Qt...", self.aboutQt, "About Qt")

		# MOTD
		self.motdAction = TestermanAction(self, "&Message of the day...", self.messageOfTheDay, "Message of the Day (from Testerman server)")

		# Logs
		self.showLogsAction = TestermanAction(self, "&Logs...", self.showLogs, "Display QTesterman log window")

	def createToolBars(self):
		self.mainToolBar = self.addToolBar("Main toolbar")
		self.mainToolBar.setObjectName("Main toolbar")
		self.mainToolBar.addAction(self.newAction)
		self.mainToolBar.addAction(self.newCampaignAction)
		self.mainToolBar.addAction(self.openAction)
		self.mainToolBar.addAction(self.saveToRepositoryAsAction)
		self.mainToolBar.addAction(self.closeAction)

		self.toggleMainToolbarAction = self.mainToolBar.toggleViewAction()

		self.windowToolBar = self.addToolBar("Window toolbar")
		self.windowToolBar.setObjectName("Window toolbar")
		self.windowToolBar.addAction(self.toggleProcessWindowAction)
		self.windowToolBar.addAction(self.toggleRepositoryWindowAction)
#		self.windowToolBar.addAction(self.toggleDocumentPropertyWindowAction)
		self.windowToolBar.addAction(self.toggleProbeManagerWindowAction)
		self.windowToolBar.addAction(self.toggleOutlineWindowAction)
		self.windowToolBar.addAction(self.toggleChatWindowAction)

		self.toggleWindowToolBarAction = self.windowToolBar.toggleViewAction()

	def createMenus(self):
		self.fileMenu = self.menuBar().addMenu("&File")
		self.fileMenu.addAction(self.newAction)
		self.fileMenu.addAction(self.newCampaignAction)
		self.fileMenu.addAction(self.newModuleAction)
		self.fileMenu.addAction(self.openAction)
		self.fileMenu.addAction(self.openLogAction)
		self.fileMenu.addAction(self.saveAction)
		self.fileMenu.addAction(self.saveAsAction)
		self.fileMenu.addAction(self.saveLocalCopyAsAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.saveToRepositoryAsAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.reloadAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.closeAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.quitAction)

		self.editMenu = self.menuBar().addMenu("&Edit")
		self.editMenu.addAction(self.replaceAction)

		self.windowsMenu = self.menuBar().addMenu("&Windows")
		self.windowsMenu.addAction(self.toggleProcessWindowAction)
		self.windowsMenu.addAction(self.toggleRepositoryWindowAction)
#		self.windowsMenu.addAction(self.toggleDocumentPropertyWindowAction)
		self.windowsMenu.addAction(self.toggleProbeManagerWindowAction)
		self.windowsMenu.addAction(self.toggleOutlineWindowAction)
		self.windowsMenu.addAction(self.toggleChatWindowAction)
		self.windowsMenu.addSeparator()
		self.windowsMenu.addAction(self.toggleMainToolbarAction)
		self.windowsMenu.addAction(self.toggleWindowToolBarAction)
		self.windowsMenu.addSeparator()
		self.windowsMenu.addAction(self.toggleFullScreenAction)

		self.pluginsMenu = self.menuBar().addMenu("&Plugins")
		self.connect(self.pluginsMenu, SIGNAL("aboutToShow()"), self.preparePluginsMenu)

		self.toolsMenu = self.menuBar().addMenu("&Tools")
		self.toolsMenu.addAction(self.preferencesAction)
		self.toolsMenu.addSeparator()
		self.toolsMenu.addAction(self.motdAction)
		self.toolsMenu.addSeparator()
		self.toolsMenu.addAction(self.showLogsAction)

		self.helpMenu = self.menuBar().addMenu("&Help")
		self.helpMenu.addAction(self.releasesNoteAction)
		self.helpMenu.addSeparator()
		self.helpMenu.addAction(self.aboutAction)
		self.helpMenu.addAction(self.aboutQtAction)

	def toggleFullScreen(self):
		if self.isFullScreen():
			self.showNormal()
		else:
			self.showFullScreen()

	def preparePluginsMenu(self):
		"""
		Fills the plugins menu with:
		- main plugins
		- current-document dependent plugins
		"""
		self.pluginsMenu.clear()

		# The document-related plugins
		# We extract them from the current document view
		documentView = self.documentManager.getCurrentDocumentView()
		if documentView:
			for (label, actions) in documentView.getCategorizedPluginActions():
				menu = self.pluginsMenu.addMenu(label)
				for action in actions:
					menu.addAction(action)

	def open(self):
		"""
		Open a Open File dialog, etc.
		"""
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getOpenFileName(self, "Choose a file", directory, "All supported types (*.ats *.campaign *.py);;ATS (*.ats);;Campaign (*.campaign);;Module (*.py)")
		if not filename.isEmpty():
			directory = os.path.dirname(unicode(filename))
			settings.setValue('lastVisitedDirectory', QVariant(directory))
			self.documentManager.openUrl(QUrl.fromLocalFile(filename))

	def openLog(self):
		"""
		Open a Open File dialog, etc.
		"""
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getOpenFileName(self, "Choose a file", directory, "Log file (*.xml *.log);;All (*)")
		if not filename.isEmpty():
			directory = os.path.dirname(unicode(filename))
			settings.setValue('lastVisitedDirectory', QVariant(directory))
			logAnalyzer = LogViewer.WLogViewer(parent = self)
			logAnalyzer.openUrl(QUrl.fromLocalFile(filename))
			logAnalyzer.show()

	def quit(self):
		"""
		Some confirmation before actually quitting.
		"""
		if QApplication.instance().client():
			QApplication.instance().client().stopXc()
		QApplication.instance().closeAllWindows()

	def closeEvent(self, event):
		for i in range(self.documentManager.tab.count()):
			if QTabWidget.widget(self.documentManager.tab, i).model.isModified():
				ret = QMessageBox.warning(self, getClientName(), "Do you want to save the changes you made to %s ?" % QTabWidget.widget(self.documentManager.tab, i).model.getShortName(), QMessageBox.Yes,  QMessageBox.No,  QMessageBox.Cancel)
				if ret == QMessageBox.Yes:
					if not QTabWidget.widget(self.documentManager.tab, i).save():
						event.ignore()
						return
				elif ret == QMessageBox.Cancel:
					event.ignore()
					return

		# For now, back to the standard/default perspective to save it
		self.setCurrentPerspective(self.PERSPECTIVE_DEFAULT)

		self.writeSettings()
		QApplication.instance().client().finalize()
		event.accept()

	def readSettings(self):
		settings = QSettings()
		settings.beginGroup('mainwindow')
		self.resize(settings.value('size', QVariant(self.size())).toSize())
		self.move(settings.value('pos', QVariant(self.pos())).toPoint())
		self.restoreState(settings.value('state', QVariant(QByteArray())).toByteArray(), 1)
		settings.endGroup()
	
	def writeSettings(self):
		settings = QSettings()
		settings.beginGroup('mainwindow')
		settings.setValue('size', QVariant(self.size()))
		settings.setValue('pos',  QVariant(self.pos()))
		settings.setValue('state', QVariant(self.saveState(1)))
		settings.endGroup()
	
	##
	# "Perspectives" management (experimental)
	##
	def setCurrentPerspective(self, name):
		"""
		Switches the current perspective to the one named "name".
		"""
		log("Switching perspectives: from %s to %s" % (self._currentPerspective, name))
		# Save the current perspective
		self._perspectives[self._currentPerspective] = self.saveState(1)
		perspective = self._perspectives.get(name, None)
		if perspective:
			self.restoreState(perspective, 1)
		else:
			log("The target perspective %s is new - nothing to restore" % name)
		self._currentPerspective = name

	def getCurrentPerspective(self):
		return self._currentPerspective
	
	def toggleMaximizeCentralWidget(self):
		"""
		Convenience function.
		"""
		if self.getCurrentPerspective() == self.PERSPECTIVE_MAXIMIZED:
			# Restore to the standard perspective
			self.setCurrentPerspective(self._initialPerspective)
			self._initialPerspective = None
		else:
			# Switch to the maximized "perspective"
			self._initialPerspective = self.getCurrentPerspective()
			self.setCurrentPerspective(self.PERSPECTIVE_MAXIMIZED)
			for dock in self._docks:
				dock.hide()

	def save(self):
		self.documentManager.saveCurrent()

	def reload(self):
		self.documentManager.reloadCurrent()

	def replace(self):
		self.documentManager.replaceCurrent()

	def saveAs(self):
		self.documentManager.saveCurrentAs()

	def saveLocalCopyAs(self):
		self.documentManager.saveCurrentLocalCopyAs()

	def close(self):
		self.documentManager.closeCurrent()
	
	def about(self):
		about = WAboutDialog(self)
		about.exec_()

	def aboutQt(self):
		QMessageBox.aboutQt(self)

	def preferences(self):
		preferences = Preferences.WPreferencesDialog(self)
		if preferences.exec_() == QDialog.Accepted:
			self.emit(SIGNAL('editorColorsUpdated()'))

	def saveToRepositoryAs(self):
		self.documentManager.saveCurrentToRepositoryAs()

	def releaseNotes(self):
		rn = ''
		try:
			f = open(QApplication.instance().get('qtestermanpath') + '/releasenotes.txt')
			rn = f.read()
			f.close()
		except Exception, e:
			log("Unable to read release notes: " + str(e))
		dialog = WTextEditDialog(rn, getClientName() + " release notes", 1, self)
		dialog.exec_()

	def messageOfTheDay(self):
		self.showMessageOfTheDay(force = True)

	def showMessageOfTheDay(self, force = False):
		"""
		Get the MOTD from the server, and display it conditionaly:
		- if force = True, show it, and does not propose not to see it again.
		- if force = False, show it only if it was not acknoledged before, and
		  propose to ack it.
		"""
		motd = "/MOTD"
		try:
			content = QApplication.instance().client().getFile(motd)
			info = QApplication.instance().client().getFileInfo(motd)
		except:
			content = None
			info = None
		
		if (content is None) or not info:
			if force:
				userInformation(self, "No Message of the Day is available on this server.")
			return

		if force:
			# Display the file without condition
			dialog = WMessageOfTheDayDialog(content, displayCheckBox = False, parent = self)
			dialog.exec_()
		else:
			settings = QSettings()
			ackedTimestamp = settings.value('motd/lastTimestamp', QVariant(0.0)).toDouble()[0]
			timestamp = info['timestamp']
			# Comparing apparently equal floats may cause some problems.
			# So we turn them into int first.
			if (int(timestamp*100) > int(ackedTimestamp*100)):
				# Display the file with an ack box
				dialog = WMessageOfTheDayDialog(content, displayCheckBox = True, parent = self)
				if (dialog.exec_() == QDialog.Accepted) and dialog.getChecked():
					settings.setValue('motd/lastTimestamp', QVariant(timestamp))

	def showLogs(self):
		"""
		Displays the log window
		"""
		self._logWindow.show()
		self._logWindow.raise_()


################################################################################
# The runners
################################################################################

def usage(txt = None):
	if txt: print txt
	print "Usage: " + sys.argv[0] + " [options]"
	print """General options are:
-v, --version         display version info and exit
-h, --help            display this help and exit
    --debug           debug mode

Full Testerman client mode:
-s ADDRESS            use ADDRESS as source IP address to subscribe on Xc
                      interface (real-time notifications)
    --force-update    propose to update to the current (stable) server's version

Standalone log analyzer mode:
-l, --log FILENAME    start the log analyzer on FILENAME, not the full client
    --online          still connect to a server to retrieve included log files
    --export-with PLUGIN
                      do not show the log analyzer window, but directly
                      export the log with the exporter plugin type PLUGIN
    --export-parameters PARAMETERS
                      use PARAMETERS as export parameters. The format is
                      key=value[,key=value]*, where the possible keys and
                      values depend on the selected PLUGIN type
"""

def showVersion():
	print "This is %s %s" % (getClientName(), getClientVersion())

def runClient():
	"""
	Runs the full client.
	"""

	# OK, now we can create some Qt objects.
	app = QApplication.instance()
	# These names enables the use of QSettings() without any additional parameters.
	app.setOrganizationName("Testerman")
	app.setApplicationName(getClientName())

	settings = QSettings()
	style = settings.value('style', QVariant(QString('Cleanlooks'))).toString()
	app.setStyle(style)

	try:
		import PyQt4.Qsci
	except ImportError:
		if sys.platform == 'win32':
			# A message for linux/unix clients
			# Under windows, we suggest installing Python 2.5 + the latest pyQt binary package, containing QScintilla as well.
			msg = """Sorry, you need QScintilla2 for Python to run this client.
You may install Python 2.5+ for Windows (http://www.python.org) as well as the latest PyQt binary package for Windows (http://www.riverbankcomputing.co.uk/software/pyqt/download) to get it."""
		else:
			msg = """Sorry, you need QScintilla2 for Python to run this client.
Please install the appropriate package for your Linux/Unix distribution or download it from http://www.riverbankcomputing.co.uk/software/qscintilla/download"""

		dialog = QMessageBox(QMessageBox.Critical, getClientName(), msg, QMessageBox.Ok)
		dialog.exec_()
		return 1

	# Display a connection dialog.
	connectionDialog = WConnectionDialog(None)

	# We continue only if accepted
	if connectionDialog.exec_() != QDialog.Accepted:
		sys.exit(0)

	QApplication.instance().showSplashScreen()

	# The next step is the autoUpdate
	QApplication.instance().notifyInitializationProgress("Checking updates...")
	acceptUnstableUpdates = settings.value('autoupdate/acceptExperimentalUpdates', QVariant(False)).toBool()
	branches = [ 'stable' ]
	if acceptUnstableUpdates:
		branches.append('testing')
		branches.append('experimental')
	if AutoUpdate.checkAndUpdateComponent(proxy = QApplication.instance().client(), destinationPath = QApplication.instance().get('basepath'), component = "qtesterman", currentVersion = getClientVersion(), branches = branches):
		# Update done. Restart ?
		AutoUpdate.Restarter.restart()
	log("Updates checked.")

	QApplication.instance().notifyInitializationProgress("Loading plugins...")
	PluginManager.scanPlugins()

	# Initialize the main window
	mainWindow = WMainWindow()
	QApplication.instance().finishSplashScreen(mainWindow) # The splashscreen will automatically hide after the main window shows up

	log("Main Window created.")
	app.connect(app, SIGNAL("lastWindowClosed()"), mainWindow.quit)
	mainWindow.show()
	
	return app.exec_()

def runLogAnalyzer(logFilename, shouldConnect = False):
	"""
	Runs the log analyzer as a standalone application
	to analyze logFilename.
	
	@type  logFilename: unicode
	@param logFilename: the filename of the log file to open
	"""
	logFilename = os.path.normpath(os.path.realpath(logFilename))

	# OK, now we can create some Qt objects.
	app = QApplication.instance()
	# These names enables the use of QSettings() without any additional parameters.
	app.setOrganizationName("Testerman")
	app.setApplicationName(getClientName())

	settings = QSettings()
	style = settings.value('style', QVariant(QString('Cleanlooks'))).toString()
	app.setStyle(style)

	PluginManager.scanPlugins()
	
	# Optional login (to retrieve included files on the server)
	if shouldConnect:
		connectionDialog = WConnectionDialog(None)
		if connectionDialog.exec_() != QDialog.Accepted:
			sys.exit(0)
		# No Xc for log analysis
		QApplication.instance().client().stopXc()

	# Open a LogViewer
	logAnalyzer = LogViewer.WLogViewer(standalone = True)
	logAnalyzer.setTitle("Testerman Log Analyzer")
	logAnalyzer.openUrl(QUrl.fromLocalFile(logFilename))
	logAnalyzer.show()

	return app.exec_()

def exportLog(logFilename, pluginName, **pluginParameters):
	"""
	CLI only/no GUI.
	
	Loads a file and exports it through an instance of the exporter plugin
	named pluginName, using the pluginParameters.
	
	@type  logFilename: unicode
	@param logFilename: the filename of the log file to open
	"""
	logFilename = os.path.normpath(os.path.realpath(logFilename))

	# OK, now we can create some Qt objects.
	app = QApplication.instance()
	# These names enables the use of QSettings() without any additional parameters.
	app.setOrganizationName("Testerman")
	app.setApplicationName(getClientName())

	PluginManager.scanPlugins()
	
	# Make sure the plugin to use actually exists, create an instance.
	# ...
	plugin = None
	
	pclasses = PluginManager.getPluginClasses(pluginType = Plugin.TYPE_REPORT_EXPORTER)
	for pc in pclasses:
		if pc['label'] == pluginName:
			plugin = pc['class']()
			break
	if not plugin:
		log("Unable to find a report exporter plugin named '%s'" % pluginName)
		return 1
	
	# Inject the parameters
	for k, v in pluginParameters.items():
		plugin._setProperty(k, v)
	
	# Load the XML file and turns it into a LogModel object suitable for the plugin
	try:
		f = open(logFilename, 'r')
		xmlLog = f.read()
		f.close()
	except Exception, e:
		log("Unable to load log file: %s" % unicode(e))
		return 1
	
	logModel = LogViewer.LogModel()	

	xmlDoc = QtXml.QDomDocument()
	(res, errormessage, errorline, errorcol) = xmlDoc.setContent(xmlLog, 0)
	log("Logs parsed, DOM constructed")
	if res:
		root = xmlDoc.documentElement()
		element = root.firstChildElement()
		while not element.isNull():
			logModel.feedEvent(element)
			element = element.nextSiblingElement()
	else:
		log("Parsing error: " + str(errormessage) + 'at line ' + str(errorline) + ' col ' + str(errorcol))
		return 1

	log("Log model constructed, exporting using %s..." % pluginName)
	
	plugin._setModel(logModel)
	
	ret = plugin.export()
	if ret:
		log("Log file correctly exported.")
		return 0
	else:
		log("Unspecified error during export.")
		return 1


def run():
	"""
	Main function.
	"""
	AutoUpdate.Restarter.initialize()

	app = QTestermanApplication([])

	# Some basic initialization
	app.set('interface.ex.sourceip', '0.0.0.0')
	# qtestermanpath contains the path of the qtesterman package dir
	app.set('qtestermanpath', os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__))))
	# basepath contains the path to the qtesterman.py diversion and the TestermanClient.py; this is the base path for an update.
	app.set('basepath', os.path.normpath(os.path.realpath(app.get('qtestermanpath') + "/..")))

	logFilename = None
	exportPluginParameters = ""
	exportPluginName = None
	shouldConnect = False

	# Let's parse the command line.
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvs:l:", ["help", "version", "log=", "debug", "force-update", "online", "export-with=", "export-parameters="])
	except Exception, e:
		usage(str(e))
		sys.exit(2)

	for opt, arg in opts:
		if opt in ['-h', '--help']:
			usage()
			sys.exit(0)
		if opt in ['-v', '--version']:
			showVersion()
			sys.exit(0)
		if opt in ['-s']:
			app.set('interface.ex.sourceip', arg)
		if opt in ['-l', '--log']:
			logFilename = arg
		if opt in ['--export-with']:
			exportPluginName = arg
		if opt in ['--export-parameters']:
			exportPluginParameters = arg
		if opt in ['--force-update']:
			app.set('autoupdate.force', 1)
		if opt in ['--online']:
			shouldConnect = True
		if opt in ['--debug']:
			import gc
			gc.set_debug(gc.DEBUG_STATS)
#			gc.set_debug(gc.DEBUG_LEAK)
			print "Current GC settings: " + str(gc.get_threshold())
			gc.set_threshold(10, 1, 1)
			print "Current GC state: " + str(gc.isenabled())

	# Export mode
	if logFilename and exportPluginName:
		parameters = {}
		for p in exportPluginParameters.split(','):
			try:
				key, val = p.split('=', 2)
				parameters[key] = val
			except:
				pass
		return exportLog(logFilename, exportPluginName, **parameters)

	# Log analyzer only mode
	if logFilename:
		return runLogAnalyzer(logFilename, shouldConnect)

	# Full client mode
	else:
		log("Starting %s %s..." % (getClientName(), getClientVersion()))
		return runClient()



if __name__ == "__main__":
	run()
