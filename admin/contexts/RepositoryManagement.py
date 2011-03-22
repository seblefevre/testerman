# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2011 Sebastien Lefevre and other contributors
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
# Repository browser context for testerman-admin.
#
##


import TestermanManagementClient

import os
import datetime
import time
import os.path

##
# Context definition
##

from StructuredInteractiveShell import *

class RepositoryContext(CommandContext):
	"""
	This context is basically a shell to browse a repository as if it
	was a local filesystem.
	"""
	def __init__(self):
		CommandContext.__init__(self)
		self._client = None

		# cp
		node = SequenceNode()
		node.addField("source", "source object", StringNode("source path"))
		node.addField("destination", "destination object", StringNode("destination path"))
		self.addCommand("cp", "copy a file to a destination", node, self.cp)

		# ls
		self.addCommand("ls", "list current entries", None, self.ls)

		# cd
		node = StringNode("directory")
		self.addCommand("cd", "change directory", node, self.cd)
		
		# pwd
		self.addCommand("pwd", "show current directory", None, self.cwd)

		# mkdir
		self.addCommand("mkdir", "make a new directory", StringNode("directory name"), self.mkdir)

		# rm
		self.addCommand("rm", "remove a file. Associated profiles are also removed, if any.", StringNode("file to remove"), self.rm)

		# rmdir
		self.addCommand("rmdir", "remove a directory.", StringNode("directory to remove"), self.rmdir)

		# rename
		node = SequenceNode()
		node.addField("source", "source object", StringNode("source object"))
		node.addField("newname", "new name", StringNode("new name"))
		self.addCommand("rename", "rename a file or a directory to a new name", node, self.rename)
		
		self._cwd = "/repository"

	def _getClient(self):
		if not self._client:
			serverUrl = os.environ.get('TESTERMAN_SERVER')
			if not serverUrl:
				raise Exception("Sorry, no testerman server set (TESTERMAN_SERVER).")
			self._client = TestermanManagementClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)

		return self._client

	def ls(self):
		entries = self._getClient().getDirectoryListing(self.getCwd())
		if entries is None:
			self.error("Invalid directory (%s)" % self.getCwd())
		else:
			self.printTable(headers = ['name', 'type'], rows = entries, order = 'name')

	def getCwd(self):
		return self._cwd
	
	def cwd(self):
		self.notify(self.getCwd())
	
	def cd(self, path):
		if path.startswith('/'):
			p = os.path.normpath(path)
		else:
			p = os.path.normpath(self.getCwd() + "/" + path)
		
		if not (p+"/").startswith("/repository/"):
			self.error("Invalid directory (%s)" % p)
		else:
			entries = self._getClient().getDirectoryListing(p)
			if entries is not None:
				self._cwd = p
				self.notify("Current dir: %s" % p)
			else:
				self.error("Invalid directory (%s)" % (p))

	def cp(self, source, destination):
		if not source.startswith('/'):
			source = self.getCwd() + '/' + source
		source = os.path.normpath(source)

		if not destination.startswith('/'):
			destination = self.getCwd() + '/' + destination
		destination = os.path.normpath(destination)
		
		self.notify("Copying %s to %s..." % (source, destination))
		
		ret = self._getClient().copy(source, destination)
		if not ret:
			self.error("Unable to copy (unspecified error)")
		else:
			self.notify("OK")

	def rename(self, source, newname):
		if not source.startswith('/'):
			source = self.getCwd() + '/' + source
		source = os.path.normpath(source)

		self.notify("Renaming %s to %s..." % (source, newname))
		
		ret = self._getClient().rename(source, newname)
		if not ret:
			self.error("Unable to rename (unspecified error)")
		else:
			self.notify("OK")

	def mkdir(self, path):		
		if not path.startswith('/'):
			path = self.getCwd() + '/' + path
		path = os.path.normpath(path)

		self.notify("Creating %s..." % (path))
		
		ret = self._getClient().makeDirectory(path)
		if not ret:
			self.error("Unable to create directory (unspecified error)")
		else:
			self.notify("OK")

	def rm(self, path):		
		if not path.startswith('/'):
			path = self.getCwd() + '/' + path
		path = os.path.normpath(path)

		self.notify("Removing %s..." % (path))
		
		ret = self._getClient().removeFile(path)
		if not ret:
			self.error("Unable to remove file (unspecified error)")
		else:
			self.notify("OK")

	def rmdir(self, path):		
		if not path.startswith('/'):
			path = self.getCwd() + '/' + path
		path = os.path.normpath(path)

		self.notify("Removing %s..." % (path))
		
		ret = self._getClient().removeDirectory(path)
		if not ret:
			self.error("Unable to remove directory (unspecified error)")
		else:
			self.notify("OK")
