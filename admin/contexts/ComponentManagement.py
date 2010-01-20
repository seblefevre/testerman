#!/usr/bin/env python
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
# Component management context for testerman-admin
##


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

	def getFormattedComponentsList(self):
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
		
		return prettyPrintDictList([ 'component', 'version', 'branch', 'archive', 'status' ], ret)

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



##
# Context definition
##

from CiscoCommandShell import *

class Context(CommandContext):
	def __init__(self):
		CommandContext.__init__(self)
		# Deploy command
		node = SequenceNode()
		node.addField("branch", "deployment branch", ChoiceNode().addChoices([("stable", "stable component", NullNode()), ("testing", "testing component", NullNode())]), True)
		node.addField("component", "component name", StringNode())
		node.addField("archive", "path to archive", StringNode())
		node.addField("version", "version to announce", StringNode(), True)
		self.addCommand("deploy", "deploy a new component on server", node, self.deployComponent)
		# List command		
		self.addCommand("list", "list deployed components", NullNode(), self.listComponents)

	def listComponents(self):
		docroot = os.environ.get('TESTERMAN_DOCROOT')

		if not docroot:
			self.error("Sorry, the document root is not set (TESTERMAN_DOCROOT).")
			return

		docroot = os.path.realpath(docroot)
		updateFilename = "%s/updates.xml" % docroot
		umu = UpdateMetadataWrapper(updateFilename)
		self.notify(umu.getFormattedComponentsList())

	def deployComponent(self, component, archive, version = None, branch = ("testing", None)):
		self.notify("Deploying package %s as component %s, version %s, branch %s..." % (archive, component, version, branch[0]))

