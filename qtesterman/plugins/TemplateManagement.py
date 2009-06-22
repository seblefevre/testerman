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
# Provides several common patterns, functions, and classes
# to build template-based plugins.
##

from PyQt4.Qt import *
import PyQt4.QtWebKit as QtWebKit

from Base import *
import CommonWidgets

import airspeed

import copy
import os


##############################################################################
# Tools
##############################################################################

def html_escape(s):
	"""
	The usual escape and transformations to turns a string
	into something more (X)HTML compliant.
	"""
	print ">> html_escape: %s" % repr(s)
	s = s.replace("&", "&amp;").strip()
	s = s.replace("<", "&lt;")
	s = s.replace(">", "&gt;")
	s = s.replace("\n", "<br />")
	print "<< html_escape: %s" % repr(s)
	return s


##############################################################################
# Template Management (Models Management)
##############################################################################

class TemplateModel:
	def __init__(self, name = "Default", filename = '', displayAsHtml = False, uuid = None):
		self._name = name
		self._filename = filename
		self._displayAsHtml = displayAsHtml
		self._uuid = uuid
	
	def getName(self):
		return self._name
	
	def setName(self, name):
		self._name = name

	def getFilename(self):
		return self._filename
	
	def setFilename(self, filename):
		self._filename = filename

	def displayAsHtml(self):
		return self._displayAsHtml
	
	def setDisplayAsHtml(self, v = True):
		self._displayAsHtml = v

	def getUuid(self):
		return self._uuid


def loadTemplates(pluginId, defaultTemplateFilename = None):
	"""
	Loads templates properties from the settings,
	storing the templates as a collection of
	plugins/<uuid>/templates/<template-uuid>/{name,filename,displayAsHtml}
	QSettings keys.
	
	@rtype: list of TemplateModel
	@returns: the loaded templates. Contains a default one if the
	loaded list was empty.
	"""
	settings = QSettings()
	settings.beginGroup("plugins/%s/templates" % pluginId)

	templateModels = []
	for group in settings.childGroups():
		# By construction, group is the UUID string identifying the template
		name = settings.value("%s/name" % group).toString()
		filename = settings.value("%s/filename" % group).toString()
		displayAsHtml = settings.value("%s/displayAsHtml" % group).toBool()
		templateModel = TemplateModel(name, filename, displayAsHtml, group)
		templateModels.append(templateModel)
	
	# Load a default template, if none exists
	if defaultTemplateFilename and not templateModels:
		defaultTemplateFilename = os.path.normpath(unicode("%s/plugins/%s" % (QApplication.instance().get('qtestermanpath'), defaultTemplateFilename)))
		templateModels.append(TemplateModel("Default", defaultTemplateFilename, True))
	
	return templateModels

def saveTemplates(templateModels, pluginId):
	"""
	Saves templates properties as a collection of 
	plugins/<uuid>/templates/<template-uuid>/{name,filename,displayAsHtml}
	QSettings keys.

	@type  templateModels: list of TemplateModel
	@param templateModels: the template to save to a persistent storage
	
	@rtype: boolean
	@returns: True if OK, False in case of an error
	"""
	settings = QSettings()
	settings.beginGroup("plugins/%s/templates" % pluginId)

	# Clear all
	for group in settings.childGroups():
		settings.remove(group)

	# Reconstruct everything
	for templateModel in templateModels:
		group = templateModel.getUuid()
		if group is None:
			# New template - generates a new UUID
			group = QUuid.createUuid().toString()
		settings.beginGroup(group)
		settings.setValue("name", QVariant(templateModel.getName()))
		settings.setValue("filename", QVariant(templateModel.getFilename()))
		settings.setValue("displayAsHtml", QVariant(templateModel.displayAsHtml()))
		settings.endGroup()
	
	return True

##############################################################################
# Custom web view
##############################################################################

class MyWebView(QtWebKit.QWebView):
	def __init__(self, manager, parent = None):
		QtWebKit.QWebView.__init__(self, parent)
		self._manager = manager
		self.setTextSizeMultiplier(0.8)
		reloadAction = self.pageAction(QtWebKit.QWebPage.Reload)
		reloadAction.setText("(Re)apply template")
		self.connect(reloadAction, SIGNAL('triggered(bool)'), self.reload)

	def reload(self):
		print "Reloading..."
		self._manager.reapplyTemplate()
		
