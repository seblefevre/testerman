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
# A probe to access MySQL databases.
#
# Based on Python DB API (1.0 or 2.0), depends on mysql backend providing
# MySQLdb module:
# source: http://sourceforge.net/projects/mysql-python
# debian package: python-mysql
##

import ProbeImplementationManager

import MySQLdb as dbapi

class MySqlProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	type charstring SqlRequest;
	
	type union Result
	{
		charstring error,
		record of SqlResult result
	}
	
	type record SqlResult
	{
		any <field name>* // according to your request 
	}
	
	type port MySqlPortType message
	{
		in SqlRequest,
		out SqlResult
	}
	
	SqlResult is an empty set in case of non-SELECT requests.
	
	
	Properties:
	host
	port
	database
	user
	password
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self.setDefaultProperty('host', 'localhost')
		self.setDefaultProperty('port', 3306)
		self.setDefaultProperty('password', '')
		self.setDefaultProperty('db', '')
		self.setDefaultProperty('user', '')
	
	def onTriMap(self):
		pass
	
	def onTriUnmap(self):
		pass
	
	def onTriSAReset(self):
		pass
	
	def onTriExecuteTestCase(self):
		pass
	
	def onTriSend(self, message, sutAddress):
		self._executeQuery(message)
	
	def _executeQuery(self, query):
		try:
			conn = dbapi.connect(user = self['user'], passwd = self['password'], db = self['database'], host = self['host']) # '%s:%s' % (self['host'], self['port']))
			cursor = conn.cursor()
			self.logSentPayload(query.split(' ')[0].upper(), query)
			try:
				cursor.execute(query)
				conn.commit()
			except Exception, e:
				conn.rollback()
				cursor.close()
				conn.close()
				raise e

			res = []
			if cursor.description: # equivalent to "the previous execution() provided a set ?"
				columnNames = map(lambda x: x[0], cursor.description)
				for row in cursor.fetchall():
					res.append(dict(zip(columnNames, row)))

			self.triEnqueueMsg(('result', res))
			cursor.close()
			conn.close()
		except Exception, e:
			self.getLogger().warning("Exception while handling a query: %s" % str(e))
			self.triEnqueueMsg(('error', str(e)))
		
		

ProbeImplementationManager.registerProbeImplementationClass('sql.mysql', MySqlProbe)
		
