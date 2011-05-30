# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2011 Sebastien Lefevre and other contributors
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
# Some execution Profile-related tools
#
##


import logging
import xml.dom.minidom

import Tools

def getLogger():
	return logging.getLogger('ProfileTools')


class Profile:
	def __init__(self):
		self.description = ''
		self.parameters = {}
	
	def getParameters(self):
		return self.parameters
	
	def getDescription(self):
		return self.description
	
	def __str__(self):
		return "Profile:\ndescription: %s\nparameters: %s\n" % (self.description, repr(self.parameters))

def parseProfile(xmlProfile):
	"""
	Parses the XML string containing a profile.
	
	@type  xmlProfile: utf-8 string
	@param xmlProfile: a profile, xml format
	
	@rtype: Profile
	@returns: the parsed Profile, or None in case of an error
	"""
	profile = None
	try:
		# parseString takes unicode ?? (hence ignoring the <?xml encoding=...?> ?
 		doc = xml.dom.minidom.parseString(xmlProfile)
		
		profile = Profile()

		e = doc.getElementsByTagName('description')
		if e:	profile.description = e[0].childNodes[0].data
		
		for parameter in doc.getElementsByTagName('parameter'):
			try:
				name = parameter.attributes['name'].value
				value = parameter.childNodes[0].data
				profile.parameters[name] = value
			except Exception, e:
				getLogger().warning("Unable to parse a parameter in profile: %s" % str(e))

	except Exception:
		getLogger().warning("Unable to parse profile:\n%s" % Tools.getBacktrace())
	
	return profile


def test():
	logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S')
	xml = """<?xml version='1.0'?>
<profile>
 <description>hello</description>
 <parameters>
  <parameter name="PX_UNICODE_STRING">hello ça marche</parameter>
 </parameters>
</profile>"""
	print str(parseProfile(xml))

if __name__ == '__main__':
	test()
