#!/usr/bin/env python
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
# A command-line interface testerman minimal client.
#
# Suitable for test execution from a higher-level script or 
# continuous integration system.
#
# $Id$
##

import TestermanClient

import optparse
import os
import sys
import threading
import time
import logging


VERSION = "0.0.1"


def getVersion():
	return "Testerman Minimal CLI Client %s" % VERSION

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


class TestermanCliClient:
	def __init__(self, serverUrl):
		self.__client = TestermanClient.Client(name = "Testerman CLI Client", userAgent = getVersion(), serverUrl = serverUrl)
		self.__jobCompleteEvent = threading.Event()
		self.__client.setLogger(logging.getLogger('cli'))
	
	def log(self, txt):
		logging.getLogger('cli').info(txt)

	def startXc(self):
		self.__client.startXc()
	
	def stopXc(self):
		self.__client.stopXc()	

	##
	# High level functions
	##
	
	def scheduleAts(self, atsFilename, username, parameterFilename = None, sessionFilename = None, at = None):
		"""
		Returns one scheduled.
		"""

		# Load the file
		try:
			f = open(atsFilename)
			ats = f.read()
			f.close()
		except Exception, e:
			err = "Error: unable to read ATS file %s (%s)" % (atsFilename, str(e))
			self.log(err)
			return err
		
		# TODO: parameter and sessionFilename read
		
		# Prepare Ws.scheduleAts() parameters
		self.log("Scheduling ATS...")
		atsId = atsFilename.split('/')[-1].replace(' ', '.')
		user = "cliclient-user"
		session = {} # for now

		# Schedule the ATS		
		ret = self.__client.scheduleAts(ats, atsId, user, session, at)
		jobId = ret['job-id']
		header = [ ('job-id', 'job-id'), ('message', 'message') ]
		print prettyPrintDictList(header, [ ret ])
		
		return jobId
	
	def listRegisteredProbes(self):
		ret = self.__client.getRegisteredProbes()
		header = [ ('name', 'name'), ('type', 'type'), ('contact', 'location') ]
		print prettyPrintDictList(header, ret)

	def monitor(self, uri):
		try:
			self.__client.subscribe(uri, self.onNotification)
		except KeyboardInterrupt:
			self.__client.unsubscribe(uri, self.onNotification)

	def onNotification(self, notification, jobId = None):
		if notification.getMethod() == "LOG":
			self.log("%s | %s\n%s" % (str(notification.getUri()), notification.getHeader('Log-Class'), notification.getBody()))
		elif notification.getMethod() == "JOB-EVENT":
			state = notification.getApplicationBody()['state']
			result = notification.getApplicationBody()['result']
			id_ = notification.getApplicationBody()['id']
			self.log("%s | state changed to %s" % (str(notification.getUri()), state))
			if jobId and str(jobId) == str(id_) and result is not None:
				self.__jobCompleteEvent.set()
				self.__jobCompleteResult = notification.getApplicationBody()['result']

	def monitorUntilCompletion(self, jobId):
		self.__jobCompleteEvent.clear()
		onJobNotification = lambda x: self.onNotification(x, jobId)
		self.__client.subscribe("job:%s" % jobId, onJobNotification)
		while not self.__jobCompleteEvent.isSet():
			time.sleep(0.1)
		self.__client.unsubscribe("job:%s" % jobId, onJobNotification)
		return self.__jobCompleteResult

	def sendSignal(self, jobId, signal):
		print "Sending signal %s to %s..." % (signal, jobId)
		self.__client.sendSignal(jobId, signal)

	def deployProbe(self, agentName, probeName, probeType):
		print "Deploying probe..."
		ret = self.__client.deployProbe(agentName, probeName, probeType)
		print str(ret)

	def undeployProbe(self, agentName, probeName):
		print "Undeploying probe..."
		ret = self.__client.undeployProbe(agentName, probeName)
		print str(ret)


def main():
	parser = optparse.OptionParser(version = getVersion())
	parser.add_option("--debug", dest = "debug", action = "store_true", help = "turn debug mode on (default: %default)", default = False)
	parser.add_option("--log-filename", dest = "logFilename", metavar = "FILE", help = "set log filename to FILE (default: none used)", default = None)
	parser.add_option("-s", "--server", dest = "serverUrl", metavar = "URL", help = "use URL as Testerman serverURL (default: %default)", default = os.environ.get('TESTERMAN_SERVER', None) or "http://localhost:8080")
	parser.add_option("-u", "--username", dest = "username", metavar = "USERNAME", help = "use USERNAME as Testerman user (default: %default)", default = os.environ.get('LOGNAME', None))

	# Actions
	parser.add_option("--execute-ats", dest = "atsFilename", metavar = "FILENAME", help = "execute ATS FILENAME, monitor it and wait for its completion", default = None)
	parser.add_option("--nowait", dest = "waitForAtsCompletion", action = "store_false", help = "when executing an ATS, immediately returns without waiting for its completion (default: false)", default = True)

	parser.add_option("--monitor", dest = "monitorUri", metavar = "URI", help = "monitor events on URI", default = None)

	parser.add_option("--deploy", dest = "deployProbeName", metavar = "NAME", help = "deploy a probe named NAME", default = None)
	parser.add_option("--undeploy", dest = "undeployProbeName", metavar = "NAME", help = "undeploy a probe named NAME", default = None)
	parser.add_option("--agent", dest = "deployAgentName", metavar = "NAME", help = "on agent named NAME", default = None)
	parser.add_option("--type", dest = "deployProbeType", metavar = "TYPE", help = "with type TYPE (deploy only)", default = None)
	

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
		if options.atsFilename:
			client.startXc()
			jobId = client.scheduleAts(options.atsFilename, options.username)
			if jobId:
				result = None
			else:
				result = 1
			if options.waitForAtsCompletion:
				if jobId:
					try:
						result = client.monitorUntilCompletion(str(jobId))
					except KeyboardInterrupt:
						result = 1
			client.stopXc()
			return result

		elif options.listProbes:
			client.listRegisteredProbes()
		
		elif options.monitorUri:
			client.startXc()
			client.monitor(options.monitorUri)
			client.stopXc()
		
		elif options.sendSignal and options.jobId:
			client.sendSignal(options.jobId, options.sendSignal)
		
		elif options.deployProbeName and options.deployProbeType and options.deployAgentName:
			client.deployProbe(options.deployAgentName, options.deployProbeName, options.deployProbeType)

		elif options.undeployProbeName and options.deployAgentName:
			client.undeployProbe(options.deployAgentName, options.undeployProbeName)
			
	except Exception, e:
		print str(e)
		return 1
	


if __name__ == "__main__":
	sys.exit(main())

	
	
		
	
