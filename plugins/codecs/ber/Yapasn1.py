# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 Sebastien Lefevre and other contributors
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
# Yet Another Python ASN.1 lib (Yapasn1).
# Based on X.690-0207
#
# A BER coder/decoder that can work with
# Tyrannioware's Z3950 ASN.1 compiler's generated specifications.
# (py_output.py file.asn > OutputAsn.py)
#
# #############################################################################
# Contains some code snippets from asn1.py available from
# http://www.pobox.com/~asl2/software/PyZ3950/
# and is licensed under the X Consortium license:
#
# Copyright (c) 2001, Aaron S. Lav, asl2@pobox.com
# All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, and/or sell copies of the Software, and to permit persons
# to whom the Software is furnished to do so, provided that the above
# copyright notice(s) and this permission notice appear in all copies of
# the Software and that both the above copyright notice(s) and this
# permission notice appear in supporting documentation.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
# OF THIRD PARTY RIGHTS. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# HOLDERS INCLUDED IN THIS NOTICE BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL
# INDIRECT OR CONSEQUENTIAL DAMAGES, OR ANY DAMAGES WHATSOEVER RESULTING
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE. 
#
# Except as contained in this notice, the name of a copyright holder
# shall not be used in advertising or otherwise to promote the sale, use
# or other dealings in this Software without prior written authorization
# of the copyright holder. 
##

# Main model:
# An ASN.1 specification is compiled to a Python file
# that contains the Yapasn1 representation of this spec,
# using SyntaxNodes: BooleanSyntaxNode, SequenceSyntaxNode, etc.
#
# These SyntaxNode provides several functions:
# - they can create ValueNodes on decoding from a context
# - they can encode ValueNodes on encoding to a context
#
# SyntaxNodes are organized in trees in the compiled ASN.1 spec.
# ValueNodes are in fact built-in Python types.
# using the following rules:

# boolean -> bool
# integer -> integer
# real -> float (NOT IMPLEMENTED for now)
# bitstring -> dict{string: bool} (upon encoding, non-provided values are assumed to be False) (NOT IMPLEMENTED for now)
# octetstring -> string (buffer)
# enumerated -> string (if well known) or integer
# null -> None
# sequence value -> dict {'fieldName': value}
# sequence of value -> list
# set -> same as sequence
# set of -> same as sequenceof
# choice value -> tuple ('choiceName', value)
# tagged value, undefined -> *discarded* (not decoded)
# any -> string (buffer), undecoded, including base/implicit tag
# external value -> usually as a dict {direct_reference: .., encoding: ...} as described in X.690
# object identifier -> string A.B.C.D.C.D...
# VisibleString -> string
# IA5String -> string
# NumericString -> string
# *String -> NOT IMPLEMENTED for now

# BER Encoding strategies (since multiple options are available):
# - length byte: definite length form (both definite and undefinite forms
#   are supported on decoding) (this is DER/CER compliant, incidentaly)
# - Boolean values set to True are encoding with a content = 0xff (this is DER compliant, by the way)




import math
import binascii

# General syntax tree configuration - maybe it should be left to the compiler...
explicit_tag_environment = False

# Traces
trace_extraction = False
trace_debug = False
trace_decoding = False
trace_encoding = False


UNIVERSAL_FLAG = 0
APPLICATION_FLAG = 0x40
CONTEXT_FLAG = 0x80
PRIVATE_FLAG = 0xC0

CONS_FLAG = 0x20

ANY_TAG = -1 # pseudotag

BOOL_TAG = 0x1
INT_TAG = 0x2
BITSTRING_TAG = 0x3
OCTSTRING_TAG = 0x4
NULL_TAG = 0x5
OID_TAG = 0x6
OBJECTDESCRIPTOR_TAG = 0x7
EXTERNAL_TAG = 0x8
REAL_TAG = 0x9
SEQUENCE_TAG = 0x10
UTF8STRING_TAG = 0xC
NUMERICSTRING_TAG = 0x12
PRINTABLESTRING_TAG = 0x13
T61STRING_TAG = 0x14
VIDEOTEXSTRING_TAG = 0x15
IA5STRING_TAG = 0x16
GENERALIZEDTIME_TAG = 0x18
GRAPHICSTRING_TAG = 0x19
VISIBLESTRING_TAG = 0x1A
GENERALSTRING_TAG = 0x1B
UNIVERSALSTRING_TAG = 0x1C
BMPSTRING_TAG = 0x1E


class BerDecodingError(Exception): pass
class BerEncodingError(Exception): pass

def getBacktrace():
	"""
	Returns the current backtrace.
	"""
	import traceback
	import StringIO
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

##
# Tag management
##

def is_construct(tag):
	flags, val = tag
	return flags & CONS_FLAG

def match_tag(a, b):
	cons_match = (a[0] & ~CONS_FLAG == b[0] & ~CONS_FLAG)
	if (a[1] == ANY_TAG or b[1] == ANY_TAG):
		return cons_match
	return a[1] == b[1] and cons_match

