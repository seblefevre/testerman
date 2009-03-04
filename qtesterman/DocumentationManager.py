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
# Documentation manager.
# Interfaces a DocGenerator cache.
# Displays documentation.
#
##

from PyQt4.Qt import *

from Base import *
import CommonWidgets
import DocumentationGenerator

import os

class WDocumentationView(QWidget):
	"""
	This widget displays a documentation through a HTML viewer.
	Basic search function.
	"""
	def __init__(self, pathToIndex, title, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()
		self.setWindowTitle(title)
		log("Setting documentation source to: %s" % pathToIndex)
		self.browser.setSource(QUrl.fromLocalFile(pathToIndex))

	def __createWidgets(self):
		layout = QVBoxLayout()

		self.browser = QTextBrowser()
		self.browser.setOpenExternalLinks(True)
		layout.addWidget(self.browser)

		self.buttonLayout = QHBoxLayout()
		self.buttonLayout.addWidget(CommonWidgets.WFind(self.browser))
		layout.addLayout(self.buttonLayout)

		self.setLayout(layout)

def showContentDocumentation(content, key, parent):
	settings = QSettings()
	documentationCache = os.path.normpath(unicode(settings.value('documentation/cacheDir', QVariant(QString(QApplication.instance().get('documentationcache')))).toString()) + "/docCache")
	cache = DocumentationGenerator.DocumentationCacheManager(documentationCache)
	transient = CommonWidgets.WTransientWindow("Doc Generator", parent)
	transient.showTextLabel("Generating documentation...")
	path = cache.generateDocumentation(content, key)
	transient.hide()
	transient.setParent(None)
	if path:
		view = WDocumentationView(path, "Documentation for %s" % key, parent)
		view.setWindowFlags(Qt.Window)
		view.show()
	else:
		CommonWidgets.systemError(parent, "Unable to generate documentation, please check stderr output.\nPlease check epydoc syntax and indentation")
