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

import TestermanCD

import xml.dom.minidom


class XmlCodec(TestermanCD.Codec):
	"""
	('element', { 'attributes': { ... }, 'children': [ ... ])
	if no child:
	('element', { 'attributes': { ... }, 'value': <unicode>, 'cdata': bool)
	
	
	This codec is NOT SUITABLE to parse XHTML, since it won't create dedicated nodes
	for text-node (as a consequence: <h1>hello <b>dolly</b></h1> 
	will only return ('h1', { 'value': hello }) - the first text node renders the
	element 'text only'.
	"""
	def encode(self, template):
		(rootTag, rootAttr) = template
		dom = xml.dom.minidom.getDOMImplementation().createDocument(None, rootTag, None)
		root_element = dom.documentElement
		self._encode(dom, root_element, rootAttr)
		if self.getProperty('prettyprint', False):
			return dom.toprettyxml() # encoding support possible here.
		else:
			return dom.toxml()
	
	def _encode(self, doc, element, attr):
		"""
		@type  doc: Document
		@type  element: Element
		@type  attr: dict{'attributes' (optional), 'value' (optional), 'children' (optional), 'cdata' (optional)}
		"""
		if attr.has_key('attributes'):
			for k, v in attr.items():
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
			elif node.nodeType == node.TEXT_NODE:
				return (tag, { 'attributes': attributes, 'cdata': False, 'value': node.nodeValue }) 
			elif node.nodeType == node.CDATA_SECTION_NODE:
				return (tag, { 'attributes': attributes, 'cdata': True, 'value': node.nodeValue })
			# Ignore other final node types (comments, ...)
		
		return (tag, { 'attributes': attributes, 'children': children }) 

TestermanCD.registerCodecClass('xml', XmlCodec)


if __name__ == '__main__':
	codec = XmlCodec()
	
	sample = """<?xml version="1.0"?>
<library owner="John Smith" administrator="çalia utf">
	<book isbn="88888-7777788">
		<author>Mickaël</author>
		<title locale="fr">Tonnerre sous les tropiques</title>
		<title locale="us">Tropic thunder</title>
	</book>
</library>
"""
	
	decoded = codec.decode(sample)
	print decoded
	print codec.encode(decoded)
	
	