def encode_tag_ber(tag, orig_flags = None):
	"""
	Returns a tag (a, b) encoded to BER.
	@type  tag: (a, b)
	@param tag: (flags, value) where flags is the tag class + form (primitive/constructed indicator)
	"""
	(flags, val) = tag
	# Constructed encoding is property of original tag, not of
	# implicit tag override
	if orig_flags <> None:
		flags = flags | (orig_flags & CONS_FLAG)
	extra = 0
	if val >=0x1F:
		extra = val
		val = 0x1F
	l = chr(flags | val)
	if extra:
		l2 = encode_base128 (extra)
		l += l2
	return l

def decode_tag_ber(buf):
	"""
	Reads the tag at the beginning of buf.
	Returns the read tag and the number of consumed bytes.
	"""
	if trace_debug:
		print "DEBUG: decoding tag from %s" % binascii.hexlify(buf)
	i = 0
	c = ord(buf[i])
	flags = c & 0xe0
	value = c & 0x1f
	i += 1
	if value == 0x1f:
		# Needs to read more bytes
		while c & 0x80:
			c = ord(buf[i])
			value = value * 128 + c & 0x7f
			i += 1
	return ((flags, value), i)

def tag_str(tag, verbose = True):
	flags, value = tag
	if verbose:
		if flags & CONS_FLAG:
			v = " (C)"
		else:
			v = " (P)"
	else:
		v = ''

	cls = flags & ~CONS_FLAG
	labels = { 
		UNIVERSAL_FLAG: 'UNIVERSAL', APPLICATION_FLAG: 'APPLICATION', 
		CONTEXT_FLAG: 'CONTEXT', PRIVATE_FLAG: 'PRIVATE' }

	label = labels.get(cls, 'INVALID')

	return "[%s %s%s]" % (label, value, v)

##
# Low level coders
##
def encode_base128(val):
	"""
	Encodes an integer value to pseudo base128 (i.e. only using 7 bit on each byte).
	@type  val: integer
	@param val: the value to encode.
	@rtype: string/buffer
	"""
	if val == 0:
		return '\0'
	l = []
	while val:
		a, b = divmod(val, 128)
		l.append(b | 0x80) # by default, consider this is the last coding byte
		val = a
	if l:
		l[0] = l[0] & 0x1f # adjust what will become the last byte within its extension bit
	l.reverse()
	return ''.join(map(chr, l))

def read_base128(buf):
	"""
	Decodes/reads an integer value coded in pseudo-base128 from a buffer
	@type  buf: string/buffer
	@rtype: (integer, integer)
	@returns: (value, offset) where offset is the number of consumed bytes.
	"""
	val = 0
	offset = 0
	while 1:
		b = ord(buf[offset])
		offset += 1
		val = val * 128 + (b & 0x7F)
		if b & 0x80 == 0:
			break
	return (val, offset)


def extract_bits(val, lo_bit, hi_bit):
	tmp = (val & (~0L << (lo_bit))) >> lo_bit
	tmp = tmp & ((1L << (hi_bit - lo_bit + 1)) - 1)
	return tmp

def set_bit(val, bit):
	val |= (1 << bit)
	return val

def get_bit(val, bit):
	return val & (1 << bit)

log_of_2 = math.log (2)

def log2(x):
	return int(math.log (x) / log_of_2)

def sgn(val):
	if val < 0: return -1
	if val == 0: return 0
	return 1

##
# Len management
##
def encode_len_ber(mylen):
	if mylen < 128:
		return chr(mylen)
	else:
		l = []
		while mylen:
			l.append (mylen % 256)
			mylen = mylen / 256
		assert (len (l) < 0x80)
		l.append (len (l) | 0x80)
		l.reverse ()
		return ''.join(map(chr, l))

def decode_len_ber(buf):
	"""
	Reads the len at the beginning of buf.
	Returns the read len and the number of consumed bytes.
	the read len is None for end-of-content marked contents.
	"""
	c = ord(buf[0])
	if c > 128:
		# bit 8 was set. Bit 7-1 indicate the number of bytes
		# coding the len
		n = c & 0x7f
		if n == 0: # indefinite form
			return (None, 1)
		else:
			# let's read n additional bytes
			value = 0
			if len(buf) < 1 + n:
				raise BerDecodingError("Unable to decode length: expected %s bytes to code the length, only %s available" % (n+1, len(buf)))
			for c in buf[1:1+n]:
				value = value * 256 + ord(c)
			return (value, 1 + n)
	else:
		# bit 8 not set. Bit 7-1 indicate the length
		value = c & 0x7f
		return (value, 1)
	

################################################################################
# SyntaxNodes
################################################################################

