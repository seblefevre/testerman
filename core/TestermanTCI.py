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
# Logger module for Testerman.
# Implements a part of the TCI TTCN-3 standard interface:
# logging tli methods.
# Implemented as a client of the TL (Test Logger) module which
# is embedded into the Testerma Server as the EventManager.
#
#
# A log event contains a class, which is an "application-oriented" classification.
#
# It is also associated to a log level; log levels and classes are independent
# (even if their names ressemble each others).
# 
# Log levels are configurable from the userland. However, some levels cannot
# be deactivated ('core', 'action').
#
##

import TestermanMessages as Messages
import TestermanNodes as Nodes

import base64
import cgi
import sys
import time

# These global variables are set during the TE initialization,
# through initialize()
TheIlClient = None
MaxLogPayloadSize = 65535


################################################################################
# General purpose functions
################################################################################

def getBacktrace():
	"""
	Returns the current backtrace.
	"""
	import traceback
	import StringIO
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

################################################################################
# These functions are called by the Testerman TE execution stub (when
# an ATS is executed through the Testerman Server)
################################################################################

class IlClient(Nodes.ConnectingNode):
	def __init__(self, jobId, serverAddress, localAddress = ('', 0), logFilename = None):
		Nodes.ConnectingNode.__init__(self, "TE job:%s" % str(jobId), "TestermanTCI/IlClient")
		
		self.logFilename = logFilename
		self.jobId = jobId
		
		self.localAddress = localAddress
		self.initialize(serverAddress, self.localAddress)

	def sendLogNotification(self, logClass, xml):
		"""
		Creates a notification and send it to the EventManager/TL, through the Il interface.
		"""
		try:	
			notification = Messages.Notification("LOG", "job:%s" % self.jobId, "Il", "1.0")
			if self.logFilename:
				notification.setHeader("Log-Filename", self.logFilename)
			notification.setHeader("Log-Class", logClass)
			notification.setHeader("Log-Timestamp", time.time())
			notification.setHeader("Content-Encoding", "utf-8")
			notification.setHeader("Content-Type", "application/xml")
			notification.setBody(xml.encode('utf-8'))

			self.sendNotification(0, notification)
		except Exception:
			# Logging fallback to stderr
			print >> sys.stdout, "WARNING: unable to send LOG notification: " + getBacktrace()

def initialize(ilServerAddress, jobId, logFilename, maxPayloadSize = 65535):
	"""
	Sets module variables, starts connecting the IlClient to the TL subsystem.
	"""
	global TheIlClient
	global MaxLogPayloadSize

	MaxLogPayloadSize = maxPayloadSize

	TheIlClient = IlClient(jobId, serverAddress = ilServerAddress, logFilename = logFilename)
	TheIlClient.start()

def finalize():
	"""
	Finalizes the module: stops the Il Client.
	"""
	if TheIlClient:
		TheIlClient.stop()
		TheIlClient.finalize()


################################################################################
# Log level selection
################################################################################

ExcludedLogLevels = [ 'internal' ]

def setExcludedLogLevels(levels):
	# Cannot exclude some low-level levels
	global ExcludedLogLevels
	ExcludedLogLevels = filter(lambda x: not x in [ 'core', 'action' ], levels)

def getExcludedLogLevels():
	return ExcludedLogLevels

def enableDebugLogs():
	setExcludedLogLevels([])

def disableLogs():
	setExcludedLogLevels([ 'internal', 'system', 'event', 'user' ]) # 'action' is always enabled

def enableLogs():
	setExcludedLogLevels([ 'internal' ])


################################################################################
# TLI interface: main entry point for all logging.
# Implemented to redirect things to a TL-like module.
################################################################################

def toXml(element, attributes, value = ''):
	return u'<%s %s>%s</%s>' % (element, " ".join(map(lambda e: '%s="%s"' % (e[0], str(e[1])), attributes.items())), value, element)

