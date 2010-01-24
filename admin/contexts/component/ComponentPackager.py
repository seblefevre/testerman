# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2010 Sebastien Lefevre and other contributors
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
# Component Package Creation from Source.
#
# A Testerman component source should include the following files in its
# root folder:
#
# PACKAGE: contains a list (one per line) of files to include in a package.
# wildcards are accepted.
# PACKAGE.exclude: contains a list of excluded files/dirs.
#
# Examples:
# PACKAGE:
# ../core/CodecManager.py
# ../core/ProbeImplementationManager.py
# ../plugins
# *.py
# ../common/*.py
#
# PACKAGE.exclude:
# .svn
# .CVS
# *.asn
# *.pyc
# 
# 
##

import glob
import shutil
import tempfile
import tarfile
import os.path
import re

def fileExists(filename):
	try:
		os.stat(filename)
		return True
	except:
		return False

def walk(sources, exclude = None):
	"""
	Returns a list of files (complete paths) contained in sources
	(list of files/dir with wildcard support) that are not
	excluded.
	exclude is a function(name) -> True/False
	"""
	ret = []
	for source in sources:
		source = os.path.realpath(source)
		for obj in glob.glob(source):
			if exclude and exclude(obj):
				continue
			if os.path.isdir(obj):
				ret += walk([ '%s/*' % obj ], exclude)
			else:
				ret.append(obj)
	return ret

def wildcardToRegexp(s):
	"""
	Turns a wildcard-based string s into an equivalent regexp.
	(only * and ? are supported for now)
	"""
	return s.replace('.', '\\.').replace('?', '.').replace('*', '.*') + '$'


def _createPackage(sources, filename, baseDir = "", excluded = []):
	"""
	Creates the component package.
	This function is wrapped into createPackage() for convenience.
	"""
	def isExcluded(f):
		for regexp in excluded:
			if re.match(regexp, f):
				return True
		return False
	
	tmpdir = tempfile.mkdtemp()

	try:
		for entry in sources:
			for obj in glob.glob(entry):
#				print "Copying %s to %s ..." % (obj, tmpdir)
				if os.path.isdir(obj):
					shutil.copytree(obj, tmpdir + "/" + os.path.basename(obj))
				else:
					shutil.copy(obj, tmpdir + "/")

		# Now, create a tar file
		t = tarfile.open(name = filename, mode = 'w:gz')
		for name in walk([tmpdir + '/*'], isExcluded):
			t.add(name, arcname = name.replace(tmpdir, baseDir), recursive = False) # strip the tmpdir from the archive name
		t.close()
#		print "archive %s created." % filename

		# Purge the temp dir
		shutil.rmtree(tmpdir)
	except Exception, e:
		try:
			shutil.rmtree(tmpdir)
		except:
			pass
		raise e


def createPackage(sourceRoot, filename, baseDir = ""):
	"""
	Creates a package that is suitable for a deployment for the component 
	whose source is located in sourceRoot.
	
	This function automatically searches for the PACKAGE and PACKAGE.exclude
	files to create the package, whose filename is provided by the user.
	
	The baseDir is the resulting base directory in the final archive.
	"""
	pfile = os.path.join(sourceRoot, "PACKAGE")
	pefile = os.path.join(sourceRoot, "PACKAGE.exclude")
	if not fileExists(pfile):
		raise Exception("Unable to find a PACKAGE file in %s." % sourceRoot)

	sources = [ x.strip() for x in open(pfile).readlines() if x.strip() and not x.strip().startswith('#') ]

	excluded = []	
	if fileExists(pefile):
		excluded = [ wildcardToRegexp(x.strip()) for x in open(pefile).readlines() if x.strip() and not x.strip().startswith('#') ]

	sources = [ '%s/%s' % (sourceRoot, x) for x in sources ]

	return _createPackage(sources, filename, baseDir, excluded)


if __name__ == "__main__":
	createPackage("/home/seb/dev/testerman/trunk/pyagent", "/tmp/pyagent.tgz")


