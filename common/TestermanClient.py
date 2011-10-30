# -*- coding: utf-8 -*-
##
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
# Module to implement Testerman clients, interfacing both Ws and Xc interfaces.
# 
# This version implements Ws 1.4, but can connect to Ws 1.0-1.3 as well.
#
##

import TestermanMessages as Messages
import TestermanNodes as Nodes

import base64
import tarfile
import threading
import time
import xmlrpclib
import zlib

import StringIO

class DummyLogger:
	"""
	A Defaut logging.Logger-like implementation.
	"""
	def formatTimestamp(self, timestamp):
		return time.strftime("%Y%m%d %H:%M:%S", time.localtime(timestamp))  + ".%3.3d" % int((timestamp * 1000) % 1000)

	def info(self, txt):
		pass
	
	def debug(self, txt):
		pass
	
	def critical(self, txt):
		print "%s - CRITICAL - %s" % (self.formatTimestamp(time.time()), txt)
	
	def warning(self, txt):
		print "%s - WARNING - %s" % (self.formatTimestamp(time.time()), txt)

	def error(self, txt):
		print "%s - ERROR - %s" % (self.formatTimestamp(time.time()), txt)

class Client(Nodes.ConnectingNode):
	"""
	This class interfaces both Ws and Xc accesses.
	This is a Testerman Xc Client Node delegating Ws operations to an embedded XMLRPC proxy.
	"""
	def __init__(self, name, userAgent, serverUrl, localAddress = ('', 0)):
		Nodes.ConnectingNode.__init__(self, name, userAgent)
		self._logger = DummyLogger()
		self._localAddress = localAddress
		self.__mutex = threading.RLock()
		self.__channel = None
		self.__localSubscriptions = {}
		self._serverUrl = None
		self.__proxy = None
		self.setServerUrl(serverUrl)
	
	def trace(self, txt):
		"""
		Reimplemented from Nodes.ConnectingNode.
		Forwards the trace as a debug action for the current logger.
		"""
		self.getLogger().debug(txt)
	
	def getLogger(self):
		return self._logger
	
	def setLogger(self, logger):
		self._logger = logger
	
	def _lock(self):
		self.__mutex.acquire()
	
	def _unlock(self):
		self.__mutex.release()
	
	def setServerUrl(self, url):
		"""
		Updates the current server url.
		It does not stop or restart the Xc link automatically.
		The caller should take care of that.
		
		@type  url: string
		@param url: the new server url
		"""
		self._serverUrl = url
		self.__proxy = xmlrpclib.ServerProxy(self._serverUrl, allow_none = True)
	
	def getServerUrl(self):
		"""
		Gets the current server URL.
		
		@rtype: string
		@returns: the current server url
		"""
		return self._serverUrl
	
	def getServerAddress(self):
		"""
		Returns the transport address of the current server.
		
		@rtype: (string, integer)
		@returns: (ip, port)
		"""
		try:
			netloc = self._serverUrl.split('/')[2]
			host, port = netloc.split(':')
			port = int(port)
			return (host, port)
		except Exception, e:
			return ('', 0)

	def startXc(self):
		"""
		Starts the Xc interface: connects to Xc, listening for incoming notifications.
		You must start it to be able to subscribe to events.
		
		@rtype: bool
		@returns: True if the link has been started (may be not connected yet),
		          False if we were unable to start the link (Ws interface error)
		"""
		try:
			xcAddress = self.getXcInterfaceAddress()
		except:
			return False
		self.initialize((xcAddress['ip'], xcAddress['port']), self._localAddress)
		self.start()
		return True
	
	def stopXc(self):
		"""
		Stops the Xc interface.
		Has no effect if it was not started.
		"""
		self.stop()

	##
	# Job management
	##
	
	def getJobQueue(self):
		"""
		Gets the current jobs in the queue, returning several attributes for each of them.
		
		@throws Exception in case of an error.
		
		@rtype: a list of dict (see the dict contents in getJobInfo() description)
		@returns: the list of current job in the server queue. See getJobInfo() for details
		about the dict.
		"""
		self.getLogger().debug("Getting jobs...")
		jobs = self.__proxy.getJobInfo()
		self.getLogger().debug("%d jobs retrieved" % len(jobs))
		return jobs

	def getJobInfo(self, jobId):
		"""
		@type  jobId: integer
		@param jobId: the job's ID

		@exception: Exception in case of an error.
		
		@rtype: dict{'id': integer, 'parent-id': integer, 'name': string,
	        'state': string in ['waiting', 'running', 'stopped', 'cancelled', 'killed', 'paused'],
	        'duration': float or None, 'result': integer or None, 'username': string, 
					'start-time': float or None, 'stop-time': float or None, 'scheduled-at': float,
	        'type': string in ['ats', 'campaign'],
					'path': string (docroot-based path for jobs whose source is in docroot) or None (client-based source)
	       }
				 or None
		@returns: job information regarding the jobId, or None if the jobId was not found.
		"""
		self.getLogger().debug("Getting job status for jobId %s" % str(jobId))
		jobs = self.__proxy.getJobInfo(jobId)
		self.getLogger().debug("%d jobs retrieved" % len(jobs))
		if jobs:
			return jobs[0]
		else:
			return None

	def scheduleAts(self, ats, atsId, username, session = {}, at = None, path = None, groups = None):
		"""
		Schedules an ATS to be executed at 'at' time.
		If 'at' is lower than the current server's time or None, an immediate execution occurs. 
		
		@type  ats: buffer string (utf-8 encoded string)
		@param ats: the ATS to schedule
		@type  atsId: unicode
		@param atsId: a friendly name identifying the ATS
		@type  session: dict[unicode] of strings
		@param session: the initial session parameters, altering the ATS metadata's provided ones
		@type  at: float
		@param at: timestamp of the scheduled start
		@type  username: string
		@param username: username identifying the user scheduling the ATS
		@type  path: string, or None
		@param path: the complete docroot-path to the file associated to the source,
	            	 if any. For source files not located on the server, set to None.
	            	 For the other ones, enables to know where to search dependencies
	            	 from.
		@type  groups: list os unicode strings, or None
		@param groups: a list of groups selected for this run. If set to None, all groups are considered
		               (no particular selection)
		
		@throws Exception in case of a scheduling error.
		
		@rtype: dict{'job-id': integer, 'job-uri': string, 'message': string}
		@returns: some info about the scheduled job.
		"""
		try:
			s = {}
			if not (session is None):
				for (k, v) in session.items():
					s[k.encode('utf-8')] = v.encode('utf-8')
			
			return self.__proxy.scheduleAts(ats, atsId.encode('utf-8'), username.encode('utf-8'), s, at, path, groups)
		except xmlrpclib.Fault, e:
			self.getLogger().error("ATS Scheduling fault: " + str(e))
			raise Exception(e.faultString)

	def scheduleCampaign(self, source, campaignId, username, session = {}, at = 0.0, path = None):
		"""
		Schedules a campaign to be executed at 'at' time.
		If 'at' is lower than the current server's time, an immediate execution occurs. 
		
		@type  ats: buffer string (utf-8 encoded string)
		@param ats: the ATS to schedule
		@type  campaignId: unicode
		@param campaignId: a name identifying the campaign
		@type  session: dict[unicode] of strings
		@param session: the initial session parameters, altering the ATS metadata's provided ones
		@type  at: float
		@param at: timestamp of the scheduled start
		@type  username: string
		@param username: username identifying the user scheduling the ATS
		@type  path: string, or None
		@param path: the complete docroot-path to the file associated to the source,
	            	 if any. For source files not located on the server, set to None.
	            	 For the other ones, enables to know where to search dependencies
	            	 from.
		
		@throws Exception in case of a scheduling error.
		
		@rtype: dict{'job-id': integer, 'job-uri': string, 'message': string}
		@returns: some info about the scheduled job.
		"""
		try:
			s = {}
			if not (session is None):
				for (k, v) in session.items():
					s[k.encode('utf-8')] = v.encode('utf-8')
			
			return self.__proxy.scheduleCampaign(source, campaignId.encode('utf-8'), username.encode('utf-8'), s, at, path)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Campaign Scheduling fault: " + str(e))
			raise Exception(e.faultString)
		
	def rescheduleJob(self, jobId, at):
		"""
		Schedules a (waiting) job to be executed at 'at' time.
		If 'at' is lower than the current server's time, an immediate execution occurs. 

		@type  jobId: integer
		@param jobId: the job ID
		@type  at: float
		@param at: timestamp of the scheduled start
		
		@throws Exception in case of a scheduling technical error.
		
		@rtype: bool
		@returns: True if the job was actually rescheduled (i.e. still in waiting state), 
		          or False if already started (or finished) or not found.
		"""
		try:
			return self.__proxy.rescheduleJob(jobId, at)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Job rescheduling fault: " + str(e))
			raise(e)

	def getJobLog(self, jobId):
		"""
		Returns the current log for a job whose ID is jobId, 
		or None if the job was not found.
		
		This client-side implementation always requests the log as
		a compressed data (gziped + base64 encoding).
		
		@type  jobId: integer
		@param jobId: the job ID
		
		@throws Exception in case of an error.
		
		@rtype: string (not unicode), or None
		@returns: job log, as an XML content (utf-8 encoding), or None
		if the job was not found.
		"""
		self.getLogger().debug("getJobLog...")
		res = self.__proxy.getJobLog(jobId)
		self.getLogger().debug("log retrieved")
		if res:
			res = zlib.decompress(base64.decodestring(res))
			self.getLogger().debug("log decompressed")
		return res

	def getJobDetails(self, jobId):
		"""
		Gets a specific job's details.

		@since: 1.8

		@type  jobId: integer
		@param jobId: the job ID identifying the job whose status should be retrieved.

		@throws Exception: in case of an internal error.

		@rtype: dict
	      	 {'id': integer, 'parent-id': integer, 'name': string,
	        	'state': string in ['waiting', 'running', 'stopped', 'cancelled', 'killed', 'paused'],
	        	'running-time': float or None, 'result': integer or None, 'username': string, 
						'start-time': float or None, 'stop-time': float or None, 'scheduled-at': float,
	        	'type': string in ['ats', 'campaign'],
						'path': string (docroot-based path for jobs whose source is in docroot) or None (client-based source),
						'te-filename': string or None
						'te-input-parameters': dict or None
						'te-command-line': string or None
						'source': base64-encoded string
	      	 }
		@returns: a dict of info for the given job, or None if not found or in case of an error.
		"""
		self.getLogger().debug("getJobDetails...")
		res = None
		try:
			res = self.__proxy.getJobDetails(jobId)
			if res and res.has_key('source'):
				# Automatically decode the source
				res['source'] = base64.decodestring(res['source'])
		except:
			pass
		return res

	def getJobLogFilename(self, jobId):
		"""
		Returns the job's log filename,
		or None if the job was not found.
		The returned filename is relative to the server's document root,
		and can be passed directly to a getFile() as parameter.
		
		@type  jobId: integer
		@param jobId: the job ID
		
		@throws Exception in case of an error.
		
		@rtype: string, or None
		@returns: the log filename, relative to the server's document root.
		"""
		self.getLogger().debug("getJobLogFilename...")
		res = self.__proxy.getJobLogFilename(jobId)
		return res

	def getJobOutputSession(self, jobId):
		"""
		Gets the output session for a job.
		Returns None if the job was not found, not complete,
		or did not generate any output session (in case of some premature
		job terminations: errors, kill).
		
		@type  jobId: integer
		@param jobId: the job ID
		
		@throws Exception in case of an error.
		
		@rtype: dict[string] of string ?? or None
		@returns: a dict containing the job output session.
		"""
		res = self.__proxy.getJobOutputSession(jobId)
		return res

	def sendSignal(self, jobId, signal):
		"""
		Sends a signal to a job.
		
		@type  jobId: integer
		@param jobId: the job ID
		@type  signal: string in [ 'kill', 'cancel', 'pause', 'resume' ]
		@param signal: the signal to send

		@throws Exception in case of an error.
		
		@rtype: bool
		@returns: True if the signal was successfully sent (job found),
		False otherwise (job not found)
		"""
		res = self.__proxy.sendSignal(jobId, signal)
		return res

	##
	# Xc management (subscription, event notifications, ...)
	##

	def getXcInterfaceAddress(self):
		"""
		@rtype:
		"""
		res = self.__proxy.getXcInterfaceAddress()
		return res

	def subscribe(self, uri, callback):
		"""
		Subscribes to events related to the uri, so that incoming events are raised through callback.
		Won't add a callback registration if it was already registered for this uri.
		
		@type  uri: string
		@param uri: the uri showse events we want to subscribe to 
		@type  callback: callable(string, string, Event)
		@param callback: the callback to call when receiving an event from uri
		
		@rtype: None
		@returns: None
		"""	
		self._lock()
		if not self.__localSubscriptions.has_key(uri):
			self.__localSubscriptions[uri] = []
			self.__localSubscriptions[uri].append(callback)
			self._unlock()
			self.sendNotification(self.__channel, Messages.Notification("SUBSCRIBE", uri, "XC", "1.0"))
			self.getLogger().debug("subscribed to URI %s, callback %s" % (uri, callback))
			return

		if not callback in self.__localSubscriptions[uri]:
			self.__localSubscriptions[uri].append(callback)
			self.getLogger().debug("already subscribed to URI %s, added callback %s" % (uri, callback))

		self._unlock()

	def unsubscribe(self, uri, callback = None):
		"""
		Unsubscribes from events related to the uri.
		Actually sends an UNSUBSCRIBE message over Xc only if no other callbacks
		are subscribed to the uri.
		
		@type  uri: string
		@param uri: the uri whose events we want to unsubscribe from
		@type  callback: callable(string, string, Event) or None
		@param callback: the callback to unregister for this event
		
		@rtype: None
		@returns: None
		"""
		# If Xc is not connected, does nothing ?
		# if not self.__channel:
		# 	return

		self.getLogger().debug("unsubscribing from URI %s, callback %s" % (uri, callback))

		self._lock()
		# We only send an UNSUBSCRIBE if no registered callback remains.
		if self.__localSubscriptions.has_key(uri):
			if callback:
				if callback in self.__localSubscriptions[uri]:
					self.__localSubscriptions[uri].remove(callback)
				if len(self.__localSubscriptions[uri]) == 0:
					del self.__localSubscriptions[uri]
					self._unlock()
					self.sendNotification(self.__channel, Messages.Notification("UNSUBSCRIBE", uri, "XC", "1.0"))
					return

			else:
				# We remove all callbacks for this uri
				del self.__localSubscriptions[uri]
				self._unlock()
				self.sendNotification(self.__channel, Messages.Notification("UNSUBSCRIBE", uri, "XC", "1.0"))
				return

		self._unlock()

	def notify(self, method, uri, body, headers = {}):
		"""
		Sends a notification through Xc. Useful for chat sessions, for instance.
		"""
		notification = Messages.Notification(method, uri, "XC", "1.0")
		for n, v in headers.items():
			notification.setHeader(n, v)
		notification.setApplicationBody(body)
		self.sendNotification(self.__channel, notification)

	def onNotification(self, channel, notification):
		"""
		Reimplemented from Nodes.ConnectingNode.
		"""
		uri = str(notification.getUri())
		
		if self.__localSubscriptions.has_key(uri):
			for callback in self.__localSubscriptions[uri]:
				try:
					callback(notification)
				except:
					pass

	def onConnection(self, channel):
		"""
		Reimplemented from Nodes.ConnectingNode.
		"""
		self.__channel = channel
		for uri in self.__localSubscriptions.keys():
			self.sendNotification(self.__channel, Messages.Notification("SUBSCRIBE", uri, "XC", "1.0"))

	##
	# File management: core, web services methods
	##
	
	def getDirectoryListing(self, directory):
		"""
		TODO: rename to getDirContent() ?
		
		Gets a list of objects in a directory. Empty list if the directory is empty or does not exist.
		
		@type  directory: string
		@param directory: complete path within the docroot of the directory to list
		
		@throws Exception in case of a (technical) error.
		
		@rtype: list of dict[('name': string, 'type' = 'ats'|'py'|'log'|'directory')]
		@returns: a list of object in the directory, with their relative name within the dir (with extension) and type.
		"""
		self.getLogger().debug("getDirectoryListing (%s)..." % directory)
		res = self.__proxy.getDirectoryListing(directory)
		if res is not None:
			self.getLogger().debug("getDirectoryListing: %d entries returned" % len(res))
		else:
			self.getLogger().debug("getDirectoryListing: invalid directory (%s)" % directory)
		return res

	def fileExists(self, filename):
		"""
		Tells if a file/path exists or not in the server's document root.
		
		@type  filename: string
		@param filename: complete path within the docroot of the filename to check

		@throws Exception in case of a (technical) error.

		@rtype: bool
		@returns: True if the file exists, False otherwise.
		"""
		res = self.__proxy.getFileInfo(filename)
		if res:
			return True
		else:
			return False

	def putFile(self, content, filename, useCompression = False, username = None):
		"""
		Puts content as a file named filename in the server's document root.
		
		ATS, campaigns, etc are stored as utf-8. So you should make sure
		your content is utf-8 encoded when using this method.
		
		Automatically creates missing directories to filename, if needed.
		
		If the filename points outside the document root, returns False.
		
		@type  content: (buffer-like) string (typically utf-8)
		@param content: the file content
		@type  filename: string
		@param filename: the complete path within the docroot of the filename to create/modify
		@type  useCompression: bool
		@param useCompression: if set to True, compress the content before sending it (requires Ws 1.3)
		@type  username: string
		@param username: if set, the username of the user who is writing this file, for
		revisions management (requires Ws 1.7)
		
		@throws Exception in case of a (technical ?) error
		
		@rtype: bool
		@returns: True if the creation/update was ok, False otherwise
		"""
		self.getLogger().debug("Putting file %s to repository..." % filename)
		if useCompression:
			payload = base64.encodestring(zlib.compress(content))
			res = self.__proxy.putFile(payload, filename, True, username)
		else:
			payload = base64.encodestring(content)
			res = self.__proxy.putFile(payload, filename)
		self.getLogger().debug("putFile: " + str(res))
		return res

	def getFile(self, filename):
		"""
		Gets a file.
		This implementation always request the file as compressed data
		(gzip + base64 encoding).
		
		@type  filename: string
		@param filename: complete path within the docroot of the filename to retrieve
		
		@throws Exception in case of a (technical) error.
		
		@rtype: (buffer) string, or None
		@returns: the file content, or None if the file was not found.
		"""
		start = time.time()
		self.getLogger().debug("Getting file %s..." % filename)
		try:
			content = self.__proxy.getFile(filename, True)
			if content:
				content = zlib.decompress(base64.decodestring(content))
				self.getLogger().debug("File decoded, loaded in %fs" % (time.time() - start))
		except Exception, e:
			self.getLogger().error("Unable to get file: " + str(e))
			raise e
		return content

	def getFileInfo(self, filename):
		"""
		@type  filename: string
		@param filename: complete path within the docroot of the filename to retrieve

		@throws Exception in case of a (technical) error
		
		@rtype: None, or a dict with at least 'timestamp': float, optionally 'size': int
		@returns: None if the file was not found, 
		or a dict with file attributes according to the backend.
		"""
		self.getLogger().debug("Getting info on file %s..." % filename)
		res = self.__proxy.getFileInfo(filename)
		self.getLogger().debug("File info received: " + str(res))
		return res

	def removeFile(self, filename):
		"""
		Removes a file.
		
		@type  filename: string
		@param filename: complete docroot-path of the file to delete

		@throws Exception in case of a (technical) error
		
		@rtype: bool
		@returns: True if file deletion was ok, False if it was not possible to delete it.
		"""
		self.getLogger().debug("Removing file %s ..." % filename)
		res = self.__proxy.removeFile(filename)
		self.getLogger().debug("Removed file %s: %s" % (filename, str(res)))
		return res

	def removeDirectory(self, path, recursive = False):
		"""
		Removes a directory.
		If recursive if false, only accepts to remove an empty directory.
		
		@type  path: string
		@param path: complete path within the docroot of the filename/directory to delete
		@type  recursive: bool
		@param recursive: deletes the directory recursively or not

		@throws Exception in case of a (technical) error
		
		@rtype: bool
		@returns: True if the directory deletion was ok, False if it was not possible to delete it.
		"""
		self.getLogger().debug("Removing directory %s ..." % path)
		res = self.__proxy.removeDirectory(path, recursive)
		self.getLogger().debug("Removed directory %s: %s" % (path, str(res)))
		return res

	def rename(self, path, newName):
		"""
		Renames a file or a directory to newName, in the same folder.

		@type  path: string
		@param path: the docroot-path to the object to rename
		@type  newName: string
		@param newName: the new name (basename) of the object, including extension,
	                	if applicable.

		@rtype: bool
		@returns: False if newName already exists. True otherwise.
		"""
		self.getLogger().debug("Renaming %s to %s..." % (path, newName))
		ret = self.__proxy.rename(path, newName)
		self.getLogger().debug("%s renamed to %s: %s" % (path, newName, ret))
		return ret
	
	def move(self, source, destination):
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

		@type  source: string
		@param source: docroot-path to the object to move
		@type  destination: string
		@param destination: docroot-path to the destination
		(if existing: must be a directory; if not existing, will rename
		the object on the fly)

		@rtype: bool
		@returns: True if the operation was OK.
		"""
		self.getLogger().debug("Moving %s to %s..." % (source, destination))
		ret = self.__proxy.move(source, destination)
		self.getLogger().debug("%s moved to %s: %s" % (source, destination, ret))
		return ret

	def copy(self, source, destination):
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

		@type  source: string
		@param source: docroot-path to the object to move
		@type  destination: string
		@param destination: docroot-path to the destination
		(if existing: must be a directory; if not existing, will rename
		the object on the fly)

		@rtype: bool
		@returns: True if the operation was OK.
		"""
		self.getLogger().debug("Copying %s to %s..." % (source, destination))
		ret = self.__proxy.copy(source, destination)
		self.getLogger().debug("%s copied to %s: %s" % (source, destination, ret))
		return ret
	
	def makeDirectory(self, path):
		"""
		Creates a directory indicated by path, creating all required directories
		if needed (mkdir -p).
		
		@type  path: string
		@param path: docroot-path to the directory to create
		
		@rtype: bool
		@returns: True if the directory was created, False otherwise.
		"""
		self.getLogger().debug("Making directory %s..." % (path))
		ret = self.__proxy.makeDirectory(path)
		self.getLogger().debug("Making directory %s: %s" % (path, ret))
		return ret

	def getDependencies(self, path, recursive = True):
		"""
		Computes the file dependencies of the file referenced by path.

		If recursive is set to True, also searches for additional dependencies
		recursively; otherwise only direct dependencies are computed.

		A dependency for an ATS is a module it imports.
		A depencendy for a module is a module it imports.
		A dependency for a campaign is a a script (ats or campaign) it calls.

		This method may be used by a client to create a package.

		@type  path: string
		@param path: a docroot path to a module, ats or campaign
		@type  recursive: boolean
		@param recursive: False for direct depencencies only. True for all
		dependencies. 

		@rtype: list of strings
		@returns: a list of dependencies as docroot-path to filenames.
		A dependency is only listed once (no duplicate).
		"""
		self.getLogger().debug("Getting dependencies for %s..." % (path))
		ret = self.__proxy.getDependencies(path, recursive)
		self.getLogger().debug("Dependencies for %s:\n%s" % (path, ret))
		return ret

	##
	# High-level file management: convenience functions to manage dependencies between files
	##

	def deleteAts(self, filename, deleteExecutionLogs = True):
		"""
		Deletes an ATS and its associated execution logs.

		@type  filename: string
		@param filename: the docroot-path of the ATS to delete
		@type  deleteExecutionLogs: bool
		@param deleteExecutionLogs: delete associated execution logs (with TE), if any
		"""
		ret = self.removeFile(filename)
		if deleteExecutionLogs:
			# compute associated log path
			archivePath = '/archives/%s' % ('/'.join(filename.split('/')[2:]))
			# this archive folder contains all TEs and all associated logs for the ats.
			# Delete all.
			self.removeDirectory(archivePath, True)
		return ret

	def deleteCampaign(self, filename, deleteExecutionLogs = True):
		"""
		Deletes a Campaign and its associated execution logs.

		@type  filename: string
		@param filename: the docroot-path of the ATS to delete
		@type  deleteExecutionLogs: bool
		@param deleteExecutionLogs: delete associated execution logs (with TE), if any
		"""
		ret = self.removeFile(filename)
		if deleteExecutionLogs:
			# compute associated log path
			archivePath = '/archives/%s' % ('/'.join(filename.split('/')[2:]))
			# this archive folder contains all TEs and all associated logs for the ats.
			# Delete all.
			self.removeDirectory(archivePath, True)
		return ret

	def deleteExecutionLog(self, filename, deleteTestExecutable = True):
		"""
		Deletes an execution log and its associated TE.

		@type  filename: string
		@param filename: the docroot-path of the file to delete
		@type  deleteTestExecutable: bool
		@param deleteTestExecutable: delete associated TE package
		"""
		assert(filename.endswith('.log'))
		tePath = filename[:-4] # removes the trailing '.log'
		ret = self.removeFile(filename)
		if deleteTestExecutable:
			self.removeDirectory(tePath, True)
		return ret

	def deleteProfile(self, filename):
		"""
		Deletes a profile associated to a script.

		@type  filename: string
		@param filename: the docroot-path of the file to delete
		"""
		assert(filename.endswith('.profile'))
		ret = self.removeFile(filename)
		return ret

	##
	# Update management
	##

	def getComponentVersions(self, component, branches = [ 'stable', 'testing', 'experimental' ]):
		"""
		Returns the available updates for a given component, with a basic filering on branches.
		
		Based on metadata stored into /updates.xml within the server's docroot:
		
		<updates>
			<update component="componentname" branch="stable" version="1.0.0" url="/components/componentname-1.0.0.tar">
				<!-- optional properties -->
				<property name="release_notes_url" value="/components/rn-1.0.0.txt />
				<!-- ... -->
			</update>
		</updates>
		
		@type  component: string
		@param component: the component identifier ("qtesterman", "pyagent", ...)
		@type  branches: list of strings in [ 'stable', 'testing', 'experimental' ]
		@param branches: the acceptable branches. 
		
		@rtype: list of dict{'version': string, 'branch': string, 'url': string, 'properties': dict[string] of strings}
		@returns: versions info, as list ordered from the newer to the older. The url is a relative path from the docroot, suitable
		          for a subsequent getFile() to get the update archive.
		"""
		updates = None
		try:
			updates = self.getFile("/updates.xml")
		except:
			return []
		if updates is None:
			return []
		
		ret = []
		# Now, parse the updates metadata
		import xml.dom.minidom
		import operator
		try:
		
			doc = xml.dom.minidom.parseString(updates)
			rootNode = doc.documentElement
			for node in rootNode.getElementsByTagName('update'):
				c = None
				branch = None
				version = None
				url = None
				if node.attributes.has_key('component'):
					c = node.attributes.get('component').value
				if node.attributes.has_key('branch'):
					branch = node.attributes.get('branch').value
				if node.attributes.has_key('version'):
					version = node.attributes.get('version').value
				if node.attributes.has_key('url'):
					url = node.attributes.get('url').value

				if c and c == component and url and version and branch in branches:
					# Valid version detected. Add it to our return result
					entry = {'version': version, 'branch': branch, 'url': url, 'properties': {}}
					# Don't forget to add optional update properties
					for p in node.getElementsByTagName('property'):
						if p.attributes.has_key('name') and p.attribute.has_key('value'):
							entry['properties'][p.attributes['name']] = p.attributes['value']
					ret.append(entry)
		except Exception, e:
			self.getLogger().warning("Error while parsing update metadata file: %s" % str(e))
			ret = []

		# Sort the results
		ret.sort(key = operator.itemgetter('version'))
		ret.reverse()
		return ret
	
	def installComponent(self, archivePath, destinationPath):
		"""
		Download the component file referenced by url, and install it into basepath.
		
		@type  archivePath: string
		@param archivePath: the docroot-path to the component archive to install
		@type  destinationPath: unicode string
		@param destinationPath: the local destination path to unpack the package to
		
		"""
		# We retrieve the archive
		archive = self.getFile(archivePath)
		if not archive:
			raise Exception("Archive file not found on server (%s)" % archivePath)
		
		# We untar it into the current directory.
		archiveFileObject = StringIO.StringIO(archive)
		try:
			tfile = tarfile.TarFile.open('any', 'r', archiveFileObject)
			contents = tfile.getmembers()
			# untar each file into the qtesterman directory

			for c in contents:
				self.getLogger().debug("Unpacking %s to %s..." % (c.name, destinationPath))
				tfile.extract(c, destinationPath)
				# TODO: make sure to set write rights to allow future updates
				# os.chmod("%s/%s" % (basepath, c), ....)
			tfile.close()
		except Exception, e:
			archiveFileObject.close()
			raise Exception("Error while unpacking the update archive:\n%s" % str(e))

		archiveFileObject.close()
	
	##
	# Package management
	##
	
	def createPackage(self, path):
		"""
		Creates a new package tree somewhere in the docroot.
		
		@type  path: string
		@param path: docroot path to the package root
		
		@throws Exception on error
		
		@rtype: bool
		"""
		self.getLogger().debug("Creating new package %s..." % path)
		ret = None
		try:
			ret = self.__proxy.createPackage(path)
		except xmlrpclib.Fault, e:
			self.getLogger().error("!! exportPackage: Fault: " + str(e.faultString))
			raise e
		return ret
	
	def exportPackage(self, path):
		"""
		Extracts a package file from a package
		This implementation always request the package file as compressed data
		(gzip + base64 encoding).
		
		@type  path: string
		@param path: complete path within the docroot of the package to retrieve
		
		@throws Exception in case of a (technical) error.
		
		@rtype: (buffer) string, or None
		@returns: the package file (.tpk) content, or None if the package was not found.
		"""
		start = time.time()
		self.getLogger().debug("Exporting package %s..." % path)
		res = None
		try:
			content = self.__proxy.exportPackage(path, True)
			if content:
				content = zlib.decompress(base64.decodestring(content))
				self.getLogger().debug("Package file extracted, loaded in %fs" % (time.time() - start))
		except xmlrpclib.Fault, e:
			self.getLogger().error("!! exportPackage: Fault: " + str(e.faultString))
			raise e
		return content
	
	def importPackageFile(self, content, path):
		"""
		Imports a package file to a package folder in the doc root.
		
		The destination patch must not exist.
		
		@type  path: string
		@param path: docroot path to the package root
		
		@throws Exception on error
		
		@rtype: bool
		@returns: True if the import was OK.
		"""
		start = time.time()
		self.getLogger().debug("Importing package file to %s..." % path)
		res = False
		try:
			res = self.__proxy.importPackageFile(base64.encodestring(content), path, False)
			self.getLogger().debug("Package file imported, loaded in %fs" % (time.time() - start))
		except xmlrpclib.Fault, e:
			self.getLogger().error("!! importPackageFile: Fault: " + str(e.faultString))
			raise e
		return res

	def schedulePackage(self, path, username, session = {}, at = 0.0, script = None, profileName = None):
		"""
		TODO: documentation (once the API is stable)
		"""
		try:
			s = {}
			if not (session is None):
				for (k, v) in session.items():
					s[k.encode('utf-8')] = v.encode('utf-8')

			return self.__proxy.schedulePackage(path, username.encode('utf-8'), s, at, script, profileName)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Package Scheduling fault: " + str(e))
			raise Exception(e.faultString)

	##
	# Probe management
	##
	
	def getRegisteredProbes(self):
		"""
		...
		"""
		self.getLogger().debug(">> getRegisteredProbes...")
		res = []
		try:
			res = self.__proxy.getRegisteredProbes()
		except xmlrpclib.Fault, e:
			self.getLogger().error("!! getRegisteredProbes: Fault: " + str(e.faultString))
			raise e
		self.getLogger().debug("<< getRegisteredProbes: %d probes returned" % len(res))
		return res

	def getRegisteredAgents(self):
		"""
		...
		"""
		self.getLogger().debug(">> getRegisteredAgents...")
		res = []
		try:
			res = self.__proxy.getRegisteredAgents()
		except xmlrpclib.Fault, e:
			self.getLogger().debug("!! getRegisteredAgents: Fault: " + str(e.faultString))
			raise e
		self.getLogger().debug("<< getRegisteredAgents: %d agents returned" % len(res))
		return res

	def deployProbe(self, agentName, probeName, probeType):
		"""
		Deploys a probe probeName, type probeType, on agent whose name is agentName
		"""
		self.getLogger().debug("Deploying probe %s: %s on %s..." % (probeType, probeName, agentName))
		try:
			return self.__proxy.deployProbe(agentName, probeName, probeType)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Deploying fault: " + str(e))
		return False

	def undeployProbe(self, agentName, probeName):
		"""
		Undeploys a probe probeName on agent whose name is agentName
		"""
		self.getLogger().debug("Undeploying probe %s from %s..." % (probeName, agentName))
		try:
			return self.__proxy.undeployProbe(agentName, probeName)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Undeploying fault: " + str(e))
			raise e
		return False

	def restartAgent(self, agentName):
		"""
		Restarts an agent whose name is agentName
		"""
		self.getLogger().debug("Restarting agent %s..." % (agentName))
		try:
			return self.__proxy.restartAgent(agentName)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Restarting fault: " + str(e))
			raise Exception(e.faultString)
		return False

	def updateAgent(self, agentName, branch = None, version = None):
		"""
		Updates an agent to branch:version, or to latest version on branch,
		or to latest version on its branch.
		"""
		self.getLogger().debug("Updating agent %s..." % (agentName))
		try:
			return self.__proxy.updateAgent(agentName, branch, version)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Updating fault: " + str(e))
			raise Exception(e.faultString)
		return False

	##
	# Server Management
	##
	
	def getCounter(self, path):
		res = self.__proxy.getCounter(path)
		return res
	
	def getCounters(self, paths):
		res = self.__proxy.getCounters(paths)
		return res
	
	def getAllCounters(self):
		res = self.__proxy.getAllCounters()
		return res

	def resetAllCounters(self):
		self.getLogger().debug("resetAllCounters()...")
		res = self.__proxy.resetAllCounters()
		self.getLogger().debug("resetAllCounters(): " + str(res))
		return res
			
	def getSystemInformation(self):
		self.getLogger().debug("getSystemInformation()...")
		res = self.__proxy.getSystemInformation()
		self.getLogger().debug("getSystemInformation(): " + str(res))
		return res

	def getBackendInformation(self):
		self.getLogger().debug("getBackendInformation()...")
		res = self.__proxy.getBackendInformation()
		self.getLogger().debug("getBackendInformation(): " + str(res))
		return res

	def getConfigInformation(self):
		self.getLogger().debug("getConfigInformation()...")
		res = self.__proxy.getConfigInformation()
		self.getLogger().debug("getConfigInformation(): " + str(res))
		return res

	def getVariables(self, component):
		self.getLogger().debug("getVariables()...")
		res = self.__proxy.getVariables()
		self.getLogger().debug("getVariables(): " + str(res))
		return res


# Basic test
if __name__ == "__main__":
	import sys
	c = Client("test", "ClientTester/1.0", sys.argv[1])
#	c.start()
	print str(c.getRegisteredProbes())
#	c.stop()
	
	
