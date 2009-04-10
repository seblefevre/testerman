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
# Documentation-related functions.
#
# Epydoc-like metadata parsing on functions and classes,
# special TestCase docstring handling for test specification extraction.
#
# The functions included in this module can be used from any plugin
# to extract specific inline documentation (reporters, doc plugins..)
#
##




import re

##############################################################################
# docstring trimmer - from PEP 257 sample code
##############################################################################

def trim(docstring):
	if not docstring:
		return ''
	maxint = 2147483647
	# Convert tabs to spaces (following the normal Python rules)
	# and split into a list of lines:
	lines = docstring.expandtabs().splitlines()
	# Determine minimum indentation (first line doesn't count):
	indent = maxint
	for line in lines[1:]:
		stripped = line.lstrip()
		if stripped:
			indent = min(indent, len(line) - len(stripped))
	# Remove indentation (first line is special):
	trimmed = [lines[0].strip()]
	if indent < maxint:
		for line in lines[1:]:
			trimmed.append(line[indent:].rstrip())
	# Strip off trailing and leading blank lines:
	while trimmed and not trimmed[-1]:
		trimmed.pop()
	while trimmed and not trimmed[0]:
		trimmed.pop(0)
	# Return a single string:
	return '\n'.join(trimmed)

##############################################################################
# Tag-based Docstring parsers
##############################################################################

class TagValue:
	"""
	Represents a valued instance of a tag, with optional arguments.
	
	For instance:
	 @mytag: value,
	 continued value
	 
	-> TagValue(parameters = [])._value = "value, continued value"
	
	 @mytag p,v: value,
	 continued value
	 
	-> TagValue(parameters = [ p, v ])._value = "value, continued value"
	"""
	def __init__(self, arguments = []):
		self._arguments = arguments
		self._body = ''

	def appendToBody(self, val):
		if not val.strip():
			# new line
			self._body += '\n'
		else:
			# string concatenation
			if not self._body or self._body[-1] in [' ', '\n']:
				self._body += val.strip()
			else:
				self._body += ' ' + val.strip()

	def __str__(self):
		ret = '   arguments: %s\n' % ', '.join(self._arguments)
		ret += '  body:\n%s\n' % self._body
		return ret
	
	def getBody(self):
		return self._body
	
	def getArguments(self):
		return self._arguments

class Tag:
	"""
	Represents a multivalued tag.
	Each value is a TagValue that contains a list of arguments and a body.
	"""
	def __init__(self, name):
		self._name = name
		self._values = []

	def startValue(self, arguments = []):
		# According to the name, may select a TagValue implementation.
		self._values.append(TagValue(arguments))

	def appendToValue(self, val):
		self._values[-1].appendToBody(val)
	
	def __str__(self):
		ret = []
		ret.append("Tag '%s':" % self._name)
		for v in self._values:
			ret.append(" Value:")
			ret.append(str(v))
		return '\n'.join(ret)
	
	def getName(self):
		return self._name
	
	def getValues(self):
		return self._values

	def value(self, default = ''):
		"""
		First value's body, if any.
		"""
		if self._values:
			return self._values[0].getBody()
		else:
			return default

	def __getitem__(self, index):
		return self._values[index]


class TaggedDocstring:
	"""
	Represents a parsed docstring that used epydoc-like @-based tags.
	
	Tags are multivalued; each value may have arguments.
	A value's body is the concatenation of the docstring lines until
	the next tag.

	First call .parse(docstring) to initialize your object
	with the content on a docstring.
	"""

	reTag = re.compile(r'\@(?P<tag>\w+)(\s+(?P<arguments>\w+))?\s*:(?P<content>.*)')

	def __init__(self, tagAliases = {}):
		self._tags = None
		self._default = None
		self._aliases = tagAliases

	def _convertTag(self, tag):
		"""
		Returns a transformed tag according to tag aliases.
		
		@rtype: string
		@returns: a lowercase tag.
		"""
		tag = tag.lower()
		if tag in self._aliases:
			tag = self._aliases[tag].lower()
		return tag

	def parse(self, docstring):
		"""
		Call this to fill your object with the result of a docstring
		parsing.

		Once called, you may access the parsed tags using the following

		"""
		self._default = Tag('')
		self._tags = {}
		lines = trim(docstring).splitlines()
		currentTag = self._default
		currentTag.startValue()
		for line in lines:
			m = self.reTag.match(line)
			if m:
				tag = self._convertTag(m.group('tag'))
				arguments = m.group('arguments')
				if arguments:
					arguments = map(lambda x: x.strip(), arguments.split(','))
				else:
					arguments = []
				if not tag in self._tags:
					self._tags[tag] = Tag(tag)
				currentTag = self._tags[tag]
				currentTag.startValue(arguments)
				currentTag.appendToValue(m.group('content'))
			else:
				currentTag.appendToValue(line)
		
	def __str__(self):
		ret = []
		ret.append("Parse docstring:")
		ret.append(str(self._default))
		for tag in self._tags.values():
			ret.append(str(tag))
		return '\n'.join(ret)
	
	def __getitem__(self, tagName):
		tagName = self._convertTag(tagName)
		if not tagName:
			return self._default
		elif tagName in self._tags:
			return self._tags[tagName]
		else:
			# Create a default tag
			return Tag(tagName)



if __name__ == '__main__':
	sample = """
	This could be a docstring, with
	some usual parameters.
	
	@description: this is a description parameter.
	@text: this is a
	multi-line text
	@text2: this
	is
	also a multi-line
	string
	
	with some blank lines.

	@param name: this is a
	tag with a single parameter.
	@param name2: this is a second value for the
	previous tag.
	"""

	pds = TaggedDocstring()
	pds.parse(sample)
	print str(pds)


