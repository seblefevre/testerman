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
# (Pluggable) Script to get/set a value in a XML file.
# Requires libxml2-python package (or equivalent)
#
# Usage:
# thisfile.py get <filename> <keypath>
# thisfile.py set <filename> <keypath> <value>
#
# where keypath is a xpath query.
##

import os
import sys
import libxml2 as xml
import StringIO
import tempfile

SUPPORTED_CONF_FILE_FORMATS = [ 'xml' ]

class GetSet:
	def __init__(self):
		self.properties = {}
	
	def setProperty(self, name, value):
		self.properties[name] = value
	
	def getProperty(self, name, defaultValue):
		return self.properties.get(name, defaultValue)

	def setValue(self, filename, keypath, value):
		"""
		Updates a value.
		If the keypath selects more that one value, all values are updated.

		WARNING: 

		@type  filename: string
		@param filename: the full path to the file to update
		@type  keypath: string
		@param keypath: an xpath path to the value to update
		@type  value: string
		@param value: the value to update

		@rtype: boolean
		@returns: True if OK, False otherwise
		"""
		try:
			doc = xml.parseFile(filename)
			nodes = doc.xpathEval(keypath)
			if not nodes:
				raise Exception("Unable to update %s: node not found" % (filename))
			for e in nodes:
				e.setContent(value)

			tmpfile = tempfile.TemporaryFile()
			doc.saveTo(tmpfile, format = True)
			
			tmpfile.seek(0)
			output = tmpfile.read()
			tmpfile.close()
			
			# unlink the original file to avoid open file problems
			os.remove(filename)
			# WARNING: here we have a risk to lose our file -
			# if we were able to delete it, but unable to recreate it.
			f = open(filename, 'w')
			f.write(output)
			f.close()

			doc.freeDoc()
			return True

		except Exception, e:
			raise Exception("Unable to update %s (%s)" % (filename, str(e)))

	def getValue(self, filename, keypath):
		"""
		Returns the value corresponding to the keypath.

		If the keypatch selects multiple values, raises an Exception.

		@type  filename: string
		@param filename: the full path to the file to read
		@type  keypath: string
		@param keypath: an xpath path to the value to get

		@rtype: string
		@returns: the value, if found, or None otherwise
		"""
		try:
			doc = xml.parseFile(filename)
			ctx = doc.xpathNewContext()
			nodes = ctx.xpathEval(keypath)

			if len(nodes) > 1:
				doc.freeDoc()
				ctx.xpathFreeContext()
				raise Exception("Multiple nodes found. Cannot identify a single value to return.")
			elif not nodes:
				doc.freeDoc()
				ctx.xpathFreeContext()
				raise Exception("Node not found.")
			else:
				# Single node found
				value = unicode(nodes[0].content).encode('utf-8')
				doc.freeDoc()
				ctx.xpathFreeContext()
		except Exception, e:
			raise Exception("Unable to get %s in %s (%s)" % (keypath, filename, str(e)))
		return value


def getInstance():
	return GetSet()


if __name__ == '__main__':
	def usage():
		print"""Usage:
  %(name)s get <filename> <keypath>
  %(name)s set <filename> <keypath> <value>

  where keypath is a xpath query.""" % dict(name = sys.argv[0])
	
	if len(sys.argv) < 3:
		usage()
		sys.exit(1)
	
	try:
		op = sys.argv[1]
		if op == 'set':
			ret = getInstance().setValue(filename = sys.argv[2], keypath = sys.argv[3], value = sys.argv[4])
			if ret:
				print "Value set."
				status = 0
			else:
				print "Unable to set value."
				status = 1
		else:
			value = getInstance().getValue(filename = sys.argv[2], keypath = sys.argv[3])
			print value
			if value is None:
				status = 1
			else:
				status = 0
	except Exception, e:
		print "Configuration script exception: %s" % str(e)
		status = 1
	sys.exit(status)

