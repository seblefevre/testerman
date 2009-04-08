# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 QTesterman contributors
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
# Also include specialized classes ({Module,Ats,Campaign}Model, etc)
#
##

from PyQt4.Qt import *
from PyQt4.QtXml import *

from Base import *

# Document types
TYPE_ATS = "ats"
TYPE_MODULE = "module"
TYPE_CAMPAIGN = "campaign"

###############################################################################
# Model Base
###############################################################################

class MetadataModel(QObject):
	"""
	A Metadata model is a sub-model of a DocumentModel.

	It manages all the metadata-related stuff for a body.
	Body + Metadata composes a Document.

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
	def __init__(self, metadata = None):
		QObject.__init__(self)

		# The (default) model
		#: unicode string
		self.prerequisites = None
		#: unicode string
		self.description = None
		#: document parameters (ATS variables). Indexed by a unicode name, contain dicts[unicode] of unicode
		self.parameters = {}

		# For heavy modifications, we allow to disable the model notification mechanism.
		# In this case, use:
		# model.disableUpdateNotifications()
		# ... <heavy modifications>
		# model.enableUpdateNotifications()
		# model.notifyUpdate()
		self.notificationDisabled = False

		# Modification flag since the last setMetadata()
		self.modified = False

		if metadata is not None:
			self.setMetadata(metadata)
			self.modified = False

	def resetModificationFlag(self):
		"""
		To call once modifications have been saved
		"""
		self.setModified(False)

	def setModified(self, modified):
		if modified:
			self.notifyUpdate()
		if modified != self.modified:
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

	def setMetadata(self, metadata):
		"""
		loads XML metadata into the model.

		@type  metadata: unicode string
		@param metadata: valid XML content, compliant with Testerman metadata schema

		@rtype: None
		@returns: None
		"""
		# First we clear the model
		self.prerequisites = u''
		self.description = u''
		self.parameters = {}

		# Parse into a DOM document
		metadataDoc = QDomDocument()
		(res, errorMessage, errorLine, errorColumn) = metadataDoc.setContent(metadata, 0)

		if not res:
			raise Exception("Invalid metadata: %s (line %d, column %d)" % (str(errorMessage), errorLine, errorColumn))

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

		# Parameters
		parameters = metadataDoc.documentElement().firstChildElement('parameters')
		if not parameters.isNull():
			parameter = parameters.firstChildElement('parameter')
			while not parameter.isNull():
				self.parameters[unicode(parameter.attribute('name'))] = {
					'default': unicode(parameter.attribute('default')),
					'type': unicode(parameter.attribute('type')),
					'description': unicode(parameter.text()),
				}

				parameter = parameter.nextSiblingElement()

		self.setModified(True)
		
		log(u"Metadata set: " + unicode(self))

	def __str__(self):
		ret = u"Metadata:\n"
		ret += u"prerequisites: %s\n" % self.prerequisites
		ret += u"description: %s\n" % self.description
#		ret += u"parameters: %s\n" % str(self.parameters)
		return ret

	def getMetadata(self):
		"""
		Serializes the model to XML.

		<?xml version="1.0" encoding="utf-8"?>
		<metadata version="1.0">
			<description><![CDATA[description]]></description>
			<prerequisites><![CDATA[prerequisites]]></prerequisites>
			<parameters>
				<parameter name="PX_PARAM1" default="defaultValue01" type="string"><![CDATA[description]]></parameter>
			</parameters>
		</meta>'

		@rtype: unicode string (ready to be encoded in utf-8, as the XML encoding suggest)
		@returns: the metadata serialized into XML
		"""
		# Manual XML encoding.
		res =  u'<?xml version="1.0" encoding="utf-8" ?>\n'
		res += u'<metadata version="1.0">\n'
		res += u'<description>%s</description>\n' % Qt.escape(self.description) # This replacement enables to correcly read \n from the XML (when reloaded)
		res += u'<prerequisites>%s</prerequisites>\n' % Qt.escape(self.prerequisites)
		res += u'<parameters>\n'
		for (name, p) in self.parameters.items():
			# We must escape the values (to avoid ", etc)
			# TODO: use pure Qt facilities
			res += u'<parameter name="%s" default="%s" type="string"><![CDATA[%s]]></parameter>\n' % (Qt.escape(name), Qt.escape(p['default']), p['description'].replace('\n', '&cr;'))
		res += u'</parameters>\n'
		res += u'</metadata>\n'
		return res

	def getParameter(self, name):
		"""
		Gets a parameter attributes.

		@type  name: unicode string
		@param name: the name of the parameter

		@rtype: dict[unicode] of unicode
		@returns: { 'default', 'type', 'description' } None if the parameter does not exist.
		"""
		ret = {}
		if self.parameters.has_key(name):
			for k, v in self.parameters[name]:
				ret[k] = v
			# FIXME: Kept for compatibility
			ret['previous-value'] = ret['default']
		return None

	def setParameter(self, name, default = None, description = None, previousValue = None, newName = None):
		"""
		Sets a parameter or selected parameter attributes.
		Adds it if name does not exists.
		If newName is provided, rename the parameter (or create it with newName directly if it does not exist)

		Keeps attributes that are set to None. For new parameters with None attributes, uses an empty default value.
		
		FIXME: previousValue kept for compatibility. To remove.
		"""
		if not self.parameters.has_key(name):
			self.parameters[name] = { 'type': 'string', 'default': '', 'description': '' }
		p = self.parameters[name]

		if default is not None:
			p['default'] = default
		if description is not None:
			p['description'] = description
		
		if newName and newName != name:
			self.parameters[newName] = p
			del self.parameters[name]

		self.setModified(True)

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


class DocumentModel(QObject):
	"""
	A Document model using metadata and body aspects (acts as a proxy for a MetadataModel)
	Used as a base class for ModuleModel and ScriptModel.

	You may set/get metadata & body.
	You may get the complete document.

	The Document Model is initialized with a unicode complete document.
	This unicode doc is a valid python file that contains a special commented part containing some XML describing the doc metadata.

	Upon initialization, the document is parsed and exposed through multiple, differents aspects:
	The model aspects:
		- the medatadata model (R/W/Notify): unicode string (valid xml) ; getMetadata, setMetadata, SIGNAL(metadataUpdated())
		- the body model (R/W/Notify): unicode string ; getBody, setBody, SIGNAL(bodyUpdated())
	The main model, if you don't want to work with one of its aspects:
		- the document model (R/W/Notify): unicode string ; getDocument, setDocument, SIGNAL(documentReplaced())

	When modifying a single aspect of the model, documentReplaced() won't be fired.
	When replacing the complete document at once (with setDocument), this fires all aspect updates (medataUpdated, bodyUpdated)
	and an additional documentReplaced().
	"""

	def __init__(self, document = None, defaultMetadata = u""):
		"""
		document (unicode string) is the complete document data (metadata + body, automatically split)
		defaultMetadata is the metadata returned when the initial document does not contain any metadata.
		filename is either a local filename or a filename relative to the doc root on the testerman server (however starts with a /: /repository/newats.ats, etc)
		timestamp is the document timestamp to use to check for changes on the server during the local edition.
		
		"""
		QObject.__init__(self)
		# Metadata is a unicode string
		self.defaultMetadata = defaultMetadata
		# Body is a unicode string, metadata is a metadataModel
		(metadata, self.body) = self._explode(document)

		self.metadataModel = MetadataModel(metadata)

		#: must be overridden in DocumentModel subclasses.
		self.extension = ""
		#: must be overridden in DocumentModel subclasses with a TYPE_*
		self.documentType = None

		# These Document attributes are updated whenever the file is actually saved to a location.
		#: QUrl
		self.url = None
		# This timestamp is the reference timestamp of the doc when retrieved from the server.
		# If we put this doc into the repository, if the file was updated in the meanwhile,
		# we'll get a warning ("optimistic locking" concurrency management model)
		self.savedTimestamp = 0

		# Modification status
		# We manage the body part directly
		self.bodyModified = False
		# But the metadata part is managed by the sub model.
		# modified is the current modification status according to both body and metadata status.
		self.modified = False
		
		# We act as a proxy for the metadata sub-model,
		# i.e. we reemit a local signal whenever we have a modification here.
		self.connect(self.metadataModel, SIGNAL('metadataUpdated()'), self.onMetadataUpdated)
		self.connect(self.metadataModel, SIGNAL('modificationChanged(bool)'), self.onMetadataModificationChanged)
	
	def onMetadataUpdated(self):
		log("DEBUG: forwarding metadataUpdated signal")
		self.emit(SIGNAL('metadataUpdated()'))

	def onMetadataModificationChanged(self, modified):
		log("DEBUG: onMetadataModificationChanged, %s" % str(modified))
		# If the body has been modified, the document status stays to "modified".
		if self.bodyModified:
			log("DEBUG: onMetadataModificationChanged, %s, not taken into account, body modified (local status: %s)" % (str(modified), str(self.modified)))
			return
		# If the body has not been modified, then we can have a look to the metadata.
		# Only taken into account if it changes our local status.
		if modified != self.modified:
			self.modified = modified
			self.emit(SIGNAL('modificationChanged(bool)'), self.modified)

	def onBodyModificationChanged(self, modified):
		# If the metadata has been modified, the document status stays to "modified".
		log("DEBUG: onBodyModificationChanged, %s" % str(modified))
		if self.metadataModel.isModified():
			log("DEBUG: onBodyModificationChanged, %s, not taken into account, metadata modified (local status: %s)" % (str(modified), str(self.modified)))
			return
		# If the body has not been modified, then we can have a look to the metadata.
		# Only taken into account if it changes our local status.
		if modified != self.modified:
			self.modified = modified
			self.bodyModified = modified
			self.emit(SIGNAL('modificationChanged(bool)'), self.modified)

	def resetModificationFlag(self):
		"""
		To call once modifications have been saved.
		"""
		self.modified = False
		self.bodyModified = False
		self.metadataModel.resetModificationFlag()
		self.emit(SIGNAL('modificationChanged(bool)'), self.modified)

	def isModified(self):
		return self.bodyModified or self.metadataModel.isModified() # Should be equals to self.modified at any time, normally.

	def getDocumentType(self):
		return self.documentType

	def getTimestamp(self):
		return self.savedTimestamp

	def isRemote(self):
		if not self.url:
			return False
		return (self.url.scheme() == "testerman")

	def getUrl(self):
		"""
		Returns the URL corresponding to the file, according to its type, etc.
		
		Returns None if the document was never saved before, and this has no URL yet.
		
		@rtype: QUrl, or None
		@returns: the last saved URL, if any, or None otherwise.
		"""
		return self.url
	
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
		if self.url:
			if self.url.scheme() == 'testerman':
				return self.url.path()[len('/repository/'):]
			else:
				return "%s (local)" % self.url.path().split('/')[-1]
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
		self.url = url
		self.savedTimestamp = timestamp
		self.emit(SIGNAL('urlUpdated()'))

	def getExtension(self):
		"""
		Returns the associated file extension (py, ats, campaign).
		@rtype: string
		@returns: the file extension, corresponding to the document model type.
		"""
		return self.extension

	def getDocument(self):
		"""
		Returns the complete document, incuding metadata, according to the currently known model

		@rtype: unicode string
		@returns: the complete document underlying the model
		"""
		return self._join(self.metadataModel.getMetadata(), self.body)

	def setDocument(self, document):
		"""
		Replace the initial document with a new one.
		@type  document: unicode string
		@param document: the document to expose through the model

		@rtype: None
		@returns: None
		"""
		log("Replacing document in Model")
		(metadata, self.body) = self._explode(document)
		self.metadataModel.setMetadata(metadata)
		self.emit(SIGNAL('bodyUpdated()'))
		self.emit(SIGNAL('documentReplaced()'))

	def setMetadata(self, metadata):
		"""
		Sets the metadata aspect of the model (acts as a proxy for the sub-metadataModel)
		@type  metadata: unicode string
		@param metadata: the metadata, as a valid xml text string

		@rtype: None
		@returns: None
		"""
		self.metadataModel.setMetadata(metadata)

	def getMetadata(self):
		"""
		Returns the metadata aspect of the model.

		@rtype: unicode string
		@returns: the medata for the document, as a valid (ready to parse) xml text string
		"""
		return self.metadataModel.getMetadata()

	def getMetadataModel(self):
		"""
		Returns the metadata sub-model.

		@rtype: unicode string
		@returns: the medata for the document, as a valid (ready to parse) xml text string
		"""
		return self.metadataModel

	def setBody(self, body):
		"""
		Sets the body aspect of the model.
		@type  body: unicode string
		@param body: the body

		@rtype: None
		@returns: None
		"""
		self.body = body
		self.emit(SIGNAL('bodyUpdated()'))
		self.emit(SIGNAL('modificationChanged(bool)'), self.isModified())

	def getBody(self):
		"""
		Gets the body aspect of the model.

		@rtype: unicode string
		@returns: the body of the document.
		"""
		return self.body

	def _explode(self, document):
		"""
		Returns a tuple (metadata, body), extracting the metadata from the body of the module.
		
		the document must starts with a line # __METADATA__BEGIN__,
		then contains commented lines (starting with a #) containing the metadata in xml format,
		then a # __METADATA__END__ line
		After that, this is the document body.

		@type  document: unicode string
		@param document: the complete document.
		
		@rtype: tuple (unicode, unicode)
		@returns: a tuple corresponding to the (metadata, body) document model aspects.
		"""
		body = u""
		lines = document.split('\n')
		if not len(lines):
			return (self.defaultMetadata, document)
		if not lines[0].startswith('# __METADATA__BEGIN__'):
			return (self.defaultMetadata, document)

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
			return (self.defaultMetadata, document)

		# OK, we have valid metadata.
		metadata = u""
		for l in metadataLines:
			metadata += l[2:] + '\n' # we skip the first '# ' characters

		body = u'\n'.join(lines[index:])

#		print "DEBUG: extracted metadata: " + metadata

		return (metadata, body)

	def _join(self, metadata, body):
		"""
		Internal fonction.
		Create a document made of a body with associated metadata
		Returns a unicode string
		"""
		module = u"# __METADATA__BEGIN__\n"
		for l in metadata.split(u'\n'):
			if l:
				module += u"# " + l + u"\n"
		module += u"# __METADATA__END__\n"
		module += body
		return module


###############################################################################
# Module Model management
###############################################################################

class ModuleModel(DocumentModel):
	"""
	Module model.
	Basic reimplementation from DocumentModel.
	Some specificities, but not that much.
	"""
	def __init__(self, document = None, url = None, timestamp = 0):
		defaultMetadata = u'<?xml version="1.0" encoding="utf-8"?>\n<meta>\n<description><![CDATA[description]]></description>\n<prerequisites><![CDATA[prerequisites]]></prerequisites>\n</meta>'
		DocumentModel.__init__(self, document, defaultMetadata)
		self.extension = "py"
		self.documentType = TYPE_MODULE
		self.setSavedAttributes(url = url, timestamp = timestamp)
		info = "New ModuleModel created:\n"
		info += " document len: " + str(len(document)) + "\n"
		info += " timestamp: " + str(self.savedTimestamp)
		log(info)

###############################################################################
# Ats Model management
###############################################################################

class AtsModel(DocumentModel):
	"""
	Ats model.
	Basic reimplementation from DocumentModel.
	"""
	def __init__(self, document = None, url = None, timestamp = 0):
		defaultMetadata = u'<?xml version="1.0" encoding="utf-8"?>\n<meta>\n<description><![CDATA[description]]></description>\n<prerequisites><![CDATA[prerequisites]]></prerequisites><parameters><parameter name="PX_PARAM1" default="defaultValue01" type="string"></parameter></parameters>\n</meta>'
		DocumentModel.__init__(self, document, defaultMetadata)
		self.extension = "ats"
		self.documentType = TYPE_ATS
		self.setSavedAttributes(url = url, timestamp = timestamp)
		info = "New AtsModel created:\n"
		info += " document len: " + str(len(document)) + "\n"
		info += " timestamp: " + str(self.savedTimestamp)
		log(info)

###############################################################################
# Campaign Model management
###############################################################################

class CampaignModel(DocumentModel):
	"""
	Campaign model.
	Basic reimplementation from DocumentModel.
	"""
	def __init__(self, document = None, url = None, timestamp = 0):
		defaultMetadata = u'<?xml version="1.0" encoding="utf-8"?>\n<meta>\n<description><![CDATA[description]]></description>\n<prerequisites><![CDATA[prerequisites]]></prerequisites><parameters><parameter name="PX_PARAM1" default="defaultValue01" type="string"></parameter></parameters>\n</meta>'
		DocumentModel.__init__(self, document, defaultMetadata)
		self.extension = "campaign"
		self.documentType = TYPE_CAMPAIGN
		self.setSavedAttributes(url = url, timestamp = timestamp)
		info = "New CampaignModel created:\n"
		info += " document len: " + str(len(document)) + "\n"
		info += " timestamp: " + str(self.savedTimestamp)
		log(info)

