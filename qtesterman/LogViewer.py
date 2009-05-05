# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 QTesterman contributors
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
# Log & events viewer widgets and associated stuff.
#
##

from PyQt4.Qt import *
import PyQt4.QtXml as QtXml

from Base import *
from CommonWidgets import *
import VisualLogView
import EventMonitor
import Actions
import PluginManager

import gc
import base64
import urlparse
import os
import os.path

###############################################################################
# Log file loader
###############################################################################

def loadLog(url):
	"""
	Load a log file from an url.
	
	@type  url: QUrl
	@param url: the url locating the log file (testerman://, file://)
	
	@rtype: utf-8 string
	@returns: the log contents, or None if not found
	"""
	log("Loading log from '%s'" % unicode(url.toString()))

	content = None
	if url.scheme() == "file": # local file
		log("Loading from local file %s..." % url.toString())
		path = url.toLocalFile()
		f = open(unicode(path), 'r')
		content = f.read()
		f.close()

	else: # remote file
		log("Loading from server: remote file %s..." % url.path())
		content = getProxy().getFile(unicode(url.path()))

	# If this is not a well formed xml file but a "log" file (i.e. a list of xml elements only)
	# add some basic xml headers and a root element.
	if content and not content.startswith('<?xml'):
		content = '<?xml version="1.0" encoding="utf-8" ?>\n<ats>\n%s</ats>' % content
	
	return content

def trim(docstring):
	"""
	docstring trimmer - from PEP 257 sample code
	Used to trim descriptions from old Testerman versions that
	did not trim the docstrings by themselves.
	"""
	if not docstring:
		return ''
	maxint = 2147483647
	# Convert tabs to spaces (following the normal Python rules)
	# and split into a list of lines:
	lines = docstring.expandtabs().splitlines()
	# Determine minimum indentation (first line doesn't count):
	indent = maxint
	for line in lines[1:]:
		stripped = line.lstrip()
		if stripped:
			indent = min(indent, len(line) - len(stripped))
	# Remove indentation (first line is special):
	trimmed = [lines[0].strip()]
	if indent < maxint:
		for line in lines[1:]:
			trimmed.append(line[indent:].rstrip())
	# Strip off trailing and leading blank lines:
	while trimmed and not trimmed[-1]:
		trimmed.pop()
	while trimmed and not trimmed[0]:
		trimmed.pop(0)
	# Return a single string:
	return '\n'.join(trimmed)

class LogSaver:
	"""
	A Raw log saver that can follow include directives
	to expand the logs inline or save them into a dedicated
	sub-directory.
	
	Based on *string* parsing, not XML parsing, 
	and assumes that <include> elements are on a single line.
	"""
	MODE_EXPAND = "expand"
	MODE_REWRITE = "rewrite"
	MODE_RAW = "raw"

	def __init__(self, client, mode = MODE_RAW):
		self._client = client
		self._mode = mode

	def saveAs(self, filename, rawLogs):
		f = open(filename, 'w')
		self._save(f, rawLogs, prefix = '.'.join(filename.split('/')[-1].split('.')[-1]))
		f.close()

	def _save(self, f, rawLogs, prefix = None):
		if self._mode == self.MODE_RAW:
			f.write(rawLogs)
			return

		for line in rawLogs.split('\n'):
			line = unicode(line).encode('utf-8')
			if not line.startswith('<include '):
				f.write(line + '\n')
			else:
				m = re.match(r'\<include (?P<prefix>.*)url="(?P<url>.*?)" (?P<suffix>.*)', line)
				if m:
					url = m.group('url')
					if self._mode == self.MODE_EXPAND:
						includedLogs = self.fetchUrl(url)
						if includedLogs is not None:
							self._save(f, includedLogs)
						else:
							# Warning
							log("Unable to fetch url '%s'..." % url)

					elif self._mode == self.MODE_REWRITE: # Untested code (for now)
						includedLogs = self.fetchUrl(url)
						if includedLogs is not None:
							# new file in a new folder
							dirname = prefix
							name = url.split('/')[-1]
							filename = "%s/%s" % (dirname, name)
							f.write('<include %surl="%s/%s" %s\n' % (m.group('prefix'), filename, m.group('suffix')))
							# Create the file
							try:
								os.makedirs(dirname)
							except:
								pass
							subf = open(filename, 'w')
							self._save(subf, prefix = '.'.join(name.split('.')[-1]))
							subf.close()

	def fetchUrl(self, url):
		log("Fetching included url '%s'..." % url)
		# extract path from url
		path = os.path.normpath(urlparse.urlparse(url).path)
		log("Fetching included path '%s'..." % path)
		return self._client.getFile(path)

###############################################################################
# LogModel - inner object emitting interesting event signals
###############################################################################

def xmlToDomElement(xmlLog):
	"""
	Constructs a DOM element based on a xml string, and returns it.
	
	@type  xmlLog: unicode
	@param xmlLog: a log event as a xml string
	
	@rtype: QDomElement
	@returns: the parsed element as a DOM node, or None in case of an error
	"""
	doc = QtXml.QDomDocument()
	(res, errormessage, errorline, errorcol) = doc.setContent(xmlLog, 0)
	if res:
		return doc.documentElement()
	else:
		log("WARNING: Unable to parse XML event: %s" % str(errormessage))
		return None

class TestCaseLogModel:
	"""
	Stores the events associated to a testcase.
	Provides additional convenience functions for the usual
	testcase properties, too.
	"""
	def __init__(self, id_, atsLogModel):
		self._domElements = []
		self._atsLogModel = atsLogModel
		# Set by the main log model
		self._verdict = None
		self._description = None
		self._id = id_
		self._title = ''
	
	def _append(self, domElement):
		"""
		Local model feeder, storage only.
		"""
		tag = domElement.tagName()
		if tag == "testcase-started":
			self._title = unicode(domElement.text()).strip()
		elif tag == "testcase-stopped":
			self._description = trim(unicode(domElement.text()))
			self._verdict = unicode(domElement.attribute('verdict'))
		
		self._domElements.append(domElement)
		
	##
	# Public functions usable in log reporters, plugins
	##	
	def getDomElements(self, tagName = None):
		if tagName:
			return filter(lambda x: x.tagName() == QString(tagName), self._domElements)
		else:
			return self._domElements
	
	def isComplete(self):
		return self._verdict is not None
	
	def getVerdict(self):
		return self._verdict
	
	def getDescription(self):
		return self._description
	
	def getId(self):
		return self._id
	
	def getTitle(self):
		return self._title
	
	def getAts(self):
		return self._atsLogModel

class AtsLogModel:
	def __init__(self, id_):
		# Local DOM elements (ATS control part)
		self._domElements = []

		# Set by the main log model
		self._result = None
		self._id = id_
		self._testCases = [] # list of TestCaseModels
	
	def _append(self, domElement):
		"""
		Local model feeder, storage only.
		"""
		tag = domElement.tagName()
		if tag == "ats-stopped":
			self._result = int(domElement.attribute('result'))
		
		self._domElements.append(domElement)
	
	##
	# Public functions usable in log reporters, plugins
	##	
	def getDomElements(self, tagName = None):
		if tagName:
			return filter(lambda x: x.tagName() == QString(tagName), self._domElements)
		else:
			return self._domElements
	
	def isComplete(self):
		return self._result is not None
	
	def getId(self):
		return self._id
	
	def getResult(self):
		return self._result
	
	def getTestCases(self):
		return self._testCases

