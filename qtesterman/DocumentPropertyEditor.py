##
# -*- coding: utf-8 -*-
#
# Widget: Document property editor
#
##

import PyQt4.Qt as qt
import PyQt4.QtXml as QtXml
import PyQt4.QtGui as qtItem

from Base import *
from CommonWidgets import *

class WParameterTreeWidgetItem(qt.QTreeWidgetItem):
	def __init__(self, parent, parameter):
		"""
		parameter is a dict[unicode] of unicode containing "name", "description", "previous-value", "type", "default"
		
		The initial name is used as a key for the model, so we save it in a safe place as soon as the item is created.
		"""
		qt.QTreeWidgetItem.__init__(self, parent)
		self.parameter = parameter
		self.key = parameter['name']
		self.columns = [ 'name', 'default', 'description', 'type', 'previous-value' ]
		self.setFlags(qt.Qt.ItemIsEnabled | qt.Qt.ItemIsEditable | qt.Qt.ItemIsSelectable)
		#self.setSortingEnabled(1)
		
	def data(self, column, role):
		name = self.columns[column]
		if role == qt.Qt.DisplayRole:
			return qt.QVariant(self.parameter[name])
		if role == qt.Qt.EditRole:
			return qt.QVariant(self.parameter[name])
		return qt.QVariant()

	def setData(self, column, role, value):
		val = unicode(value.toString())
		name = self.columns[column]
		if role == qt.Qt.EditRole:
			if name == 'name':
				# Special constraint for the name
				val = val.upper()
				if not val.startswith('PX_'):
					val = 'PX_' + val
			self.parameter[name] = val
			# It doesn't seem normal to send this signal explicitly... It should be done by the
			# treeWidget by itself, AFAIK.
			self.treeWidget().emit(qt.SIGNAL('itemChanged(QTreeWidgetItem*, int)'), self, column)


class WParameterEditor(qt.QTreeWidget):
	"""
	An editor of script metadata.parameters.

	A WParameterEditor is a subelement of WPropertyEditor which is a view over a DocumentModel model (aspect: metadata only).

	This widget enables the edition of meta parameters, i.e. their type, meaning, name, default values.
	This is not suitable for a session parameter instanciation.
	"""
	def __init__(self, propertyEditor, parent = None):
		qt.QTreeWidget.__init__(self, parent)
		# The metadataModel from which we display parameters
		# Immediately updated on updated/deleted/add items.
		# As a consequence the view is updated with the updated model, and we redisplay it this way.
		# (i.e. no local cache)
		self.metadataModel = None
		self.propertyEditor = propertyEditor
		self.PARAMETERS_MIME = "application/x-qtesterman-parameters"
		self.__createWidgets()
		self.__createActions()
		# Initialize clipboard-related actions
		self.onClipboardUpdated()

	def __createWidgets(self):
		self.setRootIsDecorated(0)
		# Type is not yet managed.
