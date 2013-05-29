# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009-2012 QTesterman contributors
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
# Editors for ATS, Campaign, Modules.
#
##

import PyQt4.Qsci as sci

from PyQt4.Qt import *

import compiler
import copy
import keyword
import os.path
import parser
import re
import time

from Base import *
import DocumentModels
import CommonWidgets

import LogViewer
import PluginManager
import Plugin
import RemoteBrowsers
import TemplateManager
import DocumentManager

import DocumentPropertyEditor

##
# A WDocument is either a WModuleDocument, WAtsDocument, or a WCampaignDocument.
#
##



###############################################################################
# WDocumentEditor: base class for an editor able to manage a DocumentModel.
# Inherited by W{Ats,Campaign,Module}Document
###############################################################################

class WDocumentEditor(QWidget):
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

	def getCategorizedPluginActions(self):
		"""
		Returns a list of categorized actions associated to the
		possible plugins for the current document.
		May be structured into several menu actions, depending on the document type.
		
		This function is called to create the main window "plugins" menu,
		and may be used by the WDocument itself to add entry points
		to plugins according to the local GUI (context menu, explicit buttons, ...).
		
		@rtype: list of tuple (label, list of QAction)
		@returns: a list of categories labelled with a label and a list
		of plugin QActions that fits into this category.
		"""
		ret = []
		# Editor plugins
		category = []
		for action in self.getEditorPluginActions():
			category.append(action)
		ret.append(('Editor', category))
		# Documentation
		category = []
		for action in self.getDocumentationPluginActions():
			category.append(action)
		ret.append(('Documentation', category))
		return ret

	def getEditorPluginActions(self):
		# For now, we just have code writer plugins.
		ret = getCodeWriterPluginActions(self.editor, self.model.getDocumentType(), self.editor)
		return ret
	
	def getDocumentationPluginActions(self):
		ret = getDocumentationPluginActions(self.model, self.model.getDocumentType(), self.editor)
		return ret

	def setTabWidget(self, tabWidget):
		"""
		Enables this widget to be aware of the tab widget it is insered into, and its position.
		Note: normally it is its direct widget parent.
		"""
		self.tabWidget = tabWidget

	def _saveLocally(self, filename, copy = False):
		"""
		@type  filename: QString
		@param filename: the filename to use to save the current document (absolute path)
		@type  copy: bool
		@param copy: True f this is a local copy; in this case, the current saved attributes remains
		unchanged.
		
		@rtype: bool
		@returns: True if successfully saved, False otherwise
		"""
		self.updateModel()
		log(u"Saving locally to filename %s (copy=%s)" % (filename, copy))
		try:
			f = open(unicode(filename), 'w')
			# Store files as utf8
			f.write(self.model.getDocumentSource())
			f.close()
			if not copy:
				QApplication.instance().get('gui.statusbar').showMessage("Successfully saved as %s" % (filename))
				self.model.setSavedAttributes(url = QUrl.fromLocalFile(filename), timestamp = time.time())
				self.model.resetModificationFlag()
				QApplication.instance().get('gui.statusbar').setFileLocation(self.model.getUrl())
			else:
				QApplication.instance().get('gui.statusbar').showMessage("Local copy saved as %s successfully" % (filename))
			return True
		except Exception, e:
			log(getBacktrace())
			CommonWidgets.systemError(self, "Unable to save file as %s: %s" % (filename, str(e)))
			QApplication.instance().get('gui.statusbar').showMessage("Unable to save file %s: %s" % (filename, str(e)))
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
		
		username = QVariant(QSettings().value('connection/username', QVariant(QString()))).toString()
		try:
			# Store files as utf8
			# compress the files on the wire (requires Ws 1.3)
			ret = getProxy().putFile(self.model.getDocumentSource(), unicode(filename), useCompression = True, username = unicode(username))
			if not ret:
				error = "Please check permissions."
		except Exception, e:
			log(getBacktrace())
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
			CommonWidgets.systemError(self, "Unable to save file to repository: %s" % error)
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
		if not self.aboutToSave():
			return False

		# Is it a resave ?
		if self.model.getUrl().scheme() != 'unsaved':
			if self.model.isRemote():
				# Resave to repository
				return self.saveToRepository()
			else:
				# Locally resave
				return self._saveLocally(self.model.getUrl().toLocalFile())
		else:
			# Never saved for now.
			return self.saveAs()

	def saveAs(self, copy = False):
		"""
		Opens a local browser to browse for a filename to save,
		then saves the file.
		
		@type  copy: bool
		@param copy: set to True if this is a local copy. In this case, the
		current document's URI won't be modified.

		@rtype: bool
		@returns: True if successufully saved, False otherwise
		"""
		# Open a browser
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getSaveFileName(self, "Save as...", directory, self.filenameTemplate)
		if filename.isEmpty():
			return False
		elif not filename.split('.')[-1] == self.model.getFileExtension():
			filename = "%s.%s" % (filename, self.model.getFileExtension())

		directory = os.path.dirname(unicode(filename))
		settings.setValue('lastVisitedDirectory', QVariant(directory))

		# Save the file
		return self._saveLocally(filename, copy)

	def saveToRepositoryAs(self):
		"""
		Opens a sort of remote browser to browser for a filename to save on the server,
		(proposing file overwrite if needed)
		then saves the file.

		@rtype: bool
		@returns: True if successufully saved, False otherwise
		"""
		self.updateModel()
		
		initialDir = None
		if self.model.isRemote():
			filename = self.model.getUrl().path()
			initialDir = os.path.split(unicode(filename))[0]
		
		# Get a new filename (docroot-path, extension added if needed, overwrite confirmation prompted)
		
		filename = RemoteBrowsers.getSaveFileName(getProxy(), dir = initialDir, caption = "Save to repository as...", filter_ = [ self.model.getDocumentType() ], defaultExtension = self.model.getFileExtension(), parent = self)
		if not filename.isEmpty():
			# Now we can save the file
			return self._saveRemotely(filename)

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
		if not change and self.editor:
			self.editor.setModified(0)
		self.onUrlUpdated()

	##
	# Things to reimplement in subclasses
	##
	def updateModel(self):
		# Implemented in sub-classes only
		pass

	def goTo(self, line, col = 0):
		"""
		Called by the outline view.
		FIXME: should be removed from the WDocumentEditor base class,
		as it is only suitable to line/text based editors.
		"""
		pass

	def replace(self):
		"""
		Function to override in dedicated subclasses.
		"""
		return
	
	def aboutToSave(self):
		"""
		Called before saving a document.
		Enables last-second checks before saving.
		May be overriden in the WDocument subclasses.

		The default implementation does nothing and allows saving the doc.

		@rtype: boolean
		@returns: True if OK to save, False otherwise.
		"""
		return True

	def aboutToDocument(self):
		"""
		Called before documenting the viewed model.
		Useful to intercept a documentation action to perform
		some view to model commit and optional syntax checks.
		May be overriden in the WDocument subclasses.

		The default implementation does nothing and allows proceeding with 
		creating the documentation.

		@rtype: boolean
		@returns: True if OK to document, False otherwise.
		"""
		return True

	def getIcon(self):
		"""
		Returns an icon representing the edited object.
		"""
		return icon(':/icons/item-types/unknown')

###############################################################################
# Module Edition
###############################################################################

class WModuleDocumentEditor(WDocumentEditor):
	"""
	Enable to edit and manipulate a module.

	This is a view over a ModuleModel (aspect: body)

	This should better be inherited from something common to WScript and WModuleDocument (especially for
	save/saveToRepository functions).
	"""
	def __init__(self, moduleModel, parent = None):
		WDocumentEditor.__init__(self, moduleModel, parent)
		self.__createWidgets()
		self.filenameTemplate = "Testerman Module (*.py)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelDocumentReplaced)

	def onModelDocumentReplaced(self):
		self.primaryEditor.setPlainText(self.model.getBodyModel())

	def getEditorPluginActions(self):
		"""
		Overriden to provide the correct parent to the plugin actions.
		"""
		# For now, we just have code writer plugins.
		ret = getCodeWriterPluginActions(self.activeEditor, self.model.getDocumentType(), self.activeEditor)
		return ret
	
	def getDocumentationPluginActions(self):
		"""
		Overriden to provide the correct parent to the plugin actions.
		"""
		ret = getDocumentationPluginActions(self.model, self.model.getDocumentType(), self.activeEditor)
		return ret

	def setActiveEditor(self, editor):
		self.activeEditor = editor
		self.find.setScintillaWidget(editor)
	
	def splitView(self):
		"""
		Add another editor view.
		"""
		editor = WPythonCodeEditor(None, self, self.primaryEditor.document(), documentEditor = self)
		self.connect(editor, SIGNAL("focused"), self.setActiveEditor)
		self.editors.append(editor)

		self.editorSplitter.addWidget(editor)
		
		# Not collapsible for now
		self.editorSplitter.setCollapsible(len(self.editors), False)

	def closeView(self):
		if self.activeEditor is not self.primaryEditor:
			index = self.editors.index(self.activeEditor)
			w = self.editorSplitter.widget(index+1) # +1 because it includes the primaryEditor (index 0 in the splitter), and it is not in self.editors
			# Remove the widget from the QSplitter
			w.hide()
			w.setParent(None)
			del self.editors[index]
			del w
			# Focus on the previous widget - that's (index+1)-1, so always >= 0, i.e. the widget always exists.
			self.editorSplitter.widget(index).setFocus(Qt.OtherFocusReason)
		
	def __createWidgets(self):
		"""
		A main WScriptEditor, plus an associated action bar at the bottom with:
		- an action button to test/run the script.
		- a button to check syntax
		"""

		layout = QVBoxLayout()

		# The primary editor view
		self.primaryEditor = WPythonCodeEditor(self.model.getBodyModel(), self, documentEditor = self)
		self.connect(self.primaryEditor, SIGNAL("focused"), self.setActiveEditor)
		# QsciScintilla directly manage the signal
		self.connect(self.primaryEditor, SIGNAL('modificationChanged(bool)'), self.model.onBodyModificationChanged)

		self.activeEditor = self.primaryEditor
		
		# Split views
		self.editors = []

		self.editorSplitter = QSplitter(Qt.Vertical)
		self.editorSplitter.addWidget(self.primaryEditor)
		self.editorSplitter.setCollapsible(0, False)
		
		layout.addWidget(self.editorSplitter)

		##
		# The action bar, bottom bar
		##
		actionLayout = QHBoxLayout()

		# A find widget
		self.find = CommonWidgets.WSciFind(self.primaryEditor, self)
		actionLayout.addWidget(self.find)
		
		# Actions associated with Module edition:
		# syntax check,
		# documentation via Module documentation plugins,
		# run with several options (session parameters, scheduling)
		# By default, icon sizes are 24x24. We resize them to 16x16 to avoid too large buttons.

		# Syntax check action
		self.syntaxCheckAction = CommonWidgets.TestermanAction(self, "Check syntax", self.verify, "Check Module syntax")
		self.syntaxCheckAction.setIcon(icon(':/icons/check.png'))
		self.syntaxCheckButton = QToolButton()
		self.syntaxCheckButton.setIconSize(QSize(16, 16))
		self.syntaxCheckButton.setDefaultAction(self.syntaxCheckAction)

		# Documentation actions - needs switching to a plugin architecture
		self.documentationButton = QToolButton()
		self.documentationButton.setIcon(icon(':/icons/documentation'))
		self.documentationButton.setIconSize(QSize(16, 16))
		self.documentationPluginsMenu = QMenu('Documentation', self)
		self.connect(self.documentationPluginsMenu, SIGNAL("aboutToShow()"), self.prepareDocumentationPluginsMenu)
		self.documentationButton.setMenu(self.documentationPluginsMenu)
		self.documentationButton.setPopupMode(QToolButton.InstantPopup)

		actionLayout.addStretch()
		actionLayout.addWidget(self.documentationButton)
		actionLayout.addWidget(self.syntaxCheckButton)

		actionLayout.setMargin(2)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def onModelModificationChanged(self, change):
		"""
		Update the tab title (status indicator),
		tells the Editor widget that its document is marked as not modified.
		
		Overriden for this document editor, using a self.primaryEditor instead of a self.editor.
		"""
		if not change:
			self.primaryEditor.setModified(0)
		self.onUrlUpdated()

	def aboutToSave(self):
		return self.verify(False)

	def updateModel(self):
		self.model.setBodyModel(self.activeEditor.getCode())

	def goTo(self, line, col = 0):
		self.activeEditor.goTo(line, col)

	def replace(self):
		"""
		replace function
		"""
		replaceBox = CommonWidgets.WSciReplace(self.activeEditor, self)
		replaceBox.show()

	def verify(self, displayNoError = True):
		self.updateModel()
		self.activeEditor.clearHighlight()
		try:
			body = unicode(self.model.getBodyModel()).encode('utf-8')
			parser.suite(body).compile()
			compiler.parse(body)
			if displayNoError:
				QMessageBox.information(self, getClientName(), "No syntax problem was found in this module.", QMessageBox.Ok)
			return True
		except SyntaxError, e:
			self.activeEditor.highlight(e.lineno - 1)
			self.activeEditor.goTo(e.lineno - 1, e.offset)
			CommonWidgets.userError(self, "Syntax error on line %s: <br />%s" % (str(e.lineno), e.msg))
			self.activeEditor.setFocus(Qt.OtherFocusReason)
		return False

	def prepareDocumentationPluginsMenu(self):
		self.documentationPluginsMenu.clear()
		print "DEBUG: yoyo"
		for action in getDocumentationPluginActions(self.model, self.model.getDocumentType(), self):
			log("adding action in plugin contextual menu..." + unicode(action.text()))
			self.documentationPluginsMenu.addAction(action)

	def aboutToDocument(self):
		return self.verify(False)

	def getIcon(self):
		"""
		Returns an icon representing the edited object.
		"""
		return icon(':/icons/item-types/module')

