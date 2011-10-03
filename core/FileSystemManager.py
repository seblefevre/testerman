# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008,2009,2010 Sebastien Lefevre and other contributors
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
# Virtual Path analyzer
################################################################################

class VirtualPath:
	def __init__(self, vpath):
		self._vtype = None
		self._vvalue = None
		self._basevalue = vpath
	
		velements = vpath.split('/')

		# non-repository paths cannot be virtual		
		if len(velements) > 1 and velements[1] != 'repository':
			return
		
		i = 0
		for element in velements:
			if element.endswith('.ats') or element.endswith('.campaign'):
				if velements[i+1:]:
					# remaining elements after the script name -> pure virtual path
					vobject = velements[i+1]
					if vobject in ['executions', 'profiles', 'revisions']:
						self._vtype = vobject
						self._vvalue = '/'.join(velements[i+2:])
						self._basevalue = '/'.join(velements[:i+1])
						return
					else:
						raise Exception('Invalid virtual path %s, unsupported virtual object %s' % (vpath, vobject))

			i += 1

	def isProfileRelated(self):
		return self._vtype == 'profiles'		
	
	def getVirtualValue(self):
		return self._vvalue

	def getBaseValue(self):
		return self._basevalue

	def isVirtual(self):
		return (self._vtype is not None)

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

	def logged(fn, *args, **kw):
		"""
		Decorator function to log function calls easily.
		"""
		def _decorator(self, *args, **kw):
			arglist = ', '.join([repr(x) for x in args])
			if kw:
				arglist += ', '.join([u'%s=%s' % x for x in kw.items()])
			desc = "%s(%s)" % (fn.__name__, arglist)
			getLogger().debug(">>> %s" % desc)
			ret = fn(self, *args, **kw)
			getLogger().debug("<<< %s: %s" % (desc, ret))
			return ret
		return _decorator
	
	
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
		getLogger().debug("notifying fs change: %s:%s %s (%s)" % (objectpath, objectname, event, applicationType))
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
		"""
		Returns the content of a file.
		vpath is supported.
		"""
		# Analyse the vpath: could be a virtual folder such as
		# associated profiles or associated executions
		vpath = VirtualPath(filename)
		baseObject = vpath.getBaseValue()

		(adjusted, backend) = FileSystemBackendManager.getBackend(baseObject)
		if not backend:
			raise Exception('No backend available to manipulate %s' % baseObject)
		
		if vpath.isProfileRelated():
			return backend.readprofile(adjusted, vpath.getVirtualValue())
		else:			
			return backend.read(adjusted, revision = None)

	def write(self, filename, content, reason = None, notify = True):
		"""
		Automatically creates the missing directories up to the file, if needed.
		vpath is supported.
		"""
		# Analyse the vpath: could be a virtual folder such as
		# associated profiles or associated executions
		vpath = VirtualPath(filename)

		if not vpath.isVirtual():
			return self._writeFile(filename, content, reason, notify)
		
		elif vpath.isProfileRelated():
			return self._writeProfile(vpath.getBaseValue(), vpath.getVirtualValue(), content, notify)
		else:
			raise Exception("Cannot write this resource (%s)" % filename)

	def _writeFile(self, filename, content, reason, notify):
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

		try:
			backend.write(adjusted, content, baseRevision = None, reason = reason)
		except Exception, e:
			getLogger().error("Unable to write %s: %s" % (filename, str(e)))
			return False

		if notify:
			if newfile:
				self._notifyFileCreated(filename)
			else:
				self._notifyFileChanged(filename) # Well, could be a new revision, too.
		return True

	def _writeProfile(self, filename, profilename, content, notify):
		resourcepath = '%s/profiles/%s' % (filename, profilename)
		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)

		newfile = False
		if not self.attributes(resourcepath):
			newfile = True
		
		print "DEBUG: new profile (%s): %s" % (resourcepath, newfile)

		try:
			backend.writeprofile(adjusted, profilename, content)
		except Exception, e:
			getLogger().error("Unable to profile %s for %s: %s" % (profilename, filename, str(e)))
			return False

		if notify:
			if newfile:
				self._notifyFileCreated(resourcepath)
			else:
				self._notifyFileChanged(resourcepath)
		return True

	@logged	
	def unlink(self, filename, reason = None, notify = True):
		"""
		Removes a file.
		vpath is supported to remove a profile.
		"""
		vpath = VirtualPath(filename)
		baseObject = vpath.getBaseValue()

		(adjusted, backend) = FileSystemBackendManager.getBackend(filename)
		if not backend:
			raise Exception('No backend available to manipulate %s' % filename)

		if vpath.isProfileRelated():
			ret = backend.unlinkprofile(adjusted, vpath.getVirtualValue())
		else:
			ret = backend.unlink(adjusted, reason)

		if ret and notify:
			self._notifyFileDeleted(filename)
		return ret

	@logged
	def getdir(self, path):
		"""
		Lists the contents of a directory.
		
		vpath is supported to list the profiles virtual folder.
		"""
		# Analyse the vpath: could be a virtual folder such as
		# associated profiles or associated executions
		vpath = VirtualPath(path)
		baseObject = vpath.getBaseValue()

		(adjusted, backend) = FileSystemBackendManager.getBackend(baseObject)
		if not backend:
			raise Exception('No backend available to manipulate %s' % baseObject)
		
		if vpath.isProfileRelated():
			dircontents = backend.getprofiles(adjusted)
		else:			
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

	@logged
	def mkdir(self, path, notify = True):
		"""
		Automatically creates all the directories to create this one.
		vpath is NOT supported.
		
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

	@logged
	def rmdir(self, path, recursive = False, notify = True):
		"""
		Removes a directory.
		vpath is NOT supported.
		
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
		"""
		Get the attributes of a file.
		vpath is supported.
		"""
		vpath = VirtualPath(filename)
		baseObject = vpath.getBaseValue()

		(adjusted, backend) = FileSystemBackendManager.getBackend(baseObject)
		if not backend:
			raise Exception('No backend available to manipulate %s' % baseObject)
		
		if vpath.isProfileRelated():
			return backend.profileattributes(adjusted, vpath.getVirtualValue())
		else:			
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
		"""
		FIXME: A profile is currently not a file...
		"""
		(adjusted, backend) = FileSystemBackendManager.getBackend(path)
		if not backend:
			raise Exception('No backend available to manipulate %s' % path)
		return backend.isfile(adjusted)
	
	def exists(self, path):
		"""
		FIXME: A profile currently does not exist with these criteria...
		"""
		return self.isdir(path) or self.isfile(path)
	
	def _copy(self, source, destination, removeAfterCopy = False, notify = True):
		"""
		Recursive copy from source (file or dir, docroot path) to destination (existing dir or file to overwrite)
		vpath is NOT supported at this level (self.copy() supports it).
		However, this function is profiles-aware and will copy script-associated profiles with the script.
		
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

			# take care of associated profiles
			profiles = self.getdir("%s/profiles" % source)
			if profiles:
				for profile in profiles:
					if profile['type'] == APPTYPE_PROFILE:
						spname = "%s/profiles/%s" % (source, profile['name'])
						dpname = "%s/profiles/%s" % (dst, profile['name'])
						getLogger().debug("Copying profile implicitly: %s to %s" % (spname, dpname))
						p = self.read(spname)
						if p is not None:
							self.write(dpname, content = p, notify = notify)
			# associated execution log files are NOT copied
				
			if removeAfterCopy:
				# will delete associated profiles, if any
				self.unlink(source, notify = notify)
			
			return True
		
		else:
			getLogger().warning("Unable to qualify source file. Not copying.")
			return False

	def _copyprofile(self, source, destination, removeAfterCopy, notify = True):
		"""
		Copy a profile - the destination may be outside a profiles virtual folder, too.
		
		destination can be a vprofiles folder, or any folder, or a fully qualified
		filename (including a vprofile).
		"""
		dvpath = VirtualPath(destination)
		dst = destination
		if self.isdir(destination):
			# The destination is a dir, so let's add a basename to get a
			# fully qualified destination name
			_, basename = os.path.split(source)
			dst = '%s/%s' % (destination, basename)

		elif dvpath.isProfileRelated():
			if not dvpath.getVirtualValue():
				# no basename provided for the dest in a /profiles/ vdir
				_, basename = os.path.split(source)
				dst = '%s/%s' % (destination, basename)
		
		p = self.read(source)
		if p is not None:
			self.write(dst, content = p, notify = notify)
		else:
			return False

		if removeAfterCopy:
			self.unlink(source)
		return True
	
	def copy(self, source, destination, notify = True):
		"""
		Copy source to destination.
		vpath is supported.
		
		TODO/FIXME: code cleanup, correct support of all cases:
		anyfile should be copiable to a vprofiles folder, not only
		vprofiles sources.
		This must be taken into account in _copy() itself.
		"""
		svpath = VirtualPath(source)
		
		if svpath.isProfileRelated():
			# copy a profile
			return self._copyprofile(source, destination, False, notify)
		else:
			return self._copy(source, destination, False, notify)

	@logged
	def move(self, source, destination, notify = True):		
		"""
		Move source to destination.
		"""
		svpath = VirtualPath(source)
		
		if svpath.isProfileRelated():
			# copy a profile
			return self._copyprofile(source, destination, True, notify)
		else:
			return self._copy(source, destination, True, notify)

	@logged
	def rename(self, source, newName):
		"""
		FIXME: support for vpath (to rename a profile)
		
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
			if self.isdir(source):
				ret = backend.renamedir(adjusted, newName)
			else:
				ret = backend.rename(adjusted, newName)
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
	
