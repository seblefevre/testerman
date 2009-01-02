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
# -*- coding: utf-8 -*-
# A FileSystemBackend implementation for local files management.
# 
# Also provides a basic, non-optimized revision management system, 
# prefixing filenames with @<rev>
# samples/file.ats
# samples/file.ats@1.1
# samples/file.ats@1.2
# samples/file.ats@1.1.1
#
##

import FileSystemBackend
import FileSystemBackendManager

import logging
import os

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.FSB.Local')


class LocalBackend(FileSystemBackend.FileSystemBackend):
	"""
	Properties:
	- basepath: the file basepath which files are looked from.
	- excluded: a space separated of patterns to exclude from dir listing
	"""
	def initialize(self):
		# Exclusion list.
		# Something based on a glob pattern should be better,
		# so that the user can configure in the backends.ini file something like
		# excluded = *.pyc .svn CVS
		# that generated an _excluded_files to [ '*.pyc', '.svn', 'CVS' ], ...
		
		self._excludedPatterns = filter(lambda x: x, self.getProperty('excluded', '.svn CVS').split(' '))

		# Check that the base path actually exists		
		if not os.path.isdir(self['basepath']):
			return False
			
		return True
	
	def _realpath(self, path):
		"""
		Compute the local path of a filename.
		filename is relative to the mountpoint.
		
		Returns None if we compute a filename/path which is outside
		the basepath.
		"""
		path = os.path.realpath("%s/%s" % (self['basepath'], path))
		if not path.startswith(self['basepath']):
			getLogger().warning("Attempted to handle a path that is not under basepath (%s). Ignoring." % path)
			return None
		else:
			return path
	
	def read(self, filename, revision = None):
		filename = self._realpath(filename)
		if not filename: 
			return None
		
		try:
			f = open(filename)
			content = f.read()
			f.close()
			return content
		except Exception, e:
			getLogger().warning("Unable to read file %s: %s" % (filename, str(e)))
			return None
	
	def write(self, filename, content, baseRevision = None, reason = None):
		filename = self._realpath(filename)
		if not filename: 
			raise Exception('Invalid file: not in base path')

		try:
			f = open(filename, 'w')
			f.write(content)
			f.close()
			return None # No new revision created.
		except Exception, e:
			getLogger().warning("Unable to write content to %s: %s" % (filename, str(e)))
			raise(e)

	def unlink(self, filename, reason = None):
		filename = self._realpath(filename)
		if not filename: 
			return False

		try:
			os.remove(filename)
			return True
		except Exception, e:
			getLogger().warning("Unable to unlink %s: %s" % (filename, str(e)))
		return False

	def getdir(self, path):
		path = self._realpath(path)
		if not path: 
			return None

		try:
			entries = os.listdir(path)
			ret = []
			for entry in entries:
				if os.path.isfile("%s/%s" % (path, entry)):
					ret.append({'name': entry, 'type': 'file'})
				elif os.path.isdir("%s/%s" % (path, entry)) and not entry in self._excludedPatterns:
					ret.append({'name': entry, 'type': 'directory'})
			return ret
		except Exception, e:
			getLogger().warning("Unable to list directory %s: %s" % (path, str(e)))
		return None

	def mkdir(self, path):
		path = self._realpath(path)
		if not path: 
			return False
		
		if os.stat(path):
			if os.path.isdir(path):
				return True
			else:
				return False # And won't be able to create it...

		try:
			os.makedirs(path, 0755)
		except:
			# already exists only ?...
			pass
		return True
	
	def rmdir(self, path):
		path = self._realpath(path)
		if not path: 
			return False

		try:
			if not os.path.isdir(path):
				return False
			else:
				os.rmdir(path)
				return True
		except Exception, e:
			getLogger().warning("Unable to rmdir %s: %s" % (path, str(e)))
		return False

	def attributes(self, filename, revision = None):
		filename = self._realpath(filename)
		if not filename: 
			return None

		try:
			s = os.stat(filename)
			a = FileSystemBackend.Attributes()
			a.mtime = s.st_ctime
			a.size = s.st_size
			return a
		except Exception, e:
			getLogger().warning("Unable to get file attributes for %s: %s" % (filename, str(e)))			
		return None
	
	def revisions(self, filename, baseRevision, scope):
		filename = self._realpath(filename)
		if not filename: 
			return None
		
		# Not implemented yet
		return None
		
		

FileSystemBackendManager.registerFileSystemBackendClass("local", LocalBackend)