class SyntaxNode:
	"""
	Base class for a Syntax Node.
	Instantiated when creating the SyntaxTree (generated by the Python ASN.1 compiler).
	
	Can be made implicit or explicit tagged by injection.
	"""
	def __init__(self, base_tag, name = None):
		"""
		@type  base_tag: tuple (a, b)
		@param base_tag: the tag for this syntax node. 
		            a corresponds to tag class + form (primitive/constructed indicator)
		            b is the tag number.
		"""
		self._base_tag = base_tag
		self._implicit_tag = None
		self._explicit_tag = None
		self._name = name

	def __str__(self):
		if not self._name:
			name = self.__class__.__name__
		else:
			name = "%s (%s)" % (self._name, self.__class__.__name__)
		if self._implicit_tag:
			return "%s [%s IMPLICIT]" % (name, tag_str(self._implicit_tag))
		elif self._explicit_tag:
			return "%s [%s EXPLICIT]" % (name, tag_str(self._explicit_tag))
		else:
			return "%s %s" % (name, tag_str(self._base_tag))

	def set_implicit_tag(self, tag):
		"""
		Turns the syntax node into an implicit tagged value. 
		(i.e. defined as:
		ThisType ::= [APPLICATION 3] IMPLICIT AnotherType,
		ThisType ::= [2] AnotherType -- with default implicit tagging environment
		ThisType ::= [3] IMPLICIT AnotherType,
		)
		"""
		flags, value = tag
		# Make sure that we keep the same form (at least we cannot pass from C to P)
		c = self._base_tag[0] & CONS_FLAG
		if c: flags |= CONS_FLAG
		self._implicit_tag = (flags, value)
		self._explicit_tag = None

	def set_explicit_tag(self, tag):
		"""
		Turns the syntax node into an explicit tagged value.
		"""
		flags, value = tag
		# If explicit -> constructed, always.
		flags |= CONS_FLAG
		self._explicit_tag = (flags, value)
		self._implicit_tag = None
	
	def encode_ber(self, content, context):
		"""
		BER-Encodes a content.
		
		For convenience, the default implementation takes care of the tag + length bytes,
		and call a self.encode_ber_content leaving you with the responsibility of the actual
		content encoding only.
		
		However, several types that needs to control the way tags are written may override this
		function.
		
		@type  content: a high-level content as acceptable by this syntax node
		@rtype: string/buffer
		@returns: the encoded value (including ALL identifier + length bytes, according to explicit or not tagging)
		"""
		c = self.encode_content_ber(content, context)
		l = encode_len_ber(len(c))
		if self._implicit_tag:
			i = encode_tag_ber(self._implicit_tag)
		else:
			i = encode_tag_ber(self._base_tag)
		ret = i + l + c

		# Now, if we had an explicit tag, add it before as this is a construct.
		if self._explicit_tag:
			l = encode_len_ber(len(ret))
			i = encode_tag_ber(self._explicit_tag)
			ret = i + l + ret
		
		return ret
	
	def match_tag(self, tag):
		"""
		Called by the current syntax node to check if the next tag
		corresponds to this node.
		"""
		if self._explicit_tag:
			return match_tag(self._explicit_tag, tag)
		elif self._implicit_tag:
			return match_tag(self._implicit_tag, tag)
		else:
			return match_tag(self._base_tag, tag)

	def extract_element(self, buf):
		"""
		Reads a buffer assumed to start with a tag
		Returns a tag + content + number of consumed bytes.
		Checks the length.
		"""
		if trace_extraction:
			print "%s: extracting element from %s" % (str(self), binascii.hexlify(buf))
		(tag, tagbytes) = decode_tag_ber(buf)
		buf = buf[tagbytes:]
		(length, lenbytes) = decode_len_ber(buf)
		content = buf[lenbytes:]
		if length is None:
			# undefined form. Search an EOC ("\0\0")
			f = buf.find('\0\0')
			if f < 0:
				raise BerDecodingError("%s: no End-Of-Content found in current buffer for undefinite length for tag %s." % (str(self), tag_str(tag)))
			else:
				content = content[:f]
				lenbytes += 2 # the EOC bytes are consumed, too
		elif length > len(content):
			raise BerDecodingError("%s: Missing bytes when decoding tag %s: expected %s, available %s" % (str(self), tag_str(tag), length, len(buf)))
		else:
			content = content[:length]

		totalbytes = tagbytes + lenbytes + len(content)		
		
		if trace_extraction:
			print "%s: extracted element %s, %s bytes consumed, len %s:\n%s" % (str(self), tag_str(tag), totalbytes, len(content), binascii.hexlify(content))
		return (tag, content, totalbytes)
		
	def decode_ber(self, tag, buf, context):
		"""
		BER-Decodes a buffer.
		The buf is assumed to be decodable with this SyntaxNode,
		i.e. it has been explicitly selected as is by the user (decoding bootstrap)
		or selected dynamically after tag matching.
		
		@type  tag: tuple (flags, value)
		@param tag: the seen tag
		@type  buf: string/buffer
		@param buf: the buffer to decode, already to the correct length (no incremental decoding).
		This buf does not contain the explicit or implicit tag.
		However, if this syntaxnode is explicitly tagged, you should expect a
		the base_tag + length as first bytes of the given buf.
		"""
		if self._explicit_tag:
			# Check that we have the base tag construct
			(tag, content, consumedbytes) = self.extract_element(buf)
			if not match_tag(tag, self._base_tag):
				# In some samples, I ran into the following cases: a sequence was both explicit and implicitly tagged.
				# Normally, since it is explicitly tagged it should be useless to check the base tag.
				# But when checked, we got this error.
				raise BerDecodingError("%s: expected base tag %s, got %s" % (str(self), tag_str(self._base_tag), tag_str(tag)))
		else:
			content = buf	
		# OK, now we can decode the content.
		return self.decode_content_ber(tag, content, context)
	
	##
	# To reimplement
	##
	def encode_content_ber(self, content, context):
		"""
		To reimplement in each SyntaxNode.
		"""
		raise BerEncodingError("%s: Content encoding not implemented" % str(self))
	
	def decode_content_ber(self, tag, buf, context):
		"""
		To reimplement in each SyntaxNode.
		@param  tag: the tag that led to this SyntaxNode
		@param  buf: the content buffer for this SyntaxNode, according to read length bytes.
		             This buffer does not contain the tag nor the length bytes any more.
		"""
		raise BerDecodingError("%s: Content decoding not implemented" % str(self))

	def value_from_str(self, s):
		"""
		Returns a structured value from a ASN.1 value representation.
		Used to deduce default values representation.
		"""
		return None

