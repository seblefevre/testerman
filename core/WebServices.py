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
# Web Services (Ws interface).
#
# WARNING: all methods in this file are exposed through the Ws
# (WebServices is a dispatch module for an XML-RPC server)
#
##

import ConfigManager
import CounterManager
import FileSystemManager
import FileSystemBackendManager
import JobManager
import ProbeManager
import Tools
import Versions

import base64
import logging
import operator
import time
import zlib

################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('TS.Ws')

################################################################################
# WS - Testerman Platform Control part
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
# Job management
################################################################################

def scheduleAts(source, atsId, username, session, at):
	"""
	Schedule an ATS to start at <at>
	
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
	
	@throws Exception: in case of an internal error

	@rtype: dict { 'job-uri': string, 'job-id': integer, 'message': string }
	@returns: a dict containing: 
	          job-uri: the newly created job uri, only valid if status == 0
	          job-id: the newly created job id, only valid if status == 0
	          message: a human readable string indicating what was done.
	"""
	getLogger().info(">> scheduleAts(..., session = %s)" % str(session))

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
		
		job = JobManager.AtsJob(atsId, source)
		job.setUsername(username)
		job.setScheduledStartTime(at)
		job.setScheduledSession(s)
		jobId = JobManager.instance().submitJob(job)
		message = ""
		if job.getScheduledStartTime() <= time.time():
			message = "immediate start"
		else:
			message = "will start on %s" % time.strftime("%Y%m%d, at %H:%M:%S", time.localtime(job.getScheduledStartTime()))
		res = { 'job-id': jobId, 'job-uri': job.getUri(), 'message': "ATS scheduled, %s. Its job ID is %d" % (message, jobId) }
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< scheduleAts(...): Fault:\n%s" % str(e))
		raise(e)

	getLogger().info("<< scheduleAts(...): %s" % str(res))
	return res

def scheduleCampaign(source, campaignId, username, session, at):
	"""
	Schedule an ATS to start at <at>
	
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
		
		job = JobManager.CampaignJob(campaignId, source)
		job.setUsername(username)
		job.setScheduledStartTime(at)
		job.setScheduledSession(s)
		jobId = JobManager.instance().submitJob(job)
		message = ""
		if job.getScheduledStartTime() <= time.time():
			message = "immediate start"
		else:
			message = "will start on %s" % time.strftime("%Y%m%d, at %H:%M:%S", time.localtime(job.getScheduledStartTime()))
		res = { 'job-id': jobId, 'job-uri': job.getUri(), 'message': "Campaign scheduled, %s. Its job ID is %d" % (message, jobId) }
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< scheduleCampaign(...): Fault:\n%s" % str(e))
		raise(e)

	getLogger().info("<< scheduleCampaign(...): %s" % str(res))
	return res

def getJobInfo(jobId = None):
	"""
	Gets a job or all jobs information.

	@type  jobId: integer, or None
	@param jobId: the job ID identifying the job whose status should be retrieved, or None for all jobs.
	
	@throws Exception: in case of an internal error.

	@rtype: a list of dict
	       {'id': integer, 'parent-id': integer, 'name': string,
	        'state': string in ['waiting', 'running', 'stopped', 'cancelled', 'killed', 'paused'],
	        'duration': float or None, 'result': integer or None, 'username': string, 
					'start-time': float or None, 'stop-time': float or None, 'scheduled-at': float,
	        'type': string in ['ats', 'campaign'],
	       }
	@returns: a list of info for the given job, or for all jobs in the queue if jobId is None.
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
	
	@type  jobId: integer
	@param jobId: the job ID identifying the job whose log should be retrieved
	@type  useCompression: bool
	@param useCompression: if set to True, compress the log using zlib before encoding the response in base64
	
	@rtype: string
	@returns: None if the job was not for, or the job's log in utf-8 encoded XML,
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
# File management
################################################################################

def getFile(path, useCompression = False):
	"""
	Retrieves a file according to the path.
	The path is relative to the document root.
	
	If useCompression is set, compress the output before encoding it to mime64.
	
	@type  path: string
	@param path: a path to a file
	@type  useCompression: bool
	@param useCompression: if True, the output is gziped before being mime64-encoded
	
	@rtype: string (utf-8 or buffer, encoded in base64), or None
	@returns: None if the file was not found,
	          or the file contents in base64 encoding, optionally compressed
	"""
	getLogger().info(">> getFile(%s, %s)" % (path, str(useCompression)))
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

