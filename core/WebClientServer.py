#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2010,2011 Sebastien Lefevre and other contributors
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
# This is the WebClient Server module.
# This runs a web server to offer simple
# Testerman client capabilities through a web page,
# such as:
# browsing the repositories,
# execute an ATS
# display logs & ATS execution results, etc.
# 
#
# This has been implemented outside the embedded
# Testerman to be run on a different box.
#
##


import WebServer
import Tools
import ConfigManager
import TestermanClient
import TestermanMessages
import TEFactory
import ProfileTools

import logging
import BaseHTTPServer
import os.path
import socket
import select
import threading
import sys
import time
import optparse
import re
import libxml2
import JSON
import SocketServer




VERSION = '1.4.1'


DEFAULT_PAGE = "/index.vm"

JSON_CONTENT_TYPE = "text/plain" # or application/json

# "ajax-like" method async timeout
TIMEOUT_GET_JOB_STATUS = 10.0

# Rights
RIGHT_CUSTOMIZE_RUN_PARAMETERS = "customize-run-parameters"
RIGHT_SELECT_RUN_PROFILE = "select-run-profile"
RIGHT_SELECT_RUN_GROUPS = "select-run-groups"



cm = ConfigManager.instance()



################################################################################
# Logging & Tooling
################################################################################

def getLogger():
	return logging.getLogger('WebClient')

def formatTimestamp(timestamp):
  return time.strftime("%Y%m%d %H:%M:%S", time.localtime(timestamp))  + ".%3.3d" % int((timestamp * 1000) % 1000)

def escapeXml(s):
	"""
	Escape non-ascii characters (<= 1f).
	Notice that the XMLs we are dealing with are all utf-8 encoded.
	So no need to escape above 127.
	"""
	r = re.compile(ur'[\x00-\x1f]')
	def replacer(m):
		c = m.group(0)
		if c in [ '\n', '\r' ]:
			return c
		return "&#x"+('%02x' % ord(c))+";"
	return re.sub(r, replacer, s)


################################################################################
# Request Handler to provide Xc-equivalent interface through HTML5 WebSockets
################################################################################

class XcApplication(WebServer.WebSocketApplication):
	def __init__(self, testermanServerUrl, **kwargs):
		WebServer.WebSocketApplication.__init__(self, **kwargs)
		self._client = TestermanClient.Client(name = "Testerman WebClient/WebSocket", userAgent = "WebClient/%s" % VERSION, serverUrl = testermanServerUrl)

	def _getClient(self):
		return self._client

	def __str__(self):
		return "WebSocket/Xc application [%s]" % str(self._getClientAddress())

	def _onXcNotification(self, notification):
		"""
		Forward subscribed events to the WebSocket client
		"""
		if notification.isNotification():
			getLogger().debug("%s: received an Xc notification to forward" % self)
			self.wsSend(str(notification))

	##
	# Reimplementations from WebSocketApplication
	##
	
	def onWsOpen(self):
		getLogger().info("%s: connected" % self)
		# We connect the Xc Client and starts it.
		self._client.startXc()

	def onWsClose(self):
		getLogger().info("%s: disconnected" % self)
		# Let's disconnect the Xc Client
		self._client.stopXc()

	def onWsMessage(self, msg):
		"""
		Xc-like to Xc transformation.
		Not all Xc methods are supported.
		For now, we handle SUBSCRIBE <uri> only.
		
		The Xc-like (Xcl) interface is used between a web client and this application.
		This is not a complete Xc implementation to make web clients easier to develop.
		"""
		try:
			m = TestermanMessages.parse(msg)
		except Exception, e:
			getLogger().info("%s: Invalid Xc message: %s" % (self, str(e)))
			return
		
		if m.isRequest():
			method = m.getMethod()
			uri = str(m.getUri())
			if method == "SUBSCRIBE":
				getLogger().info("%s: subscribing to %s" % (self, uri))
				# We should do some authorization stuff here -not everybody should be allowed to monitor anything
				self._client.subscribe(uri, self._onXcNotification)
				getLogger().info("%s: subscribed to %s" % (self, uri))
			else:
				getLogger().info("%s: unsupported Xc request method (%s)" % (self, method))
				return
			
		else:
			getLogger().info("%s: unsupported Xc message, not a request" % (self))
			return


