# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008-2013 Sebastien Lefevre and other contributors
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
# Configuration File updater/setter probe.
#
# Able to manipulate most common configuration file formats:
# .conf (shell source-able)
# .ini (windows configurable behaviour regarding comment characters, case, ...)
# .xml (using xpath)
# 
# These supports are based on plugins.
# These plugins do not actively register as probes/codecs
# but are detected by this probe automatically. 
# Constraint: only one file support per plugin.
#
# A plugin must be a Python module that defines the following attributes:
#
# SUPPORTED_CONF_FILE_FORMATS = [ 'xml' ] # list of strings
#
# getInstance() # generate an instance of an object that provides the
# following interface:
#  getValue(filename, keypath) # must returns a string
#  setValue(filename, keypath, value) # must returns a bool
#  setProperty(name, value)
#
#  get/setValue may raise an exception on error.
##

import ProbeImplementationManager



class ConfigFileProbe(ProbeImplementationManager.ProbeImplementation):
	"""
Identification and Properties
-----------------------------

Probe Type ID: ``configurationfile``

Properties:

.. csv-table::
   :header: "Name","Type","Default value","Description"

   "``plugin_properties``","dict[string] of dict","``{}``","properties to pass to sub-plugins, indexed by the format they support"

Properties for the ``ini`` plugin:

.. csv-table::
   :header: "Name","Type","Default value","Description"

   "``comments``","list of strings","``['#', ';']``","List of characters or strings that identify a comment in a .ini file"

There are no properties for the other ``xml`` and ``conf`` plugins.

Overview
--------

This probe is specialized in updating configuration files, so that you can easily integrate small configuration changes
prior to running a particular test (and rollback this change after).

In can only work with files located on the system the probe is running on (i.e. you cannot update a file remotely via this probe,
but you can still deploy your probe on a remote agent, so technically you can still update a configuration file anywhere on your
distributed SUT).

This implementation relies on probe-specific plugins (yes, nested plugins ! where this over-engineering spree will end ?)
to update the files. These plugins simply provide ``get`` and ``set`` operations for a specific key, and the way the key
is identified is plugin-specific.

Currently the following configuration file formats are supported:

* XML files (extension: ``.xml``): the key format is a XPath request, so you can change an element value or attribute.
* Shell sourceable configuration files (extension: ``.conf``): the typical key=value configuration file that
  can be read by ``sh``, using ``#`` for comments, and a flat structure (no sections).
* INI files (extension: ``.ini``): Windows-like configuration files, with sections. The key format is "section/key".
  The characters used for comments in such a file are configurable (see the ``comments`` property) so that
  it could adapt to some custom INI file formats.

The plugin to use to handle a configuration file is automatically detected based on the file extension, unless you force one
(which is convenient to support INI files named ``something.conf``).

To get the value of a key in a file (here, the value of the key name ``key`` in section ``[section]`` in the INI configuration file ``/pat/to/my/config.ini``), simply send the following message:

.. code-block: python

  configPort.send( ('get', { 'keypath': 'section/key', 'filename': '/path/to/my/config.ini' }) )

Then, expect a result message:

.. code-block: python

  configPort.receive( ('getResult', extract('myvalue', any_or_none()) )
	
	myvalue = value('myvalue')
	log("Read value for key: " + myvalue)

If the key or the configuration file was not found or not readable, the returned value is an empty string.

To set the previous key to a given value:

.. code-block: python

  configPort.send( ('set', { 'keypath': 'section/key', 'filename': '/path/to/my/config.ini', 'value': 'my value' }) )

Then, optionally expect a result message (if you don't mind if the operation succeeded, don't expect anything):

.. code-block: python

  configPort.receive( ('setResult', True )
	
Other received messages indicate a set error.

As usual, it may be convenient to embed these message-based calls into a convenience function to use in your ATSes.

Availability
~~~~~~~~~~~~

All platforms.

Dependencies
~~~~~~~~~~~~

None.

See Also
~~~~~~~~

TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the ``ConfigFileProbeType`` port type as specified below:

::

  type union Command
  {
    SetKeyCommand set,
    GetKeyCommand get,
  }
  
  type record SetKeyCommand
  {
    charstring filename,
    charstring keypath,
    charstring value,
    charstring format optional, // default: autodetect based on extension
  }
  
  type record GetKeyCommand
  {
    charstring filename,
    charstring keypath,
    charstring format optional, // default: autodetect based on extension
  }
  
  type union Result
  {
    charstring errorResult, // contains a human readable error string
    charstring getResult, // empty string if not found
    bool setResult, // True if OK, False otherwise 
  }
  
  type port ConfigFileProbeType
  {
    in Command;
    out Result
  }

Properties:
|| `plugin_properties`|| dict[string] of dict || `{}` || properties to pass to plugins, indexed by the format they support ||

Properties for the `ini` plugin:
|| `comments` || list of strings || `['#', ';']` || List of characters or strings that identify a comment in a .ini file ||
	
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self.setDefaultProperty('plugin_properties', {})
	
	def onTriMap(self):
		pass
	
	def onTriUnmap(self):
		pass
	
	def onTriSAReset(self):
		pass
	
	def onTriSend(self, message, sutAddress):
		try:
			(operation, args) = message
		except:
			raise Exception("Invalid message format")
		
		self._checkArgs(args, [ ('filename', None), ('keypath', None), ('format', '') ])
		
		format = args['format']
		if not format:
			# Autodetection attempt based on file extension
			format = args['filename'].split('.')[:-1]
		
		if operation == 'get':
			resp = self.getValue(filename = args['filename'], keypath = args['keypath'], format = format)
		elif operation == 'set':
			self._checkArgs(args, [ ('value', None) ])
			resp = self.setValue(filename = args['filename'], keypath = args['keypath'], value = args['value'], format = format)
		else:
			raise Exception("Unsupported operation (%s)" % operation)
		
		self.triEnqueueMsg(resp)

	def getValue(self, filename, keypath, format):
		plugin = self.getPluginInstance(format)
		if not plugin:
			return  ('errorResult', 'unsupported configuration file format (%s)' % format)
		try:
			ret = plugin.getValue(filename, keypath)
			if ret is None:
				ret = ''
		except Exception, e:
			return ('errorResult', str(e))
		return ('getResult', ret)
	
	def setValue(self, filename, keypath, value, format):
		plugin = self.getPluginInstance(format)
		if not plugin:
			return  ('errorResult', 'unsupported configuration file format (%s)' % format)
		try:
			ret = plugin.setValue(filename, keypath, value)
		except Exception, e:
			return ('errorResult', str(e))
		return ('setResult', ret)
	
	def getPluginInstance(self, format):
		"""
		Instanciates and configure a plugin
		"""
		plugin = getPluginInstance(format)
		if not plugin:
			return None
		for name, value in self['plugin_properties'].get(format, {}).items():
			plugin.setProperty(name, value)
		return plugin

##
# Plugin Management
##

RegisteredPlugins = {}

def registerPlugin(formats, plugin):
	if not hasattr(plugin, 'getInstance'):
		ProbeImplementationManager.getLogger().warning("ConfigFile plugin candidate for %s has no getInstance() entry point. Discarding." % format)
	else:
		for format in formats:
			RegisteredPlugins[format] = plugin
			ProbeImplementationManager.getLogger().info("ConfigFile plugin module registered for format %s" % format)

def getPluginInstance(format):
	if RegisteredPlugins.has_key(format):
		return RegisteredPlugins[format].getInstance()
	return None

import sys
import os		
def scanPlugins(paths, label):
	for path in paths:
		if not path in sys.path:
			sys.path.append(path)
		try:
			for m in os.listdir(path):
				if m.startswith('__init__') or not (os.path.isdir(path + '/' + m) or m.endswith('.py')) or m.startswith('.'):
					continue
				if m.endswith('.py'):
					m = m[:-3]
				try:
					plugin = __import__(m)
					registerPlugin(plugin.SUPPORTED_CONF_FILE_FORMATS, plugin)
				except Exception, e:
					ProbeImplementationManager.getLogger().warning("Unable to import %s %s: %s" % (m, label, str(e)))
		except Exception, e:
			ProbeImplementationManager.getLogger().warning("Unable to scan %s path for %ss: %s" % (path, label, str(e)))

# On import, scan plugins
import os.path
currentDir = os.path.normpath(os.path.realpath(os.path.dirname(sys.modules[globals()['__name__']].__file__)))
scanPlugins([ "%s/plugins" % currentDir ], 'configuration file accessor')

##
# ConfigFile probe class registration
##
ProbeImplementationManager.registerProbeImplementationClass('configurationfile', ConfigFileProbe)		

	