def logAtsStarted(id_):
	tliLog('core', toXml('ats-started', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logAtsStopped(id_, result, message = ''):
	tliLog('core', toXml('ats-stopped', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'result': str(result) }, cgi.escape(message)))

def logUser(message, tc = None):
	if tc is None:
		tliLog('user', toXml('user', { 'class': 'user', 'timestamp': time.time() }, cgi.escape(message)))
	else:
		tliLog('user', toXml('user', { 'class': 'user', 'timestamp': time.time(), 'tc': tc }, cgi.escape(message)))

def logInternal(message):
	tliLog('internal', toXml('internal', { 'class': 'internal', 'timestamp': time.time() }, cgi.escape(message)))
	
def logMessageSent(fromTc, fromPort, toTc, toPort, message, address = None):
	if not address:
		address = ''
	try:
		tliLog('event', toXml('message-sent', { 'class': 'event', 'timestamp': time.time(), 'from-tc': fromTc, 'from-port': fromPort, 'to-tc': toTc, 'to-port': toPort }, '%s%s' % (testermanToXml(message, 'message'), testermanToXml(address, 'address'))))
	except Exception, e:
		ret = getBacktrace()
		logUser(unicode(e) + u'\n' + unicode(ret))

def logTestcaseCreated(id_):
	tliLog('core', toXml('testcase-created', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logTestcaseStarted(id_, title):
	tliLog('core', toXml('testcase-started', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }, cgi.escape(title)))

def logTestcaseStopped(id_, verdict, description):
	tliLog('core', toXml('testcase-stopped', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'verdict': verdict }, cgi.escape(description)))

def logTimerStarted(id_, tc, duration):
	tliLog('event', toXml('timer-started', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'duration': str(duration), 'tc': tc }))

def logTimerStopped(id_, tc, runningTime):
	tliLog('event', toXml('timer-stopped', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'running-time': str(runningTime), 'tc': tc }))

def logTimerExpiry(id_, tc):
	tliLog('event', toXml('timer-expiry', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'tc': tc }))

def logTestComponentCreated(id_):
	tliLog('event', toXml('tc-created', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logTestComponentStarted(id_, behaviour):
	tliLog('event', toXml('tc-started', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'behaviour': behaviour }))

def logTestComponentStopped(id_, verdict, message = ''):
	tliLog('event', toXml('tc-stopped', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'verdict': verdict }, cgi.escape(message)))

def logTestComponentKilled(id_, message = ''):
	tliLog('event', toXml('tc-killed', { 'class': 'event', 'timestamp': time.time(), 'id': id_, }, cgi.escape(message)))

def logVerdictUpdated(tc, verdict):
	tliLog('event', toXml('verdict-updated', { 'class': 'event', 'timestamp': time.time(), 'tc': tc, 'verdict': verdict }))

def logTemplateMatch(tc, port, message, template, encodedMessage = None):
	try:
		# Should we call a tliMatch/tliMisMatch ?
		if encodedMessage:
			tliLog('event', toXml('template-match', { 'class': 'event', 'timestamp': time.time(), 'tc': tc, 'port': port }, '%s%s%s' % (testermanToXml(message, 'message'), testermanToXml(template, 'template'), testermanToXml(encodedMessage, 'encoded-message'))))
		else:
			tliLog('event', toXml('template-match', { 'class': 'event', 'timestamp': time.time(), 'tc': tc, 'port': port }, '%s%s' % (testermanToXml(message, 'message'), testermanToXml(template, 'template'))))
	except Exception, e:
		ret = getBacktrace()
		logUser(unicode(e) + u'\n' + unicode(ret))

def logTemplateMismatch(tc, port, message, template, encodedMessage = None):
	try:
		# Should we call a tliMatch/tliMisMatch ?
		if encodedMessage:
			tliLog('event', toXml('template-mismatch', { 'class': 'event', 'timestamp': time.time(), 'tc': tc, 'port': port }, '%s%s%s' % (testermanToXml(message, 'message'), testermanToXml(template, 'template'), testermanToXml(encodedMessage, 'encoded-message'))))
		else:
			tliLog('event', toXml('template-mismatch', { 'class': 'event', 'timestamp': time.time(), 'tc': tc, 'port': port }, '%s%s' % (testermanToXml(message, 'message'), testermanToXml(template, 'template'))))
	except Exception, e:
		ret = getBacktrace()
		logUser(unicode(e) + u'\n' + unicode(ret))