################################################################################
# Request Handler to provide WebClient services
################################################################################

class WebClientApplication(WebServer.WebApplication):
	def __init__(self, testermanClient, **kwargs):
		WebServer.WebApplication.__init__(self, **kwargs)
		self._client = testermanClient
		self._repositoryHome = None
		self._jobMonitorManager = JobMonitorManager(testermanClient)

	def authenticate(self, username, password):
		self._repositoryHome = None
		if cm.get('wcs.users.%s.password' % username) == password:
			self._repositoryHome = os.path.normpath('/repository/%s' % (cm.get('wcs.users.%s.repository_home' % username) or '/'))
			return True
		else:
			getLogger().warning("Invalid password for user %s" % username)
			return False

	def hasRight(self, username, right):
		"""
		Checks if a particular user has a particular right.
		Granted rights are defined as a coma-separated list of rights in the config file as wcs.users.%s.rights
		"""
		# Non-optimized implementation.
		# Waiting for an end-to-end user management for the Testerman infrastructure.
		rights = cm.get('wcs.users.%s.rights' % username) or ''
		return right in rights.split(',')

	def _getClient(self):
		return self._client

	def handle_docroot(self, path):
		self.request.sendError(403)
	
	def _adjustRepositoryPath(self, path):
		"""
		Makes sure that the repository path in within the restricted area
		the user has an access to (its "home")
		If not, simply replaces the path with the home.
		"""
		if not path: path = '/'
		path = os.path.normpath(path)
		home = self._repositoryHome
		if not path.startswith(home):
			path = home
		return path
	
	def handle_browser(self, path):
		"""
		Browses a particular folder or a file.
		
		Depending on the path extension, displays a page
		dedicated to ATS, campaign, or folder browsing.
		"""
		getLogger().info("Attempt to browse %s" % path)
		path = self._adjustRepositoryPath(path)
		getLogger().info("Actually browsing %s" % path)
		
		if path.endswith('.ats'):
			self._browse_ats(path)
		else:
			self._browse_directory(path)
	
	def _browse_directory(self, path):
		"""
		Displays the contents of a directory.
		@path: testerman-docroot-path of the directory.
		"""
		try:
			l = self._getClient().getDirectoryListing(path)
		except Exception, e:
			getLogger().error("Unable to browse directory %s: %s" % (path, str(e)))
			l = []

		if path > self._repositoryHome:
			l = [ dict(name = '..', type = 'directory') ] + l

		getLogger().debug('repository result: %s' % l)
		
		webpaths = []
		prev = ''
		for x in [ x for x in path.split('/') if x ]:
			current = "%s/%s" % (prev, x)
			webpaths.append(dict(label = x, path = current))
			prev = current
		
		self._serveTemplate("browser.vm", context = dict(path = path, entries = l, webpaths = webpaths))
	
	def _browse_ats(self, path):
		"""
		Displays a page to view latest ATS execution and to execute the ATS.
		
		@path: a testerman-docroot path to an ats.
		"""
		
		# Fetch the file to extract the metadata
		try:
			source = self._client.getFile(path)
		except Exception, e:
			getLogger().error("Unable to fetch source code for %s: %s" % (path, str(e)))
			self.request.sendError(404, "ATS not found")
			return
		# Now extract the metadata from the source		
		metadata = TEFactory.getMetadata(source)

		# Fetch the parameters
		parameters = None
		if self.hasRight(self.username, RIGHT_CUSTOMIZE_RUN_PARAMETERS):
			parameters = metadata.getSignature().values()
			# Let's sort them
			parameters.sort(lambda x, y: cmp(x.get("name"), y.get("name")))

		# Fetch the groups
		groups = None
		if self.hasRight(self.username, RIGHT_SELECT_RUN_GROUPS):
			groups = metadata.getGroups().values() # list of dict of name, description
			# Let's sort them
			groups.sort(lambda x, y: cmp(x.get("name"), y.get("name")))

		# Fetch the profiles
		profiles = []
		if self.hasRight(self.username, RIGHT_SELECT_RUN_PROFILE):
			archivePath = '/archives/%s' % ('/'.join(path.split('/')[2:]))
			try:
				l = self._getClient().getDirectoryListing(path + '/profiles')
			except Exception, e:
				getLogger().error("Unable to fetch profiles for %s: %s" % (path, str(e)))
				l = []
			if l:
				for entry in l:
					if entry['type'] == 'profile':
						profiles.append(dict(name = os.path.splitext(entry['name'])[0]))
		

		# Fetch available archived execution logs
		logs = []
		archivePath = '/archives/%s' % ('/'.join(path.split('/')[2:]))
		try:
			l = self._getClient().getDirectoryListing(archivePath)
		except Exception, e:
			getLogger().error("Unable to fetch logs for %s: %s" % (path, str(e)))
			l = []

		if l:
			for entry in l:
				if entry['type'] == 'log':
					log = {}
					name = entry['name']
					filename = '%s/%s' % (archivePath, name)
					# According to the name, retrieve some additional info.
					m = re.match(r'([0-9-]+)_(.*)\.log', name)
					if m:
						date = m.group(1)
						username = m.group(2)
						log = dict(name = name, filename = filename, date = date, username = username)
						logs.append(log)
		
		logs.reverse()

		webpaths = []
		prev = ''
		for x in [ x for x in path.split('/') if x ]:
			current = "%s/%s" % (prev, x)
			webpaths.append(dict(label = x, path = current))
			prev = current

		context = dict(path = path, logs = logs, webpaths = webpaths, profiles = profiles, parameters = parameters, groups = groups)
		
		self._serveTemplate("ats.vm", context = context)

	def handle_run_ats(self, path, profile = None, groups = None, **customParameters):
		"""
		Execute an ATS whose testerman-docroot-path is provided in argument.
		Once run, redirect the user to a monitoring page.
		"""
		getLogger().info("Attempt to run %s" % path)
		path = self._adjustRepositoryPath(path)
		getLogger().info("Actually running %s" % path)

		parameters = {}

		if profile and profile != "__custom__":
			if self.hasRight(self.username, RIGHT_SELECT_RUN_PROFILE):
				getLogger().info("Running %s with profile %s" % (path, profile))
				# We have to fetch the associated profile and turn its content into a dict of parameters
				if profile == "__default__":
					parameters = {}
				else:
					# Actually fetching (and parsing) the profile
					try:
						p = ProfileTools.parseProfile(self._getClient().getFile(path + '/profiles/%s.profile' % profile))
						if not p:
							raise Exception("Profile not found or invalid for this ATS")
					except Exception, e:
						getLogger().error("Error in run_ats: %s" % str(e))
						raise e
					parameters = p.getParameters()

		else:
			if self.hasRight(self.username, RIGHT_CUSTOMIZE_RUN_PARAMETERS):
				getLogger().info("Running %s with custom parameters:\n%s" % (path, repr(customParameters.items())))
				# Provided parameters must be decoded from utf8 to unicode
				# (provided as utf8 by the browser because the page was served as char-encoding utf8)
				for k, v in customParameters.items():
					parameters[k.decode('utf-8')] = v.decode('utf-8')
			
		getLogger().info("Running %s with resolved parameters:\n%s" % (path, repr(parameters.items())))

		if groups is not None:
			if self.hasRight(self.username, RIGHT_SELECT_RUN_GROUPS):
				if not isinstance(groups, list):
					# Single value - was passed to this function as a simple value, not a list
					groups = [ groups ]
			else:
				getLogger().info("Attempt to bypass groups selection right - discarding")
				groups = None
		
		getLogger().info("Running %s with selected groups:\n%s" % (path, repr(groups)))


		jobId = None
		try:
			source = self._getClient().getFile(path).decode('utf-8')
			if not source:
				raise Exception("ATS not found")

			# FIXME on server side: the "label" is actually used to locate
			# the archive folder where log files will be created. This is thus much more
			# than a 'label'...
			label = path[len('/repository/'):]
			session = parameters
			at = None
			username = '%s@%s' % (self.username, self.request.getClientAddress()[0])

			ret = self._getClient().scheduleAts(source, label, username, session, at, path = path, groups = groups)
			jobId = ret['job-id']
		except Exception, e:
			getLogger().error("Error in run_ats: %s" % str(e))
			raise e

		if jobId:
			# ATS started - let's monitor it
			self.request.sendResponse(302)
			self.request.sendHeader('Location', 'monitor_ats?%s' % jobId)
			self.request.sendHeader('Connection', 'Close')
			self.request.endHeaders()
		else:
			self.request.sendResponse(302)
			self.request.sendHeader('Location', 'ats?%s' % path)
			self.request.sendHeader('Connection', 'Close')
			self.request.endHeaders()

	def handle_monitor_ats(self, jobId):
		context = dict(jobId = jobId)
		error = False
		jobInfo = {}
		jobLogFilename = None
		try:
			jobInfo = self._getClient().getJobInfo(int(jobId))
			jobLogFilename = self._getClient().getJobLogFilename(int(jobId))
		except Exception, e:
			getLogger().error("handle_monitor_ats: %s" % str(e))
			error = True
		
		if jobInfo is None:
			error = True

		context = dict(jobId = jobId, error = error)
		if not error:
			for (k, v) in jobInfo.items():
				context[k.replace('-', '')] = v
			