def putFile(content, path):
	"""
	Write a file to docroot/path
	
	@type  content: utf-8 encoded (or buffer) string, encoded in mime64
	@param content: the content of the file
	@type  path: string
	@param path: a complete path, with filename and extension, relative to the document root.
	
	@rtype: bool
	@returns: True if OK, False otherwise
	"""
	getLogger().info(">> putFile(%s)" % (path))

	res = False
	try:
		content = base64.decodestring(content)
		revision = FileSystemManager.instance().write(path, content)
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
	
	@type  path: string
	@param path: the path of the directory within the docroot
	
	@rtype: list of dict{'name': string, 'type': string in [ ats, campaign, module, log, directory ] }
	@returns: the dir contents, with a name (with extension) relative to the dir, and an associated "meta"type.
	          Returns None if the directory was not accessible or in case of an error.
	"""
	getLogger().info(">> getDirectoryListing(%s)" % path)
	res = []
	try:
		contents = FileSystemManager.instance().getdir(path)
		if contents is None:
			raise Exception("Unable to get directory contents through backend")

		for entry in contents:
			name = entry['name']
			type_ = None
			if entry['type'] == 'file':
				if name.endswith('.ats'):
					type_ = 'ats'
				elif name.endswith('.campaign'):
					type_ = 'campaign'
				elif name.endswith('.py') and name != '__init__.py':
					type_ = 'module'
				elif name.endswith('.log'):
					type_ = 'log'
				elif name.endswith('.package'):
					type_ = 'package'
			elif entry['type'] == 'directory':
				type_ = 'directory'

			if type_:			
				res.append({'name': name, 'type': type_})

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
		getLogger().info("<< getDirectoryListing(%s): path not found" % (path))
	return res
		
def getFileInfo(path):
	"""
	Gets some info about a file.
	
	Returns a dict{ 'size': integer, 'timestamp': float }
	where the size is optional (in bytes, if provided), and timestamp is
	the file modification time.

	@type  path: string
	@param path: the path to the file whose info we want to get
	
	@rtype: a dict, or None
	@returns: None on error, or the dict of attributes.
	"""
	getLogger().info(">> getFileInfo(%s)" % path)

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
	Remove a file.
	
	@type  path: string
	@param path: the docroot-path to the file to delete
	
	@rtype: bool
	@returns: True if OK, False if nothing deleted. (? to check)
	"""
	getLogger().info(">> removeFile(%s)" % path)
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
	Remove an empty directory, unless recursive is set to True.
	
	@type  path: string
	@param path: the docroot-path to the directory to delete
	@type  recursive: bool
	@param recursive: True if we should delete files and directories in it. DANGEROUS.
	
	@rtype: bool
	@returns: True if OK, False if nothing deleted. (? to check)
	"""
	getLogger().info(">> removeDirectory(%s)" % path)
	res = False
	try:
		res = FileSystemManager.instance().rmdir(path, recursive)
	except Exception, e:
		e =  Exception("Unable to perform operation: %s\n%s" % (str(e), Tools.getBacktrace()))
		getLogger().info("<< removeDirectory(...): Fault:\n" + str(e))
		raise(e)

	getLogger().info("<< removeDirectory(): %s" % str(res))
	return res

def getReferencingFiles(module):
	"""
	Kept for compatibility.
	TODO (or to remove ?)
	"""	
	return []
	
################################################################################
# Xc management
################################################################################

def getXcInterfaceAddress():
	"""
	Gets the Xc interface address.
	
	@rtype: dict { 'ip': string, 'port': integer }
	@returns: the Xc interface IP + port
	"""
	getLogger().info(">> getXcInterfaceAddress()")
	ret = { 'ip': ConfigManager.get('interface.xc.ip'), 'port': ConfigManager.get('interface.xc.port') }
	getLogger().info("<< getXcInterfaceAddress: %s" % str(ret))
	return ret


################################################################################
# Agents & Probes management
################################################################################

def deployProbe(agentName, probeName, probeType):
	"""
	Deploys a new probe on a already existent agent.
	
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
# Component management
# TODO: must be managed as a file, with a specific metadata file if needed.
################################################################################

def getLatestComponentVersion(component, currentVersion, acceptTestVersions):
	"""
	Kept for compatibility.
	To remove.
	"""
	return ''


################################################################################
# Server Management: stats, low level info, etc.
################################################################################

def getConfigInformation():
	"""
	Returns the current internal configuration values.
	
	@rtype: a dict[string] of strings
	@returns: a dict containing the configuration values, indexed by their keys
	"""	
	ret = {}
	for name, value in ConfigManager.instance().getValues().items():
		ret[name] = str(value)
	return ret

def getBackendInformation():
	"""
	Returns the FS mount points and their associated backend descriptions.
	"""	
	ret = {}
	for mountpoint, backend in FileSystemBackendManager.Mountpoints.items():
		ret[mountpoint] = str(backend)
	return ret

def getSystemInformation():
	"""
	Returns some system information,
	regarding the hardware, os, and the application (the server)
	
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
	
