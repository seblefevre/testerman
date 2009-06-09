#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 Sebastien Lefevre and other contributors
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
# Component deployer for Testerman.
# 
# Copy a component file to the repository,
# and update the updates.xml file to make the new
# component available.
#
##

import optparse
import xml.dom.minidom
import os
import shutil
import sys

###############################################################################
# Some usual tools
###############################################################################

def fileExists(filename):
	try:
		os.stat(filename)
		return True
	except:
		return False

def error(txt):
	sys.stdout.write("Error: %s\n" % txt)

def fatal(txt = None, retcode = 1):
	if txt:
		error(txt)
	sys.exit(retcode)

def prettyPrintDictList(header = [], distList = []):
	"""
	Pretty display the list of dict according to the header list.
	Header names not found in the dict are not displayed, and
	only header names found in the dict are displayed.
	
	Header is a list of either simple string (name) or tuple (name, label).
	If it is a tuple, label is used to display the header, and name
	to look for the element in the dicts.
	"""
	def formatLine(cols, widths):
		"""
		Formatting helper: array pretty print.
		"""
		line = "%s%s " % (cols[0], (widths[0]-len(cols[0]))*' ')
		for i in range(1, len(cols)):
			line = line + "| %s%s " % (cols[i], (widths[i]-len(cols[i]))*' ')
		return line

	# First, we compute the max widths for each col
	displayableHeader = []
	width = []
	for h in header:
		try:
			name, label = h
		except:
			label = h
		width.append(len(label))
		displayableHeader.append(label)

	lines = [ ]
	for entry in distList:
		i = 0
		line = []
		for h in header:
			try:
				name, label = h
			except:
				name = h
			if entry.has_key(name):
				e = str(entry[name])
				if len(e) > width[i]: width[i] = len(e)
				line.append(e)
			else:
				line.append('') # element not found for this dict entry
			i += 1
		lines.append(line)

	# Then we can display them
	res = formatLine(displayableHeader, width)
	res +="\n" + '-'*len(res) + "\n"
	for line in lines:
		res += formatLine(line, width) + "\n"
	return res


###############################################################################
# updates.xml updater
###############################################################################

