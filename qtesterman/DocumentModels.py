# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009,2010 QTesterman contributors
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
# Basic Document model (used in multiple views).
#
# Also include specialized classes ({Module,Ats,Campaign,PackageDescription}Model, etc)
#
# Each model is responsible for encoding/decoding their content to/from the storage
# format.
# The loader/savers (provided by the associated Document Editors)
# simply pass the data as read from the storage location. Consider this is a
# simple 8-bit buffer, as string.
# So, conversion from/to utf-8, if applicable, must be performed by the models themselves.
#
##

from PyQt4.Qt import *
from PyQt4.QtXml import *

from Base import *

import re

# 'Application' Document types
# These type values are those returned by a Ws.getDirectoryListing()
# by the server.
TYPE_ATS = 'ats'
TYPE_MODULE = 'module'
TYPE_CAMPAIGN = 'campaign'
TYPE_PACKAGE_METADATA = 'package-metadata'
TYPE_PROFILE = 'profile'

###############################################################################
# DocumentModel registrations
###############################################################################

DocumentModelClasses = []

def registerDocumentModelClass(fileFilter, documentModelClass):
	"""
	Registers a model class as the one to be used to open a file
	whose filename matches the fileFilter regexp.
	
	TODO: we should base our registration on application type, not
	filename...
	"""
	global DocumentModelClasses
	DocumentModelClasses.append({'filter': fileFilter, 'class': documentModelClass})

def getDocumentModelClass(filename):
	"""
	For a given filename, returns the first document model whose file type support matches.
	"""
	for d in DocumentModelClasses:
		if re.match(d['filter'], filename):
			return d['class']
	return None		


###############################################################################
# Model Base
###############################################################################

class MetadataModel(QObject):
	"""
	A Metadata model is a sub-model of a DocumentModel.

	It manages all the metadata-related stuff for a body.
	Body (unicode) + MetadataModel composes a DocumentModel.

	This Metadata model is initialized with a unicode string containing a valid Testerman XML metadata description.
	It provides several functions to manage the data without dealing with the actual XML,
	and a serialization function to retrieve the corresponding XML string for document serialization.

	The metada model itself exposes:
	- the metadata model (R/W/Notify): unicode string ; getMetadata, setMetadata, SIGNAL(metadataUpdated())

	and convenience functions to hide the XML backend:
	- get/setParameters (dict[name] of dict of unicode strings { 'type', 'previous-value', 'default', 'description'} )
	- get/setParameter
	- get/setDescription (unicode string)
	- get/setPrerequisites (unicode string)

	"""
	def __init__(self, metadataSource = None):
		QObject.__init__(self)

		# The (default) model
		#: unicode string
		self.prerequisites = None
		#: unicode string
		self.description = None
		# : unicode string
		self.languageApi = None
		#: document parameters (ATS variables). Indexed by a unicode name, contain dicts[string] of unicode
		self.parameters = {}
		#: execution groups. Indexed by a unicode name, contain dict[string] of unicode
		self.groups = {}

		# For heavy modifications, we allow to disable the model notification mechanism.
		# In this case, use:
		# model.disableUpdateNotifications()
		# ... <heavy modifications>
		# model.enableUpdateNotifications()
		# model.notifyUpdate()
		self.notificationDisabled = False

		# Modification flag since the last setMetadata()
		self.modified = False

		if metadataSource is not None:
			self.setMetadataSource(metadataSource)
			self.modified = False

	def resetModificationFlag(self):
		"""
		To call once modifications have been saved
		"""
		self.setModified(False, force = True)

	def setModified(self, modified, force = False):
		"""
		Updates the modified state from true to false only if force is set.
		"""
		if modified:
			self.notifyUpdate()
		if modified != self.modified:
			if modified or force:
				self.modified = modified
				self.emit(SIGNAL('modificationChanged(bool)'), self.modified)

	def notifyUpdate(self):
		if not self.notificationDisabled:
			self.emit(SIGNAL('metadataUpdated()'))

	def disableUpdateNotifications(self):
		self.notificationDisabled = True

	def enableUpdateNotifications(self):
		self.notificationDisabled = False

	def isModified(self):
		return self.modified

	def setMetadataSource(self, metadataSource):
		"""
		loads XML metadata into the model.

		@type  metadataSource: buffer string
		@param metadataSource: valid (encoded) XML content, compliant with Testerman metadata schema

		@rtype: None
		@returns: None
		"""
		# First we clear the model
		self.prerequisites = u''
		self.description = u''
		self.languageApi = '1' # this is the default value when not provided.
		self.parameters = {}
		
		# Parse into a DOM document
		metadataDoc = QDomDocument()
		(res, errorMessage, errorLine, errorColumn) = metadataDoc.setContent(metadataSource, False)
		
		if not res:
			raise Exception("Invalid metadata: %s (line %d, column %d)" % (unicode(errorMessage), errorLine, errorColumn))

		# Now we fill our internal model representation
		version = metadataDoc.documentElement().attribute('version')
		# according to the version, we may fill our internal representation differently.
		# for now, only version 1.0 (or no version) is supported.
		if not version.isNull() and version != "1.0":
			raise Exception("Unsupported metadata version %s" % version)
		
		element = metadataDoc.documentElement().firstChildElement('prerequisites')
		if not element.isNull():
			self.prerequisites = unicode(element.text())
		element = metadataDoc.documentElement().firstChildElement('description')
		if not element.isNull():
			self.description = unicode(element.text())
		element = metadataDoc.documentElement().firstChildElement('api')
		if not element.isNull():
			self.languageApi = unicode(element.text())

		# Parameters
		parameters = metadataDoc.documentElement().firstChildElement('parameters')
		if not parameters.isNull():
			parameter = parameters.firstChildElement('parameter')
			while not parameter.isNull():
				self.parameters[unicode(parameter.attribute('name'))] = {
					'default': unicode(parameter.attribute('default')),
					'type': unicode(parameter.attribute('type')),
					'description': unicode(parameter.text()),
					'name': unicode(parameter.attribute('name'))
				}

				parameter = parameter.nextSiblingElement()

		# Groups
		groups = metadataDoc.documentElement().firstChildElement('groups')
		if not groups.isNull():
			group = groups.firstChildElement('group')
			while not group.isNull():
				self.groups[unicode(group.attribute('name'))] = {
					'description': unicode(group.text()),
					'name': unicode(group.attribute('name'))
				}

				group = group.nextSiblingElement()

		self.setModified(True)
		
		log(u"Metadata set: " + unicode(self))

	def __str__(self):
		ret = u"Metadata:\n"
		ret += u"prerequisites: %s\n" % self.prerequisites
		ret += u"description: %s\n" % self.description
