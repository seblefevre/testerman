# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008-2011 Sebastien Lefevre and other contributors
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
# Web Services (Ws interface).
#
# WARNING: all methods in this file are exposed through the Ws
# (WebServices is a dispatch module for an XML-RPC server)
#
#
# The Ws interface is split into several logical services:
# - main
# - file
# - job
# - agent
# - xc
# - server
#
##

import ConfigManager
import CounterManager
import DependencyResolver
import FileSystemManager
import FileSystemBackendManager
import JobManager
import Package
import ProbeManager
import Tools
import Versions

import base64
import logging
import operator
import os.path
import time
import zlib


#: API versions: major.minor
#: major += 1 if not backward compatible,
#: minor += 1 if feature-enriched, backward compatible
WS_VERSION = '1.7'


################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.Ws')


################################################################################
# Service: main
################################################################################

def getVersion():
	"""
	Returns the Testerman Server implementation version.
	
	Format A.B.C:
	- A = main version
	- B = new features
	- C = fixes / small enhancements
	
	@rtype: string
	@returns: the server implementation version
	"""
	return Versions.getServerVersion()

def getWsVersion():
	"""
	Returns the Ws interface API version.
	
	Format A.B:
	- A += 1 if not backward compatible.
	- B += 1 if enriched API, but still backward compatible.
	
	@rtype: string
	@returns: the Ws API version
	"""
	return Versions.getWsVersion()

def getXcVersion():
	"""
	Returns the Xc interface API version.
	
	Format A.B:
	- A += 1 if not backward compatible.
	- B += 1 if enriched API, but still backward compatible.
	
	@rtype: string
	@returns: the Xc API version
	"""
	return Versions.getXcVersion()


################################################################################
# service: job (Job management)
################################################################################

def scheduleAts(source, atsId, username, session, at, path = None, groups = None):
	"""
	Schedules an ATS to start at <at>
	
	@since: 1.0
	
	@type  source: string
	@param source: the ats contents, as a utf-8 string
	@type  atsId: string
	@param atsId: a friendly identifier/job label
	@type  username: string
	@param username: the username of the user who scheduled this ATS
	@type  session: dict[utf-8 strings] of utf8 strings
	@param session: input session variables (may be empty)
	@type  at: float, or None
	@param at: the timestamp at which the ats should be started.
	           If set to None or lower than current (server) time, immediate start.
	@type  path: string, or None
	@param path: the complete docroot-path to the file associated to the source,
	             if any. For source files not located on the server, set to None.
	             For the other ones, enables to know where to search dependencies
	             from.
	@since: 1.6
	@type  groups: list os unicode strings, or None
	@param groups: a list of groups selected for this run. If set to None, all groups are considered
	               (no particular selection)
	
	@throws Exception: in case of an internal error

	@rtype: dict { 'job-uri': string, 'job-id': integer, 'message': string }
	@returns: a dict containing: 
	          job-uri: the newly created job uri, only valid if status == 0
	          job-id: the newly created job id, only valid if status == 0
	          message: a human readable string indicating what was done.
	"""
	getLogger().info(">> scheduleAts(at = %s, username = %s, ..., session = %s, groups = %s)" % (at, username, session, groups))

	try:
		# FIXME: ats and the dict of string seems to be received as unicode,
		# whereas they were sent by the client as UTF-8.
		# I should check on the wire and/or an XML-RPC feature somewhere (default encoding, etc).

		# Translate the session into a dict[unicode] of unicode
		s = {}
		if session:
			for (k, v) in session.items():
				s[k] = v
		
		source = source.encode('utf-8')
		
		job = JobManager.AtsJob(atsId, source, path)
		job.setUsername(username)
		job.setScheduledStartTime(at)
		job.setScheduledSession(s)
		job.setSelectedGroups(groups)
		jobId = JobManager.instance().submitJob(job)
		message = ""
		if at is None or at <= time.time():
			message = "immediate start"
		else:
			message = "will start on %s" % time.strftime("%Y-%m-%d, at %H:%M:%S (server time)", time.localtime(job.getScheduledStartTime()))
		res = { 'job-id': jobId, 'job-uri': job.getUri(), 'message': "ATS scheduled, %s. Its job ID is %d" % (message, jobId) }
	except Exception, e:
		e =  Exception("Scheduling error: %s" % (str(e)))
		getLogger().info("<< scheduleAts(...): Fault:\n%s" % Tools.getBacktrace())
		raise(e)

	getLogger().info("<< scheduleAts(...): %s" % str(res))
	return res

