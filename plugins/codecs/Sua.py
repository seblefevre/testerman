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
# SUA (SCCP User Adaption) codec.
#
# Based on RFC3868.
#
# Implemented as an incremental codec.
#
##

import CodecManager

import xdrlib
import binascii

def tbcd2string(tbcd, length):
	"""
	Returns an ascii string corresponding to telephony bcd buffer.
	
	Example: "\x21\xf3" -> "123"
	"""
	# Reads demi-byte
	digits = []
	for c in tbcd:
		digits.append(str(ord(c) & 0x0f))
		digits.append(str((ord(c) & 0xf0) >> 4))
	
	return ''.join(digits)[:length]


def string2tbcd(digits, filler = 0x0f):
	"""
	Returns a buffer corresponding to the Telephoby BCD representation
	of digits, which is digits in a string.
	
	Example: "123" -> "\x21\xf3"
	"""
	bytes = []
	l = len(digits)
	i = 0
	while i < l:
		b = (ord(digits[i]) - ord('0')) & 0x0f
		i += 1
		if i == l:
			b |= filler << 4
		else:
			b |= ((ord(digits[i]) - ord('0')) & 0x0f) << 4
		i += 1
		bytes.append(b)	

	return ''.join(map(chr, bytes))


class InvalidMessageException(Exception): pass
class IncompleteMessageException(Exception): pass

def decodeParameters(data):
	remainingBytes = len(data)
	unpacker = xdrlib.Unpacker(data)
	print "DEBUG: decoding parameters from %s (len = %s)" % (binascii.hexlify(data), remainingBytes)
	ret = []		
	while remainingBytes >= 8:
		(bytes, parameter) = decodeParameter(unpacker, remainingBytes)
		ret.append(parameter)
		remainingBytes -= bytes
	return ret

def encodeParameters(parameters):
	"""
	Encodes a testerman messaged to a buffer.
	The result is not padded.
	"""
	packer = xdrlib.Packer()
	if parameters:
		for p in parameters:
			encodeParameter(p, packer)
	return packer.get_buffer()

MessageClasses = {
	0: ('MGMT (SUA Management)', {0: 'ERR', 1: 'NTFY'}),
	2: ('SNM (Signalling Network Management)', {1: 'DUNA', 2: 'DAVA', 3: 'DAUD', 4: 'SCON', 5: 'DUPU', 6: 'DRST'}),
	3: ('ASPSM (ASP State Maintenance)', {1: 'UP', 2: 'DOWN', 3: 'BEAT', 4: 'UP ACK', 5: 'DOWN ACK', 6: 'BEAT ACK'}),
	4: ('ASPTM (ASP Traffic Maintenance)', {1: 'ACTIVE', 2: 'INACTIVE', 3: 'ACTIVE ACK', 4: 'INACTIVE ACK'}),
	7: ('CL (Connectionless)', {1: 'CLDT', 2: 'CLDR'}),
	8: ('CO (Connection-Oriented)', {1: 'CORE', 2: 'COAK', 3: 'COREF', 4: 'RELRE', 5: 'RELCO', 6: 'RESCO', 7: 'RESRE', 8: 'CODT', 9: 'CODA', 10: 'COERR', 11: 'COIT'}),
	9: ('RKM (Routing Key Management)', {1: 'REG REQ', 2: 'REG RSP', 3: 'DEREG REQ', 4: 'DEREG RSP'}),
}


