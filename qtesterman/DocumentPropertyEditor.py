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
# Widget: Document property editor
#
##

from PyQt4.Qt import *

from Base import *
from CommonWidgets import *

import operator

################################################################################
# A Parameters editor based on Qt Tree View/Model
################################################################################

class ParametersItemModel(QAbstractItemModel):
	"""
	This class wraps a MetadataModel into a Qt-model to be used
	in a QTreeView.
	"""
	def __init__(self, metadataModel, parent = None):
		QAbstractItemModel.__init__(self, parent)
		self._metadataModel = None
		self._columns = [ 'name', 'type', 'default', 'description' ]
		self._cache = []
		self._sortInfo = ('name', Qt.AscendingOrder)
		self.setModel(metadataModel)
	
	def headerData(self, section, orientation, role):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			return QString(self._columns[section].title())

	def flags(self, modelIndex):
		return QAbstractItemModel.flags(self, modelIndex) | Qt.ItemIsEditable
	
	def index(self, row, column, parentModelIndex):
		if not parentModelIndex.isValid():
			return self.createIndex(row, column, 0)
		return QModelIndex()
	
	def parent(self, childModelIndex):
		return QModelIndex()
	
	def rowCount(self, parentModelIndex):
		if not parentModelIndex.isValid():
			return len(self._cache)
		else:
			return 0
	
	def columnCount(self, parentModelIndex):
		return len(self._columns)
	
	def data(self, index, role):
		if role == Qt.DisplayRole or role == Qt.EditRole:
			return QString(self._cache[index.row()][self._columns[index.column()]])
		return QVariant()

	def setData(self, index, value, role):
		if not role == Qt.EditRole:
			return False
	
		key = self._cache[index.row()]['name']
		# Updates the wrapper domain model.
		# Will raise an update notification, connected to 
		self._metadataModel.updateParameterAttribute(key, attribute = self._columns[index.column()], value = unicode(value.toString()))
		return True
	
	def setModel(self, metadataModel):
		"""
		Sets the inner, wrapped domain model.
		This is a MetadataModel object.
		"""
		if self._metadataModel:
			self.disconnect(self._metadataModel, SIGNAL('metadataUpdated()'), self.onModelUpdated)
		self._metadataModel = metadataModel
		self.onModelUpdated()
		self.connect(self._metadataModel, SIGNAL('metadataUpdated()'), self.onModelUpdated)
	
	def onModelUpdated(self):
		self._cache = self._metadataModel.getParameters().values()
		self._sort()
		self.emit(SIGNAL('modelReset()'))
	
	def sort(self, column, order):
		self._sortInfo = (self._columns[column], order)
		self._sort()
		self.emit(SIGNAL('layoutChanged()'))

	def _sort(self):
		self._cache.sort(key = operator.itemgetter(self._sortInfo[0]))
		if self._sortInfo[1] == Qt.DescendingOrder:
			self._cache.reverse()
	
	def _addParameter(self, parameter = None):
		if not parameter:
			return self._metadataModel.addParameter('parameter')
		else:
			return self._metadataModel.addParameter(name = parameter['name'], description = parameter['description'], type_ = parameter['type'], default = parameter['default'])

	def _deleteParameters(self, names):
		self._metadataModel.deleteParameters(names)
	
	def mimeTypes(self):
		return [ QString("application/x-qtesterman-parameters") ]

class ParameterItemDelegate(QStyledItemDelegate):
	def __init__(self, parent = None):
		QStyledItemDelegate.__init__(self, parent)
	
	def createEditor(self, parent, option, index):
		if index.column() == 1:
			cb = QComboBox(parent)
			cb.addItem('string')
			cb.addItem('boolean')
			cb.addItem('integer')
			cb.addItem('float')
			return cb
		else:
			return QStyledItemDelegate.createEditor(self, parent, option, index)
	
	def updateEditorGeometry(self, editor, option, index):
		editor.setGeometry(option.rect)
	
	def setModelData(self, editor, model, index):
		if index.column() == 1:
			model.setData(index, QVariant(editor.currentText()), Qt.EditRole)
		else:
			QStyledItemDelegate.setModelData(self, editor, model, index)