#		ret += u"parameters: %s\n" % str(self.parameters)
		return ret

	def getMetadataSource(self):
		"""
		Serializes the model to XML.

		<?xml version="1.0" encoding="utf-8"?>
		<metadata version="1.0">
			<description><![CDATA[description]]></description>
			<prerequisites><![CDATA[prerequisites]]></prerequisites>
			<language-mode></language-mode>
			<parameters>
				<parameter name="PX_PARAM1" default="defaultValue01" type="string"><![CDATA[description]]></parameter>
			</parameters>
			<groups>
				<group name="GX_GROUP1"><![CDATA[description]]></group>
			</groups>
		</meta>'

		@rtype: buffer string
		@returns: the metadata serialized as a utf-8 encoded XML string
		"""
		# Manual XML encoding.
		res =  u'<?xml version="1.0" encoding="utf-8" ?>\n'
		res += u'<metadata version="1.0">\n'
		res += u'<description>%s</description>\n' % Qt.escape(self.description) # This replacement enables to correcly read \n from the XML (when reloaded)
		res += u'<prerequisites>%s</prerequisites>\n' % Qt.escape(self.prerequisites)
		res += u'<api>%s</api>\n' % Qt.escape(self.languageApi)
		res += u'<parameters>\n'
		for (name, p) in self.parameters.items():
			# We must escape the values (to avoid ", etc)
			res += u'<parameter name="%s" default="%s" type="%s"><![CDATA[%s]]></parameter>\n' % (Qt.escape(name), Qt.escape(p['default']), Qt.escape(p['type']), p['description'].replace('\n', '&cr;'))
		res += u'</parameters>\n'
		res += u'<groups>\n'
		for (name, p) in self.groups.items():
			# We must escape the values (to avoid ", etc)
			res += u'<group name="%s"><![CDATA[%s]]></group>\n' % (Qt.escape(name), p['description'].replace('\n', '&cr;'))
		res += u'</groups>\n'
		res += u'</metadata>\n'
		return res.encode('utf-8')

	def getParameter(self, name):
		"""
		Gets a parameter's attributes.

		@type  name: unicode string
		@param name: the name of the parameter

		@rtype: dict[unicode] of unicode
		@returns: { 'default', 'type', 'description', 'name' } or None if the parameter does not exist.
		"""
		ret = {}
		if self.parameters.has_key(name):
			# returns a copy
			for k, v in self.parameters[name].items():
				ret[k] = v
			return ret
		return None

	def setParameter(self, name, default = None, description = None, newName = None):
		"""
		Sets a parameter or selected parameter attributes.
		Adds it if name does not exists.
		If newName is provided, rename the parameter (or create it with newName directly if it does not exist)

		Keeps attributes that are set to None. For new parameters with None attributes, uses an empty default value.
		"""
		# "batch parameter modification" - do not send a metadataUpdate() signal for each field
		modified = self._addParameter(name)
		modified = modified or self._updateParameterAttribute(name, "default", default)
		modified = modified or self._updateParameterAttribute(name, "description", description)
		modified = modified or self._updateParameterAttribute(name, "name", newName)
		self.setModified(modified)

	def addParameter(self, name, default = None, description = None, type_ = None):
		"""
		Adds a new parameter.
		Automatically adjusts its name to match the convention and avoid collisions.
		Returns the name of the added parameter.
		"""
		name = name.upper().replace(' ', '_')
		if not name.startswith('PX_'):
			name = 'PX_' + name
		name = self.getNewParameterName(name)
		
		if not self._addParameter(name):
			return None
		
		self._updateParameterAttribute(name, "default", default)
		self._updateParameterAttribute(name, "description", description)
		self._updateParameterAttribute(name, "type", type_)
		self.setModified(True)
		return name

	def _addParameter(self, name):
		"""
		Registers a new parameter. Returns True if the model was modified.
		"""
		name = name.upper().replace(' ', '_')
		if not name.startswith('PX_'):
			name = 'PX_' + name
		if not self.parameters.has_key(name):
			self.parameters[name] = { 'name': name, 'type': 'string', 'default': '', 'description': '' }
			return True
		return False

	def _updateParameterAttribute(self, name, attribute, value):
		"""
		Updates a single field/attribute for a particular parameter.
		"""
		modified = False
		if not self.parameters.has_key(name):
			return False
		
		if value is None:
			return False

		# We are renaming the parameter
		if attribute == 'name':
			# Adjust the name to something valid
			value = value.upper().replace(' ', '_')
			if not value.startswith('PX_'):
				value = 'PX_' + value
			if name != value:
				# we are renaming the parameter
				# Check if we are not renaming to another existing parameter
				value = self.getNewParameterName(value)
				# OK, we can rename to a new (possibly adjusted) name
				parameter = self.parameters[name]
				parameter['name'] = value
				del self.parameters[name]
				self.parameters[value] = parameter
				modified = True
			else:
				# This is a no-op. We did not changed the name
				pass

		elif self.parameters[name][attribute] != value:
			self.parameters[name][attribute] = value
			modified = True
		
		return modified
		
	def updateParameterAttribute(self, name, attribute, value):
		"""
		Updates a single field/attribute for a particular parameter.
		"""
		modified = self._updateParameterAttribute(name, attribute, value)
		self.setModified(modified)

	def deleteParameters(self, names):
		"""
		Deletes a list of parameters, emit an updated signal at the end
		if at least one parameter was actually removed.
		"""
		modified = False
		for name in names:
			if name in self.parameters:
				del self.parameters[name]
				modified = True
		self.setModified(modified)

	def getParameters(self):
		# Warning: be sure that the caller copy this if it wants to modify it.
		return self.parameters

	def getNewParameterName(self, name):
		"""
		Makes sure to get a new parameter name that is not in use currently.
		If baseName is available, returns it.
		If not, tries baseName_%2.2d starting at 1 until something is found.
		Tries to autodetect a numbering; if found, use it to select the next item if the name currently exists.

		@type  baseName: unicode string
		@param baseName: the baseName to check

		@rtype: unicode string
		@returns: a parameter name that is not in used for now.
		"""
		# Pattern autodetection: look for somethingN where N are digits.
		digits = ''
		i = len(name) - 1
		while (name[i] in "1234567890") and i >= 0:
			digits = name[i] + digits
			i -= 1

		padding = 2
		baseName = name
		index = 1
		try:
			if len(digits) > 0:
				index = int(digits)
				baseName = name[:i+1]
				padding = len(digits)
		except:
			pass

		format = u"%%s%%%d.%dd" % (padding, padding)
		while self.parameters.has_key(name):
			name = format % (baseName, index)
			index += 1
		return name

	def removeParameter(self, name):
		if self.parameters.has_key(name):
			del self.parameters[name]
			self.setModified(True)
			return True
		return False

	def setDescription(self, description):
		"""
		Sets the description.

		@type  description: unicode string
		@param description: the script description
		
		@rtype: None
		@returns: None
		"""
		# Make sure this is unicode.
		self.description = unicode(description)
		self.setModified(True)

	def setLanguageApi(self, l):
		self.languageApi = unicode(l)
		self.setModified(True)

	def getLanguageApi(self):
		return self.languageApi

	def getDescription(self):
		"""
		Gets the script description.
		
		@rtype: unicode string
		@returns: the script description
		"""
		return self.description

	def setPrerequisites(self, prerequisites):
		"""
		Sets the prerequisites.

		@type  prerequisites: unicode string
		@param prerequisites: the script description
		
		@rtype: None
		@returns: None
		"""
		# Make sure this is unicode.
		self.prerequisites = unicode(prerequisites)
		self.setModified(True)

	def getPrerequisites(self):
		"""
		Gets the script prerequisites.
		
		@rtype: unicode string
		@returns: the script prerequisites
		"""
		return self.prerequisites

	def getGroup(self, name):
		"""
		Gets a group's attributes.

		@type  name: unicode string
		@param name: the name of the group

		@rtype: dict[unicode] of unicode
		@returns: { 'description', 'name' } or None if the group does not exist.
		"""
		ret = {}
		if self.groups.has_key(name):
			# returns a copy
			for k, v in self.groups[name].items():
				ret[k] = v
			return ret
		return None

	def setGroup(self, name, description = None, newName = None):
		"""
		Sets a group or selected group attributes.
		Adds it if name does not exists.
		If newName is provided, rename the group (or create it with newName directly if it does not exist)

		Keeps attributes that are set to None. For new groups with None attributes, uses an empty default value.
		"""
		# "batch group modification" - do not send a metadataUpdate() signal for each field
		modified = self._addGroup(name)
		modified = modified or self._updateGroupAttribute(name, "description", description)
		modified = modified or self._updateGroupAttribute(name, "name", newName)
		self.setModified(modified)

	def addGroup(self, name, description = None):
		"""
		Adds a new group.
		Automatically adjusts its name to match the convention and avoid collisions.
		Returns the name of the added group.
		"""
		name = name.upper().replace(' ', '_')
		if not name.startswith('GX_'):
			name = 'GX_' + name
		name = self.getNewGroupName(name)
		
		if not self._addGroup(name):
			return None
		
		self._updateGroupAttribute(name, "description", description)
		self.setModified(True)
		return name

	def _addGroup(self, name):
		"""
		Registers a new group. Returns True if the model was modified.
		"""
		name = name.upper().replace(' ', '_')
		if not name.startswith('GX_'):
			name = 'GX_' + name
		if not self.groups.has_key(name):
			self.groups[name] = { 'name': name, 'description': '' }
			return True
		return False

	def _updateGroupAttribute(self, name, attribute, value):
		"""
		Updates a single field/attribute for a particular group.
		"""
		modified = False
		if not self.groups.has_key(name):
			return False
		
		if value is None:
			return False

		# We are renaming the group
		if attribute == 'name':
			# Adjust the name to something valid
			value = value.upper().replace(' ', '_')
			if not value.startswith('GX_'):
				value = 'GX_' + value
			if name != value:
				# we are renaming the group
				# Check if we are not renaming to another existing group
				value = self.getNewGroupName(value)
				# OK, we can rename to a new (possibly adjusted) name
				group = self.groups[name]
				group['name'] = value
				del self.groups[name]
				self.groups[value] = group
				modified = True
			else:
				# This is a no-op. We did not changed the name
				pass

		elif self.groups[name][attribute] != value:
			self.groups[name][attribute] = value
			modified = True
		
		return modified
		
	def updateGroupAttribute(self, name, attribute, value):
		"""
		Updates a single field/attribute for a particular group.
		"""
		modified = self._updateGroupAttribute(name, attribute, value)
		self.setModified(modified)

	def deleteGroups(self, names):
		"""
		Deletes a list of groups, emit an updated signal at the end
		if at least one group was actually removed.
		"""
		modified = False
		for name in names:
			if name in self.groups:
				del self.groups[name]
				modified = True
		self.setModified(modified)

	def getGroups(self):
		# Warning: be sure that the caller copy this if it wants to modify it.
		return self.groups

	def getNewGroupName(self, name):
		"""
		Makes sure to get a new group name that is not in use currently.
		If baseName is available, returns it.
		If not, tries baseName_%2.2d starting at 1 until something is found.
		Tries to autodetect a numbering; if found, use it to select the next item if the name currently exists.

		@type  baseName: unicode string
		@param baseName: the baseName to check

		@rtype: unicode string
		@returns: a group name that is not in used for now.
		"""
		# Pattern autodetection: look for somethingN where N are digits.
		digits = ''
		i = len(name) - 1
		while (name[i] in "1234567890") and i >= 0:
			digits = name[i] + digits
			i -= 1

		padding = 2
		baseName = name
		index = 1
		try:
			if len(digits) > 0:
				index = int(digits)
				baseName = name[:i+1]
				padding = len(digits)
		except:
			pass

		format = u"%%s%%%d.%dd" % (padding, padding)
		while self.groups.has_key(name):
			name = format % (baseName, index)
			index += 1
		return name

	def removeGroup(self, name):
		if self.groups.has_key(name):
			del self.groups[name]
			self.setModified(True)
			return True
		return False



