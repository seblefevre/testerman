##
# -*- coding: utf-8 -*-
#
# Editors for ATS, Campaign, Modules.
#
# $Id$
##

import PyQt4.Qsci as sci

from PyQt4.Qt import *

import compiler
import copy
import os.path
import parser
import re
import time

from Base import *
from DocumentModels import *
from CommonWidgets import *
import CommonWidgets

import LogViewer
import DocumentationManager
import PluginManager
import Plugin
import TemplateManager

##
# A WDocumentManager is a notebook that opens WDocument objects.
# A WDocument is either a WModuleDocument, WAtsDocument, or a WCampaignDocument.
#
##



###############################################################################
# Common stuff
###############################################################################

class WRepositoryCollision(QDialog):
	"""
	When putting a file into the repository, in case of collision:
	new path, or overwrite.
	"""
	def __init__(self, path, parent):
		QDialog.__init__(self, parent)
		self.path = path
		self.__createWidgets()

	def __createWidgets(self):
		layout = QVBoxLayout()
		self.setWindowTitle("Existing file")
		layout.addWidget(QLabel("A file with this name already exists\nin repository. Please enter a new one:"))
		self.lineEdit = QLineEdit(self.path, self)
		layout.addWidget(self.lineEdit)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.okButton = QPushButton("Ok")
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		self.overwriteButton = QPushButton("Overwrite")
		self.connect(self.overwriteButton, SIGNAL("clicked()"), self.overwrite)
		self.cancelButton = QPushButton("Cancel")
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self.okButton)
		buttonLayout.addWidget(self.overwriteButton)
		buttonLayout.addWidget(self.cancelButton)
		
		layout.addLayout(buttonLayout)
		self.setLayout(layout)

	def overwrite(self):
		# In case of an overwrite, the initial path id is the one to use.
		self.lineEdit.setText(self.path)
		self.done(2)

	def getFilename(self):
		return self.lineEdit.text()

	def accept(self):
		if self.lineEdit.text().length() == 0:
			userError(self, 'Sorry, you must enter a non-empty name')
			# we reinit it to the previous path
			self.lineEdit.setText(self.path)
		else:
			QDialog.accept(self)


###############################################################################
# WDocument: main widget to handle a document model.
# Inherited by W{Ats,Campaign,Module}Document
###############################################################################

class WDocument(QWidget):
	"""
	Enable to edit and manipulate the script (execute as, associate an id, etc)
	Base class for WAtsDocument and WCampaignDocument.

	This is a view over a DocumentModel (aspect: body)
	"""
	def __init__(self, model, parent = None):
		QWidget.__init__(self, parent)
		self.model = model
		self.tabWidget = None
		self.editor = None
		self.filenameTemplate = "Any file (*.*)"

	def getEditorPluginActions(self):
		# For now, we just have code writer plugins.
		ret = getCodeWriterPluginActions(self.editor, self.model.getDocumentType())
		return ret

	def setTabWidget(self, tabWidget):
		"""
		Enables this widget to be aware of the tab widget it is insered into, and its position.
		Note: normally it is its direct widget parent.
		"""
		self.tabWidget = tabWidget

	def updateModel(self):
		# Implemented in sub-classes only
		pass

	def goTo(self, line, col = 0):
		# implemented in sub-classes
		pass

	def _saveLocally(self, filename):
		"""
		@type  filename: QString
		@param filename: the filename to use to save the current document (absolute path)
		
		@rtype: bool
		@returns: True if successfully saved, False otherwise
		"""
		self.updateModel()
		log(u"Saving locally to filename %s" % filename)
		try:
			f = open(unicode(filename), 'w')
			# Store files as utf8
			f.write(self.model.getDocument().encode('utf-8'))
			f.close()
			QApplication.instance().get('gui.statusbar').showMessage("Successfully saved as %s" % (filename))
			self.model.setSavedAttributes(url = QUrl('file://%s' % filename), timestamp = time.time())
			self.model.resetModificationFlag()
			QApplication.instance().get('gui.statusbar').setFileLocation(self.model.getUrl())
			return True
		except Exception, e:
			systemError(self, "Unable to save file as %s: %s" % (filename, str(e)))
			QApplication.instance().get('gui.statusbar').showMessage("Unable to save file as %s: %s" % (filename, str(e)))
			return False

	def _saveRemotely(self, filename):
		"""
		@type  filename: QString
		@param filename: the filename to use to save the current document (absolute path within the server's docroot)
		
		@rtype: bool
		@returns: True if successfully saved, False otherwise
		"""
		self.updateModel()

		# OK, now we can continue
		error = None
		try:
			# Store files as utf8
			ret = getProxy().putFile(self.model.getDocument().encode('utf-8'), unicode(filename))
			if not ret:
				error = "Please check permissions."
		except Exception, e:
			error =	str(e)

		if error is None:
			QApplication.instance().get('gui.statusbar').showMessage("File successfully put into repository as %s" % (filename))
			# We set the timestamp on the server, not the local timestamp since the client may not be in sync with the server's time.
			info = getProxy().getFileInfo(unicode(filename))
			serverIp, serverPort = getProxy().getServerAddress()
			self.model.setSavedAttributes(url = QUrl("testerman://%s:%d%s" % (serverIp, serverPort, filename)), timestamp = info['timestamp'])
			self.model.resetModificationFlag()
			QApplication.instance().get('gui.statusbar').setFileLocation(self.model.getUrl())
			return True
		else:
			systemError(self, "Unable to save file to repository: %s" % error)
			QApplication.instance().get('gui.statusbar').showMessage("Unable to put save file to repository: %s" % error)
			return False

	def save(self):
		"""
		This is a dispatcher.
		
		Saves the file using the current available location info:
		- open a local file browser if the file was never saved before,
		- resave using the current url if the file was already saved before (local or remote)
		
		@rtype: bool
		@returns: True if OK, False if the file was not saved.
		"""
		# Is it a resave ?
		if self.model.getUrl().scheme() != 'unsaved':
			if self.model.isRemote():
				# Resave to repository
				return self.saveToRepository()
			else:
				# Locally resave
				return self._saveLocally(self.model.getUrl().path())
		else:
			# Never saved for now.
			return self.saveAs()

	def saveAs(self):
		"""
		Opens a local browser to browse for a filename to save,
		then saves the file.

		@rtype: bool
		@returns: True if successufully saved, False otherwise
		"""
		# Open a browser
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getSaveFileName(self, "Save as...", directory, self.filenameTemplate)
		if filename.isEmpty():
			return False
		elif not filename.split('.')[-1] == self.model.getExtension():
			filename = "%s.%s" % (filename, self.model.getExtension())

		directory = os.path.dirname(unicode(filename))
		settings.setValue('lastVisitedDirectory', QVariant(directory))

		# Save the file
		return self._saveLocally(filename)

	def saveToRepositoryAs(self):
		"""
		Opens a sort of remote browser to browser for a filename to save on the server,
		(proposing file overwrite if needed)
		then saves the file.

		@rtype: bool
		@returns: True if successufully saved, False otherwise
		"""
		self.updateModel()

		# Get a new filename
		(filename, status) = QInputDialog.getText(self, "Save to repository as", "Enter a path (+ name) to save within the repository")
		# WARNING: the filename entered by the user does not starts with "repository".
		# Internally, we must add this prefix.
		if not status or filename.isEmpty():
			return False
		elif not filename.split('.')[-1] == self.model.getExtension():
			filename = "%s.%s" % (filename, self.model.getExtension())
		
		# Needs a real remote browser to select a file.
		fe = getProxy().fileExists("/repository/%s" % unicode(filename))
		# We negotiate a new filename in case of a collision.
		while fe:
			# We should display a little dialog box with possible actions
			# Typically cancel, overwrite, change name
			rc = WRepositoryCollision("/repository/%s" % filename, self)
			res = rc.exec_()
			if res == QDialog.Rejected:
				return False
			if res == 2: # overwrite
				break
			filename = rc.getFilename()
			fe = getProxy().fileExists("/repository/%s" % unicode(filename))

		# Now we can save the file
		return self._saveRemotely(QString("/repository/%s" % filename))

	def saveToRepository(self):
		"""
		Resaves to repository.
		Checks if, in the meanwhile, the file was not modified on the server.

		@rtype: bool
		@returns: True if successfully saved.
		"""
		filename = self.model.getUrl().path()

		# Check if there is no newer file on the server
		referenceTimestamp = 0
		info = getProxy().getFileInfo(unicode(filename))
		if info:
			referenceTimestamp = info['timestamp']
		if referenceTimestamp > self.model.getTimestamp():