def scheduleCampaign(source, campaignId, username, session, at, path = None):
	"""
	Schedule an ATS to start at <at>
	
	@since: 1.2

	@type  ats: string
	@param ats: the ats contents, as a utf-8 string
	@type  atsId: string
	@param atsId: a friendly identifier/job label
	@type  username: string
	@param username: the username of the user who scheduled this ATS
	@type  session: dict[utf-8 strings] of utf8 strings
	@param session: input session variables (may be empty)
	@type  at: float, or None
	@param at: the timestamp at which the ats should be started.
	           If set to None or lower than current (server) time, immediate start.
	@type  path: string, or None
	@param path: the complete docroot-path to the file associated to the source,
	             if any. For source files not located on the server, set to None.
	             For the other ones, enables to know where to search dependencies
	             from.
	
	@throws Exception: in case of an internal error

	@rtype: dict { 'job-uri': string, 'job-id': integer, 'message': string }
	@returns: a dict containing: 
	          job-uri: the newly created job uri, only valid if status == 0
	          job-id: the newly created job id, only valid if status == 0
	          message: a human readable string indicating what was done.
	"""
	getLogger().info(">> scheduleCampaign(..., session = %s)" % str(session))

	try:
		# FIXME: ats and the dict of string seems to be received as unicode,
		# whereas they were sent by the client as UTF-8.
		# I should check on the wire and/or an XML-RPC feature somewhere (default encoding, etc).

		# Translate the session into a dict[unicode] of unicode
		s = {}
		if session:
			for (k, v) in session.items():
				s[k] = v
		
		source = source.encode('utf-8')
		
		job = JobManager.CampaignJob(campaignId, source, path)
		job.setUsername(username)
		job.setScheduledStartTime(at)
		job.setScheduledSession(s)
		jobId = JobManager.instance().submitJob(job)
		message = ""
		if at is None or at <= time.time():
			message = "immediate start"
		else:
			message = "will start on %s" % time.strftime("%Y%m%d, at %H:%M:%S", time.localtime(job.getScheduledStartTime()))
		res = { 'job-id': jobId, 'job-uri': job.getUri(), 'message': "Campaign scheduled, %s. Its job ID is %d" % (message, jobId) }
	except Exception, e:
		e =  Exception("Scheduling error: %s" % (str(e)))
		getLogger().info("<< scheduleCampaign(...): Fault:\n%s" % Tools.getBacktrace())
		raise(e)

	getLogger().info("<< scheduleCampaign(...): %s" % str(res))
	return res

def getJobInfo(jobId = None):
	"""
	Gets a job or all jobs information.

	@since: 1.0

	@type  jobId: integer, or None
	@param jobId: the job ID identifying the job whose status should be retrieved, or None for all jobs.
	
	@throws Exception: in case of an internal error.

	@rtype: a list of dict
	       {'id': integer, 'parent-id': integer, 'name': string,
	        'state': string in ['waiting', 'running', 'stopped', 'cancelled', 'killed', 'paused'],
	        'running-time': float or None, 'result': integer or None, 'username': string, 
					'start-time': float or None, 'stop-time': float or None, 'scheduled-at': float,
	        'type': string in ['ats', 'campaign'],
					'path': string (docroot-based path for jobs whose source is in docroot) or None (client-based source)
	       }
	@returns: a list of info for the given job, or for all jobs in the queue if jobId is None.

	@throws Exception: when the job was not found, or when the job file was removed.
	"""
	getLogger().info(">> getJobInfo(%s)" % str(jobId))
	res = []
	try:
		res = JobManager.instance().getJobInfo(jobId)
	except Exception, e:
		e =  Exception("Unable to complete getJobInfo operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< getJobStatus(...): Fault:\n%s" % str(e))
		raise(e)

	getLogger().info("<< getJobInfo: %d job info entries returned" % len(res))
	return res

def getJobLog(jobId, useCompression = True):
	"""
	Gets the current log for an existing job.
	
	@since: 1.0

	@type  jobId: integer
	@param jobId: the job ID identifying the job whose log should be retrieved
	@type  useCompression: bool
	@param useCompression: if set to True, compress the log using zlib before encoding the response in base64
	
	@rtype: string
	@returns: the job's log in utf-8 encoded XML,
	          optionally gzip + base64 encoded if useCompression is set to True
	"""
	getLogger().info(">> getJobLog(%d, %s)" % (jobId, str(useCompression)))
	res = None
	try:
		log = JobManager.instance().getJobLog(jobId)
		if log is not None:
			if useCompression:
				res = base64.encodestring(zlib.compress(log))
			else:
				res = base64.encodestring(log)
	except Exception, e:
		e =  Exception("Unable to complete getJobLog operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< getJobLog(...): Fault:\n%s" % str(e))
		raise(e)

	getLogger().info("<< getJobLog: %d bytes returned" % len(res))
	return res

