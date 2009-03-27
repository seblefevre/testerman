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
	= Identification and Properties =

	Probe Type ID: `exec.interactive`

	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	|| `host` || string || `'localhost'` || The MySQL server IP address or hostname ||
	|| `port`|| integer || `3306` || The MySQL service listening port on `host` ||
	|| `db` || string || (empty) || The database to use ||
	|| `user` || string || (empty) || The user to use to connect to the database `db` above ||
	|| `password` || string || (empty) || The password to use, if required to connect to the database `db` above for user `user` ||


	= Overview =

	This probes allows to connect to a MySQL database and perform any valid SQL command
	that are valid for this DBS. Just send the SQL request as a string through a port bound
	to the probe.
	
	As a result, you should expect a `SqlResult` choice structure, whose `'error'` arm is a simple
	charstring indicating an error (connection- or SQL- related), and `result` indicates a
	successful query. [[BR]]
	In case of a non-SELECT query, `result` is an empty list. In case of a SELECT query, 
	it contains a list of dictionaries corresponding to the selected entries, whose keys are the
	names of the returned columns. The associated values are natural Python equivalent to
	SQL types. However, the following types have not been tested yet:
	 * `NULL`
	 * blobs
	 * date/time
	
	(If you encounter any problem with these SQL types or other ones, please contact us or
	create a ticket).
	
	These structures and mechanisms are common to all `sql.*` probe types.
	
	The supported MySQL versions depend on the underlying MySQL DB libs you are using, and are
	independent from the probe.

	== Availability ==

	All platforms.

	== Dependencies ==

	This probe requires the MySQLdb Python module.
	
	 * Debian package: `python-mysql` (+ dependencies)
	 * Windows package, egg package, sources available at [http://sourceforge.net/projects/mysql-python].
	 
	The Windows package also requires a MySQL ODBC connector, as available [http://www.mysql.com/products/connector/odbc/ here].

	== See Also ==

	 * ProbeSqlOracle, a probe to access Oracle databases.


	= TTCN-3 Types Equivalence =

	The test system interface port bound to such a probe complies with the `SqlPortType` port type as specified below:
	{{{
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
	
	type port SqlPortType message
	{
		in SqlRequest,
		out SqlResult
	}
	}}}
	
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
		
