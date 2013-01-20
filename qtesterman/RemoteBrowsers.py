# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008-2013 Sebastien Lefevre and other contributors
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
# Remote browsers/explorers, triggering appropriate actions when needed.
#
# Based on a server file system view, enabling basic file management
# through Ws API, that emits some signals to integrate non-local-only logic
# (such as opening files)
#
#
# An additional file selector, used for "save as..." option, is provided,
# implemented as a listwidget.
#
##

import Resources
import CommonWidgets
import LogViewer
import DocumentModels
import Compare


import os.path
import re
import time

from PyQt4.Qt import *

from Base import *

from CommonWidgets import *

################################################################################
# Local Icon Cache
################################################################################

#: may be shared in a common file.
#: however, copying it locally enables more independent modules.
class IconCache:
	def __init__(self):
		self._icons = {}

	def icon(self, resource):
		if not self._icons.has_key(resource):
			self._icons[resource] = QIcon(resource)
		return self._icons[resource]

TheIconCache = IconCache()

def icon(resource):
	return TheIconCache.icon(resource)



################################################################################
# File Revisions Viewer
################################################################################

class RevisionItem(QTreeWidgetItem):
	def __init__(self, revisionInfo, parent = None):
		QTreeWidgetItem.__init__(self, parent)
		self.revisionInfo = revisionInfo
	
		self.setData(0, Qt.DisplayRole, QVariant(time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(self.revisionInfo['date']))))
		self.setData(1, Qt.DisplayRole, QVariant(self.revisionInfo['committer']))
		self.setData(2, Qt.DisplayRole, QVariant(self.revisionInfo['change']))
		self.setData(3, Qt.DisplayRole, QVariant(self.revisionInfo['id']))
		self.setData(4, Qt.DisplayRole, QVariant(self.revisionInfo['message']))


class WRevisionsTreeWidget(QTreeWidget):
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self._labels = [ 'Date', 'By', 'Type', 'Revision ID', 'Reason' ]

		self.setWindowIcon(icon(":/icons/job-queue.png"))

		self.setRootIsDecorated(False)
		self.setSortingEnabled(True)
		
		self.setSelectionMode(self.MultiSelection)
		
		self.setHeaderLabels(self._labels)
		self.header().setResizeMode(0, QHeaderView.ResizeToContents)
	
	def setModel(self, revisions):
		"""
		Clear the tree and display the revisions.
		"""
		self.clear()
		for revision in revisions:
			item = RevisionItem(revision, self)
		
		self.sortItems(0, Qt.DescendingOrder)
		
		
class WRevisionsDialog(QDialog):
	def __init__(self, filename, revisions, client, parent = None):
		QDialog.__init__(self, parent)
		self._client = client
		self._filename = filename
		self.__createWidgets()
		self._treeview.setModel(revisions)
	
	def __createWidgets(self):
		self.setWindowIcon(icon(':/icons/browser'))
		self.setWindowTitle('Revisions for %s' % self._filename)
		self.resize(600, 400)
		
		layout = QVBoxLayout()
		
		splitter = QSplitter(Qt.Vertical)
		
		# Simple treeview to see the various linear revisions
		self._treeview = WRevisionsTreeWidget()
		splitter.addWidget(self._treeview)
		
		self.connect(self._treeview, SIGNAL("itemSelectionChanged()"), self.onItemSelectionChanged)

		# A comparison/diff viewer
		self._diffViewer = Compare.WCompareWidget()
		splitter.addWidget(self._diffViewer)
		
		layout.addWidget(splitter)

		# Buttons
		self._closeButton = QPushButton("Close")
		self.connect(self._closeButton, SIGNAL("clicked()"), self.accept)
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self._closeButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def onItemSelectionChanged(self):
		items = self._treeview.selectedItems()
		l = len(items)
		if l > 3:
			# We should not enter this case, normally
			self._treeview.clearSelection()
			return

		if l == 3:
			# Automatically deselect the 2nd selected item (i.e. the 3rd selection replaces the 2nd one)
			items[1].setSelected(False)
		
		if l == 2:
			label1 = time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(items[0].revisionInfo['date']))
			label2 = time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(items[1].revisionInfo['date']))

			# try:			
			buffer1 = self._client.getFile('%s/revisions/%s' % (self._filename, items[0].revisionInfo['id']))
			buffer2 = self._client.getFile('%s/revisions/%s' % (self._filename, items[1].revisionInfo['id']))
			# except Exception, e: ...
			
			self._diffViewer.doDiff(label1, buffer1, label2, buffer2)

		if l < 2:
			self._diffViewer.clear()
		
		


################################################################################
# Remote file selector (read-only browsing)
################################################################################

################################################################################
# List Widget Items
################################################################################

class BaseListItem(QListWidgetItem):
	def __init__(self, path, parent = None):
		"""
		@type  path: string
		@param path: the abs path of the object within the docroot

		for instance:
		'/repository/samples/test.ats'
		'/repository'
		'/'
		"""
		QListWidgetItem.__init__(self, parent)
		self._path = path
		_, basename = os.path.split(path)
		display = basename
		if not display:
			display = "/"
		
		self.setText(display)

	def getUrl(self):
		"""
		Overridable.
		By default, returns an url based on the filepath.
		
		@rtype: QUrl
		@returns: the url of the object
		"""
		serverIp, serverPort = self.getClient().getServerAddress()
		url = "testerman://%s:%d%s" % (serverIp, serverPort, self._path)
		return QUrl(url)

	def getBasename(self):
		_, basename = os.path.split(self._path)
		return basename
	
	def getClient(self):
		return self.listWidget().getClient()


class DirListItem(BaseListItem):
	"""
	Directory/Folder
	"""
	def __init__(self, path, parent = None):
		BaseListItem.__init__(self, path, parent)
		self.setIcon(icon(':/icons/item-types/folder'))

class FileListItem(BaseListItem):
	"""
	Generic file.
	Since we use this item to display selectable
	object when saving a file to the repository,
	we don't need to support file types that
	will eventually be filtered out,
	i.e. we only support ats/module/campaign
	files, are they will be the only selectable
	objects.
	"""
	def __init__(self, path, parent = None):
		BaseListItem.__init__(self, path, parent)
		if path.endswith('.ats'):
			self.setIcon(icon(':/icons/item-types/ats'))
		elif path.endswith('.py'):
			self.setIcon(icon(':/icons/item-types/module'))
		elif path.endswith('.campaign'):
			self.setIcon(icon(':/icons/item-types/campaign'))
		else:
			self.setIcon(icon(':/icons/item-types/unknown'))

################################################################################
# Remote File Selector
################################################################################

class WRemoteFileListWidget(QListWidget):
	"""
	Remote browser, as a list, presenting a .. folder to go up
	and a context menu action to create a new folder.
	
	Can be restricted to browse a subtree of the docroot, using a "base path".
		
	Emits some signals:
	- dirChanged(QString path): the current dir has been changed. Path is a
	  docroot-path.
	- fileSelected(QUrl fileUrl): a file has been selected by activating it
	  (double-click, etc). fileUrl is the complete url to the file.
	"""
	def __init__(self, basePath = '/', path = '/', filter_ = None, parent = None):
		"""
		@type  basePath: string
		@param basePath: the "minimal" path; the user won't be able
		to browse outside it (docroot-relative)
		@type  path: string
		@param path: the current path (docroot-relative)
		@type  filter_: list of strings
		@param filter_: if None, all files are displayed. If set, only these
		file types are displayed. In any case, directories are shown.
		"""
		QListWidget.__init__(self, parent)

		self._client = None
		
		self.setWindowIcon(icon(':/icons/browser'))
		self.setWindowTitle('Remote file selector')

		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.connect(self, SIGNAL("itemActivated(QListWidgetItem*)"), self.onItemActivated)

		self._basePath = basePath
		self._path = basePath
		self.setPath(path)
		self._filter = []
		self.setFilter(filter_)

	def contextMenuEvent(self, event):
		item = self.itemAt(event.pos())
		
		menu = QMenu(self)
		# In any case, general action
		menu.addAction("New folder...", self.createFolder)
		menu.addSeparator()
		menu.addAction("Refresh", self.refresh)

		menu.popup(event.globalPos())

	def refresh(self):
		self.clear()
		try:
			l = self.getClient().getDirectoryListing(self._path)
		except Exception:
			l = []

		# If we can go up, create a pseudo item to display a ..
		if self._path > self._basePath:
			self.addItem(DirListItem('%s/%s' % (self._path, '..')))

		fileItems = []
		if l is not None:
			for entry in l:
				t = entry['type']
				if t == 'directory':
					child = DirListItem('%s/%s' % (self._path, entry['name']))
					# Directories added first - file item addition deferred
					self.addItem(child)
				elif self._filter is None or t in self._filter:
					child = FileListItem('%s/%s' % (self._path, entry['name']))
					# Deferred addition
					fileItems.append(child)

		for child in fileItems:
			self.addItem(child)

	def setFilter(self, filter_):
		"""
		Sets what file should be displayed.
		
		Set the filter_ to None to cancel any filtering.
		Directories cannot be filtered out, so no need to include
		their type ('directory') in the list.

		@type  filter_: list of strings
		@param filter_: a list of file types to be display (not extension,
		but type). Subset of: [ 'module', 'ats', 'campaign' ], etc.
		"""
		self._filter = filter_

	def setClient(self, client, autorefresh = True):
		self._client = client
		if autorefresh:
			self.refresh()

	def getClient(self):
		return self._client

	def getPath(self):
		return self._path

	def setPath(self, path):
		"""
		Sets the current path to path
		"""
		p = os.path.normpath(unicode(path))
		p = p.replace('\\', '/') # keep / as sep as we use the server convention