def getJobLogFilename(jobId):
	"""
	Gets an existing job's log filename.
	
	@since: 1.0

	@type  jobId: integer
	@param jobId: the job ID identifying the job whose log filename should be retrieved
	
	@rtype: string, or None
	@returns: the log filename relative to the docroot,
	          or None if the job was not found
	"""
	getLogger().info(">> getJobLogFilename(%d)" % jobId)
	res = None
	try:
		res = JobManager.instance().getJobLogFilename(jobId)
	except Exception, e:
		e =  Exception("Unable to complete getJobLogFilename operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< getJobLogFilename(...): Fault:\n%s" % str(e))
		raise(e)
	getLogger().info("<< getJobLogFilename: %s" % str(res))
	return res

def rescheduleJob(jobId, at):
	"""
	Reschedules a job to start at <at>.

	@since: 1.2

	@type  jobId: integer
	@param jobId: the jobId identifying the job that needs rescheduling
	@type  at: float
	@param at: the timestamp of the new scheduled start
	
	@throws Exception: in case of an internal error.

	@rtype: bool
	@returns: True if the rescheduling was OK, False otherwise (job already started)
	"""
	getLogger().info(">> rescheduleJob(%s)" % str(jobId))
	res = False
	try:
		res = JobManager.instance().rescheduleJob(jobId, at)
	except Exception, e:
		e =  Exception("Unable to complete rescheduleJob operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< rescheduleJob(...): Fault:\n%s" % str(e))
		raise(e)

	getLogger().info("<< rescheduleJob: %s" % str(res))
	return res

def sendSignal(jobId, signal):
	"""
	Sends a signal to the job id'd by jobId.
	
	@since: 1.0

	@type  jobId: integer
	@param jobId: the job Id
	@type  signal: string
	@param signal: the signal to send to the job 
	
	@throws Exception: in case of an internal error.

	@rtype: bool
	@returns: True if successfully sent, or False if the job was not found.
	"""
	getLogger().info(">> sendSignal(%d, %s)" % (jobId, signal))
	ret = False
	try:
		ret = JobManager.instance().sendSignal(jobId, signal)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< sendSignal(...): Fault:\n%s" % str(e))
		raise(e)
	getLogger().info("<< sendSignal: %s" % str(ret))
	return ret
	

################################################################################
# service: file (File management)
################################################################################

"""
Testerman identifies a resource (ats, log, campaign, revision, ...)
via a virtual path (vpath) for short.
A vpath looks like a typical /-separated path, but uses some conventions:

/repository/*: test objects (ats, campaign, logs, ...)
/repository/*/something.ats: an ats
/repository/*/something.campaign: a campaign
/repository/*/something.py: a module

/repository/*/something.ats/profiles: the (virtual) folder that contains shared
profiles for the ATS something.ats
/repository/*/something.ats/runs: the (virtual) folder that contains logs

Files that are not in /repository are not part of a virtualized file system,
but directory looked up in the $document_root/ folder, for instance:

/updates/*: contains the component packages that can be served via the server
for autoupdate (pyagent, qtesterman)
/updates.xml: the file that references the components that have been published
/archives: used to store execution logs for the various atses.

Actually, when looking for /repository/*/something.ats/runs,
the server looks at /archives/*/something.ats.
The vpath location, however, is preferred to maintain a stable abstraction
about where (and how) logs are stored.
"""

def getFile(path, useCompression = False):
	"""
	Retrieves a file according to the path.
	The path is relative to the document root.
	
	If useCompression is set, compress the output before encoding it to mime64.
	
	@since: 1.0

	@type  path: string
	@param path: a path to a file
	@type  useCompression: bool
	@param useCompression: if True, the output is gziped before being mime64-encoded
	
	@rtype: string (utf-8 or buffer, encoded in base64), or None
	@returns: None if the file was not found,
	          or the file contents in base64 encoding, optionally compressed
	"""
	getLogger().info(">> getFile(%s, %s)" % (path, useCompression))
	if not path.startswith('/'):
		path = '/' + path

	ret = None
	try:
		contents = FileSystemManager.instance().read(path)
		if contents is None:
			ret = None
		else:
			if useCompression:
				ret = base64.encodestring(zlib.compress(contents))
			else:
				ret = base64.encodestring(contents)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< getFile(...): Fault:\n%s" % str(e))
		ret = None
	
	if ret is not None:
		getLogger().info("<< getFile(%s): %d bytes returned" % (path, len(ret)))
	else:
		getLogger().info("<< getFile(%s): file not found" % (path))
	return ret

