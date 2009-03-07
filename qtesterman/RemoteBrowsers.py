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
##

from PyQt4.Qt import *

import os.path
import re

from Base import *

import Actions
import LogViewer
import ServerFileSystemView

################################################################################
# Server File System related actions
################################################################################

def deleteAts(url, deleteExecutionLogs = True):
	"""
	Deletes an ATS and its associated execution logs.

	@type  url: QUrl
	@param url: the url of the file to delete
	@type  deleteExecutionLogs: bool
	@param deleteExecutionLogs: delete associated execution logs (with TE), if any
	"""
	atsPath = unicode(url.path())
	QApplication.instance().client().removeFile(unicode(atsPath))
	if deleteExecutionLogs:
		# compute associated log path
		archivePath = '/archives/%s' % ('/'.join(atsPath.split('/')[2:]))
		# this archive folder contains all TEs and all associated logs for the ats.
		# Delete all.
		# Will fail as the directory is not empty...
		QApplication.instance().client().removeFile(unicode(archivePath))

def deleteExecutionLog(url, deleteTestExecutable = True):
	"""
	Deletes an execution log and its associated TE.

	@type  path: QUrl
	@param url: the url of the file to delete
	@type  deleteTestExecutable: bool
	@param deleteTestExecutable: delete associated TE package
	"""
	logPath = unicode(url.path())
	assert(logPath.endswith('.log'))
	tePath = logPath[:-4] # removes the trailing '.log'
	QApplication.instance().client().removeFile(logPath)
	if deleteTestExecutable:
		# Will fail as the directory is not empty...
		QApplication.instance().client().removeFile(tePath)

def deleteFile(url):
	"""
	Deletes a single file.
	
	@type  url: QUrl
	@param url: the url of the file to delete
	"""
	path = unicode(url.path())
	QApplication.instance().client().removeFile(path)

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
		self.repositoryTree = ServerFileSystemView.WServerFileSystemTreeWidget('/repository', self.tab)
		self.repositoryTree.setClient(getProxy())
		self.controller.addView(self.repositoryTree)
		self.tab.addTab(self.repositoryTree, 'Repository')
		self.archivesTree = ServerFileSystemView.WServerFileSystemTreeWidget('/archives', self.tab)
		self.archivesTree.setClient(getProxy())
		self.controller.addView(self.archivesTree)
		self.tab.addTab(self.archivesTree, 'Archives')
		self.setWidget(self.tab)