class Message:
	def __init__(self):
		self.version = None
		self.messageClass = None
		self.messageType = None
		self.parameters = []
		self.decodedLength = None

	def fromNetwork(self, data):
		unpacker = xdrlib.Unpacker(data)
		self._decode(unpacker, len(data))
	
	def toNetwork(self):
		packer = xdrlib.Packer()
		self._encode(packer)
		return packer.get_buffer()
	
	def fromUserland(self, message):
		self.version = message.get('version', 1)
		self.messageClass = message['class']
		self.messageType = message['type']
		self.parameters = message.get('parameters', [])
	
	def toUserland(self):
		ret = {'version': self.version, 
		'class': self.messageClass, 
		'type': self.messageType, 'parameters': self.parameters,
		}
		(label, typeLabels) = MessageClasses.get(self.messageClass, ('Reserved/Unknown', {}))
		ret['classLabel'] = label
		ret['typeLabel'] = typeLabels.get(self.messageType, 'Reserved/Unknown')
		return ret
	
	def summary(self):
		(label, typeLabels) = MessageClasses.get(self.messageClass, ('Reserved/Unknown', {}))
		return "%s %s" % (label.split(' ')[0], typeLabels.get(self.messageType, 'Reserved/Unknown'))
	
	def _decode(self, unpacker, bytes):
		"""
		Actually decodes and checks the header,
		then calls parameter decoders once sure that
		we have all the required bytes to decode the whole message.
		"""
		if bytes < 8:
			# Expect a strict minimal header
			raise IncompleteMessageException("Incomplete message header")
		
		# First 4 bytes: version | reserved | class | type
		h = unpacker.unpack_uint()
		self.version = h >> 24
		self.messageClass = h >> 8 & 0xff
		self.messageType = h & 0xff
		
		if self.version != 1:
			raise InvalidMessageException("Unsupported SUA version (%s)" % self.version)
		
		# The length includes the header (ie 8 bytes) and padding.
		length = unpacker.unpack_uint()
		print "DEBUG: header %s, class %s, type %s, length %s" % (self.version, self.messageClass, self.messageType, length)
		if length < 8 or length % 4:
			raise InvalidMessageException("Invalid message length")
	
		if length > bytes:
			raise IncompleteMessageException("Missing bytes in message: announced %s, available %s" % (length, bytes))
		
		remainingBytes = length - 8
		
		# ok, now we can parse the payload, containing parameters.
		# We are sure to have a complete message.
		
		pos = unpacker.get_position()
		rawvalue = unpacker.get_buffer()[pos:pos + remainingBytes]
		self.parameters = decodeParameters(rawvalue)
		self.decodedLength = length

	def getDecodedLength(self):
		return self.decodedLength
		
	def _encode(self, packer):
		payload = encodeParameters(self.parameters)
		paddedLength = (8 + len(payload) + 3) &~3
		
		packer.pack_uint(
			((self.version & 0xff) << 24) | 
			((self.messageClass & 0xff) << 8) |
			(self.messageType & 0xff)
		)
		packer.pack_uint(paddedLength)
		# fopaque pads the payload for us
		packer.pack_fopaque(len(payload), payload)

	def __str__(self):
		ret = []
		ret.append('version %s, type %s, class %s' % (self.version, self.messageType, self.messageClass))
		if self.parameters:
			for p in self.parameters:
				ret.append(str(p))
		
		return '\n'.join(ret)

class Parameter:
	"""
	type record Parameter
	{
		integer tag;
		charstring label optional; // never used on encoding
		any value;
	}
	"""
	def __init__(self):
		self.tag = None
		self.value = None
		self.label = None
	
	def toUserland(self):
		return dict(tag = self.tag, value = self.value, label = self.label)
	
	def fromUserland(self, message):
		self.tag = message['tag']
		self.value = message.get('value', '')
	
	def decode(self, unpacker, bytes):
		"""
		Leaves the unpacker ready to unpack the next parameter.
		Returns the number of consumed bytes.
		"""
		h = unpacker.unpack_uint()
		self.tag = h >> 16
		length = h & 0xffff
		# This length does not include padding, but includes the
		# common parameter header (4 bytes).
		# So let's compute the actual parameter length, in bytes,
		# i.e. the padded length
		paddedLength = (length+3) & ~3
		print "DEBUG: decoding parameter: tag %s, length %s, padded length %s, remaining bytes %s" % (self.tag, length, paddedLength, bytes)
		if bytes < paddedLength:
			# Invalid because in this context we'll never get more bytes: the message length was correct.
			raise InvalidMessageException("Invalid length: missing bytes in parameter tag %s: available %s, expected %s" % (self.tag, paddedLength, bytes))
		
		# Now store remaining bytes, excluding the padding, in rawvalue.
		pos = unpacker.get_position()
		rawvalue = unpacker.get_buffer()[pos:pos + length - 4]
		# And now, call a parameter value decoder according to the tag.
		# We garantee that the value will be complete (no missing bytes).
		self.label, codec = getParameterCodec(self.tag)
		self.value = codec.decode(rawvalue)

		# Set the position for the next parameter decoding		
		unpacker.set_position(pos + paddedLength - 4) # - 4 because we already consumed the header contained in the paddedLength
		return paddedLength

	def encode(self, packer):
		"""
		Encodes the message to the packer.
		Also encodes padding bytes.
		"""
		# Let's compute the useful length to encode in parameter header
		_, codec = getParameterCodec(self.tag)
		payload = codec.encode(self.value)
		
		# Useful len: includes the header, too
		length = len(payload) + 4
		
		packer.pack_uint(((self.tag & 0xffff) << 16) | (length & 0xffff))
		packer.pack_fopaque(len(payload), payload)

	def __str__(self):
		label, _ = getParameterCodec(self.tag)
		ret = 'parameter tag %4.4x (%s)\n' % (self.tag, label)
		ret += ' value:\n%s' % self.value
		
		return ret