class LogModel(QObject):
	"""
	This represents a complete Testerman log as an internal model
	suitable for ATS/testcase iteration and so on.
	
	It is fed log event by log event, either as XML string or
	as a single QDomElement.
	
	This model interprets the fed event and emits several signals
	enabling basic statistics and model visualisation during feeding.

	High level signals:
	atsStarted(QDomElement)
	atsStopped(int result, QDomElement)
	testCaseStarted(QString identifier, QDomElement)
	testCaseStopped(QString verdict, QDomElement)
	actionRequested(QString label, float timeout)

	Low level signal:
	testermanEvent(QDomElement element)
	"""
	def __init__(self):
		QObject.__init__(self)
		self._atses = []
		# This flag enables to know if we have some include elements quickly.
		# It is convenient to be aware of such directives
		# when saving a log file locally, so that we can prompt the user
		# to ignore/rewrite/expand include files.
		self._containsIncludes = False
		
		self._currentAts = None
		self._currentTestCase = None

	def clear(self):
		self._atses = []
		self._containsIncludes = False

	def feedXmlEvent(self, xmlLog):
		"""
		Convenience function.
		
		Uses the provided event formatted as an xml string
		to feed the model.
		
		@type  xmlLog: unicode
		@param xmlLog: a log event as a xml string
		"""
		self.feedEvent(xmlToDomElement(xmlLog))

	def feedEvent(self, domElement):
		"""
		Feeds the model with a QDomElement, corresponding
		to a single log event.
		
		Emits signals according to the event,
		then stores the event in the appropriate internal
		model structures.
		
		Automatically follows <include> elements, retrieving
		requested log file on the fly and feeding itself.
		
		@type  domElement: QDomElement
		@param domElement: a single log event as a DOM element.
		"""
		if not domElement:
			return

		tag = domElement.tagName()

		if tag == "ats-started":
			atsLogModel = AtsLogModel(domElement.attribute('id'))
			atsLogModel._append(domElement)
			self._atses.append(atsLogModel)
			self._currentAts = atsLogModel
			self.emit(SIGNAL("atsStarted"), atsLogModel)
			self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)

		elif tag == "ats-stopped":
			self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)
			if not self._currentAts:
				log("ATS stopped event received, but missed the started event. Discarding.")
			else:
				self._currentAts._append(domElement)
				self.emit(SIGNAL("atsStopped"), self._currentAts)
				self._currentAts = None
				self._currentTestCase = None

		elif tag == "testcase-created": # FIXME: should be -started instead, but MTC/system creation logs are between -created and -started events
			if not self._currentAts:
				log("TestCase started event received, but missed the started ATS event. Discarding.")
			else:
				testCaseLogModel = TestCaseLogModel(domElement.attribute('id'), self._currentAts)
				testCaseLogModel._append(domElement)
				self._currentAts._testCases.append(testCaseLogModel)
				self._currentTestCase = testCaseLogModel
				self.emit(SIGNAL("testCaseStarted"), testCaseLogModel)
			self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)

		elif tag == "testcase-stopped":
			self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)
			if not self._currentTestCase:
				log("TestCase stopped event received, but missed the started event. Discarding.")
			else:
				self._currentTestCase._append(domElement)
				self.emit(SIGNAL("testCaseStopped"), self._currentTestCase)
				self._currentTestCase = None

		elif tag == "action-requested":
			self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)
			timeout = float(domElement.attribute('timeout'))
			message = domElement.firstChildElement('message').text()
			self.emit(SIGNAL("actionRequested(QString, float)"), QString(message), timeout)
			if self._currentTestCase:
				self._currentTestCase._append(domElement)

		elif tag == "action-cleared":
			self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)
			self.emit(SIGNAL("actionCleared()"))
			if self._currentTestCase:
				self._currentTestCase._append(domElement)
		
		elif tag == "include":
			url = QUrl(domElement.attribute('url'))
			self._containsIncludes = True
			self._processInclude(url)
			# Don't forward an include 'event'
		
		else:
			# Store the event into the internal data structure
			if self._currentTestCase:
				self._currentTestCase._append(domElement)
			elif self._currentAts:
				self._currentAts._append(domElement)
			self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)

	def _processInclude(self, url):
		"""
		Loads an included file identified by the provided url,
		and feeds it to itself.
		
		@type  url: QUrl
		@param url: the url locating the file to load containing the included logs.
		"""
		xmlLog = loadLog(url)
		if not xmlLog:
			log("Warning: unable to get included logs")
			return
	
		log("Parsing included logs...")
		xmlDoc = QtXml.QDomDocument()
		(res, errormessage, errorline, errorcol) = xmlDoc.setContent(xmlLog, 0)
		log("Included Logs parsed, DOM constructed")

		element =  xmlDoc.documentElement().firstChildElement()
		count = 0
		while not element.isNull():
			self.feedEvent(element)
			count += 1
			if not (count % 50):
				QApplication.instance().processEvents()
			element = element.nextSiblingElement()

	def getAtses(self):
		"""
		Iterator version ?
		"""
		return self._atses


###############################################################################
# Log Summary
###############################################################################

class WSummaryGroupBox(QGroupBox):
	"""
	A summary that is updated thanks to TextualLogViewer signals.
	"""
	def __init__(self, parent = None):
		QGroupBox.__init__(self, "Execution summary", parent)
		self.__createWidgets()
		self.clear()

	def __createWidgets(self):
		self.labels = {}
		for l in [ 'nbPass', 'ratioPass', 'nb', 'nbFail', 'ratioFail', 'nbAts' ]:
			self.labels[l] = QLabel()

		layout = QGridLayout()
		layout.addWidget(QLabel("Executed testcases:"), 0, 0, Qt.AlignRight)
		layout.addWidget(self.labels['nb'], 0, 1)
		layout.addWidget(QLabel("Number of OK:"), 1, 0, Qt.AlignRight)
		layout.addWidget(self.labels['nbPass'], 1, 1)
		layout.addWidget(self.labels['ratioPass'], 1, 2)
		layout.addWidget(QLabel("Number of NOK:"), 2, 0, Qt.AlignRight)
		layout.addWidget(self.labels['nbFail'], 2, 1)
		layout.addWidget(self.labels['ratioFail'], 2, 2)
		layout.addWidget(QLabel("Executed ATSes:"), 0, 3, Qt.AlignRight)
		layout.addWidget(self.labels['nbAts'], 0, 4)
		layout.setColumnStretch(0, 0)
		layout.setColumnStretch(1, 0)
		layout.setColumnStretch(2, 0)
		layout.setColumnStretch(3, 0)
		layout.setColumnStretch(4, 20)
		self.setLayout(layout)

	def onTestCaseStopped(self, testCaseLogModel):
		self.total += 1
		if testCaseLogModel.getVerdict() == "pass":
			self.totalOK += 1
		else:
			self.totalKO += 1
		self.updateStats()

	def onAtsStopped(self, atsLogModel):
		self.totalAts += 1
		self.updateStats()

	def clear(self):
		self.total = 0
		self.totalOK = 0
		self.totalKO = 0
		self.totalAts = 0
		self.updateStats()

	def updateStats(self):
		self.labels['nb'].setText(str(self.total))
		self.labels['nbPass'].setText(str(self.totalOK))
		self.labels['nbFail'].setText(str(self.totalKO))
		if self.total > 0:
			self.labels['ratioPass'].setText("(%.2f %%)" % (float(self.totalOK) / float(self.total) * 100))
			self.labels['ratioFail'].setText("(%.2f %%)" % (float(self.totalKO) / float(self.total) * 100))
		else:
			self.labels['ratioPass'].setText("")
			self.labels['ratioFail'].setText("")
		self.labels['nbAts'].setText(str(self.totalAts))