#			self._startMonitoring(jobInfo)
			
		if context.has_key('runningtime') and context['runningtime']:
			context['runningtime'] = '%2.2f' % context['runningtime']

		if jobLogFilename:
			context['logFilename'] = jobLogFilename

		self._serveTemplate("monitor-ats.vm", context = context)

	def rawLogToStructuredLog(self, rawlog, xslt = None):
		"""
		Turns a raw log into a valid XML file structuring the test cases.
		"""
		# Structured log: 
		# <ats>
		#  <testcase id= verdict=>
		#   <default elements, from testcase-created to testcase-stopped, as is>
		#  </testcase>
		# </ats>
		
		getLogger().debug("DEBUG: preparing XML for re-structuration...")
		# Turns the raw log into a valid XML file for parsing
		rlog = '<?xml version="1.0" encoding="utf-8" ?>\n'
		rlog += '<ats>\n'
		rlog += rawlog
		rlog += '</ats>\n'

		# The ESC (27 / 0x1b) character is illegal in XML, even as an entity.
		# We replace it with the human readable string <ESC>
		rlog = rlog.replace('\x1b', '&lt;ESC&gt;')

		getLogger().debug("DEBUG: parsing XML...")
		# Now, let's parse it and move the 'root' elements below new testcase elements
 		rdoc = libxml2.parseDoc(rlog)
		getLogger().debug("DEBUG: re-structuring XML...")
		currentTestCaseNode = None
		atsNode = libxml2.newNode('ats')
		
		node = rdoc.getRootElement().children
		while node:
			nextnode = node.next
			if not node.type == 'element': # libxml2 constant ?
				pass

			else:
				# element nodes
				if node.hasProp('timestamp'):
					node.setProp('timestamp', formatTimestamp(float(node.prop('timestamp'))))

				# starting a new test case
				if node.name == 'testcase-created':
					currentTestCaseNode = libxml2.newNode('testcase')
					currentTestCaseNode.setProp('id', node.prop('id'))
					atsNode.addChild(currentTestCaseNode)

				# partipating to an open/started test case
				if currentTestCaseNode:
					node.unlinkNode()
					currentTestCaseNode.addChild(node)
					if node.name == 'testcase-stopped':
						currentTestCaseNode.setProp('verdict', node.prop('verdict'))
						currentTestCaseNode = None

				# Not within a testcase - part of the "ats" root
				else:
					if node.name == 'ats-started':
						atsNode.setProp('id', node.prop('id'))
						atsNode.setProp('start-timestamp', node.prop('timestamp'))
					elif node.name == 'ats-stopped':
						atsNode.setProp('result', node.prop('result'))
						atsNode.setProp('stop-timestamp', node.prop('timestamp'))

			node = nextnode

		# OK, we're done with the DOM tree.
		# Let's format it back to XML.

		ret = '<?xml version="1.0" encoding="%s"?>' % 'utf-8'
		if xslt:
			ret += '<?xml-stylesheet type="text/xsl" href="%s"?>' % xslt
		ret += atsNode.serialize()
		getLogger().debug("DEBUG: OK, structured XML finalized.")
		
		return ret

	def handle_view_log(self, path):
		"""
		Display an ATS log file as something human-readable (html).
		"""
		if not path:
			path = '/archives'
		path = os.path.normpath(path)
		if not path.startswith('/archives'):
			path = '/archives/' + path

		# A raw log file, as extracted from the server, 
		# is a collection of top-level xml elements; the whole file
		# is not a valid XML document.
		# We programmatically transform this to a valid XML document
		# that also structures the test cases to be more manageable
		# via XSL Tranformations.
		try:
			log = self._getClient().getFile(path)
		except Exception, e:
			self.request.sendError(404)
			return
		
		stylesheet = "ats-log-textual.vm.xsl"
		log = self.rawLogToStructuredLog(log, stylesheet)

		self._sendContent(log, contentType = "application/xml")
	
	def handle_download_log(self, path):
		if not path:
			path = '/archives'
		path = os.path.normpath(path)
		if not path.startswith('/archives'):
			path = '/archives/' + path
		
		try:
			log = '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n'
			log += self._getClient().getFile(path)
			log += '</ats>'
		except Exception, e:
			self.request.sendError(404)
			return
		
		filename = os.path.split(path)[1] + '.xml'
		self._sendContent(log, contentType = "application/xml", asFilename = filename)


	def handle_get_job_info(self, jobId, lastKnownState = None):
		"""
		Called via an ajax-like call.
		
		Returns the job status, either the current one if lastKnownState is different
		from the current one,
		or subscribes and waits for a state change to return it.
		"""
		jobInfo = self._jobMonitorManager.getJobInfo(jobId, lastKnownState)
		
		result = {}
		if jobInfo:
			for (k, v) in jobInfo.items():
				result[k.replace('-', '')] = v
			
			result["finished"] = (jobInfo["state"] in [ "complete", "cancelled", "killed", "error" ])
		else:
			result = None
		
		self._sendContent(JSON.dumps(result), contentType = JSON_CONTENT_TYPE)
	
	
	def handle_get_runtime_log(self, jobId, lastLogEventId = 0):
		"""
		Called via an ajax-like call.
		Returns the new log elements for a particular job (id'd by jobId)
		since the lastLogElementId.
		
		If the jobId is currently registered in our current monitoring threads,
		returns them as XML elements
		
		Otherwise returns a null object.
		"""
		elements = self._jobMonitorManager.getEvents(jobId)
		
		if not elements:
			time.sleep(1) # force a wait to avoid a requery. Normally we should wait until a new event arrives instead.
		
		logElements = [ dict(eventId = lastLogEventId + x[0], data = x[1]) for x in elements ]
		
		self._sendContent(JSON.dumps(logElements), contentType = JSON_CONTENT_TYPE)
	
	def _startMonitoring(self, jobInfo):
		self._jobMonitorManager.monitor(jobInfo)