################################################################################
# Actual Nodes
################################################################################

################################################################################
# boolean
################################################################################
class BooleanSyntaxNode(SyntaxNode):	
	def __init__(self):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, BOOL_TAG))
	
	def decode_content_ber(self, tag, buf, context):
		if len(buf) != 1:
			raise BerDecodingError("%s: invalid boolean encoding (%s bytes instead of 1)" % (str(self), len(buf)))
		if ord(buf[0]):
			return True
		else:
			return False
	
	def encode_content_ber(self, content, context):
		if content:
			return '\xff'
		else:
			return '\x00'

	def value_from_str(self, s):
		if s.tolower() in [ 'false' ]:
			return False
		else:
			return True

################################################################################
# integer
################################################################################
class IntegerSyntaxNode(SyntaxNode):
	def __init__(self, range_constraint = None):
		"""
		@type  range_constraint: tuple (integer, integer) or None
		@param range_constraint: tuple (min, max) (included)
		"""
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, INT_TAG))
		self._range_constraint = range_constraint
	
	def _match_constraint(self, val):
		if self._range_constraint:
			a, b = self._range_constraint
			if a is None:
				if b is None:
					return True
				else:
					return val <= b
			else:
				if b is None:
					return True
				else:
					return val >= a
		else:
			return True
	
	def decode_content_ber(self, tag, buf, context):
		val = 0
		if ord(buf[0]) >= 128: sgn = -1
		else: sgn = 1
		for b in buf:
			b = ord(b)
			val = 256 * val + sgn * b
		if sgn == -1:
			val = - (val + pow (2, 8 * len (buf)))
			# XXX should be much more efficient decoder here
		
		if not self._match_constraint(val):
			a, b = self._range_constraint
			raise BerDecodingError('%s: integer %s violates constraint [%s..%s]' % (str(self), val, a, b))
		return val

	def encode_content_ber(self, content, context):
		if not isinstance(content, int):
			raise BerEncodingError('%s: Expected an integer, got something else' % str(self))
		val = content
		if not self._match_constraint(val):
			a, b = self._range_constraint
			raise BerEncodingError('%s: integer %s violates constraint [%s..%s]' % (str(self), val, a, b))

		# based on ber.py in pysnmp
		l = []
		if val == 0:
			l = [0]
		elif val == -1:
			l = [0xFF]
		else:
			if sgn (val) == -1:
				term_cond = -1
				last_hi = 1
			else:
				term_cond = 0
				last_hi = 0
			while val != term_cond:
				val, res = val >> 8, (val & 0xFF)
				l.append(res)
			if (l[-1] & 0x80 <> 0) ^ last_hi:
				l.append(last_hi * 0xFF)
		l.reverse()
		return ''.join(map(chr, l))

	def value_from_str(self, s):
		return int(s)
	
################################################################################
# enumerated
################################################################################
class EnumeratedSyntaxNode(IntegerSyntaxNode):
	def __init__(self):
		IntegerSyntaxNode.__init__(self)
		self._values = {}
	
	def addValue(self, name, value):
		self._values[name] = value
	
	def decode_content_ber(self, tag, buf, context):
		val = IntegerSyntaxNode.decode_content_ber(self, tag, buf, context)
		for k, v in self._values.items():
			if v == val:
				return k
		# Unknown value. We assume that we have an open enum.
		return val
	
	def encode_content_ber(self, content, context):
		val = None
		if isinstance(content, basestring):
			if self._values.has_key(content):
				val = self._values[content]
			else:
				raise BerEncodingError('%s: Invalid enum %s' % (str(self), content))
		elif isinstance(content, int):
			val = content
		else:
			raise BerEncodingError('%s: Invalid enum to encode, expected a string or a int')
		return IntegerSyntaxNode.encode_content_ber(self, val, context)

