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
# -*- coding: utf-8 -*-
# Module to implement Testerman clients, interfacing both Ws and Xc interfaces.
#
##

import TestermanMessages as Messages
import TestermanNodes as Nodes

import base64
import threading
import time
import xmlrpclib
import zlib


class DummyLogger:
	def formatTimestamp(self, timestamp):
		return time.strftime("%Y%m%d %H:%M:%S", time.localtime(timestamp))  + ".%3.3d" % int((timestamp * 1000) % 1000)

	def info(self, txt):
		pass
	
	def debug(self, txt):
		pass
	
	def critical(self, txt):
		print "%s - CRITICAL - %s" % (self.formatTimestamp(time.time()), txt)
	
	def error(self, txt):
		print "%s - ERROR - %s" % (self.formatTimestamp(time.time()), txt)

class Client(Nodes.ConnectingNode):
	"""
	This class interfaces both Ws and Xc access.
	This is a Testerman Xc Client Node delegating Ws operations to an embedded XMLRPC proxy.
	"""
	def __init__(self, name, userAgent, serverUrl, localAddress = ('', 0)):
		Nodes.ConnectingNode.__init__(self, name, userAgent)
		self._logger = DummyLogger()
		self._serverUrl = serverUrl
		self._localAddress = localAddress
		self.__proxy = xmlrpclib.ServerProxy(self._serverUrl, allow_none = True)
		self.__mutex = threading.RLock()
		self.__channel = None
		self.__localSubscriptions = {}
	
	def trace(self, txt):
		"""
		Reimplemented from Nodes.ConnectingNode).
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
			print "DEBUG: " + str(e)
			return ('', 0)

	def startXc(self):
		"""
		Starts the Xc interface: connects to Xc, listening for incoming notifications.
		You must start it to be able to subscribe to events.
		"""
		xcAddress = self.getXcInterfaceAddress()
		self.initialize((xcAddress['ip'], xcAddress['port']), self._localAddress)
		self.start()
	
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
		Gets the current job in the queue, returning several attributes for each of them.
		
		@throws Exception in case of an error.
		
		@rtype: a list of dict
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
		
		@rtype: dict{'id': integer, 'parent-id': integer, 'state': string, ...}, or None
		@returns: job information regarding the jobId, or None if the jobId was not found.
		"""
		self.getLogger().debug("Getting job status for jobId %s" % str(jobId))
		jobs = self.__proxy.getJobInfo(jobId)
		self.getLogger().debug("%d jobs retrieved" % len(jobs))
		if jobs:
			return jobs[0]
		else:
			return None

	def scheduleAts(self, ats, atsId, username, session = {}, at = 0.0):
		"""
		Schedules an ATS to be executed at 'at' time.
		If 'at' is lower than the current time, an immediate execution occurs. 
		
		@type  ats: unicode
		@param ats: the ATS to schedule
		@type  atsId: unicode
		@param atsId: a name identifying the ATS
		@type  session: dict[unicode] of strings
		@param session: the initial session parameters, altering the ATS metadata's provided ones
		@type  at: float
		@param at: timestamp of the scheduled start
		@type  username: string
		@param username: username identifying the user scheduling the ATS
		
		@throws Exception in case of a scheduling error.
		
		@rtype: dict{'job-id': integer, 'job-uri': string, 'message': string}
		@returns: some info about the scheduled job.
		"""
		try:
			s = {}
			if not (session is None):
				for (k, v) in session.items():
					s[k.encode('utf-8')] = v.encode('utf-8')
			return self.__proxy.scheduleAts(ats.encode('utf-8'), atsId.encode('utf-8'), username.encode('utf-8'), s, at)
		except xmlrpclib.Fault, e:
			self.getLogger().error("ATS Scheduling fault: " + str(e))
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
	# Subscription management
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
		# If Xc is not connected, does nothing ?
		# if not self.__channel:
		# 	return

		self._lock()
		if not self.__localSubscriptions.has_key(uri):
			self.__localSubscriptions[uri] = []
			self.__localSubscriptions[uri].append(callback)
			self._unlock()
			self.sendNotification(self.__channel, Messages.Notification("SUBSCRIBE", uri, "XC", "1.0"))
			return

		if not callback in self.__localSubscriptions[uri]:
			self.__localSubscriptions[uri].append(callback)

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
		self.getLogger().debug("getDirectoryListing: %d entries returned" % len(res))
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

	def putFile(self, content, filename):
		"""
		Put content as a file named filename in the server's document root.
		
		ATS, campaigns, etc are stored as utf-8. So you should make sure
		your content is utf-8 encoded when using this method.
		
		Automatically creates missing directories to filename, if needed.
		
		If the filename points outside the document root, returns False.
		
		@type  content: (buffer-like) string (typically utf-8)
		@param content: the file content
		@type  filename: string
		@param filename: the complete path within the docroot of the filename to create/modify
		
		@throws Exception in case of a (technical ?) error
		
		@rtype: bool
		@returns: True if the creation/update was ok, False otherwise
		"""
		self.getLogger().debug("Putting file %s to repository..." % filename)
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
		Removes a file or a directory. In this later case, this is a recursive removal.
		The caller should check that the directory is empty before deleting it.
		
		@type  filename: string
		@param filename: complete path within the docroot of the filename/directory to delete

		@throws Exception in case of a (technical) error
		
		@rtype: bool
		@returns: True file/directory deletion was ok, False if it was not possible to delete it.
		"""
		self.getLogger().debug("Removing %s ..." % filename)
		res = self.__proxy.removeFile(filename)
		self.getLogger().debug("Removed %s: " % filename + str(res))
		return res

	def getReferencingFiles(self, module):
		"""
		Returns a list of files referencing a module.
		The module is a module friendly ID.

		@type  module: string
		@param module: the module friendly ID we should check
		
		@rtype: list of strings
		@returns: a list of filenames (complete paths within the docroot) that references the module.
		"""
		self.getLogger().debug("Checking files referencing module %s..." % module)
		ret = self.__proxy.getReferencingFiles(module)
		self.getLogger().debug("Referencing files: " + str(ret))
		return ret

	##
	# Component management
	# TODO: replace this by simple getFile.
	##

	def getLatestComponentVersion(self, module, currentVersion, acceptTestVersion):
		self.getLogger().debug("getLatestComponent(%s, %s)..." % (module, currentVersion))
		res = self.__proxy.getLatestComponentVersion(module, currentVersion, acceptTestVersion)
		self.getLogger().debug("getLatestComponent returned version: " + str(res))
		return res

	def getComponentArchive(self, module, version):
		self.getLogger().debug("Downloading Component Archive %s-%s..." % (module, version))
		res = self.__proxy.getComponentArchive(module, version)
		self.getLogger().debug("Downloaded. Decoding...")
		if res:
			res = base64.decodestring(res)
		self.getLogger().debug("Decoded.")
		return res

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


# Basic test
if __name__ == "__main__":
	import sys
	c = Client("test", "ClientTester/1.0", sys.argv[1])
#	c.start()
	print str(c.getRegisteredProbes())
#	c.stop()
	
	