class JobMonitorManager:
	"""
	This component is responsible for monitoring jobs that
	are watched by at least one web client,
	and buffering log events to serve them to the web clients
	via ajax polling.
	"""
	
	class EventQueue:
		"""
		The queue that contains buffered events for a particular
		job.
		"""
		def __init__(self, jobInfo):
			self._id = jobInfo['id']
			self._lastUpdate = time.time()
			self._lastEventId = -1
			self._queue = []
			self._running = True
		
		def setStopped(self):
			self._running = False
			self._lastUpdate = time.time()
		
		def enqueue(self, event):
			self._queue.append(event)
			self._lastEventId += 1
			self._lastUpdate = time.time()
		
		def isStopped(self):
			return not self._running
		
		def getLastUpdate(self):
			return self._lastUpdate

	def __init__(self, testermanClient):
		# TODO: add locks everywhere
		self._queues = {}			
		
		self._client = testermanClient
	
	def _getClient(self):
		return self._client

	def getJobInfo(self, jobId, lastKnownState):
		getLogger().debug("Checking for job info for %s (from %s)" % (jobId, lastKnownState))
		
		
		jobInfo = self._getClient().getJobInfo(int(jobId))
		if jobInfo:
			getLogger().debug("Got job info for %s: %s" % (jobId, jobInfo))
		else:
			getLogger().debug("job %s does not exist, not monitoring" % jobId)
			return None # non-existent job

		if jobInfo['state'] != lastKnownState:
			getLogger().debug("job %s state changed from %s to %s between two calls, not monitoring" % (jobId, lastKnownState, jobInfo["state"]))
			return jobInfo

		# finished ? no need to wait for a change
		if jobInfo['state'] in ['complete', 'cancelled', 'killed', 'error']:
			getLogger().debug("job %s is already over, not monitoring" % (jobId))
			return jobInfo
		
		# Otherwise, let's subscribe and wait for a change.
		event = threading.Event()
		def onNotification(notification):
			uri = notification.getUri()
			if notification.getMethod() == "JOB-EVENT":
				getLogger().debug("new job event received for job %s" % (jobId))
				jobInfo = notification.getApplicationBody()
				event.set()
		
		uri = "job:%s" % jobId
		getLogger().debug("subscribed to job events for job %s" % (jobId))
		self._getClient().subscribe(uri, onNotification)
		# timeout, let's force the source to poll each x seconds
		event.wait(TIMEOUT_GET_JOB_STATUS)
		self._getClient().unsubscribe(uri, onNotification)
		return jobInfo
	
			
	def monitor(self, jobInfo):
		jobId = jobInfo['id']
		state = jobInfo['state']
		uri = "job:%s" % jobId
		if state in ['waiting', 'running', 'cancelling']:
			if not jobId in self._queues:
				self._getClient().subscribe(uri, self.onNotification)
				self._queues[uri] = self.EventQueue(jobInfo)
		else:
			# Nothing to do, already stopped
			pass
	
	def onNotification(self, notification):
		uri = notification.getUri()
		if notification.getMethod() == "LOG":
			if uri in self._queues:
				self._queues.enqueue(notification.getBody())
		elif notification.getMethod() == "JOB-EVENT":
			if uri in self._queues:
				state = notification.getApplicationBody()['state']
				if not state in ['waiting', 'running', 'cancelling']:
					self._getClient().unsubscribe(uri, self.onNotification)
					self._queues[uri].setStopped()
	
	def garbageCollection(self):
		"""
		To be called regularly.
		"""
		timeout = 60
		toPurge = []
		for uri, queue in self._queues.items():
			if queue.isStopped() and queue.getLastUpdate() < (time.time() - timeout):
				# Let's purge the queue entrie
				toPurge.append(uri)
		
		for uri in toPurge:
			del self._queues[uri]
	
	def getEvents(self, jobId, startingFromId = 0):
		MAX_EVENTS = 100
		uri = "job:%s" % jobId
		if uri in self._queues:
			q = self._queues[uri]
			return zip(xrange(MAX_EVENTS), q._queue[startingFromId:])
		return []

