# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009,2010 QTesterman contributors
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

from PyQt4.Qt import *

import os.path
import time

from Base import *
import CommonWidgets
import DocumentModels

# A WDocumentManager is a notebook that opens WDocument objects.
# It hosts WDocument objects that are typically defined in Editors.py


###############################################################################
# Document Editors registrations
###############################################################################

DocumentEditorClasses = []

def registerDocumentEditorClass(documentType, documentEditorClass):
	"""
	Registers an editor class as the one to be used to edit
	a model whose type is documentType.
	
	Registering an editor for multiple document types is possible.
	Registering multiple editors for the same document type is also possible.
	"""
	global DocumentEditorClasses
	DocumentEditorClasses.append({'documentType': documentType, 'class': documentEditorClass})

def getDocumentEditorClass(documentModel):
	"""
	For a given document model instance,
	returns a list of suitable editor classes for it.
	"""
	ret = [x['class'] for x in DocumentEditorClasses if x['documentType'] == documentModel.getDocumentType()]
	return ret


###############################################################################
# Main Document Manager: a notebook widget opening/closing documents.
###############################################################################

class WDocumentManager(CommonWidgets.WEnhancedTabWidget):
	"""
	This is a notebook managing multiple WDocument (Module, Campaign, Ats).
	Provides additional methods to open new scripts/modules from outside the widget.
	
	emit:
	documentUrlsUpdated() whenever a doc url was changed.
	"""
	def __init__(self, parent = None):
		CommonWidgets.WEnhancedTabWidget.__init__(self, parent)
		self.__createWidgets()
		QApplication.instance().set('gui.documentmanager', self)

	def __createWidgets(self):
		# Additional indirection - maybe one day this won't we a tab anymore
		self.tab = self
		self.setDocumentMode(True)
		self.connect(self.tab, SIGNAL('currentChanged(int)'), self.onCurrentDocumentChanged)
		self.connect(self.tab, SIGNAL('tabCloseRequested(int)'), self.closeTab)
		self.connect(self.tab, SIGNAL('tabExpandRequested(int)'), self.expandTab)

	def onCurrentDocumentChanged(self, index):
		wdocument = self.tab.widget(index)
		if wdocument:
			url = wdocument.model.getUrl()
			QApplication.instance().get('gui.statusbar').setFileLocation(url)
			self.checkForCurrentDocumentUpdates()
		else:
			QApplication.instance().get('gui.statusbar').setFileLocation("")
	
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
		fileTimestamp = None
		contents = None

		if url.scheme() == 'file':
			log("Opening local file: %s" % url.toString())
			try:
				path = url.toLocalFile()
				f = open(unicode(path), 'r')
				contents = f.read()
				f.close()
				fileTimestamp = os.stat(unicode(path)).st_mtime
			except Exception, e:
				CommonWidgets.systemError(self, 'Unable to open %s: %s' % (unicode(path), str(e)))
				return False

		elif url.scheme() == 'testerman':
			log("Opening remote file: %s" % url.toString())
			try:
				path = url.path() # ignore the server
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

		# Now, creates a model based on the file to open
		filename = os.path.split(unicode(path))[1]
		documentModelClass = DocumentModels.getDocumentModelClass(filename)
		if not documentModelClass:
			CommonWidgets.systemError(self, 'Unable to detect file type. Not opening %s' % unicode(path))
			return False
		
		model = documentModelClass()
		model.setDocumentSource(contents)
		model.setSavedAttributes(url = url, timestamp = fileTimestamp)
		return self.openTab(model)

	def openTab(self, documentModel):
		"""
		Opens a new tab with an editor editing the document model.
		"""
		# Find an editor to edit the model
		documentEditorClasses = getDocumentEditorClass(documentModel)
		if not documentEditorClasses:
			CommonWidgets.systemError(self, 'Unable to find a suitable editor to edit %s' % documentModel.getName())
			return False
		elif len(documentEditorClasses) > 1:
			log("Multiple editors found to edit %s. Selecting the first one." % documentModel.getName())
		documentEditorClass = documentEditorClasses[0]
		
		documentEditor = documentEditorClass(documentModel, self.tab)
		
		name = documentModel.getShortName()
		tabIndex = self.tab.addTab(documentEditor, documentEditor.getIcon(), name)
		self.tab.setTabToolTip(tabIndex, documentModel.getUrl().toString())
		documentEditor.setTabWidget(self.tab)

		#We should not do this but it doesn't work without for the first tab.
		self.tab.emit(SIGNAL('currentChanged(int)'), tabIndex)
		# Set the focus on this tab
		self.tab.setCurrentIndex(tabIndex)
		self.connect(documentModel, SIGNAL('urlUpdated()'), self.documentUrlsUpdated)
		self.documentUrlsUpdated()

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
		if not self.tab.currentWidget():
			return
		
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
		contents = None
		fileTimestamp = None

		if model.isRemote():
			log("Reloading remote file...")
			path = model.getUrl().path()
			contents = getProxy().getFile(unicode(path))
			info = getProxy().getFileInfo(unicode(path))
			if contents and info:
				fileTimestamp = info['timestamp']
			else:
				CommonWidgets.systemError(self, "Unable to reload file from the repository: the file does not seem to exist anymore")
		else:
			log("Reloading local file...")
			try:
				path = model.getUrl().toLocalFile()
				f = open(unicode(path), 'r')
				contents = f.read()
				f.close()
				fileTimestamp = os.stat(unicode(path)).st_mtime
			except Exception, e:
				CommonWidgets.systemError(self, 'Unable to open %s: %s' % (model.getUrl().toString(), unicode(e)))

		if contents is not None and fileTimestamp is not None:
			try:
				model.setDocumentSource(contents)
				model.setSavedAttributes(url = model.getUrl(), timestamp = fileTimestamp)
				model.resetModificationFlag()
				QApplication.instance().get('gui.statusbar').showMessage('Document reloaded.', 5000)
			except Exception, e:
				CommonWidgets.systemError(self, 'Unable to reload %s: %s' % (model.getUrl().toString(), unicode(e)))

	def newAts(self):
		"""
		Open a new tab with an empty (or templated ?) script.
		"""
		model = DocumentModels.AtsModel()
		model.setSavedAttributes(url = QUrl('unsaved:///%s' % self.getNewName('new ats')), timestamp = time.time())
		model.setDocumentSource('# ATS Script for Testerman\n')
		self.openTab(model)

	def newCampaign(self):
		"""
		Open a new tab with an empty (or templated ?) campaign script.
		"""
		model = DocumentModels.CampaignModel()
		model.setSavedAttributes(url = QUrl('unsaved:///%s' % self.getNewName('new campaign')), timestamp = time.time())
		model.setDocumentSource('# Campaign description file for Testerman\n')
		self.openTab(model)

	def newModule(self):
		"""
		Open a new tab with an empty (or templated ?) module.
		"""
		model = DocumentModels.ModuleModel()
		model.setSavedAttributes(url = QUrl('unsaved:///%s' % self.getNewName('new module')), timestamp = time.time())
		model.setDocumentSource('# Module file for Testerman\n')
		self.openTab(model)

	def documentUrlsUpdated(self):
		"""
		Slot called whenever an URL of an open document was updated.
		We forward the signal once.
		"""
		self.emit(SIGNAL('documentUrlsUpdated()'))

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

	def saveCurrentLocalCopyAs(self):
		"""
		Retrieve the current tabbed WScript, and forward the save event
		If asFilename is None, save using the existing filename.
		"""
		self.tab.currentWidget().saveAs(copy = True)

	def closeTab(self, index):
		"""
		Close the current tab.
		Should verify that the file has not been changed...
		"""
		wdocument = self.tab.widget(index)
		if wdocument.model.isModified():
			ret = QMessageBox.warning(self, getClientName(), "Do you want to save the changes you made to %s ?" % wdocument.model.getShortName(), QMessageBox.Yes,  QMessageBox.No, QMessageBox.Cancel)
			if ret == QMessageBox.Yes:
				if not wdocument.save():
					return
			elif ret == QMessageBox.Cancel:
				return
		self.tab.removeTab(index)
		self.documentUrlsUpdated()
	
	def expandTab(self, index):
#		self.tab.setCurrentIndex(index)
		QApplication.instance().get('gui.mainwindow').toggleMaximizeCentralWidget()

	def saveCurrentToRepositoryAs(self):
		self.tab.currentWidget().saveToRepositoryAs()		