def logTimeoutBranchSelected(id_):
	# in a alt, we selected a timer.TIMEOUT where the timer's id is id_
	tliLog('alt', toXml('timeout-branch', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logDoneBranchSelected(id_):
	# in a alt, we selected a tc.DONE where the tc's id is id_
	tliLog('alt', toXml('done-branch', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logKilledBranchSelected(id_):
	# in a alt, we selected a tc.KILLED where the tc's id is id_
	tliLog('alt', toXml('killed-branch', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logSystemSent(tsiPort, label, payload):
	tliLog('system', toXml('system-sent', { 'class': 'system', 'timestamp': time.time(), 'tsi-port': tsiPort }, '%s%s' % (testermanToXml(label, 'label'), testermanToXml(payload, 'payload'))))

def logSystemReceived(tsiPort, label, payload):
	tliLog('system', toXml('system-received', { 'class': 'system', 'timestamp': time.time(), 'tsi-port': tsiPort }, '%s%s' % (testermanToXml(label, 'label'), testermanToXml(payload, 'payload'))))

def logActionRequested(message, timeout, tc):
	tliLog('action', toXml('action-requested', { 'class': 'action', 'timestamp': time.time(), 'timeout': timeout, 'tc': tc }, '%s' % (testermanToXml(message, 'message'))))

def logActionCleared(reason, tc):
	tliLog('action', toXml('action-cleared', { 'class': 'action', 'timestamp': time.time(), 'tc': tc, 'reason': reason }))

def tliLog(level, xml):
	if not level in getExcludedLogLevels():
		# Fire a log event
		TheIlClient.sendLogNotification(level, xml)
	
################################################################################
# Main Testerman log format: XML serializer
################################################################################

"""
V2 log format:

|| TTCN-3 type || Testerman representation || XML representation ||
|| union       || Python couple ('choiceName', value) || <choice name="choiceName">value</choice> ||
|| record of/set of || Python list [value0, value1, ...] || <list><item>value0</item><item>value1</item></list> ||
|| record      || Python dict {'fieldName': value} || <record><field name="fieldName">value</field></record> ||

a XER-like encoding used to be used, but it was not possible to encode fancy field names in records, such as "COUNT(*)", "1.2.5423.12.19", etc.

Octetstrings are encoded in base64, and the element that contains it gets an additional encoding="base64" attribute.

"""

def testermanToXml(obj, element):
	"""
	Serializes a Testerman structure to an XML representation in an element named element
	
	Valid structures are:
	- simple types (strings, buffers, numerics, boolean)
	- lists of valid structures
	- dict[string] of valid structures,
	- couple (string, valid structure)
	
	@type  obj: python object
	@param obj: the structure to serialize
	@type  element: string
	@param element: the name of the element to build.

	@rtype: unicode
	@returns: the XML encoded string representing the structure.
	          Notice that no character encoding is applied (unicode).
	"""
	(value, encoding) = _testermanToXml(obj)
	if encoding:
		return u'<%s encoding="%s">%s</%s>' % (element, encoding, value, element)
	else:
		return u'<%s>%s</%s>' % (element, value, element)

def _testermanToXml(obj):
	"""
	@rtype: (unicode, string)
	@returns: a tuple (data, encoding), encoding is None if none was applied.
	"""
	# Tries to apply the 'to message' transformation (useful for template proxies)
	try:
		obj = obj.toMessage()
	except:
		pass
	
	if isinstance(obj, list):
		# The internally working object is a list - faster than a string for concat ops.
		ret = [ '<l>' ]
		for item in obj:
			ret.append(testermanToXml(item, 'i'))
		ret.append('</l>')
		return (u''.join(ret), None)
	
	if isinstance(obj, tuple):
		if not len(obj) == 2:
			# Invalid "choice" representation.
			return ('', None)

		(choiceName, choiceValue) = obj
		(value, encoding) = _testermanToXml(choiceValue)
		if encoding:
			ret = u'<c n="%s" encoding="%s">%s</c>' % (convertToAttribute(choiceName), encoding, value)
		else:
			ret = u'<c n="%s">%s</c>' % (convertToAttribute(choiceName), value)
		return (ret, None)
	
	if isinstance(obj, dict):
		ret = [ '<r>' ] # record
		for fieldName, fieldValue in obj.items():
			value, encoding = _testermanToXml(fieldValue)
			if encoding:
				ret.append(u'<f n="%s" encoding="%s">%s</f>' % (convertToAttribute(fieldName), encoding, value))
			else:
				ret.append(u'<f n="%s">%s</f>' % (convertToAttribute(fieldName), value))
		ret.append('</r>')
		return (u''.join(ret), None)

	# Other (simple) types.
	
	# If they are unicode, encode them to utf-8 (if not containing the forbidden characters)
	encoding = None
	if isinstance(obj, unicode):
		ret = obj
		if not isPrintable(ret):
			encoding = "base64"
			ret = base64.encodestring(obj.encode('utf-8'))
	else:
		# Try to cast the object to unicode. 
		try:
			ret = unicode(obj)
			if not isPrintable(ret):
				ret = base64.encodestring(obj)
				encoding = "base64"
		except UnicodeDecodeError:
			ret = base64.encodestring(obj)
			encoding = "base64"

	if not encoding:
		ret = cgi.escape(ret)
	
	return (ret, encoding)
	
def convertToAttribute(value):
	"""
	Escapes the usual characters so that the value can be used as an attribute value.
	"""
	return cgi.escape(value, True)

def convertToElement(e):
	"""
	Makes sure e can be used as a valid element name.
	"""
	ret = e
	if (e[0] >= '0') and (e[0] <= '9'):
		ret = "_%s" % e
	ret = ret.replace('#','')
	return ret

def isPrintable(s):
	"""
	Returns True if the string s is 'printable' (no control characters, etc)
	"""
	if '\x00' in s:
		return False
	return True