############################################################
# The HTTP Server
############################################################

class RequestHandler(WebServer.WebApplicationDispatcherMixIn, BaseHTTPServer.BaseHTTPRequestHandler):
	# Temporary stuff: make connection read unbuffered (for websocket support)
	rbufsize = 0
	# and write buffered for explicit flush()
	wbufsize = -1
	# Disable logging DNS lookups
	def address_string(self):
		return str(self.client_address[0])	

class HttpServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	allow_reuse_address = True
	def handle_request_with_timeout(self, timeout):
		"""
		A handle_request reimplementation, with a timeout support
		so that we can interrupt the server easily.
		"""
		r, w, e = select.select([self.socket], [], [], timeout)
		if r:
			self.handle_request()

class HttpServerThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self._stopEvent = threading.Event()
		address = (cm.get("interface.wc.ip"), cm.get("interface.wc.port"))
		serverUrl = "http://%s:%s" % (cm.get("ts.ip"), cm.get("ts.port"))
		client = TestermanClient.Client(name = "Testerman WebClient", userAgent = "WebClient/%s" % VERSION, serverUrl = serverUrl)
		self._client = client
		RequestHandler.registerApplication('/', WebClientApplication, 
			documentRoot = cm.get("testerman.webclient.document_root"), 
			testermanClient = client,
			debug = cm.get("wcs.debug"),
			authenticationRealm = 'Testerman WebClient',
			theme = cm.get("wcs.webui.theme"))
		RequestHandler.registerApplication('/websocket', XcApplication, 
			testermanServerUrl = serverUrl,
			debug = cm.get("wcs.debug"))

		self._server = HttpServer(address, RequestHandler)

	def run(self):
		self._client.startXc()
		getLogger().info("Testerman Client Xc interface started")
		getLogger().info("HTTP server started")
		try:
			while not self._stopEvent.isSet(): 
				self._server.handle_request_with_timeout(0.01)
		except Exception, e:
			getLogger().error("Exception in HTTP server thread: " + str(e))
		getLogger().info("HTTP server stopped")
		self._client.stopXc()
		
	def stop(self):
		try:
			self._stopEvent.set()
			self.join()
		except Exception, e:
			getLogger().error("Unable to stop HTTP server gracefully: %s" % str(e))