class DocumentModel(QObject):
	"""
	Document Model base class.
	
	Contains a body aspect and an optional metadata aspect.

	You may set/get metadata & body.
	You may get the complete document.

	The Document Model is initialized with a source document, as stored/persisted on disk.
	This source is split by an overridable method _join() into a metadata source (encoded xml string) and a body model.
	The body model type depends on the document model (QString for ATS, Campaign, Module, QDomElement for package description).
	
	The metadata source is then turned into a MetadataModel object.

	Upon initialization, the document is parsed and exposed through multiple, differents aspects:
	The model aspects:
		- the medatadata model (R/W/Notify): MetadataModel ; getMetadataModel, setMetadataModel, SIGNAL(metadataUpdated())
		- the body model (R/W/Notify): <depends on the DocumentModel impl> ; getBodyModel, setBodyModel, SIGNAL(bodyUpdated())
	The raw document, if you don't want to work with one of its aspects:
		- the document source (R/W/Notify): buffer string ; getDocumentSource, setDocumentSource, SIGNAL(documentReplaced())

	When modifying a single aspect of the model, documentReplaced() won't be fired.
	When replacing the complete document at once (with setDocumentSource), this fires all aspect updates (medataUpdated, bodyUpdated)
	and an additional documentReplaced().
	
	In subclasses,
	typically implements _split(), _join()
	and call setFileExtension() and setDocumentType() from the constructor.
	"""
	def __init__(self):
		QObject.__init__(self)
		# The testerman application type of the document.
		self._documentType = None
		# The default file extension for this type of document.
		self._fileExtension = ""
		# The optional metadata (sub) model
		self._metadataModel = None
		# The body aspect of the document (generally unicode, but actually any object)
		self._bodyModel = None
		
		# These Document attributes are updated whenever the file is actually saved to a location.
		#: QUrl
		self._url = None
		# This timestamp is the reference timestamp of the doc when retrieved from the server.
		# If we put this doc into the repository, if the file was updated in the meanwhile,
		# we'll get a warning ("optimistic locking" concurrency management model)
		self._savedTimestamp = 0

		# Modification status
		# We manage the body part directly
		self._bodyModelModified = False
		# But the metadata part is managed by the sub model.
		# modified is the current modification status according to both body and metadata status.
		self._modified = False
		
	def onMetadataUpdated(self):
		log("DEBUG: forwarding metadataUpdated signal")
		self.emit(SIGNAL('metadataUpdated()'))

	def onMetadataModificationChanged(self, modified):
		# If the body has been modified, the document status stays to "modified".
		if self._bodyModelModified:
			log("DEBUG: onMetadataModificationChanged, %s, not taken into account, body modified (local status: %s)" % (str(modified), str(self._modified)))
			return
		# If the body has not been modified, then we can have a look to the metadata.
		# Only taken into account if it changes our local status.
		if modified != self._modified:
			log("DEBUG: onMetadataModificationChanged, %s" % str(modified))
			self._modified = modified
			self.emit(SIGNAL('modificationChanged(bool)'), self._modified)

	def onBodyModificationChanged(self, modified):
		# If the metadata has been modified, the document status stays to "modified".
		if self._metadataModel and self._metadataModel.isModified():
			log("DEBUG: onBodyModificationChanged, %s, not taken into account, metadata modified (local status: %s)" % (str(modified), str(self._modified)))
			return
		# If the body has not been modified, then we can have a look to the metadata.
		# Only taken into account if it changes our local status.
		if modified != self._modified:
			log("DEBUG: onBodyModificationChanged, %s" % str(modified))
			self._modified = modified
			self._bodyModelModified = modified
			self.emit(SIGNAL('modificationChanged(bool)'), self._modified)

	def resetModificationFlag(self):
		"""
		To call once modifications have been saved.
		"""
		self._modified = False
		self._bodyModelModified = False
		if self._metadataModel:
			self._metadataModel.resetModificationFlag()
		self.emit(SIGNAL('modificationChanged(bool)'), self._modified)

	def isModified(self):
		return self._bodyModelModified or ((self._metadataModel is not None) and self._metadataModel.isModified()) # Should be equals to self.modified at any time, normally.

	def getDocumentType(self):
		return self._documentType
	
	def setDocumentType(self, documentType):
		self._documentType = documentType

	def getTimestamp(self):
		return self._savedTimestamp

	def isRemote(self):
		if not self._url:
			return False
		return (self._url.scheme() == "testerman")

	def getUrl(self):
		"""
		Returns the URL corresponding to the file, according to its type, etc.
		
		Returns None if the document was never saved before, and this has no URL yet.
		
		@rtype: QUrl, or None
		@returns: the last saved URL, if any, or None otherwise.
		"""
		return self._url
	
	def getName(self):
		"""
		Returns the document name.
		This is extracted from the URL, depending on the scheme.
		For remote documents, this is the effective path, i.e. the path minus the /repository/ prefix.
		For local documents, this is the filename without path followed by (local).
		For unsaved documents, this is the document name followed by (local).
		
		@rtype: QString
		@returns: the name of the document.
		"""
		if self._url:
			if self._url.scheme() == 'testerman':
				return QString(self._url.path()[len('/repository/'):])
			else:
				return QString("%s (local)" % self._url.path().split('/')[-1])
		else:
			return None
	
	def getShortName(self):
		return self.getName().split('/')[-1]
	
	def setSavedAttributes(self, url, timestamp):
		"""
		@type  url: QUrl
		@param url: the url the document as been saved as
		@type  timestamp: float
		@param timestamp: the datetime of the last save
		"""
		self._url = url
		self._savedTimestamp = timestamp
		self.emit(SIGNAL('urlUpdated()'))

	def getFileExtension(self):
		"""
		Returns the associated file extension (py, ats, campaign).
		@rtype: string
		@returns: the file extension, corresponding to the document model type.
		"""
		return self._fileExtension
	
	def setFileExtension(self, extension):
		self._fileExtension = extension
	
	def getDocumentSource(self):
		"""
		Returns the complete serialized document, incuding metadata, according to the currently known model.
		Ready to be stored as is.

		@rtype: buffer string
		@returns: the complete document underlying the model
		"""
		if self._metadataModel:
			metadataSource = self._metadataModel.getMetadataSource()
		else:
			metadataSource = None
		return self._join(metadataSource, self._bodyModel)

	def setDocumentSource(self, documentSource):
		"""
		Replace the initial document with a new one.
		@type  documentSource: buffer string
		@param documentSource: the source of the document to expose through the model

		@rtype: None
		@returns: None
		"""
		if self._metadataModel:
			# Disconnect signals
			self.disconnect(self._metadataModel, SIGNAL('metadataUpdated()'), self.onMetadataUpdated)
			self.disconnect(self._metadataModel, SIGNAL('modificationChanged(bool)'), self.onMetadataModificationChanged)
			self._metadataModel = None
		
		log("Replacing document in Model")

		(metadataSource, self._bodyModel) = self._split(documentSource)
		if metadataSource is not None:
			self._metadataModel = MetadataModel(metadataSource)
		self.emit(SIGNAL('metadataUpdated()'))
		self.emit(SIGNAL('bodyUpdated()'))
		self.emit(SIGNAL('documentReplaced()'))

		# We act as a proxy for the metadata sub-model,
		# i.e. we reemit a local signal whenever we have a modification here.
		if self._metadataModel:
			# Reconnect signals
			self.connect(self._metadataModel, SIGNAL('metadataUpdated()'), self.onMetadataUpdated)
			self.connect(self._metadataModel, SIGNAL('modificationChanged(bool)'), self.onMetadataModificationChanged)
		
		self.onDocumentSourceSet()
	
	def onDocumentSourceSet(self):
		"""
		Reimplement this function to do something particular 
		once the document has been set (and split),
		i.e. self._bodyModel and self._metadataModel are available.
		"""
		pass

	def getMetadataModel(self):
		"""
		Returns the metadata sub-model.

		@rtype: MetadataModel, or None
		@returns: the medata model for the document, if any.
		"""
		return self._metadataModel

	def setBodyModel(self, bodyModel):
		"""
		Sets the body (model) aspect of the model.
		@type  body: object (usually a unicode string, depending on the document model)
		@param body: the body

		@rtype: None
		@returns: None
		"""
		self._bodyModel = bodyModel
		self.emit(SIGNAL('bodyUpdated()'))
		self.emit(SIGNAL('modificationChanged(bool)'), self.isModified())

	def getBodyModel(self):
		"""
		Gets the body aspect of the model.

		@rtype: object (usually a unicode string, depending on the document model)
		@returns: the body (model) of the document.
		"""
		return self._bodyModel

	def _split(self, documentSource):
		"""
		To reimplement.
		
		Splits a document source into
		a body part and a metadata source part.
		
		The default implementation only returns a body part.
		
		@type  documentSource: buffer string (utf-8 or anything, as read from the source file)
		@param documentSource: the document source
		
		@rtype: (buffer string, object)
		@returns: a tuple (metadata source, body model)
		If the medata source is not None, a MetadaModel() is built upon it.
		"""
		metadataSource = None
		bodyModel = documentSource
		return (metadataSource, bodyModel)

	def _join(self, metadataSource, bodyModel):
		"""
		To reimplement.
		
		Creates a document source object ready to be saved to a file,
		serializing the metadata and the body together.
		
		The default implementation returns the body as is.
		
		@type  body: object, depending on what _split() returned
		@param body: the document model's body
		@type  metadataSource: buffer string
		@param metadataSource: the XML-serialized metadata for this model
		
		@rtype: object, usually string (utf-8 or anything)
		@returns: a document buffer to dump to a file containing both the body and the medatata.
		"""
		return bodyModel