DocumentManager.registerDocumentEditorClass(DocumentModels.TYPE_MODULE, WModuleDocumentEditor)

###############################################################################
# ATS Edition
###############################################################################

class WAtsDocumentEditor(WDocumentEditor):
	"""
	Enable to edit and manipulate the script (execute as, associate an id, etc).

	Derived view from WDocument.
	
	Now includes the script properties editor:
	- one panel to edit the script prototype,
	- another panel to edit available groups
	"""
	def __init__(self, atsModel, parent = None):
		WDocumentEditor.__init__(self, atsModel, parent)
		self.__createWidgets()
		self.filenameTemplate = "Testerman ATS (*.ats)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelDocumentReplaced)
		# deselected groups are "persisted" across runs
		self._deselectedGroups = []

	def getEditorPluginActions(self):
		"""
		Overriden to provide the correct parent to the plugin actions.
		"""
		# For now, we just have code writer plugins.
		ret = getCodeWriterPluginActions(self.activeEditor, self.model.getDocumentType(), self.activeEditor)
		return ret
	
	def getDocumentationPluginActions(self):
		"""
		Overriden to provide the correct parent to the plugin actions.
		"""
		ret = getDocumentationPluginActions(self.model, self.model.getDocumentType(), self.activeEditor)
		return ret

	def onModelDocumentReplaced(self):
		self.primaryEditor.setPlainText(self.model.getBodyModel())
		self.parametersEditor.setModel(self.model.getMetadataModel())
		self.groupsEditor.setModel(self.model.getMetadataModel())

	def toggleParametersEditor(self, checked):
		if checked:
			self.parametersEditor.show()		
		else:
			self.parametersEditor.hide()

	def toggleGroupsEditor(self, checked):
		if checked:
			self.groupsEditor.show()		
		else:
			self.groupsEditor.hide()
		
	def togglePropertiesEditor(self, checked):
		if checked:
			self.propertiesEditor.show()		
		else:
			self.propertiesEditor.hide()
		
	def toggleProfilesEditor(self, checked):
		if checked:
			self.profilesManager.show()		
		else:
			self.profilesManager.hide()
	
	def toggleTestGroupsSelector(self, checked):
		if checked:
			self.testGroupsSelector.show()
		else:
			self.testGroupsSelector.hide()
	
	def setActiveEditor(self, editor):
		self.activeEditor = editor
		self.find.setScintillaWidget(editor)
	
	def splitView(self):
		"""
		Add another editor view.
		"""
		editor = WPythonCodeEditor(None, self, self.primaryEditor.document(), documentEditor = self)
		self.connect(editor, SIGNAL("focused"), self.setActiveEditor)
		self.editors.append(editor)

		self.editorSplitter.addWidget(editor)
		
		# Not collapsible for now
		self.editorSplitter.setCollapsible(len(self.editors), False)

	def closeView(self):
		if self.activeEditor is not self.primaryEditor:
			index = self.editors.index(self.activeEditor)
			w = self.editorSplitter.widget(index+1) # +1 because it includes the primaryEditor (index 0 in the splitter), and it is not in self.editors
			# Remove the widget from the QSplitter
			w.hide()
			w.setParent(None)
			del self.editors[index]
			del w
			# Focus on the previous widget - that's (index+1)-1, so always >= 0, i.e. the widget always exists.
			self.editorSplitter.widget(index).setFocus(Qt.OtherFocusReason)
		
	def __createWidgets(self):
		"""
		A main WScriptEditor, plus an associated action bar at the bottom with:
		- an action button to test/run the script.
		- a button to check syntax
		"""

		# The primary editor view
		self.primaryEditor = WPythonCodeEditor(self.model.getBodyModel(), self, documentEditor = self)
		self.connect(self.primaryEditor, SIGNAL("focused"), self.setActiveEditor)
		# QsciScintilla directly manage the signal
		self.connect(self.primaryEditor, SIGNAL('modificationChanged(bool)'), self.model.onBodyModificationChanged)

		self.activeEditor = self.primaryEditor
		
		# Split views
		self.editors = []

		##
		# (Initially) Hidden widgets
		##
		self.parametersEditor = DocumentPropertyEditor.WParametersEditor()
		self.parametersEditor.hide()
		self.parametersEditor.setModel(self.model.getMetadataModel())

		self.groupsEditor = DocumentPropertyEditor.WGroupsEditor()
		self.groupsEditor.hide()
		self.groupsEditor.setModel(self.model.getMetadataModel())

		self.propertiesEditor = DocumentPropertyEditor.WScriptPropertiesEditor()
		self.propertiesEditor.hide()
		self.propertiesEditor.setModel(self.model.getMetadataModel())

		self.profilesManager = WProfilesManager(self.model)
		self.profilesManager.hide()


		##
		# The topbar enables to show/hide ATS metadata editors, and embeds a search widget
		##
		topbarLayout = QHBoxLayout()
		# Script parameters
		self.parametersButton = QPushButton("ATS Parameters")
		topbarLayout.addWidget(self.parametersButton)
		self.parametersButton.setCheckable(True)
		self.connect(self.parametersButton, SIGNAL('toggled(bool)'), self.toggleParametersEditor)
		# Groups
		self.groupsButton = QPushButton("Testcase Groups")
		topbarLayout.addWidget(self.groupsButton)
		self.groupsButton.setCheckable(True)
		self.connect(self.groupsButton, SIGNAL('toggled(bool)'), self.toggleGroupsEditor)
		# Basic properties
		self.propertiesButton = QPushButton("Properties")
		topbarLayout.addWidget(self.propertiesButton)
		self.propertiesButton.setCheckable(True)
		self.connect(self.propertiesButton, SIGNAL('toggled(bool)'), self.togglePropertiesEditor)
		topbarLayout.addStretch()

		##
		# The action bar, bottom bar
		##
		actionLayout = QHBoxLayout()

		# A find widget
		self.find = CommonWidgets.WSciFind(self.primaryEditor, self)
		actionLayout.addWidget(self.find)
		
		# Actions associated with ATS edition:
		# syntax check,
		# documentation via ATS documentation plugins,
		# run with several options (session parameters, scheduling)
		# By default, icon sizes are 24x24. We resize them to 16x16 to avoid too large buttons.

		# Syntax check action
		self.syntaxCheckAction = CommonWidgets.TestermanAction(self, "Check syntax", self.verify, "Check ATS syntax")
		self.syntaxCheckAction.setIcon(icon(':/icons/check.png'))
		self.syntaxCheckButton = QToolButton()
		self.syntaxCheckButton.setIconSize(QSize(16, 16))
		self.syntaxCheckButton.setDefaultAction(self.syntaxCheckAction)

		# Documentation actions
		self.documentationButton = QToolButton()
		self.documentationButton.setIcon(icon(':/icons/documentation'))
		self.documentationButton.setIconSize(QSize(16, 16))
		self.documentationPluginsMenu = QMenu('Documentation', self)
		self.connect(self.documentationPluginsMenu, SIGNAL("aboutToShow()"), self.prepareDocumentationPluginsMenu)
		self.documentationButton.setMenu(self.documentationPluginsMenu)
		self.documentationButton.setPopupMode(QToolButton.InstantPopup)

		# Profile selector & associated actions
		# The toggle button to show/hide the profile manager/editor
		self.showProfilesEditorAction = QAction("Edit", self)
		self.showProfilesEditorAction.setToolTip("Open/close the profiles editor")
		self.showProfilesEditorAction.setCheckable(True)
		self.showProfilesEditorAction.setIcon(icon(':/icons/profiles-editor'))
		self.showProfilesEditorAction.setStatusTip("Open/close the profiles editor")
		self.showProfilesEditorButton = QToolButton()
		self.showProfilesEditorButton.setIconSize(QSize(16, 16))
		self.showProfilesEditorButton.setDefaultAction(self.showProfilesEditorAction)
		self.connect(self.showProfilesEditorAction, SIGNAL('toggled(bool)'), self.toggleProfilesEditor)
		# Toggle button to show/hide runtime test group selection
		self.showTestGroupsSelectorAction = QAction("Select", self)
		self.showTestGroupsSelectorAction.setToolTip("Open/close the test groups selector")
		self.showTestGroupsSelectorAction.setCheckable(True)
		self.showTestGroupsSelectorAction.setIcon(icon(':/icons/testgroups-selector'))
		self.showTestGroupsSelectorAction.setStatusTip("Open/close the test groups editor")
		self.showTestGroupsSelectorButton = QToolButton()
		self.showTestGroupsSelectorButton.setIconSize(QSize(16, 16))
		self.showTestGroupsSelectorButton.setDefaultAction(self.showTestGroupsSelectorAction)
		self.connect(self.showTestGroupsSelectorAction, SIGNAL('toggled(bool)'), self.toggleTestGroupsSelector)
		
		# Run actions
		self.runAction = CommonWidgets.TestermanAction(self, "&Run", self.run, "Run now, with regards to the previously unselected test groups")
		self.runAction.setIcon(icon(':/icons/run.png'))
		self.selectGroupsAndRunAction = CommonWidgets.TestermanAction(self, "Select groups && R&un", self.selectGroupsAndRun, "Select groups to run, then run")
		self.runWithParametersAction = CommonWidgets.TestermanAction(self, "Run with &parameters...", self.runWithParameters, "Set parameters, then run")
		self.scheduleRunAction = CommonWidgets.TestermanAction(self, "&Scheduled run...", self.scheduleRun, "Schedule a run")
		self.runMenu = QMenu('Run', self)
		self.runMenu.addAction(self.selectGroupsAndRunAction)
		self.runMenu.addAction(self.runWithParametersAction)
		self.runMenu.addAction(self.scheduleRunAction)
		self.runButton = QToolButton()
		self.runButton.setDefaultAction(self.runAction)
		self.runButton.setMenu(self.runMenu)
		self.runButton.setIconSize(QSize(16, 16))
		self.runButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
		self.runButton.setPopupMode(QToolButton.MenuButtonPopup)

		self.launchLog = QCheckBox("Display runtime log")
		self.launchLog.setChecked(True)

		actionLayout.addStretch()
		actionLayout.addWidget(self.documentationButton)
		actionLayout.addWidget(self.syntaxCheckButton)
		actionLayout.addWidget(self.runButton)
		actionLayout.addWidget(self.profilesManager.getProfileSelector())
		actionLayout.addWidget(self.showProfilesEditorButton)
		# Test Groups selector not added yet - for future study