################################################################################
# real
################################################################################
class RealSyntaxNode(SyntaxNode):
	def __init__(self):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, REAL_TAG))

	def decode_content_ber(self, tag, buf, context):
		# Not implemented yet
		return buf		

	def encode_content_ber(self, content, context):
		# Not implemented yet
		return content

	def value_from_str(self, s):
		return float(s)

################################################################################
# bitstring
################################################################################
class BitstringSyntaxNode(SyntaxNode):
	"""
	Can be constructed or primitive at the sender's option.
	We only send primitive forms,
	but can decode both.
	"""
	def __init__(self):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, BITSTRING_TAG))
		self._bitmap_by_bit = {}
		self._bitmap_by_name = {}
	
	def addBitmap(self, name, bit):
		"""
		@param  bit: the bit number
		@param  name: the mapping name corresponding to this bit
		"""
		self._bitmap_by_bit[bit] = name
		self._bitmap_by_name[name] = bit

	def decode_content_ber(self, tag, buf, context):
		# Not yet implemented
		if is_construct(tag):
			raise BerDecodingError("%s: BIT STRING construct decoding it not yet implemented" % str(self))		
		else:
			# Read first byte
			trailing_bit_count = ord(buf[0]) & 0x7f
			current_bit = 0
			ret = {}
			for byte in buf[1:]:
				for b in range(0, 8):
					name = self._bitmap_by_bit.get(current_bit, None)
					current_bit += 1
					if name is None:
						continue # possible gap between 2 flags, trailing bits
					flag = ord(byte) & (0x80 >> b) 
					if flag:
						ret[name] = True
					else:
						ret[name] = False
			return ret				

	def encode_content_ber(self, content, context):
		bc = self._useful_bit_count()
		if bc == 0:
			return '\x00' # Empty bitstring
		
		# nb of coding bytes
		nb, remaining = divmod(bc, 8)
		# First byte: the number of useless bits in the last byte.
		ret = [ (remaining % 8) & 0x80 ]
		for _ in range(max(nb, 1)):
			ret.append(0x00)
		
		for name, val in content.items():
			if not name in self._bitmap_by_name:
				raise BerEncodingError("%s: Invalid bit string name '%s'" % (str(self), name))
			else:
				if val:
					bit = self._bitmap_by_name[name]
					a, b = divmod(bit, 8)
					ret[1 + a] |= (0x80 >> b) # set the bth bit (bit 1 = msb) of the ath coding byte
		
		return ''.join(map(chr, ret))
	
	def _useful_bit_count(self):
		return max(self._bitmap_by_bit.keys()) + 1
	
	def value_from_str(self, s):
		"""
		s is something like fieldName[,fieldname]*
		"""
		ret = {}
		for name in s.split(','):
			ret[name.strip()] = True
		return ret
	

################################################################################
# Octetstring
################################################################################
##
# All string types are based on the Octetstring,
# that gets a particular codec according to the actual syntax node tag.
##
class OctetstringSyntaxNode(SyntaxNode):
	"""
	May be primitive or constructed.
	Always sent as primitive,
	but can be received as both.
	"""
	def __init__(self, base_tag = (UNIVERSAL_FLAG, OCTSTRING_TAG), length_constraint = None,):
		"""
		@type  length_constraint: tuple (integer, integer) or None
		@param length_constraint: tuple (min, max) (included)
		"""
		SyntaxNode.__init__(self, base_tag = base_tag)
		self._length_constraint = length_constraint

	def decode_content_ber(self, tag, buf, context):
		if is_construct(tag):
			ret = []
			while buf:
				(t, element, length) = self.extract_element(buf)
				buf = buf[length:]
				ret.append(self.decode_content_ber(t, element, context))
			return ''.join(ret)
		else:
			return self.from_buf(buf)
	
	def encode_content_ber(self, content, context):
		if not isinstance(content, basestring):
			raise BerEncodingError('%s: invalid value to encode, expected a string' % str(self))
		return self.to_buf(content)

	def from_buf(self, buf):
		"""
		To reimplement in each *String subclass. BER/PER/...-independent.
		"""
		return buf
	
	def to_buf(self, content):
		"""
		To reimplement in each *String subclass. BER/PER/...-independent.
		"""
		return content
	

class IA5StringSyntaxNode(OctetstringSyntaxNode):
	def __init__(self, length_constraint = None):
		OctetstringSyntaxNode.__init__(self, (UNIVERSAL_FLAG, IA5STRING_TAG), length_constraint)
	
	def from_buf(self, buf):
		return buf
	
	def to_buf(self, content):
		if isinstance(content, unicode):
			return content.encode('ascii')
		else:
			return content


