# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008-2013 Sebastien Lefevre and other contributors
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

import libxml2


class XmlCodec(CodecManager.Codec):
	"""
	Identification and Properties
	-----------------------------

	Codec ID: ``xml``

	Properties:

	+--------------------+-----------+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
	| Name               | Type      | Default value   | Description                                                                                                                                      |
	+====================+===========+=================+==================================================================================================================================================+
	| ``encoding``       | string    | ``utf-8``       | encoding: use this to encode the payload. Decoding: assumes the payload follows this encoding if the xml prolog encoding attribute is missing.   |
	+--------------------+-----------+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
	| ``write_prolog``   | boolean   | ``True``        | encoding: if True, write the ``<?xml version="1.0" encoding="..."?>`` prolog.                                                                    |
	+--------------------+-----------+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
	| ``prettyprint``    | boolean   | ``False``       | encoding: if True, pretty print the XML (carriage returns, hard tabs)                                                                            |
	+--------------------+-----------+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------+

	Overview
	--------

	This codec enables to encode/decode XML strings from/to Testerman
	message structures.

	Limitations:

	-  comments, entity nodes are not decoded (nor can be encoded)
	-  nested elements are only reported if not preceded by a text. In
	   particular, this makes this codec unsuitable for full XHTML parsing,
	   but should make it more convenient in most testing cases

	Something like

	.. code-block:: html

	   <p>In this text, <i>some elements</i> are nested</p>

	will be decoded to:

	.. code-block:: python

	   ('p', { 'value': u"In this text, <i>some elements</i> are nested" })


	I.e. the nested element won't be constructed; whereas:

	.. code-block:: html

	   <p><i>nested element</i></p>

	will be decoded to

	.. code-block:: python

	   ('p', { 'children': [ ('i', 'value': u"nested element") ] })

	If you don't need to manage attributes and CDATA sections, you may
	consider CodecXerLite.

	Decoding
	~~~~~~~~

	Input:

	.. code-block:: html

	  <element attr="attrval">
	    <subelement>subvalue</subelement>
	    <subelement2><![CDATA[cdata value]]></subelement2>
	  </element>

	Decoded message:

	.. code-block:: python

	   ('element', { 'attributes': { 'attr': 'attrval' }, 'children': [
	     ('subelement', { 'value': 'subvalue', 'cdata': False }),
	       ('subelement2', { 'value': 'cdata value', 'cdata': True }),
	     ]}
	   )

	``cdata`` is always provided during decoding.

	Encoding
	~~~~~~~~

	Input:

	.. code-block:: python

	  ('element', { 'attributes': { 'attr': 'attrval' }, 'children': [
	    ('subelement', { 'value': 'subvalue' }),
	    ('subelement2', { 'value': 'cdata value', 'cdata': True }),
	  ]})

	Encoded message:

	.. code-block:: html

	  <element attr="attrval">
	    <subelement>subvalue</subelement>
	    <subelement2><![CDATA[cdata value]]></subelement2>
	  </element>

	If ``cdata`` is not present during a value element encoding, it is assumed to be ``False``.

	If both ``children`` and ``value`` are provided, ``children`` has a greater precedence and ``value`` will be ignored.

	TTCN-3 Types Equivalence
	------------------------

	::

	  type record Element
	  {
  	  Attributes attributes,
  	  // if children is present, cdata and value are not present.
  	  // if cdata and value are present, children it not present.
  	  boolean cdata optional,
  	  universal charstring value optional,
  	  record of Element children optional
	  }
  
  	type record Attributes
  	{
    	// field name depends on the available attributes. All types are universal charstring
    	universal charstring name
  	}

	"""

	def encode(self, template):
		(tag, attr) = template
		doc = libxml2.newDoc("1.0")
		root = self._encode(doc, tag, attr.get('children'), attr.get('attributes', {}), attr.get('value', ''), attr.get('cdata', False), attr.get('ns'))
		doc.setRootElement(root)
		encoding = self.getProperty('encoding', 'utf-8')
		ret = ''
		if self.getProperty('write_prolog', True):
			ret = '<?xml version="1.0" encoding="%s"?>\n' % encoding
		ret += root.serialize(encoding = encoding, format = (self.getProperty('prettyprint', False) and 1 or 0))
		return (ret, "XML data")

	def _encode(self, doc, tag, children, attributes, value, cdata, ns, nsMap = {}):
		node = libxml2.newNode(tag)
		if ns:
			# create a prefix for the ns
			if not ns in nsMap:
				nsMap[ns] = 'ns%d' % (len(nsMap) + 1)
			prefix = nsMap[ns]
			node.setNs(node.newNs(ns, prefix))
		for k, v in attributes.items():
			node.setProp(k, v)
		
		if children:
			for (tag, attr) in children:
				node.addChild(self._encode(doc, tag, attr.get('children'), attr.get('attributes', {}), attr.get('value'), attr.get('cdata'), attr.get('ns'), nsMap))
		else:
			if cdata:
				node.addChild(doc.newCDataBlock(value, len(value)))
			else:
				node.addChild(libxml2.newText(value))
		return node
			
	def decode(self, data):
		ret = None
		doc = libxml2.parseDoc(data)
		root = doc.getRootElement()
		ret = self._decode(root)
		doc.freeDoc()
		return (ret, "XML data")

	def _decode(self, element):
		"""
		libxml2 based.
		"""
		tag = element.name
		ns = element.ns()
		if ns: ns = ns.content
		else:
			ns = None

		attributes = {} # attributes are not namespaced...		
		a = element.properties
		while a:
			attributes[a.name] = a.content
			a = a.next

		# If the node has (non-strippable) text nodes and element nodes as children,
		# for instance: "something <i>else</i>, etc"
		# we consider the whole thing as its value.
		
		# If the node has only element nodes as children,
		# the node won't have a value, but only children.
		
		children = []
		hasElementChild = False
		hasTextChild = False
		isMixed = False
		value = ''
		cdata = False

		node = element.children
		while node:
			if node.type == 'cdata':
				if hasElementChild:
					# element contains a mix of text and child elements: retrieves the element content only
					isMixed = True
					break
				else:
					hasTextChild = True
					cdata = True
					value = node.content

			elif node.isText() and node.content.strip():
				if hasElementChild:
					# element contains a mix of text and child elements: retrieves the element content only
					isMixed = True
					break
				else:
					hasTextChild = True
					value = node.content.strip()
			elif node.type == 'element':
				if hasTextChild:
					isMixed = True
					break
				else:
					# let's register the element in the children list
					children.append(self._decode(node))
					hasElementChild = True
			
			node = node.next

		if isMixed:
			d = { 'attributes': attributes, 'cdata': False, 'value': element.content }
			if ns: d['ns'] = ns
			return (tag, d)

		if hasElementChild:
			# only element children
			d = { 'attributes': attributes, 'children': children }
			if ns: d['ns'] = ns
			return (tag, d)

		# no child, or a single text child
		d = { 'attributes': attributes, 'cdata': cdata, 'value': value }
		if ns: d['ns'] = ns
		return (tag, d)
	