#		self.labels = [ 'name', 'default value', 'type', 'description' ]
		self.labels = [ 'name', 'default value', 'description' ]
		self.setSortingEnabled(1)
		# Default sort - should be read from the QSettings.
		self.sortItems(0, qt.Qt.AscendingOrder)
		self.setSelectionMode(qtItem.QAbstractItemView.ExtendedSelection)
		labels = qt.QStringList()
		for l in self.labels:
			labels.append(l)
		self.setHeaderLabels(labels)
		self.setContextMenuPolicy(qt.Qt.CustomContextMenu)
		self.connect(self, qt.SIGNAL("customContextMenuRequested(const QPoint&)"), self.onPopupMenu)

		#self.dragStartPosition = None
		self.setAcceptDrops(True)

		# Check if we can paste a parameter
		self.connect(qt.QApplication.clipboard(), qt.SIGNAL('dataChanged()'), self.onClipboardUpdated)

	def __createActions(self):
		self.deleteCurrentItemsAction = TestermanAction(self, "Delete selected", self.deleteCurrentItems)
		self.deleteCurrentItemsAction.setShortcut(qt.QKeySequence.Delete)
		self.deleteCurrentItemsAction.setShortcutContext(qt.Qt.WidgetShortcut)
		self.addItemAction = TestermanAction(self, "Add new parameter", self.addItem)
		self.copyItemsAction = TestermanAction(self, "Copy parameter(s)", self.copyItems)
		self.copyItemsAction.setShortcut(qt.QKeySequence.Copy)
		self.copyItemsAction.setShortcutContext(qt.Qt.WidgetShortcut)
		self.pasteItemsAction = TestermanAction(self, "Paste copied parameter(s)", self.pasteItems)
		self.pasteItemsAction.setShortcut(qt.QKeySequence.Paste)
		self.pasteItemsAction.setShortcutContext(qt.Qt.WidgetShortcut)

		# Don't forget to assign to the widget, too
		self.addAction(self.deleteCurrentItemsAction)
		self.addAction(self.copyItemsAction)
		self.addAction(self.pasteItemsAction)

	def mouseMoveEvent(self, e):
		"""
		Reimplementation from QWidget. Drag and drop preparation.
		"""
		items = self.selectedItems()
		if not items:
			return qt.QTreeWidget.mouseMoveEvent(self, e)
		if not ( (e.buttons() & qt.Qt.LeftButton) ):#and (e.modifiers() & qt.Qt.ControlModifier) ):
			return qt.QTreeWidget.mouseMoveEvent(self, e)

		#log("mouseEvent - dragging")
		parameters = []
		for item in items:
			parameters.append(item.parameter)
		drag = qt.QDrag(self)
		drag.setMimeData(objectsToMimeData(self.PARAMETERS_MIME, parameters))
		dropAction = drag.start(qt.Qt.CopyAction)
		return qt.QTreeWidget.mouseMoveEvent(self, e)

	def setModel(self, metadataModel):
		"""
		parameters is a domElement extracted from the XML metadata.
		"""
		# We disconnect before calling self.clear(), which emits an itemChanged... (sounds strange... buggy ?)
		self.disconnect(self, qt.SIGNAL('itemChanged(QTreeWidgetItem*, int)'), self.onItemChanged)
		self.clear()

		# Synchronize the local parameters struct with the metadataModel.
		self.metadataModel = metadataModel

		for (name, p) in self.metadataModel.getParameters().items():
			# Local copy
			data = p.copy()
			p['name'] = name
			WParameterTreeWidgetItem(self, p)

		# We re-sort the items according to the current sorting parameters
		self.sortItems(self.sortColumn(), self.header().sortIndicatorOrder())

		self.connect(self, qt.SIGNAL('itemChanged(QTreeWidgetItem*, int)'), self.onItemChanged)

	def onItemChanged(self, item, col):
		"""
		Update the model, and reselect the item.
		"""
		# Update the model
		p = item.parameter
		key = item.key
		if key != p['name']:
			# The parameter has been renamed.
			# If the new name (p['name']) already exists: 2 solutions: overwrite the existing param, or automatically adjust
			# the name.
			# For now, we adjust it, always.
			newName = self.metadataModel.getNewParameterName(p['name'])
			self.metadataModel.setParameter(key, default = p['default'], description = p['description'], newName = newName)
			newKey = newName
		else:
			# Not renamed
			self.metadataModel.setParameter(key, default = p['default'], description = p['description'])
			newKey = key

		# We reselect the item.
		self.selectParameterByName(newKey)

	def createContextMenu(self):
		contextMenu = qt.QMenu("Parameters", self)
		# The add Item if the first entry to avoid accidental param deletion
		# (we have to explicitly down the mouse cursor to select the delete op)
		contextMenu.addAction(self.addItemAction)
		item = self.currentItem()
		if item:
			contextMenu.addAction(self.deleteCurrentItemsAction)
			contextMenu.addAction(self.copyItemsAction)

		# Should be greyed out if no copy information is available
		contextMenu.addAction(self.pasteItemsAction)

		return contextMenu

	def onPopupMenu(self, pos):
		self.createContextMenu().popup(qt.QCursor.pos())

	def deleteCurrentItems(self):
		# We update the model only.
		# The view will be updated on (final) model update notification.

		self.metadataModel.disableUpdateNotifications()
		for item in self.selectedItems():
			self.metadataModel.removeParameter(item.parameter['name'])
		self.metadataModel.enableUpdateNotifications()
		self.metadataModel.notifyUpdate()

	def addItem(self, parameter = None):
		"""
		@type  parameter: dict
		@param parameter: a dict containing at least name, default, description (unicode)
		
		@rtype: unicode
		@returns: the actual name of the added parameter, after possible adjustments (collision resolution)
		"""
		# If p is None, create a default parameter, and select it for name edition
		if not parameter:
			parameter = { 'name': 'PX_PARAM_01', 'default': '', 'description': '' }
			name = self.metadataModel.getNewParameterName(parameter['name'])
			self.metadataModel.setParameter(name, default = parameter['default'], description = parameter['description'])
			# Select it in edition
			# The name is unique, so no amgiguity to select it by name.
			self.selectParameterByName(name, edition = True)
			return

		# OK, now we can add it.
		# First, we make sure to get a non-existing name.
		name = self.metadataModel.getNewParameterName(parameter['name'])
		# OK, now we can add it - the previous-value is not kept (on will)
		self.metadataModel.setParameter(name, default = parameter['default'], description = parameter['description'])

		# Select it. name is unique within the list, so no ambiguity is possible to look it by its name.
		self.selectParameterByName(name)
		return name

	def addItems(self, parameters):
		"""
		Create multiple parameters items, resolving name conflicts if any,
		and selecting the last added item.
		If only one item was created, select it in edition.
		"""
		if parameters:
			# Minimal optimizations: we won't wait for a notification for each parameter, but only at the end.
			self.metadataModel.disableUpdateNotifications()
			for parameter in parameters:
				name = self.addItem(parameter)
			self.metadataModel.enableUpdateNotifications()
			self.metadataModel.notifyUpdate()
			# We select the last parameter - we can only select it after the model notification, eitherwise the parameter is not created yet.
			# We suggest to edit the parameter only if there only one to be pasted.
			self.selectParameterByName(name, len(parameters) == 1)

	def selectParameterByName(self, name, edition = False):
		"""
		Find and select an item.
		If edition is True, select it in name edition.

		The name is unique, so no ambiguity possible.
		"""
		items = self.findItems(name, qt.Qt.MatchExactly)
		if len(items) > 0:
			item = items[-1]
			self.setCurrentItem(item)
			if edition:
				self.editItem(item)

