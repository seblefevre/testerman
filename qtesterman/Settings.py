##
# -*- coding: utf-8 -*-
#
# Settings & Configuration management.
#
# $Id$
##

import PyQt4.Qt as qt
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
class WSettingsDialog(qt.QDialog):
	def __init__(self, parent = None):
		qt.QDialog.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle(getClientName() + " configuration")
		self.settings = WSettings(self)

		# Buttons
		self.okButton = qt.QPushButton("Ok")
		self.connect(self.okButton, qt.SIGNAL("clicked()"), self.accept)
		self.cancelButton = qt.QPushButton("Cancel")
		self.connect(self.cancelButton, qt.SIGNAL("clicked()"), self.reject)

		layout = qt.QVBoxLayout()
		layout.addWidget(self.settings)
		buttonLayout = qt.QHBoxLayout()
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
			qt.QDialog.accept(self)

class WSettings(qt.QWidget):
	"""
	Client Settings. For now, a simple page.
	One day, something more complex.
	"""
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		layout = qt.QVBoxLayout()

		self.connectionSettings = WConnectionSettings()
		self.connectionSettingsGroupBox = WGroupBox("Connection", self.connectionSettings)
		layout.addWidget(self.connectionSettingsGroupBox)

		self.autoUpdateSettings = WAutoUpdateSettings()
		self.autoUpdateSettingsGroupBox = WGroupBox("Automatic updates", self.autoUpdateSettings)
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

class WConnectionSettings(qt.QWidget):
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = qt.QSettings()
		urllist = settings.value('connection/urllist', qt.QVariant(qt.QStringList(qt.QString('http://localhost:8080')))).toStringList()
		username = settings.value('connection/username', qt.QVariant(qt.QString())).toString()

		self.urlComboBox = qt.QComboBox()
		self.urlComboBox.setEditable(1)
		self.urlComboBox.addItems(urllist)
		self.urlComboBox.setMaxCount(5)
		self.urlComboBox.setMaximumWidth(250)
		self.usernameLineEdit = qt.QLineEdit(username)
		self.usernameLineEdit.setMaximumWidth(250)

		layout = qt.QVBoxLayout()
		paramLayout = qt.QGridLayout()
		paramLayout.addWidget(qt.QLabel("Server URL:"), 0, 0)
		paramLayout.addWidget(self.urlComboBox, 0, 1)
		paramLayout.addWidget(qt.QLabel("Username:"), 1, 0)
		paramLayout.addWidget(self.usernameLineEdit, 1, 1)
		layout.addLayout(paramLayout)

		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		url = str(self.urlComboBox.currentText().toAscii())
		# URL List: the currently selected item should be the first of the saved list,
		# so that it is selected upon restoration (this requirement could be matched 
		# with other strategies, however)
		urllist = qt.QStringList(self.urlComboBox.currentText())
		for i in range(0, self.urlComboBox.count()):
			if self.urlComboBox.itemText(i) !=  self.urlComboBox.currentText():
				urllist.append(self.urlComboBox.itemText(i))
		username = str(self.usernameLineEdit.text().toAscii())

		# We set them as current parameters
		qt.QApplication.instance().set('ws.username', username)
		qt.QApplication.instance().setTestermanServer(url)

		# We save them as settings
		settings = qt.QSettings()
		settings.setValue('connection/urllist', qt.QVariant(urllist))
		settings.setValue('connection/username', qt.QVariant(username))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		url = str(self.urlComboBox.currentText().toAscii())
		username = str(self.usernameLineEdit.text().toAscii())
		
		if not qt.QUrl(url).scheme() == 'http':
			qt.QErrorMessage(self).showMessage('The Testerman server URL must start with http://')
			return 0
		if username == '':
			qt.QErrorMessage(self).showMessage('You must enter a username')
			return 0
		return 1


###############################################################################
# Documentation related settings
###############################################################################

