#!/usr/bin/env python
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
# A command-line interface testerman minimal client.
#
# Suitable for test execution from a higher-level script or 
# continuous integration system.
#
##

import TestermanClient

import optparse
import os
import sys
import re
import threading
import time
import logging
import urlparse



VERSION = "1.4.0"

# Returned in case of a job submission-related execution error
RETCODE_EXECUTION_ERROR = 70

###############################################################################
# Some utilities
###############################################################################

def log(txt):
	logging.getLogger('cli').info(txt)

def prettyPrintDictList(header = [], distList = []):
	"""
	Pretty display the list of dict according to the header list.
	Header names not found in the dict are not displayed, and
	only header names found in the dict are displayed.
	
	Header is a list of either simple string (name) or tuple (name, label).
	If it is a tuple, label is used to display the header, and name
	to look for the element in the dicts.
	"""
	def formatLine(cols, widths):
		"""
		Formatting helper: array pretty print.
		"""
		line = "%s%s " % (cols[0], (widths[0]-len(cols[0]))*' ')
		for i in range(1, len(cols)):
			line = line + "| %s%s " % (cols[i], (widths[i]-len(cols[i]))*' ')
		return line

	# First, we compute the max widths for each col
	displayableHeader = []
	width = []
	for h in header:
		try:
			name, label = h
		except:
			label = h
		width.append(len(label))
		displayableHeader.append(label)

	lines = [ ]
	for entry in distList:
		i = 0
		line = []
		for h in header:
			try:
				name, label = h
			except:
				name = h
			if entry.has_key(name):
				e = str(entry[name])
				if len(e) > width[i]: width[i] = len(e)
				line.append(e)
			else:
				line.append('') # element not found for this dict entry
			i += 1
		lines.append(line)

	# Then we can display them
	res = formatLine(displayableHeader, width)
	res +="\n" + '-'*len(res) + "\n"
	for line in lines:
		res += formatLine(line, width) + "\n"
	return res

def loadSessionParameters(filename = None, parameters = ''):
	"""
	Creates the initial session parameters from a file 
	containing key=value (utf-8, # to comment),
	optionally overriding parameters from parameters
	(key=value[,key=value]*)
	
	@rtype: dict[unicode] of unicode
	@returns: the loaded initial session parameters
	"""
	values = {}
	
	# Load from the file
	if filename:
		try:
			f = open(filename)
			for l in f.readlines():
				m = re.match(r'\s*(?P<key>[^#].*)=(?P<value>.*)', l.strip())
				if m:
					values[m.group('key').decode('utf-8')] = m.group('value').decode('utf-8')
			f.close()
		except Exception, e:
			raise Exception("Unable to read parameters from file '%s' (%s)" % (filename, str(e)))

	# Now parse the parameters
	# We support a ',' as a value
	# (for instance: a=b,c=d,e,f=g)
	if parameters:
		splitParameters = parameters.split(',')
		parameters = []
		i = 0
		try:
			while i < len(splitParameters):
				if '=' in splitParameters[i]:
					parameters.append(splitParameters[i])
				else:
					parameters[-1] = parameters[-1] + ',' + splitParameters[i]
				i += 1

			for key, value in map(lambda x: x.split('=', 1), parameters):
				values[key.decode('utf-8')] = value.decode('utf-8')
		except Exception, e:
			raise Exception('Invalid parameters format (%s)' % str(e)) 
	
	return values


###############################################################################
# Log Expander
###############################################################################

class LogExpander:
	"""
	A Raw log saver that follows include directives
	to expand the logs inline.
	
	Based on *string* parsing, not XML parsing, 
	and assumes that <include> elements are on a single line.
	"""
	def __init__(self, client):
		self._client = client

	def expand(self, rawLogs):
		return '\n'.join(self._expand(rawLogs))
	
	def _expand(self, rawLogs):
		ret = []

		for line in rawLogs.split('\n'):
			if not line.startswith('<include '):
				ret.append(line)
			else:
				m = re.match(r'\<include (?P<prefix>.*)url="(?P<url>.*?)" (?P<suffix>.*)', line)
				if m:
					url = m.group('url')
					includedLogs = self.fetchUrl(url)
					if includedLogs is not None:
						ret += self._expand(includedLogs)
					else:
						# Warning
						log("Unable to fetch url '%s'..." % url)
		return ret

	def fetchUrl(self, url):
		log("Fetching included url '%s'..." % url)
		# extract path from url
		path = os.path.normpath(urlparse.urlparse(url).path)
		log("Fetching included path '%s'..." % path)
		return self._client.getFile(path)