class WParametersEditor(QTreeView):
	def __init__(self, parent = None):
		QTreeView.__init__(self, parent)
		self.PARAMETERS_MIME = "application/x-qtesterman-parameters"
		self._metadataModel = None
		self.__createWidgets()
		self.__createActions()
		# Initialize clipboard-related actions
		self.onClipboardUpdated()
	
	def setModel(self, metadataModel):
		if self.model():
			self.model().setModel(metadataModel)
		else:
			QTreeView.setModel(self, ParametersItemModel(metadataModel))
		self._metadataModel = metadataModel

	def __createWidgets(self):
		self.setRootIsDecorated(False)
		self.setItemDelegate(ParameterItemDelegate())
		self.setSortingEnabled(True)
		self.sortByColumn(0, Qt.AscendingOrder)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setAlternatingRowColors(True)
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.connect(self, SIGNAL("customContextMenuRequested(const QPoint&)"), self.onPopupMenu)
		self.setAcceptDrops(True)
		# Check if we can paste a parameter
		self.connect(QApplication.clipboard(), SIGNAL('dataChanged()'), self.onClipboardUpdated)
		
	def __createActions(self):
		self.deleteCurrentItemsAction = TestermanAction(self, "Delete selected", self.deleteCurrentItems)
		self.deleteCurrentItemsAction.setShortcut(QKeySequence.Delete)
		self.deleteCurrentItemsAction.setShortcutContext(Qt.WidgetShortcut)
		self.addItemAction = TestermanAction(self, "Add new parameter", self.addItem)
		self.copyItemsAction = TestermanAction(self, "Copy parameter(s)", self.copyItems)
		self.copyItemsAction.setShortcut(QKeySequence.Copy)
		self.copyItemsAction.setShortcutContext(Qt.WidgetShortcut)
		self.pasteItemsAction = TestermanAction(self, "Paste copied parameter(s)", self.pasteItems)
		self.pasteItemsAction.setShortcut(QKeySequence.Paste)
		self.pasteItemsAction.setShortcutContext(Qt.WidgetShortcut)

		# Don't forget to assign to the widget, too
		self.addAction(self.deleteCurrentItemsAction)
		self.addAction(self.copyItemsAction)
		self.addAction(self.pasteItemsAction)

	def createContextMenu(self):
		contextMenu = QMenu("Parameters", self)
		# The add Item if the first entry to avoid accidental param deletion
		# (we have to explicitly down the mouse cursor to select the delete op)
		contextMenu.addAction(self.addItemAction)
		if self.selectedIndexes():
			contextMenu.addAction(self.deleteCurrentItemsAction)
			contextMenu.addAction(self.copyItemsAction)

		# Should be greyed out if no copy information is available
		contextMenu.addAction(self.pasteItemsAction)

		return contextMenu

	def onPopupMenu(self, pos):
		self.createContextMenu().popup(QCursor.pos())

	def selectParameterByName(self, name, edition = False):
		"""
		Selects a particular row, and optionally opens the editor to edit the name.
		"""
		if name:
			indexes = self.model().match(self.model().createIndex(0, 0, 0), Qt.DisplayRole, name)
			if indexes:
				index = indexes[0]
				self.setCurrentIndex(index)
				if edition:
					self.edit(index)
	
	def pasteItems(self):
		"""
		Retrieve the copied items from the clipboard, and paste them.
		Also select them once copied.
		"""
		parameters = mimeDataToObjects(self.PARAMETERS_MIME, QApplication.clipboard().mimeData())
		self.addItems(parameters)

	def deleteCurrentItems(self):
		self.model()._deleteParameters(self.getSelectedParametersNames())

	def addItem(self, parameter = None):
		"""
		@type  parameter: dict
		@param parameter: a dict containing at least name, default, description (unicode)
		
		@rtype: unicode
		@returns: the actual name of the added parameter, after possible adjustments (collision resolution)
		"""
		name = self.model()._addParameter(parameter)
		if name:
			if not parameter:
				self.selectParameterByName(name, edition = True)
			else:
				self.selectParameterByName(name)
		return name

	def addItems(self, parameters):
		"""
		Create multiple parameters items, resolving name conflicts if any,
		and selecting the last added item.
		If only one item was created, select it in edition.
		"""
		if parameters:
			name = None
			for parameter in parameters:
				name = self.addItem(parameter)
			# We select the last parameter
			# We suggest to edit the parameter only if there only one to be pasted.
			self.selectParameterByName(name, len(parameters) == 1)

	def copyItems(self):
		"""
		Copy the current items to the clipboard
		"""
		mimeData = objectsToMimeData(self.PARAMETERS_MIME, self.getSelectedParameters())
		# Also add a text representation to paste to other applications
		mimeData.setText("\n".join([ "%(name)s\t%(default)s\t%(type)s\t%(description)s" % p for p in self.getSelectedParameters()]))
		QApplication.clipboard().setMimeData(mimeData)

	def getSelectedParametersNames(self):
		selectedParametersNames = []
		for index in self.selectedIndexes():
			if index.column() == 0:
				selectedParametersNames.append(unicode(self.model().data(index, Qt.DisplayRole)))
