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
# Package-related functions:
#
# - package creation in a file system,
# - package extraction, importation, etc.
#
##

import FileSystemManager

import logging
import os
import cStringIO as StringIO
import tarfile
import time

def getLogger():
	return logging.getLogger("PM")

def createPackageFile(path):
	"""
	Creates a testerman package file from a docroot package folder.
	"""
	def _packageFolder(tfile, relbasepath, docrootbasepath):
		getLogger().debug("Walking folder %s..." % docrootbasepath)
		for entry in FileSystemManager.instance().getdir(docrootbasepath):
			name, apptype = entry['name'], entry['type']
			if apptype == FileSystemManager.APPTYPE_DIR:
				relpath = "%s%s/" % (relbasepath, name) # the name of the current item within the package
				docrootpath = "%s%s/" % (docrootbasepath, name) # the name of the current item within the docroot
				getLogger().debug("Adding directory %s..." % relpath)
				tarinfo = tarfile.TarInfo(relpath)
				tarinfo.type = tarfile.DIRTYPE
				tarinfo.mode = 0755
				tarinfo.uid = os.getuid()
				tarinfo.gid = os.getgid()
				tarinfo.mtime = time.time()
				tfile.addfile(tarinfo)
				_packageFolder(tfile, relbasepath = relpath, docrootbasepath = docrootpath)
			else:
				relname = "%s%s" % (relbasepath, name) # the name of the current item within the package
				docrootname = "%s%s" % (docrootbasepath, name) # the name of the current item within the docroot
				getLogger().debug("Adding file %s..." % relname)
				tarinfo = tarfile.TarInfo(relname)
				tarinfo.type = tarfile.AREGTYPE
				tarinfo.mode = 0644
				tarinfo.uid = os.getuid()
				tarinfo.gid = os.getgid()
				tarinfo.mtime = time.time()
				content = FileSystemManager.instance().read(docrootname)
				tarinfo.size = len(content)
				contentObj = StringIO.StringIO(content)
				tfile.addfile(tarinfo, contentObj)
				contentObj.close()
				getLogger().debug("File %s added to package file (%s bytes)" % (relname, tarinfo.size))
		
	getLogger().info("Creating package file from %s..." % path)
	
	if not FileSystemManager.instance().isdir(path):
		getLogger().info("Cannot create package from %s: not a path to package" % path)
		return None
	
	tpk = StringIO.StringIO()
	tfile = tarfile.open("tpk", "w:gz", tpk)
	# Now, traverse the files into path
	if not path.endswith('/'):
		path = "%s/" % path
	_packageFolder(tfile, '', path)

	tfile.close()
	
	contents = tpk.getvalue()
	tpk.close()
	getLogger().info("Package file for %s created, %s bytes" % (path, len(contents)))
	return contents

