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
# ATS/Module (i.e. Python) and Campaign
# dependency resolver.
#
# Provides several functions to identify dependencies
# and resolve them to actual file names.
#
##

import ConfigManager
import FileSystemManager

import imp
import logging
import modulefinder
import os.path
import re
import StringIO


cm = ConfigManager.instance()

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('DepResolver')


################################################################################
# Python source management
################################################################################

def python_getDependencyFilenames(source, sourcePath = None, recursive = True, sourceFilename = "<local>"):
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
	@type  sourceFilename: string
	@param sourceFilename: a string to help identify the file that yielded the source. 
	For non-repository files, use <local>, by convention.
	
	@rtype: list of strings
	@returns: a list of docroot-path to dependencies (no duplicate).
	"""
	ret = []

	# Bootstrap the deps (stored as (list of imported modules, path of the importing file) )
	toResolve = [ (d, sourceFilename) for d in python_getImportedUserlandModules(source, sourceFilename = sourceFilename) ]
	
	# the list of resolved dependencies,
	# as a map (import, fromFilename): resolvedFilename
	resolvedSoFar = {}
	
	# For each deps to resolve (a list of (import, fromFilename)),
	# we need to resolve the filename that will provide this import for this file.
	while len(toResolve):
		getLogger().debug("List of imports to resolve for script %s:\n%s" % (sourceFilename, "\n".join(["%s (used in %s)" % x for x in toResolve])))
		dep, fromFilename = toResolve.pop()
		# Some non-userland files - not resolved to build the TE userland package
		# How can we detect standard Python includes ?
		# fromFilePath starts with the "python home" ? something else ?
		getLogger().debug("Resolving import %s from %s..." % (dep, fromFilename))

		# Skip some dependencies provided by the Testerman infrastructure
		#if dep in [ ]:
		#	getLogger().info("Resolving import %s from %: skipped, not userland" % (dep, fromFilename))
		#	continue

		# Skip already resolved dependencies
		if (dep, fromFilename) in resolvedSoFar:
			getLogger().debug("Resolving import %s from %s: already resolved as %s" % (dep, fromFilename, resolvedSoFar[(dep, fromFilename)]))
			continue

		# Ordered list of filenames within the docroot that could provide the dependency:
		# (module path)
		# - first search from the local file path, if provided,
		# - then search from the userland module paths (limited to '/repository/' for now)
		modulePaths = []
		# First, try a local module (relative path) (same dir as the currently analyzed file)
		if sourcePath:
			modulePaths.append(sourcePath)
		# Then fall back to standard "testerman userland paths" (for now, hardcoded to /repository)
		for modulePath in [ '/repository' ]:
			if not modulePath in modulePaths:
				modulePaths.append(modulePath)

		getLogger().debug("Resolving import %s from %s: searching in paths:\n%s" % (dep, fromFilename, "\n".join(modulePaths)))

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
			getLogger().debug("Resolving import %s from %s: failed, not available in the repository, searched in paths:\n%s" % (dep, fromFilename, "\n".join(modulePaths)))
			raise Exception('Missing module: %s (imported from %s) is not available in the repository (search path: %s)' % (dep, fromFilename, modulePaths))

		# OK, we resolved a file.
		resolvedSoFar[(dep, fromFilename)] = depFilename
		getLogger().debug("Resolving import %s from %s: resolved as %s" % (dep, fromFilename, depFilename))
		if not depFilename in ret:
			ret.append(depFilename)
			getLogger().debug("Script %s is now using the following files:\n%s" % (sourceFilename, "\n".join(ret)))

		# Now, analyze the resolved file and add its own dependencies to the list to resolve,
		# if not already resolved
		if recursive:
			sourcePath = '/'.join(depFilename.split('/')[:-1])
			importedModules = python_getImportedUserlandModules(depSource, depFilename)
			for im in importedModules:
				if not (im, depFilename) in resolvedSoFar:
					toResolve.append((im, depFilename))
				else:
					getLogger().debug("Resolving import %s from %s: already resolved" % (im, depFilename))

	return ret	

def python_getImportedUserlandModules(source, sourceFilename):
	"""
	Returns a list of direct (userland) dependencies (source is an ATS/Module source code),
	as a list of module names (not filenames !)
	
	@type  source: utf-8 string
	@param source: Python source code
	@type  sourceFilename: utf-8 string
	@param sourceFilename: the filename of this source, if known
	
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
	
	getLogger().info('Userland modules imported by file %s:\n%s' % (sourceFilename, "\n".join(directdeps)))
	
	return directdeps