class VisibleStringSyntaxNode(OctetstringSyntaxNode):
	def __init__(self, length_constraint = None):
		OctetstringSyntaxNode.__init__(self, (UNIVERSAL_FLAG, VISIBLESTRING_TAG), length_constraint)

	def from_buf(self, buf):
		return buf

	def to_buf(self, content):
		if isinstance(content, unicode):
			return content.encode('ascii')
		else:
			return content


################################################################################
# Null value
################################################################################
class NullSyntaxNode(SyntaxNode):
	"""
	Primitive only.
	"""
	def __init__(self):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, NULL_TAG))
	
	def decode_content_ber(self, tag, buf, context):
		if buf:
			raise BerDecodingError('%s: non empty content for NULL value' % str(self))
		return None
	
	def encode_content_ber(self, content, context):
		# ignore the content even if it's not None
		return ''


################################################################################
# Sequence
################################################################################
class SequenceSyntaxNode(SyntaxNode):
	"""
	Constructed only.
	"""
	def __init__(self, name):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG | CONS_FLAG, SEQUENCE_TAG), name = name)
		self._fields = []
	
	def addField(self, name, syntaxNode, optional = False, default = None):
		"""
		Declare a new field in the sequence.
		"""
		self._fields.append((name, syntaxNode, optional, (default is not None and syntaxNode.value_from_str(default)) or None))
	
	def decode_content_ber(self, tag, buf, context):
		"""
		While contents remain, read the tag + length, call the associated decoder, etc.
		"""
		ret = {}
		last_field_index = 0
		
		while buf:
			(tag, content, consumedbytes) = self.extract_element(buf)
			buf = buf[consumedbytes:]
			# Now match the tag against one of our possible field - order matters
			found = False
			i = 0
			for name, sn, _, _ in self._fields[last_field_index:]:
				i += 1
				if sn.match_tag(tag):
					if trace_decoding:
						print "%s: found field '%s', decoding..." % (str(self), name)
					ret[name] = sn.decode_ber(tag, content, context)
					if trace_decoding:
						print "%s: field '%s' decoded" % (str(self), name)
					found = True
					last_field_index = last_field_index + i # Make sure we detect the field only once and in the correct order.
					break

			if not found:
				if trace_decoding:
					print("%s: INFO: consumed an unexpected field in sequence, tag %s" % (str(self), tag_str(tag)))
		
		# Check if this is satisfying or not
		for name, sn, optional, default in self._fields:
			if not name in ret:
				if not optional:
					raise BerDecodingError("%s: Missing mandatory field '%s' in sequence" % (str(self), name))
				elif default is not None:
					# Create the default value (if available) so that the application sees it
					ret[name] = default
					if trace_decoding:
						print "%s: field '%s' not present on the wire, filled with its default value %s" % (str(self), name, repr(default))
		# OK
		return ret
	
	def encode_content_ber(self, content, context):
		if not isinstance(content, dict):
			raise BerEncodingError("%s: invalid content to encode, expected a dict" % (str(self)))

		buf = []
		for name, sn, optional, default in self._fields:
			if content.has_key(name):
				buf.append(sn.encode_ber(content[name], context))
				if trace_encoding:
					print "%s: field '%s' encoded in sequence:\n%s" % (str(self), name, binascii.hexlify(buf[-1]))
			elif not optional:
				# NB: default values are not encoded.
				raise BerEncodingError("%s: missing mandatory field '%s' in sequence" % (str(self), name))

		return ''.join(buf)
		
		
################################################################################
# Sequence Of
################################################################################
class SequenceOfSyntaxNode(SyntaxNode):
	"""
	Constructed only.
	"""
	def __init__(self, syntaxNode):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG | CONS_FLAG, SEQUENCE_TAG))
		self._syntaxNode = syntaxNode
	
	def decode_content_ber(self, tag, buf, context):
		"""
		While contents remain, read the tag + length, call the associated decoder, etc.
		"""
		ret = []
		
		while buf:
			(tag, content, consumedbytes) = self.extract_element(buf)
			buf = buf[consumedbytes:]
			if not self._syntaxNode.match_tag(tag):
				raise BerDecodingError("%s: invalid element in SEQUENCE OF: got %s" % (str(self), tag_str(tag)))
			ret.append(self._syntaxNode.decode_ber(tag, content, context))
		
		# OK
		return ret
	
	def encode_content_ber(self, content, context):
		if not isinstance(content, list):
			raise BerEncodingError("%s: invalid content to encode, expected a list" % (str(self)))
		buf = []
		for c in content:
			buf.append(self._syntaxNode.encode_ber(c, context))
		return ''.join(buf)

