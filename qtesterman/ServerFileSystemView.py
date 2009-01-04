##
# -*- coding: utf-8 -*-
#
# A server dir browser, enabling basic file management
# through Ws API.
#
# Implemented as a model/view Qt Tree.
#
# Emits some signals to integrate additional logic
# (such as opening files)
#
##

import Resources

import time
import re
import os.path

from PyQt4.Qt import *


#: may be shared in a common file.
#: however, copying it locally enables more independent modules.
class IconCache:
	def __init__(self):
		self._icons = {}

	def icon(self, resource):
		if not self._icons.has_key(resource):
			self._icons[resource] = QIcon(resource)
		return self._icons[resource]

################################################################################
# Nodes used behind the Qt Model
################################################################################

class FileSystemNode(QObject):
	"""
	Base class for File system nodes (DirNode, AtsNode, etc)
	"""
	
	TYPE_UNKNOWN = 'unknown'
	TYPE_ATS = 'ats'
	TYPE_DIRECTORY = 'directory'
	TYPE_FILE = 'file'
	TYPE_LOG = 'log'
	TYPE_CAMPAIGN = 'campaign'
	TYPE_EXECUTION_LOG = 'execution log'
	TYPE_VIRTUAL = 'virtual'
	TYPE_REVISION = 'versioned file'
	TYPE_MODULE = 'module'
	TYPE_PACKAGE = 'package'
	
	def __init__(self, path, context, parent = None):
		"""
		@type  path: string
		@param path: the full path of the node, (directory + basename + extension)
		@type  parent: FileSystemNode (or None)
		@param parent: the parent node. None if it's the root.
		"""
		QObject.__init__(self, parent)

		#: name: basename + extension
		self._basePath, self._name = os.path.split(path)
		#: basePath: always finished by a /
		if not self._basePath.endswith('/'):
			self._basePath = '%s/' % self._basePath
		
		self._parent = parent
		self._type = FileSystemNode.TYPE_UNKNOWN
		self._context = context
	
	def getName(self):
		return self._name
	
	def getParent(self):
		return self._parent
		
	def getType(self):
		return self._type
	
	def getContext(self):
		return self._context
	
	def getFilePath(self):
		"""
		Constructs and returns the complete node path, including
		the basename and extension.
		@rtype: string
		@returns: the complete node path
		"""
		return '%s%s' % (self._basePath, self._name)
	
	def refresh(self):
		"""
		Invalidates all nodes.
		The next access will refresh the model.
		"""
		for c in self.getChildren():
			c.invalidate()
		self.invalidate()
	
	def getChildren(self):
		"""
		To reimplement.
		@rtype: list of FileSystemNode
		@returns: the node children
		"""
		return []

	def invalidate(self):
		"""
		To reimplement.
		Make sure that local caches are purged, or
		at least won't be used on next operations.
		"""
		pass

	def getDisplay(self):
		"""
		Overridable.
		By default, returns the node name.
		"""
		return self._name
	
	def getUrl(self):
		"""
		Overridable.
		By default, returns an url based on the filepath.
		"""
		serverIp, serverPort = self.getContext().getClient().getServerAddress()
		url = "testerman://%s:%d%s" % (serverIp, serverPort, self.getFilePath())
		return url
	

##
# Directory
##
class DirNode(FileSystemNode):
	"""
	A node representing a remote directory.
	"""
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_DIRECTORY
		self._children = None
	
	def invalidate(self):
		self._children = None

	def getChildren(self):
		"""
		Gets a directory listing from the server.
		"""
		# cached ?
		if self._children is not None:
			return self._children

		# Not cached.
		dirPath = self.getFilePath()
		if not dirPath.endswith('/'):
			dirPath = '%s/' % dirPath
		try:
			l = self._context.getClient().getDirectoryListing(dirPath)
		except:
			l = []
		
		self._children = []
		for entry in l:
			if entry['type'] == 'directory':
				child = DirNode('%s%s' % (dirPath, entry['name']), self.getContext(), self)
			elif entry['type'] == 'ats':
				child = AtsNode('%s%s' % (dirPath, entry['name']), self.getContext(), self)
			elif entry['type'] == 'log':
				child = LogFileNode('%s%s' % (dirPath, entry['name']), self.getContext(), self)
			elif entry['type'] == 'campaign':
				child = CampaignNode('%s%s' % (dirPath, entry['name']), self.getContext(), self)
			elif entry['type'] == 'module':
				child = ModuleNode('%s%s' % (dirPath, entry['name']), self.getContext(), self)
			# Not supported yet