#		actionLayout.addWidget(self.showTestGroupsSelectorButton)
		actionLayout.addWidget(self.launchLog)
		actionLayout.setMargin(2)

		##
		# Final layout
		##
		layout = QVBoxLayout()
		layout.addLayout(topbarLayout)
		
		self.mainSplitter = QSplitter(Qt.Vertical)
		
		self.mainSplitter.addWidget(self.parametersEditor)
		self.mainSplitter.addWidget(self.groupsEditor)
		self.mainSplitter.addWidget(self.propertiesEditor)
		
		self.editorSplitter = QSplitter(Qt.Vertical)
		self.editorSplitter.addWidget(self.primaryEditor)
		self.editorSplitter.setCollapsible(0, False)
		
		self.mainSplitter.addWidget(self.editorSplitter)
		
		self.mainSplitter.addWidget(self.profilesManager)
		
		self.mainSplitter.setCollapsible(0, False)
		self.mainSplitter.setCollapsible(1, False)
		self.mainSplitter.setCollapsible(2, False)
		self.mainSplitter.setCollapsible(3, False)
		self.mainSplitter.setCollapsible(4, False)
		self.mainSplitter.setStretchFactor(0, 1)
		self.mainSplitter.setStretchFactor(1, 1)
		self.mainSplitter.setStretchFactor(2, 1)
		self.mainSplitter.setStretchFactor(3, 3)
		self.mainSplitter.setStretchFactor(4, 1)
		layout.addWidget(self.mainSplitter)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def onModelModificationChanged(self, change):
		"""
		Update the tab title (status indicator),
		tells the Editor widget that its document is marked as not modified.
		
		Overriden for this document editor, using a self.primaryEditor instead of a self.editor.
		"""
		if not change:
			self.primaryEditor.setModified(0)
		self.onUrlUpdated()

	def updateModel(self):
		self.model.setBodyModel(self.activeEditor.getCode())
		
	def goTo(self, line, col = 0):
		self.activeEditor.goTo(line, col)

	def replace(self):
		"""
		replace function
		"""
		replaceBox = CommonWidgets.WSciReplace(self.activeEditor, self)
		replaceBox.show()

	def verify(self, displayNoError = 1):
		self.updateModel()
		self.activeEditor.clearHighlight()
		try:
			body = unicode(self.model.getBodyModel()).encode('utf-8')
			parser.suite(body).compile()
			compiler.parse(body)
			if displayNoError:
				QMessageBox.information(self, getClientName(), "No syntax problem was found in this ATS.", QMessageBox.Ok)
			return 1
		except SyntaxError, e:
			self.activeEditor.highlight(e.lineno - 1)
			self.activeEditor.goTo(e.lineno - 1, e.offset)
			CommonWidgets.userError(self, "Syntax error on line %s: <br />%s" % (str(e.lineno), e.msg))
			self.activeEditor.setFocus(Qt.OtherFocusReason)
		return 0

	def _schedule(self, session, at = None, selectedGroups = None):
		"""
		Returns the job ID is ok, None otherwise.
		Takes care of the user notifications.
		"""
		try:
			res = getProxy().scheduleAts(
				ats = self.model.getDocumentSource(), 
				atsId = unicode(self.model.getName()),
				username = unicode(QApplication.instance().username()),
				session = session,
				at = at,
				groups = selectedGroups)
		except Exception, e:
			CommonWidgets.systemError(self, str(e))
			return None
		QApplication.instance().get('gui.statusbar').showMessage(res['message'])
		return res['job-id']

	##
	# Run actions
	##
	def run(self):
		"""
		Immediate run, using the current profiles,
		and the currently deselected test groups.
		"""
		# we 'commit' and verify the modified view of the script
		if not self.verify(0):
			return
		
		session = None
		profileModel = self.profilesManager.getProfileSelector().getProfileModel()
		if profileModel:
			session = profileModel.toSession()
			if profileModel.getUrl():
				log("Running with profile %s" % unicode(profileModel.getUrl().path()))
		
		# compute selected groups
		selectedGroups = [x for x in self.model.getMetadataModel().getGroups().keys() if not x in self._deselectedGroups]
		log("Selected groups for this run: %s" % ",".join(selectedGroups))
		
		jobId = self._schedule(session, selectedGroups = selectedGroups or None)
		if jobId is None:
			return

		if self.launchLog.isChecked():
			logViewer = LogViewer.WLogViewer(parent = self)
			logViewer.openJob(jobId)
			logViewer.show()

	def selectGroupsAndRun(self):
		"""
		First displays a dialog to select groups to run, then run the script.
		"""
		# we 'commit' and verify the modified view of the script
		if not self.verify(0):
			return
			
		session = None

		profileModel = self.profilesManager.getProfileSelector().getProfileModel()
		if profileModel:
			session = profileModel.toSession()
			if profileModel.getUrl():
				log("Running with profile %s" % unicode(profileModel.getUrl().path()))

		groupSelectorDialog = WGroupSelectorDialog(self.model.getMetadataModel(), self._deselectedGroups, self)
		if groupSelectorDialog.exec_() == QDialog.Accepted:
			self._deselectedGroups = groupSelectorDialog.getDeselectedGroups()
		else:
			QApplication.instance().get('gui.statusbar').showMessage('Operation cancelled')
			return

		# compute selected groups
		selectedGroups = [x for x in self.model.getMetadataModel().getGroups().keys() if not x in self._deselectedGroups]
		log("Selected groups for this run: %s" % ",".join(selectedGroups))
		
		jobId = self._schedule(session, selectedGroups = selectedGroups or None)
		if jobId is None:
			return

		if self.launchLog.isChecked():
			logViewer = LogViewer.WLogViewer(parent = self)
			logViewer.openJob(jobId)
			logViewer.show()
		
	def runWithParameters(self):
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

		jobId = self._schedule(session = session)
		if jobId is None:
			return

		if self.launchLog.isChecked():
			logViewer = LogViewer.WLogViewer(parent = self)
			logViewer.openJob(jobId)
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
		
		self._schedule(session, scheduledTime)

	def prepareDocumentationPluginsMenu(self):
		self.documentationPluginsMenu.clear()
		for action in getDocumentationPluginActions(self.model, self.model.getDocumentType(), self):
			log("adding action in plugin contextual menu..." + unicode(action.text()))
			self.documentationPluginsMenu.addAction(action)

	def aboutToDocument(self):
		return self.verify(False)

	def getIcon(self):
		"""
		Returns an icon representing the edited object.
		"""
		return icon(':/icons/item-types/ats')

DocumentManager.registerDocumentEditorClass(DocumentModels.TYPE_ATS, WAtsDocumentEditor)

###############################################################################
# Campaign Edition
###############################################################################

class WCampaignDocumentEditor(WDocumentEditor):
	"""
	Enable to edit and manipulate a Campaign.
	"""
	def __init__(self, model, parent = None):
		WDocumentEditor.__init__(self, model, parent)
		self.__createWidgets()
		self.filenameTemplate = "Testerman Campaign (*.campaign)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelDocumentReplaced)

	def onModelDocumentReplaced(self):
		self.editor.setPlainText(self.model.getBodyModel())
		self.parametersEditor.setModel(self.model.getMetadataModel())

	def toggleParametersEditor(self, checked):
		if checked:
			self.parametersEditor.show()		
		else:
			self.parametersEditor.hide()

	def toggleProfilesEditor(self, checked):
		if checked:
			self.profilesManager.show()		
		else:
			self.profilesManager.hide()
	
	def __createWidgets(self):
		"""
		A main WScriptEditor, plus an associated action bar at the bottom with:
		- an action button to test/run the script.
		- a button to check syntax (well, not yet)
		"""
		layout = QVBoxLayout()

		# The code editor
		self.editor = WPythonCodeEditor(self.model.getBodyModel(), self)
		# QsciScintilla directly manage the signal
		self.connect(self.editor, SIGNAL('modificationChanged(bool)'), self.model.onBodyModificationChanged)
	
		##
		# (Initially) Hidden widgets
		##
		self.parametersEditor = DocumentPropertyEditor.WParametersEditor()
		self.parametersEditor.hide()
		self.parametersEditor.setModel(self.model.getMetadataModel())

		self.profilesManager = WProfilesManager(self.model)
		self.profilesManager.hide()

		##
		# The topbar enables to show/hide Campaign metadata editors, and embeds a search widget
		##
		topbarLayout = QHBoxLayout()
		# Script parameters
		self.parametersButton = QPushButton("Campaign Parameters")
		topbarLayout.addWidget(self.parametersButton)
		self.parametersButton.setCheckable(True)
		self.connect(self.parametersButton, SIGNAL('toggled(bool)'), self.toggleParametersEditor)
		topbarLayout.addStretch()

		##
		# The action bar, bottom bar
		##
		actionLayout = QHBoxLayout()

		# A find widget
		self.find = CommonWidgets.WSciFind(self.editor, self)
		actionLayout.addWidget(self.find)

		# Profile selector & associated actions
		# The toggle button to show/hide the profile manager/editor
		self.showProfilesEditorAction = QAction("Edit", self)
		self.showProfilesEditorAction.setToolTip("Open/close the profiles editor")
		self.showProfilesEditorAction.setCheckable(True)
		self.showProfilesEditorAction.setIcon(icon(':/icons/profiles-editor'))
		self.showProfilesEditorAction.setStatusTip("Open/close the profiles editor")
		self.showProfilesEditorButton = QToolButton()
		self.showProfilesEditorButton.setIconSize(QSize(16, 16))
		self.showProfilesEditorButton.setDefaultAction(self.showProfilesEditorAction)
		self.connect(self.showProfilesEditorAction, SIGNAL('toggled(bool)'), self.toggleProfilesEditor)

		# Run actions
		self.runAction = CommonWidgets.TestermanAction(self, "&Run", self.run, "Run now")
		self.runAction.setIcon(icon(':/icons/run.png'))
		self.runWithParametersAction = CommonWidgets.TestermanAction(self, "Run with &parameters...", self.runWithParameters, "Set parameters, then run")
		self.scheduleRunAction = CommonWidgets.TestermanAction(self, "&Scheduled run...", self.scheduleRun, "Schedule a run")
		self.runMenu = QMenu('Run', self)
		self.runMenu.addAction(self.runWithParametersAction)
		self.runMenu.addAction(self.scheduleRunAction)
		
		self.runButton = QToolButton()
		self.runButton.setDefaultAction(self.runAction)
		self.runButton.setMenu(self.runMenu)
		self.runButton.setIconSize(QSize(16, 16))
		self.runButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
		self.runButton.setPopupMode(QToolButton.MenuButtonPopup)

		actionLayout.addStretch()
		actionLayout.addWidget(self.runButton)
		actionLayout.addWidget(self.profilesManager.getProfileSelector())
		actionLayout.addWidget(self.showProfilesEditorButton)
		actionLayout.setMargin(2)

		##
		# Final layout
		##
		layout = QVBoxLayout()
		layout.addLayout(topbarLayout)
		
		self.mainSplitter = QSplitter(Qt.Vertical)
		
		self.mainSplitter.addWidget(self.parametersEditor)
		self.mainSplitter.addWidget(self.editor)
		
		self.mainSplitter.addWidget(self.profilesManager)
		self.mainSplitter.setCollapsible(0, False)
		self.mainSplitter.setCollapsible(1, False)
		self.mainSplitter.setStretchFactor(0, 1)
		self.mainSplitter.setStretchFactor(1, 3)
		layout.addWidget(self.mainSplitter)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def updateModel(self):
		self.model.setBodyModel(self.editor.getCode())

	def replace(self):
		"""
		replace function
		"""
		replaceBox = CommonWidgets.WSciReplace(self.editor, self)
		replaceBox.show()

	def _schedule(self, session, at = None):
		"""
		Returns the job ID is ok, None otherwise.
		Takes care of the user notifications.
		"""
		if at is None:
			at = time.time() + 1.0
		try:
			res = getProxy().scheduleCampaign(
				self.model.getDocumentSource(),
				unicode(self.model.getName()), 
				unicode(QApplication.instance().username()), 
				session = session,
				at = at)
		except Exception, e:
			CommonWidgets.systemError(self, str(e))
			return None
		QApplication.instance().get('gui.statusbar').showMessage(res['message'])
		QMessageBox.information(self, getClientName(), res['message'], QMessageBox.Ok)
		return res['job-id']

	##
	# Run actions
	##
	def run(self):
		# we 'commit' the modified view of the script
		self.updateModel()

		session = None
		profileModel = self.profilesManager.getProfileSelector().getProfileModel()
		if profileModel:
			session = profileModel.toSession()
			if profileModel.getUrl():
				log("Running with profile %s" % unicode(profileModel.getUrl().path()))

		self._schedule(session = session)

	def runWithParameters(self):
		# we 'commit' the modified view of the script
		self.updateModel()

		session = None
		paramEditorDialog = WSessionParameterEditorDialog(self.model.getMetadataModel(), self)
		if paramEditorDialog.exec_() == QDialog.Accepted:
			session = paramEditorDialog.getSessionDict()
		else:
			QApplication.instance().get('gui.statusbar').showMessage('Operation cancelled')
			return
		
		self._schedule(session = session)

	def scheduleRun(self):
		"""
		Displays a dialog box to schedule a run.
		"""
		# we 'commit' the modified view of the script
		self.updateModel()

		session = None
		scheduledTime = None
		paramEditorDialog = WScheduleDialog(self.model.getMetadataModel(), self)
		if paramEditorDialog.exec_() == QDialog.Accepted:
			session = paramEditorDialog.getSessionDict()
			scheduledTime = paramEditorDialog.getScheduledTime()
		else:
			QApplication.instance().get('gui.statusbar').showMessage('Operation cancelled')
			return
		
		self._schedule(session, scheduledTime)

	def getIcon(self):
		"""
		Returns an icon representing the edited object.
		"""
		return icon(':/icons/item-types/campaign')