class PythonDocumentModel(DocumentModel):
	"""
	A Document model composed of a body and an optional metadata sub-model.
	
	The body model is a unicode string.
	
	This model is persisted/stored as a utf-8 string.

	Used as a base class for ModuleModel and AtsModel.
	"""
	def __init__(self, defaultMetadataSource = ""):
		"""
		@type  defaultMetadataSource: unicode string
		@param defaultMetadataSource: a default metadata source (xml string) for
		documents that do not have any metadata in it (including empty documents).
		"""
		DocumentModel.__init__(self)
		# Let's split our document into a body and metadata raw data
		# (unicode strings)
		self._defaultMetadataSource = defaultMetadataSource
	
	def _split(self, documentSource):
		"""
		Reimplemented from DocumentModel for Python-based documents.
		
		The metadata source is stored as comments at the start of the 
		document source.
		
		The body is the remaining part of the file, as a unicode string.
		
		Returns a tuple (metadata, body), extracting the metadata from the body of the module.
		
		the document must starts with a line # __METADATA__BEGIN__,
		then contains commented lines (starting with a #) containing the metadata in xml format,
		then a # __METADATA__END__ line
		After that, this is the document body.

		@type  document: buffer string
		@param document: the complete document source (as utf-8)
		
		@rtype: tuple (buffer string, QString)
		@returns: a tuple corresponding to the (metadataSource, bodyModel) document model aspects.
		"""
		lines = documentSource.split('\n')
		if not len(lines):
			return (self._defaultMetadataSource, QString(documentSource.decode('utf-8')))
		if not lines[0].startswith('# __METADATA__BEGIN__'):
			return (self._defaultMetadataSource, QString(documentSource.decode('utf-8')))

		completed = 0
		metadataLines = [ lines[1] ]
		index = 2
		for l in lines[2:]:
			if not len(l):
				index += 1
				break

			if l.startswith('# __METADATA__END__'):
				index += 1
				completed = 1
				break

			if l[0] != '#':
				break

			metadataLines.append(l)
			index += 1

		if not completed:
			return (self._defaultMetadataSource, QString(documentSource.decode('utf-8')))

		# OK, we have valid metadata.
		metadataSource = ""
		for l in metadataLines:
			metadataSource += l[2:] + '\n' # we skip the first '# ' characters

		bodyModel = '\n'.join(lines[index:])

		return (metadataSource, QString(bodyModel.decode('utf-8')))

	def _join(self, metadataSource, bodyModel):
		"""
		Reimplemented from DocumentModel for Python-based documents.
		
		Recreates a full document source made of a body with associated metadata,
		ready to be persisted/stored.
		
		@type  metadata: buffer string
		@type  bodyModel: QString (as decoded via _split())
		
		@rtype: buffer string
		@returns: a document source
		"""
		documentSource = ""
		if metadataSource is not None:
			documentSource = "# __METADATA__BEGIN__\n"
			for l in metadataSource.split('\n'):
				if l:
					documentSource += "# " + l + "\n"
			documentSource += "# __METADATA__END__\n"
		documentSource += unicode(bodyModel).encode('utf-8')
		return documentSource


