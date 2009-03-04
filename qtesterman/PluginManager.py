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
# An interface to qtesterman plugins.
#
# Provides everything to instantiate and register plugin classes.
#
##

from PyQt4.Qt import *

import sys
import os
import os.path

from Base import *


###############################################################################
# Plugin registrations
###############################################################################

PluginClasses = {}

def registerPluginClass(label, pluginId, pluginClass, configurationClass = None, description = None, version = None, author = None):
	"""
	@type pluginId: string
	@type pluginClass: a Plugin-based class
	@type description: unicode
	@type version: unicode
	@type author: unicode
	"""
	global PluginClasses
	try:
		if not PluginClasses.has_key(pluginId):
			PluginClasses[pluginId] = { "type": pluginClass.pluginType, 
				"label": label, "plugin-id": unicode(pluginId), "class": pluginClass, 
				"configuration-class": configurationClass, "description": "", "version": "unknown", "author": "unknown"
				}
			if description: PluginClasses[pluginId]["description"] = unicode(description)
			if version: PluginClasses[pluginId]["version"] = unicode(version)
			if author: PluginClasses[pluginId]["author"] = unicode(author)
			log("Plugin %s '%s' {%s} registered" % (pluginClass.pluginType, label, pluginId))
			return True
		else:
			log("WARNING: unable to register Plugin '%s' {%s}: a plugin with the same ID has already been registered" % (label, pluginId))
			return False
	except Exception, e:
		log("WARNING: unable to register a plugin: " + unicode(e))
	return Flase


###############################################################################
# Plugin Manager "private" functions
###############################################################################

def rescanPlugins():
	log("Rescanning plugins...")
#	global PluginClasses
#	PluginClasses = {}
#	# We also need to "unimport" existing plugins
	scanPlugins()

def scanPlugins():
	"""
	Attempt to load plugins fromthe plugins directory.
	"""
	# Get the absolute plugin path, regarless from where qtesterman was called.
	# We assume that this PluginManager module is in the qtesterman dir.
	qtestermanpath = QApplication.instance().get('qtestermanpath')
	path = qtestermanpath + "/plugins"
	# We also make sure that plugins can access to basic qtesterman modules, regardless of the
	# current working dir and the way we invoked qtesterman.py
	sys.path.append(qtestermanpath)

	log("Scanning plugins directory (%s)..." % path)

	try:
#		import plugins
		for m in os.listdir(path):
			if m == '__init__.py' or not (os.path.isdir(path + '/' + m) or m.endswith('.py')):
				continue
			if m.endswith('.py'):
				m = m[:-3]
			try:
				log("Trying to import plugin %s..." % m)
				__import__("plugins." + m)
				log("%s analyzed" % m)

			except Exception, e:
				log("Unable to import plugin %s: %s" % (m, str(e)))
	except Exception, e:
		log("Unable to scan for plugins: " + str(e))

###############################################################################
# Plugin Manager "general" functions
###############################################################################

def getPluginClass(pluginId):
	"""
	Returns a dict of label, plugin-id, class, configuration-class, type, activated (True/False)
	type is filtered according to pluginType.
	"""
	if PluginClasses.has_key(pluginId):
		ret = PluginClasses[pluginId]
		# Add	activation status
		settings = QSettings()
		ret['activated'] = settings.value('plugins/activated/' + ret['plugin-id'], QVariant(True)).toBool()
		return ret
	return None

def getPluginClasses(pluginType = None):
	"""
	Returns a list of dict of label, plugin-id, class, configuration-class, type, activated (True/False)
	type is filtered according to pluginType.

	@type  pluginType: string
	@param pluginType: the type of plugins to return. None to return all types.
	"""
	ret = PluginClasses.values()
	if pluginType:
		ret = filter(lambda x: x['type'] == pluginType, ret)

	# Add	activation status
	settings = QSettings()
	for p in ret:
		p['activated'] = settings.value('plugins/activated/' + p['plugin-id'], QVariant(True)).toBool()
	
	ret.sort()
	return ret