#		print "DEBUG: setting path to %s..." % p
		# Restrict to base path
		# FIXME - this allows something like /repository2 if /repository is the base path
		if not p.startswith(self._basePath):
			p = self._basePath
		self._path = p
		self.refresh()

	def createFolder(self):
#		print "DEBUG: creating a new folder in %s..." % self.getPath()
		(name, status) = QInputDialog.getText(self, "New folder", "Folder name:")
		while status and not validateDirectoryName(name):
			# Display some error message
			CommonWidgets.userError(self, "The following characters are forbidden in a folder name:\n%s" % ', '.join([x for x in RESTRICTED_NAME_CHARACTERS]))
			(name, status) = QInputDialog.getText(self, "New folder", "Folder name:")

		if not name.isEmpty():
			self._client.makeDirectory("%s/%s" % (self.getPath(), name))
			self.refresh()

	def onItemActivated(self, item):
		if isinstance(item, DirListItem):
			self.setPath(item.getUrl().path())
			self.emit(SIGNAL('dirChanged(QString)'), self.getPath())
		else:
			self.emit(SIGNAL('fileSelected(QUrl)'), item.getUrl())

class WRemoteFileDialog(QDialog):
	"""
	File selector.
	"""
	def __init__(self, client, basePath = '/repository', path = None, filter_ = None, defaultExtension = None, saveMode = False, parent = None):
		QDialog.__init__(self, parent)
		self._client = client
		self._defaultExtension = defaultExtension
		self._saveMode = saveMode
		if not path:
			path = basePath
		self.__createWidgets(basePath, path, filter_)
		
		if self._saveMode:
			self._okButton.setText("Save")
			self.setWarningOnOverwrite(True)
		
		self._selectedFilename = None
		
	def __createWidgets(self, basePath, path, filter_):
		self.setWindowIcon(icon(':/icons/browser'))
		self.setWindowTitle('Remote file selector')

		layout = QVBoxLayout()
		self._currentPathLabel = QLabel()
		layout.addWidget(self._currentPathLabel)
		
		self._listWidget = WRemoteFileListWidget(basePath, path, filter_)
		self._listWidget.setClient(self._client)
		# On double-click, equivalent to an accept. Ignore the selected file url.
		self.connect(self._listWidget, SIGNAL('fileSelected(QUrl)'), lambda url: self.accept())
		self.connect(self._listWidget, SIGNAL('dirChanged(QString)'), self.updateCurrentPathLabel)
		layout.addWidget(self._listWidget)
		layout.addWidget(QLabel('File name:'))
		self._filenameLineEdit = QLineEdit()
		layout.addWidget(self._filenameLineEdit)
		self.setLayout(layout)

		# Buttons
		self._okButton = QPushButton("Open")
		self.connect(self._okButton, SIGNAL("clicked()"), self.accept)
		self._cancelButton = QPushButton("Cancel")
		self.connect(self._cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self._okButton)
		buttonLayout.addWidget(self._cancelButton)
		layout.addLayout(buttonLayout)

		self.connect(self._listWidget, SIGNAL('currentItemChanged(QListWidgetItem*, QListWidgetItem*)'), self.onCurrentItemChanged)
		self.updateCurrentPathLabel(self._listWidget.getPath())
		self._filenameLineEdit.setFocus(Qt.OtherFocusReason)

	def updateCurrentPathLabel(self, path):
		if not path:
			path = '/'
		self._currentPathLabel.setText(path)

	def onCurrentItemChanged(self, current, previous):
		if isinstance(current, FileListItem):
			self._filenameLineEdit.setText(current.getBasename())

	def setWarningOnOverwrite(self, w):
		self._warningOnOverwrite = w

	def accept(self):
		filename = unicode(self._filenameLineEdit.text())
		if not filename:
			# Do not accept/close the window.
			return
		else:
			if self._saveMode:
				if self._defaultExtension and not filename.endswith(".%s" % self._defaultExtension):
					filename = "%s.%s" % (filename, self._defaultExtension)
				if not validateFileName(filename):
					CommonWidgets.userError(self, "The following characters are forbidden in a file name:\n%s" % ', '.join([x for x in RESTRICTED_NAME_CHARACTERS]))
					return

				# Set the complete selected file name
				self._selectedFilename = "%s/%s" % (self._listWidget.getPath(), filename)
				if self._warningOnOverwrite:
					# Check if the file exist - in real time, not based on the current view
					# (which may not be up-to-date)
					if self._client.fileExists(self._selectedFilename):
						if QMessageBox.warning(self, "Overwrite ?",
							"%s already exists.\nDo you want to overwrite it ?" % filename,
							QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) != QMessageBox.Yes:
							# Do not accept/close the window
							return
			
			else:
				# Set the complete selected file name
				self._selectedFilename = "%s/%s" % (self._listWidget.getPath(), filename)

			QDialog.accept(self)

	def getSelectedFilename(self):
		"""
		Compliant with QFileDialog:getOpen/SaveFileName() return.
		
		The returned result is only valid if the dialog has just been accepted.
		May contain garbage in other cases.
		"""
		if self._selectedFilename:
			return QString(self._selectedFilename)
		else:
			return QString()


##
# Convenience function to get a filename to use to save a file to the repository
##
def getSaveFileName(client, basePath = '/repository', dir = '', caption = "Save file as...", filter_ = None, defaultExtension = None, parent = None):
	"""
	Convenience function.

	Returns a QString with a path to use to save a file, 
	or an empty string if no name has been selected (or dialog box cancelled)
	"""
	if not dir:
		dir = basePath
	dialog = WRemoteFileDialog(client, basePath, dir, filter_, defaultExtension, saveMode = True, parent = parent)
	dialog.setWindowTitle(caption)
	if dialog.exec_() == QDialog.Accepted:
		return dialog.getSelectedFilename()
	else:
		return QString()




################################################################################
# File Explorer (as a tree view), with R/W actions
################################################################################

################################################################################
# Tree Widget Items
################################################################################

class BaseWidgetItem(QTreeWidgetItem):
	def __init__(self, path, parent = None):
		"""
		@type  path: string
		@param path: the abs path of the object within the docroot
		
		for instance:
		'/repository/samples/test.ats'
		'/repository'
		'/'
		"""
		QTreeWidgetItem.__init__(self, parent)
		self._flags = 0
		self._path = path  # complete path
		_, basename = os.path.split(path)
		display = basename
		if not display:
			display = "/"
		self.setText(0, display)
		self.updateFlags()
	
	def updateFlags(self):
		self.setFlags(Qt.ItemIsEnabled)

	def getClient(self):
		return self.treeWidget().getClient()
	
	def isRenameable(self):
		return self.flags() & Qt.ItemIsEditable
	
	def isCopyable(self):
		return self.flags() & Qt.ItemIsDragEnabled

	def isMoveable(self):
		return self.flags() & Qt.ItemIsDragEnabled
	
	def shouldRetainExtensionOnRename(self):
		return True

	def onDropMimeData(self, data, action):
		"""
		Called when some mime data are dropped on the item,
		with the specified action.
		"""
		pass

	def getUrl(self):
		"""
		Overridable.
		By default, returns an url based on the filepath.
		
		@rtype: QUrl
		@returns: the url of the object
		"""
		serverIp, serverPort = self.getClient().getServerAddress()
		url = "testerman://%s:%d%s" % (serverIp, serverPort, self._path)
		return QUrl(url)
	
	def getBasename(self):
		_, basename = os.path.split(self._path)
		return basename

	def setBasename(self, basename):
		basepath, _ = os.path.split(self._path)
		self._path = "%s/%s" % (basepath, basename)
		self.setText(0, basename)
