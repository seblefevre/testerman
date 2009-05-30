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
# Remote browsers, triggering appropriate actions when needed.
#
# Based on a server file system view, enabling basic file management
# through Ws API, that emits some signals to integrate non-local-only logic
# (such as opening files)
#
##

import Resources
import CommonWidgets
import LogViewer

import os.path
import re
import time

from PyQt4.Qt import *

from Base import *

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
		self.setText(1, 'unknown')
		
		self.setFlags(Qt.ItemIsEnabled)
	
	def isRenameable(self):
		return self.flags() & Qt.ItemIsEditable
	
	def isCopyable(self):
		return self.flags() & Qt.ItemIsDragEnabled

	def isMoveable(self):
		return self.flags() & Qt.ItemIsDragEnabled
	
	def shouldRetainExtensionOnRename(self):
		return True

	def getUrl(self):
		"""
		Overridable.
		By default, returns an url based on the filepath.
		
		@rtype: QUrl
		@returns: the url of the object
		"""
		serverIp, serverPort = self.treeWidget().getClient().getServerAddress()
		url = "testerman://%s:%d%s" % (serverIp, serverPort, self._path)
		return QUrl(url)
	
	def getBasename(self):
		_, basename = os.path.split(self._path)
		return basename

	def setBasename(self, basename):
		basepath, _ = os.path.split(self._path)
		self._path = "%s/%s" % (basepath, basename)
		self.setText(0, basename)
		print "DEBUG: new file path: %s" % self._path
			

class AsyncFetchingThread(QThread):
	"""
	This thread calls the fetching method to get child items.
	Works with a lazyExpander.
	"""
	def __init__(self, asyncExpander, parent = None):
		QThread.__init__(self, parent)
		self._asyncExpander = asyncExpander
	
	def run(self):
		self._asyncExpander._fetchedChildItems = self._asyncExpander._fetcher()

class AsyncExpander(QObject):
	"""
	Decorator class over a TreeWidgetItem, enabling
	to turn it into a lazy expanding node, fetching
	children asynchronously calling the fetcher command,
	which returns a list of unparented nodes.
	
	Usage:
	AsyncExpander(item, fetcher).expand()
	
	where fetcher() returns a list of TreeWidgetItems.
	
	NB: we use a wrapper/decorator design pattern instead of
	a subclassing (embedding async expanding capability into
	ExpandableWidgetItem) to be able to apply it to the
	invisibleRootItem() of the main QTreeWidget.
	"""
	def __init__(self, item, fetcher):
		QObject.__init__(self)
		self._item = item
		self._fetcher = fetcher
		self._fetchedChildItems = []
		self.loadingItem = None
		self.loadingAnimation = None

	def expand(self):
		"""
		Overriden from the QTreeWidgetItem class.
		Displays a loading icon when expanding
		"""
		self._item.takeChildren()
		# Display a loading item
		self._loading()
		# Call our feeder
		self.fetchingThread = AsyncFetchingThread(self)
		self.fetchingThread.connect(self.fetchingThread, SIGNAL("finished()"), self._childItemsFetched)
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
		Removes the loading, animated icon added by _loading()
		"""
		self.loadingAnimation.stop()
		self._item.removeChild(self.loadingItem)
		del self.loadingItem
		del self.loadingAnimation
	
	def _childItemsFetched(self):
		"""
		Called when the fetching is over. Removes the loading indicator,
		adds the fetched items.
		"""
		self._loaded()
		self.fetchingThread = None
		# Replace the loading item with the fetched items
		for item in self._fetchedChildItems:
			self._item.addChild(item)


class ExpandableWidgetItem(BaseWidgetItem):
	"""
	Base class for nodes that can be expanded.
	Will be wrapped into a AsyncExpander when expanding.
	
	Provides a way to get children.
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)

	def fetchChildItems(self):
		"""
		To re-implement.
		Returns a list of unparented QTreeWidgetItems corresponding
		to the child nodes.
		"""
		return []


class DirWidgetItem(ExpandableWidgetItem):
	"""
	Directory/Folder
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/folder'))
		self.setText(1, 'folder')
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | 
			Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)

	def fetchChildItems(self):
		# The implementation is in the treewidget because it also
		# needs such a function.
		# The delegation cannot be performed the other way because
		# when the treewidget fetches its children, it cannot have
		# any DirWidgetItem (all its children are removed in the meanwhile).
		return self.treeWidget().fetchChildItems(self._path)

	def shouldRetainExtensionOnRename(self):
		return False
	

class AtsWidgetItem(ExpandableWidgetItem):
	"""
	ATS Document.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/ats'))
		self.setText(1, 'ats')
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
	
	def fetchChildItems(self):
		revisionsItem = RevisionsWidgetItem(self._path)
		executionLogsItem = ExecutionLogsWidgetItem(self._path)
		return [ revisionsItem, executionLogsItem ]