################################################################################
# Testerman WebClient Server: Main
################################################################################

def getVersion():
	ret = "Testerman WebClient Server %s" % VERSION
	return ret

def main():
	server_root = os.path.abspath(os.path.dirname(sys.modules[globals()['__name__']].__file__))
	testerman_home = os.path.abspath("%s/.." % server_root)
	# Set transient values
	cm.set_transient("testerman.testerman_home", testerman_home)
	cm.set_transient("wcs.server_root", server_root)


	# Register persistent variables
	expandPath = lambda x: x and os.path.abspath(os.path.expandvars(os.path.expanduser(x)))
	splitPaths = lambda paths: [ expandPath(x) for x in paths.split(',')]
	cm.register("interface.wc.ip", "0.0.0.0")
	cm.register("interface.wc.port", 8888)
	cm.register("ts.ip", "127.0.0.1")
	cm.register("ts.port", 8080)
	cm.register("wcs.daemonize", False)
	cm.register("wcs.debug", False)
	cm.register("wcs.log_filename", "")
	cm.register("wcs.pid_filename", "")
	cm.register("testerman.var_root", "", xform = expandPath)
	cm.register("testerman.webclient.document_root", "%s/webclient" % testerman_home, xform = expandPath, dynamic = False)
	cm.register("testerman.administrator.name", "administrator", dynamic = True)
	cm.register("testerman.administrator.email", "testerman-admin@localhost", dynamic = True)
	cm.register("wcs.webui.theme", "default", dynamic = True)


	parser = optparse.OptionParser(version = getVersion())

	group = optparse.OptionGroup(parser, "Basic Options")
	group.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug traces on")
	group.add_option("-d", dest = "daemonize", action = "store_true", help = "daemonize")
	group.add_option("-r", dest = "docRoot", metavar = "PATH", help = "use PATH as document root (default: %s)" % cm.get("testerman.document_root"))
	group.add_option("--log-filename", dest = "logFilename", metavar = "FILENAME", help = "write logs to FILENAME instead of stdout")
	group.add_option("--pid-filename", dest = "pidFilename", metavar = "FILENAME", help = "write the process PID to FILENAME when daemonizing (default: no pidfile)")
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "IPs and Ports Options")
	group.add_option("--wc-ip", dest = "wcIp", metavar = "ADDRESS", help = "set listening Wc IP address to ADDRESS (default: listening on all interfaces)")
	group.add_option("--wc-port", dest = "wcPort", metavar = "PORT", help = "set listening Wc port to PORT (default: %s)" % cm.get("interface.wc.port"), type = "int")
	group.add_option("--ts-ip", dest = "tsIp", metavar = "ADDRESS", help = "set TS Ws target IP address to ADDRESS (default: %s)" % cm.get("ts.ip"))
	group.add_option("--ts-port", dest = "tsPort", metavar = "PORT", help = "set TS Ws target port address to PORT (default: %s)" % cm.get("ts.port"), type = "int")
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "Advanced Options")
	group.add_option("-V", dest = "varDir", metavar = "PATH", help = "use PATH to persist Testerman Server runtime variables, such as the job queue. If not provided, no persistence occurs between restarts.")
	group.add_option("-C", "--conf-file", dest = "configurationFile", metavar = "FILENAME", help = "path to a configuration file. You may still use the command line options to override the values it contains.")
	group.add_option("-U", "--users-file", dest = "usersFile", metavar = "FILENAME", help = "path to the configuration file that contains authorized webclient users.")
	group.add_option("--var", dest = "variables", metavar = "VARS", help = "set additional variables as VARS (format: key=value[,key=value]*)")
	parser.add_option_group(group)

	(options, args) = parser.parse_args()


	# Configuration 
	
	# Read the settings from the saved configuration, if any
	configFile = None
	# Provided on the command line ?
	if options.configurationFile is not None:
		configFile = options.configurationFile
	# No config file provided - fallback to $TESTERMAN_HOME/conf/testerman.conf if set and exists
	elif Tools.fileExists("%s/conf/testerman.conf" % testerman_home):
		configFile = "%s/conf/testerman.conf" % testerman_home
	
	cm.set_transient("wcs.configuration_filename", configFile)

	# Read the settings from the saved configuration, if any
	usersFile = None
	# Provided on the command line ?
	if options.usersFile is not None:
		usersFile = options.configurationFile
	# No config file provided - fallback to $TESTERMAN_HOME/conf/webclient-users.conf if set and exists
	elif Tools.fileExists("%s/conf/webclient-users.conf" % testerman_home):
		usersFile = "%s/conf/webclient-users.conf" % testerman_home
	
	cm.set_transient("wcs.users_filename", usersFile)

	try:
		if configFile: cm.read(configFile)
		if usersFile: cm.read(usersFile, autoRegister = True)
	except Exception, e:
		print str(e)
		return 1


	# Now, override read settings with those set on explicit command line flags
	# (or their default values inherited from the ConfigManager default values)
	cm.set_user("interface.wc.ip", options.wcIp)
	cm.set_user("interface.wc.port", options.wcPort)
	cm.set_user("ts.ip", options.tsIp)
	cm.set_user("ts.port", options.tsPort)
	cm.set_user("wcs.daemonize", options.daemonize)
	cm.set_user("wcs.debug", options.debug)
	cm.set_user("wcs.log_filename", options.logFilename)
	cm.set_user("wcs.pid_filename", options.pidFilename)
	cm.set_user("testerman.var_root", options.varDir)
	if options.variables:
		for var in options.variables.split(','):
			try:
				(key, val) = var.split('=')
				cm.set_user(key, val)
			except:
				pass

	# Commit all provided values (construct actual values via registered xforms)
	cm.commit()

	# Compute/adjust actual variables where applies

	# If an explicit pid file was provided, use it. Otherwise, fallback to the var_root/ts.pid if possible.
	pidfile = cm.get("wcs.pid_filename")
	if not pidfile and cm.get("testerman.var_root"):
		# Set an actual value
		pidfile = cm.get("testerman.var_root") + "/wcs.pid"
		cm.set_actual("wcs.pid_filename", pidfile)