#		print "DEBUG: new file path: %s" % self._path

	def isAts(self):
		return isinstance(self, AtsWidgetItem)

	def isExecutionLog(self):
		return isinstance(self, ExecutionLogWidgetItem)

	def isModule(self):
		return isinstance(self, ModuleWidgetItem)

	def isCampaign(self):
		return isinstance(self, CampaignWidgetItem)

	def isDir(self):
		return isinstance(self, DirWidgetItem)

	def isExpandable(self):
		return isinstance(self, ExpandableWidgetItem)
	
	def isPackageRootDir(self):
		return isinstance(self, PackageDirWidgetItem)

	def isPackageProfilesDir(self):
		return isinstance(self, PackageProfilesDirWidgetItem)

	def isPackageSrcDir(self):
		return isinstance(self, PackageSrcDirWidgetItem)

	def isProfile(self):
		return isinstance(self, ProfileWidgetItem)

	def isProfilesDir(self):
		return isinstance(self, ProfilesDirWidgetItem)
	
	def isPackageDescription(self):
		return isinstance(self, PackageDescriptionWidgetItem)

	def isVirtual(self):
		return False
	
	def isLocked(self):
		# A locked file is a file that is within a locked package.
		# TODO: implement me (especially for a PackageDir)
		return False

	def getParentPackageRootDir(self):
		item = self
		while item and item != self.treeWidget():
			if item.isPackageRootDir():
				return item
			item = item.parent()
		return None
	
	def isInPackageTree(self):
		if self.getParentPackageRootDir():
			return True
		else:
			return False

	def isInPackageProfilesTree(self):
		item = self
		while item and item != self.treeWidget():
			if item.isPackageProfilesDir():
				return True
			if item.isPackageRootDir():
				# Break the search once we reached a package root
				return False
			item = item.parent()
		return False
	
	def isInPackageSrcTree(self):
		item = self
		while item and item != self.treeWidget():
			if item.isPackageSrcDir():
				return True
			if item.isPackageRootDir():
				# Break the search once we reached a package root
				return False
			item = item.parent()
		return False


class AsyncFetchingThread(QThread):
	"""
	This worker thread calls the fetching method to get child items.
	Works with a lazyExpander.
	"""
	def __init__(self, asyncExpander, parent = None):
		QThread.__init__(self, parent)
		self._asyncExpander = asyncExpander
	
	def run(self):
		try:
			self._asyncExpander._fetchedChildItemData = self._asyncExpander._fetcher()
		except Exception, e:
			pass
		self.emit(SIGNAL("fetched"))
		self.exec_()

class AsyncExpander(QObject):
	"""
	Decorator class over a WidgetItem, enabling
	to turn it into a lazy expanding node, fetching
	children asynchronously calling the fetcher command,
	which returns a list of unparented nodes.
	
	Usage:
	AsyncExpander(item, fetchFunction, addChildrenFunction).expand()
	
	where fetchFunction() returns a list of data that will be passed to
	addChildrenFunction(data) when retrieved, once the fetching thread
	is over.
	
	
	NB: we use a wrapper/decorator design pattern instead of
	a subclassing (embedding async expanding capability into
	ExpandableWidgetItem) to be able to apply it to the
	invisibleRootItem() of the main QTreeWidget.
	"""
	
	def __init__(self, item, fetchFunction, addChildrenFunction):
		QObject.__init__(self)
		self._item = item
		self._fetcher = fetchFunction
		self._adder = addChildrenFunction
		self._fetchedChildItemData = []
		self.loadingItem = None
		self.loadingAnimation = None
		self.fetchingThread = None

	def expand(self):
		"""
		Expands the decorated QTreeWidgetItem.
		
		Starts a thread to fetch the child items, and during
		this displays a loading icon.
		On completion, the loading icon animation will be stopped and the 
		fetched child items are added.
		"""
		self._item.takeChildren()
		# Display a loading item
		self._loading()
		# Call our item feeder in a worker thread
		self.fetchingThread = AsyncFetchingThread(self)
		self.connect(self.fetchingThread, SIGNAL("fetched"), self._childItemsFetched)
		self.fetchingThread.start()
	
	def _loading(self):
		"""
		Displays a loading, animated icon as a single child
		"""
		self.loadingItem = QTreeWidgetItem(self._item)
		self.loadingItem.setText(0, "Loading...")
		f = self.loadingItem.font(0)
		f.setStyle(QFont.StyleItalic)
		self.loadingItem.setFont(0, f)
		self.loadingAnimation = QMovie(':/animations/loading-subtree')
		self.loadingAnimation.connect(self.loadingAnimation, SIGNAL("updated(const QRect&)"), lambda rect: self.loadingItem.setIcon(0, QIcon(self.loadingAnimation.currentPixmap())))
		self.loadingAnimation.start()
	
	def _loaded(self):
		"""
		Removes the loading, animated icon added by _loading(),
		add the fetched child items to the expanded node.
		"""
		self.loadingAnimation.stop()
		self._item.removeChild(self.loadingItem)
		self._adder(self._fetchedChildItemData)
		del self.loadingItem
		del self.loadingAnimation
		try:
			self._item.onExpanded()
		except:
			pass
	
	def _childItemsFetched(self):
		"""
		Called when the fetching is over. Removes the loading indicator,
		adds the fetched items.
		"""
		self._loaded()
		self.fetchingThread.quit()


class ExpandableWidgetItem(BaseWidgetItem):
	"""
	Base class for nodes that can be expanded.
	Will be wrapped into a AsyncExpander when expanding.
	
	Provides a way to get children asynchronously.
	
	First, the fetchChildItems method is called from
	an async, worker thread. 
	It should returns a list of (cls, parameters) where cls is
	the class of the QWidgetItem to add, and parameters is a list of
	its constructor parameters to apply (no parent should be provided).
	
	These construction info are used later, from the main GUI thread,
	to instanciate and add the child items actually .

	They should be created in the main GUI thread to avoid some
	internal Qt race conditions, especially regarding icons/pixmaps.
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)

	def fetchChildItems(self):
		"""
		To override.
		Returns a list of any data that will be passed transparently to 
		a call to addFetchedChildItems(data) from the main GUI thread later.
		
		This method is called in a worker (non GUI) thread.
		"""
		return []
	
	def addFetchedChildItems(self, data):
		"""
		Creates and appends the items from the fetched data.
		Called from the main GUI thread.
		"""
		pass
	
	def onExpanded(self):
		"""
		To override. Called when the node has been
		expanded and its children loaded and displayed.
		"""
		pass


class DirWidgetItem(ExpandableWidgetItem):
	"""
	Directory/Folder
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/folder'))

	def updateFlags(self):
		# In a package tree, we can't drop a file in it.
		# But outside, we can
		if self.isInPackageSrcTree():
			self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
		else:
			self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)

	def fetchChildItems(self):
		# The implementation is in the treewidget because it also
		# needs such a function.
		# The delegation cannot be performed the other way because
		# when the treewidget fetches its children, it cannot have
		# any DirWidgetItem (all its children are removed in the meanwhile).
		return self.treeWidget().fetchChildItems(self._path)

	def addFetchedChildItems(self, data):
		return self.treeWidget().addFetchedChildItems(data, self._path, self)

	def onExpanded(self):
		"""
		Re-implemented from ExpandableWidgetItem.
		Xc-Subscribes for updates regarding this directory.
		"""
		self._subscribe()

	def _subscribe(self):
		self.getClient().subscribe('filesystem:%s' % self.getUrl().path(), self._onFileSystemNotification)
	
	def onCollapsed(self):
		"""
		Re-implemented from ExpandableWidgetItem.
		Xc-Unsubscribes for updates regarding this directory.
		"""
		self._unsubscribe()
	
	def _unsubscribe(self):
		self.getClient().unsubscribe('filesystem:%s' % self.getUrl().path(), self._onFileSystemNotification)

	def setBasename(self, basename):
		"""
		Reimplemented to support resubscription.
		"""
		self._unsubscribe()
		ExpandableWidgetItem.setBasename(self, basename)
		self._subscribe()

	def __del__(self):
		self.onCollapsed()
		ExpandableWidgetItem.__del__(self)
	
	def _onFileSystemNotification(self, notification):
		"""
		Callback called whenever a file system notification occurs related
		to this directory.
		"""
		if notification.getMethod() != 'FILE-EVENT':
			return
		# Delta deletion or addition
		reason = notification.getHeader('Reason')
		name = notification.getHeader('File-Name')
#		print "DEBUG: file event notification on uri %s: '%s' %s" % (notification.getUri(), name, reason)
		if reason == 'deleted':
			# name, which is an item in this folder, has been deleted.
			# Find it and delete it.
			for i in range(0, self.childCount()):
				item = self.child(i)
				if item.getBasename() == name:
					self.removeChild(item)
					break
		elif reason == 'created':
			# a new item name has been created
			applicationType = notification.getHeader('File-Type')
			# Reimplemented in DirWidgetItem subclasses
			self.addFetchedChildItems([{'name': name, 'type': applicationType}])
		elif reason == 'renamed':
			newname = notification.getHeader('File-New-Name')