###############################################################################
# Executable Source URI
###############################################################################

class SourceUri:
	TYPE_CAMPAIGN = 'campaign'
	TYPE_ATS = 'ats'
	TYPE_PACKAGE = 'package'

	def __init__(self, uri):
		self._scheme = None
		self._path = None # includes the extension
		self._type = None 
		self.parse(uri)
	
	def parse(self, uri):
		try:
			self._scheme, self._path = uri.split(':', 1)
		except Exception, e:
			raise Exception("Invalid source URI format (%s)" % uri)
		
		if self._path.endswith('.campaign'):
			self._type = self.TYPE_CAMPAIGN
		elif self._path.endswith('.ats'):
			self._type = self.TYPE_ATS
		elif self._path.endswith('.tpk'):
			self._type = self.TYPE_PACKAGE
		elif self.isRepository():
			self._type = self.TYPE_PACKAGE
		else:
			raise Exception("Unable to detect source URI type from file extension (%s)" % self._path)
		
	def isLocal(self):
		return self._scheme in ['local']
	
	def isRepository(self):
		return self._scheme in ['repository']
	
	def getPath(self):
		return self._path
	
	def getType(self):
		return self._type
	
	def __str__(self):
		return "%s:%s" % (self._scheme, self._path)
		

###############################################################################
# The CLI Client
###############################################################################

