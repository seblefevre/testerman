# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2013 Sebastien Lefevre and other contributors
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
# A FileSystemBackend implementation that use a SVN repository
# to store versioned files.
#
# Relies on pysvn library.
#
# Files are locally managed into a working dir.
# Write operations trigger SVN actions.
##

import FileSystemBackend
import FileSystemBackendManager

import pysvn

import glob
import logging
import os
import shutil
import time

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.FSB.Svn')


def fileExists(path):
	try:
		os.stat(path)
		return True
	except:
		return False

class SvnBackend(FileSystemBackend.FileSystemBackend):
	"""
	Properties:

		- ``working_dir``: the working directory the SVN repo is initially checked out.
		  You need to do a first checkout in this folder and accept to store login/password for remote access.
		  This is typically a checkout of a local svn repo, as a remote repo may add a sensible overhead whenever
		  a user saves a file via the Testerman interface.
	
	Typical use:
	
		1. Create a new repo somewhere::
		
			svnadmin create /path/to/a/svn/repo
			
		2. Checkout the repo in a working dir:
		
			mkdir -p /home/testerman/backends/svn
			cd /home/testerman/backends/svn
			svn co file:///path/to/a/svn/repo
		
		3. Configure Testerman's ``backends.ini``:
		
			[svnsample]
			backend = svn
			mountpoint = /svnfolder
			working_dir = /home/testerman/backends/svn
		
		4. Restart the Testerman server:
		
			bin/testerman-admin restart server
		
	From QTesterman, create a folder named "svnfolder" (the name of your mountpoint) in the Testerman repository.
	Now, everything put below this folder will be versioned via the SVN backend and stored in your ``working_dir`` (before
	being pushed to the source SVN repo).
	
	Note: revisions in the SVN repo will be created with the username that was used for the initial checkout.
	
	This is a "one way" backend: if you make changes to the SVN repo, they won't be checked out automatically
	into the ``working_dir`` before being presented to Testerman users.
	
	"""
	def logged(fn, *args, **kw):
		"""
		Decorator function to log function calls easily.
		"""
		def _decorator(self, *args, **kw):
			arglist = ', '.join([repr(x) for x in args])
			if kw:
				arglist += ', ' + ', '.join([u'%s=%s' % x for x in kw.items()])
			desc = "%s(%s)" % (fn.__name__, arglist)
			getLogger().debug(":: %s" % desc)
			return fn(self, *args, **kw)
		return _decorator

	def __init__(self):
		FileSystemBackend.FileSystemBackend.__init__(self)
		# Some default properties
		self.setProperty('excluded', '.svn')

		# Mandatory properties (defined here to serve as documentation)
		self.setProperty('working_dir', None)

	
	def initialize(self):
		# Exclusion list.
		# Something based on a glob pattern should be better,
		# so that the user can configure in the backends.ini file something like
		# excluded = *.pyc .svn CVS
		# that generated an _excluded_files to [ '*.pyc', '.svn', 'CVS' ], ...
		self._excludedPatterns = filter(lambda x: x, self['excluded'].split(' '))

		self._workingDir = self['working_dir']
			
		return True
	
	def _realpath(self, path):
		"""
		Compute the local path of a filename.
		filename is relative to the mountpoint.
		
		Returns None if we compute a filename/path which is outside
		the basepath.
		"""
		path = os.path.realpath("%s/%s" % (self['working_dir'], path))
		if not path.startswith(self['working_dir']):
			getLogger().warning("Attempted to handle a path that is not under SVN working_dir (%s). Ignoring." % path)
			return None
		else:
			return path
	
	def read(self, filename, revision = None):
		if filename.startswith('/'):
			filename = filename[1:]
		
		localpath = filename

		filename = self._realpath(filename)
		if not filename: 
			return None
		
		if not revision:
			# Get the head - what we're supposed to have in our working dir
			try:
				f = open(filename)
				content = f.read()
				f.close()
				return content
			except Exception, e:
				getLogger().warning("Unable to read file %s: %s" % (filename, str(e)))
				return None
		else:
			# We need to retrieve the file from the given revision - notice that we only support number-based revs, no date.
			rev = pysvn.Revision(pysvn.opt_revision_kind.number, int(revision))
			try:
				content = pysvn.Client().cat(filename, revision = rev)
			except Exception, e:
				getLogger().warning("Unable to read file %s (revision %s): %s" % (filename, revision, e))
				return None
			else:
				return content

	def write(self, filename, content, baseRevision = None, reason = None, username = None):
		"""
		Write the file in the working tree, then autocommit it.
		
		WARNING: baseRevision is not supported yet - committed to head.
		"""
		if filename.startswith('/'):
			filename = filename[1:]
		
		localpath = filename

		filename = self._realpath(filename)
		if not filename: 
			raise Exception('Invalid file: not in base path')

		backupFile = None
		try:
			if fileExists(filename):
				b = '%s.backup' % filename
				os.rename(filename, b)
				backupFile = b
			f = open(filename, 'w')
			f.write(content)
			f.close()
			if backupFile:
				try:
					os.remove(backupFile)
				except:
					pass
		except Exception, e:
			if backupFile:
				os.rename(backupFile, filename)
			getLogger().warning("Unable to write content to %s: %s" % (filename, str(e)))
			raise(e)

		c = pysvn.Client()
		try:
			c.add(filename)
		except:
			# May already be under version control
			pass
		
		# May throw an error
		rev = c.checkin([filename], log_message = "%s %s (reason: %s)" % (backupFile and "Updated" or "Added", localpath, reason))
		
		getLogger().info("New revision created: %s" % rev.number)
		return str(rev.number)

	@logged
	def rename(self, filename, newname, reason = None, username = None):
		"""
		**** TODO *****
		
		Rename the file locally, then autocommit one deletion / one insertion for the main file,
		and one deletion/insertion per associated profile.
		"""
		# Remove the heading / for the local name
		if filename.startswith('/'):
			filename = filename[1:]
		localname = filename

		# The new local name relative to the file's cwd
		if newname.startswith('/'):
			newname = newname[1:]
		newlocalname = newname
		# The new local name relative to the working tree
		newlocalname = os.path.join(os.path.split(filename)[0], newlocalname)

		# local filesystem: absolute filenames
		filename = self._realpath(localname)
		if not filename: 
			return False
		newfilename = self._realpath(newlocalname)
		if not newfilename: 
			getLogger().warning("Unable to rename %s to %s: the target name is not in base path" % (filename, newname, str(e)))
			return False
		
		profilesdir = "%s.profiles" % filename
		newprofilesdir = "%s.profiles" % newfilename
		try:
			os.rename(filename, newfilename)
		except Exception, e:
			getLogger().warning("Unable to rename %s to %s: %s" % (filename, newname, str(e)))
			return False

		try:
			# rename profiles dir, too
			os.rename(profilesdir, newprofilesdir)
		except Exception, e:
			pass

		# Identify the profiles that were renamed/moved
		staged = [newlocalname, localname]
		
		for profile in glob.glob(newprofilesdir + '/*'):
			# The old profile name
			staged.append("%s.profiles/%s" % (localname, os.path.split(profile)[1]))
			# The new profile name
			staged.append("%s.profiles/%s" % (newlocalname, os.path.split(profile)[1]))
		
		c = pysvn.Client()
		rev = c.checkin(staged, log_message = "Renamed %s to %s (reason: %s)" % (localname, newname, reason))
		getLogger().info("New revision created: %s" % rev.number)
		return str(rev.number)

	@logged
	def unlink(self, filename, reason = None, username = None):
		"""
		Mark the file and its optional profiles folder as to remove, and commit the changes.
		"""
		# Remove the heading / for the local name
		if filename.startswith('/'):
			filename = filename[1:]
		localname = filename

		# local filesystem: absolute filenames
		filename = self._realpath(filename)
		if not filename: 
			return False

		staged = []		
		c = pysvn.Client()
		
		# Reference profiles to remove
		profilesdir = "%s.profiles" % filename
		if os.path.isdir(profilesdir):
			c.remove(profilesdir)
			staged.append(profilesdir)

		# Now mark the file to remove
		c.remove(filename)
		staged.append(filename)
		
		rev = c.checkin(staged, log_message = "Deleted %s (reason: %s)" % (localname, reason))
		getLogger().info("New revision created: %s" % rev.number)

		return True

	@logged
	def getdir(self, path):
		"""
		Read the working tree. No VCS interaction here.
		"""
		path = self._realpath(path)
		if not path: 
			return None

		try:
			entries = os.listdir(path)
			ret = []
			for entry in entries:
				if os.path.isfile("%s/%s" % (path, entry)):
					ret.append({'name': entry, 'type': 'file'})
				elif os.path.isdir("%s/%s" % (path, entry)) and not entry in self._excludedPatterns and not entry.endswith('.profiles'):
					ret.append({'name': entry, 'type': 'directory'})
			return ret
		except Exception, e:
			getLogger().warning("Unable to list directory %s: %s" % (path, str(e)))
		return None

	@logged
	def mkdir(self, path, username = None):
		"""
		Create a directory in the working tree.
		"""
		if path.startswith('/'):
			path = path[1:]
		localpath = path

		path = self._realpath(path)
		if not path: 
			return False

		if fileExists(path):
			return False

		try:
			os.makedirs(path, 0755)
		except:
			# already exists only ?...
			pass

		# We add the file, but it will be committed only when a file in it is checked in.
		c = pysvn.Client()
		c.add(path)
		c.checkin([path], "Added directory %s" % localpath)
			
		return True
	
	@logged
	def rmdir(self, path):
		"""
		Remove an empty directory. (and associated files)
		"""
		path = self._realpath(path)
		if not path: 
			return False

		try:
			if not os.path.isdir(path):
				return False
			
			# Check that the folder is empty
			entries = glob.glob("%s/" % path)
			if entries and not os.path.split(entries[0])[1] != ".svn":
				# Not empty
				return False
			
			c = pysvn.Client()
			c.remove(path)
			c.checkin([path], "Deleted directory %s" % path)
			return True

		except Exception, e:
			getLogger().warning("Unable to rmdir %s: %s" % (path, str(e)))
		return False

	@logged
	def renamedir(self, path, newname, reason = None, username = None):
		"""
		Rename a directory, then autocommit removes/adds.
		
		TODO: recursive staging.
		Since it's not ready, support for renaming the dir is disabled.
		"""
		getLogger().warning("Dir renaming is not supported by this backend")
		return False

	@logged
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

	@logged
	def revisions(self, filename, baseRevision, scope):
		"""
		Returns the revisions for a given file.
		"""
		if filename.startswith('/'):
			filename = filename[1:]
		
		localname = filename
		
		filename = self._realpath(filename)
		if not filename: 
			return None

		ret = []
		
		c = pysvn.Client()
		
		logs = c.log(filename)
		
		for l in logs:
			# We won't detect if the file was added/removed or actually updated.
			ret.append(dict(message = l.message, committer = l.author, date = l.date, id = l.revision.number, change = "updated"))
			
		return ret
	
	def isdir(self, path):
		path = self._realpath(path)
		if not path: 
			return False
		return os.path.isdir(path)

	def isfile(self, path):
		path = self._realpath(path)
		if not path:
			return False
		return os.path.isfile(path)

	# Profiles Management			

	def getprofiles(self, filename):
		filename = self._realpath(filename)
		if not filename:
			return None
		
		profilesdir = "%s.profiles" % filename
		
		try:
			entries = os.listdir(profilesdir)
			ret = []
			for entry in entries:
				if os.path.isfile("%s/%s" % (profilesdir, entry)):
					ret.append({'name': entry, 'type': 'file'})
				elif os.path.isdir("%s/%s" % (profilesdir, entry)) and not entry in self._excludedPatterns:
					ret.append({'name': entry, 'type': 'directory'})
			return ret
		except Exception, e:
			getLogger().warning("Unable to list profiles directory %s: %s" % (profilesdir, str(e)))
		return None

	def readprofile(self, filename, profilename):
		filename = self._realpath(filename)
		if not filename:
			return None
		
		profilefilename = "%s.profiles/%s" % (filename, profilename)
		try:
			f = open(profilefilename)
			content = f.read()
			f.close()
			return content
		except Exception, e:
			getLogger().warning("Unable to read file %s: %s" % (filename, str(e)))
			return None
		
	def writeprofile(self, filename, profilename, content, username = None):
		"""
		Create or update a profile, then autocommit.
		"""
		if filename.startswith('/'):
			filename = filename[1:]
		localname = filename

		profilelocalname = "%s.profiles/%s" % (localname, profilename)
		filename = self._realpath(filename)
		if not filename: 
			raise Exception('Invalid file: not in base path')

		# Automatically creates this backend-specific dir
		profilesdir = "%s.profiles" % filename

		c = pysvn.Client()
		try:
			os.makedirs(profilesdir, 0755)
			c.add(profilesdir)
			# May fail if already added - we ignore the exception
			c.checkin([profilesdir], "Added profiles directory for file %s" % localname)
		except:
			pass

		profilefilename = "%s.profiles/%s" % (filename, profilename)
		backupFile = None
		try:
			if fileExists(profilefilename):
				b = '%s.backup' % profilefilename
				os.rename(profilefilename, b)
				backupFile = b
			f = open(profilefilename, 'w')
			f.write(content)
			f.close()
			if backupFile:
				try:
					os.remove(backupFile)
				except:
					pass
		except Exception, e:
			if backupFile:
				os.rename(backupFile, profilefilename)
			getLogger().warning("Unable to write content to %s: %s" % (profilefilename, str(e)))
			raise(e)

		try:
			c.add(profilelocalname)
		except:
			# May already be under version control
			pass
		# May throw an error
		rev = c.checkin([profilelocalname], log_message = "%s profile %s for %s" % (backupFile and "Updated" or "Added", profilename, localname))
		getLogger().info("New revision created: %s" % rev.number)
		return str(rev.number)

	def unlinkprofile(self, filename, profilename, username = None):
		"""
		Removes a profile, then autocommit the change. 
		"""
		if filename.startswith('/'):
			filename = filename[1:]
		localname = filename

		profilelocalname = "%s.profiles/%s" % (localname, profilename)

		filename = self._realpath(filename)
		if not filename:
			return None
		
		profilefilename = "%s.profiles/%s" % (filename, profilename)
		c = pysvn.Client()
		try:
			c.remove(profilefilename)
		except Exception, e:
			getLogger().warning("Unable to unlink %s: %s" % (profilefilename, str(e)))
			return False
		rev = c.checkin([profilefilename], log_message = "Removed profile %s for %s" % (profilename, localname))
		getLogger().info("New revision created: %s" % rev.number)
		return True
		
	def profileattributes(self, filename, profilename):
		filename = self._realpath(filename)
		if not filename: 
			return None

		profilefilename = "%s.profiles/%s" % (filename, profilename)

		try:
			s = os.stat(profilefilename)
			a = FileSystemBackend.Attributes()
			a.mtime = s.st_ctime
			a.size = s.st_size
			return a
		except Exception, e:
			getLogger().warning("Unable to get file attributes for %s: %s" % (profilefilename, str(e)))			
		return None
	

FileSystemBackendManager.registerFileSystemBackendClass("svn", SvnBackend)
