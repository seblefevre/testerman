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
# File System Backend manager:
# - manages backends (as plugins),
# - manages mount points within the virtual file system exposed through Ws
#
##

import ConfigManager

import logging
import os
import posixpath
import sys

import ConfigParser

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.FSBManager')


################################################################################
# Backend mounter
################################################################################

# Backend instance indexed by their normalized mountpoint within the docroot.
# (starts with a /, ends with a /)
Mountpoints = {}

def mount(mountpoint, backend, prefix = '/repository/'):
	"""
	@type  mountpoint: string
	@param mountpoint: the mountpoint path within the repository/
	                   (i.e. $(docroot)/repository/).
	@type  backend: FileSystemBackend
	@param backend: the configured FileSystemBackend instance to mount
	@type  prefix: string
	@param prefix: a prefix to prefix the mountpoint.
	Normally we only mount backends within the repository.
	An administrative backend, however, is mounted as the docroot
	(using a prefix = '/').
	
	The mountpoint must be reachable from the root repository to 
	be useful i.e. the mountpoint must be a directory in the parent
	backend.
	Even if not, you can still provide a direct path to save a
	file to repository through the backend, but you won't be able
	to browse from it before doing so (since the file save will
	create the required directory tree to reach the mountpoint)
	
	@rtype: bool
	@returns: True if the mount successes.
	"""
	# Clean up and normalize the mountpoint relative to the docroot
	# Notice the trailing /
	mountpoint = "%s/" % posixpath.normpath("%s%s" % (prefix, mountpoint))
	
	if Mountpoints.has_key(mountpoint):
		# does not allow mount override
		getLogger().warning("Not mounting %s with %s: mount point already mounted with %s" % (mountpoint, str(backend), str(Mountpoints[mountpoint])))
		return False
	else:
		Mountpoints[mountpoint] = backend
		getLogger().info("%s successfully mounted with %s" % (mountpoint, str(backend)))
		return True

def getBackend(path):
	"""
	Returns the backend used to access path, and the path of path relative to the backend mountpoint.
	
	@type  path: string
	@param path: the path of something to access relative to the docroot (including a leading /)
	
	@rtype: tuple (string, backend)
	"""
	# Clean up and normalize the path relative to the docroot
	path = posixpath.normpath("/%s" % (path))
	
	# Now, look for the longuest (best) match within the existing mountpoints
	mountpoints = Mountpoints.keys()
	mountpoints.sort()
	mountpoints.reverse() # So that the longuest mountpoints is the first one
	
	# Let's find the first match
	for mountpoint in mountpoints:
		# mountpoint always ends with a /, avoiding incorrect matches in case
		# where path = "/repository/my/filename"
		# and mountpoint = "/repository/my/file"
		if path.startswith(mountpoint):
			# the adjusted path is then trivial
			# - still starts with a /
			adjusted = "/%s" % path[len(mountpoint):]
			backend = Mountpoints[mountpoint]
			getLogger().debug('%s: backend %s, adjusted name %s' % (path, str(backend), adjusted))
			return (adjusted, backend)
	
	# No match
	return (None, None)

def mountRoot():
	"""
	Mount the root file system.
	Contains special error handling.
	"""
	rootBackendType = 'local'
	backend = getFileSystemBackendInstance(rootBackendType)
	if not backend:
		raise Exception("Unable to find the backend type %s for mouting root file system." % rootBackendType)
	# Set the backend properties
	backend.setProperty('basepath', ConfigManager.get('testerman.document_root'))
	# Initialize it
	try:
		if not backend.initialize():
			raise Exception('initialize() returned False')
	except Exception, e:
		raise Exception("Unable to initialize the root backend %s: %s" % (str(backend), str(e)))
	# Finally mount it
	if not mount('/', backend, prefix = ''):
		raise Exception("Unable to mount root file system with %s" % str(backend))

