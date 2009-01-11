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
# XML codec.
##

import CodecManager

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

class XmlCodec(CodecManager.Codec):
	"""
	('element', { 'attributes': { ... }, 'children': [ ... ])
	if no child:
	('element', { 'attributes': { ... }, 'value': <unicode>, 'cdata': bool)
	
	
	This codec is NOT SUITABLE to parse XHTML, since it won't create dedicated nodes
	for text-node (as a consequence: <h1>hello <b>dolly</b></h1> 
	will only return ('h1', { 'value': hello }) - the first text node renders the
	element 'text only'.
	
	
	Valid properties:
	
	prettyprint  || boolean || False || encoding: pretty xml print
	encoding     || string  || utf-8 || encoding: encoding format. decoding: decoding format if no prolog present.
	write_prolog || boolean || True || encoding: write the <?xml version="1.0" ?> prolog or not
	"""
	def encode(self, template):
		(rootTag, rootAttr) = template
		dom = xml.dom.minidom.getDOMImplementation().createDocument(None, rootTag, None)
		root_element = dom.documentElement
		self._encode(dom, root_element, rootAttr)
		if self.getProperty('prettyprint', False):
			return writexml(dom, prolog = self.getProperty('write_prolog', True), encoding = self.getProperty('encoding', 'utf-8'), addindent = "\t", newl = "\n")
		else:
			return writexml(dom, prolog = self.getProperty('write_prolog', True), encoding = self.getProperty('encoding', 'utf-8'))
	
	def _encode(self, doc, element, attr):
		"""
		@type  doc: Document
		@type  element: Element
		@type  attr: dict{'attributes' (optional), 'value' (optional), 'children' (optional), 'cdata' (optional)}
		"""
		attributes = attr.get('attributes', {})
		for k, v in attributes.items():
			element.setAttribute(k, unicode(v))
		children = attr.get('children', [])
		if children:
			# OK, children present. Ignoring value/cdata
			for (tag, a) in children:
				e = doc.createElement(tag)
				self._encode(doc, e, a)
				element.appendChild(e)
		else:
			cdata = attr.get('cdata', False)
			value = attr.get('value', '')
			if cdata:
				e = doc.createCDATASection(value)
			else:
				e = doc.createTextNode(value)
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
		
		@rtype: tuple (tag, { attributes, children (if any), text (if any), cdata (if applicable) }
		"""
		tag = element.tagName
		attributes = {}
		# Retrieve attributes
		for a, v in element.attributes.items():
			attributes[a] = v
		
		# Now retrieve children, if any
		children = []
		for node in element.childNodes:
			if node.nodeType == node.ELEMENT_NODE:
				children.append(self._decode(node))
			# We should return only if these nodes are the first one.. ?
			elif node.nodeType == node.TEXT_NODE and node.nodeValue.strip():
				return (tag, { 'attributes': attributes, 'cdata': False, 'value': node.nodeValue.strip() })
			elif node.nodeType == node.CDATA_SECTION_NODE:
				return (tag, { 'attributes': attributes, 'cdata': True, 'value': node.nodeValue })
			# Ignore other final node types (comments, ...)
		
		return (tag, { 'attributes': attributes, 'children': children }) 

CodecManager.registerCodecClass('xml', XmlCodec)


if __name__ == '__main__':
	CodecManager.alias('xml.noprolog', 'xml', write_prolog = False)
	CodecManager.alias('xml.iso', 'xml', encoding = "iso-8859-1", write_prolog = True)
	CodecManager.alias('xml.pretty', 'xml', prettyprint = True)
	
	sample = """<?xml version="1.0"?>
<library owner="John Smith" administrator="Héléna Utf8">
	<book isbn="88888-7777788">
		<author>Mickaël Orangina</author>
		<title locale="fr">Tonnerre sous les tropiques</title>
		<title locale="us">Tropic thunder</title>
		<summary><![CDATA[This is a CDATA section <-> <-- this is a tie fighter]]></summary>
	</book>
</library>
"""
	
	for codec in [ 'xml', 'xml.noprolog', 'xml.iso', 'xml.pretty' ]:
		print "%s %s %s" % (40*'=', codec, 40*'=')
		print "decoded with %s:" % codec
		decoded = CodecManager.decode(codec, sample)
		print decoded
		print
		print "re-encoded with %s:" % codec
		reencoded = CodecManager.encode(codec, decoded)
		print
		print reencoded
		print "re-decoded with %s:" % codec
		redecoded = CodecManager.decode(codec,reencoded)
		print redecoded
		assert(decoded == redecoded)
		print
	
	