class WDocumentationSettings(qt.QWidget):
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = qt.QSettings()
		documentationCache = settings.value('documentation/cacheDir', qt.QVariant(qt.QString(qt.QApplication.instance().get('documentationcache')))).toString()
		layout = qt.QGridLayout()
		# Documentation cache location + browse directory button
		layout.addWidget(qt.QLabel("Documentation cache:"), 0, 0, 1, 2)
		self.documentationCacheLineEdit = qt.QLineEdit(documentationCache)
		self.browseDirectoryButton = qt.QPushButton("...")
		self.connect(self.browseDirectoryButton, qt.SIGNAL('clicked()'), self.browseForCacheDirectory)
		layout.addWidget(self.documentationCacheLineEdit, 1, 0)
		layout.addWidget(self.browseDirectoryButton, 1, 1)
		# Documentation cache clean button
		self.cleanDocumentationCacheButton = qt.QPushButton("Clean cache now")
		self.connect(self.cleanDocumentationCacheButton, qt.SIGNAL('clicked()'), self.cleanDocumentationCache)
		layout.addWidget(self.cleanDocumentationCacheButton, 2, 0, 1, 2)

		self.setLayout(layout)

	def browseForCacheDirectory(self):
		documentationCache = qt.QFileDialog.getExistingDirectory(self, "Documentation cache root directory", self.documentationCacheLineEdit.text())
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
		settings = qt.QSettings()
		settings.setValue('documentation/cacheDir', qt.QVariant(documentationCache))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# General interface related settings
###############################################################################

class WInterfaceSettings(qt.QWidget):
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = qt.QSettings()
		style = settings.value('style', qt.QVariant(qt.QString('Cleanlooks'))).toString()
		reopenOnStartup = settings.value('mru/reopenOnStartup', qt.QVariant(True)).toBool()

		layout = qt.QGridLayout()
		# GUI Style
		self.styleComboBox = qt.QComboBox()
		self.styleComboBox.addItems(qt.QStyleFactory.keys())
		self.styleComboBox.setCurrentIndex(self.styleComboBox.findText(style))
		layout.addWidget(qt.QLabel("GUI Style:"), 0, 0)
		layout.addWidget(self.styleComboBox, 0, 1)
		# Reopen most recently used docs on startup
		self.reopenOnStartupCheckBox = qt.QCheckBox("Re-open last open files on startup")
		self.reopenOnStartupCheckBox.setChecked(reopenOnStartup)
		layout.addWidget(self.reopenOnStartupCheckBox, 1, 0, 1, 2)

		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		style = self.styleComboBox.currentText()

		# We save them as settings
		settings = qt.QSettings()
		settings.setValue('style', qt.QVariant(style))
		reopenOnStartup = self.reopenOnStartupCheckBox.isChecked()
		settings.setValue('mru/reopenOnStartup', qt.QVariant(reopenOnStartup))

		qt.QApplication.instance().setStyle(style)

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# Auto-update related settings
###############################################################################

class WAutoUpdateSettings(qt.QWidget):
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		settings = qt.QSettings()
		layout = qt.QVBoxLayout()
		a = settings.value('autoupdate/acceptExperimentalUpdates', qt.QVariant(False)).toBool()
		self.acceptExperimentalUpdatesCheckBox = qt.QCheckBox("Accept experimental updates")
		self.acceptExperimentalUpdatesCheckBox.setChecked(a)
		layout.addWidget(self.acceptExperimentalUpdatesCheckBox)
		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		settings = qt.QSettings()

		# We set them as current parameters
		a = self.acceptExperimentalUpdatesCheckBox.isChecked()
		settings.setValue('autoupdate/acceptExperimentalUpdates', qt.QVariant(a))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# Log viewer related settings
###############################################################################

class WLogsSettings(qt.QWidget):
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = qt.QSettings()
		raws = settings.value('logs/raws', qt.QVariant(True)).toBool()
		tracking = settings.value('logs/autotracking', qt.QVariant(True)).toBool()

		layout = qt.QVBoxLayout()
		self.rawsCheckBox = qt.QCheckBox("Activate raw logs view")
		self.rawsCheckBox.setChecked(raws)
		layout.addWidget(self.rawsCheckBox)
		self.trackingCheckBox = qt.QCheckBox("Automatic event tracking")
		self.trackingCheckBox.setChecked(tracking)
		layout.addWidget(self.trackingCheckBox)

		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		settings = qt.QSettings()

		# We set them as current parameters
		raws = self.rawsCheckBox.isChecked()
		settings.setValue('logs/raws', qt.QVariant(raws))
		tracking = self.trackingCheckBox.isChecked()
		settings.setValue('logs/autotracking', qt.QVariant(tracking))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return 1


###############################################################################
# Plugins related settings
###############################################################################