class TestermanCliClient:
	def __init__(self, serverUrl):
		self.__client = TestermanClient.Client(name = "Testerman CLI Client", userAgent = getVersion(), serverUrl = serverUrl)
		self.__jobCompleteEvent = threading.Event()
		self.__client.setLogger(logging.getLogger('cli'))
	
	def log(self, txt):
		log(txt)

	def startXc(self):
		self.__client.startXc()
	
	def stopXc(self):
		self.__client.stopXc()	

	##
	# High level functions
	##
	def scheduleJobByUri(self, uri, username = None, session = {}, at = None, hint = None, **kwargs):
		uri = SourceUri(uri)
		if hint:
			type_ = hint
		else:
			type_ = uri.getType()
		if uri.isLocal():
			if type_ == uri.TYPE_ATS:
				return self.scheduleAtsByFilename(uri.getPath(), username, session, at)
			elif type_ == uri.TYPE_CAMPAIGN:
				return self.scheduleCampaignByFilename(uri.getPath(), username, session, at)
			elif type_ == uri.TYPE_PACKAGE:
				return self.schedulePackageByFilename(uri.getPath(), username, session, at, kwargs.get('packageScript', None))
		elif uri.isRepository():
			if type_ == uri.TYPE_ATS:
				return self.scheduleAtsByPath(uri.getPath(), username, session, at)
			elif type_ == uri.TYPE_CAMPAIGN:
				return self.scheduleCampaignByPath(uri.getPath(), username, session, at)
			elif type_ == uri.TYPE_PACKAGE:
				return self.schedulePackageByPath(uri.getPath(), username, session, at, kwargs.get('packageScript', None))
		raise Exception("Unsupported URI scheme or job type (%s)" % uri)
	
	def scheduleAtsByFilename(self, sourceFilename, username = None, session = {}, at = None):
		"""
		Reads an ATS file locally and schedule it.
		
		Returns the jobId once scheduled, or None in case of an error.
		"""
		# Load the file
		try:
			f = open(sourceFilename)
			source = f.read()
			f.close()
		except Exception, e:
			err = "Error: unable to read ATS file %s (%s)" % (sourceFilename, str(e))
			self.log(err)
			return None

		label = sourceFilename.split('/')[-1].replace(' ', '.')
		if not username:
			username = "cliclient-user"
		return self._scheduleAts(source, label, username, session, at, path = None)		
	
	def scheduleAtsByPath(self, sourcePath, username = None, session = {}, at = None):
		"""
		Gets an ATS by path locally and schedule it.
		
		Returns the jobId once scheduled, or None in case of an error.
		"""
		# Load the file
		try:
			source = self.__client.getFile('/repository/%s' % sourcePath).decode('utf-8')
		except Exception, e:
			err = "Error: unable to get ATS from the server path %s." % (sourcePath)
			self.log(err)
			return None

		label = sourcePath.split('/')[-1].replace(' ', '.')
		if not username:
			username = "cliclient-user"

		# Reconstruct the server path
		path = '/'.join(('/repository/%s' % sourcePath).split('/')[:-1])
		return self._scheduleAts(source, label, username, session, at, path = path)		

	def _scheduleAts(self, source, label, username, session = {}, at = None, path = None):
		"""
		Schedule an ATS whose source is provided by source and returns its JobID once scheduled,
		or None in case of an error.
		"""
		# Prepare Ws.scheduleAts() parameters
		self.log("Scheduling ATS...")

		# Schedule the job		
		try:
			ret = self.__client.scheduleAts(source, label, username, session, at, path)
			jobId = ret['job-id']
			header = [ ('job-id', 'job-id'), ('message', 'message') ]
			self.log("Schedule ATS result: %s" % ret['message'])
			return jobId
		except Exception, e:
			self.log(str(e))
			return None

	def scheduleCampaignByFilename(self, sourceFilename, username = None, session = {}, at = None):
		"""
		Reads a Campaign file locally and schedules it.
		
		Returns the jobId once scheduled, or None in case of an error.
		"""
		# Load the file
		try:
			f = open(sourceFilename)
			source = f.read()
			f.close()
		except Exception, e:
			err = "Error: unable to read Campaign file %s (%s)" % (sourceFilename, str(e))
			self.log(err)
			return None

		label = sourceFilename.split('/')[-1].replace(' ', '.')
		if not username:
			username = "cliclient-user"
		return self._scheduleCampaign(source, label, username, session, at, path = None)		
	
	def scheduleCampaignByPath(self, sourcePath, username = None, session = {}, at = None):
		"""
		Gets a Campaign by path locally and schedules it.
		
		Returns the jobId once scheduled, or None in case of an error.
		"""
		# Load the file
		try:
			source = self.__client.getFile('/repository/%s' % sourcePath).decode('utf-8')
		except Exception, e:
			err = "Error: unable to get Campaign from the server path %s." % (sourcePath)
			self.log(err)
			return None

		label = sourcePath.split('/')[-1].replace(' ', '.')
		if not username:
			username = "cliclient-user"

		# Reconstruct the server path
		path = '/'.join(('/repository/%s' % sourcePath).split('/')[:-1])
		return self._scheduleCampaign(source, label, username, session, at, path = path)		

	def _scheduleCampaign(self, source, label, username, session = {}, at = None, path = None):
		"""
		Schedules a Campaign whose source is provided by source and returns its JobID once scheduled,
		or None in case of an error.
		"""
		# Prepare Ws.scheduleCampaign() parameters
		self.log("Scheduling Campaign...")

		# Schedule the ATS		
		try:
			ret = self.__client.scheduleCampaign(source, label, username, session, at, path)
			jobId = ret['job-id']
			header = [ ('job-id', 'job-id'), ('message', 'message') ]
			self.log("Schedule Campaign result:\n%s" % prettyPrintDictList(header, [ ret ]))
			return jobId
		except Exception, e:
			self.log(str(e))
			return None
	
	def schedulePackageByFilename(self, sourceFilename, username = None, session = {}, at = None, script = None, profileName = None):
		"""
		Imports a package to a temporary folder,
		executes it.
		
		Returns the jobId once scheduled, or None in case of an error.
		"""
		# Generate a temporary package name
		tmpPackagePath = "/tmp/%s-%s" % (time.time(), username) # a real random name is required.
		# Import the file
		self.log("Uploading %s to %s..." % (sourceFilename, tmpPackagePath))
		try:
			f = open(sourceFilename, 'r')
			contents = f.read()
			f.close()
			
			ret = self.__client.importPackageFile(contents, tmpPackagePath)
			if not ret:
				raise Exception("Unable to upload package (no error provided)")
			self.log("%s correctly uploaded to %s" % (sourceFilename, tmpPackagePath))
		except Exception, e:
			self.log("Sorry, unable to import package: %s" % str(e))

		# Execute it
		return self._schedulePackage(tmpPackagePath, username, session, at, script, profileName)
		# Normally remove the package once completed.
	
	def schedulePackageByPath(self, path, username = None, session = {}, at = None, script = None, profileName = None):
		return self._schedulePackage("/repository/%s" % path, username, session, at, script, profileName)

	def _schedulePackage(self, path, username, session = {}, at = None, script = None, profileName = None):
		"""
		Schedules a Campaign whose source is provided by source and returns its JobID once scheduled,
		or None in case of an error.
		"""
		self.log("Scheduling Package...")

		# Schedule the ATS		
		try:
			ret = self.__client.schedulePackage(path, username, session, at, script, profileName)
			jobId = ret['job-id']
			header = [ ('job-id', 'job-id'), ('message', 'message') ]
			self.log("Schedule Package result:\n%s" % prettyPrintDictList(header, [ ret ]))
			return jobId
		except Exception, e:
			self.log(str(e))
			return None

	def listRegisteredProbes(self):
		"""
		Displays the currently registered probes
		"""
		ret = self.__client.getRegisteredProbes() + self.__client.getRegisteredAgents()
		header = [ ('uri', 'uri'), ('type', 'type'), ('contact', 'location'), ('user-agent', 'version') ]
		print prettyPrintDictList(header, ret)

	def monitor(self, uri):
		"""
		Monitors, in real time, an uri, displaying:
		- LOG events as a very simple log line,
		- JOB-EVENT state change only
		
		Other events are not displayed.
		
		Only returns on user interruption.
		"""
		def _onNotification(notification):
			if notification.getMethod() == "LOG":
				self.log("%s | %s\n%s" % (str(notification.getUri()), notification.getHeader('Log-Class'), notification.getBody()))
			elif notification.getMethod() == "JOB-EVENT":
				state = notification.getApplicationBody()['state']
				result = notification.getApplicationBody()['result']
				id_ = notification.getApplicationBody()['id']
				self.log("%s | state changed to %s" % (str(notification.getUri()), state))

		try:
			self.__client.subscribe(uri, _onNotification)
		except KeyboardInterrupt:
			self.__client.unsubscribe(uri, _onNotification)

	def monitorUntilCompletion(self, jobId, delay = 5.0):
		"""
		Starts monitoring a job via Xc, and returns its result upon completion.
		
		In parallel, performs Ws status check for the job to be sure it is still
		running.
		This check is performed every delay seconds.
		"""
		def _onNotification(notification):
			if notification.getMethod() == "JOB-EVENT":
				state = notification.getApplicationBody()['state']
				result = notification.getApplicationBody()['result']
				id_ = notification.getApplicationBody()['id']
				self.log("%s | state changed to %s" % (str(notification.getUri()), state))
				if str(jobId) == str(id_) and result is not None:
					self.__jobCompleteEvent.set()
					self.__jobCompleteResult = notification.getApplicationBody()['result']

		previousTick = 0.0
		self.__jobCompleteResult = None
		self.__jobCompleteEvent.clear()
		self.__client.subscribe("job:%s" % jobId, _onNotification)
		self.log("Waiting for job completion...")
		while not self.__jobCompleteEvent.isSet():
			time.sleep(0.1)
			now = time.time()
			if now - previousTick > delay:
				# "Manual" check
				previousTick = now
				try:
					jobInfo = self.__client.getJobInfo(jobId)
					result = jobInfo['result']
					if result is not None:
						self.__jobCompleteResult = result
						self.__jobCompleteEvent.set()
				except Exception, e:
					self.log("Sorry, the job is not available on this server any more. Stopping monitoring (%s)" % str(e))
					return None
				
		self.__client.unsubscribe("job:%s" % jobId, _onNotification)
		return self.__jobCompleteResult

	def sendSignal(self, jobId, signal):
		"""
		Sends a signal to a job.
		"""
		print "Sending signal %s to %s..." % (signal, jobId)
		self.__client.sendSignal(jobId, signal)

	def deployProbe(self, agentName, probeName, probeType):
		"""
		Deploys a new probe probe:probeName@agentName
		"""
		print "Deploying probe..."
		ret = self.__client.deployProbe(agentName, probeName, probeType)
		print str(ret)

	def undeployProbe(self, agentName, probeName):
		"""
		Undeploys probe:probeName@agentName
		"""
		print "Undeploying probe..."
		ret = self.__client.undeployProbe(agentName, probeName)
		print str(ret)

	def restartAgent(self, agentName):
		"""
		Restarts the agent agent:agentName
		"""
		print "Restarting agent..."
		ret = self.__client.restartAgent(agentName)
		print str(ret)

	def updateAgent(self, agentName, branch = None, version = None):
		"""
		Requests the agent agent:agentName to update
		"""
		print "Updating agent..."
		ret = self.__client.updateAgent(agentName, branch, version)
		print str(ret)

	def getLog(self, jobId, expandLogs):
		"""
		Returns the current log for a job;
		expands include elements if expandLogs is set to True.
		"""
		try:
			ret = self.__client.getJobLog(jobId)
			if not ret:
				raise Exception("No log available (job not started or delete logs)")
		except Exception, e:
			self.log("Unable to get current log for job ID %s: %s\n" % (jobId, str(e)))
			return None
		
		if expandLogs:
			logExpander = LogExpander(self.__client)
			return logExpander.expand(ret)
		else:
			return ret

	def listDependencies(self, path, recursive = True):
		"""
		Prints the dependencies for a given file (module/ats/campaign)
		identified by path in the *repository*.
		"""
		print "Getting dependencies for %s..." % path
		ret = self.__client.getDependencies("/repository/%s" % path, recursive)
		print "File dependencies:"
		print "\n".join(ret)
	
	def extractPackage(self, path, filename):
		"""
		Extract/export a package from the repository.
		"""
		if not filename:
			print "Sorry, missing output filename"
			return
		
		print "Extracting %s to %s..." % (path, filename)
		try:
			contents = self.__client.exportPackage("/repository/%s" % path)
			if contents is None:
				raise Exception("Package %s not found" % path)
			f = open(filename, 'wb')
			f.write(contents)
			f.close()
			print "%s created." % filename
		except Exception, e:
			self.log("Sorry, unable to extract package: %s" % str(e))

	def importPackage(self, path, filename):
		"""
		Import the package filename to path
		"""
		if not filename:
			print "Sorry, missing input filename"
			return
		
		print "Importing %s to %s..." % (filename, path)
		try:
			f = open(filename, 'r')
			contents = f.read()
			f.close()
			
			ret = self.__client.importPackageFile(contents, "/repository/%s" % path)
			if not ret:
				raise Exception("Unable to import package (no error provided)")
			print "%s correctly imported as %s" % (filename, path)
		except Exception, e:
			self.log("Sorry, unable to import package: %s" % str(e))