#			print "DEBUG: file event notification on uri %s: '%s' %s to '%s'" % (notification.getUri(), name, reason, newname)
			if newname:
				for i in range(0, self.childCount()):
					item = self.child(i)
					if item.getBasename() == name:
						item.setBasename(newname)

	def shouldRetainExtensionOnRename(self):
		return False

	def onDropMimeData(self, data, action):
		"""
		Accept file copy in this folder.
		"""
		if data.hasUrls() and action == Qt.CopyAction:
			destination = self.getUrl().path()
			sources = data.urls()
			if self.isInPackageTree():
				self.treeWidget()._importItems(sources, destination)
			else:
				self.treeWidget()._copyItems(sources, destination)
	

class AtsWidgetItem(ExpandableWidgetItem):
	"""
	ATS Document.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/ats'))

	def updateFlags(self):
		# You can drag a file on an ATS to do a diff
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable | Qt.ItemIsDropEnabled)

	def addFetchedChildItems(self, data):
		if not self.isInPackageTree():
			self.addChild(ProfilesDirWidgetItem(self._path + '/profiles'))
		self.addChild(ExecutionLogsWidgetItem(self._path))

	def onDropMimeData(self, data, action):
		"""
		Accept copy action to display a diff between the dropped file and the current one.
		"""
		if data.hasUrls() and action == Qt.CopyAction:
			file1 = unicode(self.getUrl().path())
			file2 = unicode(data.urls()[0].path())
		
			transient = CommonWidgets.WTransientWindow()
			transient.showTextLabel("Preparing diff between\n%s\nand\n%s..." % (file1, file2))
			try:
				buffer1 = self.treeWidget().getClient().getFile(file1)
				buffer2 = self.treeWidget().getClient().getFile(file2)
			except Exception, e:
				CommonWidgets.systemError(self.treeWidget(), "Unable to get at least one file for file comparison:\n%s" % str(e))
				return
			finally:
				transient.dispose()
			diffViewer = Compare.WCompareWidget(self.treeWidget())
			diffViewer.doDiff(file1, buffer1, file2, buffer2)
			diffViewer.setWindowFlags(Qt.Window)
			diffViewer.show()


class ModuleWidgetItem(BaseWidgetItem):
	"""
	Module Document.
	This node is not expandable as there are no associated profiles,
	and revisions are managed via a dedicated dialog box.
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/module'))

	def updateFlags(self):
		# You can drag a file on a Module to do a diff
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable | Qt.ItemIsDropEnabled)

	def onDropMimeData(self, data, action):
		"""
		Accept copy action to display a diff between the dropped file and the current one.
		"""
		if data.hasUrls() and action == Qt.CopyAction:
			file1 = unicode(self.getUrl().path())
			file2 = unicode(data.urls()[0].path())
		
			transient = CommonWidgets.WTransientWindow()
			transient.showTextLabel("Preparing diff between\n%s\nand\n%s..." % (file1, file2))
			try:
				buffer1 = self.treeWidget().getClient().getFile(file1)
				buffer2 = self.treeWidget().getClient().getFile(file2)
			except Exception, e:
				CommonWidgets.systemError(self.treeWidget(), "Unable to get at least one file for file comparison:\n%s" % str(e))
				return
			finally:
				transient.dispose()
			diffViewer = Compare.WCompareWidget(self.treeWidget())
			diffViewer.doDiff(file1, buffer1, file2, buffer2)
			diffViewer.setWindowFlags(Qt.Window)
			diffViewer.show()

class CampaignWidgetItem(ExpandableWidgetItem):
	"""
	Campaign Document.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/campaign'))

	def updateFlags(self):
		# You can drag a file on a Campaign to do a diff
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable | Qt.ItemIsDropEnabled)

	def addFetchedChildItems(self, data):
		if not self.isInPackageTree():
			self.addChild(ProfilesDirWidgetItem(self._path + '/profiles'))
		self.addChild(ExecutionLogsWidgetItem(self._path))

	def onDropMimeData(self, data, action):
		"""
		Accept copy action to display a diff between the dropped file and the current one.
		"""
		if data.hasUrls() and action == Qt.CopyAction:
			file1 = unicode(self.getUrl().path())
			file2 = unicode(data.urls()[0].path())
		
			transient = CommonWidgets.WTransientWindow()
			transient.showTextLabel("Preparing diff between\n%s\nand\n%s..." % (file1, file2))
			try:
				buffer1 = self.treeWidget().getClient().getFile(file1)
				buffer2 = self.treeWidget().getClient().getFile(file2)
			except Exception, e:
				CommonWidgets.systemError(self.treeWidget(), "Unable to get at least one file for file comparison:\n%s" % str(e))
				return
			finally:
				transient.dispose()
			diffViewer = Compare.WCompareWidget(self.treeWidget())
			diffViewer.doDiff(file1, buffer1, file2, buffer2)
			diffViewer.setWindowFlags(Qt.Window)
			diffViewer.show()

class ExecutionLogsWidgetItem(ExpandableWidgetItem):
	"""
	Virtual folder containing execution logs for
	a script.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/folder-virtual'))
		self.setText(0, 'Executions')
	
	def fetchChildItems(self):
		ret = []
		try:
			# Compute the corresponding archive path for this ATS
			archivePath = '/archives/%s' % ('/'.join(self._path.split('/')[2:]))
			l = self.getClient().getDirectoryListing(archivePath)
			for entry in l:
				if entry['type'] == 'log':
					ret.append('%s/%s' % (archivePath, entry['name']))
		except Exception, e:
			print "DEBUG: " + str(e)
		return ret

	def addFetchedChildItems(self, data):
		# More recent executions first
		data.sort(reverse = True)
		for name in data:
			item = ExecutionLogWidgetItem(name)
			self.addChild(item)

	def getUrl(self):
		return None


class ExecutionLogWidgetItem(BaseWidgetItem):
	"""
	Execution log associated to a script, within
	a virtual folder.
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/execution-log'))

		_, name = os.path.split(path)
		display = "(invalid log filename)"
		# According to the name, retrieve some additional info.
		m = re.match(r'([0-9-]+)_(.*)\.log', name)
		if m:
			date = m.group(1)
			username = m.group(2)
			display = "%s, by %s" % (date, username)
		self.setText(0, display)

	def updateFlags(self):
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

	def isVirtual(self):
		return True
				
class LogWidgetItem(BaseWidgetItem):
	"""
	Execution log, as a document (from the Archive view)
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/execution-log'))

	def updateFlags(self):
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

class ProfilesDirWidgetItem(ExpandableWidgetItem):
	"""
	Virtual folder containing the profiles associated to
	an executable script.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/folder-package-profiles'))
		self.setText(0, 'Profiles')

	def updateFlags(self):
		# Allow file drop in it (provided this is a profile)
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

	def fetchChildItems(self):
		ret = []
		try:
			l = self.getClient().getDirectoryListing(self._path)
			for entry in l:
				if entry['type'] == 'profile':
					ret.append('%s/%s' % (self._path, entry['name']))
		except Exception, e:
			print "DEBUG: " + str(e)
		return ret

	def addFetchedChildItems(self, data):
		data.sort()
		for name in data:
			item = ProfileWidgetItem(name)
			self.addChild(item)

	def onExpanded(self):
		"""
		Re-implemented from ExpandableWidgetItem.
		Xc-Subscribes for updates regarding this directory.
		"""
		self._subscribe()

	def _subscribe(self):
		self.getClient().subscribe('filesystem:%s' % self.getUrl().path(), self._onFileSystemNotification)
	
	def onCollapsed(self):
		"""
		Re-implemented from ExpandableWidgetItem.
		Xc-Unsubscribes for updates regarding this directory.
		"""
		self._unsubscribe()
	
	def _unsubscribe(self):
		self.getClient().unsubscribe('filesystem:%s' % self.getUrl().path(), self._onFileSystemNotification)

	def __del__(self):
		self.onCollapsed()
		ExpandableWidgetItem.__del__(self)
	
	def _onFileSystemNotification(self, notification):
		"""
		Callback called whenever a file system notification occurs related
		to this directory.
		"""
		if notification.getMethod() != 'FILE-EVENT':
			return
		# Delta deletion or addition
		reason = notification.getHeader('Reason')
		name = notification.getHeader('File-Name')
#		print "DEBUG: file event notification on uri %s: '%s' %s" % (notification.getUri(), name, reason)
		if reason == 'deleted':
			# name, which is an item in this folder, has been deleted.
			# Find it and delete it.
			for i in range(0, self.childCount()):
				item = self.child(i)
				if item.getBasename() == name:
					self.removeChild(item)
					break
		elif reason == 'created':
			# a new item name has been created
			applicationType = notification.getHeader('File-Type')
			self.addFetchedChildItems([name])
		elif reason == 'renamed':
			newname = notification.getHeader('File-New-Name')
#			print "DEBUG: file event notification on uri %s: '%s' %s to '%s'" % (notification.getUri(), name, reason, newname)
			if newname:
				for i in range(0, self.childCount()):
					item = self.child(i)
					if item.getBasename() == name:
						item.setBasename(newname)

	def onDropMimeData(self, data, action):
		"""
		Accept file copy in this folder.
		
		TODO: only copy profile files here
		"""
		if data.hasUrls() and action == Qt.CopyAction:
			destination = self.getUrl().path()
			sources = data.urls()
			self.treeWidget()._copyItems(sources, destination)


class ProfileWidgetItem(BaseWidgetItem):
	"""
	Execution profile
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/profile'))

	def updateFlags(self):
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)