class WAboutPluginDialog(qt.QDialog):
	def __init__(self, pluginInfo, parent = None):
		qt.QDialog.__init__(self, parent)
		self.__createWidgets(pluginInfo)
	
	def __createWidgets(self, pluginInfo):
		layout = qt.QVBoxLayout()
		self.setWindowTitle("About plugin: %s" % pluginInfo["label"])

		txt = "<p>Plugin ID: %s</p><p>Name: %s</p><p>Version: %s</p><p>Author: %s</p><p>Description:<br />%s</p>" % (pluginInfo["plugin-id"],
			pluginInfo["label"], pluginInfo["version"], pluginInfo["author"], pluginInfo["description"])

		label = qt.QLabel(txt)
		label.setAlignment(qt.Qt.AlignLeft)
		layout.addWidget(label)

		# Buttons
		buttonLayout = qt.QHBoxLayout()
		buttonLayout.addStretch()
		self.closeButton = qt.QPushButton("Close")
		self.connect(self.closeButton, qt.SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self.closeButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

# Dialog Box wrapper over a plugin configuration widget
class WPluginSettingsDialog(qt.QDialog):
	def __init__(self, label, configurationClass, parent = None):
		qt.QDialog.__init__(self, parent)
		self.__createWidgets(label, configurationClass)

	def __createWidgets(self, label, configurationClass):
		self.setWindowTitle("Plugin configuration: %s" % label)
		self.settings = configurationClass(self)
		self.settings.displayConfiguration()

		# Buttons
		self.okButton = qt.QPushButton("Ok")
		self.connect(self.okButton, qt.SIGNAL("clicked()"), self.accept)
		self.cancelButton = qt.QPushButton("Cancel")
		self.connect(self.cancelButton, qt.SIGNAL("clicked()"), self.reject)

		layout = qt.QVBoxLayout()
		layout.addWidget(self.settings)
		buttonLayout = qt.QHBoxLayout()
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
			qt.QDialog.accept(self)

class WPluginsSettings(qt.QWidget):
	def __init__(self, parent = None):
		qt.QWidget.__init__(self, parent)
		self.__createWidgets()
	
	def __createWidgets(self):
		layout = qt.QHBoxLayout()
		self.pluginsTreeView = WPluginsTreeView()
		layout.addWidget(self.pluginsTreeView)
		self.setLayout(layout)
	
	def checkModel(self):
		return self.pluginsTreeView.checkModel()
	
	def updateModel(self):
		return self.pluginsTreeView.updateModel()

class WPluginsTreeView(qt.QTreeWidget):
	def __init__(self, parent = None):
		qt.QTreeWidget.__init__(self, parent)
		self.__createWidgets()
		self.__createActions()
		self.buildTree()

	def __createWidgets(self):
		pass
	
	def buildTree(self):
		self.clear()
		class PluginItem(qt.QTreeWidgetItem):
			def __init__(self, pluginInfo, parent):
				qt.QTreeWidgetItem.__init__(self, parent)
				self.pluginInfo = pluginInfo
				self.pluginId = pluginInfo['plugin-id']
				self.setText(0, pluginInfo['label'])
				self.setText(1, pluginInfo['type'])
				self.configurationClass = pluginInfo['configuration-class']
				self.setFlags(qt.Qt.ItemIsUserCheckable | qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable)
				if pluginInfo['activated']:
					self.setCheckState(2, qt.Qt.Checked)
				else:
					self.setCheckState(2, qt.Qt.Unchecked)

			def activated(self):
				return self.checkState(2) == qt.Qt.Checked
	
		self.setRootIsDecorated(False)
		self.setSortingEnabled(True)
		self.sortItems(0, qt.Qt.AscendingOrder)
		self.setHeaderLabels(qt.QStringList([ "name", "type", "activated"]))
#		settings = qt.QSettings()
		# Load all plugins into a listview
		for v in PluginManager.getPluginClasses():
			item = PluginItem(v, parent = self)

		self.connect(self, qt.SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)

	def __createActions(self):
		# Hidden actions for now. To expose through a contextual popup menu.
		self.rescanAction = TestermanAction(self, "Rescan plugins", PluginManager.rescanPlugins)
		self.rescanAction.setShortcut("F5")
		self.rescanAction.setShortcutContext(qt.Qt.WidgetShortcut)
		self.addAction(self.rescanAction)
		self.aboutAction = TestermanAction(self, "About", self.aboutPlugin)
		self.aboutAction.setShortcut("Ctrl+Shift+A")
		self.aboutAction.setShortcutContext(qt.Qt.WidgetShortcut)
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
		settings = qt.QSettings()
		root = self.invisibleRootItem()
		for i in range(0, root.childCount()):
			item = root.child(i)
			settings.setValue('plugins/activated/' + item.pluginId, qt.QVariant(item.activated()))
		pass
	
	def checkModel(self):
		return True
	