###############################################################################
# Raw log viewer
###############################################################################

class WSaveLogOptionDialog(QDialog):
	def __init__(self, parent = None):
		QDialog.__init__(self, parent)
		self.__createWidgets()
	
	def __createWidgets(self):
		self.setWindowTitle("Select raw log exportation method")
		layout = QVBoxLayout()

		self._group = QButtonGroup()
		button = QRadioButton("Expand included logs inline\nInclude directives are followed, leading to a single, but possibly large, log file")
		self._group.addButton(button, 0)
		layout.addWidget(button)
		button.setChecked(True)
		button = QRadioButton("Retrieve included logs as dedicated files\nInclude directives are followed, leading to a master file referencing other files in sub-directories")
		self._group.addButton(button, 1)
		layout.addWidget(button)
		button = QRadioButton("Leave the raw log as is\nDo not follow include directives. The saved log file may contain incomplete contents.")
		self._group.addButton(button, 2)
		layout.addWidget(button)

		buttonsLayout = QHBoxLayout()
		self.okButton = QPushButton("OK")
		self.connect(self.okButton, SIGNAL('clicked()'), self.accept)
		self.cancelButton = QPushButton("Cancel")
		self.connect(self.cancelButton, SIGNAL('clicked()'), self.reject)
		buttonsLayout.addStretch()
		buttonsLayout.addWidget(self.okButton)
		buttonsLayout.addWidget(self.cancelButton)
		layout.addLayout(buttonsLayout)

		self.setLayout(layout)

	def getSelectedMode(self):
		id_ = self._group.checkedId()
		if id_ == 0:
			return LogSaver.MODE_EXPAND
		elif id_ == 1:
			return LogSaver.MODE_REWRITE
		else:
			return LogSaver.MODE_RAW

