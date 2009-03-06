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
from EventMonitor import *
from CommonWidgets import *
from VisualLogView import WVisualTestCaseView
import Actions
import PluginManager

import gc
import sys
import os.path
import base64

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
		for l in [ 'nbPass', 'ratioPass', 'nb', 'nbFail', 'ratioFail' ]:
			self.labels[l] = QLabel()

		layout = QGridLayout()
		layout.addWidget(QLabel("Performed testcases:"), 0, 0)
		layout.addWidget(self.labels['nb'], 0, 1)
		layout.addWidget(QLabel("Number of OK:"), 1, 0)
		layout.addWidget(self.labels['nbPass'], 1, 1)
		layout.addWidget(self.labels['ratioPass'], 1, 2)
		layout.addWidget(QLabel("Number of NOK:"), 2, 0)
		layout.addWidget(self.labels['nbFail'], 2, 1)
		layout.addWidget(self.labels['ratioFail'], 2, 2)
		layout.setColumnStretch(0, 0)
		layout.setColumnStretch(1, 0)
		layout.setColumnStretch(2, 20)
		self.setLayout(layout)

	def onTestCaseStopped(self, verdict, element):
		self.total += 1
		if verdict == "pass":
			self.totalOK += 1
		else:
			self.totalKO += 1
		self.updateStats()

	def onAtsStarted(self, element):
		self.clear()

	def clear(self):
		self.total = 0
		self.totalOK = 0
		self.totalKO = 0
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

###############################################################################
# Raw log viewer
###############################################################################