CodecManager.registerCodecClass('xml', XmlCodec)


if __name__ == '__main__':
	CodecManager.alias('xml.noprolog', 'xml', write_prolog = False)
	CodecManager.alias('xml.iso', 'xml', encoding = "iso-8859-1", write_prolog = True)
	CodecManager.alias('xml.pretty', 'xml', prettyprint = True)
	
	sampleNoNs = """<?xml version="1.0" encoding="utf-8" ?>
<library owner="John Smith" administrator="Héléna Utf8 and Mickaël Orangina">
	<book isbn="88888-7777788">
		<author>Mickaël Orangina</author>
		<title locale="fr">Tonnerre sous les tropiques</title>
		<title locale="us">Tropic thunder</title>
		<title locale="es">No <i>habla</i> espagnol</title>
		<summary><![CDATA[This is a CDATA section <-> <-- this is a tie fighter]]></summary>
	</book>
</library>
"""

	sampleNs = """<?xml version="1.0" encoding="utf-8" ?>
<library owner="John Smith" administrator="Héléna Utf8 and Mickaël Orangina" xmlns="http://default" xmlns:b="http://base">
	<book isbn="88888-7777788">
		<b:author>Mickaël Orangina</b:author>
		<title locale="fr">Tonnerre sous les tropiques</title>
		<title locale="us">Tropic thunder</title>
		<title locale="es">No <i>habla</i> espagnol</title>
		<b:summary><![CDATA[This is a CDATA section <-> <-- this is a tie fighter]]></b:summary>
	</book>
</library>
"""
	
	for codec in [ 'xml', 'xml.noprolog', 'xml.iso', 'xml.pretty' ]:
		for sample in [ sampleNoNs, sampleNs ]:
			print "%s %s %s" % (40*'=', codec, 40*'=')
			print "decoded with %s:" % codec
			(decoded, _) = CodecManager.decode(codec, sample)
			print decoded
			print
			print "re-encoded with %s:" % codec
			(reencoded, _) = CodecManager.encode(codec, decoded)
			print
			print reencoded
			print "re-decoded with %s:" % codec
			(redecoded, _) = CodecManager.decode(codec,reencoded)
			print redecoded
			assert(decoded == redecoded)
			print
	
	