##
# Package-specific items
##
class PackageDirWidgetItem(DirWidgetItem):
	"""
	Package (the folder).
	Such a folder may be renamed, as it is a root for its contained
	files. Renaming it won't break any dependencies.
	"""
	def __init__(self, path, parent = None):
		DirWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/folder-package'))

	def updateFlags(self):
		# Well, isEditable should be set only if unlocked.
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

	def fetchChildItems(self):
		try:
			l = self.getClient().getDirectoryListing(self._path)
		except Exception:
			l = []
		return l
	
	def addFetchedChildItems(self, data):
		"""
		Data is what is returned by fetchChildItems().
		"""
		for entry in data:
			child = None
			fullpath = '%s/%s' % (self._path, entry['name'])
			if entry['type'] == 'directory':
				if entry['name'] == 'src':
					child = PackageSrcDirWidgetItem(fullpath)
				elif entry['name'] == 'profiles':
					child = PackageProfilesDirWidgetItem(fullpath)
			elif entry['type'] == 'package-metadata':
				child = PackageDescriptionWidgetItem(fullpath)

			if child:
				self.addChild(child)
	

class PackageSrcDirWidgetItem(DirWidgetItem):
	"""
	This item represents the package/src folder.
	"""
	def __init__(self, path, parent = None):
		DirWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/folder-package-src'))

	def updateFlags(self):
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

class PackageProfilesDirWidgetItem(DirWidgetItem):
	"""
	This item represents the package/profiles folder.
	"""
	def __init__(self, path, parent = None):
		DirWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/folder-package-profiles'))

	def updateFlags(self):
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

	def fetchChildItems(self):
		try:
			l = self.getClient().getDirectoryListing(self._path)
		except Exception:
			l = []
		return l