################################################################################
# Campaign source management
################################################################################

def campaign_getDependencyFilenames(source, sourcePath = None, recursive = False, sourceFilename = "<local>"):
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
	@type  sourceFilename: string
	@param sourceFilename: a string to help identify the file that yielded the source. 
	For non-repository files, use <local>, by convention.
	
	@rtype: list of strings
	@returns: a list of docroot-path to dependencies (no duplicate).
	"""
	
	currentDependencies = []
	
	getLogger().info("%s: parsing campaign file to look for its dependencies" % sourceFilename)

	# The path of the campaign within the docroot.
	path = sourcePath

	# Based on a file parsing.
	indent = 0
	parentPresent = True
	lc = 0
	for line in source.splitlines():
		lc += 1
		# Remove comments
		line = line.split('#', 1)[0].rstrip()
		if not line:
			continue # empty line
		m = re.match(r'(?P<indent>\s*)((?P<branch>\w+|\*)\s+)?(?P<type>\w+)\s+(?P<filename>[^\s]+)(\s+with\s+(?P<mapping>.*)\s*)?', line)
		if not m:
			raise Exception('%s: parse error at line %s: invalid line format' % (sourceFilename, lc))

		type_ = m.group('type')
		filename = m.group('filename')
		indentDiff = len(m.group('indent')) - indent
		indent = indent + indentDiff

		# Filename creation within the docroot
		if filename.startswith('/'):
			# absolute path within the *repository*
			filename = '/%s%s' % (cm.get_transient('constants.repository'), filename)
		else:
			# just add the local campaign path
			filename = '%s/%s' % (path, filename)               

		# Type validation
		if not type_ in [ 'ats', 'campaign' ]:
			raise Exception('%s: error at line %s: invalid job type (%s)' % (sourceFilename, lc, type_))

		# Indentation validation
		if indentDiff > 1:
			raise Exception('%s: parse error at line %s: invalid indentation (too deep)' % (sourceFilename, lc))

		
		elif indentDiff == 1:
			if not parentPresent:
				raise Exception('%s: parse error at line %s: invalid indentation (invalid initial indentation)' % (sourceFilename, lc))

		elif indentDiff == 0:
			# the current parent remains the parent
			pass

		else:
			# negative indentation. 
			pass

		# OK, now we have at least one parent.
		parentPresent = True

		# Branch validation: ignored for dependency resolver

		# Now handle the dependency.
		if not filename in currentDependencies:
			getLogger().info('%s: campaign direct dependency added: %s' % (sourceFilename, filename))
			currentDependencies.append(filename)
			
			if recursive and type_ in ['ats', 'campaign']:
				nextDependencies = []
				nextPath, nextFilename = os.path.split(filename)
				nextSource = FileSystemManager.instance().read(filename)
				if nextSource is None:
					raise Exception('%s: missing dependency: file %s is not in the repository' % (sourceFilename, filename))
				if type_ == 'campaign':
					nextDependencies = campaign_getDependencyFilenames(nextSource, nextPath, True, filename)
				elif type_ == 'ats':
					nextDependencies = python_getDependencyFilenames(nextSource, nextPath, True, filename)
				
				for dep in nextDependencies:
					if not dep in currentDependencies:
						getLogger().info('%s: campaign indirect dependency added: %s' % (sourceFilename, dep))
						currentDependencies.append(dep)
		
	return currentDependencies
		

