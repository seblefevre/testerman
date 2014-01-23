# -*- coding: utf-8 -*-

##
# A probe that can control a Selenium WebDriver via the Selenium RC Server.
##

import ProbeImplementationManager

from selenium import webdriver
import re, inspect

class SeleniumWebdriverProbe(ProbeImplementationManager.ProbeImplementation):
	"""
Identification and Properties
-----------------------------

Probe Type ID: ``selenium.webdriver``

Properties:

.. csv-table::
   :header: "Name","Type","Default value","Description"

   "``rc_host``","string","``localhost``","Selenium server hostname or IP address"
   "``rc_port``","integer","``4444``","Selenium server port"
   "``browser``","string","``firefox``","The browser Selenium should use on the Selenium host"
   "``server_url``","string","``None``","The server URL to browse when opening the browser. Providing it is mandatory."
   "``auto_shutdown``","boolean","``True``","When set, Selenium closes the browser window when the test case is over. It may be convenient to set it to False to leave this window open to debug a test case on error."

Overview
--------

This probe enables Testerman to perform Selenium-based tests through the Selenium Webdriver using a standalone Selenium Server.

The probe automatically starts the browser on the host as soon as it is mapped, and everything is cleaned up once the test case is over.

A basic example is available in ``samples/selenium_webdriver.ats``.

Availability
~~~~~~~~~~~~

All platforms.

Dependencies
~~~~~~~~~~~~

The probe needs a configured (and running) Selenium Server that it can reach (depending on the browser, you may need different servers).[[BR]]
You may install it on the host you want to run the browsers from.

TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the ``SeleniumWebdriverProbePortType`` port type as specified below:

::

  type record SeleniumSelenese
  {
   charstring command,
   charstring target optional,
   charstring value optinal
  }

  type SeleniumWebdriverProbePortType
  {
    in SeleniumSelenes
    out any; // depends on the invoked command
  }
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self.setDefaultProperty('auto_shutdown', True)
		self.setDefaultProperty('implicitly_wait', 30)
		self.setDefaultProperty('rc_host', 'localhost')
		self.setDefaultProperty('rc_port', '4444')
		self.setDefaultProperty('browser', 'firefox')
		self.driver = None
		self.locatorPattern = re.compile("^(xpath|css|id|link|name|tag_name)=(.*)$")
		self.retValuePattern = re.compile("^(is|get).") # assumption!

	def onTriMap(self):
		self._reset()
		# Note: the following lines might be needed if you don't use the standalone server (a.k.a. remote webdriver)
		#[import os]
		#if not os.environ.has_key('PATH') or os.environ['PATH'] == '':
		#	os.environ['PATH'] = os.defpath
		#if not os.environ.has_key('DISPLAY') or not os.environ['DISPLAY']:
		#	# Linux specific (?)
		#	os.environ['DISPLAY'] = ":0"
		#self.driver = webdriver.Firefox()
		b = self['browser'].upper()
		if hasattr(webdriver.DesiredCapabilities, b):
			caps = getattr(webdriver.DesiredCapabilities, b)
			self.driver = webdriver.Remote(self._getRemotAddr(b, self['rc_host'], self['rc_port']), caps.copy())
			self.driver.implicitly_wait(self['implicitly_wait'])
		else:
			self._probe.getLogger().error("No support for browser '%s'" % b)

	def _getRemotAddr(self, browser, host, port):
		addr = ("http://%s:%s") % (host, port)
		if (browser.upper() == "FIREFOX"):
			addr += "/wd/hub"
		return str(addr)

	def onTriUnmap(self):
		self._reset()

	def onTriSAReset(self):
		self._reset()

	def onTriExecuteTestCase(self):
		self._reset()

	def onTriSend(self, message, sutAddress):
		if (not isinstance(message, list) and not isinstance(tuple)) or len(message) < 1:
			raise Exception("Invalid message")
		if not self.driver:
			raise Exception("Webdriver isntance not availabe")
		if isinstance(message, tuple):
			message = list(message)

		cmd = message[0]
		target = message[1] if len(message) > 1 else None
		value = message[2] if len(message) > 2 else None

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
			if self['auto_shutdown']:
				self.driver.quit()
			self.driver = None

ProbeImplementationManager.registerProbeImplementationClass('selenium.webdriver', SeleniumWebdriverProbe)