#			elif entry['type'] == 'package':
#				child = PackageNode('%s%s' % (dirPath, entry['name']), self.getContext(), self)
			else:
				# Generic node
				child = FileNode('%s%s' % (dirPath, entry['name']), self)
			self._children.append(child)
		
		return self._children

##
# ATS
##
class AtsNode(FileSystemNode):
	"""
	Represents an ATS.
	May be able to list its executions (one day).
	"""	
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_ATS
		self._children = None

	def invalidate(self):
		self._children = None

	def getChildren(self):
		# Cached ?
		if self._children is not None:
			return self._children
		
		# Create subnodes
		self._children = []
		self._children.append(RevisionListNode(self.getFilePath(), self.getContext(), self))
		if self.getContext().showExecutionLogs():
			self._children.append(ExecutionLogListNode(self.getFilePath(), self.getContext(), self))
		return self._children

##
# ATS
##
class CampaignNode(FileSystemNode):
	"""
	Represents an ATS.
	May be able to list its executions (one day).
	"""	
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_CAMPAIGN
		self._children = None

	def invalidate(self):
		self._children = None

	def getChildren(self):
		# Cached ?
		if self._children is not None:
			return self._children
		
		# Create subnodes
		self._children = []
		self._children.append(RevisionListNode(self.getFilePath(), self.getContext(), self))
		if self.getContext().showExecutionLogs():
			self._children.append(ExecutionLogListNode(self.getFilePath(), self.getContext(), self))
		return self._children

##
# Revision (attached to an ATS/Campaign)
##
class RevisionNode(FileSystemNode):
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_REVISION

class RevisionListNode(FileSystemNode):
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_VIRTUAL
		self._display = "Revisions"
		self._children = None
	
	def getDisplay(self):
		return self._display

	def invalidate(self):
		self._children = None

	def getChildren(self):
		# Cached ?
		if self._children is not None:
			return self._children

		self._children = []
		# TODO: get existing revisions for current file, then create a RevisionNode accordingly (Ats or Campaign...)
		return self._children

##
# Execution logs (attached to an ATS/Campaign)
##	
class ExecutionLogNode(FileSystemNode):
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_EXECUTION_LOG
		self._display = "(invalid log filename)"
		
		# According to the name, retrieve some additional info.
		m = re.match(r'([0-9-]+)_(.*)\.log', self._name)
		if m:
			date = m.group(1)
			username = m.group(2)
			self._display = "%s, by %s" % (date, username)
	
	def getDisplay(self):
		return self._display

class ExecutionLogListNode(FileSystemNode):
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_VIRTUAL
		self._display = "Executions"
		self._children = None
	
	def getDisplay(self):
		return self._display

	def invalidate(self):
		self._children = None

	def getChildren(self):
		# Cached ?
		if self._children is not None:
			return self._children
		
		# Create subnodes according to known execution nodes
		self._children = []
		try:
			filePath = self.getFilePath()
			# Compute the corresponding archive path for this ATS
			archivePath = '/archives/%s' % ('/'.join(filePath.split('/')[2:]))
			l = self.getContext().getClient().getDirectoryListing(archivePath)
			for entry in l:
				if entry['type'] == 'log':
					self._children.append(ExecutionLogNode('%s/%s' % (archivePath, entry['name']), self.getContext(), self))
		except Exception, e:
			print "DEBUG: " + str(e)
		return self._children
		
##
# Log file (as a file, not attached to an ATS/Campaign
##
class LogFileNode(FileSystemNode):
	"""
	Log file node. Nothing interesting for now.
	"""
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_LOG

