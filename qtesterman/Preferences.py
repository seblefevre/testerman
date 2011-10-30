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
# NB: GUI guidelines: labels are right-aligned, input fields are left-aligned.
#
##

from PyQt4.Qt import *

import os
import shutil

from Base import *
from CommonWidgets import *

import PluginManager
import AutoUpdate

################################################################################
# Settings management
################################################################################

# Dialog Box
class WPreferencesDialog(QDialog):
	def __init__(self, parent = None):
		QDialog.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("%s preferences" % getClientName())

		layout = QVBoxLayout()
		self._preferences = WPreferences(self)
		layout.addWidget(self._preferences)

		# Buttons
		self._okButton = QPushButton("Ok")
		self.connect(self._okButton, SIGNAL("clicked()"), self.accept)
		self._cancelButton = QPushButton("Cancel")
		self.connect(self._cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self._okButton)
		buttonLayout.addWidget(self._cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)
		self.resize(500, 300)

	def accept(self):
		"""
		QDialog reimplementation.
		"""
		if self._preferences.validate():
			self._preferences.updateModel()
			QDialog.accept(self)

class WPreferencesPage(QWidget):
	"""
	A single page of preferences.
	Offers several facility to add a WSettings in it,
	either as a labelled groupbox or as a single setting.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self._layout = QVBoxLayout()
		self.setLayout(self._layout)

	def addBoxedWidget(self, widget, label):
		self._layout.addWidget(WGroupBox(label, widget))

	def addWidget(self, widget):
		self._layout.addWidget(widget)
	
	def addStretch(self):
		self._layout.addStretch(2)

class WPreferences(QTabWidget):
	"""
	Settings/Preferences.
	One tab per group of actions, each tab may contain more than a single
	widget.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):

		page = WPreferencesPage()		
		self._connectionSettings = WConnectionSettings()
		self._autoUpdateSettings = WAutoUpdateSettings()
		page.addBoxedWidget(self._connectionSettings, "Connection")
		page.addBoxedWidget(self._autoUpdateSettings, "Updates")
		page.addStretch()
		self.addTab(page, "Server")

		page = WPreferencesPage(self)
		self._uiSettings = WInterfaceSettings()
		self._logsSettings = WLogsSettings()
		self._editorSettings = WEditorSettings()
		page.addBoxedWidget(self._uiSettings, "General")
		page.addBoxedWidget(self._logsSettings, "Log viewer")
		page.addBoxedWidget(self._editorSettings, "Code editor")
		page.addStretch()
		self.addTab(page, "User interface")

		page = WPreferencesPage(self)
		self._editorColorsSettings = WEditorColorsSettings()
		page.addBoxedWidget(self._editorColorsSettings, "Editor colors")
		page.addStretch()
		self.addTab(page, "Colors")

		page = WPreferencesPage(self)
		self._pluginsSettings = WPluginsSettings()
		page.addWidget(self._pluginsSettings)
		self.addTab(page, "Plugins")

		self._settings = [ 
			self._connectionSettings,
			self._uiSettings,
			self._logsSettings,
			self._autoUpdateSettings,
			self._pluginsSettings,
			self._editorSettings, 
			self._editorColorsSettings ]

	def updateModel(self):
		"""
		Update the underlying model data.
		"""
		for setting in self._settings:
			setting.updateModel()

	def validate(self):
		"""
		Validates all the user input, delegating the local validation
		to each setting widget.
		
		@rtype: bool
		@returns: True if OK, False otherwise.
		"""
		for setting in self._settings:
			if not setting.validate():
				return False
		return True