def encodeParameter(message, packer):
	m = Parameter()
	m.fromUserland(message)
	m.encode(packer)

def decodeParameter(unpacker, bytes):
	m = Parameter()
	consumedBytes = m.decode(unpacker, bytes)
	return (consumedBytes, m.toUserland())

##
# Parameter payloads codecs
##

class SubCodec:
	"""
	A Default parameter codec implementation.
	
	type octetstring DefaultType;
	"""
	def decode(self, data):
		"""
		Decodes data from an encoded payload (string as buffer) to a testerman message.
		Returns the decoded testerman message.
		"""
		# Default implementation
		return data
	def encode(self, message):
		"""
		Encodes a testerman message to data.
		Padding will be automatically added if needed.
		Returns this payload.
		"""
		# Default implementation - we assume message is a string
		return message

class AddressSubCodec(SubCodec):
	"""
	type record AddressType
	{
		integer routingIndicator,
		integer addressIndicator,
		record of Parameter addresses,
	}
	
	"""
	def decode(self, data):
		unpacker = xdrlib.Unpacker(data)
		ret = {}
		riai = unpacker.unpack_uint()
		# RI: 
		# Reserved 0
		# Route on GT 1
		# Route on SSN+PC 2
		# Route on Hostname 3
		# Route on SSN + IP 4
		ret['routingIndicator'] = riai >> 16
		# AI:
		# bit 1: Include SSN
		# bit 2: Include PC
		# bit 3: Include GT
		ret['addressIndicator'] = riai & 0xffff
		# Address parameters follows.
		ret['addresses'] = decodeParameters(unpacker.get_buffer()[4:])
		return ret
	
	def encode(self, message):
		ai = message['addressIndicator']
		ri = message['routingIndicator']
		
		packer = xdrlib.Packer()
		packer.pack_uint(((ri & 0xffff) << 16) | (ai & 0xffff))
		
		addresses = encodeParameters(message.get('addresses', []))
		# Will automatically pad to next 4-byte
		packer.pack_fopaque(len(addresses), addresses)
		return packer.get_buffer()

class TemplateSubCodec(SubCodec):
	"""
	"""
	def decode(self, data):
		return data
	def encode(self, message):
		return message

class GlobalTitleSubCodec(SubCodec):
	"""
	type record GlobalTitleType
	{
		integer gti;
		integer translationType;
		integer numberingPlan;
		integer natureOfAddress;
		integer digits; // encoded in TBCD, 0-padded
	}
	"""
	def decode(self, data):
		print "DEBUG: GT raw data: %s" % binascii.hexlify(data)
		unpacker = xdrlib.Unpacker(data)
		gti = unpacker.unpack_uint() & 0xff
		
		info = unpacker.unpack_uint()
		translationType = (info >> 16) & 0xff
		numberingPlan = (info >> 8) & 0xff
		natureOfAddress = info & 0xff
		
		nbDigits = (info >> 24) & 0xff
		paddedDigitLen = (nbDigits / 2 + 1)&~1
		
		print "DEBUG: GT: tt %s, np %s, ton %s, nb digits %s, digit bytes %s" % (translationType,
		numberingPlan, natureOfAddress, nbDigits, paddedDigitLen)
		# read padded number of semi-bytes
		pos = unpacker.get_position()
		tbcdDigits = unpacker.get_buffer()[pos:pos + paddedDigitLen]
		
		digits = tbcd2string(tbcdDigits, nbDigits)
		
		return dict(gti = gti, translationType = translationType,
			numberingPlan = numberingPlan, natureOfAddress = natureOfAddress,
			digits = digits)
	
	def encode(self, message):
		packer = xdrlib.Packer()
		translationType = message.get('translationType', 0)
		natureOfAddress = message.get('natureOfAddress', 0)
		numberingPlan = message.get('numberingPlan', 0)
		gti = message.get('gti', 1)
		digits = message.get('digits', '')
		nbDigits = len(digits)
		tbcdDigits = string2tbcd(digits, 0x00) # padded with 0 according to the RFC
		
		packer.pack_uint(gti & 0xff)
		info = ((nbDigits & 0xff) << 24) | ((translationType & 0xff) << 16) | ((numberingPlan & 0xff) << 8) | (natureOfAddress & 0xff)
		packer.pack_uint(info)
		# Do not use pack_fopaque here because it will pad to the next 4byte
		# automatically, resulting in a parameter that is longer than expected
		# (the useful bytes would include the padding bytes, which is not a showstopper, but incorrect)
		return packer.get_buffer() + tbcdDigits

