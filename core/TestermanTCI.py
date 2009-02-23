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
##

import TestermanMessages as Messages
import TestermanNodes as Nodes

import base64
import string
import sys
import threading
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

ExcludedLogClasses = [ 'internal' ]

def setExcludedLogClasses(classes):
	global ExcludedLogClasses
	ExcludedLogClasses = classes

def getExcludedLogClasses():
	return ExcludedLogClasses

def enableDebugLogs():
	setExcludedLogClasses([])

def disableLogs():
	setExcludedLogClasses([ 'internal', 'system', 'event', 'user' ]) # 'action' is always enabled

def enableLogs():
	setExcludedLogClasses([ 'internal' ])


################################################################################
# TLI interface: main entry point for all logging.
# Implemented to redirect things to a TL-like module.
################################################################################

# WARNING: duplicated info for class and timestamp: both are available in the payload and in the notification header.

def toXml(element, attributes, value = ''):
	return u'<%s %s>%s</%s>' % (element, " ".join(map(lambda e: '%s="%s"' % (e[0], str(e[1])), attributes.items())), value, element)

def logAtsStarted(id_):
	tliLog('event', toXml('ats-started', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logAtsStopped(id_, result, message):
	tliLog('event', toXml('ats-stopped', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'result': str(result) }, '<![CDATA[%s]]>' % message))

def logUser(message, tc = None):
	if tc is None:
		tliLog('user', toXml('user', { 'class': 'user', 'timestamp': time.time() }, '<![CDATA[%s]]>' % message))
	else:
		tliLog('user', toXml('user', { 'class': 'user', 'timestamp': time.time(), 'tc': tc }, '<![CDATA[%s]]>' % message))

def logInternal(message):
	tliLog('internal', toXml('internal', { 'class': 'internal', 'timestamp': time.time() }, '<![CDATA[%s]]>' % message))
	
def logMessageSent(fromTc, fromPort, toTc, toPort, message, address = None):
	if not address:
		address = ''
	try:
		tliLog('event', toXml('message-sent', { 'class': 'event', 'timestamp': time.time(), 'from-tc': fromTc, 'from-port': fromPort, 'to-tc': toTc, 'to-port': toPort }, '%s%s' % (testermanToXml(message, 'message'), testermanToXml(address, 'address'))))
	except Exception, e:
		ret = getBacktrace()
		logUser(unicode(e) + u'\n' + unicode(ret))

def logTestcaseCreated(id_, title):
	tliLog('event', toXml('testcase-created', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }, '<![CDATA[%s]]>' % title))

def logTestcaseStarted(id_):
	tliLog('event', toXml('testcase-started', { 'class': 'event', 'timestamp': time.time(), 'id': id_ }))

def logTestcaseStopped(id_, verdict, description):
	tliLog('event', toXml('testcase-stopped', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'verdict': verdict }, '<![CDATA[%s]]>' % description))

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
	tliLog('event', toXml('tc-stopped', { 'class': 'event', 'timestamp': time.time(), 'id': id_, 'verdict': verdict }, '<![CDATA[%s]]>' % message))

def logTestComponentKilled(id_, message = ''):
	tliLog('event', toXml('tc-killed', { 'class': 'event', 'timestamp': time.time(), 'id': id_, }, '<![CDATA[%s]]>' % message))

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

def tliLog(logClass, xml):
#	print "DEBUG| %s | %s" % (logClass, xml)
	if not logClass in getExcludedLogClasses():
		# Fire a log event
		TheIlClient.sendLogNotification(logClass, xml)
	
################################################################################
# Main Testerman log format: XML serializer
################################################################################

def testermanToXml(obj, simpleElement = None):
	"""
	Serializes a Testerman structure to an XML representation.
	
	Valid structures are:
	- simple types (strings, buffers, numerics, boolean)
	- lists of valid structures
	- dict[string] of valid structures,
	- couple (string, valid structure)
	
	@type  obj: python object
	@param obj: the structure to serialize
	@type  simpleElement: string, or None
	@param simpleElement: if present, the function results to a string that contains
	       the element. This is mainly useful (if not mandatory) for simple types, so
	       that the element can contain a correct encoding attribute. Ignored for non-simple types.

	@rtype: unicode
	@returns: the XML encoded string representing the structure.
	          Notice that no character encoding is applied (unicode).
	"""
	# Tries to apply the 'to message' transformation (useful for template proxies)
	try:
		obj = obj.toMessage()
	except:
		pass
	
	if isinstance(obj, list):
		# The internally working object is a lis - faster than a string for concat ops.
		ret = []
		count = 0
		for subobj in obj:
			ret.append(testermanToXml(subobj, '_%d' % count))
			count += 1
		if simpleElement:
			return u'<%s>%s</%s>' % (simpleElement, ''.join(ret), simpleElement)
		else:
			return u''.join(ret)
	
	if isinstance(obj, tuple):
		if not len(obj) == 2:
			# ignore it - invalid structure
			if simpleElement:
				return u'<%s />' % simpleElement
			else:
				return u''
		# Make sure this is a valid element name
		element = convertToElement(unicode(obj[0]))
		ret = testermanToXml(obj[1], element)
		if simpleElement:
			return u'<%s>%s</%s>' % (simpleElement, ret, simpleElement)
		else:
			return ret
	
	if isinstance(obj, dict):
		ret = [ testermanToXml(val, convertToElement(element)) for element, val in obj.items() ]
		if simpleElement:
			return u'<%s>%s</%s>' % (simpleElement, ''.join(ret), simpleElement)
		else:
			return u''.join(ret)
	

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
	
	if simpleElement:
		if encoding:
			return u'<%s encoding="%s"><![CDATA[%s]]></%s>' % (simpleElement, encoding, ret, simpleElement)
		else:
			return u'<%s><![CDATA[%s]]></%s>' % (simpleElement, ret, simpleElement)
	else:
		# Discarded encoding information in this case.
		return ret
			
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