#		print "selected:\n%s" % "\n".join(selectedParametersNames)
		return selectedParametersNames

	def getSelectedParameters(self):
		ret = []
		names = self.getSelectedParametersNames()
		for name in names:
			# FIXME: let the TreeView model manage this - or the domain model itself
			ret.append(self._metadataModel.getParameter(name))
		return ret

	def onClipboardUpdated(self):
		c = QApplication.clipboard()
		if c.mimeData().hasFormat(self.PARAMETERS_MIME):
			self.pasteItemsAction.setEnabled(True)
		else:
			self.pasteItemsAction.setEnabled(False)

################################################################################
# A Groups editor based on Qt Tree View/Model
################################################################################

class GroupsItemModel(QAbstractItemModel):
	"""
	This class wraps a MetadataModel into a Qt-model to be used
	in a QTreeView.
	"""
	def __init__(self, metadataModel, parent = None):
		QAbstractItemModel.__init__(self, parent)
		self._metadataModel = None
		self._columns = [ 'name', 'description' ]
		self._cache = []
		self._sortInfo = ('name', Qt.AscendingOrder)
		self.setModel(metadataModel)
	
	def headerData(self, section, orientation, role):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			return QString(self._columns[section].title())

	def flags(self, modelIndex):
		return QAbstractItemModel.flags(self, modelIndex) | Qt.ItemIsEditable
	
	def index(self, row, column, parentModelIndex):
		if not parentModelIndex.isValid():
			return self.createIndex(row, column, 0)
		return QModelIndex()
	
	def parent(self, childModelIndex):
		return QModelIndex()
	
	def rowCount(self, parentModelIndex):
		if not parentModelIndex.isValid():
			return len(self._cache)
		else:
			return 0
	
	def columnCount(self, parentModelIndex):
		return len(self._columns)
	
	def data(self, index, role):
		if role == Qt.DisplayRole or role == Qt.EditRole:
			return QString(self._cache[index.row()][self._columns[index.column()]])
		return QVariant()

	def setData(self, index, value, role):
		if not role == Qt.EditRole:
			return False
	
		key = self._cache[index.row()]['name']
		# Updates the wrapper domain model.
		# Will raise an update notification, connected to 
		self._metadataModel.updateGroupAttribute(key, attribute = self._columns[index.column()], value = unicode(value.toString()))
		return True
	
	def setModel(self, metadataModel):
		"""
		Sets the inner, wrapped domain model.
		This is a MetadataModel object.
		"""
		if self._metadataModel:
			self.disconnect(self._metadataModel, SIGNAL('metadataUpdated()'), self.onModelUpdated)
		self._metadataModel = metadataModel
		self.onModelUpdated()
		self.connect(self._metadataModel, SIGNAL('metadataUpdated()'), self.onModelUpdated)
	
	def onModelUpdated(self):
		self._cache = self._metadataModel.getGroups().values()
		self._sort()
		self.emit(SIGNAL('modelReset()'))
	
	def sort(self, column, order):
		self._sortInfo = (self._columns[column], order)
		self._sort()
		self.emit(SIGNAL('layoutChanged()'))

	def _sort(self):
		self._cache.sort(key = operator.itemgetter(self._sortInfo[0]))
		if self._sortInfo[1] == Qt.DescendingOrder:
			self._cache.reverse()
	
	def _addGroup(self, group = None):
		if not group:
			return self._metadataModel.addGroup('group')
		else:
			return self._metadataModel.addGroup(name = group['name'], description = group['description'])

	def _deleteGroups(self, names):
		self._metadataModel.deleteGroups(names)
	
	def mimeTypes(self):
		return [ QString("application/x-qtesterman-groups") ]