class WRawLogView(QWidget):
	"""
	A simple composite widget with a read-only text edit, and an option to save
	and find things.
	"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()
		
	def __createWidgets(self):
		layout = QVBoxLayout()
		self.textEdit = QTextEdit()
		self.textEdit.setReadOnly(True)
#		font = self.textEdit.font()
#		font.setFixedPitch(True)
#		self.textEdit.setFont(font)
		self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
		self.textEdit.setUndoRedoEnabled(False)

		layout.addWidget(self.textEdit)

		optionLayout = QHBoxLayout()
		optionLayout.addWidget(WFind(self.textEdit))
		self.saveButton = QPushButton("Save as...")
		self.connect(self.saveButton, SIGNAL('clicked()'), self.saveAs)
		optionLayout.addWidget(self.saveButton)

		layout.addLayout(optionLayout)

		self.setLayout(layout)

	def saveAs(self):
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
			f = open(filename, 'w')
			f.write(self.textEdit.toPlainText())
			f.close()
			QMessageBox.information(self, getClientName(), "Execution log saved successfully.", QMessageBox.Ok)
			return True
		except Exception, e:
			systemError(self, "Unable to save file as %s: %s" % (filename, unicode(e)))
			return False

	def clearLog(self):
		self.textEdit.clear()

	def setLog(self, txt):
		self.textEdit.setPlainText(txt)

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
		self.actionRequiredDialog = None
		
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
		log("DEBUG: opening %s" % unicode(url.toString()))
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
		self.eventMonitor = EventMonitor(parent = self)
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
		# Inner objects (non widget)
		self.eventMonitor = None
		self.logParser = LogParser()

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
		self.visualLogView = WVisualTestCaseView()
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
				self.reportViews.append(view)
				self.reportTab.addTab(view, label)

		self.perspectiveTab.addTab(self.reportTab, "Report")

		# Perspective: Advanced (Raw log)
		self.rawView = WRawLogView()

		self.perspectiveTab.addTab(self.rawView, "Raw log")

		# Connection on parser
		self.connect(self.logParser, SIGNAL("testermanEvent(QDomElement)"), self.testCaseView.onEvent)
		for view in self.reportViews:
			self.connect(self.logParser, SIGNAL("testermanEvent(QDomElement)"), view.onEvent)

		# Summary connection on parser
		self.connect(self.logParser, SIGNAL("testCaseStopped(QString, QDomElement)"), self.summary.onTestCaseStopped)

		# Action management
		self.connect(self.logParser, SIGNAL("actionRequired(QString, float)"), self.onActionRequired)
		self.connect(self.logParser, SIGNAL("actionCleared()"), self.onActionCleared)

		# Inter widget connections
		self.connect(self.textualLogView, SIGNAL("messageSelected(QDomElement)"), self.templateView.setTemplates)
		self.connect(self.textualLogView, SIGNAL("templateMisMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)
		self.connect(self.textualLogView, SIGNAL("templateMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)

		self.connect(self.visualLogView, SIGNAL("messageSelected(QDomElement)"), self.templateView.setTemplates)
		self.connect(self.visualLogView, SIGNAL("templateMisMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)
		self.connect(self.visualLogView, SIGNAL("templateMatchSelected(QDomElement, QDomElement)"), self.templateView.setTemplates)

		self.connect(self.testCaseView, SIGNAL("currentItemChanged(QTreeWidgetItem*, QTreeWidgetItem*)"), self.onTestCaseItemChanged)
		# The Test Case view also "forward" domElement in case of an event arriving while the item corresponding to the updated TestCase is selected
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
		if self.jobState in [ 'running', 'paused' ]:
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
		return True

	def onSubscribedEvent(self, event):
		"""
		Event is a TestermanClient.Event.
		Dispatch the event to the interesting sub-system: real-time control, or log parser.
		"""
		if event.getMethod() == "LOG":
			self.logParser.onLogEvent(event)
		elif event.getMethod() == "JOB-EVENT":
			info = event.getApplicationBody()
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
		state = 'n/a'
		logfile = ""
		try:
			if self.isRealtimeMode():
				log("Updating from server: hot log from job %d..." % self.jobId)
				logfile = getProxy().getJobLog(self.jobId)
				jobInfo = getProxy().getJobInfo(self.jobId)
				if jobInfo and jobInfo.has_key('state'):
					state = jobInfo['state']

			elif self._url.scheme() == "file": # local file
				log("Updating from local file %s..." % self._url.path())
				f = open(unicode(self._url.path()), 'r')
				logfile = f.read()
				f.close()
				# If this is not a real xml file but a "log" file, add some basic xml headers.
				# We should find something more reliable... and more efficient
				if not logfile.startswith('<?xml'):
					logfile = '<?xml version="1.0" encoding="utf-8" ?><ats>%s</ats>' % logfile

			else: # remote file
				log("Updating from server: remote file %s..." % self._url.path())
				logfile = '<?xml version="1.0" encoding="utf-8" ?><ats>%s</ats>' % getProxy().getFile(unicode(self._url.path()))

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
		if newItem:
			if not self.trackingActivated:
				transient = WTransientWindow("Log Viewer", self)
				transient.showTextLabel("Preparing views...")
			self.textualLogView.clearLog()
			self.textualLogView.displayPartialLog(newItem.domElements)
			self.visualLogView.clearLog()
			self.visualLogView.displayPartialLog(newItem.domElements)
			if not self.trackingActivated:
				transient.hide()
				transient.setParent(None)

	def setLog(self, xmlLog):
		return self.setLog_Dom(xmlLog)

	def setLog_Sax(self, xmlLog):
		"""
		A SAX version of log parsing to generate local testerman log events to
		analyzers and viewers.

		Surprinsingly, this is much slower that the DOM version, but costs
		a little bit less memory.
		
		The current implementation is not optimized at all, and looks a bit awkward:
		we re-create a QDomElement for interesting elements by serializing what have been parsed by the SAX parser
		into a XML string, and reparsing the result string into a QDomElement using the DOM parser.
		A better solution is probably
		- to create the QDomElement manually (adding elements depending on SAX events)
		- or use an internal structure instead of a QDomElement for all loggers and plugins
		  (i.e. change the basic event type and onEvent signature).
		Since we still have to load the whole model into memory, whether it is a DOM or an internal model, using
		an internal model should not speed up things dramatically.

		So, creating the DOM node without passing by a xml re-serialization could be the best way to follow.
		"""
		class XmlLogHandler(QtXml.QXmlDefaultHandler):
			"""
			This content handler is able to create a QDomElement for each interesting parse XML elements,
			and calls a callback with the created QDomElement as the single param.
			"""
			def __init__(self, callback):
				QtXml.QXmlDefaultHandler.__init__(self)
				self.currentXmlEvent = None
				self.errorStr = QString()
				self.currentLevel = 0
				self.callback = callback

			def fatalError(self, exception):
				"""
				exception is a QXmlParseException
				"""
				print "Sorry, error: " + str(exception.message().toUtf8())
				return False

			def errorString(self):
				return self.errorStr

			def characters(self, s):
				"""
				QString
				"""
				if self.currentXmlEvent:
					self.currentXmlEvent += s
					pass
				return True

			def startElement(self, namespaceUri, localName, qName, attrs):
				"""
				QString
				QString
				QString
				QXmlAttributes

				Generate a QDomElement based on this element.
				"""
#				print "starting element " + str(qName.toUtf8())
				if self.currentLevel == 1:
		#			print "initializing new domElement..."
					self.currentXmlEvent = ''
				if self.currentLevel >= 1:
					self.currentXmlEvent += '<' + qName
					for i in range(0, attrs.count()):
						self.currentXmlEvent += ' %s="%s"' % (attrs.qName(i).toUtf8(), attrs.value(i).toUtf8())
					self.currentXmlEvent += '>'
				self.currentLevel += 1
				return True

			def endElement(self, namespaceUri, localName, qName):
				self.currentLevel -= 1
#				print "ending element " + str(qName.toUtf8()) + "level %d" % self.currentLevel
				if self.currentLevel >= 1:
					self.currentXmlEvent += '</' + qName + '>'
				if self.currentLevel == 1:
					# Now that we have a new reserialized XML string, parse it using the DOM parser
					self.currentXmlEvent = '<?xml version="1.0" encoding="utf-8" ?>' + self.currentXmlEvent
#					print self.currentDomElement.toUtf8()
					xmlDoc = QtXml.QDomDocument()
					(res, errormessage, errorline, errorcol) = xmlDoc.setContent(self.currentXmlEvent, 0)
					if res:
						# Theorically, since the SAX parser parsed it, the currentXmLEvent should be parsable to create the DomElement.
						self.callback(xmlDoc.documentElement())
					self.currentXmlEvent = None

				return True


		transient = WTransientWindow("Log Viewer", self)

		transient.showTextLabel("Clearing views...")
		log("Clearing views...")
		# Context preservation: if a TestCase was selected, we'll have to select it after the update.
		previousSelectedItemIndex = None
		if self.testCaseView.currentItem():
			previousSelectedItemIndex = self.testCaseView.indexOfTopLevelItem(self.testCaseView.currentItem())
		self.testCaseView.clear()
		self.rawView.clearLog()
		for view in self.reportViews:
			view.clearLog()

		transient.showTextLabel("Parsing & analysing events...")

		log("Parsing & analysing events...")
		xlr = QtXml.QXmlSimpleReader()
		xis = QtXml.QXmlInputSource()
		xis.setData(xmlLog)
		xlh = XmlLogHandler(self.logParser.onEvent)
		xlr.setContentHandler(xlh)
		log("Parsing...")
		res = xlr.parse(xis, False)
		log("Parsed, res " + str(res))
		transient.hide()

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



	def setLog_Dom(self, xmlLog):
		"""
		Let's format a new log.
		xmlLog is a string text.

		We always replay the log as if it was in realTime.
		"""
		transient = WTransientWindow("Log Viewer", self)
		transient.showTextLabel("Parsing logs...")

		log("Parsing logs...")
		xmlDoc = QtXml.QDomDocument()
		(res, errormessage, errorline, errorcol) = xmlDoc.setContent(xmlLog, 0)
		transient.hide()

		previousSelectedItemIndex = None
		if res:
			transient.showTextLabel("Clearing views...")
			log("Clearing views...")
			# Context preservation: if a TestCase was selected, we'll have to select it after the update.
			if self.testCaseView.currentItem():
				previousSelectedItemIndex = self.testCaseView.indexOfTopLevelItem(self.testCaseView.currentItem())
			self.testCaseView.clear()
			self.rawView.clearLog()
			for view in self.reportViews:
				view.clearLog()

			transient.hide()
			log("Analyzing events...")
			root = xmlDoc.documentElement()
			# Additional progress bar
			progress = QProgressDialog("Analyzing log file...", "Cancel", 0, root.childNodes().count(), self)
			progress.setWindowTitle("Log Viewer")
#			progress.setWindowModality(Qt.WindowModal) # useful ?

			element = root.firstChildElement()
			count = 0
			while not element.isNull() and not progress.wasCanceled():
				self.logParser.onEvent(element)
				count += 1
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
		Reimplementation from QWidget. (does not work at WMonitor level ?!)
		"""
		log("LogViewer window closed.")
		if self.eventMonitor:
			self.eventMonitor.unsubscribe()
		# PyQt special: this enables to drop the parent -> this widget reference.
		# As a consequence, the widget instance will be garbage collected correctly.
		self.setParent(None)
		QWidget.closeEvent(self, event)
