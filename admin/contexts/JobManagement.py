# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2010 Sebastien Lefevre and other contributors
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
# Job management context for testerman-admin.
#
##


import TestermanClient

import os
import time

##
# Context definition
##

from CiscoInteractiveShell import *

class JobContext(CommandContext):
	"""
	This context is basically a wrapper over administration-oriented functions on TestermanClient.
	"""
	def __init__(self):
		CommandContext.__init__(self)
		self._client = None
		# list jobs
		node = SequenceNode()
		states = ChoiceNode()
		states.addChoice("running", "running jobs only")
		states.addChoice("waiting", "scheduled but not started jobs only")
		states.addChoice("paused", "paused jobs only")
		states.addChoice("cancelled", "cancelled jobs only")
		states.addChoice("killed", "killed jobs only")
		states.addChoice("completed", "successfully completed jobs only")
		states.addChoice("error", "error jobs only")
		node.addField("state", "filter on state", states, optional = True)
		node.addField("username", "filter on username", StringNode(), optional = True)
		self.addCommand("list", "list registered jobs", node, self.listJobs)

		# send a signal
		node = SequenceNode()
		signals = ChoiceNode()
		signals.addChoice("kill", "kill the job")
		signals.addChoice("pause", "pause a running job")
		signals.addChoice("resume", "resume a paused job")
		signals.addChoice("cancel", "gracefully stop the job")
		node.addField("signal", "signal to send", signals)
		node.addField("job", "the job id", IntegerNode())
		self.addCommand("send", "send a signal to a job", node, self.sendSignal)

		# Monitor a job
		node = SequenceNode()
		node.addField("job", "the job id of the job to monitor", IntegerNode())
		self.addCommand("monitor", "monitor a job", node, self.monitorJob)

	def _getClient(self):
		if not self._client:
			serverUrl = os.environ.get('TESTERMAN_SERVER')
			if not serverUrl:
				raise Exception("Sorry, no testerman server set (TESTERMAN_SERVER).")
			self._client = TestermanClient.Client(name = "Testerman Admin", userAgent = "testerman-admin", serverUrl = serverUrl)

		return self._client

	def monitorJob(self, job):
		"""
		Monitors, in real time, an uri, displaying:
		- LOG events as a very simple log line,
		- JOB-EVENT state change only
		
		Other events are not displayed.
		
		Only returns on user interruption.
		"""
		self.notify("Press Ctrl+C to stop monitoring.")
		def _onNotification(notification):
			if notification.getMethod() == "LOG":
				self.notify("%s | %s\n%s" % (str(notification.getUri()), notification.getHeader('Log-Class'), notification.getBody()))
			elif notification.getMethod() == "JOB-EVENT":
				state = notification.getApplicationBody()['state']
				result = notification.getApplicationBody()['result']
				id_ = notification.getApplicationBody()['id']
				self.notify("%s | state changed to %s" % (str(notification.getUri()), state))

		uri = "job:%s" % job
		self._getClient().startXc()
		try:
			self._getClient().subscribe(uri, _onNotification)
			while 1:
				time.sleep(1)
		except KeyboardInterrupt:
			self._getClient().unsubscribe(uri, _onNotification)
			self._getClient().stopXc()
		except Exception:
			self._getClient().unsubscribe(uri, _onNotification)
			self._getClient().stopXc()
		
	def sendSignal(self, job, signal):
		"""
		Sends a signal to a job.
		"""
		signal = signal[0]
		self.notify("Sending signal %s to %s..." % (signal, job))
		self._getClient().sendSignal(job, signal)

	def listJobs(self, state = None, username = None):
		rows = self._getClient().getJobQueue()
		headers = [('id', 'job id'), ('state', 'state'), ('name', 'name'), 
			('type', 'type'), ('username', 'username'), 
			('start-time', 'start', lambda x: x and time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x)) or 'n/a'),
			('stop-time', 'stop', lambda x: x and time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x)) or 'n/a'),
			('scheduled-at', 'scheduled', lambda x: x and time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x)) or ''),
		]
		if state:
			rows = [ x for x in rows if x['state'] == state[0] ]
		if username:
			rows = [ x for x in rows if x['username'] == username ]
		self.printTable(headers, rows)

