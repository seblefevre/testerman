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
		self._path = path
		_, name = os.path.split(path)
		if not name:
			name = "/"
		self.setText(0, name)
		self.setText(1, 'unknown')

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
	
	def getName(self):
		return self.text(0)

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
		self.loadingAnimation.stop()
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

	def fetchChildItems(self):
		# The implementation is in the treewidget because it also
		# needs such a function.
		# The delegation cannot be performed the other way because
		# when the treewidget fetches its children, it cannot have
		# any DirWidgetItem (all its children are removed in the meanwhile).
		return self.treeWidget().fetchChildItems(self._path)
	

class AtsWidgetItem(ExpandableWidgetItem):
	"""
	ATS
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/ats'))
		self.setText(1, 'ats')
	
	def fetchChildItems(self):
		revisionsItem = RevisionsWidgetItem(self._path)
		executionLogsItem = ExecutionLogsWidgetItem(self._path)
		return [ revisionsItem, executionLogsItem ]

class ModuleWidgetItem(ExpandableWidgetItem):
	"""
	Module
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/module'))
		self.setText(1, 'module')

	def fetchChildItems(self):
		revisionsItem = RevisionsWidgetItem(self._path)
		return [ revisionsItem ]

class CampaignWidgetItem(ExpandableWidgetItem):
	"""
	Campaign
	"""
	def __init__(self, path, parent = None):
		ExpandableWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/campaign'))
		self.setText(1, 'campaign')

	def fetchChildItems(self):
		revisionsItem = RevisionsWidgetItem(self._path)
		executionLogsItem = ExecutionLogsWidgetItem(self._path)
		return [ revisionsItem, executionLogsItem ]

class LogWidgetItem(BaseWidgetItem):
	"""
	Execution lof file
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/execution-log'))
		self.setText(1, 'log')

class RevisionsWidgetItem(ExpandableWidgetItem):
	"""
	Revision file
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
	Revision file
	"""
	def __init__(self, path, parent = None):
		BaseWidgetItem.__init__(self, path, parent)
		self.setIcon(0, icon(':/icons/revision'))
		self.setText(1, 'revision')

class ExecutionLogsWidgetItem(ExpandableWidgetItem):
	"""
	Virtual node
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
	Revision file
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
	- file system related: delete (ats/campaign/module/log),
	  module referrer lookup
	- view related: refresh (all, subtree)
	External actions:
	- open (for edition) : emit SIGNAL('openUrl(const QUrl&)')
	"""
	def __init__(self, path = '/', parent = None):
		QTreeWidget.__init__(self, parent)

		self._client = None
		
		self.setWindowIcon(icon(':/icons/browser'))
		self.setWindowTitle('Remote browser')
		self.setHeaderLabels([ 'name', 'type' ])
		self.header().setResizeMode(0, QHeaderView.ResizeToContents)
		self.header().setResizeMode(1, QHeaderView.Stretch)
		self.header().resizeSection(1, 70)
		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.connect(self, SIGNAL("itemExpanded(QTreeWidgetItem*)"), self.onItemExpanded)
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
		
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
			dialog = CommonWidgets.WUserQuestion("Delete ATS", "Are you sure you want to delete the ATS %s ?" % item.getName(), 
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
			dialog = CommonWidgets.WUserQuestion("Delete Campaign", "Are you sure you want to delete the campaign %s ?" % item.getName(), 
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
			b = QMessageBox.warning(self, "Delete Module", "Deleting a module may break a lot of existing ATSes or other modules. Are you sure you want to delete the module %s ?" % item.getName(), 
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
			dialog = CommonWidgets.WUserQuestion("Delete Directory", "Are you sure you want to delete the directory %s ?" % item.getName(), parent = self)
			if dialog.exec_() == QDialog.Accepted:
				ret = self.getClient().removeDirectory(unicode(url.path()), False)
				if ret:
					item.parent().removeChild(item)
				else:
					CommonWidgets.userInformation(self, "Unable to delete directory: not empty")

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
		raise Exception(TestermanNodes.getBacktrace())
		
		
	app.exec_()