DocumentManager.registerDocumentEditorClass(DocumentModels.TYPE_CAMPAIGN, WCampaignDocumentEditor)


################################################################################
# Code Writers plugins
################################################################################

class CodeWriterPluginAction(CommonWidgets.TestermanAction):
	def __init__(self, editor, label, pluginInstance, parent):
		CommonWidgets.TestermanAction.__init__(self, parent, label, self.activatePlugin)
		self._editor = editor
		self._pluginInstance = pluginInstance

	def activatePlugin(self):
		ret = self._pluginInstance.activate()
		if ret:
			self._editor.insert(ret)

def getCodeWriterPluginActions(editor, documentType, parent):
	"""
	Create a list containing valid plugin actions according to the editor type.

	codeType in module/ats/campaign (for now)
	"""
	log("getting code writer plugins for " + str(documentType))
	ret = []
	for p in PluginManager.getPluginClasses(Plugin.TYPE_CODE_WRITER):
		if p['activated'] and p['class']:
			# Verify plugin/codeType compliance
			plugin = p['class'](parent)
			if plugin.isDocumentTypeSupported(documentType):
				ret.append(CodeWriterPluginAction(editor, p['label'], plugin, parent))
	return ret

class DocumentationPluginAction(CommonWidgets.TestermanAction):
	def __init__(self, model, label, pluginInstance, parent):
		"""
		The parent must be a WDocument
		"""
		CommonWidgets.TestermanAction.__init__(self, parent, label, self.activatePlugin)
		self._model = model
		self._pluginInstance = pluginInstance
		self._documentView = parent

	def activatePlugin(self):
		if hasattr(self._documentView, 'aboutToDocument'):
			if not self._documentView.aboutToDocument():
				return
		self._pluginInstance.activate(self._model)

def getDocumentationPluginActions(model, documentType, parent):
	"""
	Create a list containing valid plugin actions according to the document type.

	documentType in module/ats/campaign (for now)
	"""
	log("getting documentation plugins for " + str(documentType))
	ret = []
	for p in PluginManager.getPluginClasses(Plugin.TYPE_DOCUMENTATION_GENERATOR):
		if p['activated'] and p['class']:
			# Verify plugin/codeType compliance
			plugin = p['class'](parent)
			if plugin.isDocumentTypeSupported(documentType):
				ret.append(DocumentationPluginAction(model, p['label'], plugin, parent))
	return ret


################################################################################
# Python Editor: used for ATS and Module edition
################################################################################

TESTERMAN_KEYWORDS = [
	'setverdict',
	'getverdict',
	'get_variable',
	'set_variable',
	'connect',
	'disconnect',
	'port_map',
	'port_unmap',
	'TestCase',
	'Behaviour',
	'Timer',
	'mtc',
	'system',
	'log',
	'alt',
	'match',
	'mismatch',
	'enable_debug_logs',
	'disable_debug_logs',
]

class PythonLexer(sci.QsciLexerPython):
	pass
#	def keywords(self, setIndex):
#		if setIndex == 2:
#			return ' '.join(TESTERMAN_KEYWORDS + keyword.kwlist)
#		else:
#			return sci.QSciLexerPython.keywords(setIndex)

class WPythonCodeEditor(sci.QsciScintilla):
	def __init__(self, text = None, parent = None, scintillaDocument = None, documentEditor = None):
		sci.QsciScintilla.__init__(self, parent)
		
		# Being attached to a documentEditor enables some additional features/contextual actions
		self._documentEditor = documentEditor
		
		self._outlineUpdateTimer = QTimer()
		self.connect(self._outlineUpdateTimer, SIGNAL('timeout()'), lambda: QApplication.instance().get('gui.outlineview').updateModel(str(self.text().toUtf8())))
		self._autoCompletionTimer = QTimer()
		self.connect(self._autoCompletionTimer, SIGNAL('timeout()'), self.autoCompletion)

		# Macro
		self.learntKeystrokes = sci.QsciMacro(self)
		self.learningKeystrokes = False

		# Lexer/Highlighter settings
		lexer = PythonLexer(self)
		self.setLexer(lexer)

		self.setBraceMatching(sci.QsciScintilla.SloppyBraceMatch)

		lexer.setIndentationWarning(sci.QsciLexerPython.Inconsistent)

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
		errorColor = QColor(Qt.red)
		errorColor.setAlpha(128)
		self.setMarkerBackgroundColor(errorColor, self.ERROR_MARKER)
		self.setMarkerBackgroundColor(Qt.yellow, self.LINE_MARKER)
		# No marker margin
		self.setMarginLineNumbers(0, False)
		self.setMarginWidth(0, 10)

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
		
		# Colors & Fonts
		self.setColors()
		self.setFonts()

		self.connect(QApplication.instance().get('gui.mainwindow'), SIGNAL("editorColorsUpdated()"), self.setColors)
		self.connect(QApplication.instance().get('gui.mainwindow'), SIGNAL("editorFontsUpdated()"), self.setFonts)

	def setFonts(self):
		"""
		Load and applies fonts from the saved settings.
		"""
		settings = QSettings()
		
		lexer = self.lexer()

		# Lexer/Highlighter settings
		defaultFont = QFont()
		defaultFont.fromString(settings.value('editor/defaultFont', QVariant(QFont("courier", 8).toString())).toString())
		defaultFont.setFixedPitch(True)
		lexer.setDefaultFont(defaultFont)
		f = defaultFont
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


	def setColors(self):
		"""
		Loads and applies colors from the saved settings.
		"""
		def invert(color):
			return QColor(255 - color.red(), 255 - color.green(), 255 - color.blue(), color.alpha())

		settings = QSettings()
		lexer = self.lexer()

		defaultFgColor = QColor(settings.value('editor/colors/default.fg', QVariant(QColor(Qt.black))).toString())
		defaultBgColor = QColor(settings.value('editor/colors/default.bg', QVariant(QColor(Qt.white))).toString())

		lexer.setDefaultColor(defaultFgColor)
		lexer.setDefaultPaper(defaultBgColor)
		lexer.setColor(defaultFgColor, sci.QsciLexerPython.Default)
		lexer.setPaper(defaultBgColor, sci.QsciLexerPython.Default)

		# Dedicated color groups
		color = QColor(settings.value('editor/colors/strings.fg', QVariant(QColor(Qt.darkGreen))).toString())
		lexer.setColor(color, sci.QsciLexerPython.DoubleQuotedString)
		lexer.setColor(color, sci.QsciLexerPython.SingleQuotedString)
		lexer.setColor(color, sci.QsciLexerPython.TripleSingleQuotedString)
		lexer.setColor(color, sci.QsciLexerPython.TripleDoubleQuotedString)
		lexer.setColor(color, sci.QsciLexerPython.UnclosedString)
		color = QColor(settings.value('editor/colors/strings.bg', QVariant(defaultBgColor)).toString())
		lexer.setPaper(color, sci.QsciLexerPython.DoubleQuotedString)
		lexer.setPaper(color, sci.QsciLexerPython.SingleQuotedString)
		lexer.setPaper(color, sci.QsciLexerPython.TripleSingleQuotedString)
		lexer.setPaper(color, sci.QsciLexerPython.TripleDoubleQuotedString)
		lexer.setPaper(color, sci.QsciLexerPython.UnclosedString)

		color = QColor(settings.value('editor/colors/comments.fg', QVariant(QColor(Qt.red))).toString())
		lexer.setColor(color, sci.QsciLexerPython.Comment)
		lexer.setColor(color, sci.QsciLexerPython.CommentBlock)
		color = QColor(settings.value('editor/colors/comments.bg', QVariant(defaultBgColor.name())).toString())
		lexer.setPaper(color, sci.QsciLexerPython.Comment)
		lexer.setPaper(color, sci.QsciLexerPython.CommentBlock)
		color = QColor(settings.value('editor/colors/numbers.fg', QVariant(QColor(Qt.darkMagenta))).toString())
		lexer.setColor(color, sci.QsciLexerPython.Number)
		color = QColor(settings.value('editor/colors/numbers.bg', QVariant(defaultBgColor.name())).toString())
		lexer.setPaper(color, sci.QsciLexerPython.Number)
		color = QColor(settings.value('editor/colors/identifiers.fg', QVariant(QColor(Qt.black))).toString())
		lexer.setColor(color, sci.QsciLexerPython.Identifier)
		lexer.setColor(color, sci.QsciLexerPython.FunctionMethodName)
		lexer.setColor(color, sci.QsciLexerPython.ClassName)
		color = QColor(settings.value('editor/colors/identifiers.bg', QVariant(defaultBgColor.name())).toString())
		lexer.setPaper(color, sci.QsciLexerPython.Identifier)
		lexer.setPaper(color, sci.QsciLexerPython.FunctionMethodName)
		lexer.setPaper(color, sci.QsciLexerPython.ClassName)

		color = QColor(settings.value('editor/colors/keywords.fg', QVariant(QColor(Qt.blue))).toString())
		lexer.setColor(color, sci.QsciLexerPython.Keyword)
		lexer.setColor(color, sci.QsciLexerPython.HighlightedIdentifier)
		color = QColor(settings.value('editor/colors/keywords.bg', QVariant(defaultBgColor.name())).toString())
		lexer.setPaper(color, sci.QsciLexerPython.Keyword)
		lexer.setPaper(color, sci.QsciLexerPython.HighlightedIdentifier)

		color = QColor(settings.value('editor/colors/decorators.fg', QVariant(defaultFgColor.name())).toString())
		lexer.setColor(color, sci.QsciLexerPython.Decorator)
		color = QColor(settings.value('editor/colors/decorators.bg', QVariant(defaultBgColor.name())).toString())
		lexer.setPaper(color, sci.QsciLexerPython.Decorator)

		color = QColor(settings.value('editor/colors/operators.fg', QVariant(defaultFgColor.name())).toString())
		lexer.setColor(color, sci.QsciLexerPython.Operator)
		color = QColor(settings.value('editor/colors/operators.bg', QVariant(defaultBgColor.name())).toString())
		lexer.setPaper(color, sci.QsciLexerPython.Operator)

		self.setMatchedBraceForegroundColor(Qt.red)
		self.setMatchedBraceBackgroundColor(defaultBgColor)
		self.setUnmatchedBraceForegroundColor(Qt.red)
		self.setUnmatchedBraceBackgroundColor(invert(defaultBgColor))

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
			parameters = CommonWidgets.mimeDataToObjects(mimeParameterType, e.mimeData())
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
		self.commentAction = CommonWidgets.TestermanAction(self, "Comment", self.comment)
		self.commentAction.setShortcut(Qt.ALT + Qt.Key_C)
		self.commentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.commentAction)
		self.uncommentAction = CommonWidgets.TestermanAction(self, "Uncomment", self.uncomment)
		self.uncommentAction.setShortcut(Qt.ALT + Qt.Key_X)
		self.uncommentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.uncommentAction)
		self.indentAction = CommonWidgets.TestermanAction(self, "Indent", self.indent)
		self.indentAction.setShortcut(Qt.Key_Tab)
		self.indentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.indentAction)
		self.unindentAction = CommonWidgets.TestermanAction(self, "Unindent", self.unindent)
		self.unindentAction.setShortcut(Qt.SHIFT + Qt.Key_Tab)
		self.unindentAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.unindentAction)
		# nedit-inspired keystrokes learner (aka "anonymous macro")
		self.learnKeystrokesAction = CommonWidgets.TestermanAction(self, "Learn keystrokes", self.toggleLearnKeystrokes) 
		self.learnKeystrokesAction.setShortcut(Qt.ALT + Qt.Key_K)
		self.learnKeystrokesAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.learnKeystrokesAction)
		self.replayKeystrokesAction = CommonWidgets.TestermanAction(self, "Replay keystrokes", self.replayKeystrokes) 
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

		# Let's check if we are embedded in a widget that allows splitting/closing views
		if self._documentEditor:
			# Split views
			self.splitViewAction = CommonWidgets.TestermanAction(self, "Split view", self.splitView)
			self.splitViewAction.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_H)
			self.splitViewAction.setShortcutContext(Qt.WidgetShortcut)
			self.addAction(self.splitViewAction)
			self.closeViewAction = CommonWidgets.TestermanAction(self, "Close view", self.closeView)
			self.closeViewAction.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_J)
			self.closeViewAction.setShortcutContext(Qt.WidgetShortcut)
			self.addAction(self.closeViewAction)

			self.menu.addSeparator()
			self.menu.addAction(self.splitViewAction)
			self.menu.addAction(self.closeViewAction)

		# Adding this sub-menu makes the PythonCodeEditor not suitable for integration in any 
		# widget, but only in WDocument. So we check that the parent has the required features
		if self._documentEditor:
			self.menu.addSeparator()
			self.pluginsMenu = QMenu("Plugins")
			self.menu.addMenu(self.pluginsMenu)
			self.connect(self.pluginsMenu, SIGNAL("aboutToShow()"), self.preparePluginsMenu)

		self.menu.addSeparator()