def putFile(content, path, useCompression = False, username = None):
	"""
	Writes a file to docroot/path
	
	@since: 1.0

	@type  content: utf-8 encoded (or buffer) string, encoded in mime64
	@param content: the content of the file
	@type  path: string
	@param path: a complete path, with filename and extension, relative to the document root.
	@type  useCompression: bool
	@param useCompression: (since 1.3) if set to True, the content is gziped before being mime64-encoded.
	@type  username: string
	@param username: (since 1.7) the committer/writer
	
	@rtype: bool
	@returns: True if OK, False otherwise
	"""
	getLogger().info(">> putFile(%s, %s)" % (path, useCompression))
	if not path.startswith('/'):
		path = '/' + path

	res = False
	try:
		content = base64.decodestring(content)
		if useCompression:
			content = zlib.decompress(content)
		revision = FileSystemManager.instance().write(path, content, username = username)
		# No revision handling for now
		# We should return the new filepath in case of a success
		# /repository/samples/test.ats@1.1.2
		# etc
		res = True
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< putFile(...): Fault:\n" + str(e))
		raise(e)
	
	getLogger().info("<< putFile(): %s" % str(res))
	return res

def getDirectoryListing(path):
	"""
	Returns the contents of a directory.
	Also filters some 'internal' files (in particular __init__.py files)
	
	@since: 1.0

	@type  path: string
	@param path: the path of the directory within the docroot
	
	@rtype: list of dict{'name': string, 'type': string in [ ats, campaign, module, log, directory, package, ... ] }
	@returns: the dir contents, with a name (with extension) relative to the dir,
	          and an associated application type.
	          Returns None if the directory was not accessible or in case of an error.
	"""
	getLogger().info(">> getDirectoryListing(%s)" % path)
	if not path.startswith('/'):
		path = '/' + path

	res = []
	try:
		res = FileSystemManager.instance().getdir(path)
		if res is None:
			raise Exception("Unable to get directory contents through backend")

		# Sort the entries, so that it is useless to implement it in all clients ?
		res.sort(key = operator.itemgetter('name'))
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< getDirectoryListing(...): Fault:\n%s" % str(e))
		# Well, actually, we do not return a fault in this case...
		res = None

	if res is not None:
		getLogger().info("<< getDirectoryListing(%s): %d entries returned" % (path, len(res)))
	else:
		getLogger().info("<< getDirectoryListing(%s): path not found or error" % (path))
	return res
		