class UpdateMetadataWrapper:
	"""
	A class to manage several actions on the updates.xml
	"""
	def __init__(self, filename):
		self._filename = filename
		self._docroot = os.path.split(self._filename)[0]

	def listComponents(self):
		"""
		Displays the currently deployed components and their status.
		"""
		if not fileExists(self._filename):
			return
		
		f = open(self._filename, 'r')
		content = ''.join([x.strip() for x in f.readlines()])
		f.close()

		ret = []
		
		doc = xml.dom.minidom.parseString(content)
		for e in doc.firstChild.getElementsByTagName('update'):
			version = e.attributes['version'].value
			component = e.attributes['component'].value
			branch = e.attributes['branch'].value
			url = e.attributes['url'].value
			if fileExists('%s%s' % (self._docroot, url)):
				status = 'OK'
			else:
				status = 'Missing archive file'
			ret.append(dict(version = version, component = component, branch = branch, archive = url, status = status))
		
		print prettyPrintDictList([ 'component', 'version', 'branch', 'archive', 'status' ], ret)

	def isComponentDeployed(self, componentName, componentVersion):
		"""
		Returns { 'url', 'branch' } if the component is already deployed,
		or None if not.
		"""
		if not fileExists(self._filename):
			return None
		
		f = open(self._filename, 'r')
		content = ''.join([x.strip() for x in f.readlines()])
		f.close()

		doc = xml.dom.minidom.parseString(content)
		for e in doc.firstChild.getElementsByTagName('update'):
			version = e.attributes['version'].value
			component = e.attributes['component'].value
			branch = e.attributes['branch'].value
			url = e.attributes['url'].value
			if version == componentVersion and component == componentName:
				return dict(url = url, component = component, version = version, branch = branch)
		return None 
	
	def deployComponent(self, componentName, componentVersion, componentUrl, componentBranch):
		"""
		Updates the updates.xml file:
		adds a new entry to deploy the component,
		or update an existing one, if any.

		Creates a new updates.xml file if needed.
		"""
		if not fileExists(self._filename):
			content = '<?xml version="1.0" ?>\n<updates/>\n'

		else:
			f = open(self._filename, 'r')
			content = ''.join([x.strip() for x in f.readlines()])
			f.close()
		
		updated = False

		doc = xml.dom.minidom.parseString(content)
		for e in doc.firstChild.getElementsByTagName('update'):
			version = e.attributes['version'].value
			component = e.attributes['component'].value
			branch = e.attributes['branch'].value
			if version == componentVersion and component == componentName:
				e.attributes['branch'] = componentBranch
				e.attributes['url'] = componentUrl
				print "Component %s %s (%s) has been redeployed successfully" % (component, version, branch)
				updated = True
				break
		
		if not updated:
			e = doc.createElement('update')
			e.attributes['version'] = componentVersion
			e.attributes['url'] = componentUrl
			e.attributes['component'] = componentName
			e.attributes['branch'] = componentBranch
			doc.firstChild.appendChild(e)
			print "Component %s %s (%s) has been deployed successfully" % (componentName, componentVersion, componentBranch)

		f = open(self._filename, 'w')
		f.write(doc.toprettyxml())
		f.close()
		return True

	def undeployComponent(self, componentName, componentVersion):
		"""
		Removes a component from the advertised list of components.
		"""
		if not fileExists(self._filename):
			# Nothing to do
			return False

		f = open(self._filename, 'r')
		content = ''.join([x.strip() for x in f.readlines()])
		f.close()

		doc = xml.dom.minidom.parseString(content)
		for e in doc.firstChild.getElementsByTagName('update'):
			version = e.attributes['version'].value
			component = e.attributes['component'].value
			branch = e.attributes['branch'].value
			if version == componentVersion and component == componentName:
				doc.firstChild.removeChild(e)
				print "Component %s %s (%s) has been undeployed" % (component, version, branch)
				
		f = open(self._filename, 'w')
		f.write(doc.toprettyxml())
		f.close()
		return True

	def updateComponent(self, componentName, componentVersion, toBranch = None, toUrl = None):
		"""
		Updates a component from its current branch to a new branch.
		"""
		if not fileExists(self._filename):
			# Nothing to do
			return False

		f = open(self._filename, 'r')
		content = ''.join([x.strip() for x in f.readlines()])
		f.close()

		doc = xml.dom.minidom.parseString(content)
		for e in doc.firstChild.getElementsByTagName('update'):
			version = e.attributes['version'].value
			component = e.attributes['component'].value
			branch = e.attributes['branch'].value
			url = e.attributes['url'].value
			if version == componentVersion and component == componentName:
				if toBranch:
					e.attributes['branch'] = toBranch
					print "Component %s %s switched from %s to %s" % (component, version, branch, toBranch)
				if toUrl:
					e.attributes['url'] = toUrl
					print "Component %s %s updated, now serving %s" % (component, version, toUrl)
				
		f = open(self._filename, 'w')
		f.write(doc.toprettyxml())
		f.close()
		return True


###############################################################################
# Component deployment
###############################################################################

def copyComponent(archiveFilename, docroot, componentName, componentVersion):
	"""
	Copies a component archive to the docroot/updates/<componentName>-<componentVersion>,
	making directories on the fly if needed.
	
	@rtype: string
	@returns: the "url" of the file to reference in
	          the updates.xml file (docroot-path to the file)
	"""
	docroot = os.path.realpath(docroot)
	archiveFilename = os.path.realpath(archiveFilename)
	
	url = "/updates/%s-%s%s" % (componentName, componentVersion, os.path.splitext(archiveFilename)[1])
	dst = "%s%s" % (docroot, url)

	updateDir = os.path.split(dst)[0]
	if not fileExists(updateDir):
		try:
			os.makedirs(updateDir, 0755)
		except Exception, e:
			print sys.stderr << "Cannot create the updates directory (%s)" % str(e)
			return None

	try:
		shutil.copyfile(archiveFilename, dst)
		os.chmod(dst, 0644)
	except Exception, e:
		error("Cannot copy %s to %s (%s)" % (archiveFilename, dst, str(e)))
		return None
	 
	return url

def deployComponent():
	parser = optparse.OptionParser(version = "Testerman Component Deployer")
	parser.add_option("-r", dest = "docroot", metavar = "DOCROOT", help = "the path to the Testerman document root (mandatory)", default = os.environ.get('TESTERMAN_DOCROOT', None))
	parser.add_option("-c", "--component", dest = "name", metavar = "NAME", help = "the name of the component to deploy (mandatory)", default = None)
	parser.add_option("-v", dest = "version", metavar = "VERSION", help = "the component version to advertise (mandatory)", default = None)
	parser.add_option("-a", "--archive", dest = "filename", metavar = "FILENAME", help = "the archive to deploy (mandatory)", default = None)
	parser.add_option("-b", "--branch", dest = "branch", metavar = "BRANCH", help = "the deployment branch (default: %default)", default = "testing")
	(options, args) = parser.parse_args()
	
	if not options.name:
		fatal("missing component name.")
	if not options.version:
		fatal("missing component version.")
	if not options.docroot:
		fatal("missing document root.")
	if not options.filename:
		fatal("missing archive filename.")

	options.docroot = os.path.realpath(options.docroot)
	updateFilename = "%s/updates.xml" % options.docroot
	umu = UpdateMetadataWrapper(updateFilename)
	url = copyComponent(options.filename, options.docroot, options.name, options.version)
	if not url:
		fatal()
	
	umu.deployComponent(options.name, options.version, url, options.branch)