#	print Tools.formatTable([ ('key', 'Name'), ('format', 'Type'), ('dynamic', 'Dynamic'), ('default', 'Default value'), ('user', 'User value'), ('actual', 'Actual value')], cm.getVariables(), order = "key")

	# Logger initialization
	if cm.get("wcs.debug"):
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', filename = cm.get("ts.log_filename"))

	# Display startup info
	getLogger().info("Starting WebClient Server %s" % (VERSION))
	getLogger().info("WebClient         (Wc) listening on tcp://%s:%s" % (cm.get("interface.wc.ip"), cm.get("interface.wc.port")))
	getLogger().info("Using TS at tcp://%s:%s" % (cm.get("ts.ip"), cm.get("ts.port")))
	items = cm.getKeys()
	items.sort()
	for k in items:
		getLogger().info("Using %s = %s" % (str(k), cm.get(k)))

	# Now we can daemonize if needed
	if cm.get("wcs.daemonize"):
		if pidfile:
			getLogger().info("Daemonizing, using pid file %s..." % pidfile)
		else:
			getLogger().info("Daemonizing...")
		Tools.daemonize(pidFilename = pidfile, displayPid = True)


	# Main start
	cm.set_transient("wcs.pid", os.getpid())
	try:
		serverThread =HttpServerThread() # Ws server
		serverThread.start()
		getLogger().info("Started.")
		while 1:
			time.sleep(1)
	except KeyboardInterrupt:
		getLogger().info("Shutting down WebClient Server...")
	except Exception, e:
		sys.stderr.write("Unable to start server: %s\n" % str(e))
		getLogger().critical("Unable to start server: " + str(e))

	serverThread.stop()
	getLogger().info("Shut down.")
	logging.shutdown()
	Tools.cleanup(cm.get("wcs.pid_filename"))

if __name__ == "__main__":
	main()