###############################################################################
# Module Model
###############################################################################

class ModuleModel(PythonDocumentModel):
	"""
	Module model.
	
	Does not offer metadata;
	however, for compatibility purpose with older modules whose source may
	contain metadata,
	the split function is implemented to filter the metadata our of the
	body.

	The body model is a unicode string.
	
	This model is persisted/stored as a utf-8 string.
	"""
	def __init__(self):
		PythonDocumentModel.__init__(self)
		self.setFileExtension("py")
		self.setDocumentType(TYPE_MODULE)

	def _split(self, documentSource):
		"""
		Reimplemented to discard the metadata that old
		module files may (incorrectly) contain.
		
		Newly saved modules won't contain metadata.
		"""
		(metadataSource, bodyModel) = PythonDocumentModel._split(self, documentSource)
		return (None, bodyModel)

registerDocumentModelClass(r'.*\.py', ModuleModel)
	

###############################################################################
# Ats Model
###############################################################################

class AtsModel(PythonDocumentModel):
	"""
	Ats model.
	Basic reimplementation from DocumentModel.
	"""
	def __init__(self):
		defaultMetadataSource = u'''<?xml version="1.0" encoding="utf-8"?>
<meta>
<description><![CDATA[description]]></description>
<prerequisites><![CDATA[prerequisites]]></prerequisites>
<parameters>
<parameter name="PX_PARAM1" default="defaultValue01" type="string"></parameter>
</parameters>
<parameters>
<!-- there is no default groups -->
</parameters>
</meta>'''
		PythonDocumentModel.__init__(self, defaultMetadataSource)
		self.setFileExtension("ats")
		self.setDocumentType(TYPE_ATS)

