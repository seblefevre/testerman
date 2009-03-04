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
# Interface/Base class to create plugins
#
##

from PyQt4.Qt import *


TYPE_CODE_WRITER = "code-writer"
TYPE_REPORT_VIEW = "report-view"

###############################################################################
# Base plugin configuration widget. The same for all plugin types.
###############################################################################

class WPluginConfiguration(QWidget):
	"""
	Plugin configuration widget.
	
	This widget is automatically embedded within a dialog box when
	the plugin configuration is invoked from QtTesterman's interface.

	You should implement such a class if you need specific configuration.
	This configuration should then be checked through checkConfiguration()
	and saved to a persistent storage either through the application QSettings() 
	in a dedicated subtree (plugins/PLUGIN_ID/ where PLUGIN_ID is your Plugin's UUID),
	either to any files you can retrieve the filenames out of the blue (i.e. not relying
	on QtTesterman's working or current directories).

	The saved configuration should be reloaded to be displayed in displayConfiguration.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
	
	def displayConfiguration(self):
		"""
		Load and display current configuration settings.
		
		You are invited to use QSettings() and "plugins/%PLUGIN_ID/" as yor configuration tree root
		in the settings manager.
		
		@rtype: None
		@returns: None
		"""
		pass
	
	def saveConfiguration(self):
		"""
		Save currently displayed/edited configuration settings.
		
		You are invited to use QSettings() and "plugins/%PLUGIN_ID/" as yor configuration tree root
		in the settings manager.
		
		Always called *after* checkConfiguration().

		@rtype: bool
		@returns: True is the configuration was correctly saved, False in case of an error.
		"""
		return True

	def checkConfiguration(self):
		"""
		Check the currently displayed/edited configuration settings.
		In case of an error (invalid value, etc), you may display a warning dialog indicating the error.
		
		@rtype: bool
		@returns: True is the configuration is correct (and can be saved), False in case of an error.
		"""
		return True


###############################################################################
# ReportView: ideal to develop log exporters
###############################################################################

class WReportView(QWidget):
	pluginType = TYPE_REPORT_VIEW
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

	def clearLog(self):
		"""
		Called when logs are cleared.

		@rtype: None
		@returns: None
		"""
		pass
	
	def onEvent(self, domElement):
		"""
		Called whenever a new log element has been parsed/received.
		
		@type  domElement: QDomElement
		@param domElement: the new log element, already parsed.
		
		@rtype: None
		@returns: None
		"""
		pass
	
	def displayLog(self):
		"""
		Called to actually display the log. May do nothing if
		you implemented a event-based display

		@rtype: None
		@returns: None
		"""
	

###############################################################################
# CodeWriter: ideal to develop code snippet managers, resource importers, 
# code generators, ...
###############################################################################

class CodeWriter(QObject):
	pluginType = TYPE_CODE_WRITER
	def __init__(self, parent = None):
		QObject.__init__(self, parent)

	def activate(self):
		"""
		Called to activate the plugin.

		May display a specific window to set things.
		@rtype: unicode, or None
		@returns: generated code, or None if no code has been generated.
		"""

	def isDocumentTypeSupported(self, documentType):
		"""
		Called to filter plugins list according to the document/model type
		we display them.
		documentType is a DocumentModels.TYPE_*

		By default, all types are supported.
		
		@type  documentType: DocumentModels.TYPE_*
		@param documentType: the document type to announce support for

		@rtype: bool
		@returns: True if code generation for document type is supported, False otherwise.
		"""
		return True

	