class WSettings(QWidget):
	"""
	Base class/interface to create widgets dedicated to a single-domain
	preferences, called settings.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
	
	def updateModel(self):
		"""
		To reimplement.
		Called to write the validated settings to a persistent storage 
		plus activate them if applicable (server changes, etc).
		"""
		pass
	
	def validate(self):
		"""
		To reimplement.
		Called to validate the user input.
		@rtype: bool
		@returns: True if the user input are all valid, False otherwise.
		You may display additional message boxes to point the user to his/her 
		invalid input.
		
		The default implementation assumes that no validation is required.
		"""
		return True


###############################################################################
# Connection/Servers related settings
###############################################################################

class WConnectionSettings(WSettings):
	def __init__(self, parent = None):
		WSettings.__init__(self, parent)
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
		self.urlComboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.usernameLineEdit = QLineEdit(username)
		self.usernameLineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

		layout = QVBoxLayout()
		form = QFormLayout()
		form.setMargin(2)
		form.addRow("Server URL:", self.urlComboBox)
		form.addRow("Username:", self.usernameLineEdit)
		layout.addLayout(form)
		layout.addStretch()

		self.setLayout(layout)

	def updateModel(self):
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

	def validate(self):
		url = QUrl(self.urlComboBox.currentText())
		username = self.usernameLineEdit.text()
		
		if not url.scheme() == 'http':
			QErrorMessage(self).showMessage('The Testerman server URL must start with http://')
			return False
		if username == '':
			QErrorMessage(self).showMessage('You must enter a username')
			return False
		return True


###############################################################################
# General interface related settings
###############################################################################

class WInterfaceSettings(WSettings):
	def __init__(self, parent = None):
		WSettings.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = QSettings()
		style = settings.value('style', QVariant(QString('Cleanlooks'))).toString()
		reopenOnStartup = settings.value('mru/reopenOnStartup', QVariant(True)).toBool()
		enableArchivesBrowser = settings.value('enableArchiveBrowser', QVariant(False)).toBool()

		vlayout = QVBoxLayout()
		layout = QGridLayout()
		layout.setColumnStretch(1, 1)
		# GUI Style
		self.styleComboBox = QComboBox()
		self.styleComboBox.addItems(QStyleFactory.keys())
		self.styleComboBox.setCurrentIndex(self.styleComboBox.findText(style))
		layout.addWidget(QLabel("GUI Style:"), 0, 0, Qt.AlignRight)
		layout.addWidget(self.styleComboBox, 0, 1, Qt.AlignLeft)
		# Reopen most recently used docs on startup
		self.reopenOnStartupCheckBox = QCheckBox("Re-open last open files on startup")
		self.reopenOnStartupCheckBox.setChecked(reopenOnStartup)
		layout.addWidget(self.reopenOnStartupCheckBox, 1, 0, 1, 2, Qt.AlignLeft)
		# Display the archives browser
		self.enableArchivesBrowserCheckBox = QCheckBox("Show archives remote browser (requires restart)")
		self.enableArchivesBrowserCheckBox.setChecked(enableArchivesBrowser)
		layout.addWidget(self.enableArchivesBrowserCheckBox, 2, 0, 1, 2, Qt.AlignLeft)
		vlayout.addLayout(layout)
		vlayout.addStretch()
		self.setLayout(vlayout)

	def updateModel(self):
		style = self.styleComboBox.currentText()

		# We save them as settings
		settings = QSettings()
		settings.setValue('style', QVariant(style))
		reopenOnStartup = self.reopenOnStartupCheckBox.isChecked()
		settings.setValue('mru/reopenOnStartup', QVariant(reopenOnStartup))
		enableArchivesBrowser = self.enableArchivesBrowserCheckBox.isChecked()
		settings.setValue('enableArchiveBrowser', QVariant(enableArchivesBrowser))

		QApplication.instance().setStyle(style)


###############################################################################
# Colors settings
###############################################################################

class ColorButton(QPushButton):
	def __init__(self, settingPath, defaultColor = QColor(), label = None, parent = None):
		QPushButton.__init__(self, parent)
		self._settingPath = settingPath
		self._color = defaultColor
		self.setIconSize(QSize(12, 12))
		self.setMinimumSize(QSize(50, 0))
		if label:
			self.setText(label)
		self.connect(self, SIGNAL('clicked()'), self.onClicked)
		self.load()

	def onClicked(self):
		self._setColor(QColorDialog.getColor(self._color, self))

	def load(self):
		settings = QSettings()
		self._setColor(QColor(settings.value(self._settingPath, QVariant(self._color)).toString()))

	def _setColor(self, color):
		if color.isValid():
			self._color = color
			pixmap = QPixmap(self.iconSize())
			pixmap.fill(color)
			self.setIcon(QIcon(pixmap))

	def save(self):
		settings = QSettings()
		settings.setValue(self._settingPath, QVariant(self._color.name()))

class WEditorColorsSettings(WSettings):
	"""
	Editor colors.
	"""
	def __init__(self, parent = None):
		WSettings.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		clayout = QGridLayout()
		colors = [
			('Default', 'default', QColor(Qt.black), QColor(Qt.white)),
			('Comments', 'comments', QColor(Qt.red), QColor(Qt.white)),
			('Strings', 'strings', QColor(Qt.darkGreen), QColor(Qt.white)),
			('Numbers', 'numbers', QColor(Qt.darkMagenta), QColor(Qt.white)),
			('Identifiers', 'identifiers', QColor(Qt.black), QColor(Qt.white)),
			('Keywords', 'keywords', QColor(Qt.blue), QColor(Qt.white)),
			('Decorators', 'decorators', QColor(Qt.black), QColor(Qt.white)),
			('Operators', 'operators', QColor(Qt.black), QColor(Qt.white)),
		]
		self._colorButtons = []
		i = 0
		for label, name, defaultFg, defaultBg in colors:
			clayout.addWidget(QLabel('%s:' % label), i, 0, Qt.AlignRight)
			colorButton = ColorButton('editor/colors/%s.fg' % name, defaultFg)
			colorButton.setToolTip('Foreground color')
			self._colorButtons.append(colorButton)
			clayout.addWidget(colorButton, i, 1)
			colorButton = ColorButton('editor/colors/%s.bg' % name, defaultBg)
			colorButton.setToolTip('Background color')
			self._colorButtons.append(colorButton)
			clayout.addWidget(colorButton, i, 2)
			clayout.setColumnStretch(3, 1)
			i += 1
		self.setLayout(clayout)

	def updateModel(self):
		# We save them as settings
		settings = QSettings()
		for button in self._colorButtons:
			button.save()


###############################################################################
# Editor settings
###############################################################################

class WEditorSettings(WSettings):
	"""
	For now, only a way to activate/deactivate autocompletion.
	Will be completed later with other options.
	"""
	def __init__(self, parent = None):
		WSettings.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		# Read the settings
		settings = QSettings()
		autocompletion = settings.value('editor/autocompletion', QVariant(False)).toBool()

		layout = QVBoxLayout()
		self._autocompletionCheckBox = QCheckBox("Enable code autocompletion (experimental)")
		self._autocompletionCheckBox.setChecked(autocompletion)
		layout.addWidget(self._autocompletionCheckBox)

		layout.addStretch()
		self.setLayout(layout)

	def updateModel(self):
		# We save them as settings
		settings = QSettings()
		autocompletion = self._autocompletionCheckBox.isChecked()
		settings.setValue('editor/autocompletion', QVariant(autocompletion))


###############################################################################
# Auto-update related settings
###############################################################################

class WAutoUpdateSettings(WSettings):
	def __init__(self, parent = None):
		WSettings.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		settings = QSettings()
		layout = QVBoxLayout()
		a = settings.value('autoupdate/acceptExperimentalUpdates', QVariant(False)).toBool()
		self.acceptExperimentalUpdatesCheckBox = QCheckBox("Accept experimental updates")
		self.acceptExperimentalUpdatesCheckBox.setChecked(a)
		layout.addWidget(self.acceptExperimentalUpdatesCheckBox)
		self.checkUpdatesButton = QPushButton("Check updates now")
		self.connect(self.checkUpdatesButton, SIGNAL("clicked()"), self.checkUpdates)
		layout.addWidget(self.checkUpdatesButton)
		layout.addStretch()
		self.setLayout(layout)

	def checkUpdates(self):
		branches = [ 'stable' ]
		if self.acceptExperimentalUpdatesCheckBox.isChecked():
			branches.append('testing')
			branches.append('experimental')

		versionInfo = AutoUpdate.getNewVersionInfo(proxy = QApplication.instance().client(), component = "qtesterman", currentVersion = getClientVersion(), branches = branches)
		if versionInfo:
			(newerVersion, branch, url) = versionInfo
			ret = QMessageBox.question(None, getClientName(), "A new QTesterman Client version is available on the server:\n%s (%s)\nDo you want to update now ?" % (newerVersion, branch), QMessageBox.Yes, QMessageBox.No)
			if ret == QMessageBox.Yes:
				if AutoUpdate.updateComponent(proxy = QApplication.instance().client(), destinationPath = QApplication.instance().get('basepath'), url = url):
					ret = QMessageBox.question(None, getClientName(), "Do you want to restart now ? (Unsaved file modifications will be discarded)", QMessageBox.Yes | QMessageBox.No)
					if ret == QMessageBox.Yes:
						AutoUpdate.Restarter.restart()
		else:
			QMessageBox.information(None, getClientName(), "No new version is available on this server.")

	def updateModel(self):
		"""
		Update the data model.
		"""
		settings = QSettings()

		# We set them as current parameters
		a = self.acceptExperimentalUpdatesCheckBox.isChecked()
		settings.setValue('autoupdate/acceptExperimentalUpdates', QVariant(a))


###############################################################################
# Log viewer related settings
###############################################################################

class WLogsSettings(WSettings):
	def __init__(self, parent = None):
		WSettings.__init__(self, parent)
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

		layout.addStretch()
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

class WPluginsSettings(WSettings):
	def __init__(self, parent = None):
		WSettings.__init__(self, parent)
		self.__createWidgets()
	
	def __createWidgets(self):
		layout = QHBoxLayout()
		layout.setMargin(1)
		self.pluginsTreeView = WPluginsTreeView()
		layout.addWidget(self.pluginsTreeView)
		self.setLayout(layout)
	
	def validate(self):
		return True
	
	def updateModel(self):
		return self.pluginsTreeView.updateModel()

class WPluginsTreeView(QTreeWidget):
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

	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self.__createWidgets()
		self.__createActions()
		self.buildTree()

	def __createWidgets(self):
		self.setRootIsDecorated(False)
		self.setSortingEnabled(True)
		self.setHeaderLabels(["Name", "Type", "Active"])
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
		self.setContextMenuPolicy(Qt.DefaultContextMenu)
		self.header().setResizeMode(0, QHeaderView.Interactive)
		self.header().resizeSection(0, 200)
		self.header().setResizeMode(1, QHeaderView.ResizeToContents)
		self.header().setResizeMode(2, QHeaderView.ResizeToContents)
	
	def buildTree(self):
		self.clear()
		# Load all plugins into a listview
		for v in PluginManager.getPluginClasses():
			item = self.PluginItem(v, parent = self)
		self.sortItems(0, Qt.AscendingOrder)

	def __createActions(self):
		self.rescanAction = TestermanAction(self, "Rescan plugins", PluginManager.rescanPlugins)
		self.rescanAction.setShortcut("F5")
		self.rescanAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.rescanAction)
		self.aboutAction = TestermanAction(self, "About", self.aboutPlugin)
		self.aboutAction.setShortcut("Ctrl+Shift+A")
		self.aboutAction.setShortcutContext(Qt.WidgetShortcut)
		self.addAction(self.aboutAction)
		self.configureAction = TestermanAction(self, "Configure", self.configurePlugin)

	def rescanPlugins(self):
		PluginManager.rescanPlugins()
		self.buildTree()

	def aboutPlugin(self):
		item = self.currentItem()
		if item:
			dialog = WAboutPluginDialog(item.pluginInfo, self)
			dialog.exec_()

	def configurePlugin(self):
		item = self.currentItem()
		if item:
			if item.configurationClass:
				dialog = WPluginSettingsDialog(item.text(0), item.configurationClass, self)
				dialog.exec_()
			else:
				userInformation(self, "This plugin has no configuration dialog.")

	def onItemActivated(self, item, col):
		self.configurePlugin()

	def contextMenuEvent(self, event):
		item = self.itemAt(event.pos())
		menu = QMenu(self)
		if item:
			menu.addAction(self.configureAction)
			menu.addAction(self.aboutAction)
			menu.addSeparator()
		# In any case, general action
		menu.addAction(self.rescanAction)
		menu.popup(event.globalPos())
	
	def updateModel(self):
		# Activate/deactivate plugins
		settings = QSettings()
		root = self.invisibleRootItem()
		for i in range(0, root.childCount()):
			item = root.child(i)
			settings.setValue('plugins/activated/' + item.pluginId, QVariant(item.activated()))
	