class ModuleWidgetItem(ExpandableWidgetItem):
	"""
	Module Document.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/module'))
		self.setText(1, 'module')
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)

	def fetchChildItems(self):
		revisionsItem = RevisionsWidgetItem(self._path)
		return [ revisionsItem ]


class CampaignWidgetItem(ExpandableWidgetItem):
	"""
	Campaign Document.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/campaign'))
		self.setText(1, 'campaign')
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)

	def fetchChildItems(self):
		revisionsItem = RevisionsWidgetItem(self._path)
		executionLogsItem = ExecutionLogsWidgetItem(self._path)
		return [ revisionsItem, executionLogsItem ]


class RevisionsWidgetItem(ExpandableWidgetItem):
	"""
	Revision file virtual folder.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/folder-virtual'))
		self.setText(0, 'Revisions')
		self.setText(1, '')
	
	def fetchChildItems(self):
		return [] # Not yet implemented.

	def getUrl(self):
		return None


class RevisionWidgetItem(BaseWidgetItem):
	"""
	Revision file (document)
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/revision'))
		self.setText(1, 'revision')


class ExecutionLogsWidgetItem(ExpandableWidgetItem):
	"""
	Virtual folder containing execution logs for
	a script.
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/folder-virtual'))
		self.setText(0, 'Executions')
		self.setText(1, '')
	
	def fetchChildItems(self):
		ret = []
		try:
			# Compute the corresponding archive path for this ATS
			archivePath = '/archives/%s' % ('/'.join(self._path.split('/')[2:]))
			l = self.treeWidget().getClient().getDirectoryListing(archivePath)
			for entry in l:
				if entry['type'] == 'log':
					ret.append(ExecutionLogWidgetItem('%s/%s' % (archivePath, entry['name'])))
		except Exception, e:
			print "DEBUG: " + str(e)
		return ret

	def getUrl(self):
		return None


class ExecutionLogWidgetItem(BaseWidgetItem):
	"""
	Execution log associated to a script, within
	a virtual folder.
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/revision'))
		self.setText(1, 'log')
		
		_, name = os.path.split(path)
		display = "(invalid log filename)"
		
		# According to the name, retrieve some additional info.
		m = re.match(r'([0-9-]+)_(.*)\.log', name)
		if m:
			date = m.group(1)
			username = m.group(2)
			display = "%s, by %s" % (date, username)
		self.setText(0, display)

		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
				
class LogWidgetItem(BaseWidgetItem):
	"""
	Execution log, as a document (from the Archive view)
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/execution-log'))
		self.setText(1, 'log')
		self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)


class PackageWidgetItem(BaseWidgetItem):
	"""
	Package
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/archive'))


################################################################################
# Tree Widget
################################################################################