###############################################################################
# Main
###############################################################################

def getVersion():
	return "Testerman CLI Client %s" % VERSION

def main():
	parser = optparse.OptionParser(version = getVersion())

	# General Options
	group = optparse.OptionGroup(parser, "General Options")
	group.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug mode on (default: %default)", default = False)
	group.add_option("--log-filename", dest = "logFilename", metavar = "FILE", help = "set log filename to FILE (default: none used)", default = None)
	group.add_option("-s", "--server", dest = "serverUrl", metavar = "URL", help = "use URL as Testerman serverURL (default: %default). You may set TESTERMAN_SERVER environment variable, too.", default = os.environ.get('TESTERMAN_SERVER', None) or "http://localhost:8080")
	group.add_option("-u", "--username", dest = "username", metavar = "USERNAME", help = "use USERNAME as Testerman user (default: %default)", default = os.environ.get('LOGNAME', None))
	group.add_option("--output-filename", "-o", dest = "outputFilename", metavar = "FILENAME", help = "the file to use for actions that require or may use an output file", default = None)
	group.add_option("--input-filename", "-i", dest = "inputFilename", metavar = "FILENAME", help = "the file to use for actions that require or may use an input file", default = None)
	parser.add_option_group(group)

	# Actions
	
	# Runners
	group = optparse.OptionGroup(parser, "Job Runners")
	group.add_option("--run", dest = "runUri", metavar = "URI", help = "run a ats/campaign/package, either local or from the repository, then monitor it and wait for its completion.\nThe URI format is: local:<path> or repository:<path>. The filename extension (.ats, .campaign, .tpk) indicates the job type.\nIf --output-filename is provided, dump the logs once the job is complete.", default = None)
	# Deprecated runners
	group.add_option("--run-local-ats", dest = "atsFilename", metavar = "FILENAME", help = "[DEPRECATED - use --run instead]\nrun FILENAME as an ATS, monitor it and wait for its completion", default = None)
	group.add_option("--run-ats", dest = "atsPath", metavar = "PATH", help = "[DEPRECATED - use --run instead]\nrun an ATS whose path in the repository is PATH, monitor it and wait for its completion", default = None)
	group.add_option("--run-local-campaign", dest = "campaignFilename", metavar = "FILENAME", help = "[DEPRECATED - use --run instead]\nrun FILENAME as a campaign, monitor it and wait for its completion", default = None)
	group.add_option("--run-campaign", dest = "campaignPath", metavar = "PATH", help = "[DEPRECATED - use --run instead]\nrun a campaign whose path in the repository is PATH, monitor it and wait for its completion", default = None)
	# Run options
	group.add_option("--at", dest = "scheduledDate", metavar = "YYYYMMDD-hhmm", help = "instead of an immediate run, schedule it to start at YYYYMMDD-hhmm (localtime). This implies --nowait.", default = None)
	group.add_option("--nowait", dest = "waitForJobCompletion", action = "store_false", help = "when executing an ATS, immediately return without waiting for its completion (default: false)", default = True)
	group.add_option("--session-filename", dest = "sessionParametersFilename", metavar = "FILENAME", help = "initial session parameters file", default = None)
	group.add_option("--session-parameters", dest = "sessionParameters", metavar = "PARAMETERS", help = "initial session parameters, overriding those from form session-filename, if any", default = "")
	group.add_option("--override-default-script", dest = "packageScriptName", metavar = "SCRIPTNAME", help = "when executing a package, override the default script provided in the package description, and run SCRIPTNAME instead. Must be a path relative to the src/ package folder.", default = None)
	parser.add_option_group(group)

	# Job runtime management
	group = optparse.OptionGroup(parser, "Job Runtime Management")
	group.add_option("--monitor", dest = "monitorUri", metavar = "URI", help = "monitor events on URI", default = None)
	group.add_option("--send-signal", dest = "sendSignal", metavar = "SIGNAL", help = "send SIGNAL to job ID", default = None)
	group.add_option("-j", "--job-id", dest = "jobId", metavar = "ID", help = "job ID to send signals to, when using --send-signal", default = None)
	parser.add_option_group(group)

	# Log management
	group = optparse.OptionGroup(parser, "Log Management")
	group.add_option("--get-log", dest = "logJobId", metavar = "ID", help = "get the current logs for job ID", default = None)
	group.add_option("--expand-logs", dest = "expandLogs", action = "store_true", help = "expand include elements in retrieved log files", default = False)
	parser.add_option_group(group)

	# Probe management
	group = optparse.OptionGroup(parser, "Probe Management")
	group.add_option("--list-probes", dest = "listProbes", action = "store_true", help = "list registered agents and probes", default = False)
	group.add_option("--deploy", dest = "deployProbeName", metavar = "NAME", help = "deploy a probe named NAME", default = None)
	group.add_option("--undeploy", dest = "undeployProbeName", metavar = "NAME", help = "undeploy a probe named NAME", default = None)
	group.add_option("--agent", dest = "deployAgentName", metavar = "NAME", help = "on agent named NAME", default = None)
	group.add_option("--type", dest = "deployProbeType", metavar = "TYPE", help = "with type TYPE (deploy only)", default = None)
	parser.add_option_group(group)

	# Agent management
	group = optparse.OptionGroup(parser, "Agent Management")
	group.add_option("--restart-agent", dest = "restartAgentName", metavar = "NAME", help = "restart the agent named NAME", default = None)
	group.add_option("--update-agent", dest = "updateAgentName", metavar = "NAME", help = "update the agent named NAME to the latest version in its branch", default = None)
	parser.add_option_group(group)

	# Package management
	group = optparse.OptionGroup(parser, "Package Management")
	group.add_option("--extract-package", dest = "extractPackage", metavar = "PATH", help = "extract the package whose repository path is PATH to a tpk file indicated with --output-filename", default = None)
	group.add_option("--import-package-to", dest = "importPackage", metavar = "PATH", help = "import the package provided by --input-filename to the repository path PATH", default = None)
	parser.add_option_group(group)

	# Misc
	group = optparse.OptionGroup(parser, "Misc Options")
	group.add_option("--list-dependencies", dest = "listDependencies", metavar = "PATH", help = "list the dependencies of the file whose repository path is PATH", default = None)
	parser.add_option_group(group)


	(options, args) = parser.parse_args()
	
	if not options.serverUrl:
		print "Error: missing server URL. You may use either -s, --server, or set the environment variable TESTERMAN_SERVER."
		sys.exit(1)
	
	# Logger initialization
	if options.debug:
		level = logging.DEBUG
	else:
		level = logging.INFO
	logging.basicConfig(level = level, format = '%(asctime)s.%(msecs)03d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', filename = options.logFilename)

	client = TestermanCliClient(options.serverUrl)
	
	
	try:
		# Run options
		
		if options.scheduledDate:
			try:
				options.scheduledDate = time.mktime(time.strptime(options.scheduledDate, '%Y%m%d-%H%M'))
			except:
				print "Invalid date/time format. Please see the inline documentation (--help)."
				return RETCODE_EXECUTION_ERROR

		if options.atsFilename or options.atsPath or options.campaignFilename or options.campaignPath or options.runUri:
			# Load initial session parameters
			try:
				session = loadSessionParameters(options.sessionParametersFilename, options.sessionParameters)
			except Exception, e:
				print str(e)
				return RETCODE_EXECUTION_ERROR
		
			client.startXc()
			
			# First, schedule the job
			if options.runUri:
				jobId = client.scheduleJobByUri(options.runUri, options.username, session = session, at = options.scheduledDate, packageScript = options.packageScriptName)
			# other way to schedule jobs kept for compatibility
			elif options.atsFilename:
				jobId = client.scheduleAtsByFilename(options.atsFilename, options.username, session = session, at = options.scheduledDate)
			elif options.atsPath:
				jobId = client.scheduleAtsByPath(options.atsPath, options.username, session = session, at = options.scheduledDate)
			elif options.campaignFilename:
				jobId = client.scheduleCampaignByFilename(options.campaignFilename, options.username, session = session, at = options.scheduledDate)
			else:
				jobId = client.scheduleCampaignByPath(options.campaignPath, options.username, session = session, at = options.scheduledDate)
			if jobId is None:
				client.stopXc()
				return RETCODE_EXECUTION_ERROR
			
			result = 0
			
			# Now, if we are in synchronous execution, let's wait
			if options.waitForJobCompletion and not options.scheduledDate:
				try:
					result = client.monitorUntilCompletion(jobId)
				except KeyboardInterrupt:
					client.stopXc()
					return RETCODE_EXECUTION_ERROR
				
				# Optionally, get the log and dump it to a file.
				if result is not None and options.outputFilename:
					try:
						log = client.getLog(jobId, options.expandLogs)
						f = open(options.outputFilename, 'w')
						f.write(log)
						f.close()
						client.log("Execution logs available in '%s'" % options.outputFilename)
					except Exception, e:
						client.log("Unable to dump execution logs to '%s': %s" % (options.outputFilename, str(e)))
						client.stopXc()
						return RETCODE_EXECUTION_ERROR
					
			client.stopXc()
			# If result == 40, no log available.
			return result


		# Log options
		elif options.logJobId:
			log = client.getLog(int(options.logJobId), options.expandLogs)
			if log:
				print log
				return 0
			else:
				return 1
		
		# Tools options
		elif options.listDependencies:
			client.listDependencies(options.listDependencies)
		
		elif options.extractPackage:
			client.extractPackage(options.extractPackage, options.outputFilename)

		elif options.importPackage:
			client.importPackage(options.importPackage, options.inputFilename)
		

		# Administrative options (now replaced by testerman-admin, but kept here for convenience and compatibility)
		elif options.listProbes:
			client.listRegisteredProbes()
		
		elif options.monitorUri:
			client.startXc()
			client.monitor(options.monitorUri)
			client.stopXc()
		
		elif options.sendSignal and options.jobId:
			client.sendSignal(int(options.jobId), options.sendSignal)
		
		elif options.deployProbeName and options.deployProbeType and options.deployAgentName:
			client.deployProbe(options.deployAgentName, options.deployProbeName, options.deployProbeType)

		elif options.undeployProbeName and options.deployAgentName:
			client.undeployProbe(options.deployAgentName, options.undeployProbeName)

		elif options.restartAgentName:
			client.restartAgent(options.restartAgentName)

		elif options.updateAgentName:
			client.updateAgent(options.updateAgentName)
		
		else:
			parser.print_help()
			
	except Exception, e:
		print str(e)
		return 1
	


if __name__ == "__main__":
	sys.exit(main())

	
	
		
	