#		self.templatesMenu = QMenu("Templates")
#		self.menu.addMenu(self.templatesMenu)
#		self.templateManager = TemplateManager.TemplateManager([QApplication.instance().get('qtestermanpath') + "/default-templates.xml", QApplication.instance().get('qtestermanpath') + "/user-templates.xml"], self.parent())
#		if len(self.templateManager.templates) != 0:
#			previousXmlFile = ""
#			for template in self.templateManager.templates:
#				#separator between default and user templates (and others...)
#				if previousXmlFile != "" and previousXmlFile != template.xmlFile:
#					self.templatesMenu.addSeparator()
#				previousXmlFile = template.xmlFile
#				#log("DEBUG: adding action in templates contextual menu..." + unicode(template.name))
#				showName = template.name
#				if template.shortcut != "":
#					showName = "%s (%s)" % (showName, template.shortcut)
#				templateAction = CommonWidgets.TestermanAction(self, showName, lambda name=template.name: self.templateCodeWriter(name), template.description)
#				self.templatesMenu.addAction(templateAction)

		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.connect(self, SIGNAL("customContextMenuRequested (const QPoint&)"), self.onPopupMenu)
		
		# shortcut only actions
		self.autoCompletionAction = CommonWidgets.TestermanAction(self, "Auto completion", self.autoCompletion) 
		self.autoCompletionAction.setShortcut(Qt.CTRL + Qt.Key_Space)
		self.autoCompletionAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.autoCompletionAction)
#		self.callTipAction = CommonWidgets.TestermanAction(self, "Tool tip", self.showTip) 
#		self.callTipAction.setShortcut(Qt.CTRL + Qt.Key_Shift + Qt.Key_Space) #does not work... (ctrl + shift + space)
#		self.callTipAction.setShortcutContext(Qt.WidgetShortcut)
#		self.addAction(self.callTipAction)
		self.autoCompleteTemplate = CommonWidgets.TestermanAction(self, "Auto complete template", self.autoCompleteTemplate) 
		self.autoCompleteTemplate.setShortcut(Qt.CTRL + Qt.Key_J)
		self.autoCompleteTemplate.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.autoCompleteTemplate)

	def preparePluginsMenu(self):
		self.pluginsMenu.clear()
		for (label, actions) in self._documentEditor.getCategorizedPluginActions():
			menu = self.pluginsMenu.addMenu(label)
			for action in actions:
				menu.addAction(action)

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
		if delta < 0:
			self.zoomOut(1) # does nothing when the text was already set with a currentFont ???!
		else:
			self.zoomIn(1)
		# Updates the width of the line counter margin as well.
		self.onLinesChanged()
		wheelEvent.accept()

	def getCode(self):
		"""
		Return the code being edited.
		
		@rtype: QString
		@returns: the current code being edited
		"""
		# Get rids of possible ^M, etc.
		self.convertEols(self.eolMode())
		return self.text()

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

	def splitView(self):
		self._documentEditor.splitView()

	def closeView(self):
		self._documentEditor.closeView()

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
		#template = self.templateManager.byName(templateName)
		#if template is not None:
		#	code = template.activate()
		#	if code is not None:
		#		self.beginUndoAction()
		#		self.removeSelectedText()
		#		indent = self.getLineIndentation()
		#		self.insert(code.replace("\n", "\n" + indent))
		#		self.endUndoAction()
		#		self.outlineMaybeUpdated()
		#		return True
		return False

	def autoCompleteTemplate(self):
		"""
		Add template code using shortcut (shortcut then ctrl+j)
		"""
		#self.getLineIndentation()
		#(lineFrom, _, lineTo, _) = self.getSelection()
		#if lineFrom == -1 and lineTo == -1: # no actual selection
		#	currentLine, currentIndex = self.getCursorPosition()
		#	previousWord = self.getPreviousWord()
		#	#log("previous word:%s" % previousWord)
		#	if previousWord != "":
		#		template = self.templateManager.byShortcut(previousWord)
		#		if template is not None:
		#			currentLine, currentIndex = self.getCursorPosition()
		#			self.setSelection(currentLine, currentIndex-len(previousWord), currentLine, currentIndex)
		#			if not self.templateCodeWriter(template.name):
		#				self.setCursorPosition(currentLine, currentIndex)
		
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
		#FIXME: make sure we stop the timer when switching documents
		#self._outlineUpdateTimer.start(0)

	def onTextChanged(self):
		autocompletion = QSettings().value('editor/autocompletion', QVariant(False)).toBool()
		if autocompletion:
			self._autoCompletionTimer.start(500)
	
	def focusInEvent(self, event):
		"""
		Overriden from QWidget.
		Emit a signal when focused so that the world can know which editor
		is the active one (useful for multiview document editor).
		"""
		self.emit(SIGNAL("focused"), self)
		return sci.QsciScintilla.focusInEvent(self, event)

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
		labels.append('Name')
		labels.append('Value')
		self.setHeaderLabels(labels)
		self.setRootIsDecorated(False)
		self.setSortingEnabled(True)
		self.header().setClickable(True)
		# Default sort
		self.sortItems(0, Qt.AscendingOrder)
		self.setAlternatingRowColors(True)

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
				CommonWidgets.systemError(self, "Unable to save parameter file: " + str(e))
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
				CommonWidgets.systemError(self, "Unable to load parameter file: " + str(e))
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

################################################################################
# Group Selection
################################################################################

class WGroupTreeWidgetItem(QTreeWidgetItem):
	"""
	This item interfaces a metadata group element (dict[name, description]).
	"""
	def __init__(self, group, parent = None):
		"""
		@type  group: dict[unicode] of unicode
		@param group: a representation of a parameter, as performed by a metadataModel:
											a dict of 'name', 'description'.
		"""
		QTreeWidgetItem.__init__(self, parent)
		self.group = group
		self.setToolTip(1, self.group['description'])
		self.setText(1, self.group['name'])
		self.setText(2, self.group['description'])
#		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)

class WGroupSelector(QTreeWidget):
	"""
	Using a documentModel.metadataModel.getGroups() as an input, enables to
	select groups for a run.

	This is not a view over a model; just an interface to modify things, with
	exploitable outputs:
	- getDeselectedGroups(): return the deselected groups only
	"""
	def __init__(self, groups, deselectedGroups, parent = None):
		"""
		We make a copy of the input groups dict, since we're about to reuse it for our own purposes.
		"""
		QTreeWidget.__init__(self, parent)
		self.groups = copy.deepcopy(groups)
		self.__createWidgets()
		self.rebuildTree(deselectedGroups)

	def __createWidgets(self):
		labels = QStringList()
		labels.append('')
		labels.append('Name')
		labels.append('Description')
		self.setHeaderLabels(labels)
		self.setRootIsDecorated(False)
		self.setSortingEnabled(True)
		self.header().setClickable(True)
		# Default sort
		self.sortItems(1, Qt.AscendingOrder)
		self.setAlternatingRowColors(True)

		# Context menu to check/uncheck all
		self.menu = QMenu(self)
		self.menu.addAction(CommonWidgets.TestermanAction(self, "Check all", self.checkAll))
		self.menu.addAction(CommonWidgets.TestermanAction(self, "Uncheck all", self.uncheckAll))

		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.connect(self, SIGNAL("customContextMenuRequested (const QPoint&)"), self.onPopupMenu)

	def onPopupMenu(self, event):
		self.menu.popup(QCursor.pos())

	def rebuildTree(self, deselectedGroups):
		"""
		Rebuild the tree according to the current "model"
		"""
		self.clear()

		for (name, group) in self.groups.items():
			item = WGroupTreeWidgetItem(group, self)
			# selected by defaut
			item.setCheckState(0, (not name in deselectedGroups) and Qt.Checked )

		# We resort the view
		self.sortItems(self.sortColumn(), self.header().sortIndicatorOrder())
		self.resizeColumnToContents(0) # checkbox
		self.resizeColumnToContents(1) # group name
		self.setColumnWidth(2, 200) # description

	def getDeselectedGroups(self):
		"""
		Returns a list containing deselected groups names.
		@rtype: list of unicode
		@returns: a list of deselected groups
		"""
		ret = []
		for i in range(self.topLevelItemCount()):
			item = self.topLevelItem(i)
			group = item.group
			if not item.checkState(0) == Qt.Checked:
				ret.append(group['name'])
		return ret

	def checkAll(self):
		for i in range(self.topLevelItemCount()):
			item = self.topLevelItem(i)
			item.setCheckState(0, Qt.Checked)
	
	def uncheckAll(self):
		for i in range(self.topLevelItemCount()):
			item = self.topLevelItem(i)
			item.setCheckState(0, Qt.Unchecked)

