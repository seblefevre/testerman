# -*- coding: utf-8 -*-

##
# A probe that can control a Selenium engine via its remote control.
##


import ProbeImplementationManager

import selenium


# Automatically generated from selenium.py
SeleniumCommandPrototypes = \
{'metaKeyDown': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getTitle': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'allowNativeXpath': {'args': ['allow'], 'method': 'do_command', 'treturnType': None}, 'focus': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'shiftKeyUp': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getAllWindowNames': {'args': [], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'mouseOut': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'isElementPresent': {'args': ['locator'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'getExpression': {'args': ['expression'], 'method': 'get_string', 'treturnType': 'charstring'}, 'getSelectedValues': {'args': ['selectLocator'], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'setCursorPosition': {'args': ['locator', 'position'], 'method': 'do_command', 'treturnType': None}, 'captureNetworkTraffic': {'args': ['type'], 'method': 'get_string', 'treturnType': 'charstring'}, 'getCookieByName': {'args': ['name'], 'method': 'get_string', 'treturnType': 'charstring'}, 'getCursorPosition': {'args': ['locator'], 'method': 'get_number', 'treturnType': 'integer'}, 'getAllLinks': {'args': [], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'contextMenu': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'getSelectedIndex': {'args': ['selectLocator'], 'method': 'get_string', 'treturnType': 'charstring'}, 'keyUp': {'args': ['locator', 'keySequence'], 'method': 'do_command', 'treturnType': None}, 'testComplete': {'args': [], 'method': 'do_command', 'treturnType': None}, 'contextMenuAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'removeAllSelections': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'getSpeed': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'getHtmlSource': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'attachFile': {'args': ['fieldLocator', 'fileLocator'], 'method': 'do_command', 'treturnType': None}, 'refresh': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getConfirmation': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'chooseOkOnNextConfirmation': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getElementPositionLeft': {'args': ['locator'], 'method': 'get_number', 'treturnType': 'integer'}, 'waitForCondition': {'args': ['script', 'timeout'], 'method': 'do_command', 'treturnType': None}, 'getAlert': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'removeSelection': {'args': ['locator', 'optionLocator'], 'method': 'do_command', 'treturnType': None}, 'getSelectOptions': {'args': ['selectLocator'], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'addSelection': {'args': ['locator', 'optionLocator'], 'method': 'do_command', 'treturnType': None}, 'waitForPageToLoad': {'args': ['timeout'], 'method': 'do_command', 'treturnType': None}, 'keyDownNative': {'args': ['keycode'], 'method': 'do_command', 'treturnType': None}, 'doubleClick': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'close': {'args': [], 'method': 'do_command', 'treturnType': None}, 'createCookie': {'args': ['nameValuePair', 'optionsString'], 'method': 'do_command', 'treturnType': None}, 'click': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'isSomethingSelected': {'args': ['selectLocator'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'getAttributeFromAllWindows': {'args': ['attributeName'], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'clickAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'goBack': {'args': [], 'method': 'do_command', 'treturnType': None}, 'rollup': {'args': ['rollupName', 'kwargs'], 'method': 'do_command', 'treturnType': None}, 'addScript': {'args': ['scriptContent', 'scriptTagId'], 'method': 'do_command', 'treturnType': None}, 'captureEntirePageScreenshotToString': {'args': ['kwargs'], 'method': 'get_string', 'treturnType': 'charstring'}, 'mouseUpRightAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'controlKeyUp': {'args': [], 'method': 'do_command', 'treturnType': None}, 'keyUpNative': {'args': ['keycode'], 'method': 'do_command', 'treturnType': None}, 'getAllWindowTitles': {'args': [], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'getLocation': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'waitForFrameToLoad': {'args': ['frameAddress', 'timeout'], 'method': 'do_command', 'treturnType': None}, 'keyPress': {'args': ['locator', 'keySequence'], 'method': 'do_command', 'treturnType': None}, 'useXpathLibrary': {'args': ['libraryName'], 'method': 'do_command', 'treturnType': None}, 'keyPressNative': {'args': ['keycode'], 'method': 'do_command', 'treturnType': None}, 'controlKeyDown': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getAllButtons': {'args': [], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'setTimeout': {'args': ['timeout'], 'method': 'do_command', 'treturnType': None}, 'shutDownSeleniumServer': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getXpathCount': {'args': ['xpath'], 'method': 'get_number', 'treturnType': 'integer'}, 'isCookiePresent': {'args': ['name'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'getAllWindowIds': {'args': [], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'keyDown': {'args': ['locator', 'keySequence'], 'method': 'do_command', 'treturnType': None}, 'setSpeed': {'args': ['value'], 'method': 'do_command', 'treturnType': None}, 'mouseDownRightAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'isPromptPresent': {'args': [], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'selectPopUp': {'args': ['windowID'], 'method': 'do_command', 'treturnType': None}, 'waitForPopUp': {'args': ['windowID', 'timeout'], 'method': 'do_command', 'treturnType': None}, 'isVisible': {'args': ['locator'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'getSelectedValue': {'args': ['selectLocator'], 'method': 'get_string', 'treturnType': 'charstring'}, 'metaKeyUp': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getAttribute': {'args': ['attributeLocator'], 'method': 'get_string', 'treturnType': 'charstring'}, 'typeKeys': {'args': ['locator', 'value'], 'method': 'do_command', 'treturnType': None}, 'getText': {'args': ['locator'], 'method': 'get_string', 'treturnType': 'charstring'}, 'selectWindow': {'args': ['windowID'], 'method': 'do_command', 'treturnType': None}, 'deleteAllVisibleCookies': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getMouseSpeed': {'args': [], 'method': 'get_number', 'treturnType': 'integer'}, 'openWindow': {'args': ['url', 'windowID'], 'method': 'do_command', 'treturnType': None}, 'answerOnNextPrompt': {'args': ['answer'], 'method': 'do_command', 'treturnType': None}, 'getSelectedLabels': {'args': ['selectLocator'], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'open': {'args': ['url'], 'method': 'do_command', 'treturnType': None}, 'select': {'args': ['selectLocator', 'optionLocator'], 'method': 'do_command', 'treturnType': None}, 'setContext': {'args': ['context'], 'method': 'do_command', 'treturnType': None}, 'isEditable': {'args': ['locator'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'mouseMoveAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'deleteCookie': {'args': ['name', 'optionsString'], 'method': 'do_command', 'treturnType': None}, 'selectFrame': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'submit': {'args': ['formLocator'], 'method': 'do_command', 'treturnType': None}, 'fireEvent': {'args': ['locator', 'eventName'], 'method': 'do_command', 'treturnType': None}, 'mouseDown': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'dragdrop': {'args': ['locator', 'movementsString'], 'method': 'do_command', 'treturnType': None}, 'type': {'args': ['locator', 'value'], 'method': 'do_command', 'treturnType': None}, 'getSelectedIds': {'args': ['selectLocator'], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'getSelectedLabel': {'args': ['selectLocator'], 'method': 'get_string', 'treturnType': 'charstring'}, 'mouseUpAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'ignoreAttributesWithoutValue': {'args': ['ignore'], 'method': 'do_command', 'treturnType': None}, 'chooseCancelOnNextConfirmation': {'args': [], 'method': 'do_command', 'treturnType': None}, 'shiftKeyDown': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getElementHeight': {'args': ['locator'], 'method': 'get_number', 'treturnType': 'integer'}, 'getTable': {'args': ['tableCellAddress'], 'method': 'get_string', 'treturnType': 'charstring'}, 'mouseOver': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'getBodyText': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'getAllFields': {'args': [], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'getSelectedIndexes': {'args': ['selectLocator'], 'method': 'get_string_array', 'treturnType': 'record of charstring'}, 'isAlertPresent': {'args': [], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'getValue': {'args': ['locator'], 'method': 'get_string', 'treturnType': 'charstring'}, 'isConfirmationPresent': {'args': [], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'windowMaximize': {'args': [], 'method': 'do_command', 'treturnType': None}, 'runScript': {'args': ['script'], 'method': 'do_command', 'treturnType': None}, 'highlight': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'getElementWidth': {'args': ['locator'], 'method': 'get_number', 'treturnType': 'integer'}, 'addLocationStrategy': {'args': ['strategyName', 'functionDefinition'], 'method': 'do_command', 'treturnType': None}, 'isOrdered': {'args': ['locator1', 'locator2'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'assignId': {'args': ['locator', 'identifier'], 'method': 'do_command', 'treturnType': None}, 'setBrowserLogLevel': {'args': ['logLevel'], 'method': 'do_command', 'treturnType': None}, 'setMouseSpeed': {'args': ['pixels'], 'method': 'do_command', 'treturnType': None}, 'captureScreenshotToString': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'removeScript': {'args': ['scriptTagId'], 'method': 'do_command', 'treturnType': None}, 'getEval': {'args': ['script'], 'method': 'get_string', 'treturnType': 'charstring'}, 'getWhetherThisWindowMatchWindowExpression': {'args': ['currentWindowString', 'target'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'check': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'mouseDownRight': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'uncheck': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'getPrompt': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'captureEntirePageScreenshot': {'args': ['filename', 'kwargs'], 'method': 'do_command', 'treturnType': None}, 'mouseMove': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'isChecked': {'args': ['locator'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'captureScreenshot': {'args': ['filename'], 'method': 'do_command', 'treturnType': None}, 'retrieveLastRemoteControlLogs': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'isTextPresent': {'args': ['pattern'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'altKeyUp': {'args': [], 'method': 'do_command', 'treturnType': None}, 'dragAndDrop': {'args': ['locator', 'movementsString'], 'method': 'do_command', 'treturnType': None}, 'getElementPositionTop': {'args': ['locator'], 'method': 'get_number', 'treturnType': 'integer'}, 'deselectPopUp': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getSelectedId': {'args': ['selectLocator'], 'method': 'get_string', 'treturnType': 'charstring'}, 'dragAndDropToObject': {'args': ['locatorOfObjectToBeDragged', 'locatorOfDragDestinationObject'], 'method': 'do_command', 'treturnType': None}, 'mouseDownAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'mouseUpRight': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'altKeyDown': {'args': [], 'method': 'do_command', 'treturnType': None}, 'windowFocus': {'args': [], 'method': 'do_command', 'treturnType': None}, 'getCookie': {'args': [], 'method': 'get_string', 'treturnType': 'charstring'}, 'mouseUp': {'args': ['locator'], 'method': 'do_command', 'treturnType': None}, 'getWhetherThisFrameMatchFrameExpression': {'args': ['currentFrameString', 'target'], 'method': 'get_boolean', 'treturnType': 'boolean'}, 'doubleClickAt': {'args': ['locator', 'coordString'], 'method': 'do_command', 'treturnType': None}, 'addCustomRequestHeader': {'args': ['key', 'value'], 'method': 'do_command', 'treturnType': None}, 'getElementIndex': {'args': ['locator'], 'method': 'get_number', 'treturnType': 'integer'}}


class SeleniumProbe(ProbeImplementationManager.ProbeImplementation):
	"""
Identification and Properties
-----------------------------

Probe Type ID: ``selenium``

Properties:

.. csv-table::
   :header: "Name","Type","Default value","Description"

   "``rc_host``","string","``localhost``","Selenium-RC hostname or IP address"
   "``rc_port``","integer","``4444``","Selenium-RC port"
   "``browser``","string","``firefox``","The browser Selenium should use on the Selenium host"
   "``server_url``","string","``None``","The server URL to browse when opening the browser. Providing it is mandatory."
   "``auto_shutdown``","boolean","``True``","When set, Selenium closes the browser window when the test case is over. It may be convenient to set it to False to leave this window open to debug a test case on error."

Overview
--------

This probe enables to perform Selenium-based test through the Selenium Remote Control (RC) / Server.

It uses two kinds of command interfaces:

* a "loose command" approach that enables to trigger any actions you may record via the Selenium IDE - in this case all commands have at most two optional parameters: target, and value. Adapting a Selenium IDE script to Testerman	is in this case trivial and a QTesterman plugin will be made available soon to do it for you.
* a "strict command" approach that enables to name the different parameters a Selenium command supports. Only commands specified in the TTCN-3 equivalence below are supported in this mode.

In both cases, some commands may return a result (for instance, isTextPresent returns a boolean result). You may expect such a result in a ``alt()`` loop as usual.

The probe automatically starts the browser on the RC host as soon as it is mapped, and everything is cleaned up once the test case is over.

A basic example is available in ``samples/selenium.ats``.

Limitations: for now, only the "loose command" mode is implemented.

Availability
~~~~~~~~~~~~

All platforms.

Dependencies
~~~~~~~~~~~~

The probe needs a configured (and running) Selenium Server (provided by Selenium RC) that it can reach.[[BR]]
You may install it on the host you want to run the browsers from.

See Also
~~~~~~~~

.. toctree::
   :maxdepth: 1

   /plugins/SeleniumFormatter

Extensions
----------

If you are using Selenium IDE to record events from your browser, you can user the following formatter to generate Testerman code directly: :doc:`/plugins/SeleniumFormatter`.

TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the ``SeleniumProbePortType`` port type as specified below:

::

  type union SeleniumStrictCommand
  {
    record { charstring key, charstring value } addCustomRequestHeader, 
    record { charstring strategyName, charstring functionDefinition } addLocationStrategy, 
    record { charstring scriptContent, charstring scriptTagId } addScript, 
    record { charstring locator, charstring optionLocator } addSelection, 
    record { charstring allow } allowNativeXpath, 
    record {} altKeyDown, 
    record {} altKeyUp, 
    record { charstring answer } answerOnNextPrompt, 
    record { charstring locator, charstring identifier } assignId, 
    record { charstring fieldLocator, charstring fileLocator } attachFile, 
    record { charstring filename, charstring kwargs } captureEntirePageScreenshot, 
    record { charstring kwargs } captureEntirePageScreenshotToString, // then expect a response as charstring
    record { charstring type } captureNetworkTraffic, // then expect a response as charstring
    record { charstring filename } captureScreenshot, 
    record {} captureScreenshotToString, // then expect a response as charstring
    record { charstring locator } check, 
    record {} chooseCancelOnNextConfirmation, 
    record {} chooseOkOnNextConfirmation, 
    record { charstring locator } click, 
    record { charstring locator, charstring coordString } clickAt, 
    record {} close, 
    record { charstring locator } contextMenu, 
    record { charstring locator, charstring coordString } contextMenuAt, 
    record {} controlKeyDown, 
    record {} controlKeyUp, 
    record { charstring nameValuePair, charstring optionsString } createCookie, 
    record {} deleteAllVisibleCookies, 
    record { charstring name, charstring optionsString } deleteCookie, 
    record {} deselectPopUp, 
    record { charstring locator } doubleClick, 
    record { charstring locator, charstring coordString } doubleClickAt, 
    record { charstring locator, charstring movementsString } dragAndDrop, 
    record { charstring locatorOfObjectToBeDragged, charstring locatorOfDragDestinationObject } dragAndDropToObject, 
    record { charstring locator, charstring movementsString } dragdrop, 
    record { charstring locator, charstring eventName } fireEvent, 
    record { charstring locator } focus, 
    record {} getAlert, // then expect a response as charstring
    record { charstring attributeLocator } getAttribute, // then expect a response as charstring
    record {} getBodyText, // then expect a response as charstring
    record {} getConfirmation, // then expect a response as charstring
    record {} getCookie, // then expect a response as charstring
    record { charstring name } getCookieByName, // then expect a response as charstring
    record { charstring locator } getCursorPosition, // then expect a response as integer
    record { charstring locator } getElementHeight, // then expect a response as integer
    record { charstring locator } getElementIndex, // then expect a response as integer
    record { charstring locator } getElementPositionLeft, // then expect a response as integer
    record { charstring locator } getElementPositionTop, // then expect a response as integer
    record { charstring locator } getElementWidth, // then expect a response as integer
    record { charstring script } getEval, // then expect a response as charstring
    record { charstring expression } getExpression, // then expect a response as charstring
    record {} getHtmlSource, // then expect a response as charstring
    record {} getLocation, // then expect a response as charstring
    record {} getMouseSpeed, // then expect a response as integer
    record {} getPrompt, // then expect a response as charstring
    record { charstring selectLocator } getSelectedId, // then expect a response as charstring
    record { charstring selectLocator } getSelectedIndex, // then expect a response as charstring
    record { charstring selectLocator } getSelectedLabel, // then expect a response as charstring
    record { charstring selectLocator } getSelectedValue, // then expect a response as charstring
    record {} getSpeed, // then expect a response as charstring
    record { charstring tableCellAddress } getTable, // then expect a response as charstring
    record { charstring locator } getText, // then expect a response as charstring
    record {} getTitle, // then expect a response as charstring
    record { charstring locator } getValue, // then expect a response as charstring
    record { charstring currentFrameString, charstring target } getWhetherThisFrameMatchFrameExpression, // then expect a response as boolean
    record { charstring currentWindowString, charstring target } getWhetherThisWindowMatchWindowExpression, // then expect a response as boolean
    record { charstring xpath } getXpathCount, // then expect a response as integer
    record {} goBack, 
    record { charstring locator } highlight, 
    record { charstring ignore } ignoreAttributesWithoutValue, 
    record {} isAlertPresent, // then expect a response as boolean
    record { charstring locator } isChecked, // then expect a response as boolean
    record {} isConfirmationPresent, // then expect a response as boolean
    record { charstring name } isCookiePresent, // then expect a response as boolean
    record { charstring locator } isEditable, // then expect a response as boolean
    record { charstring locator } isElementPresent, // then expect a response as boolean
    record { charstring locator1, charstring locator2 } isOrdered, // then expect a response as boolean
    record {} isPromptPresent, // then expect a response as boolean
    record { charstring selectLocator } isSomethingSelected, // then expect a response as boolean
    record { charstring pattern } isTextPresent, // then expect a response as boolean
    record { charstring locator } isVisible, // then expect a response as boolean
    record { charstring locator, charstring keySequence } keyDown, 
    record { charstring keycode } keyDownNative, 
    record { charstring locator, charstring keySequence } keyPress, 
    record { charstring keycode } keyPressNative, 
    record { charstring locator, charstring keySequence } keyUp, 
    record { charstring keycode } keyUpNative, 
    record {} metaKeyDown, 
    record {} metaKeyUp, 
    record { charstring locator } mouseDown, 
    record { charstring locator, charstring coordString } mouseDownAt, 
    record { charstring locator } mouseDownRight, 
    record { charstring locator, charstring coordString } mouseDownRightAt, 
    record { charstring locator } mouseMove, 
    record { charstring locator, charstring coordString } mouseMoveAt, 
    record { charstring locator } mouseOut, 
    record { charstring locator } mouseOver, 
    record { charstring locator } mouseUp, 
    record { charstring locator, charstring coordString } mouseUpAt, 
    record { charstring locator } mouseUpRight, 
    record { charstring locator, charstring coordString } mouseUpRightAt, 
    record { charstring url } open, 
    record { charstring url, charstring windowID } openWindow, 
    record {} refresh, 
    record { charstring locator } removeAllSelections, 
    record { charstring scriptTagId } removeScript, 
    record { charstring locator, charstring optionLocator } removeSelection, 
    record {} retrieveLastRemoteControlLogs, // then expect a response as charstring
    record { charstring rollupName, charstring kwargs } rollup, 
    record { charstring script } runScript, 
    record { charstring selectLocator, charstring optionLocator } select, 
    record { charstring locator } selectFrame, 
    record { charstring windowID } selectPopUp, 
    record { charstring windowID } selectWindow, 
    record { charstring logLevel } setBrowserLogLevel, 
    record { charstring context } setContext, 
    record { charstring locator, charstring position } setCursorPosition, 
    record { charstring pixels } setMouseSpeed, 
    record { charstring value } setSpeed, 
    record { charstring timeout } setTimeout, 
    record {} shiftKeyDown, 
    record {} shiftKeyUp, 
    record {} shutDownSeleniumServer, 
    record { charstring formLocator } submit, 
    record {} testComplete, 
    record { charstring locator, charstring value } type, 
    record { charstring locator, charstring value } typeKeys, 
    record { charstring locator } uncheck, 
    record { charstring libraryName } useXpathLibrary, 
    record { charstring script, charstring timeout } waitForCondition, 
    record { charstring frameAddress, charstring timeout } waitForFrameToLoad, 
    record { charstring timeout } waitForPageToLoad, 
    record { charstring windowID, charstring timeout } waitForPopUp, 
    record {} windowFocus, 
    record {} windowMaximize, 
  }
  
  
  // With this "simplified" model, the command can be anything
  // (assumed to be valid for Selenium), and its arguments
  // are made of 0, 1 or 2 arguments (none, target, or target + value)
  type union SeleniumLooseCommand
  {
    record { charstring target optional, charstring value optional } *, 
  }
  
  type SeleniumProbePortType
  {
    in SeleniumStrictCommand;
    in SeleniumLooseCommand;
    out any; // depends on the invoked command
  }
	"""

	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self.setDefaultProperty('rc_host', 'localhost')
		self.setDefaultProperty('rc_port', 4444)
		self.setDefaultProperty('browser', 'firefox')
		self.setDefaultProperty('server_url', None)
		self.setDefaultProperty('auto_shutdown', True)
		
		self._selenium = None
		self._sessionId = None
		self._extensionJs = ""

	# ProbeImplementation reimplementation
	def onTriMap(self):
		self._reset()
		# Automatically start browsing if a default url is provided
		url = self['server_url']
		if url:
			self._selenium = selenium.selenium(self['rc_host'], int(self['rc_port']), self['browser'], self['server_url'])
			self._selenium.start()
	
	def onTriUnmap(self):
		self._reset()
	
	def onTriSAReset(self):
		self._reset()
	
	def onTriExecuteTestCase(self):
		self._reset()

	# Specific implementation
	def _reset(self):	
		if self._selenium:
			if self['auto_shutdown']:
				self._selenium.stop()
			self._selenium = None

	def onTriSend(self, message, sutAddress):
		# Support for a list as loose command model, with only positional args
		# We turn this list into a (command, dict[target, value]) structure for further standard processing
		if isinstance(message, list):
			args = {}
			m = message[1:]
			if len(m) > 0:
				args['target'] = m[0]
			if len(m) > 1:
				args['value'] = m[1]
			message = (message[0], args)

		if not isinstance(message, tuple) or len(message) != 2:
			raise Exception("Invalid command message for this Selenium probe - expecting a couple (command, [args])")

		if not self._selenium:
			raise Exception("No available connection to a Selenium RC - please make sure the probe was mapped and a server_url was provided before using it")
			
		(cmd, args) = message

		# Loose command implementation only for now
		largs = []
		if args.has_key('target'):
			largs = [ args['target'] ]
			if args.has_key('value'):
				largs.append(args['value'])
		
		if SeleniumCommandPrototypes.has_key(cmd):
			proto = SeleniumCommandPrototypes[cmd]
			method = getattr(self._selenium, proto['method'])
			self.logSentPayload("%s(target = %s, value = %s)" % (cmd, args.get('target', None), args.get('value', None)), payload = '', sutAddress = '%s:%s' % (self['rc_host'], self['rc_port']))
			ret = method(cmd, largs)
			if proto['treturnType']:
				self.logReceivedPayload("%s returned" % cmd, payload = ret, sutAddress = '%s:%s' % (self['rc_host'], self['rc_port']))
				self.triEnqueueMsg(ret)
		else:
			# We assume that no return value is expected
			method = getattr(self._selenium, "do_command")
			self.logSentPayload("%s(target = %s, value = %s)" % (cmd, args.get('target', None), args.get('value', None)), payload = '', sutAddress = '%s:%s' % (self['rc_host'], self['rc_port']))
			ret = method(cmd, largs)
			
		
					

ProbeImplementationManager.registerProbeImplementationClass('selenium', SeleniumProbe)
		

