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
# Settings & Configuration management.
#
##

from PyQt4.Qt import *

import md5
import os
import shutil

from Base import *
from CommonWidgets import *

import PluginManager

################################################################################
# Settings management
################################################################################

# Dialog Box
class WSettingsDialog(QDialog):
	def __init__(self, parent = None):
		QDialog.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle(getClientName() + " configuration")
		self.settings = WSettings(self)

		# Buttons
		self.okButton = QPushButton("Ok")
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		self.cancelButton = QPushButton("Cancel")
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)

		layout = QVBoxLayout()
		layout.addWidget(self.settings)
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self.okButton)
		buttonLayout.addWidget(self.cancelButton)
		layout.addLayout(buttonLayout)
		self.setLayout(layout)

	def accept(self):
		"""
		QDialog reimplementation.
		"""
		if self.settings.checkModel():
			self.settings.updateModel()
			QDialog.accept(self)

class WSettings(QWidget):
	"""
	Client Settings. For now, a simple page.
	One day, something more complex.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		layout = QVBoxLayout()

		self.connectionSettings = WConnectionSettings()
		self.connectionSettingsGroupBox = WGroupBox("Connection", self.connectionSettings)
		layout.addWidget(self.connectionSettingsGroupBox)

		self.autoUpdateSettings = WAutoUpdateSettings()
		self.autoUpdateSettingsGroupBox = WGroupBox("Updates", self.autoUpdateSettings)
		layout.addWidget(self.autoUpdateSettingsGroupBox)

		self.uiSettings = WInterfaceSettings()
		self.uiSettingsGroupBox = WGroupBox("User interface", self.uiSettings)
		layout.addWidget(self.uiSettingsGroupBox)

		self.docSettings = WDocumentationSettings()
		self.docSettingsGroupBox = WGroupBox("Documentation", self.docSettings)
		layout.addWidget(self.docSettingsGroupBox)

		self.logsSettings = WLogsSettings()
		self.logsSettingsGroupBox = WGroupBox("Logs", self.logsSettings)
		layout.addWidget(self.logsSettingsGroupBox)

		self.pluginsSettings = WPluginsSettings()
		self.pluginsSettingsGroupBox = WGroupBox("Plugins", self.pluginsSettings)
		layout.addWidget(self.pluginsSettingsGroupBox)

		self.setLayout(layout)

		self.settings = [ self.connectionSettings, self.uiSettings, self.docSettings, self.logsSettings, self.autoUpdateSettings, self.pluginsSettings ]

	def updateModel(self):
		"""
		Update the underlying model data.
		Returns True if success, False on error.
		"""
		for setting in self.settings:
			setting.updateModel()
		return True

	def checkModel(self):
		"""
		Check the proposed values according to the possible data models.
		Returns 1 if success, 0 on error.
		"""
		for setting in self.settings:
			if not setting.checkModel():
				return False
		return True


###############################################################################
# Connection/Servers related settings
###############################################################################

class WConnectionSettings(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = QSettings()
		urllist = settings.value('connection/urllist', QVariant(QStringList(QString('http://localhost:8080')))).toStringList()
		lasturl = settings.value('connection/lasturl', QVariant(QString('http://localhost:8080'))).toString()
		username = settings.value('connection/username', QVariant(QString())).toString()

		self.urlComboBox = QComboBox()
		self.urlComboBox.setEditable(1)
		self.urlComboBox.addItems(urllist)
		self.urlComboBox.setEditText(lasturl)
		self.urlComboBox.setMaxCount(5)
		self.urlComboBox.setMaximumWidth(250)
		self.usernameLineEdit = QLineEdit(username)
		self.usernameLineEdit.setMaximumWidth(250)

		layout = QVBoxLayout()
		paramLayout = QGridLayout()
		paramLayout.addWidget(QLabel("Server URL:"), 0, 0)
		paramLayout.addWidget(self.urlComboBox, 0, 1)
		paramLayout.addWidget(QLabel("Username:"), 1, 0)
		paramLayout.addWidget(self.usernameLineEdit, 1, 1)
		layout.addLayout(paramLayout)

		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		url = self.urlComboBox.currentText()
		# URL List: the currently selected item should be the first of the saved list,
		# so that it is selected upon restoration (this requirement could be matched 
		# with other strategies, however)
		urllist = QStringList(url)
		for i in range(self.urlComboBox.count()):
			if self.urlComboBox.itemText(i) !=  self.urlComboBox.currentText():
				urllist.append(self.urlComboBox.itemText(i))
		username = self.usernameLineEdit.text()

		# We set them as current parameters
		QApplication.instance().setUsername(username)
		QApplication.instance().setServerUrl(QUrl(url))

		# We save them as settings
		settings = QSettings()
		settings.setValue('connection/urllist', QVariant(urllist))
		settings.setValue('connection/username', QVariant(username))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		url = QUrl(self.urlComboBox.currentText())
		username = self.usernameLineEdit.text()
		
		if not url.scheme() == 'http':
			QErrorMessage(self).showMessage('The Testerman server URL must start with http://')
			return 0
		if username == '':
			QErrorMessage(self).showMessage('You must enter a username')
			return 0
		return 1


###############################################################################
# Documentation related settings
###############################################################################

class WDocumentationSettings(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = QSettings()
		documentationCache = settings.value('documentation/cacheDir', QVariant(QString(QApplication.instance().get('documentationcache')))).toString()
		layout = QGridLayout()
		# Documentation cache location + browse directory button
		layout.addWidget(QLabel("Documentation cache:"), 0, 0, 1, 2)
		self.documentationCacheLineEdit = QLineEdit(documentationCache)
		self.browseDirectoryButton = QPushButton("...")
		self.connect(self.browseDirectoryButton, SIGNAL('clicked()'), self.browseForCacheDirectory)
		layout.addWidget(self.documentationCacheLineEdit, 1, 0)
		layout.addWidget(self.browseDirectoryButton, 1, 1)
		# Documentation cache clean button
		self.cleanDocumentationCacheButton = QPushButton("Clean cache now")
		self.connect(self.cleanDocumentationCacheButton, SIGNAL('clicked()'), self.cleanDocumentationCache)
		layout.addWidget(self.cleanDocumentationCacheButton, 2, 0, 1, 2)

		self.setLayout(layout)

	def browseForCacheDirectory(self):
		documentationCache = QFileDialog.getExistingDirectory(self, "Documentation cache root directory", self.documentationCacheLineEdit.text())
		if not documentationCache.isEmpty():
			self.documentationCacheLineEdit.setText(os.path.normpath(unicode(documentationCache)))

	def cleanDocumentationCache(self):
		# The cache is actually a subdir "docCache" within the configuration dir.
		# This keeps the user from selecting an existing directory that contains other things than the pure cache data,
		# and click "clean". For instance, it would be trivial to delete a complete Program Files (or windows...) directory without this 
		# additional suffix.
		documentationCache = os.path.normpath(unicode(self.documentationCacheLineEdit.text()) + "/docCache")
		print "DEBUG: cleaning " + unicode(documentationCache) + "..."
		shutil.rmtree(documentationCache, ignore_errors = True)
		userInformation(self, "Documentation cache directory cleaned up.")

	def updateModel(self):
		"""
		Update the data model.
		"""
		documentationCache = self.documentationCacheLineEdit.text()
		# We save them as settings
		settings = QSettings()
		settings.setValue('documentation/cacheDir', QVariant(documentationCache))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# General interface related settings
###############################################################################

class WInterfaceSettings(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = QSettings()
		style = settings.value('style', QVariant(QString('Cleanlooks'))).toString()
		reopenOnStartup = settings.value('mru/reopenOnStartup', QVariant(True)).toBool()

		layout = QGridLayout()
		# GUI Style
		self.styleComboBox = QComboBox()
		self.styleComboBox.addItems(QStyleFactory.keys())
		self.styleComboBox.setCurrentIndex(self.styleComboBox.findText(style))
		layout.addWidget(QLabel("GUI Style:"), 0, 0)
		layout.addWidget(self.styleComboBox, 0, 1)
		# Reopen most recently used docs on startup
		self.reopenOnStartupCheckBox = QCheckBox("Re-open last open files on startup")
		self.reopenOnStartupCheckBox.setChecked(reopenOnStartup)
		layout.addWidget(self.reopenOnStartupCheckBox, 1, 0, 1, 2)

		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		style = self.styleComboBox.currentText()

		# We save them as settings
		settings = QSettings()
		settings.setValue('style', QVariant(style))
		reopenOnStartup = self.reopenOnStartupCheckBox.isChecked()
		settings.setValue('mru/reopenOnStartup', QVariant(reopenOnStartup))

		QApplication.instance().setStyle(style)

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# Auto-update related settings
###############################################################################

class WAutoUpdateSettings(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		settings = QSettings()
		layout = QVBoxLayout()
		a = settings.value('autoupdate/acceptExperimentalUpdates', QVariant(False)).toBool()
		self.acceptExperimentalUpdatesCheckBox = QCheckBox("Accept experimental updates")
		self.acceptExperimentalUpdatesCheckBox.setChecked(a)
		layout.addWidget(self.acceptExperimentalUpdatesCheckBox)
		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		settings = QSettings()

		# We set them as current parameters
		a = self.acceptExperimentalUpdatesCheckBox.isChecked()
		settings.setValue('autoupdate/acceptExperimentalUpdates', QVariant(a))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# Log viewer related settings
###############################################################################

class WLogsSettings(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = QSettings()
		raws = settings.value('logs/raws', QVariant(True)).toBool()
		tracking = settings.value('logs/autotracking', QVariant(True)).toBool()

		layout = QVBoxLayout()
		self.rawsCheckBox = QCheckBox("Activate raw logs view")
		self.rawsCheckBox.setChecked(raws)
		layout.addWidget(self.rawsCheckBox)
		self.trackingCheckBox = QCheckBox("Automatic event tracking")
		self.trackingCheckBox.setChecked(tracking)
		layout.addWidget(self.trackingCheckBox)

		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		settings = QSettings()

		# We set them as current parameters
		raws = self.rawsCheckBox.isChecked()
		settings.setValue('logs/raws', QVariant(raws))
		tracking = self.trackingCheckBox.isChecked()
		settings.setValue('logs/autotracking', QVariant(tracking))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# Plugins related settings
###############################################################################

class WAboutPluginDialog(QDialog):
	def __init__(self, pluginInfo, parent = None):
		QDialog.__init__(self, parent)
		self.__createWidgets(pluginInfo)
	
	def __createWidgets(self, pluginInfo):
		layout = QVBoxLayout()
		self.setWindowTitle("About plugin: %s" % pluginInfo["label"])

		txt = "<p>Plugin ID: %s</p><p>Name: %s</p><p>Version: %s</p><p>Author: %s</p><p>Description:<br />%s</p>" % (pluginInfo["plugin-id"],
			pluginInfo["label"], pluginInfo["version"], pluginInfo["author"], pluginInfo["description"])

		label = QLabel(txt)
		label.setAlignment(Qt.AlignLeft)
		layout.addWidget(label)

		# Buttons
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.closeButton = QPushButton("Close")
		self.connect(self.closeButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self.closeButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

# Dialog Box wrapper over a plugin configuration widget
class WPluginSettingsDialog(QDialog):
	def __init__(self, label, configurationClass, parent = None):
		QDialog.__init__(self, parent)
		self.__createWidgets(label, configurationClass)

	def __createWidgets(self, label, configurationClass):
		self.setWindowTitle("Plugin configuration: %s" % label)
		self.settings = configurationClass(self)
		self.settings.displayConfiguration()

		# Buttons
		self.okButton = QPushButton("Ok")
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		self.cancelButton = QPushButton("Cancel")
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)

		layout = QVBoxLayout()
		layout.addWidget(self.settings)
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self.okButton)
		buttonLayout.addWidget(self.cancelButton)
		layout.addLayout(buttonLayout)
		self.setLayout(layout)

	def accept(self):
		"""
		QDialog reimplementation.
		"""
		if self.settings.checkConfiguration():
			self.settings.saveConfiguration()
			QDialog.accept(self)

class WPluginsSettings(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()
	
	def __createWidgets(self):
		layout = QHBoxLayout()
		self.pluginsTreeView = WPluginsTreeView()
		layout.addWidget(self.pluginsTreeView)
		self.setLayout(layout)
	
	def checkModel(self):
		return self.pluginsTreeView.checkModel()
	
	def updateModel(self):
		return self.pluginsTreeView.updateModel()

class WPluginsTreeView(QTreeWidget):
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self.__createWidgets()
		self.__createActions()
		self.buildTree()

	def __createWidgets(self):
		pass
	
	def buildTree(self):
		self.clear()
		class PluginItem(QTreeWidgetItem):
			def __init__(self, pluginInfo, parent):
				QTreeWidgetItem.__init__(self, parent)
				self.pluginInfo = pluginInfo
				self.pluginId = pluginInfo['plugin-id']
				self.setText(0, pluginInfo['label'])
				self.setText(1, pluginInfo['type'])
				self.configurationClass = pluginInfo['configuration-class']
				self.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
				if pluginInfo['activated']:
					self.setCheckState(2, Qt.Checked)
				else:
					self.setCheckState(2, Qt.Unchecked)

			def activated(self):
				return self.checkState(2) == Qt.Checked
	
		self.setRootIsDecorated(False)
		self.setSortingEnabled(True)
		self.sortItems(0, Qt.AscendingOrder)
		self.setHeaderLabels(QStringList([ "name", "type", "activated"]))
#		settings = QSettings()
		# Load all plugins into a listview
		for v in PluginManager.getPluginClasses():
			item = PluginItem(v, parent = self)

		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)

	def __createActions(self):
		# Hidden actions for now. To expose through a contextual popup menu.
		self.rescanAction = TestermanAction(self, "Rescan plugins", PluginManager.rescanPlugins)
		self.rescanAction.setShortcut("F5")
		self.rescanAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.rescanAction)
		self.aboutAction = TestermanAction(self, "About", self.aboutPlugin)
		self.aboutAction.setShortcut("Ctrl+Shift+A")
		self.aboutAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.aboutAction)

	def rescanPlugins(self):
		PluginManager.rescanPlugins()
		self.buildTree()

	def aboutPlugin(self):
		item = self.currentItem()
		if item:
			dialog = WAboutPluginDialog(item.pluginInfo, self)
			dialog.exec_()

	def onItemActivated(self, item, col):
		if item:
			dialog = WPluginSettingsDialog(item.text(0), item.configurationClass, self)
			dialog.exec_()
	
	def updateModel(self):
		# Activate/deactivate plugins
		settings = QSettings()
		root = self.invisibleRootItem()
		for i in range(0, root.childCount()):
			item = root.child(i)
			settings.setValue('plugins/activated/' + item.pluginId, QVariant(item.activated()))
		pass
	
	def checkModel(self):
		return True
	