class WGroupSelectorDialog(QDialog):
	"""
	A WGroupSelector embedded within a dialog.
	"""
	def __init__(self, metadataModel, deselectedGroups = [], parent = None):
		"""
		metadataModel is the ATS' metadata model, containing the current list of possible groups.
		deselectedGroups contains the previously deselected groups.
		"""
		QDialog.__init__(self, parent)
		self.metadataModel = metadataModel
		self.__createWidgets(deselectedGroups)

	def sizeHint(self):
		return QSize(500, 300)

	def __createWidgets(self, deselectedGroups):
		self.setWindowTitle("Select groups to run")
		self.setWindowIcon(icon(':icons/testerman.png'))

		layout = QVBoxLayout()
		self.groupSelector = WGroupSelector(self.metadataModel.getGroups(), deselectedGroups, self)
		layout.addWidget(self.groupSelector)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.okButton = QPushButton("Run", self)
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self.okButton)
		self.cancelButton = QPushButton("Cancel", self)
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self.cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def getDeselectedGroups(self):
		return self.groupSelector.getDeselectedGroups()

###############################################################################
# Package Description/Metadata Edition
###############################################################################

class WPackageDescriptionDocumentEditor(WDocumentEditor):
	"""
	Enable to edit and manipulate a package description.
	
	This is a view over a PackageDescriptionModel (aspect: body, which is a QDomDocument).
	
	Directly interfaces interesting fields in this description:
	author, 
	description,
	entry point
	
	Also an entry point to execute the package from a selected profiles ?
	"""
	def __init__(self, documentModel, parent = None):
		WDocumentEditor.__init__(self, documentModel, parent)
		self._initialStatus = "designing"
		self.__createWidgets()
		self.filenameTemplate = "Testerman Package Description (*.xml)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelUpdated)
		self.onModelUpdated() # Refresh the displayed values

	def __createWidgets(self):
		"""
		A main WScriptEditor, plus an associated action bar at the bottom with:
		- an action button to test/run the script.
		- a button to check syntax
		"""
		layout = QVBoxLayout()
		
		self._packageNameLineEdit = QLineEdit()
		self._packageNameLineEdit.setReadOnly(True)
		self._authorLineEdit = QLineEdit()
		self._defaultScriptLineEdit = QLineEdit()
		self._descriptionTextEdit = QTextEdit()
		
		self._statusComboBox = QComboBox()
		self._statusComboBox.addItems([ "designing", "testing", "ready" ])
		
		# Let's reference the different isModified() functions
		self._editorModifiedFunctions = [ 
			lambda: self._authorLineEdit.isModified(), 
			lambda: self._defaultScriptLineEdit.isModified(), 
			lambda: self._descriptionTextEdit.document().isModified()
		]
		self.connect(self._authorLineEdit, SIGNAL('textChanged(const QString&)'), self.maybeModified)
		self.connect(self._defaultScriptLineEdit, SIGNAL('textChanged(const QString&)'), self.maybeModified)
		self.connect(self._statusComboBox, SIGNAL('currentIndexChanged(const QString&)'), self.maybeModified)
		self.connect(self._descriptionTextEdit, SIGNAL('textChanged()'), self.maybeModified)

		form = QFormLayout()
		form.setMargin(2)
		form.addRow("Package:", self._packageNameLineEdit)
		form.addRow("Author:", self._authorLineEdit)
		form.addRow("Default script:", self._defaultScriptLineEdit)
		form.addRow("Status:", self._statusComboBox)
		form.addRow("Description:", self._descriptionTextEdit)
		layout.addLayout(form)

		# The action bar below
		actionLayout = QHBoxLayout()

		# Actions associated with package edition:
		# documentation via documentation plugins,
		# run with several options (session parameters, scheduling)
		# By default, icon sizes are 24x24. We resize them to 16x16 to avoid too large buttons.
		# Documentation actions - needs switching to a plugin architecture
		self.documentationButton = QToolButton()
		self.documentationButton.setIcon(icon(':/icons/documentation'))
		self.documentationButton.setIconSize(QSize(16, 16))
		self.documentationPluginsMenu = QMenu('Documentation', self)
		self.connect(self.documentationPluginsMenu, SIGNAL("aboutToShow()"), self.prepareDocumentationPluginsMenu)
		self.documentationButton.setMenu(self.documentationPluginsMenu)
		self.documentationButton.setPopupMode(QToolButton.InstantPopup)

		actionLayout.addStretch()
		actionLayout.addWidget(self.documentationButton)

		actionLayout.setMargin(2)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def maybeModified(self):
		"""
		Scan for a change in the multiple local editors so that 
		we can fire a modification status change, if needed.
		"""
		for isModified in self._editorModifiedFunctions:
			if isModified():
				# Something has been modified.
				self.model.onBodyModificationChanged(True)
				return
		if self._statusComboBox.currentText() != self._initialStatus:
			self.model.onBodyModificationChanged(True)
			return
		
		# Back to unmodified flag
		self.model.onBodyModificationChanged(False)

	def onModelUpdated(self):
		root = self.model.getBodyModel().documentElement()
		self._packageNameLineEdit.setText(self.model.getPackageName())
		self._authorLineEdit.setText(root.firstChildElement('author').text())
		self._defaultScriptLineEdit.setText(root.firstChildElement('default-script').text())
		self._descriptionTextEdit.setText(root.firstChildElement('description').text())
		self._initialStatus = root.firstChildElement('status').text()
		self._statusComboBox.setCurrentIndex(self._statusComboBox.findText(self._initialStatus))
		self.model.onBodyModificationChanged(False)

	def aboutToSave(self):
		return True

	def _updateModelElement(self, name, value):
		# Can't update a text value directly with QtXml....
		# We have to create a new child and replace the previous one
		doc = self.model.getBodyModel()
		root = doc.documentElement()
		oldChild = root.firstChildElement(name)
		newChild = doc.createElement(name)
		newChild.appendChild(doc.createTextNode(value))
		if oldChild.isNull():
			root.appendChild(newChild)
		else:
			root.replaceChild(newChild, oldChild)

	def updateModel(self):
		"""
		Commit the changes to the model.
		"""
		author = self._authorLineEdit.text()
		defaultScript = self._defaultScriptLineEdit.text()
		status = self._statusComboBox.currentText()
		description = self._descriptionTextEdit.toPlainText()
		self._updateModelElement('author', author)
		self._updateModelElement('default-script', defaultScript)
		self._updateModelElement('status', status)
		self._updateModelElement('description', description)

	def prepareDocumentationPluginsMenu(self):
		self.documentationPluginsMenu.clear()
		for action in getDocumentationPluginActions(self.model, self.model.getDocumentType(), self):
			log("adding action in plugin contextual menu..." + unicode(action.text()))
			self.documentationPluginsMenu.addAction(action)

	def aboutToDocument(self):
		# Nothing to do
		return True

	def getIcon(self):
		"""
		Returns an icon representing the edited object.
		"""
		return icon(':/icons/item-types/package-metadata')

DocumentManager.registerDocumentEditorClass(DocumentModels.TYPE_PACKAGE_METADATA, WPackageDescriptionDocumentEditor)


###############################################################################
# Profile Management
###############################################################################

class WProfileValueTreeWidgetItem(QTreeWidgetItem):
	def __init__(self, parent, parameter):
		"""
		parameter is a dict[unicode] of unicode containing "name", "description", "default", "value"
		
		The initial name is used as a key for the model, so we save it in a safe place as soon as the item is created.
		"""
		QTreeWidgetItem.__init__(self, parent)
		self.parameter = parameter
		self.key = parameter['name']
		self.columns = [ 'name', 'type', 'description', 'default', 'value' ]
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
		self.setText(0, self.parameter['name'])
		self.setText(1, self.parameter['type'])
		self.setText(2, self.parameter['description'])
		self.setText(3, self.parameter['default'])
		self.setText(4, self.parameter['value'])
		self._updateDisplayedState()

	def _updateDisplayedState(self):
		if self.parameter['implicit']:
			for i in range(len(self.columns)):
				self.setForeground(i, QBrush(Qt.lightGray))
			self.setToolTip(0, "This parameter has not been explicitly set in this profile yet. This is the value from the default profile.")
		elif self.parameter['extra']:
			for i in range(len(self.columns)):
				self.setForeground(i, QBrush(Qt.darkRed))
			self.setToolTip(0, "This parameter is not defined in the script properties. You may remove it.")
		else:
			for i in range(len(self.columns)):
				self.setForeground(i, QBrush())
			self.setToolTip(0, QString())
		
	
	def _data(self, column, role):
		name = self.columns[column]
		if role == Qt.DisplayRole:
			return QVariant(self.parameter[name])
		if role == Qt.EditRole:
			return QVariant(self.parameter[name])
		return QVariant()

	def setData(self, column, role, value):
		val = unicode(value.toString())
		name = self.columns[column]
		if role == Qt.EditRole:
			if name == 'value':
				self.parameter[name] = val
				self.parameter['implicit'] = False # this parameter is no longer implicit now it has been explicitly set
				self._updateDisplayedState()
				return QTreeWidgetItem.setData(self, column, role, value)
		else:
			return QTreeWidgetItem.setData(self, column, role, value)

class WProfileValuesEditor(QTreeWidget):
	"""
	An editor to edit the script parameters values for the profile.
	Displays multiple columns: name, description, default value, and profile value.
	Only the profile value is editable.
	The user cannot add or delete new parameters. Instead, he/she may "reapply"
	the script parameters to the profile (to create/delete missing parameters)
	and/or reassign default values.
	"""
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self._scriptMetadataModel = None
		self.__createWidgets()

	def __createWidgets(self):
		self.setRootIsDecorated(0)
		self.labels = [ 'Name', 'Type', 'Description', 'Default value', 'Profile value' ]
		self.setSortingEnabled(1)
		# Default sort - should be read from the QSettings.
		self.sortItems(0, Qt.AscendingOrder)
#		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		labels = QStringList()
		for l in self.labels:
			labels.append(l)
		self.setHeaderLabels(labels)
#		self.setContextMenuPolicy(Qt.CustomContextMenu)
#		self.connect(self, SIGNAL("customContextMenuRequested(const QPoint&)"), self.onPopupMenu)

