##
# -*- coding: utf-8 -*-
#
# Documentation manager.
# Interfaces a DocGenerator cache.
# Displays documentation.
#
##

import PyQt4.Qt as qt

from Base import *
import CommonWidgets
import DocumentationGenerator

import os

class WDocumentationView(qt.QWidget):
	"""
	This widget displays a documentation through a HTML viewer.
	Basic search function.
	"""
	def __init__(self, pathToIndex, title, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()
		self.setWindowTitle(title)
		log("Setting documentation source to: %s" % pathToIndex)
		self.browser.setSource(qt.QUrl.fromLocalFile(pathToIndex))

	def __createWidgets(self):
		layout = qt.QVBoxLayout()

		self.browser = qt.QTextBrowser()
		self.browser.setOpenExternalLinks(True)
		layout.addWidget(self.browser)

		self.buttonLayout = qt.QHBoxLayout()
		self.buttonLayout.addWidget(CommonWidgets.WFind(self.browser))
		layout.addLayout(self.buttonLayout)

		self.setLayout(layout)

def showContentDocumentation(content, key, parent):
	settings = qt.QSettings()
	documentationCache = os.path.normpath(unicode(settings.value('documentation/cacheDir', qt.QVariant(qt.QString(qt.QApplication.instance().get('documentationcache')))).toString()) + "/docCache")
	cache = DocumentationGenerator.DocumentationCacheManager(documentationCache)
	transient = CommonWidgets.WTransientWindow("Doc Generator", parent)
	transient.showTextLabel("Generating documentation...")
	path = cache.generateDocumentation(content, key)
	transient.hide()
	transient.setParent(None)
	if path:
		view = WDocumentationView(path, "Documentation for %s" % key, parent)
		view.setWindowFlags(qt.Qt.Window)
		view.show()
	else:
		CommonWidgets.systemError(parent, "Unable to generate documentation, please check stderr output.\nPlease check epydoc syntax and indentation")
