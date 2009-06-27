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

import EventManager
import FileSystemBackendManager
import FileSystemBackend
import TestermanMessages as Messages
import Versions

import logging
import os


# Application-type for returned objects in dir lists (sort of mime-types)
APPTYPE_ATS = 'ats'
APPTYPE_CAMPAIGN = 'campaign'
APPTYPE_MODULE = 'module'
APPTYPE_LOG = 'log'
APPTYPE_PROFILE = 'profile'
APPTYPE_PACKAGE_METADATA = 'package-metadata'
APPTYPE_PACKAGE = 'package'
APPTYPE_DIR = 'directory'

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
	
	TODO:
	- name/path validation:
	  '/' is the character to use for path elements.
	  Each element should match the following regexp: [a-zA-Z0-9_.\(\)\[\]#-]
		
	
	The following operations are non-read only and may emit some 
	Xc notifications:
	- mkdir
	- write
	- rmdir
	- unlink
	"""
	def _notify(self, path, backendType, event):
		"""
		We notify the filesystem:/directory URI subscribers
		whenever a new entry is created/deleted or a file in this dir is modified.
		
		WARNING/FIXME: the application type may not be correctly
		identified in all case, especially when creating a package forlder,
		as the package.xml is created after the directory...
		"""
		if path.endswith('/'):
			path = path[:-1]
		objectpath, objectname = os.path.split(path)
		if not objectpath:
			objectpath = '/'
		applicationType = self.getApplicationType(objectname, objectpath, backendType)
		if applicationType:
			uri = 'filesystem:%s' % objectpath
			notification = Messages.Notification("FILE-EVENT", uri, "Xc", Versions.getXcVersion())
			notification.setHeader('File-Type', applicationType)
			notification.setHeader('File-Path', objectpath)
			notification.setHeader('File-Name', objectname)
			notification.setHeader('Reason', event)
			EventManager.instance().dispatchNotification(notification)
	
	def _notifyDirCreated(self, path):
		return self._notify(path, 'directory', 'created')
	
	def _notifyDirDeleted(self, path):
		return self._notify(path, 'directory', 'deleted')
	
	def _notifyFileCreated(self, filename):
		return self._notify(filename, 'file', 'created')
	
	def _notifyFileDeleted(self, filename):
		return self._notify(filename, 'file', 'deleted')
	
	def _notifyFileChanged(self, filename):
		pass

	def _notifyFileRenamed(self, filename, newName):
		"""
		Filename is the path+name to the previous name, before renaming.
		"""
		if filename.endswith('/'):
			filename = filename[:-1]
		objectpath, objectname = os.path.split(filename)
		if not objectpath:
			objectpath = '/'
		applicationType = self.getApplicationType(newName, objectpath, 'file')
		if applicationType:
			uri = 'filesystem:%s' % objectpath
			notification = Messages.Notification("FILE-EVENT", uri, "Xc", Versions.getXcVersion())
			notification.setHeader('File-Type', applicationType)
			notification.setHeader('File-Path', objectpath)
			notification.setHeader('File-Name', objectname)
			notification.setHeader('Reason', 'renamed')
			notification.setHeader('File-New-Name', newName)
			EventManager.instance().dispatchNotification(notification)

	def getApplicationType(self, name, path, backendType):
		"""
		Identify the application type of a file path/name,
		whose backend type is backendType ('directory' or 'file')
		"""
		applicationType = None
		if backendType == 'file':
			if name.endswith('.ats'):
				applicationType = APPTYPE_ATS
			elif name.endswith('.campaign'):
				applicationType = APPTYPE_CAMPAIGN
			elif name.endswith('.py') and name != '__init__.py':
				applicationType = APPTYPE_MODULE
			elif name.endswith('.log'):
				applicationType = APPTYPE_LOG
			elif name.endswith('.profile'):
				applicationType = APPTYPE_PROFILE
			elif name == 'package.xml':
				applicationType = APPTYPE_PACKAGE_METADATA
		elif backendType == 'directory':
			# Could be a plain directory, 
			# or a package directory,
			package = False
			try:
				package = self.isfile('%s/%s/package.xml' % (path, name))
			except:
				package = False
			if package:
				applicationType = APPTYPE_PACKAGE
			else:
				applicationType = APPTYPE_DIR
		return applicationType
	
	def read(self, filename):
		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)
		return backend.read(adjusted, revision = None)
	
	def write(self, filename, content, reason = None, notify = True):
		"""
		Automatically creates the missing directories up to the file, if needed.
		"""
		path = os.path.split(filename)[0]
		res = self.mkdir(path, notify = notify)
		if not res:
			raise Exception('Unable to create directory %s to write %s' % (path, filename))

		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)

		newfile = False
		if not self.isfile(filename):
			newfile = True

		ret = backend.write(adjusted, content, baseRevision = None, reason = reason)
		if notify:
			if newfile:
				self._notifyFileCreated(filename)
			else:
				self._notifyFileChanged(filename) # Well, could be a new revision, too.
		return ret
	
	def unlink(self, filename, reason = None, notify = True):
		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)
		ret = backend.unlink(adjusted, reason)
		if ret and notify:
			self._notifyFileDeleted(filename)
		return ret

	def getdir(self, path):
		(adjusted, backend) = FileSystemBackendManager.getBackend(path)
		if not backend:
			raise Exception('No backend available to manipulate %s' % path)
		dircontents = backend.getdir(adjusted)
		if dircontents is None:
			return None
		
		# Now converts the backend-level object type to application-level type
		res = []
		for entry in dircontents:
			name = entry['name']
			applicationType = self.getApplicationType(name, path, entry['type'])
			if applicationType:			
				res.append({'name': name, 'type': applicationType})
		return res

	def mkdir(self, path, notify = True):
		"""
		Automatically creates all the directories to create this one.
		
		@rtype: bool
		@returns: True if the directory was created or was already created
		(i.e. available). False otherwise.
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

				if backend.isfile(adjusted):
					return False # Cannot create
				elif backend.isdir(adjusted):
					# nothing to do at this level
					continue
				else:
					res = backend.mkdir(adjusted)
					if not res:
						return False
					if notify:
						self._notifyDirCreated(p)

		return True

	def rmdir(self, path, recursive = False, notify = True):
		"""
		Removes a directory.
		If recursive is set to True, which is DANGEROUS,
		will remove all existing files and directories before deleting
		the directory.
		
		TODO: define a strategy to follow mount points or not...
		For now, we do not follow them and only deletes entities in the same backend
		as the deleted dir.

		@rtype: bool
		@returns: True if the directory was removed or was already removed
		(i.e. deleted). False otherwise.
		"""
		(adjusted, backend) = FileSystemBackendManager.getBackend(path)
		if not backend:
			raise Exception('No backend available to manipulate %s' % path)
		if backend.isfile(adjusted):
			raise Exception("Attempting to delete directory '%s', which is a file" % path)
		if not backend.isdir(adjusted):
			return True # already removed

		if not recursive:
			ret = backend.rmdir(adjusted)
		else:
			getLogger().info("Deleting directory '%s' recursively, adjusted to '%s' for backend '%s'" % (path, adjusted, backend))
			ret = self._rmdir(adjusted, backend, notify = True)
		if ret and notify:
			self._notifyDirDeleted(path)
		return ret
	
	def _rmdir(self, adjustedPath, currentBackend, notify = True):
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
						currentBackend.unlink(name, notify = notify)
					except Exception, e:
						getLogger().warning("Unable to recursively delete adjusted file '%s' for backend '%s': %s" % (name, currentBackend, str(e)))
				elif type_ == 'directory':
					# FIXME: here we should compute the docroot name of the file
					# so that we can recompute its backend again
					self._rmdir(name, currentBackend, notify = notify)
		ret = currentBackend.rmdir(adjustedPath)
		return ret

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
		
	def isdir(self, path):
		(adjusted, backend) = FileSystemBackendManager.getBackend(path)
		if not backend:
			raise Exception('No backend available to manipulate %s' % path)
		return backend.isdir(adjusted)

	def isfile(self, path):
		(adjusted, backend) = FileSystemBackendManager.getBackend(path)
		if not backend:
			raise Exception('No backend available to manipulate %s' % path)
		return backend.isfile(adjusted)
	
	def exists(self, path):
		return self.isdir(path) or self.isfile(path)
	
	def _copy(self, source, destination, removeAfterCopy = False, notify = True):
		"""
		Recursive copy from source (file or dir, docroot path) to destination (existing dir or file to overwrite)
		
		The usual rules apply:
		- if source is a directory, destination must be an existing directory
		  or must not exist (cannot overwrite a file with a dir)
		- if source is a file, destination must be an existing directory
		  or a new file
		"""
		getLogger().debug("Copying %s to %s, remove after copy: %s" % (source, destination, removeAfterCopy))
		if self.isdir(source):
			getLogger().debug("Copying a directory")
			# We copy a directory
			if self.isdir(destination):
				# Copy dir to an existing dir - create a new dir into this dir
				_, basename = os.path.split(source)
				dst = '%s/%s' % (destination, basename)
			elif not self.isfile(destination):
				# Create the target directory directly
				dst = destination
			else:
				# This is a file
				raise Exception('Cannot copy directory %s to %s, which is a file' % (source, destination))

			getLogger().debug("Copying a directory to adjusted destination %s" % dst)
			# Create the target directory
			self.mkdir(dst, notify = notify)
			getLogger().debug("New target directory created")
			
			# Now we recursively copy each file
			entries = self.getdir(source)
			if entries:
				for entry in entries:
					name = entry['name']
					# Reconstruct the docroot path for source
					src = '%s/%s' % (source, name)
					# Call recursively.
					self._copy(src, dst, removeAfterCopy, notify = notify)
			
			if removeAfterCopy:
				self.rmdir(source, True, notify = notify)
			
			return True

		elif self.isfile(source):
			getLogger().debug("Copying a file")
			# We copy a file
			if self.isdir(destination):
				getLogger().debug("Copying a file to a directory")
				# Copy the file into the directory
				_, basename = os.path.split(source)
				dst = '%s/%s' % (destination, basename)
			elif self.isfile(destination):
				# Copy the file to another file (overwrite)
				dst = destination
			else:
				# Create a new file
				dst = destination

			getLogger().debug("Copying file to %s" % dst)
			
			content = self.read(source)
			self.write(dst, content, notify = notify)
			if removeAfterCopy:
				self.unlink(source, notify = notify)
			
			return True
		
		else:
			getLogger().warning("Unable to qualify source file. Not copying.")
			return False
	
	def copy(self, source, destination, notify = True):
		"""
		Copy source to destination.
		"""
		return self._copy(source, destination, False, notify)

	def move(self, source, destination, notify = True):		
		"""
		Move source to destination.
		"""
		return self._copy(source, destination, True, notify)

	def rename(self, source, newName):
		"""
		Constraints on name:
		only [a-zA-Z0-9_.\(\)\[\]#-]
		
		@type  source: string
		@param source: docroot-path of the object to rename
		@type  newName: string
		@param newName: the new (base)name of the object in its current
		                directory.
		
		@rtype: bool
		@returns: True if renamed, False otherwise (typically because
		          the destination already exists)
		"""
		(adjusted, backend) = FileSystemBackendManager.getBackend(source)
		if not backend:
			raise Exception('No backend available to manipulate %s' % source)

		destination = '%s/%s' % (os.path.split(source)[0], newName)
		if self.exists(destination):
			return False
		else:
			ret = self.move(source, destination, False)
			if ret:
				self._notifyFileRenamed(source, newName)
			return ret

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
	
