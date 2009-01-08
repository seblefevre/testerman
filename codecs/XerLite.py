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
# XER-like lite codec.
# (ITU-T X.693 inspired)
#
# Not a real XER codec since it won't map received data to
# a provided ASN.1 specification.
# Instead, see it as a XML codec without:
# - element attributes support
# - cdata support
#
# This enables to simplify the userland syntax:
#
# ('name', [ ('givenName', 'John'), ('familyName', 'Smith') ])
#
# decoded from/encoded to:
# 
# <name><givenName>John</givenName><familyName>Smith</familyName></name>
#
# (with optional prolog)
##

import TestermanCD

import StringIO
import codecs
import xml.dom.minidom

# "overriden" Document.toxml and toprettyxml to optionaly write the prolog.

def writexml(doc, prolog = True, encoding = None, indent = "", addindent = "", newl = ""):
	writer = StringIO.StringIO()
	if encoding is not None:
		writer = codecs.lookup(encoding)[3](writer)
	if prolog:
		if encoding is None:
			writer.write('<?xml version="1.0" ?>%s' % newl)
		else:
			writer.write('<?xml version="1.0" encoding="%s"?>%s' % (encoding, newl))
	for node in doc.childNodes:
		node.writexml(writer, indent, addindent, newl)
	return writer.getvalue()

class XerLiteCodec(TestermanCD.Codec):
	"""
	('element', [ ... ])
	if no child:
	('element', <unicode>)
	
	
	Valid properties:
	
	canonical    || boolean || False || encoding: CANONICAL-XER (no pretty print) or BASIC-XER if false.
	encoding     || string  || utf-8 || encoding: encoding format. decoding: decoding format if no prolog present.
	write_prolog || boolean || True  || encoding: write the <?xml version="1.0" ?> prolog or not
	"""
	def encode(self, template):
		(rootTag, value) = template
		dom = xml.dom.minidom.getDOMImplementation().createDocument(None, rootTag, None)
		root_element = dom.documentElement
		self._encode(dom, root_element, value)
		if not self.getProperty('canonical', False):
			return writexml(dom, prolog = self.getProperty('write_prolog', True), encoding = self.getProperty('encoding', 'utf-8'), addindent = "\t", newl = "\n")
		else:
			return writexml(dom, prolog = self.getProperty('write_prolog', True), encoding = self.getProperty('encoding', 'utf-8'))
	
	def _encode(self, doc, element, value):
		"""
		@type  doc: Document
		@type  element: Element
		@type  value: basetring, or a list of (string, value)
		"""
		if isinstance(value, list):
			# OK, children present. Ignoring value/cdata
			for (tag, v) in value:
				e = doc.createElement(tag)
				self._encode(doc, e, v)
				element.appendChild(e)
		else:
			e = doc.createTextNode(unicode(value))
			element.appendChild(e)
			
	def decode(self, data):
		ret = None
		dom = xml.dom.minidom.parseString(data)
		element = dom.documentElement
		ret = self._decode(element)
		return ret
	
	def _decode(self, element):
		"""
		Recursive decoding.
		@type  element: Element
		
		@rtype: tuple (tag, list or unicode)
		"""
		tag = element.tagName
		
		# Now retrieve children, if any
		children = []
		for node in element.childNodes:
			if node.nodeType == node.ELEMENT_NODE:
				children.append(self._decode(node))
			# We should return only if these nodes are the first one.. ?
			elif node.nodeType == node.TEXT_NODE and node.nodeValue.strip():
				return (tag, node.nodeValue.strip())
			# Ignore other final node types (cdata, comments, ...)
		
		return (tag, children) 

TestermanCD.registerCodecClass('xer.lite', XerLiteCodec)


if __name__ == '__main__':
	TestermanCD.alias('xer.noprolog', 'xer.lite', write_prolog = False)
	TestermanCD.alias('xer.iso', 'xer.lite', encoding = "iso-8859-1")
	TestermanCD.alias('xer.canonical', 'xer.lite', canonical = True)
	
	sample = """<?xml version="1.0"?>
<library>
	<administrator>Héléna Utf8</administrator>
	<book>
		<isbn>89084-89089</isbn>
		<author>Philippe Kendall</author>
		<author>Mickaël Orangina</author>
		<title>Tropic thunder</title>
	</book>
</library>
"""

	for codec in [ 'xer.lite', 'xer.noprolog', 'xer.iso', 'xer.canonical' ]:
		print "%s %s %s" % (40*'=', codec, 40*'=')
		print "decoded with %s:" % codec
		decoded = TestermanCD.decode(codec, sample)
		print decoded
		print
		print "re-encoded with %s:" % codec
		reencoded = TestermanCD.encode(codec, decoded)
		print
		print reencoded
		print "re-decoded with %s:" % codec
		redecoded = TestermanCD.decode(codec,reencoded)
		print redecoded
		assert(decoded == redecoded)
		print


	
	