registerDocumentModelClass(r'.*\.ats', AtsModel)

###############################################################################
# Campaign Model
###############################################################################

class CampaignModel(PythonDocumentModel):
	"""
	Campaign model.
	
	Based on a PythonDocumentModel as it uses the same split/join
	implementations.
	"""
	def __init__(self):
		defaultMetadataSource = u'<?xml version="1.0" encoding="utf-8"?>\n<meta>\n<description><![CDATA[description]]></description>\n<prerequisites><![CDATA[prerequisites]]></prerequisites><parameters><parameter name="PX_PARAM1" default="defaultValue01" type="string"></parameter></parameters>\n</meta>'
		PythonDocumentModel.__init__(self, defaultMetadataSource)
		self.setFileExtension("campaign")
		self.setDocumentType(TYPE_CAMPAIGN)

registerDocumentModelClass(r'.*\.campaign', CampaignModel)

###############################################################################
# Package Description/Manifest Model
###############################################################################

class PackageDescriptionModel(DocumentModel):
	"""
	Package description model.
	
	Federates all package attributes, properties, and links
	to its dependencies/actual files.
	
	No metadata model.
	
	The body model is QDomDocument.
	
	This model is persisted/stored as a utf-8 encoded XML file.
	"""
	def __init__(self):
		DocumentModel.__init__(self)
		self.setFileExtension("xml")
		self.setDocumentType(TYPE_PACKAGE_METADATA)
	
	def _split(self, documentSource):
		"""
		Reimplemented.
		
		Splits the source document to extract the metadataSource (as buffer string),
		and a body model.
		For this PackageDescriptionModel, the body model is a QDomDocument.
		There is no metadata in this kind of document.
		
		@rtype: (buffer string, QDomDocument)
		@returns: (metadataSource, body model)
		"""
		if not documentSource:
			documentSource = u'<?xml version="1.0" encoding="utf-8"?><package></package>'
		
		metadataSource = None
		bodyModel = QDomDocument()
		(res, errorMessage, errorLine, errorColumn) = bodyModel.setContent(documentSource, 0)
		
		if not res:
			raise Exception("Invalid package.xml file: %s (line %d, column %d)" % (unicode(errorMessage), errorLine, errorColumn)) 
		
		return (metadataSource, bodyModel)

	def _join(self, metadataSource, bodyModel):
		"""
		Reimplemented.
		
		Constructs the document source from the elements as returned by _split().

		Ignores the metadata (which should be None, anyway).
		
		@rtype: buffer string
		@returns: the document source, ready for storage. For information, stored as  utf-8 encoded XML string.
		"""
		return unicode(bodyModel.toString()).encode('utf-8')

	def getPackageName(self):
		"""
		Returns the package name, i.e. the folder the package is defined in.
		
		@rtype: QString
		@returns: the package name
		"""
		return self.getName()[:-len('/package.xml')]