class UInt8SubCodec(SubCodec):
	"""
	Generic class for several parameters.
	"""
	def decode(self, data):
		hop = xdrlib.Unpacker(data).unpack_uint()
		return hop & 0xff
	def encode(self, message):
		packer = xdrlib.Packer()
		packer.pack_uint(message & 0xff)
		return packer.get_buffer()

class UInt32SubCodec(SubCodec):
	"""
	Generic class for several parameters.
	"""
	def decode(self, data):
		unpacker = xdrlib.Unpacker(data)
		return unpacker.unpack_uint()
	def encode(self, message):
		packer = xdrlib.Packer()
		packer.pack_uint(message)
		return packer.get_buffer()

class PointCodeSubCodec(UInt32SubCodec): pass
class ReferenceNumberSubCodec(UInt32SubCodec): pass
class NetworkAppearanceSubCodec(UInt32SubCodec): pass
class ErrorCodeSubCodec(UInt32SubCodec): pass
class TrafficModeTypeSubCodec(UInt32SubCodec): pass
class AspIdentifierSubCodec(UInt32SubCodec): pass
class CorrelationIdSubCodec(UInt32SubCodec): pass
class RegistrationStatusSubCodec(UInt32SubCodec): pass
class DeregistrationStatusSubCodec(UInt32SubCodec): pass
class LocalRoutingKeyIdentifierSubCodec(UInt32SubCodec): pass

class SubsystemNumberSubCodec(UInt8SubCodec): pass
class CongestionLevelSubCodec(UInt8SubCodec): pass
class MessagePrioritySubCodec(UInt8SubCodec): pass
class ImportanceSubCodec(UInt8SubCodec): pass
class ReceiveSequenceNumberSubCodec(UInt8SubCodec): pass
class Ss7HopCounterSubCodec(UInt8SubCodec): pass
class SmiSubCodec(UInt8SubCodec): pass
class CreditSubCodec(UInt8SubCodec): pass


class UserCauseSubCodec(SubCodec):
	"""
	type record UserCauseType
	{
		integer cause;
		integer user;
	}
	"""
	def decode(self, data):
		unpacker = xdrlib.Unpacker(data)
		uc = unpacker.unpack_uint()
		cause = (uc >> 16) & 0xffff
		user = uc & 0xffff
		return dict(cause = cause, user = user)
	def encode(self, message):
		packer = xdrlib.Packer()
		user = message.get('user', 0)
		cause = message.get('cause', 0)
		uc = ((cause & 0xffff) << 16) | (user & 0xffff)
		packer.pack_uint(uc)
		return packer.get_buffer()

class DataSubCodec(SubCodec):
	"""
	type octetstring DataType;
	"""
	def decode(self, data):
		return data
	def encode(self, message):
		return message