class WRawLogView(QWidget):
	"""
	A simple composite widget with a read-only text edit to display
	raw XML logs,
	and an option to save and find things in it.
	
	Raw logs are not updated on realtime, as appending each event
	won't create a valid XML file (unless we insert those events
	before a final root element's closing tag, which would be costly).
	
	Instead, they are displayed only when the user updates
	the logs, i.e. (re)load them from the server.
	In these case, we have an opportunity to fix the log to make it
	xml-well-formed, adding requiring missing root element and XML prologue.
	(this is done in the (re)loading function, i.e. updateFromSource).
	The "Save as" option is then enabled.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()
		
	def __createWidgets(self):
		layout = QVBoxLayout()
		self.textEdit = QTextEdit()
		self.textEdit.setReadOnly(True)
		self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
		self.textEdit.setUndoRedoEnabled(False)

		layout.addWidget(self.textEdit)
		self.textEdit.setHtml('<i>Click on Update to load raw logs</i>')

		# Save actions
		self.saveRawAction = TestermanAction(self, "Save raw logs", lambda: self.saveAs(LogSaver.MODE_RAW), "Do not follow include directives. The saved log file may contain incomplete content")
		self.saveExpandAction = TestermanAction(self, "Expand included files inline and save", lambda: self.saveAs(LogSaver.MODE_EXPAND), "Include directives are followed, leading to a single, but possibly large, log file")
		self.saveRewriteAction = TestermanAction(self, "Follow and save included files", lambda: self.saveAs(LogSaver.MODE_REWRITE), "Include directives are followed, leading to a master file referencing other files in sub-directories")
		self.saveMenu = QMenu('Save as...', self)
		self.saveMenu.addAction(self.saveExpandAction)
#		self.saveMenu.addAction(self.saveRewriteAction) # Not yet

		self.saveAsButton = QToolButton()
		self.saveAsButton.setDefaultAction(self.saveRawAction)
		self.saveAsButton.setMenu(self.saveMenu)
		self.saveAsButton.setIconSize(QSize(16, 16))
		self.saveAsButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
		self.saveAsButton.setPopupMode(QToolButton.MenuButtonPopup)

		optionLayout = QHBoxLayout()
		optionLayout.addWidget(WFind(self.textEdit))
		self.saveAsButton.setEnabled(False) # enabled on loading raw logs
		optionLayout.addWidget(self.saveAsButton)

		layout.addLayout(optionLayout)

		self.setLayout(layout)

	def saveAs(self, mode):
		"""
		TODO: if the log file contains links to other files,
		proposes the user to:
		- save this file only (does not follow links)
		- save links as external files and updates the links accordingly
		- expand the log file by including linked files directly in it
		"""
		settings = QSettings()
		directory = settings.value('lastVisitedDirectory', QVariant("")).toString()
		filename = QFileDialog.getSaveFileName(self, "Save execution log as...", directory, "xml file (*.xml)")
		extension = 'xml'
		if filename.isEmpty():
			return False
		elif not filename.split('.')[-1] == extension:
			filename = filename + '.' + extension

		filename = unicode(filename)
		directory = os.path.dirname(filename)
		settings.setValue('lastVisitedDirectory', QVariant(directory))
		try:
			rawLogs = self.textEdit.toPlainText()
			logSaver = LogSaver(QApplication.instance().client(), mode)
			logSaver.saveAs(filename, rawLogs)
			QMessageBox.information(self, getClientName(), "Execution log saved successfully.", QMessageBox.Ok)
			return True
		except Exception, e:
			systemError(self, "Unable to save file as %s: %s" % (filename, unicode(e)))
			return False

	def clearLog(self):
		self.textEdit.clear()

	def setLog(self, txt):
		self.textEdit.setPlainText(txt)
		self.saveAsButton.setEnabled(True)

###############################################################################
# Complete Log Viewer
###############################################################################

class WLogViewer(QWidget):
	"""
	This viewer has both realtime/online and offline browsing capacities.
	
	Use:
		- openJob(jobId) to start watching a job (opening its current log file),
		  i.e. opening in real time mode (automatic switch to offline mode
		  when the job is over)
		- openUrl(url) to analyze an existing remote or local file (offline mode)
	
	It displays the logs in multiple forms.
	
	Log analyze 'perspective':
	Below an execution summary, a widget lists the different TestCases in the log.
	When selecting a TestCase, you can see it through a Textual Log View or a Visual Log View.

	Log report 'perspective':
	Displays reporter plugins.

	Advanced/Raw log 'perspective':
	a simple raw log in txt mode.

	In real time mode:
	- the viewer subscribes to get events related to the watched job, enabling:
		- real time log update
		- additional control over the job: pause/resume, cancel, kill
	
	An additional "delete logs" button is activated only for completed job or in offline mode.
	"""
	def __init__(self, standalone = False, parent = None):
		QWidget.__init__(self, parent, Qt.Window)

		# No jobId means "offline mode"
		self.jobId = None
		self._url = None
		self.title = ''
		self.standalone = standalone
		self.trackingActivated = False
		self.jobState = 'n/a'

		# Report plugins
		self.reportViews = []

		# get display preferences
		settings = QSettings()
		self.useRawView = settings.value('logs/raws', QVariant(True)).toBool()

		# Dialog box that may appear if an action is required by the user
		self.actionRequestedDialog = None
		
		self.__createWidgets()
		self.resize(QSize(800, 600))

	def setTitle(self, title):
		self.title = title
		self.updateWindowTitle()
	
	def openUrl(self, url):
		"""
		@type  url: QUrl
		@param url: the file to open
		"""
		log("DEBUG: opening '%s'" % unicode(url.toString()))
		self._url = url
		self.updateFromSource()
		self.updateWindowTitle()

	def openJob(self, jobId):
		"""
		@type  jobId: integer
		@param jobId: the job ID to watch
		"""		
		self.jobId = jobId
		# Synchronization problem here:
		# we should register to receive JOB-EVENT and LOG notifications asap, but:
		# - there is no garantee we don't miss any
		# - since we also need to retrieve the current job log, we may mix events.
		self.eventMonitor = EventMonitor.EventMonitor(parent = self)
		self.connect(self.eventMonitor, SIGNAL("subscribedEvent"), self.onSubscribedEvent)
		self.eventMonitor.subscribe("job:%d" % self.jobId)
		self.updateFromSource()
		self.updateWindowTitle()
		
	def updateWindowTitle(self):
		if self.jobId is not None:
			self.setWindowTitle('%s (watching running job %d)' % (self.title, self.jobId))
		elif self._url:
			self.setWindowTitle('%s (viewing %s)' % (self.title, unicode(self._url.path())))

	def __createWidgets(self):
		self.setWindowIcon(icon(':/icons/log'))
	
		# Inner objects (non widget)
		self.eventMonitor = None
		self._logModel = LogModel()

		layout = QVBoxLayout()

		# An execution summary
		self.summary = WSummaryGroupBox(self)
		layout.addWidget(self.summary)

		# The main perspective tab
		self.perspectiveTab = QTabWidget()
		self.perspectiveTab.setTabPosition(QTabWidget.West)
		layout.addWidget(self.perspectiveTab, 1)

		# Perspective: Analyze
		# The tab that enables to switch views
		self.analyzerTab = QTabWidget()

		self.testCaseView = WTestCaseView()
		self.textualLogView = WTextualLogView()
		self.visualLogView = VisualLogView.WVisualTestCaseView()
		self.templateView = WMixedTemplateView()

		self.analyzerTab.addTab(self.textualLogView, "Textual log view")
		self.analyzerTab.addTab(self.visualLogView, "Visual log view")

		# The view / template view splitter
		self.templateViewSplitter = QSplitter(Qt.Vertical)
		self.templateViewSplitter.addWidget(self.analyzerTab)
		self.templateViewSplitter.addWidget(self.templateView)
		self.templateViewSplitter.setStretchFactor(0, 3)
		self.templateViewSplitter.setStretchFactor(1, 1)

		# The testcase list / view splitter
		self.listViewSplitter = QSplitter(Qt.Horizontal, self)

		testCaseViewWidget = QWidget()
		testCaseViewLayout = QVBoxLayout()
		testCaseViewLayout.addWidget(self.testCaseView, 1)
		self.trackingCheckBox = QCheckBox("Event tracking")
		self.trackingCheckBox.setChecked(self.trackingActivated)
		testCaseViewLayout.addWidget(self.trackingCheckBox)

		testCaseViewWidget.setLayout(testCaseViewLayout)
		self.listViewSplitter.addWidget(testCaseViewWidget)
		self.listViewSplitter.addWidget(self.templateViewSplitter)
		self.listViewSplitter.setStretchFactor(0, 0) # Keep size for the testcase view
		self.listViewSplitter.setStretchFactor(1, 1)

		self.perspectiveTab.addTab(self.listViewSplitter, "Analyze")

		# Perspective: Report
		self.reportTab = QTabWidget()

		for viewPlugin in PluginManager.getPluginClasses("report-view"):
			if viewPlugin['activated']:
				view = viewPlugin["class"]()
				label = viewPlugin["label"]
				view._setModel(self._logModel)
				self.reportViews.append(view)
				self.reportTab.addTab(view, label)

		self.perspectiveTab.addTab(self.reportTab, "Report")

		# Perspective: Advanced (Raw log)
		self.rawView = WRawLogView()

		self.perspectiveTab.addTab(self.rawView, "Raw log")

		# Connection on main log model
		self.connect(self._logModel, SIGNAL("testCaseStopped"), self.testCaseView.onTestCaseStopped)
		self.connect(self._logModel, SIGNAL("testCaseStarted"), self.testCaseView.onTestCaseStarted)
		self.connect(self._logModel, SIGNAL("atsStopped"), self.testCaseView.onAtsStopped)
		self.connect(self._logModel, SIGNAL("atsStarted"), self.testCaseView.onAtsStarted)
		# The test case view forwards real-time events to the views corresponding to the currently selected item, if any
		self.connect(self._logModel, SIGNAL("testermanEvent(QDomElement)"), self.testCaseView.onEvent)
		for view in self.reportViews:
			self.connect(self._logModel, SIGNAL("testermanEvent(QDomElement)"), view.onEvent)

		# Summary connection on main log model
		self.connect(self._logModel, SIGNAL("testCaseStopped"), self.summary.onTestCaseStopped)
		self.connect(self._logModel, SIGNAL("atsStopped"), self.summary.onAtsStopped)

		# External Action management
		self.connect(self._logModel, SIGNAL("actionRequested(QString, float)"), self.onActionRequested)
		self.connect(self._logModel, SIGNAL("actionCleared()"), self.onActionCleared)

		# Inter widget connections
		self.connect(self.textualLogView, SIGNAL("messageSelected(QDomElement)"), self.templateView.setTemplates)
		self.connect(self.textualLogView, SIGNAL("templateMisMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)
		self.connect(self.textualLogView, SIGNAL("templateMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)

		self.connect(self.visualLogView, SIGNAL("messageSelected(QDomElement)"), self.templateView.setTemplates)
		self.connect(self.visualLogView, SIGNAL("templateMisMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)
		self.connect(self.visualLogView, SIGNAL("templateMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)

		self.connect(self.testCaseView, SIGNAL("currentItemChanged(QTreeWidgetItem*, QTreeWidgetItem*)"), self.onTestCaseItemChanged)
		# The Test Case view also "forwards" domElement in case of an event arriving while the item corresponding to the updated TestCase is selected
		self.connect(self.testCaseView, SIGNAL("testermanEvent(QDomElement)"), self.textualLogView.onEvent)
		self.connect(self.testCaseView, SIGNAL("testermanEvent(QDomElement)"), self.visualLogView.onEvent)

		self.connect(self.trackingCheckBox, SIGNAL('stateChanged(int)'), self.setTracking)

		# in standalone mode, several actions are not presented

		# Control bar
		controlLayout = QHBoxLayout()
		self.statusLabel = QLabel("n/a")
		self.pauseButton = QPushButton("Pause")
		self.connect(self.pauseButton, SIGNAL("clicked()"), self.pauseOrResumeJob)
		self.cancelButton = QPushButton("Cancel")
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.cancelJob)
		self.killButton = QPushButton("Kill")
		self.connect(self.killButton, SIGNAL("clicked()"), self.killJob)

		if not self.standalone:
			controlLayout.addWidget(self.pauseButton)
			controlLayout.addWidget(self.cancelButton)
			controlLayout.addWidget(self.killButton)
		
		controlLayout.addStretch()

		self.updateButton = QPushButton("Update")
		self.connect(self.updateButton, SIGNAL("clicked()"), self.updateFromSource)
		controlLayout.addWidget(self.updateButton)

		self.deleteLogsButton = QPushButton("Delete logs")
		self.connect(self.deleteLogsButton, SIGNAL("clicked()"), self.deleteLogs)
		self.deleteLogsAndCloseButton = QPushButton("Close (delete logs)")
		self.connect(self.deleteLogsAndCloseButton, SIGNAL("clicked()"), self.deleteLogsAndClose)

		if not self.standalone:
			controlLayout.addWidget(self.deleteLogsButton)
			controlLayout.addWidget(self.deleteLogsAndCloseButton)

		self.closeButton = QPushButton("Close (keep logs)")
		self.connect(self.closeButton, SIGNAL("clicked()"), self.close)
		controlLayout.addWidget(self.closeButton)

		layout.addLayout(controlLayout)

		if not self.standalone:
			layout.addWidget(self.statusLabel)

		self.setLayout(layout)

	def killJob(self):
		getProxy().sendSignal(self.jobId, "kill")
	
	def cancelJob(self):
		getProxy().sendSignal(self.jobId, "cancel")
	
	def pauseOrResumeJob(self):
		if self.jobState == 'paused':
			sig = 'resume'
		else:
			sig = 'pause'
		getProxy().sendSignal(self.jobId, sig)

	def updateControls(self):
		"""
		Updates the possible controls according to the different job states.
		"""
		# Status label
		self.statusLabel.setText(self.jobState)
		# Pause button
		if self.jobState in [ 'running' ]:
			self.pauseButton.setEnabled(True)
			self.pauseButton.setText("Pause")
		elif self.jobState in [ 'paused' ]:
			self.pauseButton.setEnabled(True)
			self.pauseButton.setText("Resume")
		else:
			self.pauseButton.setEnabled(False)
		# Kill button
		if self.jobState in [ 'running', 'paused', 'cancelling' ]:
			self.killButton.setEnabled(True)
		else:
			self.killButton.setEnabled(False)
		# Cancel button
		if self.jobState in [ 'running' ]:
			self.cancelButton.setEnabled(True)
		else:
			self.cancelButton.setEnabled(False)

		# Log deletion options		
		if self.isJobCompleted():
			self.deleteLogsAndCloseButton.setEnabled(True)
			self.deleteLogsButton.setEnabled(True)
		else:
			self.deleteLogsAndCloseButton.setEnabled(False)
			self.deleteLogsButton.setEnabled(False)
			
	def setJobState(self, state):
		self.jobState = state
		self.updateControls()
		if self.isJobCompleted():
			self.onJobStopped()

	def isRealtimeMode(self):
		if self.jobId:
			return True
		return False
	
	def isJobCompleted(self):
		if self.isRealtimeMode():
			return self.jobState in [ 'complete', 'completed', 'killed', 'cancelled', 'error' ]
		else:
			return True

	def onSubscribedEvent(self, notification):
		"""
		Dispatches a Xc event to the interesting local sub-system:
		real-time control, or log parser.
		
		@type  notification: TestermanClient.Notification
		@param notification: a Xc notification related to the subscribed job URI.
		"""
		if notification.getMethod() == "LOG":
			self._logModel.feedXmlEvent(notification.getApplicationBody())
		elif notification.getMethod() == "JOB-EVENT":
			info = notification.getApplicationBody()
			if info.has_key('state'):
				self.setJobState(info['state'])

	def setTracking(self, tracking):
		self.visualLogView.setTracking(tracking)
		self.textualLogView.setTracking(tracking)
		self.testCaseView.setTracking(tracking)
		self.trackingActivated = tracking

	def onJobStopped(self):
		"""
		Switch to offline mode: enables log deletion, fill the parameters we missed to do it.
		"""
		# We only do something if we are in online mode.
		if self.isRealtimeMode():
			serverIp, serverPort = getProxy().getServerAddress()
			url = "testerman://%s:%d%s" % (serverIp, serverPort, getProxy().getJobLogFilename(self.jobId))
			self._url = QUrl(url)
			# switch to offline mode
			self.jobId = None
			self.updateWindowTitle()

	def deleteLogs(self):
		Actions.deleteAssociatedFiles(unicode(self._url.path()), selectAssociatedFiles = True)

	def deleteLogsAndClose(self):
		Actions.deleteAssociatedFiles(unicode(self._url.path()), force = True, selectAssociatedFiles = True)
		self.close()

	def updateFromSource(self):
		"""
		Retrieve the logs from the source where they should be retrieved from:
		- Testerman server: current (existing, running or not) job logs
		- Testerman server: archived logs / Remote file
		- Local file.
		"""
		log("Updating logs from source...")

		self.summary.clear()
		self._logModel.clear()
		state = 'n/a'
		logfile = ""
		try:
			if self.isRealtimeMode():
				log("Updating from server: hot log from job %d..." % self.jobId)
				logfile = getProxy().getJobLog(self.jobId)
				jobInfo = getProxy().getJobInfo(self.jobId)
				if jobInfo and jobInfo.has_key('state'):
					state = jobInfo['state']
			else:
				logfile = loadLog(self._url)

		except Exception, e:
			QMessageBox.information(self, getClientName(), "Unable to retrieve log: either the logfile has been deleted or the job cannot be found on this server (%s)" % str(e))
			return

		self.setJobState(state)

		# When updating logs, we disable the tracking to speed up things
		tracking = self.trackingActivated
		self.setTracking(False)
		self.setLog(logfile)
		self.setTracking(tracking)

	def onTestCaseItemChanged(self, newItem, previousItem):
		"""
		A new item has been selected in the TestCase treeview.
		
		Updates the current textual and visual views with the
		selected item log elements.
		"""
		if newItem:
			if not self.trackingActivated:
				transient = WTransientWindow("Log Viewer", self)
				transient.showTextLabel("Preparing views...")
			log("DEBUG: Preparing...")
			self.textualLogView.clearLog()
			log("DEBUG: text cleared")
			self.textualLogView.displayPartialLog(newItem.getElements())
			log("DEBUG: text prepared")
			self.visualLogView.clearLog()
			log("DEBUG: visual cleared")
			self.visualLogView.displayPartialLog(newItem.getElements())
			log("DEBUG: visual prepared")
			if not self.trackingActivated:
				transient.hide()
				transient.setParent(None)
			log("DEBUG: Selected OK")

	def setLog(self, xmlLog):
		log("Loading log...")
		start = time.time()
		ret = self.setLog_Dom(xmlLog)
		log("Loading duration: %s" % (time.time() - start))
		return ret

	def setLog_Dom(self, xmlLog):
		"""
		Takes an XML log content, parses it,
		creates DOM nodes and forwards them to analysers, to
		simulate a real-time log event feeding for them.
	
		@type  xmlLog: string (utf-8)
		@param xmlLog: the log content to parse, well formed XML string
		"""
		transient = WTransientWindow("Log Viewer", self)
		transient.showTextLabel("Parsing logs...")

		log("Parsing logs...")
		xmlDoc = QtXml.QDomDocument()
		(res, errormessage, errorline, errorcol) = xmlDoc.setContent(xmlLog, 0)
		log("Logs parsed, DOM constructed")
		transient.hide()

		previousSelectedItemIndex = None
		if res:
			transient.showTextLabel("Clearing views...")
			log("Clearing views...")
			# Context preservation: if a TestCase was selected, we'll have to select it after the update.
			# FIXME: need a correct support now that the test case view is a tree
			if self.testCaseView.currentItem():
				previousSelectedItemIndex = self.testCaseView.indexOfTopLevelItem(self.testCaseView.currentItem())
			self.testCaseView.clearLog()
			self.rawView.clearLog()
			for view in self.reportViews:
				view.clearLog()

			transient.hide()
			log("Analyzing events...")
			root = xmlDoc.documentElement()
			# Additional progress bar
			nbChildren = root.childNodes().count()
			progress = QProgressDialog("Analyzing log file...", "Cancel", 0, nbChildren, self)
			progress.setWindowTitle("Log Viewer")

			element = root.firstChildElement()
			count = 0
			onePercent = max(1, nbChildren / 100)
			while not element.isNull() and not progress.wasCanceled():
				self._logModel.feedEvent(element)
				count += 1
				if not ((count - 1) % onePercent):
					progress.setValue(count)
					QApplication.instance().processEvents()
				element = element.nextSiblingElement()

			# Enable to drop the self -> progress reference, and thus free the QProgressDialog.
			progress.setParent(None)
		else:
			log("Parsing error: " + str(errormessage) + 'at line ' + str(errorline) + ' col ' + str(errorcol))

		transient.showTextLabel("Preparing views...")
		log("Preparing views...")
		self.testCaseView.displayLog()
		if previousSelectedItemIndex is not None:
			self.testCaseView.setCurrentItem(self.testCaseView.topLevelItem(previousSelectedItemIndex))
		# This should switch to a "onEvent" raw view feeding
		if self.useRawView:
			self.rawView.setLog(xmlLog)
		for view in self.reportViews:
			view.displayLog()
		transient.hide()
		transient.setParent(None)
		log("View displayed")

	def closeEvent(self, event):
		"""
		Reimplementated from QWidget.
		
		When the window is closed, make sure we unsubscribe to our
		subscribed events, if any.
		"""
		log("LogViewer window closed.")
		if self.eventMonitor:
			self.eventMonitor.unsubscribe()
		# PyQt special: this enables to drop the parent -> this widget reference.
		# As a consequence, the widget instance will be garbage collected correctly.
		self.setParent(None)
		QWidget.closeEvent(self, event)

	def onActionRequested(self, message, timeout):
		# Only display a user input in realtime mode
		if self.isRealtimeMode():
			self.actionRequestedDialog = QMessageBox(self)
			self.actionRequestedDialog.addButton(QMessageBox.Ok)
			self.actionRequestedDialog.setText(message)
			self.actionRequestedDialog.setInformativeText("(or wait %.3fs)" % timeout)
			self.actionRequestedDialog.setWindowTitle("User action requested")
			if self.actionRequestedDialog.exec_() == QMessageBox.Ok:
				getProxy().sendSignal(self.jobId, "action_performed")
			self.actionRequestedDialog = None
	
	def onActionCleared(self):
		if self.actionRequestedDialog:
			self.actionRequestedDialog.reject()
		self.actionRequestedDialog = None


###############################################################################
# Textual Log View: item and treewidget
###############################################################################

class TextualLogItem(QTreeWidgetItem):
	"""
	An entry in the Textual log viewer is in fact an entry in a table (time, label).
	The whole entry is formatted according to the item itself (start, stop, succes, etc)
	and is clickable, triggering different actions according to the item (show message {mis}matching, ...)
	"""
	def __init__(self, parent, domElement):
		"""
		xmlLogLineDoc is an Testerman2 xml log line already parsed into a QDomElement.
		"""
		QTreeWidgetItem.__init__(self, parent)
		self.columns = [ 'time', 'class', 'message' ]
		self._domElement = domElement

		#: event timestamp, humain readable, QString
		self._timestamp = None
		#: event class, QString in [ 'internal', 'system', 'event' ]
		self._class = None
		#: the message to display when displaying the item, QString
		self._message = None
		#: the associated data to show when activating the item, buffer or QString
		self._associatedData = None
		#: is the associated data binary / non-printable or not ?
		self._binary = False
		#: element name/tag, QString
		self._element = None
	
	def isBinary(self):
		return self._binary
	
	def getAssociatedData(self):
		return self._associatedData

	def _setAssociatedData(self, data, binary = False):
		if binary:
			self._associatedData = QByteArray(base64.decodestring(data))
			self._binary = True
		else:
			self._associatedData = data
			self._binary = False

	def parse(self):
		"""
		Interprets the embedded domElement and prepare the item properties accordingly,
		i.e. everything needed for data() role equivalents,
		and associated action in case of an item selection/activation.
		"""
		self._timestamp = QString(formatTimestamp(float(self._domElement.attribute("timestamp"))))
		self._class = self._domElement.attribute("class")
		self._element = self._domElement.tagName()

		# According to the element, prepare different formats
		if self._element == "internal":
			self._message = self._domElement.text()

		elif self._element == "user":
			f = self.font(2)
			f.setItalic(1)
			self.setFont(2, f)
			msg = self._domElement
			if self._domElement.attribute("encoding") == "base64":
				self._setAssociatedData(msg.text(), binary = True)
				display = "[binary]"
			else:
				display = msg.text()
			self._message = display

		# Message events
		elif self._element == "message-sent":
			self._message = "%s.%s --> %s.%s" % ( self._domElement.attribute('from-tc'), self._domElement.attribute('from-port'), self._domElement.attribute('to-tc'), self._domElement.attribute('to-port'))

		# System message events
		elif self._element == "system-sent":
			tsiPort = self._domElement.attribute('tsi-port')
			if not self._domElement.firstChildElement('label').isNull():
				message = "%s >>> %s" % (tsiPort, self._domElement.firstChildElement('label').text()) # Short description
			else:
				message = "%s >>> <sent payload>" % tsiPort
			if not self._domElement.firstChildElement('sut-address').isNull():
				message += ' to %s' % self._domElement.firstChildElement('sut-address').text()
			self._message = message
			payloadElement = self._domElement.firstChildElement('payload')
			self._setAssociatedData(self._domElement.firstChildElement('payload').text(), payloadElement.attribute("encoding") == "base64")
		elif self._element == "system-received":
			tsiPort = self._domElement.attribute('tsi-port')
			if not self._domElement.firstChildElement('label').isNull():
				message = "%s <<< %s" % (tsiPort, self._domElement.firstChildElement('label').text()) # Short description
			else:
				message = "%s <<< <received payload>" % tsiPort
			if not self._domElement.firstChildElement('sut-address').isNull():
				message += ' from %s' % self._domElement.firstChildElement('sut-address').text()
			self._message = message
			payloadElement = self._domElement.firstChildElement('payload')
			self._setAssociatedData(self._domElement.firstChildElement('payload').text(), payloadElement.attribute("encoding") == "base64")

		# Timer events
		elif self._element == "timer-created":
			# We should discard this
			self._message = "Timer %s created on TC %s" % (self._domElement.attribute('id'), self._domElement.attribute('tc'))
		elif self._element == "timer-started":
			self._message = "Timer %s started (%s) on TC %s" % (self._domElement.attribute('id'), self._domElement.attribute('duration'), self._domElement.attribute('tc'))
		elif self._element == "timer-stopped":
			self._message = "Timer %s stopped on TC %s" % (self._domElement.attribute('id'), self._domElement.attribute('tc'))
		elif self._element == "timer-expiry":
			self._message = "Timer %s timeout on TC %s" % (self._domElement.attribute('id'), self._domElement.attribute('tc'))

		# TC events
		elif self._element == "tc-created":
			self._message = "TC %s created" % self._domElement.attribute('id')
		elif self._element == "tc-started":
			self._message = "PTC %s started with Behaviour %s" % (self._domElement.attribute('id'), self._domElement.attribute('behaviour'))
		elif self._element == "tc-stopped":
			verdict = self._domElement.attribute('verdict')
			self._message = "PTC %s stopped, local verdict is %s" % (self._domElement.attribute('id'), verdict)
			# According to the verdict, display different colors.
			if verdict == "pass":
				self.setForeground(2, QBrush(QColor(Qt.blue)))
			elif verdict == "fail":
				self.setForeground(2, QBrush(QColor(Qt.red)))
			else:
				self.setForeground(2, QBrush(QColor(Qt.darkRed)))

		# Template matching events
		elif self._element == "template-match":
			self._message = "Template match on port %s.%s" % (self._domElement.attribute('tc'), self._domElement.attribute('port'))
			message = self._domElement.firstChildElement('message')
			template = self._domElement.firstChildElement('template')
			self.setForeground(2, QBrush(QColor(Qt.green)))
		elif self._element == "template-mismatch":
			self._message = "Template mismatch on port %s.%s" % (self._domElement.attribute('tc'), self._domElement.attribute('port'))
			message = self._domElement.firstChildElement('message')
			template = self._domElement.firstChildElement('template')
			self.setForeground(2, QBrush(QColor(Qt.red)))
		elif self._element == "timeout-branch":
			self._message = "Timeout match for Timer %s" % (self._domElement.attribute('id'))
			self.setForeground(2, QBrush(QColor(Qt.green)))
		elif self._element == "killed-branch":
			self._message = "Killed match for TC %s" % (self._domElement.attribute('id'))
			self.setForeground(2, QBrush(QColor(Qt.green)))
		elif self._element == "done-branch":
			self._message = "Done match for TC %s" % (self._domElement.attribute('id'))
			self.setForeground(2, QBrush(QColor(Qt.green)))

		# TestCase events
		elif self._element == "testcase-created":
			# Discarded in this viewer for now.
			self._class = "discarded"
			self._message = "TestCase %s (%s) created" % (self._domElement.attribute('id'), self._domElement.text())
		elif self._element == "verdict-updated":
			# Discarded in this viewer for now.
			self._class = "discarded"
			self._message = "TC local verdict updated to %s on %s" % (self._domElement.attribute('verdict'), self._domElement.attribute('tc'))
		elif self._element == "testcase-started":
			self._message = "TestCase %s (%s) started" % (self._domElement.attribute('id'), self._domElement.text())
			f = self.font(2)
			f.setBold(True)
			self.setFont(2, f)
		elif self._element == "testcase-stopped":
			verdict = self._domElement.attribute('verdict')
			self._message = "TestCase %s stopped, final verdict is %s" % (self._domElement.attribute('id'), verdict)
			f = self.font(2)
			f.setBold(True)
			self.setFont(2, f)
			# According to the verdict, display different colors.
			if verdict == "pass":
				self.setForeground(2, QBrush(QColor(Qt.blue)))
			elif verdict == "fail":
				self.setForeground(2, QBrush(QColor(Qt.red)))
			else:
				self.setForeground(2, QBrush(QColor(Qt.darkRed)))

		# ATS events
		elif self._element == "ats-started":
			self._message = "ATS started"
			f = self.font(2)
			f.setBold(True)
			self.setFont(2, f)
		elif self._element == "ats-stopped":
			result = int(self._domElement.attribute('result'))
			message = self._domElement.text()
			if message.isEmpty():
				self._message = "ATS stopped, result %s" % result
			else:
				self._message = "ATS stopped, result %s\n%s" % (result, message)
			f = self.font(2)
			f.setBold(True)
			self.setFont(2, f)
			if result == 0:
				self.setForeground(2, QBrush(QColor(Qt.blue)))
			else:
				self.setForeground(2, QBrush(QColor(Qt.darkRed)))

		# Actions
		elif self._element == "action-requested":
			self._message = "User action requested by TC %s: %s, timeout %s" % (self._domElement.attribute('tc'), self._domElement.firstChildElement('message').text(), self._domElement.attribute('timeout'))
		elif self._element == "action-cleared":
			self._message = "User action performed (or assumed to be performed)"
	
		# Unhandled events
		else:
			self._message = "Unhandled log element: %s" % self._element

		self.setText(0, self._timestamp)
		self.setText(1, self._class)
		self.setText(2, self._message)
		self.setTextAlignment(0, Qt.AlignTop)
		self.setTextAlignment(1, Qt.AlignTop)
		self.setTextAlignment(2, Qt.AlignTop)

	def onSelected(self):
		if self._element == "message-sent":
			self.treeWidget().emit(SIGNAL("messageSelected(QDomElement)"), self._domElement.firstChildElement('message'))
		elif self._element == "template-match":
			self.treeWidget().emit(SIGNAL("templateMatchSelected(QDomElement, QDomElement)"), self._domElement.firstChildElement('message'), self._domElement.firstChildElement('template'))
		elif self._element == "template-mismatch":
			self.treeWidget().emit(SIGNAL("templateMisMatchSelected(QDomElement, QDomElement)"), self._domElement.firstChildElement('message'), self._domElement.firstChildElement('template'))

	def applyFilter(self, hiddenLogClasses = []):
		"""
		If current class is in the hidden classes, we hide it, otherwise we
		make the item reappears.
		"""
		if self._class in hiddenLogClasses:
			self.setHidden(1)
		else:
			self.setHidden(0)

class WTextualLogView(QTreeWidget):
	"""
	A log viewer that can be updated regularly (append mode)
	that displays the logs as rich text, with filters.
	"""
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self.currentHiddenLogClasses = [ "internal", "discarded" ]
		settings = QSettings()
		self.trackingActivated = settings.value('logs/autotracking', QVariant(True)).toBool()
		self.__createWidgets()
		self.__createActions()

	def setTracking(self, tracking):
		self.trackingActivated = tracking

	def __createWidgets(self):
		self.root = self.invisibleRootItem()
		self.setRootIsDecorated(False)
		self.labels = [ 'time', 'class', 'message' ]
		labels = QStringList()
		for l in self.labels:
			labels.append(l)
		self.setHeaderLabels(labels)
		self.setColumnWidth(0, 130) # "time" sizing - well.. it may depends on the font
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.connect(self, SIGNAL("customContextMenuRequested(const QPoint&)"), self.onPopupMenu)
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
		self.connect(self, SIGNAL("currentItemChanged(QTreeWidgetItem*, QTreeWidgetItem*)"), self.onCurrentItemChanged)

	def __createActions(self):
		# logClass togglers
		self.toggleDisplayClassActions = []
		for logClass in [ "internal", "event", "user" ]:
			action = QAction("Display " + logClass + " related logs", self)
			action.setCheckable(True)
			action.setToolTip("Display/hide %s logs" % logClass)
			if not (logClass in self.currentHiddenLogClasses):
				action.setChecked(True)
			# I'm unable to make a connection correctly work with a lambda using a string as fixed param, sorry.
			self.connect(action, SIGNAL("toggled(bool)"), getattr(self, "onToggledAction_" + logClass))
			self.toggleDisplayClassActions.append(action)

	def onToggledAction_event(self, b):
		self.onToggledAction("event", b)

	def onToggledAction_user(self, b):
		self.onToggledAction("user", b)

	def onToggledAction_internal(self, b):
		self.onToggledAction("internal", b)

	def createContextMenu(self):
		contextMenu = QMenu("Textual log viewer", self)
		# Widget-level contextual menu
		for action in self.toggleDisplayClassActions:
			contextMenu.addAction(action)
		return contextMenu

	def onPopupMenu(self, pos):
		self.createContextMenu().popup(QCursor.pos())

	def onToggledAction(self, logClass, checked):
		log("Levels updated for %s, %s" % (logClass, str(checked)))
		# not checked, i.e. we hide it.
		if not checked:
			self.currentHiddenLogClasses.append(logClass)
		else:
			try:
				self.currentHiddenLogClasses.remove(logClass)
			except:
				pass
		self.applyFilter(self.currentHiddenLogClasses)

	def onItemActivated(self, item, col):
		"""
		Displays the text into a text view.
		"""
		data = item.getAssociatedData()
		if data:
			# We have an associated value
			dialog = WValueDialog(title = "Value details", data = data, binary = item.isBinary(), parent = self)
			dialog.exec_()
		else:
			# No associated value, just display the log line completely
			text = item.text(2)
			dialog = WTextEditDialog(text, "Log line details", 1, self)
			dialog.exec_()

	def onCurrentItemChanged(self, newItem, previousItem):
		"""
		May display additional info related to the current log item.
		Delegates to the item the ability to emit a signal.
		"""
		if newItem:
			newItem.onSelected()

	def clearLog(self):
		self.clear()

	def displayPartialLog(self, domElements):
		"""
		Feeds a list of dom elements that corresponds to
		a portion of a log file.
		
		@type  domElements: list of QDomElement
		"""
		log("DEBUG: starting display...")
		item = None
		for domElement in domElements:
			item = TextualLogItem(None, domElement)
			self.root.addChild(item)
			item.parse()
		log("DEBUG: applying filter display...")
		self.applyFilter(self.currentHiddenLogClasses)
		log("DEBUG: filter applied display...")

		if self.trackingActivated and item:
			self.scrollToItem(item)
		log("DEBUG: ok, displayed...")

	def onEvent(self, domElement):
		"""
		Realtime feeding.
		"""
		self.append(domElement)

	def append(self, domElement):
		"""
		Appends a new Testerman log event already formatted as a QDomElement
		to the view.
		"""
		item = TextualLogItem(None, domElement)
		self.root.addChild(item)
		item.parse()
		item.applyFilter(self.currentHiddenLogClasses)
		if self.trackingActivated:
			self.scrollToItem(item)

	def applyFilter(self, hiddenLogClasses = []):
		"""
		Hide/Unhide items according to the filter
		"""
		for i in range(0, self.root.childCount()):
			self.root.child(i).applyFilter(hiddenLogClasses)

	
###############################################################################
# TestCase View (tree of ats/testcases mapped to the underlying log models)
###############################################################################

class TestCaseItem(QTreeWidgetItem):
	"""
	Represents a TestCase in the TestCase tree view.
	Maps a TestCaseLogModel object.
	"""
	def __init__(self, model, parent):
		QTreeWidgetItem.__init__(self, parent)
		self.setText(0, model.getId())
		self.setIcon(0, icon(':/icons/testcase'))
		self._model = model

	def getElements(self):
		"""
		Returns a list of elements corresponding to this test case
		"""
		return self._model.getDomElements()

	def setComplete(self):
		verdict = self._model.getVerdict()
		if verdict == "pass":
			self.setForeground(0, QBrush(QColor(Qt.blue)))
			self.setIcon(0, icon(':/icons/job-success.png'))
		elif verdict == "fail":
			self.setForeground(0, QBrush(QColor(Qt.red)))
			self.setIcon(0, icon(':/icons/job-error.png'))
		else:
			self.setForeground(0, QBrush(QColor(Qt.darkRed)))
			self.setIcon(0, icon(':/icons/job-warning.png'))

class AtsItem(QTreeWidgetItem):
	"""
	Represents an ATS in the TestCase tree view.
	Maps a AtsLogModel object.
	"""
	def __init__(self, model, parent):
		QTreeWidgetItem.__init__(self, parent)
		self.setIcon(0, icon(':/icons/ats'))
		self.setText(0, model.getId())
		self.setExpanded(True)
		self._model = model

	def setComplete(self):
		result = self._model.getResult()
		if result == 0:
			self.setIcon(0, icon(':/icons/job-success.png'))
			self.setForeground(0, QBrush(QColor(Qt.blue)))
		elif result == 1: # Cancelled
			self.setIcon(0, icon(':/icons/job-warning.png'))
			self.setForeground(0, QBrush(QColor(Qt.darkRed)))
		else:
			self.setIcon(0, icon(':/icons/job-error.png'))
			self.setForeground(0, QBrush(QColor(Qt.darkRed)))

	def getElements(self):
		"""
		Returns a list of elements corresponding to this item
		"""
		return self._model.getDomElements()

class WTestCaseView(QTreeWidget):
	"""
	This widget lists the TestCases, colorizing them according to their status.

	Acts as a domElement dispatcher that dispatches a read domElement
	to the associated test case. 
	Each test case is directly represented by a TestCaseView Item that
	stores the domElements for the test case.
	"""
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self.__createWidgets()
		self.__createActions()
		self.__currentItem = None
		self._currentAts = None
		self.trackingActivated = False

	def setTracking(self, tracking):
		self.trackingActivated = tracking

	def __createWidgets(self):
		self.labels = [ 'Testcase' ]
		labels = QStringList()
		for l in self.labels:
			labels.append(l)
		self.setHeaderLabels(labels)
		self.setColumnWidth(0, 200) # well.. it may depends on the font
		self.setContextMenuPolicy(Qt.CustomContextMenu)

	def __createActions(self):
		pass

	def createContextMenu(self):
		contextMenu = QMenu("Tescases", self)
		return contextMenu

	def onPopupMenu(self, pos):
		self.createContextMenu().popup(QCursor.pos())

	def clearLog(self):
		self.clear()
		self._items = []
		gc.collect()

	def displayLog(self):
		pass

	def onAtsStarted(self, atsLogModel):
		item = AtsItem(atsLogModel, self)
		self._currentAts = item
		self.__currentItem = item
#		self._mapping[atsLogModel] = item
	
	def onAtsStopped(self, atsLogModel):
		self._currentAts.setComplete()
		self._currentAts = None
		self.__currentItem = None
#		self._mapping[atsLogModel].setComplete()
	
	def onTestCaseStarted(self, testCaseLogModel):
		item = TestCaseItem(testCaseLogModel, self._currentAts)
		self.__currentItem = item
#		self._mapping[testCaseLogModel] = item

	def onTestCaseStopped(self, testCaseLogModel):
		self.__currentItem.setComplete()
		self.__currentItem = None
#		self._mapping[testCaseLogModel].setComplete()
		
	def onEvent(self, domElement):
		# If we are currently watching a tree item (i.e. an item is selected),
		# forward the event to the view to display it.
		if self.currentItem() and not self.currentItem()._model.isComplete():
			self.emit(SIGNAL("testermanEvent(QDomElement)"), domElement)