registerDocumentModelClass(r'package\.xml', PackageDescriptionModel)


	
###############################################################################
# Profile Model
###############################################################################

class VirtualPath:
	"""
	A Testerman Virtual Path parser.
	Should be moved to a shared modules between servers and clients.
	"""
	def __init__(self, vpath):
		self._vtype = None
		self._vvalue = None
		self._basevalue = vpath
	
		velements = vpath.split('/')

		# non-repository paths cannot be virtual		
		if len(velements) > 1 and velements[1] != 'repository':
			return
		
		i = 0
		for element in velements:
			if element.endswith('.ats') or element.endswith('.campaign'):
				if velements[i+1:]:
					# remaining elements after the script name -> pure virtual path
					vobject = velements[i+1]
					if vobject in ['executions', 'profiles', 'revisions']:
						self._vtype = vobject
						self._vvalue = '/'.join(velements[i+2:])
						self._basevalue = '/'.join(velements[:i+1])
						return
					else:
						raise Exception('Invalid virtual path %s, unsupported virtual object %s' % (vpath, vobject))

			i += 1

	def isProfileRelated(self):
		return self._vtype == 'profiles'		
	
	def getVirtualValue(self):
		return self._vvalue

	def getBaseValue(self):
		return self._basevalue

	def isVirtual(self):
		return (self._vtype is not None)


