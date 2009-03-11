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
# File System Management.
#
# File accessors, writers, etc, through plugable backends.
# Whenever you need to read/write a file in the repository, 
# from a client (through the Ws) or from the server, you
# should access it through this module to ensure correct
# virtual file system traversal
###

import FileSystemBackendManager
import FileSystemBackend

import logging
import os

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.FS')


################################################################################
# The manager
################################################################################

class FileSystemManager:
	"""
	Acts as a proxy/dispatcher to forward file system requests
	to the proper backend.
	
	Transforms a virtual file url that may include some decorations (revisions ?)
	to something valid for the backend.
	"""
	
	def read(self, filename):
		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)
		return backend.read(adjusted, revision = None)
	
	def write(self, filename, content, reason = None):
		"""
		Automatically creates the missing directories up to the file, if needed.
		"""
		path = os.path.split(filename)[0]
		res = self.mkdir(path)
		if not res:
			raise Exception('Unable to create directory %s to write %s' % (path, filename))

		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)
		return backend.write(adjusted, content, baseRevision = None, reason = reason)
	
	def unlink(self, filename, reason = None):
		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)
		return backend.unlink(adjusted, reason)

	def getdir(self, path):
		(adjusted, backend) = FileSystemBackendManager.getBackend(path)
		if not backend:
			raise Exception('No backend available to manipulate %s' % path)
		return backend.getdir(adjusted)

	def mkdir(self, path):
		"""
		Automatically creates all the directories to create this one
		"""
		paths = os.path.normpath(path).split('/')
		previousPath = ''
		for p in paths:
			if p:
				p = '%s/%s' % (previousPath, p)
				previousPath = p

				(adjusted, backend) = FileSystemBackendManager.getBackend(p)
				if not backend:
					raise Exception('No backend available to manipulate %s (creating %s)' % (path, p))
				res = backend.mkdir(adjusted)
				if not res:
					return False

		return True

	def rmdir(self, path, recursive = False):
		"""
		Removes a directory.
		If recursive is set to True, which is DANGEROUS,
		will remove all existing files and directories before deleting
		the directory.
		
		TODO: define a strategy to follow mount points or not...
		For now, we do not follow them and only deletes entities in the same backend
		as the deleted dir.
		"""
		(adjusted, backend) = FileSystemBackendManager.getBackend(path)
		if not backend:
			raise Exception('No backend available to manipulate %s' % path)
		if not recursive:
			return backend.rmdir(adjusted)
		else:
			getLogger().info("Deleting directory '%s' recursively, adjusted to '%s' for backend '%s'" % (path, adjusted, backend))
			self._rmdir(adjusted, backend)
	
	def _rmdir(self, adjustedPath, currentBackend):
		"""
		Recursively called:
		- scan the adjustedPath dir from currentBackend,
		- call unlink or _rmdir on each entities in it. I.e. we do not try to switch backends.
		"""
		entries = currentBackend.getdir(adjustedPath)
		if entries:
			for entry in entries:
				# The name relative to the backend
				name = '%s/%s' % (adjustedPath, entry['name'])
				type_ = entry['type']
				if type_ == 'file':
					try:
						currentBackend.unlink(name)
					except Exception, e:
						getLogger().warning("Unable to recursively delete adjusted file '%s' for backend '%s': %s" % (name, backend, str(e)))
				elif type_ == 'directory':
					self._rmdir(name, currentBackend)
		return currentBackend.rmdir(adjustedPath)

	def attributes(self, filename):
		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)
		return backend.attributes(adjusted, revision = None)

	def revisions(self, filename):
		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)
		return backend.revisions(adjusted, baseRevision = None, scope = FileSystemBackend.FileSystemBackend.SCOPE_LOCAL)
		
	


################################################################################
# Main
################################################################################

TheFileSystemManager = None

def instance():
	return TheFileSystemManager

def initialize():
	global TheFileSystemManager
	TheFileSystemManager = FileSystemManager()

	# Load available backends
	FileSystemBackendManager.scanFileSystemBackends()
	# Mount everything according to the configuration file, if any
	FileSystemBackendManager.mountAll()

def finalize():
	pass
	
