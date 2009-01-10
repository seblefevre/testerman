##
# -*- coding: utf-8 -*-
#
# Main Window/Widget
#
# $Id: Main.py,v 1.31 2008/07/10 16:05:52 slefevr Exp $
##

from PyQt4.Qt import *

import sys
import os
import os.path
import getopt

import TestermanClient

from Base import *
from Settings import *
from CommonWidgets import *

import AutoUpdate
import ProbeManager
import Logger
import JobManager
import EventMonitor
import RemoteBrowsers
import DocumentPropertyEditor
import PluginManager


# Editors contains a reference to QScintilla.
# We'll let the main application code display an error
# dialog if the import fails.
try:
	import Editors
except Exception, e:
	log(str(e))
	pass

################################################################################
# Specialized QApplication
################################################################################

class TestermanClientApplication(QApplication):
	"""
	TestermanClient application: a QApplication with;
	- some minor addons:
	 - application-wide variable managements (get/set)
	 - icon proxy
	- a method to get and set a Testerman URL.
	
	emits:
	testermanServerUpdated(QString url)
	"""
	def __init__(self, args):
		QApplication.__init__(self, args)

		# Application variables
		self.__vars = {}
		# Icon cache
		self.__iconsCache = {}
		# The embedded testerman client
		self.__testermanClient = None

	def icon(self, resource):
		"""
		Gets a new icon. Retrieved from cache if the resource does not exist yet.

		@type  resource: string/unicode
		@param resource: the resource identifier ("resource:/....ico", etc)

		@rtype: QIcon
		@returns: the QIcon corresponding to the resource.
		"""
		if not self.__iconsCache.has_key(resource):
			self.__iconsCache[resource] = QIcon(resource)
		return self.__iconsCache[resource]

	def get(self, key, default = None):
		if self.__vars.has_key(key):
			return self.__vars[key]
		else:
			return default

	def set(self, key, val):
		self.__vars[key] = val

	def getProxy(self):
		return self.__testermanClient

	def setTestermanServer(self, url):
		"""
		Sets the testerman server, prepares the proxy.

		Returns True if the server has been updated. False otherwise.
		"""
		log("Setting Server to %s" % str(url))
		if not url.startswith('http://'):
			log("Invalid Testerman Server URL %s (must start with http://)" % url)
			return False

		self.set('ws.url', url)

		if self.__testermanClient:
			self.__testermanClient.stopXc()
			self.__testermanClient = None

		self.__testermanClient = TestermanClient.Client("qtesterman", "QTesterman/" + getClientVersion(), serverUrl = url)
		self.__testermanClient.startXc()
		
		# Let's emit our signal
		self.emit(SIGNAL('testermanServerUpdated(QString)'), QString(url))

		return True

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
		self.setWindowTitle("About " + getClientName())
		self.setWindowIcon(icon(':icons/testerman.png'))

		text = """QTesterman %s

This software is licensed under the General Public License 2.0.

Maintainer:
Sebastien Lefevre <seb.lefevre@gmail.com>

Contributors:
Comverse - Converged IP Commmunications

Thanks to Trolltech and Riverbank Computing""" % (getClientVersion())

		layout = QVBoxLayout()
		layout.setMargin(0)

		# A Splash image
		splash = QLabel()
		pixmap = QPixmap(":images/splash-banner.png")#.scaled(QSize(500, 300), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
		splash.setPixmap(pixmap)
		layout.addWidget(splash)

		# The label
		label = QLabel()
		label.setText(text)
		label.setAlignment(Qt.AlignCenter)

		layout.addWidget(label)

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
	Popup on startup: splash screen + connection to Testerman server
	"""
	def __init__(self, parent): # the parent is the main window
		QDialog.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("Testerman login")
		self.setWindowIcon(icon(':icons/testerman.png'))
		
		layout = QVBoxLayout()
		layout.setMargin(0)

		# A Splash image
		splash = QLabel()
		pixmap = QPixmap(":images/splash-banner.png")#.scaled(QSize(500, 300), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
		splash.setPixmap(pixmap)
		layout.addWidget(splash)

		# WConnectionSetting part
		self.connectionSettings = WConnectionSettings(self)
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
		if self.connectionSettings.checkModel():
			self.connectionSettings.updateModel()
			QDialog.accept(self)

################################################################################
# Main window, with docks support
################################################################################

class WMainStatusBar(QStatusBar):
	def __init__(self, parent = None):
		QStatusBar.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.fileLocation = QLabel(self)
		self.fileLocation.setMargin(4)
		self.addPermanentWidget(self.fileLocation)
		self.lineColLabel = QLabel(self)
		self.lineColLabel.setMargin(2)
		self.addPermanentWidget(self.lineColLabel)

	def setLineCol(self, line, col):
		self.lineColLabel.setText("line %d col %d" % (line, col))

	def setFileLocation(self, url):
		if url:
			self.fileLocation.setText(url.toString())
		else:
			self.fileLocation.setText('(never saved yet)')


class WMainWindow(QMainWindow):
	"""
	Main Window class.
	During the creation, emit a signal nextInitializationStep(QString& label)
	so that we can add a progress bar.
	"""
	def __init__(self, parent = None):
		QMainWindow.__init__(self, parent)
		QApplication.instance().set('gui.mainwindow', self)

		self.connect(self, SIGNAL("nextInitializationStep(QString&)"), QApplication.instance().get('gui.splash').showMessage)

		self.emit(SIGNAL("nextInitializationStep(QString&)"), "Initializing widgets...")
		self.__createWidgets()
		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing actions..."))
		self.createActions()
		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing toolbars..."))
		self.createToolBars()
		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing menus..."))
		self.createMenus()
		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Retrieving configuration settings..."))
		self.readSettings()

		# List of QString
		self.previousUrlsToRetry = []

		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Ready"))

	def onShow(self):
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
		Save into the application settings the currently open URLs.
		Also includes URLs that were not successfully reopenend this time but that we should try to reopen on next startup.
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
		# The central things
		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing main window..."))
		self.setWindowTitle(getClientName() + ' ' + getClientVersion())
		self.setWindowIcon(icon(':/icons/testerman.png'))

		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing document manager..."))
		self.documentManager = Editors.WDocumentManager(self)
		self.setCentralWidget(self.documentManager)

		# Acceptable docks
#		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing event monitoring manager..."))
#		self.eventMonitorDock = EventMonitor.WEventMonitorDock(self)
#		self.eventMonitorDock.setObjectName("eventMonitorDock")
#		self.addDockWidget(Qt.BottomDockWidgetArea, self.eventMonitorDock)

		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing remote browsers..."))
		self.repositoryBrowserDock = RemoteBrowsers.WRepositoryBrowsingDock(self)
		self.repositoryBrowserDock.setObjectName("repositoryBrowserDock")
		self.addDockWidget(Qt.LeftDockWidgetArea, self.repositoryBrowserDock)

		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing property editor..."))
		self.documentPropertyEditorDock = DocumentPropertyEditor.WDocumentPropertyEditorDock(self.documentManager.tab, self)
		self.documentPropertyEditorDock.setObjectName("scriptPropertyEditorDock") # this scriptPropertyEditorDock name is kept for settings compatibility
		self.addDockWidget(Qt.LeftDockWidgetArea, self.documentPropertyEditorDock)

		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing job manager..."))
		self.jobManagerDock = JobManager.WJobManagerDock(self)
		self.jobManagerDock.setObjectName("jobManagerDock")
		self.addDockWidget(Qt.RightDockWidgetArea, self.jobManagerDock)

		self.emit(SIGNAL("nextInitializationStep(QString&)"), QString("Initializing probe manager..."))
		self.probeManagerDock = ProbeManager.WProbeManagerDock(self)
		self.probeManagerDock.setObjectName("probeManagerDock")
		self.addDockWidget(Qt.RightDockWidgetArea, self.probeManagerDock)

		# Status bar
		self.statusBar = WMainStatusBar()
		self.setStatusBar(self.statusBar)
		QApplication.instance().set("gui.statusbar", self.statusBar)
		self.statusBar.showMessage("Welcome to Testerman.", 5000)

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
		self.saveAction = TestermanAction(self, "&Save", self.save, "Save the current document", "Ctrl+S")
		self.saveAction.setIcon(icon(':/icons/file-save.png'))
		self.saveAsAction = TestermanAction(self, "Save &as...", self.saveAs, "Save the current document as", "Ctrl+Shift+S")
		self.saveAsAction.setIcon(icon(':/icons/file-save-as.png'))
		self.closeAction = TestermanAction(self, "&Close", self.close, "Close the current tab", "Ctrl+W")
		self.closeAction.setIcon(icon(':/icons/file-close.png'))
		self.quitAction = TestermanAction(self, "&Quit", self.quit, "Quit", "Ctrl+Q")
		self.quitAction.setIcon(icon(':/icons/exit.png'))
		self.saveToRepositoryAsAction = TestermanAction(self, "&Save to repository as...", self.saveToRepositoryAs, "Save the current document to the Testerman repository as", "Ctrl+Shift+R")
		self.saveToRepositoryAsAction.setIcon(icon(':/icons/save-to-repository.png'))

		# Edit
		self.replaceAction = TestermanAction(self, "Searc&h/Replace", self.replace, "Search and/or replace text in the document", "Ctrl+R")

		# Windows
		self.toggleProcessWindowAction = self.jobManagerDock.toggleViewAction()
		self.toggleProcessWindowAction.setShortcut("Ctrl+Shift+P")
		self.toggleProcessWindowAction.setToolTip("Show/hide job manager")
		self.toggleProcessWindowAction.setIcon(icon(':/icons/job-manager.png'))
		self.toggleRepositoryWindowAction = self.repositoryBrowserDock.toggleViewAction()
		self.toggleRepositoryWindowAction.setShortcut("Ctrl+Shift+B")
		self.toggleRepositoryWindowAction.setIcon(icon(':/icons/browser.png'))
		self.toggleRepositoryWindowAction.setToolTip("Show/hide Testerman repository browser")
		self.toggleDocumentPropertyWindowAction = self.documentPropertyEditorDock.toggleViewAction()
		self.toggleDocumentPropertyWindowAction.setShortcut("Ctrl+Shift+K")
		self.toggleDocumentPropertyWindowAction.setIcon(icon(':/icons/list.png'))
		self.toggleDocumentPropertyWindowAction.setToolTip("Show/hide document property editor")
		self.toggleProbeManagerWindowAction = self.probeManagerDock.toggleViewAction()
		self.toggleProbeManagerWindowAction.setShortcut("Ctrl+Shift+M")
		self.toggleProbeManagerWindowAction.setIcon(icon(':/icons/probe-manager.png'))
		self.toggleProbeManagerWindowAction.setToolTip("Show/hide probe manager")

		self.toggleFullScreenAction = TestermanAction(self, "&Toggle Full Screen mode", self.toggleFullScreen, "Toggle Full Screen mode")
		self.toggleFullScreenAction.setShortcut("Ctrl+Shift+F")

		# Configuration
		self.settingsAction = TestermanAction(self, "&Settings...", self.settings, "Configure your client settings")
		self.settingsAction.setIcon(icon(':/icons/configure.png'))

		# Help/About
		self.aboutAction = TestermanAction(self, "&About...", self.about, "About this Testerman Client")
		self.releasesNoteAction = TestermanAction(self, "Release &Notes...", self.releaseNotes, "Display " + getClientName() + " release notes")
		self.aboutQtAction = TestermanAction(self, "About &Qt...", self.aboutQt, "About Qt")

		# MOTD
		self.motdAction = TestermanAction(self, "MOTD...", self.messageOfTheDay, "Message of the Day (from Testerman server)")

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
		self.windowToolBar.addAction(self.toggleDocumentPropertyWindowAction)
		self.windowToolBar.addAction(self.toggleProbeManagerWindowAction)

		self.toggleWindowToolBarAction = self.windowToolBar.toggleViewAction()

	def createMenus(self):
		self.fileMenu = self.menuBar().addMenu("&File")
		self.fileMenu.addAction(self.newAction)
		self.fileMenu.addAction(self.newCampaignAction)
		self.fileMenu.addAction(self.newModuleAction)
		self.fileMenu.addAction(self.openAction)
		self.fileMenu.addAction(self.reloadAction)
		self.fileMenu.addAction(self.saveAction)
		self.fileMenu.addAction(self.saveAsAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.saveToRepositoryAsAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.closeAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.quitAction)

		self.editMenu = self.menuBar().addMenu("&Edit")
		self.editMenu.addAction(self.replaceAction)

		self.windowsMenu = self.menuBar().addMenu("&Windows")
		self.windowsMenu.addAction(self.toggleProcessWindowAction)
		self.windowsMenu.addAction(self.toggleRepositoryWindowAction)
		self.windowsMenu.addAction(self.toggleDocumentPropertyWindowAction)
		self.windowsMenu.addAction(self.toggleProbeManagerWindowAction)
		self.windowsMenu.addSeparator()
		self.windowsMenu.addAction(self.toggleMainToolbarAction)
		self.windowsMenu.addAction(self.toggleWindowToolBarAction)
		self.windowsMenu.addSeparator()
		self.windowsMenu.addAction(self.toggleFullScreenAction)

		self.pluginsMenu = self.menuBar().addMenu("&Plugins")
		self.editorPluginsMenu = QMenu("Editor plugins")
		self.connect(self.editorPluginsMenu, SIGNAL("aboutToShow()"), self.prepareEditorPluginsMenu)
		self.pluginsMenu.addMenu(self.editorPluginsMenu)

		self.toolsMenu = self.menuBar().addMenu("&Tools")
		self.toolsMenu.addAction(self.settingsAction)
		self.toolsMenu.addSeparator()
		self.toolsMenu.addAction(self.motdAction)

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

	def prepareEditorPluginsMenu(self):
		"""
		Fills the editor plugins menu with possible plugins according to the current document.
		"""
		self.editorPluginsMenu.clear()
		documentView = self.documentManager.getCurrentDocumentView()
		if documentView:
			for action in documentView.getEditorPluginActions():
				self.editorPluginsMenu.addAction(action)

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
			self.documentManager.openUrl(QUrl('file://%s' % filename))

	def quit(self):
		"""
		Some confirmation before actually quitting.
		"""
		if QApplication.instance().getProxy():
			QApplication.instance().getProxy().stopXc()
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
		self.writeSettings()
		getProxy().finalize()
		event.accept()

	def readSettings(self):
		settings = QSettings()
		settings.beginGroup('mainwindow')
		self.resize(settings.value('size', QVariant(self.size())).toSize())
		self.move(settings.value('pos', QVariant(self.pos())).toPoint())
		self.restoreState(settings.value('state', QVariant(QByteArray())).toByteArray(), 0)
		settings.endGroup()
	
	def writeSettings(self):
		settings = QSettings()
		settings.beginGroup('mainwindow')
		settings.setValue('size', QVariant(self.size()))
		settings.setValue('pos',  QVariant(self.pos()))
		settings.setValue('state', QVariant(self.saveState(0)))
		settings.endGroup()

	def save(self):
		self.documentManager.saveCurrent()

	def reload(self):
		self.documentManager.reloadCurrent()

	def replace(self):
		self.documentManager.replaceCurrent()

	def saveAs(self):
		self.documentManager.saveCurrentAs()

	def close(self):
		self.documentManager.closeCurrent()
	
	def about(self):
		about = WAboutDialog(self)
		about.exec_()

	def aboutQt(self):
		QMessageBox.aboutQt(self)

	def settings(self):
		settings = WSettingsDialog(self)
		settings.exec_()

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
		motd = "/components/MOTD"
		content = getProxy().getFile(motd)
		if not content:
			return
		info = getProxy().getFileInfo(motd)
		if not info:
			return

		if force:
			# Display the file
			dialog = WMessageOfTheDayDialog(content, displayCheckBox = False, parent = self)
			dialog.exec_()
		else:
			settings = QSettings()
			ackedTimestamp = settings.value('motd/lastTimestamp', QVariant(0.0)).toDouble()[0]
			timestamp = info['timestamp']
#			log("DEBUG: " + str(ackedTimestamp) + " / current: " + str(timestamp))
			if (timestamp > ackedTimestamp):
				# Display the file with an ack box
				dialog = WMessageOfTheDayDialog(content, displayCheckBox = True, parent = self)
				if (dialog.exec_() == QDialog.Accepted) and dialog.getChecked():
					settings.setValue('motd/lastTimestamp', QVariant(timestamp))


################################################################################
# The runner
################################################################################

def usage(txt = None):
	if txt: print txt
	print "Usage: " + sys.argv[0] + " [options]"
	print """General options are:
