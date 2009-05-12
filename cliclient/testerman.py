#!/usr/bin/env python
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



VERSION = "0.2.0"

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
	
	def scheduleAtsByFilename(self, sourceFilename, username = None, session = {}, at = None):
		"""
		Reads an ATS file locally and schedule it.
		
		Returns the jobId once scheduled, or None in case of an error.
		"""
		# Load the file
		try:
			f = open(sourceFilename)
			source = f.read().decode('utf-8')
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
		# TODO: parameter and sessionFilename read
		
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
			source = f.read().decode('utf-8')
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
		# TODO: parameter and sessionFilename read
		
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
	
	def listRegisteredProbes(self):
		"""
		Displays the currently registered probes
		"""
		ret = self.__client.getRegisteredProbes()
		header = [ ('name', 'name'), ('type', 'type'), ('contact', 'location') ]
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


###############################################################################
# Main
###############################################################################

def getVersion():
	return "Testerman Minimal CLI Client %s" % VERSION

def main():
	parser = optparse.OptionParser(version = getVersion())
	parser.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug mode on (default: %default)", default = False)
	parser.add_option("--log-filename", dest = "logFilename", metavar = "FILE", help = "set log filename to FILE (default: none used)", default = None)
	parser.add_option("-s", "--server", dest = "serverUrl", metavar = "URL", help = "use URL as Testerman serverURL (default: %default)", default = os.environ.get('TESTERMAN_SERVER', None) or "http://localhost:8080")
	parser.add_option("-u", "--username", dest = "username", metavar = "USERNAME", help = "use USERNAME as Testerman user (default: %default)", default = os.environ.get('LOGNAME', None))

	# Actions
	parser.add_option("--run-local-ats", dest = "atsFilename", metavar = "FILENAME", help = "run FILENAME as an ATS, monitor it and wait for its completion", default = None)
	parser.add_option("--run-ats", dest = "atsPath", metavar = "PATH", help = "run an ATS whose path in the repository is PATH, monitor it and wait for its completion", default = None)
	parser.add_option("--run-local-campaign", dest = "campaignFilename", metavar = "FILENAME", help = "run FILENAME as a campaign, monitor it and wait for its completion", default = None)
	parser.add_option("--run-campaign", dest = "campaignPath", metavar = "PATH", help = "run a campaign whose path in the repository is PATH, monitor it and wait for its completion", default = None)
	parser.add_option("--nowait", dest = "waitForJobCompletion", action = "store_false", help = "when executing an ATS, immediately returns without waiting for its completion (default: false)", default = True)
	parser.add_option("--output-filename", dest = "outputFilename", metavar = "FILENAME", help = "if used with --run-* without the --nowait option, dump the execution logs into FILENAME once the execution is complete", default = None)
	parser.add_option("--session-filename", dest = "sessionParametersFilename", metavar = "FILENAME", help = "initial session parameters file", default = None)
	parser.add_option("--session-parameters", dest = "sessionParameters", metavar = "PARAMETERS", help = "initial session parameters, overriding those from form session-filename, if any", default = "")

	parser.add_option("--monitor", dest = "monitorUri", metavar = "URI", help = "monitor events on URI", default = None)

	parser.add_option("--get-log", dest = "logJobId", metavar = "ID", help = "get the current logs for job ID", default = None)
	parser.add_option("--expand-logs", dest = "expandLogs", action = "store_true", help = "expand include elements in retrieved log files", default = False)

	parser.add_option("--deploy", dest = "deployProbeName", metavar = "NAME", help = "deploy a probe named NAME", default = None)
	parser.add_option("--undeploy", dest = "undeployProbeName", metavar = "NAME", help = "undeploy a probe named NAME", default = None)
	parser.add_option("--agent", dest = "deployAgentName", metavar = "NAME", help = "on agent named NAME", default = None)
	parser.add_option("--type", dest = "deployProbeType", metavar = "TYPE", help = "with type TYPE (deploy only)", default = None)

	parser.add_option("--restart-agent", dest = "restartAgentName", metavar = "NAME", help = "restart agent named NAME", default = None)
	parser.add_option("--update-agent", dest = "updateAgentName", metavar = "NAME", help = "update agent named NAME to the latest version in its branch", default = None)

	parser.add_option("--list-probes", dest = "listProbes", action = "store_true", help = "list registered probes", default = False)

	parser.add_option("--send-signal", dest = "sendSignal", metavar = "SIGNAL", help = "send SIGNAL to job ID", default = None)
	parser.add_option("-j", "--job-id", dest = "jobId", metavar = "ID", help = "job ID to send signals to, when using --send-signal", default = None)

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
		if options.atsFilename or options.atsPath or options.campaignFilename or options.campaignPath:
			# Load initial session parameters
			try:
				session = loadSessionParameters(options.sessionParametersFilename, options.sessionParameters)
			except Exception, e:
				print str(e)
				return RETCODE_EXECUTION_ERROR
		
			client.startXc()
			# First, schedule the ATS (either a local or a repository one)
			if options.atsFilename:
				jobId = client.scheduleAtsByFilename(options.atsFilename, options.username, session = session)
			elif options.atsPath:
				jobId = client.scheduleAtsByPath(options.atsPath, options.username, session = session)
			elif options.campaignFilename:
				jobId = client.scheduleCampaignByFilename(options.campaignFilename, options.username, session = session)
			else:
				jobId = client.scheduleCampaignByPath(options.campaignPath, options.username, session = session)
			if jobId is None:
				client.stopXc()
				return RETCODE_EXECUTION_ERROR
			
			# Now, if we are in synchronous execution, let's wait
			if options.waitForJobCompletion:
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

		elif options.listProbes:
			client.listRegisteredProbes()
		
		elif options.monitorUri:
			client.startXc()
			client.monitor(options.monitorUri)
			client.stopXc()
		
		elif options.logJobId:
			log = client.getLog(int(options.logJobId), options.expandLogs)
			if log:
				print log
				return 0
			else:
				return 1
		
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

	
	
		
	
