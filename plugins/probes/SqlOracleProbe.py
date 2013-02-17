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
= Identification and Properties =

Probe Type ID: ``sql.oracle``

Properties:

.. csv-table::
   :header: "Name","Type","Default value","Description"

   "``host``","string","``'localhost'``","The Oracle server IP address or hostname. Must be the same as defined in the TSN on the server's connector."
   "``port``","integer","``1521``","The Oracle TCP listening port on ``host``"
   "``sid``","string","(empty)","The Oracle System ID corresponding to your instance"
   "``user``","string","(empty)","The user to use to connect to the database ``db`` above"
   "``password``","string","(empty)","The password to use, if required to connect to the database ``db`` above for user ``user``"

Overview
--------

This probes allows to connect to an Oracle database and perform any valid SQL command
that are valid for this DBS. Just send the SQL request as a string through a port bound
to the probe.

As a result, you should expect a ``SqlResult`` choice structure, whose ``'error'`` arm is a simple
charstring indicating an error (connection- or SQL- related), and ``result`` indicates a
successful query.

In case of a non-SELECT query, ``result`` is an empty list. In case of a SELECT query, 
it contains a list of dictionaries corresponding to the selected entries, whose keys are the
names of the returned columns. The associated values are natural Python equivalent to
SQL types. However, the following types have not been tested yet:

* ``NULL``
* blobs
* date/time

(If you encounter any problem with these SQL types or other ones, please contact us or
create a ticket).

These structures and mechanisms are common to all ``sql.*`` probe types.

The supported Oracle versions depend on the underlying Oracle libs you are using, and are
independent from the probe.

It has been tested successfully against a Oracle 10g R2 and 11g R2 servers.

Availability
~~~~~~~~~~~~

All platforms.

Dependencies
~~~~~~~~~~~~

This probe requires the cx_Oracle Python module, than can be found at http://cx-oracle.sourceforge.net.

The cx_Oracle module is a wrapper that requires Oracle librairies.

Here is a possible path to a working probe:

* Get the Oracle Instant Client from the `Oracle site <http://www.oracle.com/technology/tech/oci/instantclient/index.html>`_
  (requires free registration) for the platform that will run the probe (the Basic Lite version is sufficient)
* Decompress it wherever you want
* Under Windows, copy ``oraociicus11.dll`` and ``oci.dll`` to a directory included in the ``PYTHONPATH`` of the agent
  (in particular, you may put them into its ``plugins/probes/`` directory)
* Under Linux, copy ``?.so`` and ``oci.so`` to ``plugins/probes/`` under your agent tree, but be sure to
  add a LD_LIBRARY_PATH to this path before restarting your agent. To make the probe work from the TE (i.e. not
  hosted on a agent), you should copy them to the ``core/`` Testerman directory, since it is automatically included
  in all TE's ``LD_LIBRARY_PATH``.

Make sure to download Oracle Instant Client and a cx_Oracle module that are compatible with each other and
with your Oracle database version.

As far as it has been tested, using libs for Oracle 11g correctly works with a Oracle 10g server.

See Also
~~~~~~~~

* :doc:`ProbeSqlMysql`, a probe to access a MySQL database.

TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the ``SqlPortType`` port type as specified below:

::

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
		