class AspCapabilitiesSubCodec(SubCodec):
	"""
	type record AspCapabilitiesType
	{
		integer interworking;
		set of integer protocolClasses; // subset of (0..3)
	}
	"""
	def decode(self, data):
		unpacker = xdrlib.Unpacker(data)
		raw = unpacker.unpack_uint()
		classbitmap =  (raw >> 8) & 0x0f
		interworking = raw & 0xff
		protocolClasses = []
		for bit, val in [ (0x01, 1), (0x02, 2), (0x04, 3), (0x08, 4) ]:
			if classbitmap & bit:
				protocolClasses.append(val)
		
		return dict(interworking = interworking, protocolClasses = protocolClasses)
	def encode(self, message):
		protocolClasses = message.get('protocolClasses', [ 0 ])
		interworking = message.get('interworking', 0)
		
		classbitmap = 0
		for bit, val in [ (0x01, 1), (0x02, 2), (0x04, 3), (0x08, 4) ]:
			if val in protocolClasses:
				classbitmap |= bit
		
		packer = xdrlib.Packer()
		packer.pack_uint((classbitmap << 8) | (interworking & 0xff))
		return packer.get_buffer()

class ProtocolClassSubCodec(SubCodec):
	"""
	type record ProtocolClassType
	{
		integer protocolClass;
		boolean returnOnError;
	}
	"""
	def decode(self, data):
		unpacker = xdrlib.Unpacker(data)
		pc = unpacker.unpack_uint() & 0xff
		return dict(protocolClass = pc & 0x7f, returnOnError = (pc & 0x80))
	def encode(self, message):
		packer = xdrlib.Packer()
		protocolClass = message.get('protocolClass', 0)
		returnOnError = message.get('returnOnError', False)
		pc = protocolClass & 0x7f
		if returnOnError:
			pc = pc | 0x80
		packer.pack_uint(pc)
		return packer.get_buffer()

class SequenceNumberSubCodec(SubCodec):
	"""
	type record SequenceNumberType
	{
		
	}
	"""
	def decode(self, data):
		return data
	def encode(self, message):
		return message

class RoutingContextSubCodec(SubCodec):
	"""
	type record of integer RoutingContextType;
	"""
	def decode(self, data):
		unpacker = xdrlib.Unpacker(data)
		ret = []
		for i in range(0, len(data) / 4):
			ret.append(unpacker.unpack_uint())
		return ret
	def encode(self, message):
		packer = xdrlib.Packer()
		for m in message:
			packer.pack_uint(m)
		return packer.get_buffer()
	
class StatusSubCodec(SubCodec):
	"""
	type record StatusType
	{
		integer statusType;
		integer statusId;
	}
	"""
	def decode(self, data):
		unpacker = xdrlib.Unpacker(data)
		s = unpacker.unpack_uint()
		statusType = (s >> 16) & 0xffff
		statusId = s & 0xffff
		return dict(statusType = statusType, statusId = statusId)
	def encode(self, message):
		packer = xdrlib.Packer()
		statusType = message.get('statusType', 2) # other
		statusId = message.get('statusId', 1) # reserved
		s = ((statusType & 0xffff) << 16) | (statusId & 0xffff)
		packer.pack_uint(s)
		return packer.get_buffer()
			