def mountAll():
	"""
	Mounts all configured File systems according to the associated configuration file.
	Additionally, mount the root FS using a local filesystem configured using the
	testerman.docroot as a basepath.
	"""
	try:
		mountRoot()
	except Exception, e:
		getLogger().critical("Unable to mount the root file system: %s" % (str(e)))
		raise(e)


	# List of (mountpoint, backend type, properties dict) to mount
	mounts = []
	
	# Read other FS configurations from a file
	confFilename = "%s/backends.ini" % ConfigManager.instance().get("testerman.configuration_path")
	try:
		c = ConfigParser.ConfigParser()
		c.read([ confFilename ])
		# One backend per section
		# The section name is ignored and just a label for the admin
		for section in c.sections():
			backendType = None
			mountpoint = None
			properties = {}
			for option in c.options(section):
				# Special keys: the mountpoint, and the backend type
				if option == "backend":
					backendType = c.get(section, option)
				elif option == "mountpoint":
					mountpoint = c.get(section, option)
				else:
					properties[option] = c.get(section, option)
			if backendType and mountpoint:
				mounts.append( (mountpoint, backendType, properties) )
			else:
				getLogger().warning("Invalid backend definition '%s' in configuration file: missing 'backend' or 'mountpoint' keys" % section)
	except Exception, e:
		getLogger().warning("Unable to load backend configuration file %s: %s" % (confFilename, str(e)))

	# Now proceed to actual mounts
	for (mountpoint, backendType, properties) in mounts:
		backend = getFileSystemBackendInstance(backendType)
		if not backend:
			getLogger().warning("Backend type %s is not registered. Not mounting %s with it." % (backendType, mountpoint))
		if backend:
			# Set the backend properties
			for key, val in properties.items():
				backend.setProperty(key, val)

			# Initialize it			
			initialized = False
			try:
				initialized = backend.initialize()
			except Exception, e:
				getLogger().warning("Exception while initializing backend %s: %s" % (str(backend), str(e)))
				initialized = False
			if not initialized:
				getLogger().warning("Unable to initialize %s to mount %s" % (str(backend), mountpoint))
				continue		
			
			# Attach it to the mount point
			if not mount(mountpoint, backend):
				getLogger().warning("Unable to mount %s with %s" % (mountpoint, str(backend)))
				continue
			# OK
			getLogger().info("%s mounted with %s" % (mountpoint, str(backend)))
	
	# Normally we should issue a critical error if we are not able to mount the root backend...


################################################################################
# File System Backends (as plugins) management
################################################################################

def scanPlugins(paths, label):
	for path in paths:
		if not path in sys.path:
			sys.path.append(path)
	for path in paths:
		try:
			for m in os.listdir(path):
				if m.startswith('__init__') or not (os.path.isdir(path + '/' + m) or m.endswith('.py')) or m.startswith('.'):
					continue
				if m.endswith('.py'):
					m = m[:-3]
				try:
					__import__(m)
				except Exception, e:
					getLogger().warning("Unable to import %s %s: %s" % (m, label, str(e)))
		except Exception, e:
			getLogger().warning("Unable to scan %s path for %ss: %s" % (path, label, str(e)))

def scanFileSystemBackends():
	"""
	Convenience function.
	"""
	paths = [ ConfigManager.get("testerman.server_path") + "/backends" ]
	scanPlugins(paths, label = "backend")

FileSystemBackendClasses = {}

def registerFileSystemBackendClass(type_, class_):
	if not FileSystemBackendClasses.has_key(type_):
		FileSystemBackendClasses[type_] = class_
		getLogger().info("FileSystemBackend %s registered" % type_)
		return True
	else:
		getLogger().warning("Unable to register FileSystemBackend: type %s already registered" % type_)
		return False
	
def getFileSystemBackendInstance(type_):
	cls = FileSystemBackendClasses.get(type_, None)
	if cls:
		ret = cls()
		ret._setType(type_)
		return ret
	else:
		return None