##############################################################################
# Template Application: embeddable widget
##############################################################################

class WTemplateApplicationWidget(QWidget):
	"""
	A composite dialog enabling to
	- select a template,
	- visualize the results according to the template properties,
	- manage the templates,
	- save the output

	Just reimplement:
	- getTemplateManagementDialog() to return a template management dialog.
	"""
	def __init__(self, pluginId, defaultTemplateFilename = None, parent = None):
		QWidget.__init__(self, parent)
		self._pluginId = pluginId
		self._defaultTemplateFilename = defaultTemplateFilename

		self._source = None
		self._context = {} # Last known context when applying a template
		self.__createWidgets()
		self._refreshTemplates()

	def __createWidgets(self):
		layout = QVBoxLayout()

		# A button bar with selectable template, save option, display as HTML option
		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(QLabel("Template:"))
		self._templateComboBox = QComboBox()
		buttonLayout.addWidget(self._templateComboBox)
		self._applyTemplateButton = QPushButton("Apply")
		buttonLayout.addWidget(self._applyTemplateButton)
		self._manageTemplatesButton = QPushButton("Manage templates...")
		buttonLayout.addWidget(self._manageTemplatesButton)
		self.connect(self._applyTemplateButton, SIGNAL('clicked()'), self.reapplyTemplate)
		self.connect(self._manageTemplatesButton, SIGNAL('clicked()'), self._manageTemplates)
		
		buttonLayout.addStretch()
		self._saveButton = QPushButton("Save as...")
		self.connect(self._saveButton, SIGNAL('clicked()'), self._saveAs)
		buttonLayout.addWidget(self._saveButton)
		
		layout.addLayout(buttonLayout)

		# The main view - web mode
		self._webView = MyWebView(self)
		self._textView =QTextEdit(self)

		viewLayout = QVBoxLayout()
		viewLayout.addWidget(self._webView)
		viewLayout.addWidget(self._textView)
		viewLayout.setMargin(0)

		frame = QFrame()
		frame.setFrameShadow(QFrame.Sunken)
		frame.setFrameShape(QFrame.StyledPanel)
		frame.setLayout(viewLayout)
		layout.addWidget(frame)
		self.setLayout(layout)

	def _saveAs(self):
		path = "plugins/%s/" % self._pluginId
		settings = QSettings()
		directory = settings.value(path + 'lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getSaveFileName(self, "Save test cases specification as...", directory)
		if filename.isEmpty():
			return False

		filename = unicode(filename)
		directory = os.path.dirname(filename)
		settings.setValue(path + 'lastVisitedDirectory', QVariant(directory))
		try:
			f = open(filename, 'w')
			f.write(self._source)
			f.close()
			QMessageBox.information(self, getClientName(), "Test case specification saved successfully.", QMessageBox.Ok)
			return True
		except Exception, e:
			CommonWidgets.systemError(self, "Unable to save file as %s: %s" % (filename, unicode(e)))
			return False

	def _getTemplate(self):
		"""
		Returns the currently selected template,
		or None in case of a loading error.
		"""
		template = None
		displayAsHtml = False
		index = self._templateComboBox.currentIndex()
		if index >= 0:
			filename = self._templateComboBox.itemData(index, Qt.UserRole).toString()
			displayAsHtml = self._templateComboBox.itemData(index, Qt.UserRole+1).toBool()
			if not filename.isEmpty():
				try:
					f = open(unicode(filename))
					content = f.read()
					f.close()
					template = airspeed.Template(content)
				except Exception, e:
					# Instead of a popup, silently display the error message within the report.
					# Avoid popping an error when opening the log viewer with an incorrect plugin configuration.
					template = airspeed.Template("Unable to load template file '%s': %s" % (unicode(filename), str(e)))

		return (template, displayAsHtml)

	def _refreshTemplates(self):
		"""
		Refresh the template combobox according to available templates.
		"""
		self._templateComboBox.clear()
		templateModels = loadTemplates(self._pluginId, self._defaultTemplateFilename)
		for templateModel in templateModels:
			self._templateComboBox.addItem(templateModel.getName())
			self._templateComboBox.setItemData(self._templateComboBox.count()-1, QVariant(templateModel.getFilename()), Qt.UserRole)
			self._templateComboBox.setItemData(self._templateComboBox.count()-1, QVariant(templateModel.displayAsHtml()), Qt.UserRole+1)

	def _display(self):
		self._source = None
		(template, displayAsHtml) = self._getTemplate()
		if not template:
			return

		if displayAsHtml:
			xform = html_escape
		else:
			xform = None

		# We copy the context,
		# as airspeed updates it (servers as its base namespace)
		context = copy.copy(self._context)
		# We add some built-in macro/functions here
		context['html_escape'] = html_escape

		try:
			ret = template.merge(context, xform = xform)
			self._source = ret
		except Exception, e:
			ret = str(e)

		if self._source is None or not displayAsHtml:
			self._webView.hide()
			self._textView.setPlainText(ret)
			self._textView.show()
		else:
			self._textView.hide()
			self._webView.setHtml(ret)
			self._webView.show()

		if self._source is not None:
			self._saveButton.setEnabled(True)
		else:
			self._saveButton.setEnabled(False)

	def _manageTemplates(self):
		dialog = self.getTemplateManagementDialog()
		if dialog:
			if dialog.exec_() == QDialog.Accepted:
				self._refreshTemplates()

	##
	# 'Public' API/slots for this widget.
	##
	def reapplyTemplate(self):
		"""
		Reapply the current template with the existing context.
		"""
		self.clear()
		self._display()

	def applyTemplate(self, context):
		"""
		Sets a context, then reapply the current template.
		"""
		self._context = context
		self.reapplyTemplate()

	def clear(self):
		self._webView.setHtml('')

	def getTemplateManagementDialog(self):
		"""
		Reimplement me.
		
		@rtype: QDialog
		@returns: a dialog instance able to configure the templates for
		this plugin.
		"""
		return None


##############################################################################
# Template Management (Configuration Widgets)
##############################################################################

class TemplateEditDialog(QDialog):
	def __init__(self, model = None, parent = None):
		QDialog.__init__(self, parent)
		self._model = model
		if self._model is None:
			self._model = TemplateModel()
		self.__createWidgets()
		self._load()

	def __createWidgets(self):
		self.setWindowTitle("Template Properties")
		self.setMinimumWidth(400)
		self.resize(QSize(600, 0))
		layout = QVBoxLayout()

		attributesLayout = QGridLayout()

		self._nameLineEdit = QLineEdit(self._model.getName())
		attributesLayout.addWidget(QLabel("Name:"), 0, 0, Qt.AlignRight)
		attributesLayout.addWidget(self._nameLineEdit, 0, 1, 1, 2)
		self._filenameLineEdit = QLineEdit(self._model.getFilename())
		attributesLayout.addWidget(QLabel("Filename:"), 1, 0, Qt.AlignRight)
		attributesLayout.addWidget(self._filenameLineEdit, 1, 1)
		self._browseFileButton = QPushButton("...")
		self.connect(self._browseFileButton, SIGNAL('clicked()'), self._browseFile)
		attributesLayout.addWidget(self._browseFileButton, 1, 2)
		self._displayAsHtmlCheckBox = QCheckBox("This template generates HTML")
		attributesLayout.addWidget(self._displayAsHtmlCheckBox, 2, 0, 1, 3)
		if self._model.displayAsHtml():
			self._displayAsHtmlCheckBox.setChecked(True)
		attributesLayout.setColumnStretch(1, 1)
		layout.addLayout(attributesLayout)

		self._textEdit = QTextEdit()
		self._textEdit.setMinimumHeight(200)
		self._textEdit.setUndoRedoEnabled(True)
		self._textEdit.setWordWrapMode(QTextOption.NoWrap)
		layout.addWidget(self._textEdit)

		# Buttons
		buttonLayout = QHBoxLayout()
		self._okButton = QPushButton("Ok")
		self.connect(self._okButton, SIGNAL("clicked()"), self.aboutToAccept)
		self._cancelButton = QPushButton("Cancel")
		self.connect(self._cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addStretch()
		buttonLayout.addWidget(self._okButton)
		buttonLayout.addWidget(self._cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def _browseFile(self):
		filename = QFileDialog.getOpenFileName(self, "Select Template File", self._filenameLineEdit.text())
		if not filename.isEmpty():
			self._filenameLineEdit.setText(filename)
			self._load()
	
	def _load(self):
		filename = self._filenameLineEdit.text()
		if not filename.isEmpty():
			try:
				f = open(unicode(filename))
				content = f.read().decode('utf-8')
				f.close()
			except:
				content = '(file not found/not readable)'
			self._textEdit.setPlainText(content)

	def _save(self):
		filename = self._filenameLineEdit.text()
		if not filename.isEmpty():
			f = open(unicode(filename), 'w')
			content = unicode(self._textEdit.toPlainText()).encode('utf-8')
			f.write(content)
			f.close()

	def updateModel(self):
		self._model.setName(self._nameLineEdit.text())
		self._model.setFilename(self._filenameLineEdit.text())
		self._model.setDisplayAsHtml(self._displayAsHtmlCheckBox.isChecked())

	def getModel(self):
		self.updateModel()
		return self._model

	def aboutToAccept(self):
		if self._textEdit.document().isModified():
			# Let's save the updated template
			try:
				self._save()
			except Exception, e:
				ret = QMessageBox.warning(self, "Error",
					"Unable to save template file '%s':\n%s\nContinue anyway ?" % (unicode(filename), str(e)),
					QMessageBox.Yes | QMessageBox.No)
				if ret == QMessageBox.No:
					return

		self.accept()

class TemplateItem(QTreeWidgetItem):
	def __init__(self, templateModel, parent):
		QTreeWidgetItem.__init__(self, parent)
		self.setText(0, templateModel.getName())
		self.setText(1, templateModel.getFilename())
		self._templateModel = templateModel

	def getModel(self):
		return self._templateModel

class WTemplateTreeView(QTreeWidget):
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self.__createWidgets()
		self.__createActions()
		self._templateModels = []
		self.refresh()

	def __createWidgets(self):
		self.setRootIsDecorated(False)
		self.setSortingEnabled(True)
		self.setHeaderLabels(["Name", "Filename"])
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.header().setResizeMode(0, QHeaderView.Interactive)
		self.header().resizeSection(0, 100)
		self.header().setResizeMode(1, QHeaderView.Interactive)

	def setModel(self, templateModels):
		self._templateModels = templateModels
		self.refresh()

	def getModel(self):
		return self._templateModels

	def refresh(self):
		self.clear()
		for templateModel in self._templateModels:
			TemplateItem(templateModel, self)

		self.sortItems(self.header().sortIndicatorSection(), self.header().sortIndicatorOrder())

	def __createActions(self):
		self._addTemplateAction = CommonWidgets.TestermanAction(self, "New template...", self._addTemplate)
		self.addAction(self._addTemplateAction)
		self._removeTemplateAction = CommonWidgets.TestermanAction(self, "Remove template...", self._removeTemplate)
		self.addAction(self._removeTemplateAction)
		self._modifyTemplateAction = CommonWidgets.TestermanAction(self, "Modify template...", self._modifyTemplate)
		self.addAction(self._modifyTemplateAction)

	def _addTemplate(self):
		dialog = TemplateEditDialog(parent = self)
		if dialog.exec_() == QDialog.Accepted:
			self._templateModels.append(dialog.getModel())
			self.refresh()

	def _modifyTemplate(self):
		item = self.currentItem()
		if item:
			model = item.getModel()
			dialog = TemplateEditDialog(model, parent = self)
			if dialog.exec_() == QDialog.Accepted:
				dialog.updateModel()
				self.refresh()

	def _removeTemplate(self):
		item = self.currentItem()
		if item:
			model = item.getModel()
			ret = QMessageBox.question(self, "Remove Template", 
				"Are you sure you want to remove the template %s?\n(The template file won't be deleted)" % unicode(model.getName()),
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if ret == QMessageBox.Yes:
				try:
					self._templateModels.remove(model)
				except:
					pass

			self.refresh()

	def onItemActivated(self, item, col):
		self._modifyTemplate()

	def contextMenuEvent(self, event):
		item = self.itemAt(event.pos())
		menu = QMenu(self)
		if item:
			menu.addAction(self._modifyTemplateAction)
			menu.addAction(self._removeTemplateAction)
			menu.addSeparator()
		# In any case, general action
		menu.addAction(self._addTemplateAction)
		menu.popup(event.globalPos())
	
