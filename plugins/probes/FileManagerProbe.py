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
# LDAP client probe, based on python-ldap, the Python wrapper over
# OpenLDAP libraries.
#
##

import ProbeImplementationManager

import os

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
		boolean autorestore optional, // backup existing file, restore it on unmap, defaulted to False
	}
	
	type record RemoveCommand
	{
		universal charstring name,
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
		boolean autorestore optional, // backup existing file, restore it on unmap, defaulted to False
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
		self._server = None
		self._pendingCommand = None

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

	def onTriSend(self, message, sutAddress):
		# Exceptions are turned into Error messages sent back to userand, according of the current
		# attempted operation.
		if not isinstance(message, (list, tuple)) and not len(message) == 2:
			raise Exception("Invalid message format - please read the file.manager probe documentation")
		command, args = message
		
		if command == 'createFile':
			self._checkArgs(args, [ ('name', None), ('content', ''), ('autorestore', False) ])
			self.createFile(args['name'], args['content'], args['autorestore'])
		
		elif command == 'remove':
			self._checkArgs(args, [ ('name', None) ])
			self.remove(args['name'])
		
		elif command == 'createLink':
			self._checkArgs(args, [ ('name', None), ('target', None), ('autorestore', False) ])
			self.createLink(args['name'], args['target'], args['autorestore'])

		elif command == 'copy':
			self._checkArgs(args, [ ('source', None), ('destination', None), ('autorestore', False) ])
			self.copy(args['source'], args['destination'], args['autorestore'])

		elif command == 'move':
			self._checkArgs(args, [ ('source', None), ('destination', None), ('autorestore', False) ])
			self.move(args['source'], args['destination'], args['autorestore'])

		else:
			raise Exception("Invalid command (%s)" % command)
	
	def _getPendingCommand(self):
		self._lock()
		ret = self._pendingCommand
		self._unlock()
		return ret
	
	def _setPendingCommand(self, command):
		self._lock()
		self._pendingCommand = command
		self._unlock()
	
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
		
				
	
ProbeImplementationManager.registerProbeImplementationClass('file.manager', FileManagerProbe)

