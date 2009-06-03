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
# ATS/Module (i.e. Python) and Campaign
# dependency resolver.
#
# Provides several functions to identify dependencies
# and resolve them to actual file names.
#
##

import ConfigManager
import FileSystemManager

import logging
import os.path
import modulefinder
import imp
import StringIO


def getLogger():
	return logging.getLogger('DepResolver')

################################################################################
# Python source management
################################################################################

def python_getDependencyFilenames(source, sourcePath = None, recursive = True):
	"""
	Returns a list of userland module filenames
	(including their own dependencies) the ATS/module depends on.
	
	Only userland dependencies are searched, i.e. modules below $docroot/repository.
	Non-userland dependencies, such as Testerman and Python std modules,
	are not reported.

	NB: this works only because user modules are files only, not packages.
	
	@type  source: utf-8 string
	@param source: a Python source file (module or ATS)
	@type  sourcePath: string
	@param sourcePath: docroot path used as a 'working dir' to search for
	relative dependencies. Typically the path where the source has been extracted
	from.
	@type  recursive: bool
	@param recursive: if True, search recursively for dependencies in imported modules.
	
	@rtype: list of strings
	@returns: a list of docroot-path to dependencies (no duplicate).
	"""
	ret = []
	# Bootstrap the deps (stored as (list of imported modules, path of the importing file) )
	deps = [ (d, sourcePath) for d in python_getDirectDependencies(source) ]
	
	# tuple (dep, fromPath)
	analyzedDeps = []
	# dep only
	alreadyAnalyzedDeps = []
	
	while len(deps):
		dep, fromFilePath = deps.pop()
		# Some non-userland files - not resolved to build the TE userland package
		# How can we detect standard Python includes ?
		# fromFilePath starts with the "python home" ? something else ?
		getLogger().debug("Analyzing dependency %s" % dep)

		# Skip some 
		#if dep in [ ]:
		#	getLogger().info("Skipping dependency analysis: not userland (%s)" % dep)
		#	continue

		# Skip already analyzed deps (analyzed from this very path,
		# since the same dep name, from different paths, may resolved to
		# different things)
		if (dep, fromFilePath) in analyzedDeps:
			continue

		getLogger().debug("Analyzing dependency %s (from %s)..." % (dep, fromFilePath))

		# Ordered list of filenames within the docroot that could provide the dependency:
		# (module path)
		# - first search from the local file path, if provided,
		# - then search from the userland module paths (limited to '/repository/' for now)
		modulePaths = []
		# First, try a local module (relative path) (same dir as the currently analyzed file)
		if fromFilePath:
			modulePaths.append(fromFilePath)
		for modulePath in [ '/repository' ]:
			modulePaths.append(modulePath)

		getLogger().debug("Analyzing dependency %s, search path: %s..." % (dep, modulePaths))

		found = None
		depSource = None
		for path in modulePaths:
			depFilename = '%s/%s.py' % (path, dep.replace('.', '/'))
			try:
				depSource = FileSystemManager.instance().read(depFilename)
			except Exception:
				pass
			if depSource is not None:
				found = depFilename
				break
		if not found:
			raise Exception('Missing module: %s is not available in the repository (search path: %s)' % (dep, modulePaths))

		# OK, we found a file.
		if not depFilename in ret:
			ret.append(depFilename)

		# Now, analyze it and add new dependencies to analyze
		if recursive:
			fromFilePath = '/'.join(depFilename.split('/')[:-1])
			directDependencies = python_getDirectDependencies(depSource)
			getLogger().info('Direct dependencies for file %s (%s):\n%s' % (depFilename, 
				fromFilePath, str(directDependencies)))
			for d in directDependencies:
				if not d in deps and not (d, fromFilePath) in analyzedDeps and d != dep:
					deps.append((d, fromFilePath))

		# Flag the dep as analyzed - from this path (since it may lead to another filename
		# when evaluated from another path)
		analyzedDeps.append((dep, fromFilePath))
		alreadyAnalyzedDeps.append(dep)

	return ret	

def python_getDirectDependencies(source):
	"""
	Returns a list of direct dependencies (source is an ATS/Module source code),
	as a list of module names (not filenames !)
	
	@type  source: utf-8 string
	@param source: Python source code
	
	@rtype: list of strings
	@returns: a list of module names ('mylibs.mymodule', 'amodule', etc) 
	"""
	mf = modulefinder.ModuleFinder()
	fp = StringIO.StringIO(source)
	mf.load_module('__main__', fp, '<string>', ("", "r", imp.PY_SOURCE))

	rawdeps = mf.any_missing()
	directdeps = []
	# Let's filter and retrieve only missing imports from __main__
	# i.e. direct missing dependencies
	for name in rawdeps:
		mods = mf.badmodules[name].keys()
		if '__main__' in mods:
			directdeps.append(name)
	
	getLogger().info('Unresolved modules: %s' % str(directdeps))
	
	return directdeps


################################################################################
# Campaign source management
################################################################################

def campaign_getDependencyFilenames(source, sourcePath = None, recursive = False):
	"""
	Returns a list of userland module filenames
	(including their own dependencies) the campaign depends on.
	
	Calls pythong_getDependencyFilenames on ats files if recursive is True,
	and thus only userland dependencies are searched.

	NB: this works only because user modules are files only, not packages.
	
	@type  source: utf-8 string
	@param source: a Python source file (module or ATS)
	@type  sourcePath: string
	@param sourcePath: docroot path used as a 'working dir' to search for
	relative dependencies. Typically the path where the source has been extracted
	from.
	@type  recursive: bool
	@param recursive: if True, search recursively for dependencies in imported modules.
	
	@rtype: list of strings
	@returns: a list of docroot-path to dependencies (no duplicate).
	"""
	return []