def getFileInfo(path):
	"""
	Gets some info about a file.
	
	Returns a dict{ 'size': integer, 'timestamp': float }
	where the size is optional (in bytes, if provided), and timestamp is
	the file modification time.

	@since: 1.0

	@type  path: string
	@param path: the path to the file whose info we want to get
	
	@rtype: a dict, or None
	@returns: None on error, or the dict of attributes.
	"""
	getLogger().info(">> getFileInfo(%s)" % path)
	if not path.startswith('/'):
		path = '/' + path

	res = None
	try:
		attributes = FileSystemManager.instance().attributes(path)
		if attributes:
			res = {}
			if attributes.size is not None:
				res['size'] = attributes.size
			if attributes.mtime is not None:
				res['timestamp'] = attributes.mtime
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< getFileInfo(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< getFileInfo(): %s" % str(res))
	return res

def removeFile(path):
	"""
	Removes a file.
	
	@since: 1.0

	@type  path: string
	@param path: the docroot-path to the file to delete
	
	@rtype: bool
	@returns: True if OK, False if nothing deleted. (? to check)
	"""
	getLogger().info(">> removeFile(%s)" % path)
	if not path.startswith('/'):
		path = '/' + path

	res = False
	try:
		res = FileSystemManager.instance().unlink(path)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< removeFile(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< removeFile(): %s" % str(res))
	return res

def removeDirectory(path, recursive = False):
	"""
	Removes an empty directory, unless recursive is set to True.
	
	@since: 1.1

	@type  path: string
	@param path: the docroot-path to the directory to delete
	@type  recursive: bool
	@param recursive: True if we should delete files and directories in it. DANGEROUS.
	
	@rtype: bool
	@returns: True if OK, False if nothing deleted. (? to check)
	"""
	getLogger().info(">> removeDirectory(%s)" % path)
	if not path.startswith('/'): path = '/' + path

	res = False
	try:
		res = FileSystemManager.instance().rmdir(path, recursive)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< removeDirectory(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< removeDirectory(): %s" % str(res))
	return res

def move(source, destination):
	"""
	Moves a file or a directory to destination.
	Recursive operation: if the source is a directory, the whole
	tree will be moved. 

	Logs associated to a scripts, if any, are
	NOT moved. They are kept available in the archives,
	but not associated to the script any more.
	
	FIXME: Revisions should be moved, however. 
	
	source is a docroot to an existing path or directory.
	destination is a docroot path to a destination:
	- if source is a dir, destination can be an existing dir
	  (will create a new dir in it) or a new directory name
	  (will rename the directory).
	- if source is a file, destination can be an existing dir
	  (will create the file in it, without renaming it), or
		a new file name (will rename the file).
	
	@since: 1.3

	@type  source: string
	@param source: docroot-path to the object to move
	@type  destination: string
	@param destination: docroot-path to the destination
	(if existing: must be a directory; if not existing, will rename
	the object on the fly)

	@rtype: bool
	@returns: True if the move was OK, False otherwise.
	"""
	getLogger().info(">> move(%s, %s)" % (source, destination))
	if not source.startswith('/'): source = '/' + source
	if not destination.startswith('/'): destination = '/' + destination

	res = False
	try:
		res = FileSystemManager.instance().move(source, destination)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< move(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< move(): %s" % str(res))
	return res

def copy(source, destination):
	"""
	Copies a file or a directory to destination.
	Recursive operation: if the source is a directory, the whole
	tree will be copied. 
	
	Meta children (Revisions and logs, if any) are NOT copied.
	
	source is a docroot to an existing path or directory.
	destination is a docroot path to a destination:
	- if source is a dir, destination can be an existing dir
	  (will create a new dir in it) or a new directory name
	  (will rename the directory).
	- if source is a file, destination can be an existing dir
	  (will create the file in it, without renaming it), or
		a new file name (will rename the file).
	
	@since: 1.3

	@type  source: string
	@param source: docroot-path to the object to move
	@type  destination: string
	@param destination: docroot-path to the destination
	(if existing: must be a directory; if not existing, will rename
	the object on the fly)

	@rtype: bool
	@returns: True if the move was OK, False otherwise.
	"""
	getLogger().info(">> copy(%s, %s)" % (source, destination))
	if not source.startswith('/'): source = '/' + source
	if not destination.startswith('/'): destination = '/' + destination

	res = False
	try:
		res = FileSystemManager.instance().copy(source, destination)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< copy(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< copy(): %s" % str(res))
	return res

def rename(path, newName):
	"""
	Renames a file or a directory to newName, in the same folder.
	
	@since: 1.3

	@type  path: string
	@param path: the docroot-path to the object to rename
	@type  newName: string
	@param newName: the new name (basename) of the object, including extension,
	                if applicable.
	
	@rtype: bool
	@returns: False if newName already exists. True otherwise.
	"""
	getLogger().info(">> rename(%s, %s)" % (path, newName))
	if not path.startswith('/'): path = '/' + path

	res = False
	try:
		res = FileSystemManager.instance().rename(path, newName)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< rename(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< rename(): %s" % str(res))
	return res

def makeDirectory(path):
	"""
	Creates a directory and all the needed directories to it, if any.
	
	@since: 1.3
	
	@type  path: string
	@param path: the docroot-path to the directory to create
	
	@rtype: bool
	@returns: True if the directory was created, False otherwise.
	"""
	getLogger().info(">> makeDirectory(%s)" % (path))
	if not path.startswith('/'): path = '/' + path

	res = False
	try:
		res = FileSystemManager.instance().mkdir(path)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< makeDirectory(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< makeDirectory(): %s" % str(res))
	return res

def getDependencies(path, recursive = False):
	"""
	Computes the file dependencies of the file referenced by path.
	
	If recursive is set to True, also searches for additional dependencies
	recursively; otherwise only direct dependencies are computed.
	
	A dependency for an ATS is a module it imports.
	A depencendy for a module is a module it imports.
	A dependency for a campaign is a a script (ats or campaign) it calls.
	
	This method may be used by a client to create a package.
	
	@since: 1.3

	@type  path: string
	@param path: a docroot path to a module, ats or campaign
	@type  recursive: boolean
	@param recursive: False for direct depencencies only. True for all
	dependencies. 
	
	@rtype: list of strings
	@returns: a list of dependencies as docroot-path to filenames.
	A dependency is only listed once (no duplicate).
	"""
	getLogger().info(">> getDependencies(%s, %s)" % (path, recursive))
	if not path.startswith('/'): path = '/' + path

	res = []
	try:
		source = FileSystemManager.instance().read(path)
		if source is None:
			raise Exception('Cannot find %s' % path)
		
		if path.endswith('.py'):
			res = DependencyResolver.python_getDependencyFilenames(source, path, recursive)
		elif path.endswith('.ats'):
			res = DependencyResolver.python_getDependencyFilenames(source, path, recursive)
		elif path.endswith('.campaign'):	
			res = DependencyResolver.campaign_getDependencyFilenames(source, os.path.split(path)[0], recursive, path)
		else:
			raise Exception('Unsupported file format, cannot resolve dependencies')
		
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< getDependencies(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< getDependencies(): %s" % str(res))
	return res
	

################################################################################
# service: package (package management)
################################################################################

def exportPackage(path, useCompression = False):
	"""
	Creates and returns a testerman package file (.tpk) from a package whose root docroot-path
	is path.
	
	A tpk file is a tar.gz file containing all package files (the package.xml file
	is in the root folder of the package)
	
	@since: 1.3
	
	@type  path: string
	@param path: a docpath to a package root folder
	@type  useCompression: bool
	@param useCompression: if True, the output is gziped before being mime64-encoded
	
	@rtype: string (utf-8 or buffer, encoded in base64), or None
	@returns: None if the package was not found,
	          or the tpk file contents in base64 encoding, optionally compressed
	"""
	getLogger().info(">> createPackageFile(%s, %s)" % (path, useCompression))
	if not path.startswith('/'): path = '/' + path

	ret = None
	try:
		# We have to get all files in the package folder (recursively) then create an archive
		
		contents = Package.createPackageFile(path)
		if contents is None:
			ret = None
		else:
			if useCompression:
				ret = base64.encodestring(zlib.compress(contents))
			else:
				ret = base64.encodestring(contents)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< createPackageFile(...): Fault:\n%s" % str(e))
		raise(e)
	
	if ret is not None:
		getLogger().info("<< createPackageFile(%s): %d bytes returned" % (path, len(ret)))
	else:
		getLogger().info("<< createPackageFile(%s): package not found" % (path))
	return ret

def importPackageFile(content, path, useCompression = False):
	"""
	Import a .tpk file into the repository.
	
	@since: 1.3

	@type  content: buffer string, encoded in mime64
	@param content: the content of the tpk file
	@type  path: string
	@param path: a document-root path where the package should be "unpacked". Must NOT exist.
	@type  useCompression: bool
	@param useCompression: if set to True, the content has been gziped before being mime64-encoded.

	@rtype: bool
	@returns: True if OK, False otherwise
	"""
	getLogger().info(">> importPackageFile(%s, %s)" % (path, useCompression))

	res = False
	try:
		content = base64.decodestring(content)
		if useCompression:
			content = zlib.decompress(content)
		
		res = Package.importPackageFile(content, path)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< importPackageFile(...): Fault:\n" + str(e))
		raise(e)
	
	getLogger().info("<< importPackageFile(): %s" % str(res))
	return res

def createPackage(path):
	"""
	Creates a new package tree somewhere in the docroot.

	@since: 1.3

	@type  path: string
	@param path: docroot path to the package root

	@throws Exception on error

	@rtype: bool
	@returns: True if OK, False otherwise
	"""
	getLogger().info(">> createPackage(%s)" % (path))
	if not path.startswith('/'): path = '/' + path

	res = False
	try:
		res = Package.createPackage(path)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< createPackage(...): Fault:\n" + str(e))
		raise(e)
	
	getLogger().info("<< createPackage(): %s" % str(res))
	return res

def schedulePackage(path, username, session, at, script = None, profileName = None):
	"""
	Schedules a package to start at <at>.
	
	If script is provided, the package's default-script attribute is ignored
	and script is used instead.
	
	@since: 1.3
	"""
	getLogger().info(">> schedulePackage(%s, script = %s)" % (path, script))
	if not path.startswith('/'): path = '/' + path

	try:
		metadata = Package.getPackageMetadata(path)
		
		if not script:
			script = metadata['default-script']

		scriptFilename = "%s/src/%s" % (path, script)
		scriptPath = os.path.split(scriptFilename)[0]
		
		label = "%s:%s" % ('/'.join(path.split('/')[2:]), script)
		
		getLogger().info("Using package script filename %s, path %s" % (scriptFilename, scriptPath))
		
		if script.endswith(".campaign"):
			res = scheduleCampaign(FileSystemManager.instance().read(scriptFilename).decode('utf-8'), label, username, session, at = at, path = scriptPath)
		elif script.endswith(".ats"):
			res = scheduleAts(FileSystemManager.instance().read(scriptFilename).decode('utf-8'), label, username, session, at = at, path = scriptPath)
		else:
			raise Exception("Invalid script/default script for package execution (unrecognized job type based on extension - %s)" % script)
	
	except Exception, e:
		e =  Exception("Scheduling error: %s" % (str(e)))
		getLogger().info("<< schedulePackage(...): Fault:\n%s" % Tools.getBacktrace())
		raise(e)

	getLogger().info("<< schedulePackage(...): %s" % str(res))
	return res
		

################################################################################
# service: xc (Xc interface management)
################################################################################

def getXcInterfaceAddress():
	"""
	Gets the Xc interface address.
	
	@since: 1.0

	@rtype: dict { 'ip': string, 'port': integer }
	@returns: the Xc interface IP + port
	"""
	getLogger().info(">> getXcInterfaceAddress()")
	ret = { 'ip': ConfigManager.instance().get('interface.xc.ip'), 'port': ConfigManager.instance().get('interface.xc.port') }
	getLogger().info("<< getXcInterfaceAddress: %s" % str(ret))
	return ret


################################################################################
# service: agent (Agents & Probes management)
################################################################################

def deployProbe(agentName, probeName, probeType):
	"""
	Deploys a new probe on a already existent agent.
	
	@since: 1.0

	@type  agentName: string
	@param agentName: the agent name
	@type  probeType: string
	@param probeType: the type of the probe to deploy
	@type  probeName: string
	@param probeName: the name of the probe to deploy.
	
	The final probe URI will be: probe:probeName@agentName

	@rtype: bool
	@returns: True
	"""
	getLogger().info(">> deployProbe(%s, %s, %s)" % (agentName, probeType, probeName))
	# Raises an error if needed
	try:
		ProbeManager.instance().deployProbe(agentName, probeName, probeType)
	except Exception, e:
		getLogger().info("<< deployProbe: Fault:\n" + str(e))
		raise(e)
	getLogger().info("<< deployProbe OK")
	return True

def undeployProbe(agentName, probeName):
	"""
	Undeploys an existing probe on a already existent agent.
	
	@since: 1.0

	@type  agentName: string
	@param agentName: the agent name
	@type  probeName: string
	@param probeName: the name of the probe to undeploy.
	
	@rtype: bool
	@returns: True
	"""
	getLogger().info(">> undeployProbe(%s, %s)" % (agentName, probeName))
	# Raises an error if needed
	try:
		ProbeManager.instance().undeployProbe(agentName, probeName)
	except Exception, e:
		getLogger().info("<< undeployProbe: Fault:\n" + str(e))
		raise(e)
	getLogger().info("<< undeployProbe OK")
	return True

def getRegisteredProbes():
	"""
	Gets currently registered probes.
	
	@since: 1.0

	@rtype: list of dict{name: string, type: string, contact: string, locked: bool, uri: string}
	@returns: a list of registered probes with their names, types, contact (extracted from their agent),
	uri, and locking state
	"""
	res = []
	getLogger().info(">> getRegisteredProbes")
	try:
		res = ProbeManager.instance().getRegisteredProbes()
	except Exception, e:
		getLogger().info("<< getRegisteredProbes: Fault:\n" + str(e))
		raise(e)
	
	getLogger().info("<< getRegisteredProbes: %s probes returned" % str(len(res)))
	return res

def getRegisteredAgents():
	"""
	Gets currently registered agents.
	
	@since: 1.0

	@rtype: list of dict{name: string, type: string, contact: string, uri: string, supported-probes: list of strings, user-agent: string}
	@returns: a list of registered agents with their names, types, contact,
	uri, list of supported probe types, and user agent.
	"""
	res = []
	getLogger().info(">> getRegisteredAgents")
	try:
		res = ProbeManager.instance().getRegisteredAgents()
	except Exception, e:
		getLogger().info("<< getRegisteredAgents: Fault:\n" + str(e))
		raise(e)
	
	getLogger().info("<< getRegisteredAgents: %s agents returned" % str(len(res)))
	return res

def restartAgent(agentName):
	"""
	Restarts an agent whose uri is agent:agentName

	@since: 1.1

	@type  agentName: string
	@param agentName: the name of the agent to restart (i.e. not its URI)
	
	@rtype: bool
	@returns: True
	"""
	getLogger().info(">> restartAgent(%s)" % (agentName))
	# Raises an error if needed
	try:
		ProbeManager.instance().restartAgent(agentName)
	except Exception, e:
		getLogger().info("<< restartAgent: Fault:\n" + str(e))
		raise(e)
	getLogger().info("<< restartAgent OK")
	return True

def updateAgent(agentName, branch = None, version = None):
	"""
	Requires an agent to update to version/branch (if provided), or to update to the
	latest version of branch (if provided), or to update to the latest version
	of its default branch (if no version/branch provided).

	@since: 1.1

	@type  agentName: string
	@param agentName: the name of the agent to update (i.e. not its URI)
	@type  branch: string
	@param branch: a version branch (usually 'experimental', 'stable', ...)
	@type  version: string
	@param version: a valid version for the agent component
	
	@rtype: bool
	@returns: True
	"""
	getLogger().info(">> updateAgent(%s)" % (agentName))
	# Raises an error if needed
	try:
		ProbeManager.instance().updateAgent(agentName)
	except Exception, e:
		getLogger().info("<< updateAgent: Fault:\n" + str(e))
		raise(e)
	getLogger().info("<< updateAgent OK")
	return True


################################################################################
# service: server (Server Management: stats, low level info, etc)
################################################################################

def getConfigInformation():
	"""
	Returns the current internal configuration values.
	
	@since: 1.0
	@deprecated: 1.4 - use getVariables() instead.

	@rtype: a dict[string] of strings
	@returns: a dict containing the configuration values, indexed by their keys
	"""	
	ret = {}
	for variable in ConfigManager.instance().getVariables():
		ret[variable['key']] = str(variable.get('actual'))
	return ret

def getBackendInformation():
	"""
	Returns the FS mount points and their associated backend descriptions.

	@since: 1.0

	@rtype: a dict[string] of strings
	@returns: a dict containing a description of the backend,
	indexed by the mountpoint
	"""	
	ret = {}
	for mountpoint, backend in FileSystemBackendManager.Mountpoints.items():
		ret[mountpoint] = str(backend)
	return ret

def getSystemInformation():
	"""
	Returns some system information,
	regarding the hardware, os, and the application (the server)
	
	@since: 1.0

	@rtype: a dict[string] of string
	@returns: a dict with some supposedly interesting info
	"""
	import platform

	ret = {}
	# Platform
	ret['machine'] = platform.machine()
	ret['node'] = platform.node()
	ret['system'] = platform.system()
	ret['architecture'] = platform.architecture()[0]
	ret['release'] = platform.system()
	ret['python-version'] = platform.python_version()
	# Physical
	# TODO
	# Application (low-level)
	ret['ws-version'] = Versions.getWsVersion()
	ret['xc-version'] = Versions.getXcVersion()
	ret['server-version'] = Versions.getServerVersion()

	return ret

def getCounter(path):
	"""
	TODO.
	"""
	return 0

def getCounters(paths):
	"""
	TODO.
	"""
	return {}

def getAllCounters():
	"""
	TODO
	"""
	return {}

def resetCounter(path):
	"""
	TODO
	"""
	return False

def resetAllCounters():
	"""
	TODO
	"""
	return False

def getVariables(component = "ts"):
	"""
	Returns all persisted and transient variables for the provided server component, with
	their different default/user-provided/actual values.
	
	Replaces getConfigInformation.
	
	The result is a dict containing 2 entries,
	each containing a list of dict representing the variables:
	dict[persistent]: list of dict(key, actual, default, user, type, dynamic)
	dict[transient]: list of dict(key, value)
	
	@since: 1.4

	@type  component: string
	@param component: the server component to retrieve variables from.
	ts = testerman server; tacs = connected TACS

	@rtype: a dict[string] of list of dict
	@returns: the 2 classes of internal variables for the server component
	"""
	
	if component == "ts":
		cm = ConfigManager.instance()
		variables = dict(persistent = cm.getVariables(), transient = cm.getTransientVariables())
		return variables
	elif component == "tacs":
		return None # To be implemented
	else:
		return None

def purgeJobQueue(older_than):
	"""
	Purges jobs in the queue that:
	- are completed (any status)
	- and whose completion time is strictly older than the provided older_than timestamp (UTC)

	@since: 1.5

	@type  older_than: float (timestamp)
	@param older_than: the epoch timestamp of the older job to keep

	@throws Exception in case of an error

	@rtype: int
	@returns: the number of purged jobs
	"""
	getLogger().info(">> purgeJobQueue(%s)" % older_than)
	res = 0
	try:
		res = JobManager.instance().purgeJobs(older_than)
	except Exception, e:
		e =  Exception("Unable to complete purgeJobs operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< purgeJobQueue(...): Fault:\n%s" % str(e))
		raise(e)

	getLogger().info("<< purgeJobQueue: %s job(s) purged" % res)
	return res

def persistJobQueue():	
	"""	
	Persists the current job queue to the standard persistence file.
	This administrative function may be convenient when you're about
	to kill the server violently.
	
	@since: 1.5

	@throws Exception in case of an error
	
	@rtype: None
	"""
	getLogger().info(">> persistJobQueue()")
	
	try:
		res = JobManager.instance().persist()
	except Exception, e:
		e =  Exception("Unable to complete persistJobQueue operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< persistJobQueue(...): Fault:\n%s" % str(e))
		raise(e)

	getLogger().info("<< persistJobQueue returned")
	return None
