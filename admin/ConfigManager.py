##
# -*- coding: utf-8 -*-
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008,2009,2010 Sebastien Lefevre and other contributors
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
# A basic config (key/value) manager.
#
# Usual singleton model.
# 
##

import copy
import re

class ConfigManager:
	def __init__(self):
		self._values = {}
		
	def set(self, key, value):
		self._values[key] = value

	def get(self, key, defaultValue = None):
		ret = self._values.get(key, defaultValue)
		return ret

	def get_int(self, key, defaultValue = None):
		return int(self.get(key, defaultValue))

	def get_bool(self, key, defaultValue = None):
		b = self.get(key, defaultValue)
		if isinstance(b, (bool, int)):
			return b
		if isinstance(b, basestring):
			return b.lower() in [ '1', 'true', 't' ]
		return False

	def getValues(self):
		ret = copy.copy(self._values)
		return ret
	
	def read(self, filename):
		"""
		Load from a file.
		"""
		try:
			f = open(filename)
			for l in f.readlines():
				m = re.match(r'\s*(?P<key>[^#].*)=(?P<value>.*)', l.strip())
				if m:
					self.set(m.group('key').strip(), m.group('value').strip())
			f.close()
		except Exception, e:
			raise Exception("Unable to read configuration file '%s' (%s)" % (filename, str(e)))

	def write(self, filename):
		# TODO: implement a non-destructive writer (keeping comments, etc)
		contents = ""
		values = self.getValues().items()
		values.sort()
		contents = "\n".join(sorted)
		try:
			f = open(filename, "w")
			f.write(contents)
			f.close()
		except Exception, e:
			raise Exception("Unable to save current configuration to file '%s' (%s)" % (filename, str(e)))
	
