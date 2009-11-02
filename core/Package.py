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
import xml.dom.minidom


DEFAULT_PACKAGE_DESCRIPTION = """<?xml version="1.0" encoding="utf-8"?>
<package>
 <author></author>
 <default-script></default-script>
 <status>designing</status>
 <description></description>
</package>
"""

def getLogger():
	return logging.getLogger("PM")

def createPackageFile(path):
	"""
	Creates a testerman package file from a docroot package root folder.
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

def createPackage(path):
	"""
	Creates a new package structure with path as package root folder.
	"""
	if FileSystemManager.instance().isfile(path):
		getLogger().info("Cannot create package as %s: is a file" % path)
		raise Exception("Invalid package path: is a file")
	
	if FileSystemManager.instance().isdir(path):
		getLogger().info("Cannot create package as %s: path already exist" % path)
		raise Exception("Invalid package path: this path already exist")

	FileSystemManager.instance().mkdir("%s/profiles" % path, False)
	FileSystemManager.instance().mkdir("%s/src" % path, False)
	FileSystemManager.instance().write("%s/package.xml" % path, DEFAULT_PACKAGE_DESCRIPTION, notify = False)
	FileSystemManager.instance()._notifyDirCreated(path)
	return True		

def getPackageMetadata(path):
	"""
	Extracts the different package metadata contained into the package.xml root folder.
	
	@type  path: string
	@param path: the docroot path to the package's root folder
	
	@rtype: dict[string] of unicode string
	@returns: the metadata, as a dict containing the following keys:
	          author, description, default-script, status
	"""
	descriptionFile = "%s/package.xml" % path
	try:
		content = FileSystemManager.instance().read(descriptionFile)
		if content is None:
			raise Exception("Unable to read the package description file for package %s" % path)
		# Now, parse the document
		return parsePackageDescription(content)
	except Exception, e:
		raise e

def parsePackageDescription(content):
	"""
	Parse a package description file.
	"""
	# This implementation deserves some greater care. 
	ret = { 'description': '', 'default-script': '', 'author': '', 'status': '' }
	try:
		doc = xml.dom.minidom.parseString(content)
		
		for e in doc.getElementsByTagName('description'):
			if e.firstChild:
				ret['description'] = e.firstChild.nodeValue
		for e in doc.getElementsByTagName('author'):
			if e.firstChild:
				ret['author'] = e.firstChild.nodeValue
		for e in doc.getElementsByTagName('default-script'):
			if e.firstChild:
				ret['default-script'] = e.firstChild.nodeValue
		for e in doc.getElementsByTagName('status'):
			if e.firstChild:
				ret['status'] = e.firstChild.nodeValue
		
		return ret
	except Exception, e:
		raise Exception("Error while parsing package description file: %s" % e)
		

def checkPackageFile(content):
	"""
	Checks that a package file is correct:
	- all mandatory files are present
	- standard directories present
	
	Notice that it does not check that all dependencies are present.
	
	Package structure:
	
	package.xml
	src/
	profiles/
	"""
	profilePresent = False
	srcPresent = False
	packageDescriptionPresent = False
	metadata = None
	
	tpk = StringIO.StringIO(content)
	tfile = tarfile.open("tpk", "r:gz", tpk)
	contents = tfile.getmembers()
	for c in contents:
		if c.name == "package.xml" and c.isfile():
			metadata = parsePackageDescription(tfile.extractfile(c).read())
			packageDescriptionPresent = True
		elif c.name == "src" and c.isdir():
			srcPresent = True
		elif c.name == "profiles" and c.isdir():
			profilePresent = True
	
	if not packageDescriptionPresent:
		raise Exception("Missing package description file (package.xml)")
	if not srcPresent:
		raise Exception("Missing source folder (src)")
	if not profilePresent:
		raise Exception("Missing profile folder (profile)")
	
	# Now we should check the package.xml file, too
	return True

def importPackageFile(content, path):
	"""
	Expand a package file to a docroot folder.
	"""
	try:
		checkPackageFile(content)
	except Exception, e:
		getLogger().info("Invalid package file: %s" % e)
		raise Exception("Invalid package file: %s" % e)
	
	if FileSystemManager.instance().isfile(path):
		getLogger().info("Cannot import package to %s: not a path to package" % path)
		raise Exception("Invalid destination package path: is a file")
	
	if FileSystemManager.instance().isdir(path):
		getLogger().info("Cannot import package from %s: destination path already exist" % path)
		raise Exception("Invalid destination package path: this path already exist")


	# Minimal package tree
	FileSystemManager.instance().mkdir("%s/profiles" % path, False)
	FileSystemManager.instance().mkdir("%s/src" % path, False)

	# First unpack the package, then notify the package dir creation so that it is seen as a package folder.
	tpk = StringIO.StringIO(content)
	tfile = tarfile.open("tpk", "r:gz", tpk)
	contents = tfile.getmembers()
	for c in contents:
		# TODO
		if c.name.startswith('src/') or c.name.startswith('profiles/') or c.name in [ 'package.xml' ]:
			dst = "%s/%s" % (path, c.name)
			if c.isfile():
				getLogger().info("Importing %s to %s..." % (c.name, dst))
				content = tfile.extractfile(c).read() 
				FileSystemManager.instance().write(dst, content, notify = False)
		else:
			getLogger().info("Discarding importation of %s" % c.name)
	
	FileSystemManager.instance()._notifyDirCreated(path)
	return True	



if __name__ == '__main__':
	import sys
	f = open(sys.argv[1])
	tpk = f.read()
	f.close()
	
	try:
		checkPackageFile(tpk)
		print "The package file %s is a valid Testerman package." % sys.argv[1]
	except Exception, e:
		print "Invalid package file: %s" % e
	
	
	
