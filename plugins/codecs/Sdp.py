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
# SDP codec.
# Based on RFC4566
##

import CodecManager


class SdpCodec(CodecManager.Codec):
	"""
	= Identification and Properties =
	
	Codec ID: `sdp`
	
	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	|| `name` || string || `"Testerman SDP"` || A default session name to use for encoding, if none is provided by the user ||
	|| `version` || string || `'0'` || A default SDP version to use for encoding, if none is provided by the user ||
	
	= Overview =
	
	This codec encodes/decodes Session Description Protocol (SDP) payloads
	as defined in RFC4566.
	
	== Decoding ==
	
	This codec decodes a multi-line string describing a session to
	a high level Testerman message structure.
	
	Unknown fields are not decoded, and do not cause any error.
	
	If mandatory SDP attributes are missing, the decoding still successes
	(this behaviour may change the future).
	
	Attributes that can be repeated are decoded to a list, and as an
	empty list if they are now present at all in the encoded message.
	
	== Encoding ==
	
	This codec encodes a Testerman dict structure `Sdp` to a
	multi-line string (`\\n`-terminated), suitable 
	for a direct inclusion in a SIP/RTSP body whose Content-Type is `application/sdp`.

	If no `name` is provided, it is defaulted to the value of the `name` codec property.[[BR]]
	If no `version` is provided, it is defaulted to the value of the `version` codec property.[[BR]]
	
	If mandatory SDP attributes are missing, the encoding fails; since a default value is
	provided for both mandatory attributes `name` (`s=`) and `version` (`v=`), this mainly
	involves the `originator` (`o=`) attribute.

	== Availability ==

	All platforms.

	== Dependencies ==

	None.

	== See Also ==
	
	
	= TTCN-3 Types Equivalence =
	
	This codec decodes to/encode from the Testerman structure whose the TTCN-3 equivalent
	is the type `SdpMessage` below:
	{{{
	type record Media
	{
		charstring name_transport,      // m=
		charstring title optional,      // i=
		charstring connection optional, // c=
		record of charstring bandwidths,  // b=
		charstring key optional,        // k =
		record of charstring attributes,  // a=
	}
	
	type record Sdp
	{
		// Session parameters
		charstring version optional,         // v= - set to the default if missing
		charstring originator,               // and session ; o=
		charstring name optional,            // s= - use the default if missing
		charstring information optional,     // i=
		charstring description_uri optional, // u=
		charstring email_address optional,   // e=
		charstring phone_number optional,    // p=
		charstring connection optional,      // c=
		record of charstring bandwidths,       // b=
		charstring key optional,             // k=
		record of charstring attibutes,        // a=
		charstring time optional,            // t=
		record of charstring repeats,          // r=
		// Media descriptions
		record of Media media,
	}
	}}}
	
	"""
	def __init__(self):
		CodecManager.Codec.__init__(self)
		# Some default (encoding) properties
		self.setDefaultProperty('version', '0')
		self.setDefaultProperty('name', 'Testerman SDP')
	
	def encode(self, template):
		version = template.get('version', self['version'])
		originator = template.get('originator')
		name = template.get('name', self['name'])
		information = template.get('information')
		description_uri = template.get('description_uri')
		email_address = template.get('email_address')
		phone_number = template.get('phone_number')
		connection = template.get('connection')
		key = template.get('key')
		time_ = template.get('time')
		bandwidths = template.get('bandwidths', [])
		attributes = template.get('attributes', [])
		media = template.get('media', [])
		repeats = template.get('repeats', [])
		
		# Check mandatory parameters
		if not version or not originator or not name:
			raise Exception('Missing mandatory SDP parameters: version, originator, or name')
		
		ret = []
		# Session parameters
		ret.append('v=%s' % str(version))
		ret.append('o=%s' % originator)
		ret.append('s=%s' % name)
		if information: ret.append('i=%s' % information)
		if description_uri: ret.append('u=%s' % description_uri)
		if email_address: ret.append('e=%s' % email_address)
		if phone_number: ret.append('p=%s' % phone_number)
		if connection: ret.append('c=%s' % connection)
		for b in bandwidths: ret.append('b=%s' % b)
		if key: ret.append('k=%s' % key)
		for a in attributes: ret.append('a=%s' % a)
		if time_: ret.append('t=%s' % time_)
		for r in repeats: ret.append('r=%s' % r)
		# Media parameters
		for m in media:
			ret.append('m=%s' % m['media_transport'])
			if m.has_key('title'): ret.append('i=%s' % m['title'])
			if m.has_key('connection'): ret.append('c=%s' % m['connection'])
			if m.has_key('bandwidths'):
				for b in m['bandwidths']:
					ret.append('b=%s' % b)
			if m.has_key('key'): ret.append('k=%s' % m['key'])
			if m.has_key('attributes'):
				for a in m['attributes']:
					ret.append('a=%s' % a)

		ret = '\n'.join(ret)

		return (ret, 'SDP')

	def decode(self, data):
		ret = {}
		lines = data.split('\n')
		
		ret['repeats'] = []
		ret['bandwidths'] = []
		ret['attributes'] = []
		ret['media'] = []
		
		media = None
		for line in lines:
			if line.startswith('m='):
				# Starts a new media
				media = { 'name_transport': line[2:], 'bandwidths': [], 'attributes': []}
				ret['media'].append(media)
				
			if media is None:
				# Session parameters
				if line.startswith('v='):	ret['version'] = line[2:]
				elif line.startswith('o='):	ret['originator'] = line[2:]
				elif line.startswith('s='):	ret['name'] = line[2:]
				elif line.startswith('i='):	ret['information'] = line[2:]
				elif line.startswith('u='):	ret['description_uri'] = line[2:]
				elif line.startswith('e='):	ret['email_address'] = line[2:]
				elif line.startswith('p='):	ret['phone_number'] = line[2:]
				elif line.startswith('c='):	ret['connection'] = line[2:]
				elif line.startswith('k='):	ret['key'] = line[2:]
				elif line.startswith('t='):	ret['time'] = line[2:]
				elif line.startswith('r='):	ret['repeats'].append(line[2:])
				elif line.startswith('b='):	ret['bandwidths'].append(line[2:])
				elif line.startswith('a='):	ret['attributes'].append(line[2:])
			else:
				if line.startswith('i='):	media['title'] = line[2:]
				elif line.startswith('c='):	media['connection'] = line[2:]
				elif line.startswith('k='):	media['key'] = line[2:]
				elif line.startswith('b='):	media['bandwidths'].append(line[2:])
				elif line.startswith('a='):	media['attributes'].append(line[2:])
		
		return (ret, 'SDP')
		
CodecManager.registerCodecClass('sdp', SdpCodec)