class GroupItemDelegate(QStyledItemDelegate):
	def __init__(self, parent = None):
		QStyledItemDelegate.__init__(self, parent)
	
	def createEditor(self, parent, option, index):
		return QStyledItemDelegate.createEditor(self, parent, option, index)
	
	def updateEditorGeometry(self, editor, option, index):
		editor.setGeometry(option.rect)
	
	def setModelData(self, editor, model, index):
		QStyledItemDelegate.setModelData(self, editor, model, index)

class WGroupsEditor(QTreeView):
	def __init__(self, parent = None):
		QTreeView.__init__(self, parent)
		self.GROUPS_MIME = "application/x-qtesterman-groups"
		self._metadataModel = None
		self.__createWidgets()
		self.__createActions()
		# Initialize clipboard-related actions
		self.onClipboardUpdated()
	
	def setModel(self, metadataModel):
		if self.model():
			self.model().setModel(metadataModel)
		else:
			QTreeView.setModel(self, GroupsItemModel(metadataModel))
		self._metadataModel = metadataModel

	def __createWidgets(self):
		self.setRootIsDecorated(False)
		self.setItemDelegate(GroupItemDelegate())
		self.setSortingEnabled(True)
		self.sortByColumn(0, Qt.AscendingOrder)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setAlternatingRowColors(True)
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.connect(self, SIGNAL("customContextMenuRequested(const QPoint&)"), self.onPopupMenu)
		self.setAcceptDrops(True)
		# Check if we can paste a group
		self.connect(QApplication.clipboard(), SIGNAL('dataChanged()'), self.onClipboardUpdated)
		
	def __createActions(self):
		self.deleteCurrentItemsAction = TestermanAction(self, "Delete selected", self.deleteCurrentItems)
		self.deleteCurrentItemsAction.setShortcut(QKeySequence.Delete)
		self.deleteCurrentItemsAction.setShortcutContext(Qt.WidgetShortcut)
		self.addItemAction = TestermanAction(self, "Add new group", self.addItem)
		self.copyItemsAction = TestermanAction(self, "Copy group(s)", self.copyItems)
		self.copyItemsAction.setShortcut(QKeySequence.Copy)
		self.copyItemsAction.setShortcutContext(Qt.WidgetShortcut)
		self.pasteItemsAction = TestermanAction(self, "Paste copied group(s)", self.pasteItems)
		self.pasteItemsAction.setShortcut(QKeySequence.Paste)
		self.pasteItemsAction.setShortcutContext(Qt.WidgetShortcut)

		# Don't forget to assign to the widget, too
		self.addAction(self.deleteCurrentItemsAction)
		self.addAction(self.copyItemsAction)
		self.addAction(self.pasteItemsAction)

	def createContextMenu(self):
		contextMenu = QMenu("Groups", self)
		# The add Item if the first entry to avoid accidental param deletion
		# (we have to explicitly down the mouse cursor to select the delete op)
		contextMenu.addAction(self.addItemAction)
		if self.selectedIndexes():
			contextMenu.addAction(self.deleteCurrentItemsAction)
			contextMenu.addAction(self.copyItemsAction)

		# Should be greyed out if no copy information is available
		contextMenu.addAction(self.pasteItemsAction)

		return contextMenu

	def onPopupMenu(self, pos):
		self.createContextMenu().popup(QCursor.pos())

	def selectGroupByName(self, name, edition = False):
		"""
		Selects a particular row, and optionally opens the editor to edit the name.
		"""
		if name:
			indexes = self.model().match(self.model().createIndex(0, 0, 0), Qt.DisplayRole, name)
			if indexes:
				index = indexes[0]
				self.setCurrentIndex(index)
				if edition:
					self.edit(index)
	
	def pasteItems(self):
		"""
		Retrieve the copied items from the clipboard, and paste them.
		Also select them once copied.
		"""
		groups = mimeDataToObjects(self.GROUPS_MIME, QApplication.clipboard().mimeData())
		self.addItems(groups)

	def deleteCurrentItems(self):
		self.model()._deleteGroups(self.getSelectedGroupsNames())

	def addItem(self, group = None):
		"""
		@type  group: dict
		@param group: a dict containing at least name, default, description (unicode)
		
		@rtype: unicode
		@returns: the actual name of the added group, after possible adjustments (collision resolution)
		"""
		name = self.model()._addGroup(group)
		if name:
			if not group:
				self.selectGroupByName(name, edition = True)
			else:
				self.selectGroupByName(name)
		return name

	def addItems(self, groups):
		"""
		Create multiple groups items, resolving name conflicts if any,
		and selecting the last added item.
		If only one item was created, select it in edition.
		"""
		if groups:
			name = None
			for group in groups:
				name = self.addItem(group)
			# We select the last group
			# We suggest to edit the group only if there only one to be pasted.
			self.selectGroupByName(name, len(groups) == 1)

	def copyItems(self):
		"""
		Copy the current items to the clipboard
		"""
		mimeData = objectsToMimeData(self.GROUPS_MIME, self.getSelectedGroups())
		# Also add a text representation to paste to other applications
		mimeData.setText("\n".join([ "%(name)s\t%(description)s" % p for p in self.getSelectedGroups()]))
		QApplication.clipboard().setMimeData(mimeData)

	def getSelectedGroupsNames(self):
		selectedGroupsNames = []
		for index in self.selectedIndexes():
			if index.column() == 0:
				selectedGroupsNames.append(unicode(self.model().data(index, Qt.DisplayRole)))