class PackageDescriptionWidgetItem(BaseWidgetItem):
	"""
	The package.xml file.
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/item-types/package-metadata'))

	def updateFlags(self):
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)


################################################################################
# Local Dialogs
################################################################################

class WImportConfirmation(QDialog):
	"""
	A dialog that displays the files, including dependencies,
	to import to a package.
	Displayed when drag&dropping something to the src folder of a package.
	"""
	def __init__(self, filesToCreate, title, parent = None, size = None):
		QDialog.__init__(self, parent)
		self._filesToCreate = filesToCreate
		self._title = title
		self.__createWidgets()
		if not size:
			size = QSize(600, 400) # an arbitrary default size
		self.resize(size)

	def __createWidgets(self):
		self.setWindowTitle(self._title)

		layout = QVBoxLayout()
		# A label		
		layout.addWidget(QLabel("This will create the following files in the package (existing files will be overwritten):"))
		# The list of files
		self._textEdit = QTextEdit(self)
		self._textEdit.setPlainText("\n".join(self._filesToCreate))
		self._textEdit.setReadOnly(True)
		layout.addWidget(self._textEdit)
		defaultFont = QFont("courier", 8)
		defaultFont.setFixedPitch(True)
		self._textEdit.setFont(defaultFont)

		# Buttons
		self._okButton = QPushButton("Import")
		self.connect(self._okButton, SIGNAL("clicked()"), self.accept)
		self._cancelButton = QPushButton("Cancel")
		self.connect(self._cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self._okButton)
		buttonLayout.addWidget(self._cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

################################################################################
# Tree Widget
################################################################################

class WServerFileSystemTreeWidget(QTreeWidget):
	"""
	Remote file system explorer.

	This treeview is responsible for interfacing most filesystem-related actions,
	including application specificities.
	Some actions are said "local" are implemented by the widget -
	they are actions whose scope is the file system itself.
	Some others triggers an action elsewhere in the embedding application. In 
	this case they require a controller object to bridge signals emitted by
	the widget with external actions.
	
	Local actions:
	- file system related: delete (ats/campaign/module/log/empty dir),
	  rename (ats/campaign/package only, to avoid major breaks when renaming a whole dir tree),
		copy (dir/ats/campaign/module),
		(move disabled for now)
	- view related: refresh (all, subtree)
	
	Notes:
	- folder renaming is disabled on purpose. Could create havoks breaking
	  (a lot of) modules too easily.
	- folder moving is disabled for the same reasons.
	- this is a passive view over the remote file system: whenever
	  we attempt a file action (delete/renamed/copy/etc), the action is triggered
	  on the server through the view, then the view is notified back by the server
	  asynchronously. As a consequence, the view should not remove/add items on its
	  own: the (remote) model will do it.
	
	External actions:
	- open (for edition) : emit SIGNAL('openUrl(const QUrl&)')
	"""
	def __init__(self, path = '/', parent = None):
		QTreeWidget.__init__(self, parent)

		self._client = None
		
		self.setWindowIcon(icon(':/icons/browser'))
		self.setWindowTitle('Remote explorer')

		self.setHeaderLabels([ 'Name' ])

		# Experiment: hide the header, only one section ('name')
#		self.setHeaderHidden(True)

		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.connect(self, SIGNAL("itemExpanded(QTreeWidgetItem*)"), self.onItemExpanded)
		self.connect(self, SIGNAL("itemCollapsed(QTreeWidgetItem*)"), self.onItemCollapsed)
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
		self.connect(self, SIGNAL("itemChanged(QTreeWidgetItem*, int)"), self.onItemChanged)
		
		# Multiple selection mode would make file moves a bit weird,
		# as we may select a folder and files in this folder (or any child) to move
		# to the same final place, etc.
		# Sticking to single selection mode makes everything easier,
		# except multiple files (typically logs) deletion.
		#self.setSelectionMode(self.ExtendedSelection)
		
		self.setAcceptDrops(True)
		self.setDragEnabled(True)
		self.setDropIndicatorShown(True)
		self.setAutoScroll(True)
		self.setSortingEnabled(True)
		self.header().setSortIndicator(0, Qt.AscendingOrder)
		self.setTextElideMode(Qt.ElideNone)

		self.setEditTriggers(QAbstractItemView.EditKeyPressed)
		
		self._path = path
		
	def onItemActivated(self, item, column):
		# Default action: open attempt
		self._open(item)
	
	def onItemExpanded(self, item):
		"""
		We can only expand items subclassing ExpandableWidgetItem.
		We decorate them with the asynchronous expander.
		"""
		AsyncExpander(item, item.fetchChildItems, item.addFetchedChildItems).expand()

	def onItemCollapsed(self, item):
		try:
			item.onCollapsed()
		except:
			# Ignore inexistent attributes
			pass

	def contextMenuEvent(self, event):
		item = self.itemAt(event.pos())
		
		menu = QMenu(self)
		
		if item:
			# Depending of the node, add several actions
			if item.isAts():
				menu.addAction("Edit (head)", lambda: self._open(item))
				menu.addAction("Show revisions...", lambda: self._showRevisions(item))
				menu.addAction("Show dependencies...", lambda: self._showDependencies(item))
				menu.addAction("Delete", lambda: self._deleteAts(item))
			elif item.isExecutionLog():
				menu.addAction("Open", lambda: self._open(item))
				menu.addAction("Delete", lambda: self._deleteExecutionLog(item))
			elif item.isModule():
				menu.addAction("Edit (head)", lambda: self._open(item))
				menu.addAction("Show revisions...", lambda: self._showRevisions(item))
				menu.addAction("Show dependencies...", lambda: self._showDependencies(item))
				menu.addAction("Show referrer files...", lambda: self._showModuleReverseDependencies(item))
				menu.addAction("Delete", lambda: self._deleteModule(item))
			elif item.isCampaign():
				menu.addAction("Edit (head)", lambda: self._open(item))
				menu.addAction("Show revisions...", lambda: self._showRevisions(item))
				menu.addAction("Show dependencies...", lambda: self._showDependencies(item))
				menu.addAction("Delete", lambda: self._deleteCampaign(item))
			elif item.isPackageRootDir():
				menu.addAction("Export package...", lambda: self._exportPackage(item))
				if not item.isLocked():
					menu.addAction("Lock package...", lambda: self._notYetImplemented())
				else:
					menu.addAction("Unlock package...", lambda: self._notYetImplemented())
			elif item.isPackageProfilesDir():
				menu.addAction("New folder...", lambda: self._createDirectory(item))
			elif item.isPackageSrcDir():
				menu.addAction("New folder...", lambda: self._createDirectory(item))
			elif item.isProfilesDir():
				# Profiles cannot be created from here any more.
				# You need to first open the script and add a new profile from
				# its editor's embedded profile editor.
				pass
			elif item.isProfile():
				# No direct edition: a profile is exclusively edited via its associated script
#				if item.isInPackageProfilesTree():
#					menu.addAction("Run package with this profile", lambda: self._notYetImplemented())
#				else:
#					menu.addAction("Run script with this profile", lambda: self._notYetImplemented())
				menu.addAction("Delete", lambda: self._deleteProfile(item))
			elif item.isPackageDescription():
				menu.addAction("Edit", lambda: self._open(item))
			elif item.isDir():
				menu.addAction("New folder...", lambda: self._createDirectory(item))
				if not item.isInPackageProfilesTree():
					menu.addAction("New package...", lambda: self._createPackage(item))
					menu.addAction("Import package here...", lambda: self._importPackage(item))
				menu.addAction("Delete", lambda: self._deleteDirectory(item))

			if item.isExpandable():
				menu.addSeparator()
				menu.addAction("Refresh", lambda: self._refresh(item))

			menu.addSeparator()

		# In any case, general action
		menu.addAction("Refresh all", self.refresh)
		
		menu.popup(event.globalPos())

	def refresh(self):
		self._unsubscribe()
		AsyncExpander(self.invisibleRootItem(), self.fetchChildItems, self.addFetchedChildItems).expand()
		self._subscribe()
	
	def setClient(self, client, autorefresh = True):
		self._client = client
		if autorefresh:
			self.refresh()
	
	def getClient(self):
		return self._client

	def _subscribe(self):
		self.getClient().subscribe('filesystem:%s' % self._path, self._onFileSystemNotification)
	
	def _unsubscribe(self):
		self.getClient().unsubscribe('filesystem:%s' % self._path, self._onFileSystemNotification)
	
	def _onFileSystemNotification(self, notification):
		"""
		Callback called whenever a file system notification occurs related
		to this directory.
		"""
		if notification.getMethod() != 'FILE-EVENT':
			return
		
		node = self.invisibleRootItem()
		# Delta deletion or addition
		reason = notification.getHeader('Reason')
		name = notification.getHeader('File-Name')
#		print "DEBUG: file event notification on uri %s: '%s' %s" % (notification.getUri(), name, reason)
		if reason == 'deleted':
			# name, which is an item in this folder, has been deleted.
			# Find it and delete it.
			for i in range(0, node.childCount()):
				item = node.child(i)
				if item.getBasename() == name:
					node.removeChild(item)
					break
		elif reason == 'created':
			# a new item name has been created
			applicationType = notification.getHeader('File-Type')
			# Reimplemented in DirWidgetItem subclasses
			self.addFetchedChildItems([{'name': name, 'type': applicationType}])
		elif reason == 'renamed':
			newname = notification.getHeader('File-New-Name')
#			print "DEBUG: file event notification on uri %s: '%s' %s to '%s'" % (notification.getUri(), name, reason, newname)
			if newname:
				for i in range(0, node.childCount()):
					item = node.child(i)
					if item.getBasename() == name:
						item.setBasename(newname)

	def fetchChildItems(self, path = None):
		"""
		Fetches children on behalf of a DirItem.
		(Implemented here to support the 'invisible root item' transparently).
		
		This function is called within a worker thread.
		"""
		if path is None:
			path = self._path
		try:
			l = self.getClient().getDirectoryListing(path)
		except Exception:
			l = []
		return l

	def addFetchedChildItems(self, data, path = None, parent = None):
		if path is None:
			path = self._path
		if parent is None:
			parent = self.invisibleRootItem()
		for entry in data:
			fullpath = '%s/%s' % (path, entry['name'])
			if entry['type'] == 'directory':
				child = DirWidgetItem(fullpath)
			elif entry['type'] == 'ats':
				child = AtsWidgetItem(fullpath)
			elif entry['type'] == 'log':
				child = ExecutionLogWidgetItem(fullpath)
			elif entry['type'] == 'campaign':
				child = CampaignWidgetItem(fullpath)
			elif entry['type'] == 'module':
				child = ModuleWidgetItem(fullpath)
			elif entry['type'] == 'package':
				child = PackageDirWidgetItem(fullpath)
			elif entry['type'] == 'profile':
				child = ProfileWidgetItem(fullpath)
			else:
				child = None
			if child:
				parent.addChild(child)
				child.updateFlags()

	##
	# Local actions
	##
	def _notYetImplemented(self):
		CommonWidgets.userInformation(self, "This action is not yet implemented.")

	def _refresh(self, item):
		self.collapseItem(item)
		self.expandItem(item)

	def _showModuleReverseDependencies(self, item):
		"""
		Displays the files referencing the module.
		"""
		path = unicode(item.getUrl().path())
		transient = CommonWidgets.WTransientWindow()
		transient.showTextLabel("Getting reverse dependencies...")
		try:
			deps = self.getClient().getReverseDependencies(path)
			deps.sort()
		except Exception, e:
			CommonWidgets.systemError(self, "Unable to get reverse dependencies for this file:\n%s" % str(e))
			return
		transient.dispose()
		dialog = CommonWidgets.WTextEditDialog('\n'.join(deps), "Files referencing module %s: %d files(s)" % (os.path.split(path)[1], len(ret)), 
			readOnly = True, parent = self, fixedFont = True)
		dialog.exec_()

	def _deleteAts(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete ATS", "Are you sure you want to delete the ATS %s ?" % item.getBasename(), 
				[('Also delete associated execution logs', True)], parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().deleteAts(unicode(url.path()), dialog.isChecked(0))
				if not ret:
					# Display an error message ?
					pass

	def _deleteCampaign(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete Campaign", "Are you sure you want to delete the campaign %s ?" % item.getBasename(), 
				[('Also delete associated execution logs', True)], parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().deleteCampaign(unicode(url.path()), dialog.isChecked(0))
				if not ret:
					# Display an error message ?
					pass

	def _deleteModule(self, item):
		url = item.getUrl()
		if url:
			b = QMessageBox.warning(self, "Delete Module", "Deleting a module may break a lot of existing ATSes or other modules. Are you sure you want to delete the module %s ?" % item.getBasename(), 
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if b == QMessageBox.Yes:
				ret = self.getClient().removeFile(unicode(url.path()))
				if not ret:
					# Display an error message ?
					pass

	def _deleteDirectory(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete Folder", "Are you sure you want to delete the folder %s ?" % item.getBasename(), parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().removeDirectory(unicode(url.path()), False)
				if not ret:
					CommonWidgets.userInformation(self, "Unable to delete folder %s: not empty" % os.path.split(unicode(url.path()))[1])

	def _deleteExecutionLog(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete Execution Log", "Are you sure you want to delete this execution log ?", parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().deleteExecutionLog(unicode(url.path()), True)
				if ret:
					# Local view removal: the server does not notify us for now
					item.parent().removeChild(item)
				else:
					# Display an error message ?
					pass

	def _deleteProfile(self, item):
		url = item.getUrl()
		print "DEBUG: url: %s" % unicode(url.path())
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete profile", "Are you sure you want to delete the profile %s ?" % item.getBasename(), parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().deleteProfile(unicode(url.path()))
				if not ret:
					# Display an error message ?
					pass

	def _showDependencies(self, item):
		path = unicode(item.getUrl().path())
		transient = CommonWidgets.WTransientWindow()
		transient.showTextLabel("Getting dependencies list...")
		try:
			deps = self.getClient().getDependencies(path)
			deps.sort()
		except Exception, e:
			CommonWidgets.systemError(self, "Unable to get dependencies for this file:\n%s" % str(e))
			return
		transient.dispose()
		dialog = CommonWidgets.WTextEditDialog('\n'.join(deps), "File dependencies for %s" % os.path.split(path)[1],
			readOnly = True, parent = self, fixedFont = True)
		dialog.exec_()
	
	def _showRevisions(self, item):
		path = unicode(item.getUrl().path())
		transient = CommonWidgets.WTransientWindow()
		transient.showTextLabel("Getting revisions list...")
		revisions = None
		try:
			revisions = self.getClient().getDirectoryListing(path + '/revisions')
		except Exception, e:
			pass
		transient.dispose()
		if revisions is None:
			CommonWidgets.userInformation(self, "No revisions found for this file.")
			return
		
		# Display revisions in a dedicated dialog box that include easy diff management
		dialog = WRevisionsDialog(filename = path, revisions = [ x['revision'] for x in revisions], client = self.getClient(), parent = self)
		# This dialog is not modal, enabling to integrate some changes in existing code
		dialog.show()
		

	def _createDirectory(self, item):
		path = item.getUrl().path()
#		print "DEBUG: creating a new folder in %s..." % path
		(name, status) = QInputDialog.getText(self, "New folder", "Folder name:")
		while status and not validateDirectoryName(name):
			# Display some error message
			CommonWidgets.userError(self, "The following characters are forbidden in a folder name:\n%s" % ', '.join([x for x in RESTRICTED_NAME_CHARACTERS]))
			(name, status) = QInputDialog.getText(self, "New folder", "Folder name:")

		if status and not name.isEmpty():
			try:
				self._client.makeDirectory("%s/%s" % (path, name))
				# As usual, the new folder creation will be notified by the server, so
				# no local view update to perform synchronously
			except Exception, e:
				CommonWidgets.systemError(self, 'Unable to create this folder here: %s' % str(e))

	def _exportPackage(self, item):
		path = item.getUrl().path()
#		print "DEBUG: exporting package from %s..." % path

		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getSaveFileName(self, "Export package...", directory, "Testerman Package (*.tpk)")
		if not filename.isEmpty():
			directory = os.path.dirname(unicode(filename))
			settings.setValue('lastVisitedDirectory', QVariant(directory))
			if not filename.split('.')[-1] == 'tpk':
				filename = u"%s.tpk" % (unicode(filename))
			try:
				contents = self._client.exportPackage(unicode(path))
				if contents:
					f = open(unicode(filename), 'wb')
					f.write(contents)
					f.close()
					QMessageBox.information(self, getClientName(), "Package successfully exported to %s" % filename, QMessageBox.Ok)
				else:
					CommonWidgets.userError(self, 'Sorry, this package cannot be found')
			except Exception, e:
				CommonWidgets.systemError(self, 'Unable to export package: %s' % str(e))

	def _createPackage(self, item):
		path = item.getUrl().path()
		
		(name, status) = QInputDialog.getText(self, "New package", "Package name:")
		while status and not validateDirectoryName(name):
			# Display some error message
			CommonWidgets.userError(self, "The following characters are forbidden in a package name:\n%s" % ', '.join([x for x in RESTRICTED_NAME_CHARACTERS]))
			(name, status) = QInputDialog.getText(self, "New package", "Package name:")

		if status and not name.isEmpty():
			try:
				self._client.createPackage("%s/%s" % (path, name))
			except Exception, e:
				CommonWidgets.systemError(self, 'Unable to create this package here: %s' % str(e))

	def _importPackage(self, item):
		path = item.getUrl().path()

		# Select the package to open (local filesystem)
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getOpenFileName(self, "Choose a file", directory, "Testerman package (*.tpk);;All (*)")
		if filename.isEmpty():
			return
		
		directory = os.path.dirname(unicode(filename))
		settings.setValue('lastVisitedDirectory', QVariant(directory))

		try:		
			f = open(unicode(filename), 'rb')
			contents = f.read()
			f.close()
		except Exception, e:
			CommonWidgets.systemError(self, 'Unable to read this package: %s' % str(e))
			return
		
		(name, status) = QInputDialog.getText(self, "Import package", "Package name on the server:")
		while status and not validateDirectoryName(name):
			# Display some error message
			CommonWidgets.userError(self, "The following characters are forbidden in a package name:\n%s" % ', '.join([x for x in RESTRICTED_NAME_CHARACTERS]))
			(name, status) = QInputDialog.getText(self, "Import package", "Package name on the server:")

		if status and not name.isEmpty():
			target = "%s/%s" % (path, name)
			transient = CommonWidgets.WTransientWindow()
			transient.showTextLabel("Importing package to %s..." % target)
			try:
				self._client.importPackageFile(contents, target)
			except Exception, e:
				transient.dispose()
				CommonWidgets.systemError(self, 'Unable to import package: %s' % str(e))
				return
			transient.dispose()
			CommonWidgets.userInformation(self, "Package successfully imported.")

	def _createProfile(self, item):
		associatedScriptPath = item.parent().getUrl().path()
#		print "DEBUG: creating a new profile associated to %s..." % associatedScriptPath
		(name, status) = QInputDialog.getText(self, "New profile", "Profile name:")
		while status and not validateDirectoryName(name):
			# Display some error message
			CommonWidgets.userError(self, "The following characters are forbidden in a profile name:\n%s" % ', '.join([x for x in RESTRICTED_NAME_CHARACTERS]))
			(name, status) = QInputDialog.getText(self, "New profile", "Profile name:")

		# TODO: check for existing profiles

		if status and not name.isEmpty():
			# Now, open a blank profile document, unsaved
			model = DocumentModels.ProfileModel()
			model.setSavedAttributes(url = QUrl('testerman://testerman%s/profiles/%s.profile' % (associatedScriptPath, name)), timestamp = time.time())
			model.setDocumentSource('<?xml version="1.0"?><profile></profile>')
			QApplication.instance().get('gui.documentmanager').openTab(model)

	def _copyItems(self, sources, destination):
		"""
		Copies the first file in sources.
		May display user notifications in case of misoperations.
		
		@type  sources: list of QUrls
		@type  destination: QString (path)
		
		@rtype: bool
		@returns: True if the copy was OK. False otherwise.
		"""
		QApplication.instance().setOverrideCursor(QCursor(Qt.ArrowCursor))
		try:
			# We assume a source list containing only one URL (single selection only)
			# Will require some clean up one day.
			for url in sources:
		#			print "DEBUG: copying %s to %s..." % (url.path(), destination)
				src = unicode(url.path())
				srcBasename = os.path.split(src)[1]
				dst = unicode(destination)
				dstBasename = os.path.split(dst)[1]
				# Minimal checks to avoid self/recursive copy, etc
				if os.path.split(src)[0] == dst:
					# copy a file/folder to its own folder
					CommonWidgets.userInformation(self, "Cannot copy %s to itself" % srcBasename)
					return False
				elif dst.startswith('%s/' % src) or src == dst:
					# copy a folder to one of its sub-folders (or itself)
					# NB: this is not possible due to the current copy implementation on the server:
					# it will not create a list of files to copy before starting the copy, leading
					# to some infinite recursion operations. To fix on server side.
					CommonWidgets.userInformation(self, "Cannot copy %s to itself or to one of its sub-folders" % srcBasename)
					return False
				else:
					if QMessageBox.question(self, "Copy", "Are you sure you want to copy %s to %s (existing files will be overwritten) ?" % (srcBasename, dstBasename), 
						QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
						return self.getClient().copy(src, dst)
					else:
						return False
		except Exception, e:
			pass
		finally:
			QApplication.instance().restoreOverrideCursor()

	def _importItems(self, sources, destination):
		"""
		Imports the first file in sources to a destination within
		a package.
		Also imports/updates dependencies (optionally).

		May display user notifications in case of misoperations.
		
		@type  sources: list of QUrls
		@param sources: a list of urls to files to copy (MUST be located in the repository)
		                Only the first url is taken into account.
		@type  destination: QString (path)
		@param destination: the docroot path to the destination *folder*
		
		@rtype: bool
		@returns: True if the import copy was OK. False otherwise.
		"""
		if not sources:
			return False

		QApplication.instance().setOverrideCursor(QCursor(Qt.ArrowCursor))
		try:
			# We assume a source list containing only one URL (single selection only)
			# Will require some clean up one day.
			url = sources[0]

		#		print "DEBUG: importing %s to %s..." % (url.path(), destination)
			src = unicode(url.path())
			srcBasename = os.path.split(src)[1]
			dst = unicode(destination)

			# Minimal checks to avoid self/recursive copy, etc
			if os.path.split(src)[0] == dst:
				# copy a file/folder to its own folder
				CommonWidgets.userInformation(self, "Cannot import %s to itself" % srcBasename)
				return False

			if dst.startswith('%s/' % src) or src == dst:
				# copy a folder to one of its sub-folders (or itself)
				# NB: this is not possible due to the current copy implementation on the server:
				# it will not create a list of files to copy before starting the copy, leading
				# to some infinite recursion operations. To fix on server side.
				CommonWidgets.userInformation(self, "Cannot import %s to itself or to one of its sub-folders" % srcBasename)
				return False

			# TODO: check if we are importing a file or a folder.
			# If it's a folder, no dependency management. Just propose to copy the folder as is.

			# We assume this is a file.
			# Compute the list of dependencies, and show it to the user for import confirmation.
			transient = CommonWidgets.WTransientWindow()
			transient.showTextLabel("Computing dependencies...")
			ex = None
			try:
				deps = self.getClient().getDependencies(src)
			except Exception, e:
				ex = e
			transient.dispose()
			if ex:
				CommonWidgets.userInformation(self, "Unable to compute dependencies: %s" % str(ex))
				return False

			# Everything was OK, display a list of deps to copy
			# filesToImport is a list of unicode docroot paths to src files to copy.
			filesToImport = [ src ]
			filesToImport += deps

			# filesToCreate are a list of target filenames relative to the package/src folder
			# Used to notify the user about what we'll do
			filesToCreate = [ x[len('/repository/'):] for x in filesToImport ]

			dlg = WImportConfirmation(filesToCreate, title = "Import to package", parent = self)
			if dlg.exec_() == QDialog.Accepted:
				# Copy files
				targets = []
				for f in filesToImport:
					# Compute the dest path - replace the '/repository/' prefix with the dst folder
					targets.append("%s/%s" % (dst, f[len('/repository/'):]))
				self.copy(filesToImport, targets)
				return True
			else:
				return False
		except Exception, e:
			pass
		finally:
			QApplication.instance().restoreOverrideCursor()

	def copy(self, sources, destinations):
		"""
		Copy dialog.
		sources contains (docroot path to) source items (folders or files)
		destinations contains (docroot path to) destination items (folders or files).
		Sources and destinations lists must have the same length.
		
		@type  sources: list of unicode strings
		@type  destinations: list of unicode strings
		"""
		progress = QProgressDialog("Copying files...", "Cancel", 0, len(sources), self)
		progress.setWindowTitle("Copying files")
		progress.setMinimumDuration(0)
		progress.show()

		try:
			for i in range(len(sources)):
				src = sources[i]
				dst = destinations[i]
#				print "DEBUG: copying %s to %s..." % (src, dst)
				progress.setLabelText("Copying %s to %s..." % (src, dst))
				QApplication.instance().processEvents()
				self.getClient().copy(src, dst)
				progress.setValue(i)
				QApplication.instance().processEvents()
				if progress.wasCanceled():
					break
			progress.setParent(None)
		except Exception, e:
			progress.setParent(None)
			CommonWidgets.systemError(self, "Unable to complete operation: %s" % str(e))

	def _moveItems(self, sources, destination):
		"""
		Display a dialog with a list of files to move,
		filtering "same file" instances or "ambigious" moves, if any
		(such as a folder and some of its subfolders/files to the same destination)
		
		@type  sources: list of QUrls
		@type  destination: QString (path)
		"""
		for url in sources:
#			print "DEBUG: moving %s to %s..." % (url.path(), destination)
			self.getClient().move(unicode(url.path()), unicode(destination))

	def _renameItem(self, item, currentName, newName):
		"""
		Attempt to rename the item from currentName to newName.
		
		@type  currentName: unicode
		@type  newName: unicode
		
		@raises: Exception in case of an error.
		"""
		path = unicode(item.getUrl().path())
#		print "DEBUG: renaming %s from %s to %s..." % (path, currentName, newName)

		if not validateFileName(newName):
			raise Exception("The following characters are forbidden in a file name:\n%s" % ', '.join([x for x in RESTRICTED_NAME_CHARACTERS]))

		# rename
		if not self.getClient().rename(path, unicode(newName)):
			raise Exception("An object with the same name already exists in this folder")

	def onItemChanged(self, item, col):
		if hasattr(item, "isVirtual") and item.isVirtual():
			# No renaming check for virtual items - they can be renamed "administratively"
			return 
		
		if col == 0 and hasattr(item, "getBasename") and item.getBasename() != unicode(item.text(0)):
			currentName = item.getBasename()
			newName = unicode(item.text(0))
			# Make sure the extension is kept
			if item.shouldRetainExtensionOnRename():
				base, extension = os.path.splitext(currentName)
				if extension and not newName.endswith(extension):
					newName += extension
			try:
				self._renameItem(item, currentName, newName)
				# Let the server dispatch new name notifications.
			except Exception, e:
				# Revert to its previous name
				item.setBasename(currentName)
				CommonWidgets.userError(self, 'Cannot rename "%s" to "%s":\n%s' % (currentName, newName, str(e)))
	
	##
	# Drag & Drop support
	##
	def mimeData(self, items):
		md = QMimeData()
		urls = [item.getUrl() for item in items if (item.isCopyable() or item.isMoveable())]
		md.setUrls(urls)
		return md
	
	def dragEnterEvent(self, dragEnterEvent):
		dragEnterEvent.accept()
		
	def dragMoveEvent(self, dragMoveEvent):
		QTreeWidget.dragMoveEvent(self, dragMoveEvent)
		item = self.itemAt(dragMoveEvent.pos())
		if item:
			if item.flags() & Qt.ItemIsDropEnabled:
				dragMoveEvent.accept()
			else:
				dragMoveEvent.ignore()
			return
		else:
			# "Root" item
			dragMoveEvent.accept()
	
	def dropMimeData(self, parent, index, data, action):
		"""
		Implement drag support, depending on the drop target type.
		"""
		if parent is None:
			# We're dropping into the widget itself, not an item
			if data.hasUrls() and action == Qt.CopyAction:
				# Valid drop action here: copy urls to the "root" folder the tree
				# is displaying
				sources = data.urls()
				destination = self._path
				self._copyItems(sources, destination)
			else:
				# No supported drop action
				pass
		else:
			# We have a node, parent, we drop something into.
			# Delegate the action to the node.
			parent.onDropMimeData(data, action)
		
		# We always return False so that the widget does not add an item by
		# itself, but wait for the server to notify the change.
		return False
	
	def supportedDropActions(self):
		return (Qt.CopyAction)
		# Disable moving for now
#		return (Qt.CopyAction | Qt.MoveAction)
	
	##
	# External actions
	##
	def _open(self, item):
		if item.isDir():
			return
		url = item.getUrl()
		if url:
#			print "DEBUG: opening url %s..." % url.toString()
			self.emit(SIGNAL('openUrl(const QUrl&)'), url)


################################################################################
# View Controller
################################################################################

class ViewController(QObject):
	"""
	The bridge between view signals and shared business logic.
	"""
	def __init__(self, parent = None):
		QObject.__init__(self, parent)

	def addView(self, view):
		self.connect(view, SIGNAL('openUrl(const QUrl&)'), self.openUrl)
		self.connect(QApplication.instance(), SIGNAL('testermanServerUpdated(QUrl)'), view.refresh)
	
	def openUrl(self, url):
		log("Ready to open URL: " + unicode(url.toString()))
		if url.path().endsWith('.log'):
			self.showLog(url)
		else:
			QApplication.instance().get('gui.documentmanager').openUrl(url)

	def showLog(self, url):
		"""
		@type  url: QUrl
		@param url: the url of the file to analyze and display
		"""
		logViewer = LogViewer.WLogViewer(parent = self.parent())
		logViewer.openUrl(url)
		logViewer.show()


################################################################################
# A Dock bridging views and a controller
################################################################################
		
class WRepositoryBrowsingDock(QDockWidget):
	def __init__(self, parent):
		QDockWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.controller = ViewController(self)
		
		self.setWindowTitle("Remote browsing")

		# Only display the Archives browser - and a tab - if a specific configuration is present
		settings = QSettings()
		enableArchivesBrowser = settings.value('enableArchiveBrowser', QVariant(False)).toBool()
		if enableArchivesBrowser:
			self.tab = QTabWidget(self)
			self.repositoryTree = WServerFileSystemTreeWidget('/repository', self.tab)
			self.repositoryTree.setClient(QApplication.instance().client(), autorefresh = False)
			self.controller.addView(self.repositoryTree)
			self.tab.addTab(self.repositoryTree, 'Repository')
			self.archivesTree = WServerFileSystemTreeWidget('/archives', self.tab)
			self.archivesTree.setClient(QApplication.instance().client(), autorefresh = False)
			self.controller.addView(self.archivesTree)
			self.tab.addTab(self.archivesTree, 'Archives')
			self.setWidget(self.tab)
		else:
			# No Tab widget, keep it simple
			self.repositoryTree = WServerFileSystemTreeWidget('/repository', self)
			self.repositoryTree.setClient(QApplication.instance().client(), autorefresh = False)
			self.controller.addView(self.repositoryTree)
			self.setWidget(self.repositoryTree)
			self.archivesTree = None
	
	def refresh(self):
		self.repositoryTree.refresh()
		if self.archivesTree:
			self.archivesTree.refresh()


################################################################################
# Standalone view
################################################################################

if __name__ == "__main__":
	import sys
	import TestermanClient
	
	app = QApplication([])
	
	serverUrl = "http://localhost:8080"
	if len(sys.argv) > 1:
		serverUrl = sys.argv[1]

	client = TestermanClient.Client("test", "FileSystemViewer/1.0.0", serverUrl = serverUrl)
	client.startXc()

	try:	
		w = WServerFileSystemTreeWidget('/repository')
		w.setClient(client)
		w.show()

#		browser = WRemoteFileDialog(client, '/repository', '/sandbox')
#		browser.show()

#		print "Save file: %s" % getSaveFilename(client, defaultExtension = "ats", filter_ = [ "ats" ])
	except Exception, e:
		import TestermanNodes
		print TestermanNodes.getBacktrace()
		client.stopXc()
		raise Exception(TestermanNodes.getBacktrace())
		

	app.exec_()
	client.stopXc()