#		event.accept()

	def onActionRequired(self, message, timeout):
		# Only display a user input in realtime mode
		if self.isRealtimeMode():
			self.actionRequiredDialog = QMessageBox(self)
			self.actionRequiredDialog.addButton(QMessageBox.Ok)
			self.actionRequiredDialog.setText(message)
			self.actionRequiredDialog.setInformativeText("(or wait %.3fs)" % timeout)
			self.actionRequiredDialog.setWindowTitle("User action requested")
			if self.actionRequiredDialog.exec_() == QMessageBox.Ok:
				getProxy().sendSignal(self.jobId, "action_performed")
			self.actionRequiredDialog = None
	
	def onActionCleared(self):
		if self.actionRequiredDialog:
			self.actionRequiredDialog.reject()
		self.actionRequiredDialog = None

###############################################################################
# Textual Log View: item and treewidget
###############################################################################


class WTextualLogViewItem(QTreeWidgetItem):
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

		# According to the element, prepare different formatters
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
				self._message = "%s >>> %s" % (tsiPort, self._domElement.firstChildElement('label').text()) # Short description
			else:
				self._message = "%s >>> <sent payload>" % tsiPort
			payloadElement = self._domElement.firstChildElement('payload')
			self._setAssociatedData(self._domElement.firstChildElement('payload').text(), payloadElement.attribute("encoding") == "base64")
		elif self._element == "system-received":
			tsiPort = self._domElement.attribute('tsi-port')
			if not self._domElement.firstChildElement('label').isNull():
				self._message = "%s <<< %s" % (tsiPort, self._domElement.firstChildElement('label').text()) # Short description
			else:
				self._message = "%s <<< <received payload>" % tsiPort

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
			f.setBold(1)
			self.setFont(2, f)
		elif self._element == "testcase-stopped":
			verdict = self._domElement.attribute('verdict')
			self._message = "TestCase %s stopped, final verdict is %s" % (self._domElement.attribute('id'), verdict)
			f = self.font(2)
			f.setBold(1)
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
		elif self._element == "ats-stopped":
			result = self._domElement.attribute('result')
			self._message = "ATS stopped, result " + result

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

	emit:
	templateMisMatchSelected(QDomElement, QDomElement)
	templateMatchSelected(QDomElement, QDomElement)
	messageSelected(QDomElement)
	atsStarted()
	atsStopped()
	testCaseStopped(QString verdict)
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
		print "DEBUG: levels updated for %s, %s" % (logClass, str(checked))
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
		Display the text into a text view.
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
		Display elements between first and last (included)
		"""
		for e in domElements:
			item = WTextualLogViewItem(None, e)
			self.root.addChild(item)
			item.parse()

		self.applyFilter(self.currentHiddenLogClasses)

	def onEvent(self, event):
		# event is a QDomElement
		self.append(event)

	def append(self, xmlDomElement):
		"""
		Online/real-time view: let's add a new xml log line to our log.
		xmlDoc is an Testerman2 xml log line parsed into a QDomElement. <$(class) time="...">$(parameters, serialized in xml)<//$(class)>
		"""
		item = WTextualLogViewItem(None, xmlDomElement)
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
# LogParser - inner object emitting interesting event signals
###############################################################################

################################################################################
# Event formatting
################################################################################

previousts = ''
eventCount = 0

formatDomTime = 0.0

def printStats():
	print "Time spent to format xml to domElement: " + str(formatDomTime)

def formatEventToDomElement(event):
	"""
	event is TestermanClient.Event.
	First format to XML, then parse it to a DomElement.
	Returns the domElement.
	"""
	global formatDomTime, formatXmlTime

	xmlLogLine = event.getBody() # contains XML data

	# First we parse the logline into an xml Doc
	start = time.clock()
	xmlDoc = QtXml.QDomDocument()
	(res, errormessage, errorline, errorcol) = xmlDoc.setContent(xmlLogLine, 0)
	stop = time.clock()
	formatDomTime += (stop - start)
	if res:
		return xmlDoc.documentElement()
	else:
		print "WARNING: Unable to xml-parse xmlLogLine: " + str(errormessage)
		return None

class LogParser(QObject):
	"""
	This Object is responsible for parsing an XML log or a new event
	and generates appropriate SIGNAL events according to the XML event.
	Widgets connect to this parser to be informed of new events to display.
	The ability to emit some high-level, interesting signals avoids parsing these
	signals is some widgets.
	However, most widgets will also need to parsing other events. In this case,
	the event is simply "forwarded" as received, creating a useless indirection.
	(cost ?)

	Emit some high level signals:
	atsStarted(QDomElement)
	atsStopped(QString status, QDomElement)
	testCaseStarted(QString identifier, QDomElement)
	testCaseStopped(QString verdict, QDomElement)

	And a low level signal:
	testermanEvent(QDomElement element)
	...
	"""
	def __init__(self):
		QObject.__init__(self)

	def onLogEvent(self, event):
		"""
		event is TestermanClient.Event, representing an event as received on Ex interface.
		We parse it into a domElement, then we can emit higher level signals.
		"""
		domElement = formatEventToDomElement(event)
		if domElement:
			self.onEvent(domElement)

	def onEvent(self, domElement):
		"""
		For each XML element from the qt-parsed XML model, we analyze it and emits appropriated signals.
		"""

		eventType = domElement.tagName()
		
		if eventType == "ats-started":
			self.emit(SIGNAL("atsStarted(QDomElement)"), domElement)

		elif eventType == "ats-stopped":
			result = domElement.attribute('result')
			self.emit(SIGNAL("atsStopped(QString, QDomElement)"), QString(result), domElement)

		elif eventType == "testcase-created":
			identifier = domElement.attribute('id')
			self.emit(SIGNAL("testCaseCreated(QString, QDomElement)"), QString(identifier), domElement)

		elif eventType == "testcase-started":
			identifier = domElement.attribute('id')
			self.emit(SIGNAL("testCaseStarted(QString, QDomElement)"), QString(identifier), domElement)

		elif eventType == "testcase-stopped":
			verdict = domElement.attribute('verdict')
			self.emit(SIGNAL("testCaseStopped(QString, QDomElement)"), QString(verdict), domElement)

		elif eventType == "action-requested":
			timeout = float(domElement.attribute('timeout'))
			message = domElement.firstChildElement('message').text()
			self.emit(SIGNAL("actionRequired(QString, float)"), QString(message), timeout)

		elif eventType == "action-cleared":
			self.emit(SIGNAL("actionCleared()"))

		# In any case, emit the raw signal
		self.emit(SIGNAL('testermanEvent(QDomElement)'), domElement)

###############################################################################
# TestCase View (list)
###############################################################################

class WTestCaseView(QTreeWidget):
	"""
	This widget lists the TestCase, colorizing them according to their status.
	When a TestCase is selected, emits a signal:
	testCaseSelected(QXmlDomElement)
	where the element is the "testcase-started" Testerman Event XML element.
	"""
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self.__createWidgets()
		self.__createActions()
		self.__currentTestCaseItem = None
		self.trackingActivated = False

	def setTracking(self, tracking):
		self.trackingActivated = tracking

	def __createWidgets(self):
		self.setRootIsDecorated(False)
		self.labels = [ 'Testcase' ]
		labels = QStringList()
		for l in self.labels:
			labels.append(l)
		self.setHeaderLabels(labels)
		self.setColumnWidth(0, 180) # well.. it may depends on the font
		self.setContextMenuPolicy(Qt.CustomContextMenu)
#		self.connect(self, SIGNAL("customContextMenuRequested(const QPoint&)"), self.onPopupMenu)
#		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
#		self.connect(self, SIGNAL("currentItemChanged(QTreeWidgetItem*, QTreeWidgetItem*)"), self.onCurrentItemChanged)

	def __createActions(self):
		pass

	def createContextMenu(self):
		contextMenu = QMenu("Tescases", self)
		return contextMenu

	def onPopupMenu(self, pos):
		self.createContextMenu().popup(QCursor.pos())

	def clearLog(self):
		self.clear()

	def displayLog(self):
		pass

	def onEvent(self, domElement):
		"""
		Log event handler, as emitted by EventMonitor (parsed domElement)
		"""

		class WTestCaseTreeWidgetItem(QTreeWidgetItem):
			def __init__(self, parent):
				QTreeWidgetItem.__init__(self, parent)
				self.domElements = []
				self.finished = False # indicate if the TestCase corresponding to the node is over or not.

		eventType = domElement.tagName()

		if self.__currentTestCaseItem:
			self.__currentTestCaseItem.domElements.append(domElement)

		if self.currentItem() and not self.currentItem().finished:
			# If we selected an item whose corresponding testcase is not finished yet,
			# We should forward the domElement to the views as well for real time update
			# Note: in case of a missed "testcase-stopped" event, this creates garbages, of course.
			self.emit(SIGNAL("testermanEvent(QDomElement)"), domElement)

		# We intercept interesting events at Ats level: testcase start/stop events
		if eventType == "testcase-created":
			# Let's create a new node and view
			item = WTestCaseTreeWidgetItem(self)
			item.setText(0, domElement.attribute('id'))
			self.__currentTestCaseItem = item
			self.__currentTestCaseItem.domElements.append(domElement)
			# Automatic tracking
			# WARNING: this greatly decrease performance - due to signal emitting ?
			if self.trackingActivated:
				self.setCurrentItem(item)
		elif eventType == "testcase-stopped":
			verdict = domElement.attribute('verdict')
			if self.__currentTestCaseItem:
				# we update the color according to the verdict
				if verdict == "pass":
					self.__currentTestCaseItem.setForeground(0, QBrush(QColor(Qt.blue)))
				elif verdict == "fail":
					self.__currentTestCaseItem.setForeground(0, QBrush(QColor(Qt.red)))
				else:
					self.__currentTestCaseItem.setForeground(0, QBrush(QColor(Qt.darkRed)))
				self.__currentTestCaseItem.finished = True
				self.__currentTestCaseItem = None

