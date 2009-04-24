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
# File "manager" probe:
# basic file system operations,
# file creation from ATS embedded resources.
#
##

import ProbeImplementationManager

import os
import shutil
import tempfile
import threading
import grp
import pwd

def fileExists(path):
	try:
		os.stat(path)
		return True
	except:
		return False

class FileManagerProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	= Identification and Properties =

	Probe Type ID: `file.manager`

	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	
	(no properties)

	= Overview =

	This probe performs basic local file management operations:
	 * file creation (with content injection)
	 * file move, deletion, renaming
	 * link creation, deletion
	
	One of its primary purposes is providing the ability to create
	files on the fly from resources that were embedded in your ATS or its
	dependencies. This way, you may have no additional requirements
	on the SUT: you can embed some reference files directly into the
	Testerman userland instead of instructing the user to get and copy
	files from another source.
	
	== Availability ==

	All platforms.

	== Dependencies ==

	None.

	== See Also ==
	
	
	= TTCN-3 Types Equivalence =

	The test system interface port bound to such a probe complies with the `FileManagerPortType` port type as specified below:
	{{{
	type union FileManagementCommand
	{
		CreateFileCommand createFile,
		CreateLinkCommand createLink,
		RemoveCommand remove,
		MoveCommand move,
		CopyCommand copy,
	}
		
	type record CreateFileCommand
	{
		universal charstring name,
		octetstring content optional, // defaulted to an empty content
		boolean autorevert optional, // backup existing file, restore it on unmap, defaulted to False
	}
	
	type record RemoveCommand
	{
		universal charstring path,
	}
	
	type record MoveCommand
	{
		universal charstring source,
		universal charstring destination,
	}
	
	type record CopyCommand
	{
		universal charstring source,
		universal charstring destination,
	}
	
	type record CreateLinkCommand
	{
		universal charstring name,
		universal charstring target,
		boolean autorevert optional, // backup existing file, restore it on unmap, defaulted to False
	}
	
	type record CommandStatus
	{
		integer status,
		universal charstring errorMessage optional, // only if status > 0
	}
	
	type union FileManagementResponse
	{
		CommandStatus status,
		// more to come: fileExists response, fileType response, ...
	}

	type port FileManagerPortType message
	{
		in  FileManagementCommand;
		out FileManagementResponse;
	}
	}}}
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()
		# Backup / revert operation lists
		# Contain absolute paths
		self._addedFiles = []
		self._modifiedFiles = [] # modified or deleted

	# ProbeImplementation reimplementation

	def onTriUnmap(self):
		self.getLogger().debug("onTriUnmap()")
		self._cleanup()

	def onTriMap(self):
		self.getLogger().debug("onTriMap()")
	
	def onTriSAReset(self):
		self.getLogger().debug("onTriSAReset()")
		self._cleanup()
	
	def onTriExecuteTestCase(self):
		self.getLogger().debug("onTriExecuteTestCase()")
		self._cleanup()

	def onTriSend(self, message, sutAddress):
		# Exceptions are turned into Error messages sent back to userand, according of the current
		# attempted operation.
		if not isinstance(message, (list, tuple)) and not len(message) == 2:
			raise Exception("Invalid message format - please read the file.manager probe documentation")
		command, args = message
		
		if command == 'createFile':
			self._checkArgs(args, [ ('name', None), ('content', ''), ('autorevert', False) ])
			self.createFile(args['name'], args['content'], args['autorevert'])
		
		elif command == 'remove':
			self._checkArgs(args, [ ('path', None), ('autorevert', False) ])
			self.remove(args['path'], args['autorevert'])
		
		elif command == 'createLink':
			self._checkArgs(args, [ ('name', None), ('target', None), ('autorevert', False) ])
			self.createLink(args['name'], args['target'], args['autorevert'])

		elif command == 'copy':
			self._checkArgs(args, [ ('source', None), ('destination', None), ('autorevert', False) ])
			self.copy(args['source'], args['destination'], args['autorevert'])

		elif command == 'move':
			self._checkArgs(args, [ ('source', None), ('destination', None), ('autorevert', False) ])
			self.move(args['source'], args['destination'], args['autorevert'])

		elif command == 'chown':
			self._checkArgs(args, [ ('path', None), ('user', None), ('group', None), ('autorevert', False) ])
			self.chown(args['path'], args['user'], args['group'], args['autorevert'])

		elif command == 'chmod':
			self._checkArgs(args, [ ('path', None), ('mode', None), ('autorevert', False) ])
			self.chmod(args['path'], args['mode'], args['autorevert'])

		else:
			raise Exception("Invalid command (%s)" % command)

	##
	# Actions
	##
	def createFile(self, name, content, autorevert):
		if autorevert:
			self._backupFile(name)
		
		dirname, filename = os.path.split(name)
		if not fileExists(dirname):
			os.makedirs(dirname)
		f = open(name, 'wb')
		f.write(content)
		f.close()

	def remove(self, path, autorevert):
		if autorevert:
			self._backupFileToDelete(path)
		if os.path.isdir(path):
			shutil.rmtree(path)
		else:
			os.unlink(path)
	
	def chown(self, path, user, group, autorevert):
		if autorevert:
			self._backupFile(path)
		if not isinstance(user, int):
			user = pwd.getpwnam(user).pw_uid
		if not isinstance(group, int):
			group = grp.getgrnam(group).gr_gid
		os.chown(path, user, group)

	def chmod(self, path, mode, autorevert):
		if autorevert:
			self._backupFile(path)
		os.chmod(path, mode)
	
	def createLink(self, name, target, autorevert):
		if autorevert:
			self._backupFile(name)
		os.symlink(target, name)
	
	def copy(self, source, destination, autorevert):
		if autorevert:
			self._backupFile(destination)
		shutil.copytree(source, destination, True) # preserve symlinks

	def move(self, source, destination, autorevert):
		if autorevert:
			self._backupFile(destination)
		shutil.move(source, destination)

	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()

	def __del__(self):
		self._cleanup()
	
	def _cleanup(self):
		"""
		Reverts modified files/deletes created files.
		"""
		for path in self._addedFiles:
			try:
				self.getLogger().debug("Removing added file %s..." % path)
#				shutil.rmtree(path)
			except Exception, e:
				self.getLogger().warning("Unable to remove added file %s: %s" % (path, str(e)))
		
		for path in self._modifiedFiles:
			try:
				self.getLogger().debug("Restoring modified/deleted file %s..." % path)
				# ...
			except Exception, e:
				self.getLogger().warning("Unable to restore modified/deleted file %s: %s" % (path, str(e)))

		self._addedFiles = []
		self._modifiedFiles = []
	
	def _backupFileToDelete(self, path):
		if not path in self._addedFiles + self._modifiedFiles:
			pass
#			targetDir = "%s/
#			os.makedirs
#			target = "%s/
#			self.getLogger().info("Backup up file to delete %s -> %s" % (path, target)
#			shutil.move(path, target)
#			self._deletedFiles.append(path)
	
	def _backupFile(self, path):
		if not path in self._addedFiles + self._modifiedFiles:
			# if fileExists(path):
			pass
			
		
ProbeImplementationManager.registerProbeImplementationClass('file.manager', FileManagerProbe)