################################################################################
# Choice
################################################################################
class ChoiceSyntaxNode(SyntaxNode):
	"""
	May be constructed or primitive, depending on the chosen type.
	"""
	def __init__(self, name = None):
		"""
		"""
		SyntaxNode.__init__(self, base_tag = (0, -1), name = name)
		self._choices = []
	
	def addChoice(self, name, syntaxNode):
		self._choices.append((name, syntaxNode))
	
	def match_tag(self, tag):
		"""
		Overrides SyntaxNode match_tag, since this node tag can be
		any of its choices.
		"""
		if self._explicit_tag:
			return match_tag(self._explicit_tag, tag)
		else:
			for name, sn in self._choices:
				if sn.match_tag(tag):
					return True
			return False
	
	def set_implicit_tag(self, tag):
		# A choice cannot be implicitly tagged. Even in implicit tag environnments,
		# this is reverted to an explicit.
		return self.set_explicit_tag(tag)

	def decode_content_ber(self, tag, buf, context):
		# The tag is the seen (base) tag, i.e. it selects the choice.
		for name, sn in self._choices:
			if sn.match_tag(tag):
				return (name, sn.decode_ber(tag, buf, context))
		# No match - either an invalid choice or an open choice. For now, not open.
		raise BerDecodingError("%s: Unsupported tag %s in choice" % (str(self), tag_str(tag)))
	
	def encode_ber(self, content, context):
		"""
		Reimplemeted so that we ensure that we use the chosen tag.
		"""
		if not isinstance(content, tuple) and len(content) == 2 and isinstance(content[0], basestring):
			raise BerEncodingError("%s: Invalid value to encode, expecting a tuple (string, value)" % (str(self)))
		name, value = content
		for n, sn in self._choices:
			if name == n:
				# Found corresponding choice
				c = sn.encode_ber(value, context)
				if trace_encoding:
					print "%s: choice branch '%s' encoded as:\n%s" % (str(self), name, binascii.hexlify(c))
				# encoded, with the choice tag.
				# Now add our explicit tag if any
				if self._explicit_tag:
					l = encode_len_ber(len(c))
					i = encode_tag_ber(self._explicit_tag)
					return i + l + c
				else:
					return c
				
		raise BerEncodingError("%s: Invalid choice %s" % (str(self), name))
		
	
################################################################################
# Object Identifier
################################################################################
class ObjectIdentifierSyntaxNode(SyntaxNode):
	"""
	Primitive form only.
	"""
	def __init__(self):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, OID_TAG))
	
	def encode_content_ber(self, content, context):
		if not isinstance(content, basestring):
			raise BerEncodingError("%s: Invalid OID format, expecting a string" % str(self))
		try:
			ids = map(int, content.split('.'))
		except:
			raise BerEncodingError("%s: Invalid OID format, expecting a dot-digits notation" % str(self))
		
		encoded = [ chr(40*ids[0] + ids[1]) ] # what if > 256 ??
		for val in ids[2:]:
			encoded.append(encode_base128(val))
		if trace_encoding:
			print "%s: Encoded OID:\n%s" % (str(self), binascii.hexlify(''.join(encoded)))
		return ''.join(encoded)
	
	def decode_content_ber(self, tag, buf, context):
		if trace_decoding:
			print "%s: Decoding OID:\n%s" % (str(self), binascii.hexlify(buf))
		a, b = divmod(ord(buf[0]), 40)
		oid =  [ a, b ]
		start = 1
		mylen = len(buf)
		while start < mylen:
			val, consumed = read_base128(buf[start:])
			start += consumed
			oid.append(val)
		return '.'.join(map(str, oid))


################################################################################
# Object Descriptor
################################################################################
class ObjectDescriptorSyntaxNode(SyntaxNode):
	"""
	??
	"""
	def __init__(self):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, OID_TAG))


################################################################################
# Any
################################################################################
class AnySyntaxNode(SyntaxNode):
	"""
	The buffer is not parsed and returned as is, including its identifiers
	(explicit or not) and len bytes.
	"""
	def __init__(self):
		SyntaxNode.__init__(self, base_tag = (UNIVERSAL_FLAG, ANY_TAG))
	
	def decode_ber(self, tag, buf, context):
		"""
		Overrides the SyntaxNode complete decoding. 
		If we are EXPLICIT tagged, buf contains the base_tag.
		If not, buf does not contain any tag.
		In the later case, re-dump the base tag so that the application that will
		get the raw buffer can manage it.
		"""
		if not self._explicit_tag:
			l = encode_len_ber(len(buf))
			i = encode_tag_ber(tag)
			return i + l + buf
		else:
			return buf
	
	def encode_ber(self, content, context):
		"""
		Keeps the buffer as is, but add the explicit tag, if any.
		"""
		if self._explicit_tag:
			l = encode_len_ber(len(content))
			i = encode_tag_ber(self._explicit_tag)
			return i + l + content
		else:
			return content