class WServerFileSystemTreeWidget(QTreeWidget):
	"""
	This treeview is responsible for interfacing most filesystem-related actions,
	including application specificities.
	Some actions are said "local" are implemented by the widget -
	they are actions whose scope is the file system itself.
	Some others triggers an action elsewhere in the embedding application. In 
	this case they require a controller object to bridge signals emitted by
	the widget with external actions.
	
	Local actions:
	- file system related: delete (ats/campaign/module/log/empty dir),
	  rename (ats/campaign only, to avoid major breaks when renaming a whole dir tree),
		copy (dir/ats/campaign/module),
		(move disabled for now)
	- view related: refresh (all, subtree)
	
	Notes:
	- folder renaming is disabled on purpose. Could create havoks breaking
	  (a lot of) modules too easily.
	- folder moving is disabled for the same reasons.
	
	External actions:
	- open (for edition) : emit SIGNAL('openUrl(const QUrl&)')
	"""
	def __init__(self, path = '/', parent = None):
		QTreeWidget.__init__(self, parent)

		self._client = None
		
		self.setWindowIcon(icon(':/icons/browser'))
		self.setWindowTitle('Remote browser')

		self.setHeaderLabels([ 'Name' ]) #, 'Type' ])
		self.header().setResizeMode(0, QHeaderView.ResizeToContents)
		self.header().setResizeMode(1, QHeaderView.Stretch)
		self.header().resizeSection(1, 70)

		# Experiment: hidde the header, only one section ('name')		
		self.setHeaderHidden(True)

		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.connect(self, SIGNAL("itemExpanded(QTreeWidgetItem*)"), self.onItemExpanded)
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
		AsyncExpander(item, item.fetchChildItems).expand()

	def contextMenuEvent(self, event):
		item = self.itemAt(event.pos())
		
		menu = QMenu(self)
		
		if item:
			# Depending of the node, add several actions
			if isinstance(item, AtsWidgetItem):
				menu.addAction("Edit (head)", lambda: self._open(item))
				menu.addAction("Delete", lambda: self._deleteAts(item))

			elif isinstance(item, ExecutionLogWidgetItem):
				menu.addAction("Open", lambda: self._open(item))
				menu.addAction("Delete", lambda: self._deleteExecutionLog(item))

			if isinstance(item, ModuleWidgetItem):
				menu.addAction("Edit (head)", lambda: self._open(item))
				menu.addAction("Show referrer files...", lambda: self._showModuleReferrerFiles(item))
				menu.addAction("Delete", lambda: self._deleteModule(item))

			if isinstance(item, CampaignWidgetItem):
				menu.addAction("Edit (head)", lambda: self._open(item))
				menu.addAction("Delete", lambda: self._deleteCampaign(item))

			if isinstance(item, DirWidgetItem):
				menu.addAction("Delete", lambda: self._deleteDirectory(item))

			if isinstance(item, ExpandableWidgetItem):
				menu.addAction("Refresh subtree", lambda: self._refresh(item))

			menu.addSeparator()
		
		# In any case, general action
		menu.addAction("Refresh all", self.refresh)
		
		menu.popup(event.globalPos())

	def refresh(self):
		AsyncExpander(self.invisibleRootItem(), self.fetchChildItems).expand()
	
	def setClient(self, client):
		self._client = client
		self.refresh()
	
	def getClient(self):
		return self._client

	def fetchChildItems(self, path = None):
		if path is None:
			path = self._path
		try:
			l = self.getClient().getDirectoryListing(path)
		except Exception:
			l = []

		ret = []
		for entry in l:
			if entry['type'] == 'directory':
				child = DirWidgetItem('%s/%s' % (path, entry['name']))
			elif entry['type'] == 'ats':
				child = AtsWidgetItem('%s/%s' % (path, entry['name']))
			elif entry['type'] == 'log':
				child = ExecutionLogWidgetItem('%s/%s' % (path, entry['name']))
			elif entry['type'] == 'campaign':
				child = CampaignWidgetItem('%s/%s' % (path, entry['name']))
			elif entry['type'] == 'module':
				child = ModuleWidgetItem('%s/%s' % (path, entry['name']))
			# Not supported yet
			elif entry['type'] == 'package':
				child = PackageWidgetItem('%s/%s' % (path, entry['name']))
			ret.append(child)
		return ret

	##
	# Local actions
	##
	def _refresh(self, item):
		self.collapseItem(item)
		self.expandItem(item)

	def _showModuleReferrerFiles(self, item):
		"""
		Displays the files referencing the module.
		"""
		url = item.getUrl()
		path = unicode(url.path().toString())
		ret = self._client.getReferencingFiles(path)
		ret.sort()
		dialog = CommonWidgets.WTextEditDialog(text = '\n'.join(ret), readOnly = True, title = "Files referencing module %s: %d file(s)" % (path, len(ret)), fixedFont = True, parent = self)
		dialog.exec_()

	def _deleteAts(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete ATS", "Are you sure you want to delete the ATS %s ?" % item.getBasename(), 
				[('Also delete associated execution logs', True)], parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().deleteAts(unicode(url.path()), dialog.isChecked(0))
				if ret:
					item.parent().removeChild(item)
				else:
					# Display an error message ?
					pass

	def _deleteCampaign(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete Campaign", "Are you sure you want to delete the campaign %s ?" % item.getBasename(), 
				[('Also delete associated execution logs', True)], parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().deleteCampaign(unicode(url.path()), dialog.isChecked(0))
				if ret:
					item.parent().removeChild(item)
				else:
					# Display an error message ?
					pass

	def _deleteModule(self, item):
		url = item.getUrl()
		if url:
			b = QMessageBox.warning(self, "Delete Module", "Deleting a module may break a lot of existing ATSes or other modules. Are you sure you want to delete the module %s ?" % item.getBasename(), 
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if b == QMessageBox.Yes:
				ret = self.getClient().removeFile(unicode(url.path()))
				if ret:
					item.parent().removeChild(item)
				else:
					# Display an error message ?
					pass

	def _deleteDirectory(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete Folder", "Are you sure you want to delete the folder %s ?" % item.getBasename(), parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().removeDirectory(unicode(url.path()), False)
				if ret:
					item.parent().removeChild(item)
				else:
					CommonWidgets.userInformation(self, "Unable to delete folder %s: not empty" % os.path.split(unicode(url.path()))[1])

	def _deleteExecutionLog(self, item):
		url = item.getUrl()
		if url:
			dialog = CommonWidgets.WUserQuestion("Delete Execution Log", "Are you sure you want to delete this execution log ?", parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().deleteExecutionLog(unicode(url.path()), True)
				if ret:
					item.parent().removeChild(item)
				else:
					# Display an error message ?
					pass
	
	def _copyItems(self, sources, destination):
		"""
		Copies the first file in sources.
		May display user notifications in case of misoperations.
		
		@type  sources: list of QUrls
		@type  destination: QString (path)
		
		@rtype: bool
		@returns: True if the copy was OK. False otherwise.
		"""
		# We assume a source list containing only one URL (single selection only)
		# Will require some clean up one day.
		for url in sources:
			print "DEBUG: copying %s to %s..." % (url.path(), destination)
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
			
	def _moveItems(self, sources, destination):
		"""
		Display a dialog with a list of files to move,
		filtering "same file" instances or "ambigious" moves, if any
		(such as a folder and some of its subfolders/files to the same destination)
		
		@type  sources: list of QUrls
		@type  destination: QString (path)
		"""
		for url in sources:
			print "DEBUG: moving %s to %s..." % (url.path(), destination)
			self.getClient().move(unicode(url.path()), unicode(destination))

	def _renameItem(self, item, currentName, newName):
		"""
		Attempt to rename the item from currentName to newName.
		
		@type  currentName: unicode
		@type  newName: unicode
		
		@raises: Exception in case of an error.
		"""
		path = unicode(item.getUrl().path())
		print "DEBUG: renaming %s from %s to %s..." % (path, currentName, newName)

		# Forbidden list for simple files
		forbidden = "/\\' \"@|?*"
		for c in forbidden:		
			if c in unicode(newName):
				raise Exception("The following characters are forbidden in a file name:\n%s" % ', '.join([x for x in forbidden]))
		
		# rename
		if not self.getClient().rename(path, unicode(newName)):
			raise Exception("An object with the same name already exists in this folder")

	def onCopyUrls(self, parent, sources, destination):
		ret = self._copyItems(sources, destination)
		if ret:
			self._refresh(parent)

	def onItemChanged(self, item, col):
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
				item.setBasename(newName)
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
		if data.hasUrls() and action == Qt.CopyAction:
			if parent is None:
				# root
				destination = self._path
			elif parent.getUrl():
				destination = parent.getUrl().path()
			else:
				print "DEBUG: cannot copy/move to this node: no associated URL"
				return False

			# Tried to emit a signal so that the drop op is complete when
			# displaying message boxes, hence restoring the standard cursor
			# instead of the drag one.
			# Unfortunately, this is the same problem as when called synchronously...
			# self.emit(SIGNAL('copyUrls'), parent, data.urls(), destination)
			QApplication.instance().setOverrideCursor(QCursor(Qt.ArrowCursor))
			self.onCopyUrls(parent, data.urls(), destination)
			QApplication.instance().restoreOverrideCursor()
			return True
		else:
			return False
	
	def supportedDropActions(self):
		return (Qt.CopyAction)
		# Disable moving for now
#		return (Qt.CopyAction | Qt.MoveAction)
	
	##
	# External actions
	##
	def _open(self, item):
		url = item.getUrl()
		if url:
			print "DEBUG: opening url %s..." % url.toString()
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
		self.tab = QTabWidget(self)
		self.repositoryTree = WServerFileSystemTreeWidget('/repository', self.tab)
		self.repositoryTree.setClient(QApplication.instance().client())
		self.controller.addView(self.repositoryTree)
		self.tab.addTab(self.repositoryTree, 'Repository')
		self.archivesTree = WServerFileSystemTreeWidget('/archives', self.tab)
		self.archivesTree.setClient(QApplication.instance().client())
		self.controller.addView(self.archivesTree)
		self.tab.addTab(self.archivesTree, 'Archives')
		self.setWidget(self.tab)


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

	try:	
		w = WServerFileSystemTreeWidget('/repository')
		w.setClient(client)
		w.show()
	except Exception, e:
		import TestermanNodes
		print TestermanNodes.getBacktrace()
		raise Exception(TestermanNodes.getBacktrace())
		
		
	app.exec_()