-v, --version         display version info and exit
-h, --help            display this help and exit
    --debug           debug mode

Full Testerman client mode:
-s <IP>               source IP address to use when subscribing to events
    --force-update    propose to update to the current (stable) server's version

Standalone log analyzer mode:
-l, --log <filename>  run the log analyzer only, offline mode, on <filename>
"""

def showVersion():
	print "This is %s %s" % (getClientName(), getClientVersion())

def runClient():
	"""
	Called when run in real client mode.
	"""

	# OK, now we can create some Qt objects.
	app = QApplication.instance()
	# These names enables the use of QSettings() without any additional parameters.
	app.setOrganizationName("Testerman")
	app.setApplicationName(getClientName())

	settings = QSettings()
	style = settings.value('style', QVariant(QString('Cleanlooks'))).toString()
	app.setStyle(style)

	acceptUnstableUpdates = settings.value('autoupdate/acceptExperimentalUpdates', QVariant(False)).toBool()

	try:
		import PyQt4.Qsci
	except ImportError:
		if sys.platform == 'win32':
			# A message for linux/unix clients
			# Under windows, we suggest installing Python 2.5 + the latest pyQt binary package, containing QScintilla as well.
			msg = """Sorry, you need QScintilla2 for Python to run this client.
You may install Python 2.5 for Windows (http://www.python.org) as well as the latest PyQt binary package for Windows (http://www.riverbankcomputing.co.uk/pyqt/) to get it."""
		else:
			msg = """Sorry, you need QScintilla2 for Python to run this client.
Please install the appropriate package for your Linux/Unix distribution or download it from http://www.riverbankcomputing.co.uk/qscintilla/"""

		dialog = QMessageBox(QMessageBox.Critical, getClientName(), msg, QMessageBox.Ok)
		dialog.exec_()
		return 1

	# Display a connection dialog.
	connectionDialog = WConnectionDialog(None)

	# We continue only if accepted
	if connectionDialog.exec_() != QDialog.Accepted:
		sys.exit(0)

	# A splashscreen to let the user wait for initialization...
	pixmap = QPixmap(":images/splash.png").scaled(QSize(500, 300), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
	splash = QSplashScreen(pixmap)
	splash.showMessage("Initializing...")
	splash.show()
	app.processEvents()
	QApplication.instance().set('gui.splash', splash)

	# The next step is the autoUpdate
	splash.showMessage("Checking updates...")
	branches = [ 'stable' ]
	if acceptUnstableUpdates:
		branches.append('testing')
		branches.append('experimental')
	if AutoUpdate.updateComponent(proxy = QApplication.instance().getProxy(), basepath = QApplication.instance().get('basepath'), component = "qtesterman", currentVersion = getClientVersion(), branches = branches):
		# Update done. Restart ?
		# TODO: implement a real application restart
		QMessageBox.information(None, "Restart", "You must now restart QTesterman")
		sys.exit(1)
	log("Updates checked.")

	splash.showMessage("Loading plugins...")
	PluginManager.scanPlugins()

	# Finally, run the main window
	mainWindow = WMainWindow()
	splash.finish(mainWindow) # The splashscreen will automatically hide after the main window is shown

	log("Main Window created.")
	app.connect(app, SIGNAL("lastWindowClosed()"), mainWindow.quit)
	mainWindow.show()

	mainWindow.onShow()

	return app.exec_()

def runLogAnalyzer(logFilename):
	"""
	Called when run in log Analyzer mode
	"""
	import LogViewer
	
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

	# Now, we just open a WLogViewer with the read filename.
	# However, some tabs must be disabled (buginet) and the QTesterman tab settings must not be followed.

	logAnalyzer = LogViewer.WLogViewer(standalone = True)
	logAnalyzer.setTitle("Testerman Log Analyzer")
	logAnalyzer.openUrl(QUrl("file://" + logFilename))
	logAnalyzer.show()

	return app.exec_()

def run():

	app = TestermanClientApplication([])

	# Some basic initialization
	app.set('interface.ex.sourceip', '0.0.0.0')
	# qtestermanpath contains the path of the qtesterman package dir
	app.set('qtestermanpath', os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__))))
	# basepath contains the path to the qtesterman.py diversion and the TestermanClient.py; this is the base path for an update.
	app.set('basepath', os.path.normpath(os.path.realpath(app.get('qtestermanpath') + "/..")))
	# Default documentation cache root
	app.set('documentationcache', os.path.normpath(unicode(QDir.homePath()) + "/.testerman/"))

	logFilename = None

	# Let's parse the command line.
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvs:l:", ["help", "version", "log=", "debug", "force-update"])
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
		if opt in ['--force-update']:
			app.set('autoupdate.force', 1)
		if opt in ['--debug']:
			import gc
			gc.set_debug(gc.DEBUG_STATS)
#			gc.set_debug(gc.DEBUG_LEAK)
			print "Current GC settings: " + str(gc.get_threshold())
			gc.set_threshold(10, 1, 1)
			print "Current GC state: " + str(gc.isenabled())


	if logFilename:
		return runLogAnalyzer(logFilename)
	else:
		log("Starting %s %s..." % (getClientName(), getClientVersion()))
		return runClient()



if __name__ == "__main__":
	run()