#		print "selected:\n%s" % "\n".join(selectedGroupsNames)
		return selectedGroupsNames

	def getSelectedGroups(self):
		ret = []
		names = self.getSelectedGroupsNames()
		for name in names:
			# FIXME: let the TreeView model manage this - or the domain model itself
			ret.append(self._metadataModel.getGroup(name))
		return ret

	def onClipboardUpdated(self):
		c = QApplication.clipboard()
		if c.mimeData().hasFormat(self.GROUPS_MIME):
			self.pasteItemsAction.setEnabled(True)
		else:
			self.pasteItemsAction.setEnabled(False)

class WScriptPropertiesEditor(QWidget):
	"""
	Interfaces the extended metadata attributes,
	i.e. what is not related to parameters or groups.
	
	This is a view over a MetadataModel.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.metadataModel = None # Metadata model
		self.__createWidgets()

	def __createWidgets(self):
		layout = QVBoxLayout()

#		buttonLayout = QHBoxLayout()
#		self.descriptionButton = QPushButton("Description...", self)
#		self.connect(self.descriptionButton, SIGNAL("clicked()"), self.onDescriptionButtonTriggered)
#		buttonLayout.addWidget(self.descriptionButton)

#		self.preprequisitesButton = QPushButton("Prerequisites...", self)
#		self.connect(self.preprequisitesButton, SIGNAL("clicked()"), self.onPrerequisitesButtonTriggered)
#		buttonLayout.addWidget(self.preprequisitesButton)
#		buttonLayout.addStretch()

#		layout.addLayout(buttonLayout)

		l = QHBoxLayout()
		self.languageApiLabel = QLabel("Language API:")
		l.addWidget(self.languageApiLabel)
		self.languageApiEditor = QLineEdit()
		l.addWidget(self.languageApiEditor)
		l.setMargin(2)
		layout.addLayout(l)
		
		layout.setMargin(0)
		self.setLayout(layout)
	
	def onLanguageApiUpdated(self, api):
		self.metadataModel.setLanguageApi(unicode(api))

	def setModel(self, metadataModel):
		# Disconnect signals on previous documentModel, if any
		if self.metadataModel:
			self.disconnect(self.metadataModel, SIGNAL('metadataUpdated()'), self.onModelUpdated)

		self.metadataModel = metadataModel
		self.onModelUpdated()
		# As a real view, we subscribe for the model update notifications (aspect: metadata)
		# since we are not the single view to be able to edit it.
		# (a SessionParameterEditor updates it, too)
		if self.metadataModel:
			self.connect(self.metadataModel, SIGNAL('metadataUpdated()'), self.onModelUpdated)
	
	def onModelUpdated(self):
		# General properties
		# Description, prerequisites: using an additional dialog box, hence updated
		# when displaying the dialog box.
		# Possible TODO: other generic properties (author, etc)
		self.disconnect(self.languageApiEditor, SIGNAL("textChanged(const QString&)"), self.onLanguageApiUpdated)
		
		self.languageApiEditor.setText(self.metadataModel.getLanguageApi())
		self.languageApiEditor.show()
		self.languageApiLabel.show()
		self.connect(self.languageApiEditor, SIGNAL("textChanged(const QString&)"), self.onLanguageApiUpdated)

	def onDescriptionButtonTriggered(self):
		desc = self.metadataModel.getDescription()
		dialog = WTextEditDialog(desc, "Script description", 0, self)
		if dialog.exec_() == QDialog.Accepted:
			desc = dialog.getText()
			self.metadataModel.setDescription(unicode(desc))

	def onPrerequisitesButtonTriggered(self):
		prerequisites = self.metadataModel.getPrerequisites()
		dialog = WTextEditDialog(prerequisites, "Script prerequisites", 0, self)
		if dialog.exec_() == QDialog.Accepted:
			prerequisites = dialog.getText()
			self.metadataModel.setPrerequisites(unicode(prerequisites))


# Some 'unit' tests
if __name__ == '__main__':
	import sys
	import DocumentModels
	sampleMetadataSource = """<?xml version="1.0" encoding="utf-8" ?>
<metadata version="1.0">
<description>description</description>
<prerequisites>prerequisites</prerequisites>
<parameters>
<parameter name="PX_NEW_PARAM" default="" type="string"><![CDATA[this is a descript]]></parameter>
<parameter name="PX_PROBE_01" default="probe:tcp01@localhost" type="string"><![CDATA[fdsfdsfsd]]></parameter>
<parameter name="PX_SERVER_IP" default="127.0.0.1" type="string"><![CDATA[]]></parameter>
<parameter name="PX_PROBE_02" default="probe:tcp02@localhost" type="string"><![CDATA[]]></parameter>
<parameter name="PX_SERVER_PORT" default="2905" type="integer"><![CDATA[]]></parameter>
</parameters>
</metadata>"""
	
	
	a = QApplication(sys.argv)
	
	m = DocumentModels.MetadataModel(sampleMetadataSource)

	w = WScriptPropertiesEditor()
	w.setModel(m)

	w.show()

	a.exec_()
	