################################################################################
# External
################################################################################
class ExternalSyntaxNode(SequenceSyntaxNode):
	"""
	Following X.690, External is defined as:
	
	[UNIVERSAL 8] IMPLICIT SEQUENCE {
		direct-reference      OBJECT IDENTIFIER OPTIONAL,
		indirect-reference    INTEGER OPTIONAL,
		data-value-descriptor ObjectDescriptor OPTIONAL,
		encoding              CHOICE {
		                        single-ASN1-type [0] ABSTRACT-SYNTAX.&Type, -- "ANY"
		                        octet-aligned [1] IMPLICIT OCTET STRING,
		                        arbitrary [2] IMPLICIT BIT STRING
		                      }
	} 
	"""
	def __init__(self):
		SequenceSyntaxNode.__init__(self, name = "EXTERNAL")
		self._base_tag = (UNIVERSAL_FLAG | CONS_FLAG, EXTERNAL_TAG)
		self.addField('direct-reference', ObjectIdentifierSyntaxNode(), True)
#		self.addField('data-value-descriptor', ObjectDescriptorSyntaxNode(), True)
		self.addField('indirect-reference', IntegerSyntaxNode(), True)
		encChoice = ChoiceSyntaxNode(name = 'Encoding')
		a = AnySyntaxNode()
		a.set_explicit_tag((CONTEXT_FLAG, 0))
		encChoice.addChoice('single-ASN1-type', a)
		b = OctetstringSyntaxNode()
		b.set_explicit_tag((CONTEXT_FLAG, 1))
		encChoice.addChoice('octet-aligned', b)
		c = BitstringSyntaxNode()
		c.set_explicit_tag((CONTEXT_FLAG, 2))
		encChoice.addChoice('arbitraty', c)
		self.addField('encoding', encChoice, True)


################################################################################
# General functions - bootstrappers to encode/decode value trees
################################################################################

def encode(syntax, content):
	return syntax.encode_ber(content, None)

def decode(syntax, buf):
	(tag, content, _) = syntax.extract_element(buf)
	if not syntax.match_tag(tag):
		raise BerDecodingError("The root PDU is incorrect, mismatching tags")
	return syntax.decode_ber(tag, content, None)

################################################################################
# Compatibility with Z3950's ASN.1 compiler's output:
# Helpers to define the Syntax Tree.
################################################################################

def EXPLICIT(value, cls = CONTEXT_FLAG):
	# Returns a tag for next use as explicit with TYPE
	# (explicit, protocolClass, value)
	return (True, cls, value)

def IMPLICIT(value, cls = CONTEXT_FLAG):
	# Returns a tag for next use as implicit with TYPE
	# (explicit, protocolClass, value)
	return (False, cls, value)

import copy 

def TYPE(tag, syntaxNode):
	# creates a copy of the syntax node to turns into a particular tagged syntax node
	if trace_debug:
		print "DEBUG: tagging %s with %s..." % (syntaxNode, tag)
	sn = copy.deepcopy(syntaxNode)
	explicit, flags, value = tag
	if explicit:
		sn.set_explicit_tag((flags, value))
	else:
		sn.set_implicit_tag((flags, value))
	return sn

def SEQUENCE(seq, seq_name):
	"""
	seq is a list of (name, ?, syntaxNode, optional) tuple
	"""
	sn = SequenceSyntaxNode(name = seq_name)
	for name, _, syntaxNode, optional, default in seq:
		sn.addField(name, syntaxNode, optional, default)
	return sn

def INTEGER_class(unknown, range_min, range_max):
	sn = IntegerSyntaxNode(range_constraint = (range_min, range_max))
	return sn

def SEQUENCE_OF(syntaxNode):
	return SequenceOfSyntaxNode(syntaxNode)

# To rework
def SET(seq, seq_name):
	return SEQUENCE(seq, seq_name)

# To rework
def SET_OF(syntaxNode):
	return SEQUENCE_OF(syntaxNode)

def CHOICE(choices):
	sn = ChoiceSyntaxNode()
	for name, tag, syntaxNode in choices:
		if tag is not None:
			sn.addChoice(name, TYPE(tag, syntaxNode))
		else:
			# format name, None, type
			sn.addChoice(name, syntaxNode)
	return sn

def ENUM(values):
	"""
	values is a dict string: number (new syntax, not
	asn1.py compliant) 
	"""
	sn = EnumeratedSyntaxNode()
	for k, v in values.items():
		sn.addValue(k, v)
	return sn

def BITSTRING_class(bits, a, b):
	sn = BitstringSyntaxNode()
	for name, bit in bits:
		sn.addBitmap(name, bit)
	return sn

OBJECT_IDENTIFIER = ObjectIdentifierSyntaxNode()
INTEGER = IntegerSyntaxNode()
OCTSTRING = OctetstringSyntaxNode()
NULL = NullSyntaxNode()
BOOLEAN = BooleanSyntaxNode()
BITSTRING = BitstringSyntaxNode()
ANY = AnySyntaxNode()
EXTERNAL = ExternalSyntaxNode()
VisibleString = VisibleStringSyntaxNode()
NumericString = VisibleStringSyntaxNode()
ObjectDescriptor = ObjectDescriptorSyntaxNode()