#		self.setAcceptDrops(True)
		
		self.setAlternatingRowColors(True)
		
		self.connect(self, SIGNAL('itemChanged(QTreeWidgetItem*, int)'), self.onItemChanged)
	
	def onItemChanged(self, item, column):
		# We should be more specific, updating only one particular item instead of everything.
		self.updateModel()

	def setMetadataModel(self, scriptMetadataModel):
		"""
		Sets the associated metadata model.
		
		The widget updates the view according to it, by displaying
		default values/description/type associated to the profile's values,
		automatically adding missing values,
		and identifying spurious values.
		"""
		if self._scriptMetadataModel:
			self.disconnect(self._scriptMetadataModel, SIGNAL("metadataUpdated()"), self.onMetadataModelUpdated)
		self._scriptMetadataModel = scriptMetadataModel
		if self._scriptMetadataModel:
			self.connect(self._scriptMetadataModel, SIGNAL("metadataUpdated()"), self.onMetadataModelUpdated)
		self.onMetadataModelUpdated()

	def onMetadataModelUpdated(self):
		"""
		Updates/completes the view according to the script's parameters/signature.
		"""
		if self._scriptMetadataModel:
			templateModel = self._scriptMetadataModel.getParameters()
		else:
			templateModel = {}

		localModel = self._model.getParameters()

		# Now, construct the tree, merging the info from the metadata model and the current profile
		self.clear()

		displayed = []		
		# Construct the tree based on the "template", ie the script expected parameters
		for k, v in templateModel.items():
			d = {}
			if k in localModel:
				d = dict(name = k, value = localModel[k], description = v['description'], default = v['default'], type = v['type'], extra = False, implicit = False)
			else:
				# in the template, not in the profile, initialize it to the defaut value
				d = dict(name = k, value = v['default'], description = v['description'], default = v['default'], type = v['type'], extra = False, implicit = True)
			displayed.append(k)
			WProfileValueTreeWidgetItem(self, d)

		# Now complete with what was not displayed, but available in the profile model (extra parameters)
		for k, v in localModel.items():
			if not k in displayed:
				d = dict(name = k, value = v, description = '', default = '', type = 'string', extra = True, implicit = False)
				WProfileValueTreeWidgetItem(self, d)
		

	def setModel(self, profileModel, scriptMetadataModel = None, applyMetadataModel = False):
		"""
		The scriptParametersModel is optional and provided to fill the description and default values
		for entries that exist in profileModel too.
		"""
		self._model = profileModel

		self.clear()
		
		localModel = profileModel.getParameters()
		templateModel = scriptMetadataModel and scriptMetadataModel.getParameters() or {}

		if applyMetadataModel:
			displayed = []		
			# Now, construct the tree, merging the info from the metadata model and the current profile
			if templateModel:
				# Construct the tree based on the "template", ie the script expected parameters
				for k, v in templateModel.items():
					d = {}
					if k in localModel:
						d = dict(name = k, value = localModel[k], description = v['description'], default = v['default'], type = v['type'], extra = False, implicit = False)
					else:
						# in the template, not in the profile, initialize it to the defaut value - implicitly added
						d = dict(name = k, value = v['default'], description = v['description'], default = v['default'], type = v['type'], extra = False, implicit = True)
					displayed.append(k)
					WProfileValueTreeWidgetItem(self, d)

			# Now complete with what was not displayed, but available in the profile model (extra parameters)
			for k, v in localModel.items():
				if not k in displayed:
					d = dict(name = k, value = v, description = '(unknown)', default = '', type = 'string', extra = True)
					WProfileValueTreeWidgetItem(self, d)

		else:
			# We don't have a merge strategy. Just display the elements of the local model,
			# with the description and default value from the scriptMetadataModel, if any
			for k, v in localModel.items():
				if k in templateModel:
					d = dict(name = k, value = v, description = templateModel[k]['description'], default = templateModel[k]['default'], type = templateModel[k]['type'], extra = False, implicit = False)
				else:
					d = dict(name = k, value = v, description = '', default = '', type = 'string', extra = True, implicit = False)
				WProfileValueTreeWidgetItem(self, d)
				
		# We re-sort the items according to the current sorting parameters
		self.sortItems(self.sortColumn(), self.header().sortIndicatorOrder())
	
	def updateModel(self):
		"""
		Writes the displayed/updated values back to the model.
		"""
		self._model.setParameters(self.getProfileValues())
		
	def getProfileValues(self):
		"""
		Returns a dict of the currently set values.
		"""
		parameters = {}
		# Browse the top level items
		for i in range(self.topLevelItemCount()):
			item = self.topLevelItem(i)
			# Granted, this is dirty coding. To refactor one day.
			if not item.parameter['implicit']:
				key = item.text(0)
				value = item.text(4)
				parameters[key] = value
		return parameters


class WProfilesManager(QWidget):
	"""
	A profiles editor/manager that is embedded within
	a ATS or Campaign editor.
	
	Enables to add/delete/update profiles that
	are associated with this script, and maintains a
	list of available profiles for a run.
	
	TODO: split this widget into an actual profiles manager and a widget that interfaces it.
	"""

	class WProfileSelector(QComboBox):
		"""
		This inner class is actually a small part of the Profile manager widget
		that can be embedded anywhere.
		
		It displays the possible available profiles for the associated
		script, and communicate with its associated manager to display
		the correct values when a profile is selected.
		"""
		def __init__(self, profileManager, parent = None):
			QComboBox.__init__(self, parent)
			self._profileManager = profileManager
			self.connect(self, SIGNAL('activated(int)'), self.onActivated)
			self._refreshEntries()

		def _refreshEntries(self, selected = None):
			self.clear()
			self._entries = self._profileManager.getAvailableProfiles()
			l = self._entries.keys()
			l.sort()
			i = 0
			for name in l:
				self.addItem(name)
				if name == selected:
					self.setCurrentIndex(i)
				i += 1

		def showPopup(self):
			"""
			Reimplemented to reload the available profiles in real time.
			"""
			current = unicode(self.currentText())
			self._refreshEntries(current)
			return QComboBox.showPopup(self)

		def getProfileModel(self):
			"""
			Returns the profile model of the currently selected profile
			"""
			return self._entries.get(unicode(self.currentText()))

		def onActivated(self, index):
			self.emit(SIGNAL("profileSelected"), self.getProfileModel())

	DEFAULT_PROFILE_NAME = '(default profile)'

	def __init__(self, scriptModel, parent = None):
		QWidget.__init__(self, parent)

		# ProfileManager core part
		# Knowing the associated MetadataModel is useful to reapply the template
		# and/or to display in-use/deprecated values in a template, as well as type/description/etc
		self._associatedScriptModel = scriptModel
		self._profileModels = {} # indexed by a short/friendly name
		# Initialize the profile models list
		self._updateProfileModelsCache()

		# ProfileManager widget part
		self.__createWidgets()
		self._profileSelector = self.WProfileSelector(profileManager = self)
		self.connect(self._profileSelector, SIGNAL('profileSelected'), self.onProfileSelected)

		# Force a selection of the default profile
		self.setModel(self.getDefaultProfile())

	def _updateProfileModelsCache(self):
		"""
		Update the local cache from what is avaible from the server.
		"""
		if not self.DEFAULT_PROFILE_NAME in self._profileModels:
			# A default profile
			default = DocumentModels.ProfileModel()
			default.setDocumentSource('<?xml version="1.0"?><profile></profile>')
			default.setReadOnly(True)
			default.setDescription("Default profile")
			default.setFriendlyName(self.DEFAULT_PROFILE_NAME)

			self._profileModels[self.DEFAULT_PROFILE_NAME] = default

		# Then load from the repository
		# Then there may be a list of profiles from the server
		if self._associatedScriptModel.isRemote():
			try:
				l = getProxy().getDirectoryListing(unicode(self._associatedScriptModel.getUrl().path()) + '/profiles')
				if l is None:
					l = []
			except Exception, e:
				log('Cannot get profiles for this script: %s' % e)
				l = []
			
			for name in [ x['name'][:-len('.profile')] for x in l if x['type'] == 'profile']:
				if not name in self._profileModels:
					# New profile on the server, not in our local cache - let's load it
					profileUrl = QUrl(self._associatedScriptModel.getUrl().toString() + '/profiles/%s.profile' % name)
					try:
						profile = getProxy().getFile(unicode(profileUrl.path()))
						info = getProxy().getFileInfo(unicode(profileUrl.path()))
					except:
						profile = None
						info = None
					
					if profile:
						pm = DocumentModels.ProfileModel()
						pm.setDocumentSource(profile)
						pm.setFriendlyName(name)
						pm.setSavedAttributes(url = profileUrl, timestamp = info['timestamp'])
						self._profileModels[name] = pm
						log("Loaded profile %s" % profileUrl)
					else:
						log("WARNING: unable to load profile %s" % profileUrl)
				else:
					# The profile was already loaded. We should check if it was updated or not...
					# TODO
					pass

		# We may keep additional profiles that were not saved yet.

	def getDefaultProfile(self):
		return self._profileModels.get(self.DEFAULT_PROFILE_NAME)

	def getProfileSelector(self):
		return self._profileSelector

	def onProfileSelected(self, profileModel):
		"""
		A new profile has been selected.
		Update the currently displayed model in the profiles editor.
		"""
		self.setModel(profileModel)
	
	def __createWidgets(self):
		layout = QVBoxLayout()
		# First, display the current profile properties
		l = QHBoxLayout()
		l.addWidget(QLabel("Description:"))
		self.profileDescription = QLineEdit()
		l.addWidget(self.profileDescription)
		l.setMargin(2)
		layout.addLayout(l)

		self.valuesEditor = WProfileValuesEditor()
		layout.addWidget(self.valuesEditor)
		
		self.statusLabel = QLabel()
		
		self.newAction = CommonWidgets.TestermanAction(self, "&New", self.newProfile, "Create a new profile for this script")
		self.reapplyTemplateAction = CommonWidgets.TestermanAction(self, "&Clean", self.reapplyProfileTemplate, "Remove unused parameters")
		self.saveAction = CommonWidgets.TestermanAction(self, "&Save", self.saveProfile, "Save the current profile")
		self.saveAsAction = CommonWidgets.TestermanAction(self, "Save &As", self.saveProfileAs, "Save the current profile as a new name")
		self.deleteAction = CommonWidgets.TestermanAction(self, "&Delete", self.deleteProfile, "Delete the current profile")
		
		self.newButton = QToolButton()
		self.newButton.setDefaultAction(self.newAction)
		self.reapplyTemplateButton = QToolButton()
		self.reapplyTemplateButton.setDefaultAction(self.reapplyTemplateAction)
		self.saveButton = QToolButton()
		self.saveButton.setDefaultAction(self.saveAction)
		self.saveAsButton = QToolButton()
		self.saveAsButton.setDefaultAction(self.saveAsAction)
		self.deleteButton = QToolButton()
		self.deleteButton.setDefaultAction(self.deleteAction)
		
		# Then, display an action bar
		actionLayout = QHBoxLayout()
		actionLayout.addWidget(self.newButton)
		actionLayout.addWidget(self.statusLabel)
		actionLayout.addStretch()
		actionLayout.addWidget(self.reapplyTemplateButton)
		actionLayout.addWidget(self.saveButton)
		actionLayout.addWidget(self.saveAsButton)
		actionLayout.addWidget(self.deleteButton)
		
		layout.addLayout(actionLayout)
		self.setLayout(layout)
	
	def newProfile(self):
		"""
		Creates a new profile associated to the script.

		Saves it to the repository immediately ? Should we prevent new profile
		creations for non-repository scripts ?
		"""
		# Step 1: ask for a new name
		(name, status) = QInputDialog.getText(self, "Create a new profile", "Profile name:")
		while status and not CommonWidgets.validateDirectoryName(name):
			# Display some error message
			CommonWidgets.userError(self, "The following characters are forbidden in a profile name:\n%s" % ', '.join([x for x in CommonWidgets.RESTRICTED_NAME_CHARACTERS]))
			(name, status) = QInputDialog.getText(self, "New profile", "Profile name:")
		
		if status and not name.isEmpty():
			if not unicode(name) in self._profileModels:
				# TODO: check that the current profile is saved/save-able.
				associatedScriptPath = self._associatedScriptModel.getUrl().path()
				model = DocumentModels.ProfileModel()
				model.setFriendlyName(name)
				model.setSavedAttributes(url = QUrl('testerman://testerman%s/profiles/%s.profile' % (associatedScriptPath, name)), timestamp = time.time())
				self._profileModels[unicode(name)] = model
				
				# Select the new model as the current one
				# Quick & dirty...
				self.getProfileSelector().setEditText(name)
				self.setModel(model)
			else:
				CommonWidgets.userError(self, "This profile already exists. Please select another name.")
	
	def saveProfile(self):
		# make sure we dump the displayed info into the model
		self.updateModel() 

		filename = self.model.getUrl().path()

		# Check if there is no newer file on the server
		referenceTimestamp = 0
		info = getProxy().getFileInfo(unicode(filename))
		
		if info:
			referenceTimestamp = info['timestamp']
		if referenceTimestamp > self.model.getTimestamp():
