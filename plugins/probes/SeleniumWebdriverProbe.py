# -*- coding: utf-8 -*-

##
# A probe that can control a Selenium WebDriver.
##

import ProbeImplementationManager

from selenium import webdriver
import re, inspect

class SeleniumWebdriverProbe(ProbeImplementationManager.ProbeImplementation):
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self.setDefaultProperty('auto_shutdown', True)
		self.setDefaultProperty('implicitly_wait', 30)
		self.driver = None
		self.sutAddresString = ""
		self.locatorPattern = re.compile("^(xpath|css|id|link|name|tag_name)=(.*)$")
		self.retValuePattern = re.compile("^(is|get).") # assumption!

	def onTriMap(self):
		self._reset()
		# Note: the following lines might be needed if you don't use the standalone server (a.k.a. remote webdriver)
		#import os
		#if not os.environ.has_key('PATH') or os.environ['PATH'] == '':
		#	os.environ['PATH'] = os.defpath
		#if not os.environ.has_key('DISPLAY') or not os.environ['DISPLAY']:
		#	# Linux specific (?)
		#	os.environ['DISPLAY'] = ":0"
		#self.driver = webdriver.Firefox()
		self.driver = webdriver.Remote("http://localhost:4444/wd/hub", webdriver.DesiredCapabilities.FIREFOX.copy())
		self.driver.implicitly_wait(self['implicitly_wait'])

	def onTriUnmap(self):
		self._reset()

	def onTriSAReset(self):
		self._reset()

	def onTriExecuteTestCase(self):
		self._reset()

	def onTriSend(self, message, sutAddress):
		if not isinstance(message, dict) or not message.has_key('command'):
			raise Exception("Invalid message")
		if not self.driver:
			raise Exception("Webdriver isntance not availabe")

		cmd = message['command']
		target = message.get('target', None)
		value = message.get('value', None)

		obj, attr = self._getObjAndAttr(cmd, target)
		if callable(attr):
			numParams = self._getNumParams(attr)
			if numParams == 2: # this method has parameters (self, arg)
				arg = target if self._isWebdriverObj(obj) else value
				self._logSent(obj, cmd, target, value, hasParams = True)
				ret = attr(arg)
			elif numParams == 1:
				self._logSent(obj, cmd, target, value, hasParams = False)
				ret = attr()
			else:
				raise Exception("Unable to call this method: %s" % attr)
		else:
			self._logSent(obj, cmd, target, value, isCalled = False)
			ret = attr
		if self._hasRetValue(attr):
			self.logReceivedPayload("received '%s'" % ret, payload = ret, sutAddress = '%s:%s' % (self['rc_host'], self['rc_port']))
			self.triEnqueueMsg(ret)

	def _getObjAndAttr(self, cmd, target):
		"""
		Returns (obj = [Webdriver|Webelement], attr = [property|method])
		"""
		obj = self.driver
		if target:
			match = self.locatorPattern.search(target)
			if match:
				obj = self._getWebelement(*match.groups())
		attr = getattr(obj, cmd)
		return obj, attr

	def _getWebelement(self, locatorType, locatorString):
		"""
		Return a WebElement.
		"""
		if locatorType == "css":
			locatorType = "css_selector"
		find = getattr(self.driver, "find_element_by_" + locatorType)
		webelement = find(locatorString)
		return webelement

	def _getNumParams(self, method):
		"""
		Return # of params of the given method
		"""
		if method.__name__ == "send_keys":
			return 2 # workaround, because of 'def send_keys(self, *value)'
		else:
			arglist, _, _, _ = inspect.getargspec(method)
			return len(arglist)

	def _isWebdriverObj(self, obj):
		"""
		Check if given object is a WebDriver instance.
		"""
		return isinstance(obj, webdriver.remote.webdriver.WebDriver)

	def _logSent(self, obj, cmd, target, value, isCalled = True, hasParams = False):
		"""
		Build a nice log msg and send it.
		"""
		logmsg = "driver"
		arg = target
		if not self._isWebdriverObj(obj):
			logmsg += ".find_element(%s)" % target
			arg = value
		logmsg += ".%s" % cmd
		if isCalled:
			if hasParams:
				logmsg += "(%s)" % arg
			else:
				logmsg += "()"
		self.logSentPayload(logmsg, payload = '', sutAddress = '%s:%s' % (self['rc_host'], self['rc_port']))

	def _hasRetValue(self, attr):
		"""
		Workaround to check, whether we expect a return value
		"""
		if not inspect.ismethod(attr):
			return True
		if self.retValuePattern.search(attr.__name__):
			return True
		return False

	def _reset(self):
		if self.driver:
			self.driver.quit()
			self.driver = None

ProbeImplementationManager.registerProbeImplementationClass('selenium.webdriver', SeleniumWebdriverProbe)
