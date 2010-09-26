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
# Some Job-related tools, especially to manipulate source metadata
#
##

import Tools

import logging
import xml.dom.minidom

def getLogger():
	return logging.getLogger('TEFactory.Tools')

def extractMetadata(document, commentsPrefix = '#'):
	"""
	Extracts metadata from an ATS or Campaign job.
	
	Metadata are encoded within the document as an XML string that is commented
	between the following lines:
	# __METADATA__BEGIN__
	and
	# __METADATA__END__
	
	The metadata schema is:
	<metadata>
		<description><![CDATA[...]]></description>
		<prerequisites><![CDATA[...]]></prerequisites>
		<parameters>
			<parameter name="..." type="string" default="..."><![CDATA[(parameter description)]]></parameter>
		</parameters>
	</metadata>
	
	For now, only the type "string" is supported.
	
	For instance:

	# __METADATA__BEGIN__
	# <?xml version="1.0" encoding="utf-8" ?>
	# <metadata version="1.0">
	# <description>Testerman auto test to pass before any release.</description>
	# <prerequisites></prerequisites>
	# <parameters>
	# <parameter name="PX_UNICODE_STRING" type="string" default="ça marche"><![CDATA[unicode test string. Do not modify it.]]></parameter>
	# </parameters>
	# </metadata>
	# __METADATA__END__
	
	
	@type  document: utf-8 encoded-string
	@param document: the ATS or Campaign (or any other file containing metadata)
	@type  commentsPrefix: string
	@param commentsPrefix: the string that identify a comments in the source file (# in Python, // in TTCN-3, ...)
	
	@rtype: string or None
	@returns: the extracted raw metadata, as utf-8 string. May be empty.
	          None if no metadata was found.
	"""
	lines = document.split('\n')
	if not len(lines):
		return None
	if not lines[0].startswith('%s __METADATA__BEGIN__' % commentsPrefix):
		return None

	complete = False
	metadataLines = [ lines[1] ]
	index = 2
	for l in lines[index:]:
		if not len(l):
			index += 1
			break

		if l.startswith('%s __METADATA__END__' % commentsPrefix):
			index += 1
			complete = True
			break

		if not l.startswith(commentsPrefix):
			break

		metadataLines.append(l)
		index += 1

	if not complete:
		return None # Invalid metadata

	# OK, we have valid metadata.
	metadata = '\n'.join([l[len(commentsPrefix):].strip() for l in metadataLines]) # we skip the first comments characters characters
	
	getLogger().debug("extracted metadata:\n%s" % metadata)
	return metadata

# FIXME/TODO: refactor this.
# A mere dict-based struct (like Metadata.toDict()) should be enough instead of an actual class.

class Metadata:
	def __init__(self):
		self.description = ''
		self.prerequisites = ''
		self.api = '1' # default language API
		self.parameters = {}
	
	def getDefaultSessionDict(self):
		"""
		Returns the parameters value as suitable for a merge as session dict,
		@rtype: dict[unicode] of unicode
		@returns: the dict[name]: value
		"""
		ret = {}
		for k, v in self.parameters.items():
			ret[k] = v.defaultValue
		return ret

	def getSignature(self):
		"""
		Returns the script signature as a dict[parameter] = dict(name, defaultValue, type, description)
		"""
		ret = {}
		for k, v in self.parameters.items():
			ret[k] = dict(name = v.name, defaultValue = v.defaultValue, type = v.type_, description = v.description)
		return ret
	
	def toDict(self):
		"""
		Turns this object into a dict-based representation.
		"""
		ret = dict(description = self.description, api = self.api, parameters = self.getSignature())
		return ret
		

class Parameter:
	def __init__(self, name, defaultValue = '', type_ = 'string', description = ''):
		#: unicode
		self.name = name
		#: unicode
		self.defaultValue = defaultValue
		#: unicode
		self.type_ = type_
		#: unicode
		self.description = description

def parseMetadata(xmlMetadata):
	"""
	Parses the XML string containing the metadata.
	
	@type  xmlMetadata: utf-8 string
	@param xmlMetadata: the metadata as extracted by extractMetadata(), xml format
	
	@rtype: Metadata
	@returns: the parsed Metadata, or None in case of an error
	"""
	metadata = None
	try:
		# parseString takes unicode ?? (hence ignoring the <?xml encoding=...?> ?
 		doc = xml.dom.minidom.parseString(xmlMetadata)
		
		metadata = Metadata()
		# We don't need them for now (not used in TE)
		# metadata.description = ...
		# metadata.prerequisites = ...

		e = doc.getElementsByTagName('description')
		if e:	metadata.description = e[0].childNodes[0].data
		
		e = doc.getElementsByTagName('api')
		if e:	metadata.api = e[0].childNodes[0].data
		
		for parameter in doc.getElementsByTagName('parameter'):
			try:
				name = parameter.attributes['name'].value
				defaultValue = parameter.attributes['default'].value
				type_ = parameter.attributes['type'].value
				p = Parameter(name, defaultValue, type_)
				# description is ignored for now (not used in TE)
				metadata.parameters[name] = p
			except Exception, e:
				getLogger().warning("Unable to parse a parameter in metadata: %s" % str(e))
	
	except Exception:
		getLogger().warning("Unable to parse metadata:\n%s" % Tools.getBacktrace())
	
	return metadata
				
				
	
if __name__ == '__main__':
	sample = """# __METADATA__BEGIN__
# <?xml version="1.0" encoding="utf-8" ?>
# <metadata version="1.0">
# <description>Testerman auto test to pass before any release.</description>
# <prerequisites></prerequisites>
# <api>1</api>
# <parameters>
# <parameter name="PX_UNICODE_STRING" type="string" default="ça marche"><![CDATA[unicode test string. Do not modify it.]]></parameter>
# </parameters>
# </metadata>
# __METADATA__END__
"""

	logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S')
	xmlMetadata = extractMetadata(sample)
	if xmlMetadata:
		print "Extracted:\n%s" % xmlMetadata
		m = parseMetadata(xmlMetadata)
		if m:
			print "Parsed:\n%s" % m.parameters
			for p in m.getDefaultSessionDict().items():
				print "%s: %s" % p
			print m.getSignature()
			print
			print m.toDict()
		
		