##
# Module
##
class ModuleNode(FileSystemNode):
	"""
	Module.
	"""
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_MODULE
##
# Other File
##
class FileNode(FileSystemNode):
	"""
	Any file node. Nothing interesting with them for now.
	"""
	def __init__(self, path, context, parent = None):
		FileSystemNode.__init__(self, path, context, parent)
		self._type = FileSystemNode.TYPE_FILE


################################################################################
# Qt Model 
################################################################################

class ServerFileSystemModel(QAbstractItemModel):
	"""
	A Qt Model representation of the server's exposed
	filesystem.
	
	Greatly inspired by QFileSystemModel.
	
	Manages a local cache, updated through Xc notifications.
	
	Offers an API to remotely manage files (remove, move, etc).
	"""
	def __init__(self, path, context, parent = None):
		"""
		context provides:
		- icon()
		- ...
		
		and is passed to each FilseSystemNode instance, too.
		"""
		
		QAbstractItemModel.__init__(self, parent)
		self._context = context
		
		# Maybe we should store a flat model a la JobQueue,
		# where parenting can be detected using path prefixes ?
		# (ok to retrieve parents, but to get immediate child, this is a bit slower)
		
		self._rootNode = DirNode(path, self._context)
	
	def icon(self, resource):
		return self._context.icon(resource)
	
	def index(self, row, column, parentIndex):
		"""
		In this model implementation, we store a FileSystemNode object in modeIndex.internalPointer.
		"""
		if not self.hasIndex(row, column, parentIndex):
			return QModelIndex()
		
		if not parentIndex.isValid():
			# the parent is the (invisible) root node.
			parent = self._rootNode
		else:
			parent = parentIndex.internalPointer()

		children = parent.getChildren()
		if row < len(children):
			return self.createIndex(row, column, children[row])
		else:
			# Invalid child
			return QModelIndex()

	def flags(self, index):
		if not index.isValid():
			return 0
		return Qt.ItemIsEnabled | Qt.ItemIsSelectable

	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			if section == 0:
				return QVariant("Name")
			elif section == 1:
				return QVariant("Type")
			else:
				return QVariant()
		return QVariant()
	
	def parent(self, index):
		"""
		Constructs the modelindex for the parent of node indexed by index,
		i.e. an index:
		- that contains the parent node (as an internalPointer in our implementation)
		- identifies the parent as the Nth row for its own parent (ie the current grand parent).
		- by convention, column is set to 0.
		"""
		if not index.isValid():
			return QModelIndex()

		node = index.internalPointer()
		
		parent = node.getParent()
		
		if parent is self._rootNode:
			return QModelIndex()
		
		elif parent is None:
			return QModelIndex()
		
		else:
			grandParent = parent.getParent()
			# may be none
			if not grandParent:
				return self.createIndex(0, 0, parent) # this is the modelindex of the root
			else:
				# Need to get the row of the parent, ie its index in its parent list
				parentRow = [x.getName() for x in grandParent.getChildren()].index(parent.getName())
				return self.createIndex(parentRow, 0, parent)
	
	def columnCount(self, parentIndex):
		# Fixed column count in this model.
		return 2 # Name, Type (for now)
	
	def rowCount(self, parentIndex):
		if parentIndex.isValid():
			node = parentIndex.internalPointer()
		else:
			# The parent is the root
			node = self._rootNode
		
		return len(node.getChildren())
	
	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		
		if role == Qt.DisplayRole:
			node = index.internalPointer()
			
			if index.column() == 0:
				return QVariant(node.getDisplay())
			elif index.column() == 1:
				return QVariant(node.getType())
			else:
				return QVariant()
		
		elif role == Qt.UserRole:
			# Returns the node type
			node = index.internalPointer()
			return QVariant(node.getType())

		elif role == Qt.DecorationRole and index.column() == 0:
			t = index.internalPointer().getType()
			ret = self.icon(':/icons/unknown.png')

			if t == FileSystemNode.TYPE_DIRECTORY:
				ret = self.icon(':/icons/folder.png')
			elif t == FileSystemNode.TYPE_ATS:
				ret = self.icon(':/icons/ats.png')
			elif t == FileSystemNode.TYPE_CAMPAIGN:
				ret = self.icon(':/icons/campaign.png')
			elif t == FileSystemNode.TYPE_LOG:
				ret = self.icon(':/icons/log.png')
			elif t == FileSystemNode.TYPE_EXECUTION_LOG:
				ret = self.icon(':/icons/execution-log.png')
			elif t == FileSystemNode.TYPE_REVISION:
				ret = self.icon(':/icons/revision.png')
			elif t == FileSystemNode.TYPE_VIRTUAL:
				ret = self.icon(':/icons/folder-virtual.png')
			elif t == FileSystemNode.TYPE_PACKAGE:
				ret = self.icon(':/icons/archive.png')
			elif t == FileSystemNode.TYPE_MODULE:
				ret = self.icon(':/icons/module.png')

			return QVariant(ret)

		else:
			return QVariant()	

	##
	# Addons
	##
	def refresh(self, index = None):
		"""
		Refreshes a node through invalidation.
		"""
		self.emit(SIGNAL('layoutAboutToBeChanged()'))
		if index and index.isValid():
			index.internalPointer().refresh()
		else:
			self._rootNode.refresh()
		self.emit(SIGNAL('layoutChanged()'))
	
	def updateFileSystemInfo(self, fsInfo):
		pass
	
	def isDirectory(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_DIRECTORY)

	def isAts(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_ATS)

	def isRevision(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_REVISION)

	def isModule(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_MODULE)

	def isExecutionLog(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_EXECUTION_LOG)

	def isLog(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_LOG)

	def isCampaign(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_CAMPAIGN)

	def isPackage(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_PACKAGE)

	def isVirtual(self, index):
		return self.data(index, Qt.UserRole).toString() == QString(FileSystemNode.TYPE_VIRTUAL)

	def getFilePath(self, index):
		if index.isValid():
			return index.internalPointer().getFilePath()
		else:
			return None
	
	def getUrl(self, index):
		if index.isValid():
			return index.internalPointer().getUrl()
		else:
			return None
	
	