#	def extendSelectedParameterByName(self, name):
#		"""
#		Find and select an item without cancelling the current selection.
#
#		The name is unique, so no ambiguity possible.
#		"""
#		items = self.findItems(name, qt.Qt.MatchExactly)
#		if len(items) > 0:
#			item = items[-1]
#			self.setCurrentItem(item)

	def pasteItems(self):
		"""
		Retrieve the copied items from the clipboard, and paste them.
		Also select them once copied.
		"""
		parameters = mimeDataToObjects(self.PARAMETERS_MIME, qt.QApplication.clipboard().mimeData())
		self.addItems(parameters)

	def copyItems(self):
		"""
		Copy the current items to the clipboard
		"""
		parameters = []
		for item in self.selectedItems():
			parameters.append(item.parameter)
		qt.QApplication.clipboard().setMimeData(objectsToMimeData(self.PARAMETERS_MIME, parameters))

	def onClipboardUpdated(self):
		# When shutting down, the module seems to be reset while some objects are still alive.
		# This avoids an exception, nothing else.
		if not qt:
			return
		c = qt.QApplication.clipboard()
		if c.mimeData().hasFormat(self.PARAMETERS_MIME):
			self.pasteItemsAction.setEnabled(True)
		else:
			self.pasteItemsAction.setEnabled(False)