#			# Actually, this is more than a warning popup. It proposes to force overwriting, or a little
#			# "diff" windows, or back to edition, ... something ?
			ret = QMessageBox.warning(self, "Profile updated", "The profile was updated since your last reload. Are you sure you want to want to overwrite these changes ?", 
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if ret != QMessageBox.Yes:
				return False
		
		return self._saveProfile(filename)

	def _saveProfile(self, filename):
		error = None
		try:
			# Store files as utf8
			# compress the files on the wire (requires Ws 1.3)
			ret = getProxy().putFile(self.model.getDocumentSource(), unicode(filename), useCompression = True)
			if not ret:
				error = "Please check permissions."
		except Exception, e:
			log(getBacktrace())
			error =	str(e)

		if error is None:
			QApplication.instance().get('gui.statusbar').showMessage("Profile successfully put into repository as %s" % (filename))
			# We set the timestamp on the server, not the local timestamp since the client may not be in sync with the server's time.
			info = getProxy().getFileInfo(unicode(filename))
			serverIp, serverPort = getProxy().getServerAddress()
			self.model.setSavedAttributes(url = QUrl("testerman://%s:%d%s" % (serverIp, serverPort, filename)), timestamp = info['timestamp'])
			self.model.resetModificationFlag()
			return True
		else:
			CommonWidgets.systemError(self, "Unable to save profile to repository: %s" % error)
			QApplication.instance().get('gui.statusbar').showMessage("Unable to save profile to repository: %s" % error)
			return False
	
	def saveProfileAs(self):
		"""
		Saves the currently edited model under a particular name,
		and selects it under this new name.
		"""
		# Make sure the current model is in sync with its view
		self.updateModel()
		
		# Step 1: ask for a new name
		(name, status) = QInputDialog.getText(self, "Save profile as", "Profile name:")
		while status and not CommonWidgets.validateDirectoryName(name):
			# Display some error message
			CommonWidgets.userError(self, "The following characters are forbidden in a profile name:\n%s" % ', '.join([x for x in CommonWidgets.RESTRICTED_NAME_CHARACTERS]))
			(name, status) = QInputDialog.getText(self, "Save profile as", "Profile name:")
		
		if status and not name.isEmpty():
			# TODO: (remote) overwrite check
			if not unicode(name) in self._profileModels:
				associatedScriptPath = self._associatedScriptModel.getUrl().path()
				model = DocumentModels.ProfileModel()
				model.setFriendlyName(name)

				# Copy the current model to the new one
				model.setDescription(self.model.getDescription())
				model.setDocumentSource(self.model.getDocumentSource())
				model.setSavedAttributes(url = QUrl('testerman://testerman%s/profiles/%s.profile' % (associatedScriptPath, name)), timestamp = time.time())
				
				# Attempt to save it
				if self._saveProfile(model.getUrl().path()):
					# If OK, let's register the new model into our local list
					self._profileModels[unicode(name)] = model
					# Select the new model as the current one
					self.setModel(model)
			else:
				CommonWidgets.userError(self, "This profile already exists. Please select another name.")
				# TODO: We should propose to overwrite it.
	
	def deleteProfile(self):
		ret = QMessageBox.warning(self, "Delete profile", "Are you sure you want to delete the profile %s ?" % self.model.getFriendlyName(),
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		if ret != QMessageBox.Yes:
			return False

		filename = self.model.getUrl().path()
		if getProxy().deleteProfile(unicode(filename)):
			# Remove the profile from the local view
			try:
				del self._profileModels[self.model.getFriendlyName()]
			except:
				pass
			# Select the default profile - index 0
			self.getProfileSelector().setCurrentIndex(0)
		

	def reapplyProfileTemplate(self):
		"""
		Clean up the profile by removing spurious parameters values.
		"""
		pass
	
	def setModel(self, model):
		"""
		Set the current profile's model to display.
		"""
		self.model = model
		self.profileDescription.setText(self.model.getDescription())
		self.valuesEditor.setModel(self.model)
		self.valuesEditor.setMetadataModel(self._associatedScriptModel.getMetadataModel())
		self.statusLabel.setText(model.getFriendlyName())
		# For read-only profiles, limited options
		self.saveButton.setEnabled(not self.model.isReadOnly())
		self.deleteButton.setEnabled(not self.model.isReadOnly())
		self.reapplyTemplateButton.setEnabled(not self.model.isReadOnly())

		# Also make sure that the associated profile selector displays the correct name
		self.getProfileSelector().setEditText(self.model.getFriendlyName())

	def updateModel(self):
		"""
		Commit the changes to the model.
		"""
		self.model.setDescription(unicode(self.profileDescription.text()))
		# Parameters are committed "in real time" by the values editor

	def getModel(self):
		return self.model

	def getAvailableProfiles(self):
		"""
		Returns a list of profiles available for the associated script.
		as a dict[profile short name] = ProfileModel
		
		This is a merged list from multiple sources:
		1 - profiles available on the server, associated to the current document's url
		2 - profiles that are not saved yet, only 'in memory'
		In addition, for 1, the actual profile may be not saved yet.
		
		The manager manages a cache of the repository profiles.
		"""
		# dict[friendly name] = profileModel
		self._updateProfileModelsCache()
		return self._profileModels
		
		
		
	
class WProfileDocumentEditor(WDocumentEditor):
	"""
	Enable to edit and manipulate a profile.
	
	This is a view over a ProfileModel.
	
	Directly interfaces interesting fields in this description:
	description,
	parameters
	"""
	def __init__(self, documentModel, parent = None):
		WDocumentEditor.__init__(self, documentModel, parent)
		self.__createWidgets()
		self.filenameTemplate = "Testerman Execution Profile (*.profile)"
		self.connect(self.model, SIGNAL('modificationChanged(bool)'), self.onModelModificationChanged)
		self.connect(self.model, SIGNAL('documentReplaced()'), self.onModelUpdated)
		self.onModelUpdated() # Refresh the displayed values

	def __createWidgets(self):
		"""
		Basically a QTextEdit for the description, 
		and a table to edit parameters.
		"""
		layout = QVBoxLayout()
		layout.setMargin(3)
		
		self._descriptionTextEdit = QTextEdit()
		self._parametersEditor = WProfileValuesEditor()
		
		# Let's reference the different isModified() functions
		self._editorModifiedFunctions = [ 
			lambda: self._descriptionTextEdit.document().isModified()
		]
		self.connect(self._descriptionTextEdit, SIGNAL('textChanged()'), self.maybeModified)

		layout.addWidget(QLabel("This profile is attached to: %s" % unicode(self.model.getAssociatedScriptLabel())))
		layout.addWidget(QLabel("Profile description:"))
		layout.addWidget(self._descriptionTextEdit)
		layout.addWidget(QLabel("Parameters:"))
		layout.addWidget(self._parametersEditor)

		# The action bar below
		actionLayout = QHBoxLayout()

		# Actions associated with profile edition:
		# TODO: reapply script default values fill from templates, etc
		# TODO: run the ATS with these parameters
		# By default, icon sizes are 24x24. We resize them to 16x16 to avoid too large buttons.
		self.documentationButton = QToolButton()
		self.documentationButton.setIcon(icon(':/icons/documentation'))
		self.documentationButton.setIconSize(QSize(16, 16))
		self.documentationPluginsMenu = QMenu('Documentation', self)
		self.connect(self.documentationPluginsMenu, SIGNAL("aboutToShow()"), self.prepareDocumentationPluginsMenu)
		self.documentationButton.setMenu(self.documentationPluginsMenu)
		self.documentationButton.setPopupMode(QToolButton.InstantPopup)

		self.resetButton = QPushButton("Reset to defaults")
		self.connect(self.resetButton, SIGNAL("clicked()"), self.resetToDefaults)

		self.reapplyTemplateButton = QPushButton("Load parameters from script")
		self.connect(self.reapplyTemplateButton, SIGNAL("clicked()"), self.reapplyTemplate)

		actionLayout.addStretch()
#		actionLayout.addWidget(self.documentationButton)
#		actionLayout.addWidget(self.resetButton)
		actionLayout.addWidget(self.reapplyTemplateButton)

		actionLayout.setMargin(2)
		layout.addLayout(actionLayout)
		layout.setMargin(0)
		self.setLayout(layout)

	def maybeModified(self):
		"""
		Scan for a change in the multiple local editors so that 
		we can fire a modification status change, if needed.
		"""
		for isModified in self._editorModifiedFunctions:
			if isModified():
				# Something has been modified.
				self.model.onBodyModificationChanged(True)
				return
		
		# Back to unmodified flag
		self.model.onBodyModificationChanged(False)

	def onModelUpdated(self):
		self._descriptionTextEdit.setText(self.model.getDescription())
		self._parametersEditor.setModel(self.model, self.getAssociatedScriptMetadataModel())
		self.model.onBodyModificationChanged(False)

	def aboutToSave(self):
		return True

	def updateModel(self):
		"""
		Commit the changes to the model.
		"""
		description = self._descriptionTextEdit.toPlainText()
		self.model.setDescription(unicode(description))
		self.model.setParameters(self._parametersEditor.geProfileValues())

	def prepareDocumentationPluginsMenu(self):
		self.documentationPluginsMenu.clear()
		for action in getDocumentationPluginActions(self.model, self.model.getDocumentType(), self):
			log("adding action in plugin contextual menu..." + unicode(action.text()))
			self.documentationPluginsMenu.addAction(action)

	def aboutToDocument(self):
		# Nothing to do
		return True

	def getIcon(self):
		"""
		Returns an icon representing the edited object.
		"""
		return icon(':/icons/item-types/profile')
	
	## Specific to this widget
	def getAssociatedScriptMetadataModel(self):
		# Load the script from the server
		scriptUrl = self.model.getAssociatedScriptUrl()
		if scriptUrl:
			path = scriptUrl.path()
			script = getProxy().getFile(unicode(path))
			if script:
				# Use the document model class registry to find the correct DocumentModel class to use
				filename = os.path.split(unicode(path))[1]
				documentModelClass = DocumentModels.getDocumentModelClass(filename)
				if not documentModelClass:
					return None
				scriptModel = documentModelClass()
				scriptModel.setDocumentSource(script)
				return scriptModel.getMetadataModel()
		return None
	
	def reapplyTemplate(self):
		"""
		Loads the script parameters from the associated script, 
		then adds the missing entries to the model, with a default value.
		"""
		self._parametersEditor.setModel(self.model, self.getAssociatedScriptMetadataModel(), True)
	
	def resetToDefaults(self):
		pass

DocumentManager.registerDocumentEditorClass(DocumentModels.TYPE_PROFILE, WProfileDocumentEditor)