################################################################################
# Tree View interfacing the Model
################################################################################

class WServerFileSystemView(QTreeView):
	"""
	A tree view based on the model.
	
	Configurable to serve as a simple file system view,
	or an enhanced view gathering contextual information according to the viewed
	object (execution history on an ats, expanded packages, etc)
	
	@emits: openUrl(const QUrl&) when an URL needs opening
	@emits: showReferredByFiles(const QUrl&) when needed to show module-referencing files
	"""
	def __init__(self, path = '/', parent = None):
		QTreeView.__init__(self, parent)
		self._client = None
		self._path = path
		self._iconCache = IconCache()
		self.setWindowIcon(self.icon(':/icons/browser.png'))
		self.setWindowTitle('Remote browser')
		#: need to keep a local reference to the model, or it will be GC'd by Python
		self._model = ServerFileSystemModel(path, context = self)
		self.setModel(self._model)
		self.connect(self, SIGNAL('fileSystemNotification'), self.onFileSystemNotification)
		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.connect(self, SIGNAL('activated(const QModelIndex&)'), self.onActivated)
		self.setExpandsOnDoubleClick(False)
		self.connect(self, SIGNAL('collapsed(const QModelIndex&)'), self.onCollapsed)
#		self.setSortingEnabled(True)
		self.header().setResizeMode(0, QHeaderView.Stretch)
		self.header().setResizeMode(0, QHeaderView.ResizeToContents)
		self.header().setResizeMode(1, QHeaderView.Fixed)
		self.header().setResizeMode(1, QHeaderView.Stretch)
		self.header().resizeSection(1, 70)
	
	def setClient(self, client):
		"""
		Attaches a Testerman client instance.
		"""
		self._client = client
		self._client.subscribe('system:fs', self._onFileSystemNotification)
		self.refresh()

	def _onFileSystemNotification(self, notification):
		"""
		Bouncing to Qt world.
		"""
		self.emit(SIGNAL('fileSystemNotification'), notification)
	
	def onFileSystemNotification(self, notification):
		"""
		@type  notification: TestermanMessages.Notification
		@param notification: a new FILE-SYSTEM-EVENT notification from the server.
		"""
		if not notification.getMethod() == 'FILE-SYSTEM-EVENT':
			return
		# Forward the job update to the model.
		fsInfo = notification.getApplicationBody()
		self.model().updateFileSystemInfo(fsInfo)
	
	def refresh(self):
		model = self.model()
		if model:
			model.refresh()

	def contextMenuEvent(self, event):
		index = self.indexAt(event.pos())
		
		menu = QMenu(self)
		
		if index.isValid():
			# Depending of the node, add several actions
			if self.model().isAts(index):
				menu.addAction("Edit (head)", lambda: self._open(index))

			elif self.model().isRevision(index):
				menu.addAction("Edit", lambda: self._open(index))

			elif self.model().isExecutionLog(index):
				menu.addAction("Show", lambda: self._open(index))
			
			elif self.model().isDirectory(index) or self.model().isVirtual(index):
				menu.addAction("Refresh subtree", lambda: self.model().refresh(index))
			
			elif self.model().isModule(index):
				menu.addAction("Show referencing files...", lambda: self._showReferredByFiles(index))

			menu.addSeparator()
		
		# In any case, general action
		menu.addAction("Refresh all", self.refresh)
		
		menu.popup(event.globalPos())

	def _open(self, index):
		"""
		Emits a signal according to the node type.
		"""
		if self.model().isAts(index):
			url = self.model().getUrl(index)
			print "DEBUG: opening ATS %s..." % url
			self.emit(SIGNAL('openUrl(const QUrl&)'), QUrl(url))
		elif self.model().isRevision(index):
			url = self.model().getUrl(index)
			print "DEBUG: opening Revision %s..." % url
			self.emit(SIGNAL('openUrl(const QUrl&)'), QUrl(url))
		elif self.model().isModule(index):
			url = self.model().getUrl(index)
			print "DEBUG: opening Module %s..." % url
			self.emit(SIGNAL('openUrl(const QUrl&)'), QUrl(url))
		elif self.model().isCampaign(index):
			url = self.model().getUrl(index)
			print "DEBUG: opening Campaign %s..." % url
			self.emit(SIGNAL('openUrl(const QUrl&)'), QUrl(url))
		elif self.model().isExecutionLog(index) or self.model().isLog(index):
			url = self.model().getUrl(index)
			print "DEBUG: opening Log %s..." % url
			self.emit(SIGNAL('openUrl(const QUrl&)'), QUrl(url))

	def _showReferredByFiles(self, index):
		if not self.model().isModule(index):
			return
		self.emit(SIGNAL('showReferredByFiles(const QUrl&)'), QUrl(self.model().getUrl(index)))

	def onActivated(self, index):
		"""
		Slot called when an item is activated.
		"""
		# Expand directories and virtual nodes
		if self.model().isVirtual(index) or self.model().isDirectory(index):
			self.setExpanded(index, not self.isExpanded(index))
		# Open other kind of nodes
		# (expansion is still possible through the explicit tree expand)	
		else:
			self._open(index)
	
	def onCollapsed(self, index):
		"""
		Invalidates the collapsed index so that it will refresh on
		next expansion.
		"""
		self.model().refresh(index)
			
	##
	# FileSystemViewContext
	##
	def getClient(self):
		return self._client	

	def icon(self, resource):
		return self._iconCache.icon(resource)

	def showExecutionLogs(self):
		return True
	
	def getServerAddress(self):
		return self._client.getServerAddress()


# Basic test
if __name__ == "__main__":
	import sys
	import TestermanClient

	
	app = QApplication([])

	client = TestermanClient.Client("test", "FileSystemViewer/1.0.0", serverUrl = "http://localhost:8080")
	client.startXc()

	try:	
		w = WServerFileSystemView('/repository')
		w.show()
		w.setClient(client)
	except Exception, e:
		client.stopXc()
		import TestermanNodes
		raise Exception(TestermanNodes.getBacktrace())
		
		
	app.exec_()
	client.stopXc()
