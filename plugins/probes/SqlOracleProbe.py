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
# A probe to access Oracle 10g, 11g databases.
#
# Based on cx Oracle:
# source: http://cx-oracle.sourceforge.net/
# debian package:
#
# Under windows:
# get Oracle Instant Client
# copy oraociicus11.dll and oci.dll to something in the PYTHONPATH
# (for instance in this probe directory)
##

import ProbeImplementationManager

import cx_Oracle as dbapi

def getBacktrace():
	import traceback
	import StringIO
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

class OracleProbe(ProbeImplementationManager.ProbeImplementation):
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
	
	
	Properties:
	host # must be the same as in the TSN on the server
	port
	user
	password
	sid
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self.setDefaultProperty('host', 'localhost')
		self.setDefaultProperty('port', 1521)
		self.setDefaultProperty('password', '')
		self.setDefaultProperty('user', '')
		self.setDefaultProperty('sid', '')
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
		self.getLogger().debug("Executing query:\n%s" % repr(query))
		try:
			dsn = dbapi.makedsn(str(self['host']), self['port'], str(self['sid']))
			conn = dbapi.connect(str(self['user']), str(self['password']), dsn)
			cursor = conn.cursor()
			self.logSentPayload(query.split(' ')[0].upper(), query)
			try:
				cursor.execute(str(query))
				conn.commit()
			except Exception, e:
				self.getLogger().warning("Exception while executing query: %s" % getBacktrace())
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
			self.getLogger().warning("Exception while handling a query: %s" % getBacktrace())
			self.triEnqueueMsg(('error', str(e)))
		
		

ProbeImplementationManager.registerProbeImplementationClass('sql.oracle', OracleProbe)
		