class WDocumentPropertyEditor(qt.QWidget):
	"""
	This composite widget manages the whole script metadata management.
	It contains a WParameterEditor for the parameter part,
	and some other ways to edit the top level meta elements (prerequisites, description)

	This is a view over a DocumentModel.
	"""
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.model = None # Document model
		self.metadataModel = None # Metadata sub-model. Should be enough for this view, which should not manage other model's aspects.
		self.__createWidgets()

	def __createWidgets(self):
		layout = qt.QVBoxLayout()

		buttonLayout = qt.QHBoxLayout()
		self.descriptionButton = qt.QPushButton("Description...", self)
		self.connect(self.descriptionButton, qt.SIGNAL("clicked()"), self.onDescriptionButtonTriggered)
		buttonLayout.addWidget(self.descriptionButton)

		self.preprequisitesButton = qt.QPushButton("Prerequisites...", self)
		self.connect(self.preprequisitesButton, qt.SIGNAL("clicked()"), self.onPrerequisitesButtonTriggered)
		buttonLayout.addWidget(self.preprequisitesButton)
		buttonLayout.addStretch()

		layout.addLayout(buttonLayout)

		self.parameterEditor = WParameterEditor(self, self)
		layout.addWidget(self.parameterEditor)

		layout.setMargin(2)
		self.setLayout(layout)

	def setModel(self, documentModel):
		# Disconnect signals on previous documentModel, if any
		if self.model:
			self.disconnect(self.model, qt.SIGNAL('metadataUpdated()'), self.onModelUpdated)

		self.model = documentModel
		self.onModelUpdated()
		# As a real view, we subscribe for the model update notifications (aspect: metadata)
		# since we are not the single view to be able to edit it.
		# (a SessionParameterEditor updates it, too)
		self.connect(self.model, qt.SIGNAL('metadataUpdated()'), self.onModelUpdated)

	def onModelUpdated(self):
		self.metadataModel = self.model.getMetadataModel()
		# General properties
		# Description, prerequisites: using an additional dialog box, hence updated
		# when displaying the dialog box.
		# Possible TODO: other generic properties (author, etc)

		# Parameters: delegation to the parameterEditor.
		self.parameterEditor.setModel(self.metadataModel)

	def onDescriptionButtonTriggered(self):
		desc = self.metadataModel.getDescription()
		dialog = WTextEditDialog(desc, "Script description", 0, self)
		if dialog.exec_() == qt.QDialog.Accepted:
			desc = dialog.getText()
			self.metadataModel.setDescription(unicode(desc))

	def onPrerequisitesButtonTriggered(self):
		prerequisites = self.metadataModel.getPrerequisites()
		dialog = WTextEditDialog(prerequisites, "Script prerequisites", 0, self)
		if dialog.exec_() == qt.QDialog.Accepted:
			prerequisites = dialog.getText()
			self.metadataModel.setPrerequisites(unicode(prerequisites))


class WDocumentPropertyEditorDock(qt.QDockWidget):
	"""
	Observes the main documentTabWidget. When the tab is switched, trigger an update on the embedded WParameterEditor (for now).
	"""
	def __init__(self, documentTabWidget, parent):
		qt.QDockWidget.__init__(self, parent)
		self.documentTabWidget = documentTabWidget
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("Document properties")
		self.propertyEditor = WDocumentPropertyEditor(self)
		self.setWidget(self.propertyEditor)
		self.connect(self.documentTabWidget, qt.SIGNAL("currentChanged(int)"), self.onDocumentTabWidgetChanged)

	def onDocumentTabWidgetChanged(self, index):
		documentModel = self.documentTabWidget.currentWidget().model
		self.propertyEditor.setModel(documentModel)