#			# Actually, this is more than a warning popup. It proposes to force overwriting, or a little
#			# "diff" windows, or back to edition, ... something ?
			ret = QMessageBox.warning(self, "File updated", "The remote file was updated since your last checkout. Are you sure you want to want to overwrite these changes ?", 
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if ret != QMessageBox.Yes:
				return False

		# Now we can save the file
		return self._saveRemotely(filename)

	def onUrlUpdated(self):
		# FIXME: Wow... this code supposes that we can only receive a onUrlUpdated signal for the
		# *current* tab widget...
		if self.tabWidget:
			self.tabWidget.setTabText(self.tabWidget.currentIndex(), self.model.getShortName(), self.model.isModified())
			self.tabWidget.setTabToolTip(self.tabWidget.currentIndex(), self.model.getUrl() and self.model.getUrl().toString() or None)

	def onModelModificationChanged(self, change):
		"""
		Update the tab title (status indicator),
		tells the Editor widget that its document is marked as not modified.
		"""
		if not change:
			self.editor.setModified(0)
		self.onUrlUpdated()

	def replace(self):
		"""
		function to be overriden
		"""
		return

###############################################################################
# Module Edition
###############################################################################

class WModuleDocument(WDocument):
	"""
	Enable to edit and manipulate a module.

	This is a view over a ModuleModel (aspect: body)

	This should better be inherited from something common to WScript and WModuleDocument (especially for
	save/saveToRepository functions).
	"""
	def __init__(self, moduleModel, parent = None):
		WDocument.__init__(self, moduleModel, parent)

		self.__createWidgets()
		self.filenameTemplate = "Testerman Module (*.py)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelDocumentReplaced)

	def onModelDocumentReplaced(self):
		self.editor.setPlainText(self.model.getBody())

	def __createWidgets(self):
		"""
		A main WScriptEditor, plus an associated action bar at the bottom with:
		- an action button to test/run the script.
		- a button to check syntax
		"""

		layout = QVBoxLayout()
		self.editor = WPythonCodeEditor(self.model.getBody(), self)
		self.connect(self.editor, SIGNAL('modificationChanged(bool)'), self.model.onBodyModificationChanged)
# FFS: a secondary view on the same document
#		self.secondaryEditor = WPythonCodeEditor(scintillaDocument = self.editor.document(), parent = self)
#		splitter = QSplitter(Qt.Vertical)
#		splitter.addWidget(self.editor)
#		splitter.addWidget(self.secondaryEditor)
#		layout.addWidget(splitter)

		layout.addWidget(self.editor)

		# A find widget
		self.find = WSciFind(self.editor, self)

		# The action bar below
		actionLayout = QHBoxLayout()
		actionLayout.addWidget(self.find)

		actionLayout.addStretch()
		self.testButton = QPushButton("Check syntax")
		self.testButton.setIcon(icon(':/icons/check.png'))
		self.testButton.setIconSize(QSize(16, 16))
		self.connect(self.testButton, SIGNAL("clicked()"), self.verify)
		actionLayout.addWidget(self.testButton)
		self.docButton = QPushButton("Documentation")
		self.connect(self.docButton, SIGNAL("clicked()"), self.showDocumentation)
		actionLayout.addWidget(self.docButton)

		actionLayout.setMargin(2)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def updateModel(self):
		self.model.setBody(self.editor.getCode())

	def goTo(self, line, col = 0):
		self.editor.goTo(line, col)

	def replace(self):
		"""
		replace function
		"""
		replaceBox = WSciReplace(self.editor, self)
		replaceBox.show()

	def showDocumentation(self):
		if self.model.getUrl() is not None:
			self.updateModel()
			DocumentationManager.showContentDocumentation(content = self.model.getBody(), key = self.model.getUrl().toString(), parent = self)
		else:
			QMessageBox.warning(self, getClientName(), "Unable to generate documentation, the file must be saved", QMessageBox.Ok)

	def verify(self, displayNoError = 1):
		self.updateModel()
		self.editor.clearHighlight()
		try:
			body = self.model.getBody().encode('utf-8')
			parser.suite(body).compile()
			compiler.parse(body)
			if displayNoError:
				QMessageBox.information(self, getClientName(), "No syntax problem was found in this module.", QMessageBox.Ok)
			return 1
		except SyntaxError, e:
			self.editor.highlight(e.lineno - 1)
			self.editor.goTo(e.lineno - 1, e.offset)
			userError(self, "Syntax error on line %s: <br />%s" % (str(e.lineno), e.msg))
			self.editor.setFocus(Qt.OtherFocusReason)
		return 0


###############################################################################
# ATS Edition
###############################################################################

class WAtsDocument(WDocument):
	"""
	Enable to edit and manipulate the script (execute as, associate an id, etc).

	Derived view from WDocument
	"""
	def __init__(self, atsModel, parent = None):
		WDocument.__init__(self, atsModel, parent)
		self.__createWidgets()
		self.filenameTemplate = "Testerman ATS (*.ats)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelDocumentReplaced)

	def onModelDocumentReplaced(self):
		self.editor.setPlainText(self.model.getBody())

	def __createWidgets(self):
		"""
		A main WScriptEditor, plus an associated action bar at the bottom with:
		- an action button to test/run the script.
		- a button to check syntax
		"""

		layout = QVBoxLayout()

		# The code editor
		self.editor = WPythonCodeEditor(self.model.getBody(), self)
		# QsciScintilla directly manage the signal
		self.connect(self.editor, SIGNAL('modificationChanged(bool)'), self.model.onBodyModificationChanged)
		layout.addWidget(self.editor)

		# The action bar below
		actionLayout = QHBoxLayout()

		# A find widget
		self.find = WSciFind(self.editor, self)

		self.runMenu = QMenu('Run', self)
		self.runWithParametersAction = self.runMenu.addAction("With parameters...", self.runWithParam)
		self.scheduleRunAction = self.runMenu.addAction("Scheduled run...", self.scheduleRun)

		# By default, icon sizes are 24x24. We resize them to 16x16 to avoid to big buttons.
		self.testButton = QPushButton("Check syntax")
		self.testButton.setIcon(icon(':/icons/check.png'))
		self.testButton.setIconSize(QSize(16, 16))
		self.connect(self.testButton, SIGNAL("clicked()"), self.verify)
		# Instant run
		self.runButton = QPushButton("Run")
		self.runButton.setIcon(icon(':/icons/run.png'))
		self.runButton.setIconSize(QSize(16, 16))
		self.connect(self.runButton, SIGNAL("clicked()"), self.run)

		self.runOptionsButton = QPushButton("Special run")
		self.runOptionsButton.setIcon(icon(':/icons/run.png'))
		self.runOptionsButton.setIconSize(QSize(16, 16))
		self.runOptionsButton.setMenu(self.runMenu)

		self.launchLog = QCheckBox("Display runtime log")
		self.launchLog.setChecked(True)

		actionLayout.addWidget(self.find)
		actionLayout.addStretch()
		actionLayout.addWidget(self.testButton)
		actionLayout.addWidget(self.runOptionsButton)
		actionLayout.addWidget(self.runButton)
		actionLayout.addWidget(self.launchLog)
		actionLayout.setMargin(2)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def updateModel(self):
		self.model.setBody(self.editor.getCode())
		
	def goTo(self, line, col = 0):
		self.editor.goTo(line, col)

	def replace(self):
		"""
		replace function
		"""
		replaceBox = WSciReplace(self.editor, self)
		replaceBox.show()

	def verify(self, displayNoError = 1):
		self.updateModel()
		self.editor.clearHighlight()
		try:
			body = self.model.getBody().encode('utf-8')
			parser.suite(body).compile()
			compiler.parse(body)
			if displayNoError:
				QMessageBox.information(self, getClientName(), "No syntax problem was found in this ATS.", QMessageBox.Ok)
			return 1
		except SyntaxError, e:
			self.editor.highlight(e.lineno - 1)
			self.editor.goTo(e.lineno - 1, e.offset)
			userError(self, "Syntax error on line %s: <br />%s" % (str(e.lineno), e.msg))
			self.editor.setFocus(Qt.OtherFocusReason)
		return 0

	##
	# Run actions
	##
	def run(self):
		"""
		Immediate run, using the default parameters.
		"""
		# we 'commit' and verify the modified view of the script
		if not self.verify(0):
			return
		session = None # Use the default parameters
		res = getProxy().scheduleAts(self.model.getDocument(), unicode(self.model.getName()), unicode(QApplication.instance().username()), session, at = time.time() + 1.0)
		QApplication.instance().get('gui.statusbar').showMessage(res['message'])
		if self.launchLog.isChecked():
			logViewer = LogViewer.WLogViewer(parent = self)
			logViewer.openJob(res['job-id'])
			logViewer.show()

	def runWithParam(self):
		"""
		Runs the script after asking for specific session parameters.
		"""
		# we 'commit' and verify the modified view of the script
		if not self.verify(0):
			return

		session = None
		paramEditorDialog = WSessionParameterEditorDialog(self.model.getMetadataModel(), self)
		if paramEditorDialog.exec_() == QDialog.Accepted:
			session = paramEditorDialog.getSessionDict()
		else:
			QApplication.instance().get('gui.statusbar').showMessage('Operation cancelled')
			return

		res = getProxy().scheduleAts(self.model.getDocument(), unicode(self.model.getName()), unicode(QApplication.instance().username()), session, at = time.time() + 1.0)
		QApplication.instance().get('gui.statusbar').showMessage(res['message'])
		if self.launchLog.isChecked():
			logViewer = LogViewer.WLogViewer(parent = self)
			logViewer.openJob(res['job-id'])
			logViewer.show()
	
	def scheduleRun(self):
		"""
		Displays a dialog box to schedule a run.
		"""
		# we 'commit' and verify the modified view of the script
		if not self.verify(0):
			return

		session = None
		scheduledTime = None
		paramEditorDialog = WScheduleDialog(self.model.getMetadataModel(), self)
		if paramEditorDialog.exec_() == QDialog.Accepted:
			session = paramEditorDialog.getSessionDict()
			scheduledTime = paramEditorDialog.getScheduledTime()
		else:
			QApplication.instance().get('gui.statusbar').showMessage('Operation cancelled')
			return

		res = getProxy().scheduleAts(self.model.getDocument(), unicode(self.model.getName()), unicode(QApplication.instance().username()), session, scheduledTime)
		QApplication.instance().get('gui.statusbar').showMessage(res['message'])
		# Never shows the realtime log on scheduling.

###############################################################################
# Campaign Edition
###############################################################################

class WCampaignDocument(WDocument):
	"""
	Enable to edit and manipulate a Campaign.
	"""
	def __init__(self, model, parent = None):
		WDocument.__init__(self, model, parent)
		self.__createWidgets()
		self.filenameTemplate = "Testerman Campaign (*.campaign)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelDocumentReplaced)

	def onModelDocumentReplaced(self):
		self.editor.setPlainText(self.model.getBody())

	def __createWidgets(self):
		"""
		A main WScriptEditor, plus an associated action bar at the bottom with:
		- an action button to test/run the script.
		- a button to check syntax (well, not yet)
		"""
		layout = QVBoxLayout()
		# The code editor
		self.editor = WPythonCodeEditor(self.model.getBody(), self)
		# QsciScintilla directly manage the signal
		self.connect(self.editor, SIGNAL('modificationChanged(bool)'), self.model.onBodyModificationChanged)
		layout.addWidget(self.editor)

		# The action bar below
		actionLayout = QHBoxLayout()

		self.testButton = QPushButton("Check")
		self.testButton.setIcon(icon(':/icons/check.png'))
		self.testButton.setIconSize(QSize(16, 16))
		self.connect(self.testButton, SIGNAL("clicked()"), self.verify)
		self.runButton = QPushButton("Run")
		self.runButton.setIcon(icon(':/icons/run.png'))
		self.runButton.setIconSize(QSize(16, 16))
		self.connect(self.runButton, SIGNAL("clicked()"), self.run)
		self.runWithParamButton = QPushButton("Run with params")
		self.runWithParamButton.setIcon(icon(':/icons/run.png'))
		self.runWithParamButton.setIconSize(QSize(16, 16))
		self.connect(self.runWithParamButton, SIGNAL("clicked()"), self.runWithParam)

		actionLayout.addStretch()
#		actionLayout.addWidget(self.testButton)
		actionLayout.addWidget(self.runButton)
		actionLayout.addWidget(self.runWithParamButton)
	
		actionLayout.setMargin(2)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def updateModel(self):
		self.model.setBody(self.editor.getCode())

	def replace(self):
		"""
		replace function
		"""
		replaceBox = WSciReplace(self.editor, self)
		replaceBox.show()

	def verify(self):
		self.updateModel()
		QMessageBox.information(self, getClientName(), "This feature is not implemented yet.")

	def run(self):
		self.updateModel()
		session = None # Use the default parameters
		res = getProxy().scheduleCampaign(self.model.getDocument(), unicode(self.model.getName()), unicode(QApplication.instance().username()), session)
		QApplication.instance().get('gui.statusbar').showMessage(res['message'])
		QMessageBox.information(self, getClientName(), res['message'], QMessageBox.Ok)

	def runWithParam(self):
		# we 'commit' the modified view of the script
		self.updateModel()

		session = None

		paramEditorDialog = WSessionParameterEditorDialog(self.model.getMetadataModel(), self)
		if paramEditorDialog.exec_() == QDialog.Accepted:
			session = paramEditorDialog.getSessionDict()
		else:
			QApplication.instance().get('gui.statusbar').showMessage('Operation cancelled')
			return

		res = getProxy().scheduleCampaign(self.model.getDocument(), unicode(self.model.getName()), unicode(QApplication.instance().username()), session)
		QApplication.instance().get('gui.statusbar').showMessage(res['message'])
		QMessageBox.information(self, getClientName(), res['message'], QMessageBox.Ok)

###############################################################################
# Main Document Manager: a notebook widget opening/closing documents.
###############################################################################

class WDocumentManager(QWidget):
	"""
	This is a notebook managing multiple WDocument (Module, Campaign, Ats).
	Provides additional methods to open new scripts/modules from outside the widget.
	
	emit:
	documentUrlsUpdated() whenever a doc url was changed.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()
		QApplication.instance().set('gui.documentmanager', self)

	def __createWidgets(self):
		layout = QVBoxLayout()
		layout.setMargin(0)
		self.tab = WEnhancedTabWidget()
		layout.addWidget(self.tab)
		self.setLayout(layout)
		self.connect(self.tab, SIGNAL('currentChanged(int)'), self.onCurrentDocumentChanged)
		self.connect(self.tab, SIGNAL('closeCurrentTab()'), self.closeCurrent)

	def onCurrentDocumentChanged(self, index):
		self.checkForCurrentDocumentUpdates()
	
	def getOpenUrls(self):
		"""
		Return a list of open tab urls, used to save them for automatic reopening, for instance.
		Note: URLs are defined only when the file has a corresponding persistent storage (i.e. saved or loaded from the disk)
		"""
		urls = []
		for index in range(0, self.tab.count()):
			url = self.tab.widget(index).model.getUrl()
			if url and url.scheme() in [ 'file', 'testerman' ]:
				urls.append(url.toString())

#		log("DEBUG: " + str(urls))
		return urls

	def openUrl(self, url):
		"""
		Universal opener.
		Url is either:
		
		testerman://<server:port><absolute path> for a remote file on the current testerman server,
		file://<absolute path> for a local file

		@type  url: QUrl
		@param url: the URL to open
		Returns True if OK.
		"""
		log("Opening url: %s" % url.toString())
		path = url.path()
		fileTimestamp = None
		contents = None

		if url.scheme() == 'file':
			log("Opening local file: %s" % url.toString())
			try:
				f = open(unicode(path), 'r')
				contents = f.read()
				f.close()
				fileTimestamp = os.stat(unicode(path)).st_mtime
			except Exception, e:
				systemError(self, 'Unable to open %s: %s' % (unicode(path), str(e)))
				return False

		elif url.scheme() == 'testerman':
			log("Opening remote file: %s" % url.toString())
			try:
				contents = getProxy().getFile(unicode(path))
				info = getProxy().getFileInfo(unicode(path))
			except:
				contents = None
				info = None

			if (contents is None) or not info:
				log("Unable to open remote file due to a transport or Ws error")
				return False

			fileTimestamp = info['timestamp']

		else:
			log("Unknown URL scheme. Not opening.")
			return False

		# We store files as UTF-8. Decodes then to unicode.
		contents = contents.decode('utf-8')
		
		if path.endsWith('.campaign'):
			QApplication.instance().get('gui.documentmanager').openCampaignTab(contents, url, fileTimestamp = fileTimestamp)
		elif path.endsWith('.py'):
			QApplication.instance().get('gui.documentmanager').openModuleTab(contents, url, fileTimestamp = fileTimestamp)
		elif path.endsWith('.ats'):
			QApplication.instance().get('gui.documentmanager').openAtsTab(contents, url, fileTimestamp = fileTimestamp)
		else:
			log("Unable to open remote file: unknown file type")
			return False
		return True

	def getNewName(self, name):
		"""
		Get a the closest name possible to name, according to existing
		open tabs. Suffix it with a digit starting at 2 when needed.
		FIXME: implement this.
		"""
		return name

	def checkForCurrentDocumentUpdates(self):
		"""
		Check if the file has not been updated on the server/on disk, but only if no local modifications were done.
		"""
		model = self.tab.currentWidget().model
		newTimestamp = 0
		if (not model.isModified()):
			# Retrieve the new timestamp
			if model.isRemote():
				log("Checking for remote file updates...")
				info = getProxy().getFileInfo(unicode(model.getUrl().path()))
				if info:
					newTimestamp = info['timestamp']
			else:
				log("Checking for local file updates...")
				try:
					newTimestamp = os.stat(unicode(model.getUrl().path())).st_mtime
				except:
					pass

			# OK, file updated.
			if newTimestamp > model.getTimestamp():
				log("File updated. Asking for a possible reload.")
				# Note: the file was open, not modified, so we should reload it without asking maybe ?
				ret = QMessageBox.question(self, "File updated", "The file has been changed since you opened it. Do you want reload it ?",
					QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
				if ret == QMessageBox.Yes:
					# NB: the widget 'index' should always corresponds to the current widget.
					self.reloadCurrent(force = True)

	def getCurrentDocumentView(self):
		"""
		Returns the current WDocument, or None if no document is currently opened.
		"""
		return self.tab.currentWidget()

	def reloadCurrent(self, force = False):
		"""
		Ask for a confirmation, then reload current document in current tab.
		"""
		model = self.tab.currentWidget().model

		# If the model has never been saved, discard
		if model.getUrl() is None:
			return

		# If the model has been modified, ask for a confirmation
		if not force and model.isModified():
			ret = QMessageBox.warning(self, getClientName(), "Are you sure you want to reload this file and discard your changes?", QMessageBox.Yes,  QMessageBox.No)
			if ret != QMessageBox.Yes:
				return

		# OK, now we can reload it.
		if model.isRemote():
			log("Reloading remote file...")
			contents = getProxy().getFile(unicode(model.getUrl().path()))
			info = getProxy().getFileInfo(unicode(model.getUrl().path()))
			if contents and info:
				fileTimestamp = info['timestamp']
				model.setDocument(contents)
				model.setSavedAttributes(url = model.getUrl(), timestamp = fileTimestamp)
				model.resetModificationFlag()
				QApplication.instance().get('gui.statusbar').showMessage('Document reloaded.', 5000)
			else:
				systemError(self, "Unable to reload file from the repository: the file does not seem to exist anymore")
		else:
			log("Reloading local file...")
			try:
				f = open(unicode(model.getUrl().path()), 'r')
				contents = f.read().decode('utf-8')
				f.close()
				fileTimestamp = os.stat(unicode(model.getUrl().path())).st_mtime
				model.setDocument(contents)
				model.setSavedAttributes(url = model.getUrl(), timestamp = fileTimestamp)
				model.resetModificationFlag()
				QApplication.instance().get('gui.statusbar').showMessage('Document reloaded.', 5000)
			except Exception, e:
				systemError(self, 'Unable to open %s: %s' % (model.getUrl().toString(), unicode(e)))

	def newAts(self):
		"""
		Open a new tab with an empty (or templated ?) script.
		"""
		self.openAtsTab('# ATS Script for Testerman\n', QUrl('unsaved:///%s' % self.getNewName('new ats')))

	def newCampaign(self):
		"""
		Open a new tab with an empty (or templated ?) campaign script.
		"""
		self.openCampaignTab('# Campaign description file for Testerman\n', QUrl('unsaved:///%s' % self.getNewName('new campaign')))

	def newModule(self):
		"""
		Open a new tab with an empty (or templated ?) module.
		"""
		self.openModuleTab('# Module file for Testerman\n', QUrl('unsaved:///%s' % self.getNewName('new module')))

	def documentUrlsUpdated(self):
		"""
		Slot called whenever an URL of an open document was updated.
		We forward the signal once.
		"""
		self.emit(SIGNAL('documentUrlsUpdated()'))

	def openAtsTab(self, document, url, fileTimestamp = 0):
		documentModel = AtsModel(document, url, timestamp = fileTimestamp)
		wdocument = WAtsDocument(documentModel, self.tab)
		name = documentModel.getShortName()
		tabIndex = self.tab.addTab(wdocument, icon(':/icons/ats'), name)
		self.tab.setTabToolTip(tabIndex, documentModel.getUrl().toString())
		wdocument.setTabWidget(self.tab)
		#We should not do this but it doesn't work without for the first tab.
		self.tab.emit(SIGNAL('currentChanged(int)'), tabIndex)
		# Set the focus on this tab
		self.tab.setCurrentIndex(tabIndex)
		self.connect(documentModel, SIGNAL('urlUpdated()'), self.documentUrlsUpdated)
		self.documentUrlsUpdated()

	def openCampaignTab(self, document, url, fileTimestamp = 0):
		documentModel = CampaignModel(document, url, timestamp = fileTimestamp)
		wdocument = WCampaignDocument(documentModel, self.tab)
		name = documentModel.getShortName()
		tabIndex = self.tab.addTab(wdocument, icon(':/icons/campaign'), name)
		self.tab.setTabToolTip(tabIndex, documentModel.getUrl().toString())
		wdocument.setTabWidget(self.tab)
		# Set the focus on this tab
		self.tab.setCurrentIndex(tabIndex)
		self.connect(documentModel, SIGNAL('urlUpdated()'), self.documentUrlsUpdated)
		self.documentUrlsUpdated()

	def openModuleTab(self, document, url, fileTimestamp = 0):
		documentModel = ModuleModel(document, url, timestamp = fileTimestamp)
		wdocument = WModuleDocument(documentModel, self.tab)
		name = documentModel.getShortName()
		tabIndex = self.tab.addTab(wdocument, icon(':/icons/module'), name)
		self.tab.setTabToolTip(tabIndex, documentModel.getUrl().toString())
		wdocument.setTabWidget(self.tab)
		# Set the focus on this tab
		self.tab.setCurrentIndex(tabIndex)
		self.connect(documentModel, SIGNAL('urlUpdated()'), self.documentUrlsUpdated)
		self.documentUrlsUpdated()

	def saveCurrent(self):
		"""
		Retrieve the current tabbed WScript, and forward the save event
		If asFilename is None, save using the existing filename.
		"""
		self.tab.currentWidget().save()

	def replaceCurrent(self):
		"""
		Retrieve the current tabbed WScript, and forward the event
		"""
		self.tab.currentWidget().replace()

	def saveCurrentAs(self):
		"""
		Retrieve the current tabbed WScript, and forward the save event
		If asFilename is None, save using the existing filename.
		"""
		self.tab.currentWidget().saveAs()

	def closeCurrent(self):
		"""
		Close the current tab.
		Should verify that the file has not been changed...
		"""
		if self.tab.currentWidget().model.isModified():
			ret = QMessageBox.warning(self, getClientName(), "Do you want to save the changes you made to %s ?" % self.tab.currentWidget().model.getShortName(), QMessageBox.Yes,  QMessageBox.No, QMessageBox.Cancel)
			if ret == QMessageBox.Yes:
				if not self.tab.currentWidget().save():
					return
			elif ret == QMessageBox.Cancel:
				return
		self.tab.removeTab(self.tab.currentIndex())
		# Should we send this signal explicitely ? not done by the Qt widget ?
		if self.tab.currentIndex() >= 0:
			self.tab.emit(SIGNAL('currentChanged(int)'), self.tab.currentIndex())
		self.documentUrlsUpdated()

	def saveCurrentToRepositoryAs(self):
		self.tab.currentWidget().saveToRepositoryAs()		

################################################################################
# Code Writers plugins
################################################################################

class PluginAction(TestermanAction):
	def __init__(self, editor, label, pluginInstance):
		TestermanAction.__init__(self, editor, label, self.activatePlugin)
		self.editor = editor
		self.pluginInstance = pluginInstance

	def activatePlugin(self):
		ret = self.pluginInstance.activate()
		if ret:
			self.editor.insert(ret)

def getCodeWriterPluginActions(editor, documentType):
	"""
	Create a list containing valid plugin actions according to the editor type.

	codeType in module/ats/campaign (for now)
	"""
	print "DEBUG: getting code writer plugins for " + str(documentType)
	ret = []
	for p in PluginManager.getPluginClasses(Plugin.TYPE_CODE_WRITER):
		if p['activated'] and p['class']:
			# Verify plugin/codeType compliance
			plugin = p['class'](editor)
			if plugin.isDocumentTypeSupported(documentType):
				ret.append(PluginAction(editor, p['label'], plugin))
	return ret


################################################################################
# Python Editor: used for ATS and Module edition
################################################################################

class WPythonCodeEditor(sci.QsciScintilla):
	def __init__(self, text = None, parent = None, scintillaDocument = None):
		sci.QsciScintilla.__init__(self, parent)
		
		# Macro
		self.learntKeystrokes = sci.QsciMacro(self)
		self.learningKeystrokes = False

		# Lexer/Highlighter settings
		lexer = sci.QsciLexerPython(self)
		defaultFont = QFont("courier", 8)
		defaultFont.setFixedPitch(True)
		lexer.setDefaultFont(defaultFont)
		# The quotes font's pointSize is not impacted by the default font... lexer bug ?
		f = lexer.font(sci.QsciLexerPython.SingleQuotedString)
		f.setPointSize(8)
		lexer.setFont(f, sci.QsciLexerPython.Default)
		lexer.setFont(f, sci.QsciLexerPython.Comment)
		lexer.setFont(f, sci.QsciLexerPython.Number)
		lexer.setFont(f, sci.QsciLexerPython.DoubleQuotedString)
		lexer.setFont(f, sci.QsciLexerPython.SingleQuotedString)
		lexer.setFont(f, sci.QsciLexerPython.Keyword)
		lexer.setFont(f, sci.QsciLexerPython.TripleSingleQuotedString)
		lexer.setFont(f, sci.QsciLexerPython.TripleDoubleQuotedString)
		lexer.setFont(f, sci.QsciLexerPython.ClassName)
		lexer.setFont(f, sci.QsciLexerPython.FunctionMethodName)
		lexer.setFont(f, sci.QsciLexerPython.Operator)
		lexer.setFont(f, sci.QsciLexerPython.Identifier)
		lexer.setFont(f, sci.QsciLexerPython.CommentBlock)
		lexer.setFont(f, sci.QsciLexerPython.UnclosedString)
		lexer.setFont(f, sci.QsciLexerPython.HighlightedIdentifier)
		lexer.setFont(f, sci.QsciLexerPython.Decorator)

		f.setBold(True)
		lexer.setFont(f, sci.QsciLexerPython.Keyword)
		lexer.setFont(f, sci.QsciLexerPython.Number)

		# Colors
		lexer.setColor(Qt.darkGreen, sci.QsciLexerPython.DoubleQuotedString)
		lexer.setColor(Qt.darkGreen, sci.QsciLexerPython.SingleQuotedString)
		lexer.setColor(Qt.darkGreen, sci.QsciLexerPython.TripleSingleQuotedString)
		lexer.setColor(Qt.darkGreen, sci.QsciLexerPython.TripleDoubleQuotedString)
		lexer.setColor(Qt.red, sci.QsciLexerPython.Comment)
		lexer.setColor(Qt.red, sci.QsciLexerPython.CommentBlock)
		lexer.setColor(Qt.darkMagenta, sci.QsciLexerPython.Number)
		lexer.setColor(Qt.blue, sci.QsciLexerPython.FunctionMethodName)
		lexer.setColor(Qt.blue, sci.QsciLexerPython.ClassName)
		self.setBraceMatching(sci.QsciScintilla.SloppyBraceMatch)
		self.setMatchedBraceForegroundColor(Qt.red)
		self.setMatchedBraceBackgroundColor(Qt.white)
		self.setUnmatchedBraceBackgroundColor(Qt.red)
		self.setUnmatchedBraceForegroundColor(Qt.black)

		lexer.setIndentationWarning(sci.QsciLexerPython.Inconsistent)

		self.setLexer(lexer)

		self.setUtf8(True)
		self.setAutoIndent(True)
		self.setTabWidth(2)
		self.setIndentationsUseTabs(True)
#		self.setIndentationGuides(True)
		self.setEolMode(sci.QsciScintilla.EolUnix)
		self.setFolding(sci.QsciScintilla.BoxedTreeFoldStyle)
		self.setTabIndents(True)
		self.setMarginLineNumbers(1, True)
		self.setMarginWidth(1, "10")
		self.setMarginsBackgroundColor(Qt.white)
		self.setMarginsForegroundColor(Qt.gray)

		# Markers
		self.LINE_MARKER = self.markerDefine(self.Background)
		self.ERROR_MARKER = self.markerDefine(self.Background) # FFS
		self.BOOKMARK_MARKER = self.markerDefine(self.Background) # FFS
		self.setMarkerBackgroundColor(Qt.yellow, self.ERROR_MARKER)
		self.setMarkerBackgroundColor(Qt.yellow, self.LINE_MARKER)
		# No marker margin
		self.setMarginWidth(0, 0)

		self.lastHighlight = None

		self.connect(self, SIGNAL("linesChanged()"), self.onLinesChanged)
		self.connect(self, SIGNAL("textChanged()"), self.onTextChanged)
		
		if text:
			self.setText(text)
		if scintillaDocument:
			self.setDocument(scintillaDocument)

		# We have to set the initial text as "original" (not modified) otherwise
		# first changes won't be notified since, for the widget, the text will remain
		# 'modified'.
		self.setModified(0)

		self.connect(self, SIGNAL("cursorPositionChanged(int, int)"), self.onCursorPositionChanged)

		self.menu = self.createStandardContextMenu()
		self.createActions()

	def dragMoveEvent(self, e):
		"""
		Reimplemented to accept the event.
		Only call if a dragEnterEvent accepted the action.
		"""
		e.acceptProposedAction()

	def dropEvent(self, e):
		"""
		new item/mimedata dropped.
		"""
		#log("mouseEvent - dropEvent on editor")
		# CTRL pressed : see Qt.KeyboardModifiers
		# to do : if CTRL is pressed, open a windows asking the default value of parameter : get(param_name, default_value)
		mimeParameterType = "application/x-qtesterman-parameters"
		if e.mimeData().hasFormat(mimeParameterType):
			parameters = mimeDataToObjects(mimeParameterType, e.mimeData())
			self.insert(", ".join("get_variable('%s')" % x['name'] for x in parameters))
			e.acceptProposedAction()

	def dragEnterEvent(self, e):
		"""
		Reimplementation from QWidget. Drag and drop acceptation.
		"""
		#log("mouseEvent - dragEvent over editor !")
		mimeParameterType = "application/x-qtesterman-parameters"
		if e.mimeData().hasFormat(mimeParameterType):
			e.acceptProposedAction()
		else:
			return QTreeWidget.dragEnterEvent(self, e)
			
	def createStandardContextMenu(self):
		"""
		This function does not exist on a QSciScintilla widget, but on QTextEdit.
		It should contain: undo/redo, copy/cut/paste, which is not very interesting since shortcuts
		are all well known :-)
		"""
		menu = QMenu(self)
		return menu

	def createActions(self):
		""" Common actions """
		self.commentAction = TestermanAction(self, "Comment", self.comment)
		self.commentAction.setShortcut(Qt.ALT + Qt.Key_C)
		self.commentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.commentAction)
		self.uncommentAction = TestermanAction(self, "Uncomment", self.uncomment)
		self.uncommentAction.setShortcut(Qt.ALT + Qt.Key_X)
		self.uncommentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.uncommentAction)
		self.indentAction = TestermanAction(self, "Indent", self.indent)
		self.indentAction.setShortcut(Qt.Key_Tab)
		self.indentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.indentAction)
		self.unindentAction = TestermanAction(self, "Unindent", self.unindent)
		self.unindentAction.setShortcut(Qt.SHIFT + Qt.Key_Tab)
		self.unindentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.unindentAction)
		# nedit-inspired keystrokes learner (aka "anonymous macro")
		self.learnKeystrokesAction = TestermanAction(self, "Learn keystrokes", self.toggleLearnKeystrokes) 
		self.learnKeystrokesAction.setShortcut(Qt.ALT + Qt.Key_K)
		self.learnKeystrokesAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.learnKeystrokesAction)
		self.replayKeystrokesAction = TestermanAction(self, "Replay keystrokes", self.replayKeystrokes) 
		self.replayKeystrokesAction.setShortcut(Qt.CTRL + Qt.Key_K)
		self.replayKeystrokesAction.setShortcutContext(Qt.WidgetShortcut)
		self.replayKeystrokesAction.setEnabled(False)
		self.addAction(self.replayKeystrokesAction)

		self.menu.addAction(self.commentAction)
		self.menu.addAction(self.uncommentAction)
		self.menu.addAction(self.indentAction)
		self.menu.addAction(self.unindentAction)
		self.menu.addSeparator()
		self.menu.addAction(self.learnKeystrokesAction)
		self.menu.addAction(self.replayKeystrokesAction)
		# WARNING: Adding this sub-menu makes the PythonCodeEditor not suitable for integration in any 
		# widget, but only in WDocument.
		if hasattr(self.parent(), "getEditorPluginActions"):
			self.menu.addSeparator()
			self.editorPluginsMenu = QMenu("Plugins")
			self.menu.addMenu(self.editorPluginsMenu)
			self.connect(self.editorPluginsMenu, SIGNAL("aboutToShow()"), self.prepareEditorPluginsMenu)

		self.menu.addSeparator()
		self.templatesMenu = QMenu("Templates")
		self.menu.addMenu(self.templatesMenu)
		self.templateManager = TemplateManager.TemplateManager([QApplication.instance().get('qtestermanpath') + "/default-templates.xml", QApplication.instance().get('qtestermanpath') + "/user-templates.xml"], self.parent())
		if len(self.templateManager.templates) != 0:
			previousXmlFile = ""
			for template in self.templateManager.templates:
				#separator between default and user templates (and others...)
				if previousXmlFile != "" and previousXmlFile != template.xmlFile:
					self.templatesMenu.addSeparator()
				previousXmlFile = template.xmlFile
				#log("DEBUG: adding action in templates contextual menu..." + unicode(template.name))
				showName = template.name
				if template.shortcut != "":
					showName = "%s (%s)" % (showName, template.shortcut)
				templateAction = TestermanAction(self, showName, lambda name=template.name: self.templateCodeWriter(name), template.description)
				self.templatesMenu.addAction(templateAction)

		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.connect(self, SIGNAL("customContextMenuRequested (const QPoint&)"), self.onPopupMenu)
		
		# shortcut only actions
		self.autoCompletionAction = TestermanAction(self, "Auto completion", self.autoCompletion) 
		self.autoCompletionAction.setShortcut(Qt.CTRL + Qt.Key_Space)
		self.autoCompletionAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.autoCompletionAction)
#		self.callTipAction = TestermanAction(self, "Tool tip", self.showTip) 
#		self.callTipAction.setShortcut(Qt.CTRL + Qt.Key_Shift + Qt.Key_Space) #does not work... (ctrl + shift + space)
#		self.callTipAction.setShortcutContext(Qt.WidgetShortcut)
#		self.addAction(self.callTipAction)
		self.autoCompleteTemplate = TestermanAction(self, "Auto complete template", self.autoCompleteTemplate) 
		self.autoCompleteTemplate.setShortcut(Qt.CTRL + Qt.Key_J)
		self.autoCompleteTemplate.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.autoCompleteTemplate)

	def prepareEditorPluginsMenu(self):
		self.editorPluginsMenu.clear()
		for action in self.parent().getEditorPluginActions():
			print "DEBUG: adding action in plugin contextual menu..." + unicode(action.text())
			self.editorPluginsMenu.addAction(action)

	def onPopupMenu(self, event):
		self.menu.popup(QCursor.pos())

	def setPlainText(self, text):
		"""
		For compatibility with a QTextEdit widget.
		Also ensure that the cursor is not reset to the beginning of the text.
		text is a unicode string.
		"""
		line, index = self.getCursorPosition()
		self.setText(text)
		self.setCursorPosition(line, index)

	def toPlainText(self):
		"""
		For compatibility with a QTextEdit widget.
		return a unicode string.
		"""
		return self.getCode()

	def onLinesChanged(self):
		"""
		Update the line counter margin's width.
		"""
		# The default and minimal line count margin can contain 3 digits.
		# The experience shows that we need, for that purpose, set 4 digits to QScintilla...
		# Hence this x10 factor
		l = self.lines() * 10
		if l < 1000: l = 1000
		self.setMarginWidth(1, "%d" % l)
		self.outlineMaybeUpdated()

	def wheelEvent(self, wheelEvent):
		if not (wheelEvent.modifiers() & Qt.ControlModifier):
			return sci.QsciScintilla.wheelEvent(self, wheelEvent)
		delta = wheelEvent.delta()
#		print "DEBUG: delta: " + str(delta)
		if delta > 0:
			self.zoomOut(1) # does nothing when the text was already set with a currentFont ???!
		else:
			self.zoomIn(1)
		# Updates the width of the line counter margin as well.
		self.onLinesChanged()
		wheelEvent.accept()

	def getCode(self):
		"""
		Return the code being edited.
		"""
		# Get rids of possible ^M, etc.
		self.convertEols(self.eolMode())
		return unicode(self.text())

	def multiLineInsert(self, ch):
		"""
		Insert ch at the beginning of:
		- the current line, if no selection
		- all the selected lines, if a selection exists.
		Useful to indent and comment.
		"""
		selection = True
		(lineFrom, indexFrom, lineTo, indexTo) = self.getSelection()
		if lineFrom == -1 and lineTo == -1: # no actual selection
			currentLine, currentIndex = self.getCursorPosition()
			selection = False

		toLine = lineTo
		# If the cursor is at the beginning of a line just after a selected line, ignore this line.
		if selection and indexTo == 0: toLine -= 1

		self.beginUndoAction()

		for line in range(lineFrom, toLine + 1):
			self.insertAt(ch, line, 0)
			if line == lineTo:
				if selection: indexTo += 1
				else: currentIndex += 1

		# Restore the selection
		if selection:
			self.setSelection(lineFrom, indexFrom, lineTo, indexTo)
		else:
			self.setCursorPosition(currentLine, currentIndex)
		self.endUndoAction()
		self.outlineMaybeUpdated()

	def multiLineUninsert(self, ch):
		"""
		Delete ch if it is the first character of:
		- the current line, if no selection
		- all the selected lines, if a selection exists.
		Useful to unindent and uncomment.
		"""
		selection = True
		(lineFrom, indexFrom, lineTo, indexTo) = self.getSelection()
		if lineFrom == -1 and lineTo == -1: # no actual selection
			currentLine, currentIndex = self.getCursorPosition()
			selection = False

		toLine = lineTo
		# If the cursor is at the beginning of a line just after a selected line, ignore this line.
		if selection and indexTo == 0: toLine -= 1

		self.beginUndoAction()

		for line in range(lineFrom, toLine + 1):
			pos = self.getPosFromLineIndex(line, 0)
#			if self.text().at(pos) == QChar(ch):
			if unicode(self.text()).encode('utf-8')[pos] == ch:
				self.setSelection(line, 0, line, 1)
				self.removeSelectedText()
				# Adjust the cursor position/selection
				if not selection:
					currentIndex -= 1
				else:
					# only adjust the selection index on last and first selected line
					if line == lineTo: indexTo -= 1
					if line == lineFrom: indexFrom -= 1

		# Restore the selection
		if selection:
			self.setSelection(lineFrom, indexFrom, lineTo, indexTo)
		else:
			self.setCursorPosition(currentLine, currentIndex)
		self.endUndoAction()
		self.outlineMaybeUpdated()

	def indent(self):
		self.multiLineInsert('\t')

	def unindent(self):
		self.multiLineUninsert('\t')

	def comment(self):
		self.multiLineInsert('#')

	def uncomment(self):
		self.multiLineUninsert('#')

	def toggleLearnKeystrokes(self):
		if self.learningKeystrokes:
			self.learntKeystrokes.endRecording()
			self.replayKeystrokesAction.setEnabled(True)
			self.learningKeystrokes = False
			self.learnKeystrokesAction.setText("Learn keystrokes")
			QApplication.instance().get('gui.statusbar').showMessage("Keystrokes learnt.", 5000)
		else:
			self.learntKeystrokes.clear()
			self.learntKeystrokes.startRecording()
			self.learningKeystrokes = True
			self.learnKeystrokesAction.setText("Finish learn")
			QApplication.instance().get('gui.statusbar').showMessage("Learn mode activated. Press %s to finish" % unicode(self.learnKeystrokesAction.shortcut().toString()) )

	def replayKeystrokes(self):
		self.learntKeystrokes.play()

	def autoCompletion(self):
		self.autoCompleteFromAll()

	def showTip(self):
		self.callTip()

	def templateCodeWriter(self, templateName):
		"""
		Write template from templateManager
		"""
		template = self.templateManager.byName(templateName)
		if template is not None:
			code = template.activate()
			if code is not None:
				self.beginUndoAction()
				self.removeSelectedText()
				indent = self.getLineIndentation()
				self.insert(code.replace("\n", "\n" + indent))
				self.endUndoAction()
				self.outlineMaybeUpdated()
				return True
		return False

	def autoCompleteTemplate(self):
		"""
		Add template code using shortcut (shortcut then ctrl+j)
		"""
		self.getLineIndentation()
		(lineFrom, _, lineTo, _) = self.getSelection()
		if lineFrom == -1 and lineTo == -1: # no actual selection
			currentLine, currentIndex = self.getCursorPosition()
			previousWord = self.getPreviousWord()
			#log("previous word:%s" % previousWord)
			if previousWord != "":
				template = self.templateManager.byShortcut(previousWord)
				if template is not None:
					currentLine, currentIndex = self.getCursorPosition()
					self.setSelection(currentLine, currentIndex-len(previousWord), currentLine, currentIndex)
					if not self.templateCodeWriter(template.name):
						self.setCursorPosition(currentLine, currentIndex)
		
	def getPreviousWord(self):
		"""
		get the word just before the cursor
		"""
		currentPos = self.SendScintilla(sci.QsciScintillaBase.SCI_GETCURRENTPOS)
		wordStart = self.SendScintilla(sci.QsciScintillaBase.SCI_WORDSTARTPOSITION, currentPos, True)
		#log("current pos:%d" % currentPos)
		#log("word start true:%d" % wordStart)

		if wordStart == currentPos:
			return ""
		else:
			return unicode(self.text()).encode('utf-8')[wordStart:currentPos]

	def getLineIndentation(self):
		"""
		get the characters (tabulations or spaces) used to indent the current line
		"""
		pos = self.SendScintilla(sci.QsciScintillaBase.SCI_GETCURRENTPOS)
		lineno = self.SendScintilla(sci.QsciScintillaBase.SCI_LINEFROMPOSITION, pos)
		lineContent = unicode(self.text(lineno))[:-1]
		tab = lineContent[0:len(lineContent) - len(lineContent.lstrip())]
		#log("line:|%s|" % lineContent)
		#log("tab:|%s|, len=%d" % (tab, len(tab)))
		return tab

	def getPosFromLineIndex(self, line, index):
		"""
		Implemented from the non-exported function:
		long QsciScintilla::posFromLineIndex(int line, int index) const
{
    long pos = SendScintilla(SCI_POSITIONFROMLINE, line);

    // Allow for multi-byte characters.
    for(int i = 0; i < index; i++)
        pos = SendScintilla(SCI_POSITIONAFTER, pos);

    return pos;
}
		"""
		pos = self.SendScintilla(sci.QsciScintillaBase.SCI_POSITIONFROMLINE, line)
		for i in range(0, index):
			pos = self.SendScintilla(sci.QsciScintillaBase.SCI_POSITIONAFTER, pos)
		return pos

	def onCursorPositionChanged(self, line, col):
		QApplication.instance().get('gui.statusbar').setLineCol(line + 1, col + 1)
		QApplication.instance().get('gui.outlineview').setLine(line + 1)

	def goTo(self, line, col = 0):
		if line is not None:
			if col is None:
				col = 0
			self.setCursorPosition(line, col)
			self.setFocus(Qt.OtherFocusReason)

	def highlight(self, line, error = True):
		"""
		Highlight a line (de-highlighting a previous highlight, if any)
		If error is set, highlight it in red.

		Do not ensure that the editor is scrolled to the highlighted line. For that, use goTo().
		"""
		# Reinit the current highlight
		self.clearHighlight()

		if line:
			if error:
				self.lastHighlight = self.markerAdd(line, self.ERROR_MARKER)
			else:
				self.lastHighlight = self.markerAdd(line, self.LINE_MARKER)

	def clearHighlight(self):
		"""
		Clear existing highlight, if any
		"""
		if self.lastHighlight is not None:
			self.markerDeleteHandle(self.lastHighlight)
			self.lastHighlight = None

	def outlineMaybeUpdated(self):
		"""
		Call this whenever the outline may have been updated.
		"""
		QApplication.instance().get('gui.outlineview').updateModel(str(self.text().toUtf8()))

	def onTextChanged(self):
		autocompletion = QSettings().value('editor/autocompletion', QVariant(False)).toBool()
		if autocompletion:
			QTimer.singleShot(500, self.autoCompletion)

################################################################################
# Session Variable Management
################################################################################
#
# This widget takes a DocumentModel.metadata as an input,
# and provides two kinds of output:
# - updated metadata, containing "previous-value" set to the new value set by the user,
#   suitable for a DocumentModel.setMetadata(),
# - a session dict containing these "previous-value"s ready for the current execution.
#   This dict contains utf-8 values, and can be passed to a scheduleAts/Campaign.


class WSessionParameterTreeWidgetItem(QTreeWidgetItem):
	"""
	This item interfaces a metadata parameter QDomElement.
	"""
	def __init__(self, parameter, parent = None):
		"""
		@type  parameter: dict[unicode] of unicode
		@param parameter: a representation of a parameter, as performed by a metadataModel:
											a dict of 'name', 'default', 'description', 'previous-value', 'type'.
		"""
		QTreeWidgetItem.__init__(self, parent)
		self.parameter = parameter
		
		if not self.parameter.has_key('previous-value') or not self.parameter['previous-value']:
			self.parameter['previous-value'] = self.parameter['default']

		description = self.parameter['description']
		description += ' (defaut: %s)' % self.parameter['default']
		self.setToolTip(1, description)

		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)

	def data(self, column, role):
		if not (role == Qt.EditRole or role == Qt.DisplayRole):
			return QVariant()
		if column == 0 and role == Qt.DisplayRole: # read only on name
			return QVariant(self.parameter['name'])
		if column == 1:
			return QVariant(self.parameter['previous-value'])
		return QVariant()

	def setData(self, column, role, value):
		if role == Qt.EditRole and column > 0:
			val = unicode(value.toString())
			if column == 1:
				self.parameter['previous-value'] = val

class WSessionParameterEditor(QTreeWidget):
	"""
	Using a documentModel.metadataModel.getParameters() as an input, enables the edition of
	values for the available script parameters and build a session var dict.
	which is suitable for running an ATS/Campaign.

	the metadata is also available and updated to include previous-value attributes as
	set through this widget.

	This is not a view over a model; just an interface to modify things, with
	exploitable outputs:
	- getSessionDict(): return the session dictionnary
	"""
	def __init__(self, parameters, parent = None):
		"""
		We make a copy of the input parameters dict, since we're about to reuse it for our own purposes.
		"""
		QTreeWidget.__init__(self, parent)
		self.parameters = copy.deepcopy(parameters)
		self.__createWidgets()
		self.rebuildTree()

	def __createWidgets(self):
		labels = QStringList()
		labels.append('name')
		labels.append('value')
		self.setHeaderLabels(labels)
		self.setRootIsDecorated(False)
		self.setSortingEnabled(1)
		self.header().setClickable(1)
		# Default sort
		self.sortItems(0, Qt.AscendingOrder)

	def rebuildTree(self):
		"""
		Rebuild the tree according to the self.domDocument
		"""
		self.clear()

		for (name, parameter) in self.parameters.items():
			parameter['name'] = name
			WSessionParameterTreeWidgetItem(parameter, self)

		# We resort the view
		self.sortItems(self.sortColumn(), self.header().sortIndicatorOrder())

	def getSessionDict(self):
		"""
		Returns a dict containing set session variables.
		@rtype: dict[unicode] of unicode
		@returns: a dict indexed by name containing the value for the run.
		"""
		ret = {}
		for (name, parameter) in self.parameters.items():
			# parameters is a dict containing name/default/description/type.
			# We make it simplier here.
			ret[name] = parameter['previous-value']
		return ret

	def saveToFile(self):
		"""
		Save the current parameters to a file.
		"""
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getSaveFileName(self, "Choose a file", directory, "Parameters files (*.conf);;All files (*.*)")
		if not filename.isEmpty():
			filename = unicode(filename)
			directory = os.path.dirname(filename)
			settings.setValue('lastVisitedDirectory', QVariant(directory))
			try:
				f = open(filename, 'w')
				for name, value in self.getSessionDict().items():
					f.write("%s=%s\n" % (name.encode('utf-8'), value.encode('utf-8')))
				f.close()
				QMessageBox.information(self, getClientName(), "Script parameters have been saved successfully.", QMessageBox.Ok)
			except Exception, e:
				systemError(self, "Unable to save parameter file: " + str(e))
				log("Unable to save parameter file: " + str(e))

	def loadFromFile(self):
		"""
		Load session values from a conf file (key=value).
		Only keys declared in the metadata are read. Other are discarded.
		"""
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getOpenFileName(self, "Choose a file", directory, "Parameters files (*.conf);;All files (*.*)")
		if not filename.isEmpty():
			filename = unicode(filename)
			directory = os.path.dirname(filename)
			settings.setValue('lastVisitedDirectory', QVariant(directory))
			try:
				values = {}
				f = open(filename)
				for l in f.readlines():
					m = re.match(r'\s*(?P<key>[^#].*)=(?P<value>.*)', l)
					if m:
						values[m.group('key').decode('utf-8')] = m.group('value').decode('utf-8')
				f.close()

				# Now, update the current parameters dict with the loaded values
				for (name, p) in self.parameters.items():
					if values.has_key(name):
						p['previous-value'] = values[name]

				self.rebuildTree()
			except Exception, e:
				systemError(self, "Unable to load parameter file: " + str(e))
				log("Unable to load parameter file: " + str(e))

class WSessionParameterEditorDialog(QDialog):
	"""
	A WSessionParameterEditor embedded within a dialog.
	"""
	def __init__(self, metadataModel, parent = None):
		QDialog.__init__(self, parent)
		self.metadataModel = metadataModel
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("Initial session parameters")
		self.setWindowIcon(icon(':icons/testerman.png'))

		layout = QVBoxLayout()
		self.parameterEditor = WSessionParameterEditor(self.metadataModel.getParameters(), self)
		layout.addWidget(self.parameterEditor)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.loadButton = QPushButton("Load...", self)
		self.connect(self.loadButton, SIGNAL("clicked()"), self.parameterEditor.loadFromFile)
		buttonLayout.addWidget(self.loadButton)
		self.saveButton = QPushButton("Save...", self)
		self.connect(self.saveButton, SIGNAL("clicked()"), self.parameterEditor.saveToFile)
		buttonLayout.addWidget(self.saveButton)
		self.okButton = QPushButton("Run", self)
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self.okButton)
		self.cancelButton = QPushButton("Cancel", self)
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self.cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def getSessionDict(self):
		return self.parameterEditor.getSessionDict()

class WScheduleDialog(QDialog):
	"""
	A WSessionParameterEditor embedded within a dialog, with
	an additional date/time picker widget.
	"""
	def __init__(self, metadataModel, parent = None):
		QDialog.__init__(self, parent)
		self._metadataModel = metadataModel
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("Schedule a run")
		self.setWindowIcon(icon(':icons/testerman.png'))

		layout = QVBoxLayout()
		layout.addWidget(QLabel("Scheduling:"))
		self._dateTimePicker = CommonWidgets.WDateTimePicker()
		layout.addWidget(self._dateTimePicker)
		layout.addWidget(QLabel("Session parameters:"))
		self._parameterEditor = WSessionParameterEditor(self._metadataModel.getParameters(), self)
		layout.addWidget(self._parameterEditor)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self._loadButton = QPushButton("Load...", self)
		self.connect(self._loadButton, SIGNAL("clicked()"), self._parameterEditor.loadFromFile)
		buttonLayout.addWidget(self._loadButton)
		self._saveButton = QPushButton("Save...", self)
		self.connect(self._saveButton, SIGNAL("clicked()"), self._parameterEditor.saveToFile)
		buttonLayout.addWidget(self._saveButton)
		self._okButton = QPushButton("Schedule", self)
		self.connect(self._okButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self._okButton)
		self._cancelButton = QPushButton("Cancel", self)
		self.connect(self._cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self._cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def getSessionDict(self):
		return self._parameterEditor.getSessionDict()

	def getScheduledTime(self):
		"""
		Returns the time as a integer (Python time)
		"""
		return self._dateTimePicker.selectedDateTime().toTime_t()
