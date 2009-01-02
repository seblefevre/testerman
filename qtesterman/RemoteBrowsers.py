##
# -*- coding: utf-8 -*-
#
# Remote browsers, triggering appropriate actions when needed.
#
##

from PyQt4.Qt import *

import os.path
import re

from Base import *

import Actions
import LogViewer
import ServerFileSystemView

################################################################################
# View Controller
################################################################################

class ViewController(QObject):
	"""
	The bridge between view signals and the business logic.
	"""
	def __init__(self, parent = None):
		QObject.__init__(self, parent)
	
	def addView(self, view):
		self.connect(view, SIGNAL('openUrl(const QUrl&)'), self.openUrl)
		self.connect(view, SIGNAL('showReferredByFiles(const QUrl&)'), self.displayReferencingFiles)
	
	def openUrl(self, url):
		log("Ready to open URL: " + unicode(url.toString()))
		
		if url.path().endsWith('.log'):
			self.showLog(url)
		else:
			qt.QApplication.instance().get('gui.documentmanager').openUrl(url)

	def showLog(self, url):
		"""
		@type  url: QUrl
		@param url: the url of the file to analyze and display
		"""
		logViewer = LogViewer.WLogViewer(parent = self.parent())
		logViewer.openUrl(url)
		logViewer.show()

	def displayReferencingFiles(self, url):
		"""
		Displays the files referencing the module.
		"""
		path = unicode(url.path().toString())
		ret = getProxy().getReferencingFiles(path)
		ret.sort()
		dialog = WTextEditDialog(text = '\n'.join(ret), readOnly = True, title = "Files referencing module %s: %d file(s)" % (path, len(ret)), fixedFont = True, parent = self)
		dialog.exec_()


################################################################################
# A Dock bridging views and a controller
################################################################################
		
class WRepositoryBrowsingDock(QDockWidget):
	def __init__(self, parent):
		QDockWidget.__init__(self, parent)
		self.connect(self, SIGNAL("nextInitializationStep(QString&)"), qt.QApplication.instance().get('gui.splash').showMessage)
		self.__createWidgets()

	def __createWidgets(self):
		self.controller = ViewController(self)
		
		self.setWindowTitle("Remote browsing")
		self.tab = qt.QTabWidget(self)
		self.emit(SIGNAL("nextInitializationStep(QString&)"), qt.QString("Initializing remote browsers (repository)..."))
		self.repositoryTree = ServerFileSystemView.WServerFileSystemView('/repository', self.tab)
		self.repositoryTree.setClient(getProxy())
		self.controller.addView(self.repositoryTree)
		self.tab.addTab(self.repositoryTree, 'Repository')
		self.emit(SIGNAL("nextInitializationStep(QString&)"), qt.QString("Initializing remote browsers (archives)..."))
		self.archivesTree = ServerFileSystemView.WServerFileSystemView('/archives', self.tab)
		self.archivesTree.setClient(getProxy())
		self.controller.addView(self.archivesTree)
		self.tab.addTab(self.archivesTree, 'Archives')
		self.setWidget(self.tab)