class ProfileModel(DocumentModel):
	"""
	Profile model.
	
	No metadata aspect model.
	
	The body aspect is "private" and should not be used
	by the views that observe this model.
	
	This model is persisted/stored as a utf-8 encoded XML file.
	-> or should we stick to a key=value configuration file ?
	
	"""
	def __init__(self):
		DocumentModel.__init__(self)
		self.setFileExtension("profile")
		self.setDocumentType(TYPE_PROFILE)
		self._readOnly = False
		self._friendlyName = ""
		
	def _split(self, documentSource):
		"""
		Reimplemented.
		
		Splits the source document to extract the metadataSource (as buffer string),
		and a body model.

		For this ProfileModel, the body model is a QDomDocument.
		There is no metadata in this kind of document.
		
		@rtype: (buffer string, QDomDocument)
		@returns: (metadataSource, body model)
		"""
		if not documentSource:
			documentSource = u'<?xml version="1.0" encoding="utf-8"?><profile></profile>'
		
		metadataSource = None
		bodyModel = QDomDocument()
		(res, errorMessage, errorLine, errorColumn) = bodyModel.setContent(documentSource, 0)
		
		if not res:
			raise Exception("Invalid profile file: %s (line %d, column %d)" % (unicode(errorMessage), errorLine, errorColumn)) 
		
		return (metadataSource, bodyModel)

	def _join(self, metadataSource, bodyModel):
		"""
		Reimplemented.
		
		Constructs the document source from the elements as returned by _split().

		Ignores the metadata (which should be None, anyway).
		
		@rtype: buffer string
		@returns: the document source, ready for storage. For information, stored as  utf-8 encoded XML string.
		"""
		# We just have to serialize our memory model to an utf-8 encoded string.
		
		return unicode(bodyModel.toString()).encode('utf-8')

	##
	# ProfileModel specific functions
	##

	def getAssociatedScriptUrl(self):
		try:
			vpath = VirtualPath(unicode(self.getUrl().path()))
		except:
			return None
		scriptUrl = QUrl()
		scriptUrl.setPath(vpath.getBaseValue())
		scriptUrl.setScheme(self.getUrl().scheme())
		scriptUrl.setHost(self.getUrl().host())
		scriptUrl.setPort(self.getUrl().port())
		return scriptUrl
	
	def getAssociatedScriptLabel(self):
		url = self.getAssociatedScriptUrl()
		if not url:
			return None
		return url.path()

	def setReadOnly(self, ro):
		self._readOnly = ro
	
	def isReadOnly(self):
		return self._readOnly
	
	def setFriendlyName(self, fn):
		self._friendlyName = fn
	
	def getFriendlyName(self):
		return self._friendlyName

	# Accessors

	def getDescription(self):
		root = self.getBodyModel().documentElement()
		return unicode(root.firstChildElement('description').text())

	def setDescription(self, description):
		self._updateModelElement('description', description)
		self.emit(SIGNAL('bodyUpdated()'))

	def getParameters(self):
		localModel = {}
		root = self.getBodyModel().documentElement()
		parameters = root.firstChildElement('parameters')
		if not parameters.isNull():
			parameter = parameters.firstChildElement('parameter')
			while not parameter.isNull():
				name = unicode(parameter.attribute('name'))
				value = unicode(parameter.text())
				localModel[name] = value
				parameter = parameter.nextSiblingElement()
		return localModel

	def setParameters(self, p):
		doc = self.getBodyModel()
		root = doc.documentElement()
		root.removeChild(root.firstChildElement('parameters'))
		parameters = doc.createElement('parameters')
		for k, v in p.items():
			parameter = doc.createElement('parameter')
			parameter.setAttribute('name', k)
			parameter.appendChild(doc.createTextNode(v))
			parameters.appendChild(parameter)
		root.appendChild(parameters)
		self.emit(SIGNAL('bodyUpdated()'))
	
	def getParameter(self, key):
		pass
	
	def setParameter(self, key, value):
		pass

	def _updateModelElement(self, name, value):
		# Can't update a text value directly with QtXml.... (??)
		# We have to create a new child and replace the previous one
		doc = self.getBodyModel()
		root = doc.documentElement()
		oldChild = root.firstChildElement(name)
		newChild = doc.createElement(name)
		newChild.appendChild(doc.createTextNode(value))
		if oldChild.isNull():
			root.appendChild(newChild)
		else:
			root.replaceChild(newChild, oldChild)

	def toSession(self):
		"""
		Returns the profile contents as a dict of key: value, suitable
		for a script execution.
		"""
		return self.getParameters()
	

registerDocumentModelClass(r'.*\.profile', ProfileModel)


