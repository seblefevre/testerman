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
# Adaptation layer between tyrannioware ASN.1 model
# and Testerman userland message model
##

import asn1

TAG_NUMBER_MAP = {
asn1.END_INDEF_CONS_TAG: 'EOC',
asn1.BOOL_TAG: 'BOOLEAN',
asn1.INT_TAG: 'INTEGER',
asn1.BITSTRING_TAG: 'BIT STRING',
asn1.OCTSTRING_TAG: 'OCTET STRING',
asn1.NULL_TAG: 'NULL',
asn1.OID_TAG: 'OBJECT IDENTIFIER',
asn1.OBJECTDESCRIPTOR_TAG: 'Object Descriptor',
asn1.EXTERNAL_TAG: 'EXTERNAL',
asn1.REAL_TAG: 'REAL',
asn1.SEQUENCE_TAG: 'SEQUENCE',
asn1.UTF8STRING_TAG: 'UTF8String',
asn1.NUMERICSTRING_TAG: 'NumericString',
asn1.PRINTABLESTRING_TAG: 'PrintableString',
asn1.T61STRING_TAG: 'T61String',
asn1.VIDEOTEXSTRING_TAG: 'VideotextString',
asn1.IA5STRING_TAG: 'IA5String',
asn1.GENERALIZEDTIME_TAG: 'GeneralizedTime',
asn1.GRAPHICSTRING_TAG: 'GraphicString',
asn1.VISIBLESTRING_TAG: 'VisibleString',
asn1.GENERALSTRING_TAG: 'GeneralString',
asn1.UNIVERSALSTRING_TAG: 'UniversalString',
asn1.BMPSTRING_TAG: 'BMPString',
}


import string
import array
import binascii

def isPrintable(s):
	for i in s:
		if not i in string.printable:
			return False


def toTesterman(obj):
	"""
	Returns the Testerman userland message
	representation of a asn1.py decoded object.
	"""
	return _toTesterman(obj)

def _toTesterman(obj):
	"""
	Recursive function that turns a
	asn1.py decoded objet into a Testerman userland message
	(couple, list, float, int, string, dict only)
	"""
	# Primitives

	# OID -> numeric only, dot notation (really adapted ?)
	if isinstance(obj, asn1.OidVal):
		return '.'.join(['%d' % i for i in obj.lst])

	# Strings* -> str (buffer)
	elif isinstance(obj, str):
		return obj

	# Int -> int
	elif isinstance(obj, int):
		return obj

	# Float -> float
	elif isinstance(obj, float):
		return obj

	# Constructs

	# CHOICE -> tuple (choiceName, value)  (valued as (a, b) by asn1 module)
	elif isinstance(obj, tuple):
		# Let's analyze the tag.
		# string tag: the tag was fully known
		tag = obj[0]
		if isinstance(tag, tuple):
#			# Unknown tag. Let's map it to something.
#			classMap = { 0: 'universal', 64: 'application', 128: 'context', 192: 'private' }
#			pcMap = { 0: 'p', 32: 'c' } # p = primitive, c = construct
#			choiceName = "%s.%s.%s" % (classMap[tag[0] & 0xc0], pcMap[tag[0] & 0x20], TAG_NUMBER_MAP.get(tag[1], str(tag[1])))
			# Unknown tag -> raw buffer so that a higher codec could decode it if needed
			return asn1.encode(asn1.ANY, obj).tostring()
			
		elif isinstance(tag, str):
			# Known choice.
			choiceName = tag
			
			if tag == 'single-ASN1-type':
				# Reencode it to an octetstring - we do not want 
				# blind construct decoding at that level
				return ('single-ASN1-type', asn1.encode(asn1.ANY, obj[1]).tostring())
		else:
			raise Exception("Invalid tag format: %s" % str(obj[0]))
		return (choiceName, _toTesterman(obj[1]))

	# SEQUENCE -> dict (valued as StructBase by asn1 module)
	elif isinstance(obj, asn1.StructBase):
		# Transforms it to a dict of field names
		ret = {}
		for n, v in obj.__dict__.items():
			if n != '_allowed_attribs':
				ret[n] = _toTesterman(v)
		return ret

	# SEQUENCE OF -> list (valued as list by asn1 module)
	elif isinstance(obj, list):
		ret = []
		for n in obj:
			ret.append(_toTesterman(n))
		return ret

 	else:
		return "unsupported: " + obj.__class__.__name__


def prettyprint(message):
	"""
	Pretty prints a Testerman message.
	"""
	_prettyprint(message, 0)

def _prettyprint(message, indent):
	"""
	Recursive function to pretty print a Testerman
	message.
	"""
	if isinstance(message, tuple):
		print '%sCHOICE [%s, ' % (indent*' ', message[0])
		_prettyprint(message[1], indent + 2)
		print '%s]' % (indent*' ')

	elif isinstance(message, dict):
		d = message.items()
		d.sort()
		print '%sSEQUENCE:' % (indent*' ')
		for n, v in d:
			print '%s %s =' % (indent*' ', n)
			_prettyprint(v, indent + 2)

	elif isinstance(message, list):
		print '%sSEQUENCE OF [' % (indent*' ')
		for l in message:
			_prettyprint(l, indent + 2)
		print '%s]' % (indent*' ')

	elif isinstance(message, basestring):
		if not isPrintable(message):
			m = binascii.hexlify(message)
		else:
			m = message
		print '%s%s' % (indent*' ', m)

	else:
		print '%s%s' % (indent*' ', message)


def isOid(s):
	"""
	Checks if a string could be an OID representation
	(A.B.C.D.E....) with only digits
	"""
	dot = 0
	for c in s:
		if not c in "0123456789.":
			return False
	
	# Check that we have at least 2 dots (A.B.C) 
	# and no 2 consecutive dots
	l = s.split('.')
	if len(l) < 2:
		return False
	for d in l:
		if not d:
			return False # empty digits -> i.e. 2 consecutive dots.
	return True


def fromTesterman(message):
	"""
	Converts a Testerman userland message
	to a struct that can be used by asn1.py
	for encoding.
	"""
	return _fromTesterman(message)

def _fromTesterman(message):
	"""
	Recursive function to create a asn1.py compliant
	structure from a Testerman userland message.
	"""
	if isinstance(message, dict):
		# SEQUENCE
		ret = asn1.StructBase()
		for key, val in message.items():
			setattr(ret, key, _fromTesterman(val))
		return ret
	
	elif isinstance(message, list):
		# SEQUENCE OF
		ret = []
		for val in message:
			ret.append(_fromTesterman(val))
		return ret
	
	elif isinstance(message, tuple):
		# CHOICE
		name, val = message
		return (name, _fromTesterman(val))
	
	elif isinstance(message, basestring):
		# OK, now things are more complicated.
		# Could be a raw buffer to a ANY, 
		# a String*, OID...
		
		# OID autodetection:
		# a string that contains only digits and .
		if isOid(message):
			return asn1.OidVal([int(x) for x in message.split('.')])
		
		# If it's a ANY, we should decode it
		try:
			d = asn1.decode(asn1.ANY, message)
			return d
		except Exception, e:
#			print "The following buffer is not a ANY struct (%s):\n%s" % (str(e), repr(message))
			# Normal string ??
			return message
		
	else:
		return message
