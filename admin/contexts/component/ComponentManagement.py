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
# Component management context for testerman-admin:
# publish, unpublish, etc.
#
##


import xml.dom.minidom
import os
import shutil
import sys
import tempfile

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

	def getComponentsList(self):
		"""
		Displays the currently published components and their status.
		"""
		if not fileExists(self._filename):
			raise Exception("Cannot find updates.xml file (%s)" % self._filename)
		
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
		
		return ret

	def isComponentPublished(self, componentName, componentVersion):
		"""
		Returns { 'url', 'branch' } if the component is already published,
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
	
	def publishComponent(self, componentName, componentVersion, componentUrl, componentBranch):
		"""
		Updates the updates.xml file:
		adds a new entry to publish the component,
		or update an existing one, if any.

		Creates a new updates.xml file if needed.
		
		Returns a string status.
		"""
		status = ""
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
				# The current component version already exists - update it
				e.attributes['branch'] = componentBranch
				e.attributes['url'] = componentUrl
				status = "Component %s %s (%s) has been republished successfully" % (componentName, componentVersion, componentBranch)
				updated = True
				break
		
		if not updated:
			# New addition to the metadata (new component or version)
			e = doc.createElement('update')
			e.attributes['version'] = componentVersion
			e.attributes['url'] = componentUrl
			e.attributes['component'] = componentName
			e.attributes['branch'] = componentBranch
			doc.firstChild.appendChild(e)
			status = "Component %s %s (%s) has been published successfully" % (componentName, componentVersion, componentBranch)

		f = open(self._filename, 'w')
		f.write(doc.toprettyxml())
		f.close()
		return status

	def unpublishComponent(self, componentName, componentVersion):
		"""
		Removes a component from the advertised list of components.
		"""
		status = ""
		if not fileExists(self._filename):
			# Nothing to do
			raise Exception("Unable to find updates.xml file (%s)" % self._filename)

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
				status = "Component %s %s (%s) has been unpublished" % (component, version, branch)
				
		f = open(self._filename, 'w')
		f.write(doc.toprettyxml())
		f.close()
		return status

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



##
# Context definition
##

from StructuredInteractiveShell import *


import ComponentPackager

class ComponentContext(CommandContext):
	def __init__(self):
		CommandContext.__init__(self)
		
		branches = EnumNode()
		branches.addChoice("stable", "stable version"),
		branches.addChoice("testing", "testing version")
		branches.addChoice("experimental", "experimental version")
	
		# Publish command
		node = SequenceNode()
		node.addField("branch", "advertised component stability (default: testing)", branches, True)
		node.addField("component", "component name", StringNode())
		node.addField("archive", "path to archive file", StringNode())
		node.addField("version", "advertised version", StringNode())
		self.addCommand("publish", "publish a new component on server", node, self.publishComponent)

		# Source-publish command
		if self.hasSource():
			node = SequenceNode()
			node.addField("branch", "advertised component stability (default: testing)", branches, True)
			# supported source components
			components = EnumNode()
			components.addChoice("qtesterman", "QTesterman client")
			components.addChoice("pyagent", "general purpose python agent")
			node.addField("component", "component name", components)
			node.addField("version", "advertised version", StringNode(), True)
			self.addCommand("source-publish", "publish a new component on server from its source", node, self.publishComponentFromSource)

		# Unpublish command
		node = SequenceNode()
		node.addField("component", "component name to unpublish", StringNode())
		node.addField("version", "version to unpublish", StringNode())
		self.addCommand("unpublish", "unpublish an existing component version", node, self.unpublishComponent)

		# Show command		
		self.addCommand("show", "show published components", NullNode(), self.showComponents)

	def hasSource(self):
		return os.environ.get('TESTERMAN_HOME')

	def _getDocroot(self):
		docroot = os.environ.get('TESTERMAN_DOCROOT')
		if not docroot:
			raise Exception("Sorry, the document root is not set (TESTERMAN_DOCROOT).")
		docroot = os.path.realpath(docroot)
		return docroot
	
	def _getMetadataWrapper(self):
		updateFilename = "%s/updates.xml" % (self._getDocroot())
		return UpdateMetadataWrapper(updateFilename)

	def _copyComponent(self, archiveFilename, docroot, componentName, componentVersion):
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
				raise Exception("Cannot create the updates directory (%s)" % str(e))
		try:
			shutil.copyfile(archiveFilename, dst)
			os.chmod(dst, 0644)
		except Exception, e:
			raise Exception("Cannot copy %s to %s (%s)" % (archiveFilename, dst, str(e)))

		return url

	def showComponents(self):
		metadata = self._getMetadataWrapper()
		rows = metadata.getComponentsList()
		headers = [ ('component', 'Component'), ('version', 'Version'), ('branch', 'Branch'), ('archive', 'Archive File'), ('status', 'Status') ]
		self.printTable(headers, rows, order = 'component')

	def publishComponent(self, component, archive, version, branch = "testing"):
		branch = branch
		self.notify("Publishing package %s as component %s %s (%s)..." % (archive, component, version, branch))
		metadata = self._getMetadataWrapper()

		url = self._copyComponent(archive, self._getDocroot(), component, version)
		if not url:
			raise Exception("Sorry, unable to copy the archive to the docroot updates folder (invalid archive file ?)")

		status = metadata.publishComponent(component, version, url, branch)
		self.notify(status)

	def unpublishComponent(self, component, version):
		self.notify("Unpublishing component %s %s..." % (component, version))
		status = self._getMetadataWrapper().unpublishComponent(component, version)
		self.notify(status)

	def publishComponentFromSource(self, component, version = None, branch = "testing"):
		component = component
		branch = branch

		# Prerequisites
		sourceRoot = os.environ.get('TESTERMAN_HOME')
		if not sourceRoot:
			raise Exception("Sorry, the Testerman source root is not set (TESTERMAN_HOME).")
		
		metadata = self._getMetadataWrapper()

		# Fetch package info		
		componentSourceRoot = "%s/%s" % (sourceRoot, component)
		packageInfo = ComponentPackager.getPackageInfo(componentSourceRoot)
		if not version:
			version = packageInfo["version"]

		# OK, here we go
		self.notify("Publishing component %s %s (%s) from source..." % (component, version, branch))

		# Create the archive		
		archiveFile = tempfile.NamedTemporaryFile(suffix = ".tgz")
		archiveFilename = archiveFile.name
		ComponentPackager.createPackage(sources = packageInfo["sources"], baseDir = packageInfo['component'], excluded = packageInfo['excluded'], filename = archiveFilename)

		# Copy it to the docroot		
		url = self._copyComponent(archiveFilename, self._getDocroot(), component, version)
		if not url:
			raise Exception("Sorry, unable to copy the archive to the updates folder")

		# Update the published metadata
		status = metadata.publishComponent(component, version, url, branch)
		self.notify(status)