###############################################################################
# Component undeployment
###############################################################################

def undeployComponent():
	parser = optparse.OptionParser(version = "Testerman Component Undeployer")
	parser.add_option("-r", dest = "docroot", metavar = "DOCROOT", help = "the path to the Testerman document root (mandatory)", default = os.environ.get('TESTERMAN_DOCROOT', None))
	parser.add_option("-c", "--component", dest = "name", metavar = "NAME", help = "the name of the component to undeploy (mandatory)", default = None)
	parser.add_option("-v", dest = "version", metavar = "VERSION", help = "the component version to undeploy (mandatory)", default = None)
	(options, args) = parser.parse_args()
	
	if not options.name:
		fatal("missing component name.")
	if not options.version:
		fatal("missing component version.")
	if not options.docroot:
		fatal("missing document root.")

	options.docroot = os.path.realpath(options.docroot)
	updateFilename = "%s/updates.xml" % options.docroot
	umu = UpdateMetadataWrapper(updateFilename)
	umu.undeployComponent(options.name, options.version)


###############################################################################
# Component branch switcher
###############################################################################

def updateComponent():
	parser = optparse.OptionParser(version = "Testerman Component Branch Switcher")
	parser.add_option("-r", dest = "docroot", metavar = "DOCROOT", help = "the path to the Testerman document root (mandatory)", default = os.environ.get('TESTERMAN_DOCROOT', None))
	parser.add_option("-c", "--component", dest = "name", metavar = "NAME", help = "the name of the component (mandatory)", default = None)
	parser.add_option("-v", dest = "version", metavar = "VERSION", help = "the component version (mandatory)", default = None)
	parser.add_option("-b", "--to-branch", dest = "toBranch", metavar = "BRANCH", help = "the branch the component should be switched to (mandatory)", default = None)
	(options, args) = parser.parse_args()
	
	if not options.name:
		fatal("missing component name.")
	if not options.version:
		fatal("missing component version.")
	if not options.toBranch:
		fatal("missing target branch.")
	if not options.docroot:
		fatal("missing document root.")

	options.docroot = os.path.realpath(options.docroot)
	updateFilename = "%s/updates.xml" % options.docroot
	umu = UpdateMetadataWrapper(updateFilename)
	umu.updateComponent(options.name, options.version, options.toBranch)

	
###############################################################################
# Component list
###############################################################################

def listComponents():
	parser = optparse.OptionParser(version = "Testerman Component Lister")
	parser.add_option("-r", dest = "docroot", metavar = "DOCROOT", help = "the path to the Testerman document root (mandatory)", default = os.environ.get('TESTERMAN_DOCROOT', None))
	(options, args) = parser.parse_args()
	
	if not options.docroot:
		fatal("missing document root.")

	options.docroot = os.path.realpath(options.docroot)
	updateFilename = "%s/updates.xml" % options.docroot
	umu = UpdateMetadataWrapper(updateFilename)
	umu.listComponents()
	

###############################################################################
# Main action switch
###############################################################################

def usage():
	print """Testerman Component Manager

Usage: %s [action] [options]
Where action is:

  deploy          deploy or redeploy a component
  list            list currently deployed components
  undeploy        undeploy a component
  update          update a deployed component branch

Use -h or --help after the action flag to get
additional help, for instance:

  %s deploy --help

All actions require a Testerman doc root to be provided.
You may specify it with -r or by setting the TESTERMAN_DOCROOT
environment variable.
""" % (sys.argv[0], sys.argv[0])


def main():
	if len(sys.argv) < 2 or not sys.argv[1] in [ 'deploy', 'undeploy', 'update', 'list' ]:
		usage()
		sys.exit(2)
	
	# Pop the action parameter
	action = sys.argv[1]
	del sys.argv[1]

	if action == 'deploy':
		deployComponent()
	elif action == 'undeploy':
		undeployComponent()
	elif action == 'update':
		updateComponent()
	elif action == 'list':
		listComponents()
	else:
		usage()
		sys.exit(2)

if __name__ == '__main__':
	main()
	
		