# Codec registration map, according to the tag
SubCodecs = [
# SUA/SCCP common
(0x0000, "Reserved", SubCodec()),
(0x0004, "Info-String", SubCodec()),
(0x0006, "Routing-Context", RoutingContextSubCodec()),
(0x0007, "Diagnostic-Info", SubCodec()),
(0x0009, "Heartbeat-Data", SubCodec()),
(0x000b, "Traffic-Mode-Type", TrafficModeTypeSubCodec()),
(0x000c, "Error-Code", ErrorCodeSubCodec()),
(0x000d, "Status", StatusSubCodec()),
(0x0011, "ASP-Identifier", AspIdentifierSubCodec()),
(0x0012, "Affected-Point-Code", SubCodec()), # TODO
(0x0013, "Correlation-ID", CorrelationIdSubCodec()),
(0x0014, "Registration-Result", SubCodec()), # never used directly ??
(0x0015, "Deregistration-Result", SubCodec()),
(0x0016, "Registration-Status", RegistrationStatusSubCodec()),
(0x0017, "Deregistration-Status", DeregistrationStatusSubCodec()),
(0x0018, "Local-Routing-Key-Identifier", LocalRoutingKeyIdentifierSubCodec()),
# SUA specific
(0x0101, "SS7-Hop-Counter", Ss7HopCounterSubCodec()),
(0x0102, "Source-Address", AddressSubCodec()),
(0x0103, "Destination-Address", AddressSubCodec()),
(0x0104, "Source-Reference-Number", ReferenceNumberSubCodec()),
(0x0105, "Destination-Reference-Number", ReferenceNumberSubCodec()),
(0x0106, "SCCP-Cause", SubCodec()),
(0x0107, "Sequence-Number", SubCodec()),  # TODO
(0x0108, "Receive-Sequence-Number", ReceiveSequenceNumberSubCodec()),  # TODO
(0x0109, "ASP-Capabilities", AspCapabilitiesSubCodec()),
(0x010a, "Credit", CreditSubCodec()),
(0x010b, "Data", DataSubCodec()),
(0x010c, "User-Cause", UserCauseSubCodec()),
(0x010d, "Network-Appearance", NetworkAppearanceSubCodec()),
(0x010e, "Routing-Key", SubCodec()),
(0x010f, "DRN-Label", SubCodec()),
(0x0110, "TID-Label", SubCodec()),
(0x0111, "Address-Range", SubCodec()),
(0x0112, "SMI", SmiSubCodec()),
(0x0113, "Importance", ImportanceSubCodec()),
(0x0114, "Message-Priority", MessagePrioritySubCodec()),
(0x0115, "Protocol-Class", ProtocolClassSubCodec()),
(0x0116, "Sequence-Control", UInt32SubCodec()),
(0x0117, "Segmentation", SubCodec()),
(0x0118, "Congestion-Level", CongestionLevelSubCodec()),
# Address parameters
(0x8001, "Global-Title", GlobalTitleSubCodec()),
(0x8002, "Point-Code", PointCodeSubCodec()),
(0x8003, "Subsystem-Number", SubsystemNumberSubCodec()),
(0x8004, "IPv4-Address", SubCodec()),
(0x8005, "Hostname", SubCodec()),
(0x8006, "IPv6-Addresses", SubCodec()),
]

# Codec selector according to the parameter tag.
# A default codec implementation is provided for unknown/
# non-explicitly supported parameters.
def getParameterCodec(tag):
	for t, label, codec in SubCodecs:
		if t == tag:
			return label, codec
	return "unknown", SubCodec()



##
# Testerman Codec Wrapper
##
class SuaCodec(CodecManager.IncrementalCodec):
	def encode(self, template):
		m = Message()
		m.fromUserland(template)
		return (m.toNetwork(), m.summary())

	def incrementalDecode(self, data):
		m = Message()
		try:
			m.fromNetwork(data)
		except IncompleteMessageException:
			return (self.DECODING_NEED_MORE_DATA, 0, None, None)
		except Exception:
			return (self.DECODING_ERROR, getDecodedLength() or len(data), None, None)
		return (self.DECODING_OK, m.getDecodedLength(), m.toUserland(), m.summary())

CodecManager.registerCodecClass('sua', SuaCodec)


if __name__ == '__main__':
	print "SUA Codec unit tests"
	print 80*'-'
	samples = [	
	# SUA ASP active / Load-share, routing context 300	
	"0100040100000018000b000800000002000600080000012c",
	# SUA ERR / Refused - management blocking, network appearance 0, some diagnostic info 
	"0100000000000034000c00080000000d010d0008000000000007001c0100040100000018000b000800000002000600080000012c",
	# MAP SRI
	"01000701000000cc000600080000012c01150008000000000102002c0001000780010012000000040c0001042610101010100000800200080000057880030008000000080103002c0001000780010012000000040c000104262143658739000080020008000007d28003000800000006011600080000000001010008000000ff010b004962434804000200686b1a2818060700118605010101a00d600ba1090607040000010014026c1fa11d02010102012d30158007910026151101008101ff820791261010101010000000"
	]

	for s in samples:
		print "Testing: %s" % s
		s = binascii.unhexlify(s)
		(_, consumed, decoded, summary) = CodecManager.incrementalDecode('sua', s)
		print "Decoded: %s\nSummary: %s" % (decoded, summary)
		print "Consumed %s bytes ouf of %s" % (consumed, len(s))
		(reencoded, summary) = CodecManager.encode('sua', decoded)
		print "Reencoded: %s\nSummary: %s" % (binascii.hexlify(reencoded), summary)
		print "Original : %s" % binascii.hexlify(s)
		assert(s == reencoded)
	
			
