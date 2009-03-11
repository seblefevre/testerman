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
# Some useful, often used enhanced widgets.
#
##

from Base import *

import binascii
import base64
import pickle

from PyQt4.Qt import *


################################################################################
# Convenience function: simple message boxes
################################################################################

def userError(parent, txt):
	QMessageBox.warning(parent, getClientName(), txt, QMessageBox.Ok, QMessageBox.Ok)

def systemError(parent, txt):
	QMessageBox.warning(parent, getClientName(), txt, QMessageBox.Ok, QMessageBox.Ok)

def userInformation(parent, txt):
	QMessageBox.information(parent, getClientName(), txt, QMessageBox.Ok, QMessageBox.Ok)


################################################################################
# QActions-related convenience functions
################################################################################

class TestermanAction(QAction):
	def __init__(self, parent, label, callback, tip = None, shortcut = None):
		QAction.__init__(self, label, parent)
		if tip: self.setStatusTip(tip)
		if shortcut: self.setShortcut(shortcut)
		self.connect(self, SIGNAL("triggered()"), callback)

class TestermanCheckableAction(QAction):
	def __init__(self, parent, label, callback, tip = None, shortcut = None):
		QAction.__init__(self, label, parent)
		self.setCheckable(1)
		if tip: self.setStatusTip(tip)
		if shortcut: self.setShortcut(shortcut)
		self.connect(self, SIGNAL("toggled(bool)"), callback)


################################################################################
# Message of the Day dialog
################################################################################

class WMessageOfTheDayDialog(QDialog):
	"""
	Message of the day (MOTD) display dialog.
	A read-only text editor with an acknowledgement box.
	"""
	def __init__(self, text, displayCheckBox = True, parent = None, size = None):
		QDialog.__init__(self, parent)
		self.text = text
		self.displayCheckBox = displayCheckBox
		self.__createWidgets()
		size = QSize(650, 400) # an arbitraty default size - matches 80 courier 8 characters in width, however.
		self.resize(size)

	def __createWidgets(self):
		self.setWindowTitle("Message of the Day")

		layout = QVBoxLayout()

		self.textEdit = QTextEdit(self)
		self.textEdit.setPlainText(self.text)
		self.textEdit.setReadOnly(True)
		font = QFont("courier", 8)
		font.setFixedPitch(True)
		self.textEdit.setFont(font)

		layout.addWidget(self.textEdit)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.checkBox = QCheckBox("Do not show this MOTD again")
		if self.displayCheckBox:
			buttonLayout.addWidget(self.checkBox)
		self.closeButton = QPushButton("Close", self)
		self.connect(self.closeButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self.closeButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)
	
	def getChecked(self):
		return self.checkBox.isChecked()


################################################################################
# Text Edit, RW or RO - convenience dialog
################################################################################

class WTextEditDialog(QDialog):
	"""
	A basic Text Edit modal dialog.
	May be read-only or not.
	Useful for Description/prerequisites edition, or release notes viewing, ...
	"""
	def __init__(self, text, title, readOnly = 0, parent = None, size = None, fixedFont = False):
		QDialog.__init__(self, parent)
		self.readOnly = readOnly
		self.text = text
		self.title = title
		self.__createWidgets()
		if fixedFont:
			defaultFont = QFont("courier", 8)
			defaultFont.setFixedPitch(True)
			self.textEdit.setFont(defaultFont)
		if not size:
			size = QSize(600, 400) # an arbitraty default size
		self.resize(size)

	def __createWidgets(self):
		self.setWindowTitle(self.title)

		layout = QVBoxLayout()

		self.textEdit = QTextEdit(self)
		self.textEdit.setPlainText(self.text)
		self.textEdit.setReadOnly(self.readOnly)
		layout.addWidget(self.textEdit)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		if self.readOnly:
			self.closeButton = QPushButton("Close", self)
			self.connect(self.closeButton, SIGNAL("clicked()"), self.reject)
			buttonLayout.addWidget(self.closeButton)
		else:
			self.okButton = QPushButton("Ok", self)
			self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
			self.cancelButton = QPushButton("Cancel", self)
			self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
			buttonLayout.addWidget(self.okButton)
			buttonLayout.addWidget(self.cancelButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def getText(self):
		return self.textEdit.toPlainText()


################################################################################
# WValueDialog - displays a value in binary and text format
################################################################################

class WValueDialog(QDialog):
	"""
	Read-only.
	Provides 2 tabs: one with text/printable view, the other one is binary.
	"""
	def __init__(self, title = "Value details", data = None, binary = False, size = None, parent = None):
		"""
		You must either provide binaryData (buffer) or textData (unicode)
		
		@type  data: QString or QByteArray
		@param data: the data to display
		@type  binary: bool
		@param binary: if True, data data is a QByteArray If False, data is a QString
		"""
		QDialog.__init__(self, parent)

		self.readOnly = True
		self.title = title

		self.unicodeDisplay = '<text display not supported for binary values>'
		
		if not binary:
			# We display the binary representation of the data converted to UTF-8
			self.binaryDisplay = getHexaDisplay(str(data.toUtf8()))
			self.unicodeDisplay = data
		else:
			# data is a QByteArray
			self.binaryDisplay = getHexaDisplay(str(data))
			self.unicodeDisplay = getPrintableString(str(data))

		self.__createWidgets()

		if binary:
			self.tab.setCurrentWidget(self.binaryTextEdit)
		else:
			self.tab.setCurrentWidget(self.unicodeTextEdit)

		if not size:
			size = QSize(600, 400) # an arbitraty default size
		self.resize(size)

	def __createWidgets(self):
		self.setWindowTitle(self.title)

		layout = QVBoxLayout()

		self.tab = QTabWidget()
		self.unicodeTextEdit = QTextEdit()
		self.unicodeTextEdit.setPlainText(self.unicodeDisplay)
		self.unicodeTextEdit.setReadOnly(True)
		self.tab.addTab(self.unicodeTextEdit, "Text")

		self.binaryTextEdit = QTextEdit()
		self.binaryTextEdit.setPlainText(self.binaryDisplay)
		self.binaryTextEdit.setReadOnly(True)
		self.tab.addTab(self.binaryTextEdit, "Binary")

		layout.addWidget(self.tab)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.closeButton = QPushButton("Close", self)
		self.connect(self.closeButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self.closeButton)
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

		defaultFont = QFont("courier", 8)
		defaultFont.setFixedPitch(True)
		self.unicodeTextEdit.setFont(defaultFont)
		self.binaryTextEdit.setFont(defaultFont)


################################################################################
# Find/Replace dialog controlling a QSciScintilla widget
################################################################################

class WSciReplace(QDialog):
	"""
	A Classic Search/Replace dialog for a QsciScintilla widget
	"""
	def __init__(self, scintilla, parent = None): # the parent is the main window
		QDialog.__init__(self, parent)
		self.scintilla = scintilla
		self.firstSearch = True
		self.forward = True
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle(getClientName() + " Search/Replace")
		self.setWindowIcon(icon(':icons/testerman.png'))

		searchLayout = QGridLayout()
		searchLayout.addWidget(QLabel('Find:'), 0, 0, Qt.AlignRight)
		self.searchFor = QLineEdit()
		self.connect(self.searchFor, SIGNAL("textChanged(const QString&)"), self.onSearchForTextChanged)
		searchLayout.addWidget(self.searchFor, 0, 1)
		searchLayout.addWidget(QLabel('Replace with:'), 1, 0, Qt.AlignRight)
		self.replaceWith = QLineEdit()
		searchLayout.addWidget(self.replaceWith, 1, 1)

		self.options = QGroupBox("Options")
		optionLayout = QVBoxLayout()
		self.caseSensitive = QCheckBox("Case sensitive", self.options)
		self.connect(self.caseSensitive, SIGNAL('stateChanged(int)'), self.onOptionUpdated)
		optionLayout.addWidget(self.caseSensitive)
		self.regExp = QCheckBox("Regular expression", self.options)
		self.connect(self.regExp, SIGNAL('stateChanged(int)'), self.onOptionUpdated)
		optionLayout.addWidget(self.regExp)
		self.wordOnly = QCheckBox("Word only", self.options)
		self.connect(self.wordOnly, SIGNAL('stateChanged(int)'), self.onOptionUpdated)
		optionLayout.addWidget(self.wordOnly)
		self.options.setLayout(optionLayout)
		searchLayout.addWidget(self.options, 2, 0, 1, 2)

		layout = QVBoxLayout()
		layout.addLayout(searchLayout)
		layout.addStretch()

		# Buttons
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.nextButton = QPushButton("Next", self)
		self.connect(self.nextButton, SIGNAL("clicked()"), self.next)
		buttonLayout.addWidget(self.nextButton)
		self.previousButton = QPushButton("Previous", self)
		self.connect(self.previousButton, SIGNAL("clicked()"), self.previous)
		buttonLayout.addWidget(self.previousButton)
		self.replaceButton = QPushButton("Replace", self)
		self.connect(self.replaceButton, SIGNAL("clicked()"), self.replace)
		buttonLayout.addWidget(self.replaceButton)
		self.replaceAllButton = QPushButton("Replace All", self)
		self.connect(self.replaceAllButton, SIGNAL("clicked()"), self.replaceAll)
		buttonLayout.addWidget(self.replaceAllButton)
		self.cancelButton = QPushButton("Close", self)
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self.cancelButton)

		layout.addLayout(buttonLayout)
		self.setLayout(layout)
		self.searchFor.setFocus()

	def onSearchForTextChanged(self, txt):
		self.firstSearch = True

	def onOptionUpdated(self, newState):
		self.firstSearch = True

	def next(self):
		self.find(self.searchFor.text())

	def previous(self):
		self.find(self.searchFor.text(), forward = False)

	def replace(self):
		"""
		Replace - only if a selection exists.
		"""
		self.scintilla.replace(self.replaceWith.text())

	def replaceAll(self):
		"""
		Replace all occurences
		"""
		i = 0
		# WARNING: may loop if replacing "something" with "somethingElse" ?
		# Or does qsciscintilla.find return false if we wrapped once ?

		currentLine, currentIndex = self.scintilla.getCursorPosition()
		self.scintilla.beginUndoAction()

		self.firstSearch = True
		while self.find(self.searchFor.text(), singlePass = True):
			self.scintilla.replace(self.replaceWith.text())
			i += 1

		self.scintilla.setCursorPosition(currentLine, currentIndex)
		self.scintilla.endUndoAction()

		self.firstSearch = True
		QMessageBox.information(self, getClientName(), "qtTesterman has completed its search and has made " +  str(i) + " replacement(s).", QMessageBox.Ok)

	def find(self, text, singlePass = False, forward = True):
		"""
		Return True if the text was found, False otherwise.

		if singlePass is True, no wrapping over the document, but start from the beginning (useful for replace all)
		"""
		caseSensitive = self.caseSensitive.isChecked()
		regExp = self.regExp.isChecked()
		wordOnly = self.wordOnly.isChecked()
		if not text.length():
			return False
		if self.firstSearch or self.forward != forward:
			# The index should be the selection.indexFrom, if a selection is done.
			# So we cannot leave the default index (the current cursor position, at the end of the selection)
			(lineFrom, indexFrom, lineTo, indexTo) = self.scintilla.getSelection()
			wrap = True
			if singlePass:
				wrap = False
				lineFrom = 0
				indexFrom = 0
			found = self.scintilla.findFirst(text, regExp, caseSensitive, wordOnly, wrap, forward, lineFrom, indexFrom)
			self.forward = forward
		else:
			found = self.scintilla.findNext()
		if found and self.firstSearch:
			self.firstSearch = False
		return found

	def reject(self):
		"""
		QDialog reimplementation.
		"""
		QDialog.reject(self)


################################################################################
# Find widget controlling a QSciScintilla widget, displayed at its bottom
################################################################################

class WSciFind(QWidget):
	"""
	Find widget, to associate to a QsciScintilla widget.
	
	It automatically register a Ctrl+F action on the QsciScintilla widget to get
	the focus on itself.
	"""
	def __init__(self, scintilla, parent = None):
		QWidget.__init__(self, parent)
		self.scintilla = scintilla
		self.__createWidgets()
		# This does not work...
		self.action = TestermanAction(self.scintilla, "Find", self.getFocus)
		self.action.setShortcut(Qt.CTRL + Qt.Key_F)
		self.action.setShortcutContext(Qt.WidgetShortcut)
		self.scintilla.addAction(self.action)
		self.isCopyAvailable = False
		self.firstSearch = False
		self.forwardSearch = True

	def __createWidgets(self):
		layout = QHBoxLayout()
		layout.setMargin(0)
		layout.addWidget(QLabel("Find:", self))
		self.findLineEdit = QLineEdit(self)
		self.connect(self.findLineEdit, SIGNAL('textChanged(const QString&)'), self.onTextChanged)
		self.connect(self.findLineEdit, SIGNAL('returnPressed()'), lambda:self.onNextClicked(True))
		self.connect(self.scintilla, SIGNAL('copyAvailable(bool)'), self.onCopyAvailableChange)
		layout.addWidget(self.findLineEdit)
		self.nextButton = QPushButton("Next", self)
		self.nextButton.setShortcut('F3')
		self.connect(self.nextButton, SIGNAL('clicked()'), lambda:self.onNextClicked(True))
		layout.addWidget(self.nextButton)
		self.previousButton = QPushButton("Previous", self)
		self.previousButton.setShortcut('Shift+F3')		
		self.connect(self.previousButton, SIGNAL('clicked()'), lambda:self.onNextClicked(False))
		layout.addWidget(self.previousButton)
		self.setLayout(layout)
		self.defaultPalette = QPalette(self.findLineEdit.palette())
		self.alternatePalette = QPalette(self.defaultPalette)
		self.alternatePalette.setColor(QPalette.Base, QColor(237, 203, 197))

	def getFocus(self):
		self.findLineEdit.selectAll()
		self.findLineEdit.setFocus(Qt.OtherFocusReason)

	def getAction(self):
		return self.action

	def find(self, text, caseSensitive = False, forward = True):
		if not text.length():
			self.findLineEdit.setPalette(self.defaultPalette)
			return
		if (self.firstSearch or self.forwardSearch != forward) or not forward:
			# The index should be the selection.indexFrom, if a selection is done.
			# So we cannot leave the default index (the current cursor position, at the end of the selection)
#			print "DEBUG: selection: " + str(self.scintilla.getSelection())
			(lineFrom, indexFrom, lineTo, indexTo) = self.scintilla.getSelection()
			if forward and not self.forwardSearch:
				indexFrom = indexTo
				lineFrom = lineTo
			found = self.scintilla.findFirst(text, False, caseSensitive, False, True, forward, lineFrom, indexFrom)			
			self.forwardSearch = forward
		else:			
			found = self.scintilla.findNext()
		if found:
			self.findLineEdit.setPalette(self.defaultPalette)
		else:
			self.findLineEdit.setPalette(self.alternatePalette)
		if found and self.firstSearch:
			self.firstSearch = False

	def onCopyAvailableChange(self, bool):
		self.isCopyAvailable = bool
		# Trick: if the user clicked somewhere on the QScintilla widget, it will lost
		# its possible selection due to a previous search (1), and, more importantly, will
		# update its new position to start for a possible next search.
		# CopyAvailableChange will switch to False in this case (1), so that we can
		# configure the Find widget to perform a first search on next iteration.
		# Normally, this should be done on a signal like "cursorPositionChanged", but not 
		# due to the automatic selection/highlight from a previous search.
		if not bool:
			self.firstSearch = True

	def onTextChanged(self, text):
		self.firstSearch = True
		self.find(text = text, forward = self.forwardSearch)

	def onNextClicked(self, forward):
		if self.isCopyAvailable:
			if self.firstSearch: 
				self.findLineEdit.setText(self.scintilla.selectedText())
			elif self.findLineEdit.text() == '':
				self.getFocus()
				return
		self.find(text = self.findLineEdit.text(), forward = forward)


################################################################################
# Find dialog controlling a QTextEdit, displayed at its bottom.
################################################################################

class WFind(QWidget):
	"""
	Find widget, to associate to a textEdit widget.
	
	It automatically register a Ctrl+F action on the textEdit widget to get
	the focus on itself.
	"""
	def __init__(self, textEdit, parent = None):
		QWidget.__init__(self, parent)
		self.textEdit = textEdit
		self.__createWidgets()
		# This does not work...
		self.action = TestermanAction(self.textEdit, "Find", self.getFocus)
		self.action.setShortcut(Qt.CTRL + Qt.Key_F)
		self.action.setShortcutContext(Qt.WidgetShortcut)
		self.textEdit.addAction(self.action)
		self.isCopyAvailable = 0

	def __createWidgets(self):
		layout = QHBoxLayout()
		layout.setMargin(0)
		layout.addWidget(QLabel("Find:", self))
		self.findLineEdit = QLineEdit(self)
		self.connect(self.findLineEdit, SIGNAL('textChanged(const QString&)'), self.onTextChanged)
		#self.connect(self.findLineEdit, SIGNAL('editingFinished()'), self.onNextClicked)
		self.connect(self.textEdit, SIGNAL('copyAvailable(bool)'), self.onCopyAvailableChange)
		layout.addWidget(self.findLineEdit)
		self.nextButton = QPushButton("Next", self)
		self.nextButton.setShortcut('F3')
		self.connect(self.nextButton, SIGNAL('clicked()'), self.onNextClicked)
		layout.addWidget(self.nextButton)
		self.setLayout(layout)
		self.defaultPalette = QPalette(self.findLineEdit.palette())
		self.alternatePalette = QPalette(self.defaultPalette)
		self.alternatePalette.setColor(QPalette.Base, QColor(237, 203, 197))

	def getFocus(self):
		self.findLineEdit.selectAll()
		self.findLineEdit.grabKeyboard()
		self.findLineEdit.setFocus(Qt.OtherFocusReason)

	def getAction(self):
		return self.action

	def find(self, text, excludeCurrentSelection = 1):
		if not text.length():
			self.findLineEdit.setPalette(self.defaultPalette)
			return
		if excludeCurrentSelection:
			# Starts after the end of the selection (ideal for "next")
			cursor = self.textEdit.document().find(text, self.textEdit.textCursor())
		else:
			# Starts from the beginning of the selection (ideal for incremental)
			cursor = self.textEdit.document().find(text, self.textEdit.textCursor().selectionStart())
		if cursor.isNull():
			# we make a second try starting at the beginning
			cursor = self.textEdit.document().find(text, 0)
		if not cursor.isNull():
			self.textEdit.setTextCursor(cursor)
			self.findLineEdit.setPalette(self.defaultPalette)
		else:
			self.findLineEdit.setPalette(self.alternatePalette)

	def onCopyAvailableChange(self, bool):
		self.isCopyAvailable = bool

	def onTextChanged(self, text):
		self.find(text, 0)

	def onNextClicked(self):
		if self.isCopyAvailable:
			self.textEdit.copy()
			self.findLineEdit.setText('')
			self.findLineEdit.paste()
		elif self.findLineEdit.text() == '':
			self.getFocus()
			return
		self.find(self.findLineEdit.text())


################################################################################
# Convenience widget that embeds a widget into a QGroupBox
################################################################################

class WGroupBox(QGroupBox):
	"""
	Utility class to embed a widget within a group box easily
	"""
	def __init__(self, title, widget, parent = None):
		QGroupBox.__init__(self, title, parent)
		layout = QVBoxLayout()
		layout.addWidget(widget)
		layout.setMargin(0)
		self.setLayout(layout)


################################################################################
# Enhanced QTabWidget
################################################################################

class WEnhancedTabWidget(QTabWidget):
	"""
	Utility widget.

	Slightly enhanced tab widget with:
	- close button support
	- automatic tab name renaming in case of duplicata
	- send a signal "tabCountChanged" whenever a tab is added/removed
	- send a closeCurrentTab signal when clicking on the close button
	"""
	def __init__(self, parent = None):
		QTabWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.closeAction = TestermanAction(self, 'Close', self.closeCurrent, 'Close current document')
		self.closeAction.setIcon(icon(':/icons/file-close.png'))
		self.closeButton = QToolButton(self)
		self.closeButton.setDefaultAction(self.closeAction)
		self.closeButton.setAutoRaise(1)
		self.setCornerWidget(self.closeButton)
		self.connect(self, SIGNAL('currentChanged(int)'), self.onTabChanged)
#		self.nextTabAction = TestermanAction(self, '', self.nextTab, 'Next document', 'Ctrl+Key_Tab')
#		self.previousTabAction = TestermanAction(self, '', self.previousTab, 'Previous document', 'Ctrl+Shift+Key_Tab')

	def onTabChanged(self, index):
		url = QTabWidget.widget(self, self.currentIndex()).model.getUrl()
		QApplication.instance().get('gui.statusbar').setFileLocation(url)
	
	def closeCurrent(self):
		self.emit(SIGNAL('closeCurrentTab()'))

	def tabRemoved(self, index):
		"""
		Reimplemented from QTabWidget to send a signal.
		"""
		self.emit(SIGNAL('tabCountChanged()'))
		return QTabWidget.tabRemoved(self, index)

	def tabInserted(self, index):
		"""
		Reimplemented from QTabWidget to send a signal.
		"""
		self.emit(SIGNAL('tabCountChanged()'))
		return QTabWidget.tabInserted(self, index)

	def getClosestTabText(self, index, text):
		"""
		Return the text with a possible numbering suffix ("(2)", etc) if duplicate text in tab title exists.
		"""
		i = self.count()
		tabTexts = []
		while i:
			i -= 1
			if i != index: tabTexts.append(self.tabText(i))
		
		textAttempt = text
		i = 2
		while textAttempt in tabTexts:
			textAttempt = text + ' (%d)' % i
			i += 1
		return textAttempt 
		
	def setTabText(self, index, text, modified = 0):
		"""
		This modified version adds a possible numbering ("(2)", etc) if duplicate text exists.
		This is purely display, and does not affect any data model.
		"""
		name = self.getClosestTabText(index, text)
		if modified:
			QTabBar.setTabTextColor(self.tabBar(), index, QColor("red"))
			return QTabWidget.setTabText(self, index, name + '*')
		QTabBar.setTabTextColor(self.tabBar(), index, QColor("black"))
		return QTabWidget.setTabText(self, index, name)

	def addTab(self, child, text):
		return QTabWidget.addTab(self, child, self.getClosestTabText(-1, text))

	def addTab(self, child, icon, text):
		return QTabWidget.addTab(self, child, icon, self.getClosestTabText(-1, text))

#	def nextTab(self):
#		"""
#		Activate the next (to the right) tab (wrap to the first one to the left)
#		"""
#		print "DEBUG: nexttab"
#		index = self.currentIndex()
#		index = (index + 1) % self.count()
#		if self.currentIndex() != index: self.setCurrentIndex(index)
#
#	def previousTab(self):
#		"""
#		Activate the previous (to the left) tab (wrap to the first one to the right)
#		"""
#		print "DEBUG: previoustab"
#		index = self.currentIndex()
#		index = (index - 1 + self.count()) % self.count()
#		if self.currentIndex() != index: self.setCurrentIndex(index)


################################################################################
# Enhanced Delete Confirmation dialog
################################################################################

class WDeleteFileConfirmation(QDialog):
	"""
	Display a confirmation dialog (Yes/No) with an additional checkable options used to display additional possible deletions
	(e.g. "Delete ATS file too", or "Delete all related logs", etc)
	"""
	def __init__(self, label, checkBox = (None, False), parent = None):
		"""
		checkBox is a tuple (label, checkedByDefault)
		"""
		QDialog.__init__(self, parent)
		self.__createWidgets(label, checkBox)
	
	def __createWidgets(self, label, checkBox):
		self.title = "Remove file"
		
		(checkBoxLabel, checkBoxChecked) = checkBox
		
		layout = QVBoxLayout()

		layout.addWidget(QLabel(label))
		
		self.checkBox = None
		if checkBoxLabel:
			self.checkBox = QCheckBox(checkBoxLabel)
			self.checkBox.setChecked(checkBoxChecked)
			layout.addWidget(self.checkBox)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.okButton = QPushButton("Yes", self)
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self.okButton)
		self.cancelButton = QPushButton("No", self)
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self.cancelButton)
		buttonLayout.addStretch()
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def checkBoxChecked(self):
		if self.checkBox:
			return self.checkBox.isChecked()
		return 0

################################################################################
# Enhanced Question dialog
################################################################################

class WUserQuestion(QDialog):
	"""
	Display a confirmation dialog (Yes/No) 
	with a additional checkable options.
	(e.g. "Delete ATS file too", or "Delete all related logs", etc)
	"""
	def __init__(self, title, question, checkBoxes = [], parent = None):
		"""
		@type  title: string
		@param title: the title of the dialog box
		@type  question: string
		@param question: the label of the question to ask
		@type  checkBoxes: list of (string, bool)
		@param checkBoxes: a list of (label, checked) for additional checkboxes
		                   to display
		
		use isChecked(index) to get the check state of a checkbox once 
		the dialog has been accepted.
		"""
		QDialog.__init__(self, parent)
		self._checkBoxes = []
		self.__createWidgets(title, question, checkBoxes)
	
	def __createWidgets(self, title, question, checkBoxes):
		self.setWindowTitle(title)

		layout = QVBoxLayout()
		layout.addWidget(QLabel(question))
		for (label, checked) in checkBoxes:
			cb = QCheckBox(label)
			cb.setChecked(checked)
			layout.addWidget(cb)
			self._checkBoxes.append(cb)

		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		self.okButton = QPushButton("Yes", self)
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		buttonLayout.addWidget(self.okButton)
		self.cancelButton = QPushButton("No", self)
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addWidget(self.cancelButton)
		buttonLayout.addStretch()
		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def isChecked(self, index):
		if index < len(self._checkBoxes):
			return self._checkBoxes[index].isChecked()
		else:
			return False

################################################################################
# Message + Template viewer
################################################################################

class WMixedTemplateView(QSplitter):
	"""
	A high level widget that is able to display:
	- a single template View for message viewing
	- a double tempalte View for match/mismatch viewing
	"""
	def __init__(self, parent = None):
		QSplitter.__init__(self, parent)
		self.__createWidget()

	def __createWidget(self):
		self.templateViewLeft = WTemplateView(self)
		self.templateViewRight = WTemplateView(self)
		self.addWidget(self.templateViewLeft)
		self.addWidget(self.templateViewRight)

	def setTemplates(self, template1, template2 = None):
		self.templateViewLeft.setTemplate(template1)
		self.templateViewRight.setTemplate(template2)

def getHexaDisplay(data):
	"""
	@param data is an array of bytes / a string with non-ascii characters.
	Returns an ascii string displaying data as if it was hexdumped.
	"""
	hexa = binascii.b2a_hex(data)
	ret = ""
	i = 0
	while i < len(hexa):
		ret += hexa[i]
		i += 1
		if not (i % 2):
			ret += " "
		if not (i % 32):
			ret += "| "
#			log("debug: displaying %d to %d..." % ( ((i-1) / 32) * 32, i))
			for j in range(((i-1) / 32) * 32, i, 2):
				c = data[j / 2]
				if ord(c) < 127 and ord(c) > 31:
					ret += c
				else:
					ret += "."
			ret += "\n"

	if (i % 32):
		# Let's pad: remaining 32 - (i % 32) characters to display
		nb = 32 - (i % 32)
		ret += nb / 2 * '   '
		ret += "| "
		for j in range(((i-1) / 32) * 32, i, 2):
			c = data[j / 2]
			if ord(c) < 127 and ord(c) > 31:
				ret += c
			else:
				ret += "."
		ret += "\n"

#	log("DEBUG:" + ret)
	return ret

def getPrintableString(data):
	"""
	@type data: buffer (string)
	@param data:
	
	@rtype: string
	@returns: a displayable string based on data, where non-displayable characters have been filtered out
	
	"""
	import string
	return filter(lambda x: x in string.printable, data)


class QTemplateWidgetItem(QTreeWidgetItem):
	"""
	A message/template item to use in a WTemplateView tree.
	
	Contains 3 pieces of information:
	- a name  (col 0)
	- a value (col 1)
	- a type  (col 2)
	"""
	def __init__(self, parent = None):
		QTreeWidgetItem.__init__(self, parent)
		self.setText(2, '') # by default, the type is unspecified
		self.setExpanded(True)
		self.setTextAlignment(1, Qt.AlignTop)
		self._binaryValue = None
	
	def setName(self, name):
		self.setText(0, name)
	
	def setType(self, type_):
		self.setText(2, type_)
	
	def setBinaryValue(self, value):
		"""
		@type  value: QByteArray
		"""
		self.setValue("(contains binary data)") # actually, this is "contains non-utf-8 data"
		self._binaryValue = value
		self.setType('octetstring')
	
	def getBinaryValue(self):
		"""
		@rtype: QByteArray
		"""
		return self._binaryValue
	
	def getValue(self):
		return self.text(1)
	
	def setValue(self, value):
		self.setText(1, value)
	
	def hasBinaryValue(self):
		if self._binaryValue:
			return True
		else:
			return False

class WTemplateView(QTreeWidget):
	"""
	This widget vizualises a template/message.
	Two columns: name, value (no type in Testerman).
	Everything is expanded by default.

	This is the base widget to build a template/message comparator.
	"""
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		self.templateElement = None
		self.__createWidgets()

	def __createWidgets(self):
		self.setRootIsDecorated(1)
		self.setHeaderLabels([ 'name', 'value', 'type' ])
		self.setSortingEnabled(True)
		self.header().setSortIndicator(0, Qt.AscendingOrder)
		self.header().setClickable(True)
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)

	def setTemplate(self, templateElement):
		"""
		@type templateElement: QDomElement

		It correspond to <message>...</message> or <template>...</template>
		with a sub element for each value.
		"""
		self.templateElement = templateElement
		self.clear()

		if templateElement:
			# We build the tree the typical way (recursive)
			self.__createItem(self, templateElement)
		self.resizeColumnToContents(0)
		self.sortItems(self.sortColumn(), Qt.AscendingOrder)

	def __createItem(self, parent, element, suggestedName = None):
		"""
		Recursive function to create a tree of QTemplateWidgetItem.
		
		@type  element: QDomElement
		@param element: the element to turn into a node
		@type  parent: QTemplateWidgetItem or QTreeWidget
		@param parent: the parent of the node to create
		@type  suggestedName: string
		@param suggestedName: an optional name overriding the one autodetecting from the element
		
		@rtype: QTemplateWidgetItem
		@returns: a node, with children if needed.
		"""

		tag = element.tagName()

		# Special handling for list, since we should override their child node names		
		if tag == 'l': # list
			parent.setType('list')
			child = element.firstChildElement()
			count = 0
			while not child.isNull():
				self.__createItem(parent, child, '(%s)' % count)
				child = child.nextSiblingElement()
				count += 1
			return parent

		# All other are treated the same way
		elif tag == 'r': # record/dict
			parent.setType('record')
			item = parent
		elif tag == 'f': # field in a record
			name = element.attribute('n') # name of the field
			item = QTemplateWidgetItem(parent)
			item.setName(name)		
		elif tag == 'i': # item in a list
			name = suggestedName
			item = QTemplateWidgetItem(parent)
			item.setName(name)		
		elif tag == 'c': # choice/union
			parent.setType('choice')
			name = element.attribute('n') # name of the choice
			item = QTemplateWidgetItem(parent)
			item.setName(name)		
			
		else: # Default behaviour - also for compatibility with previous log format (v1)
			name = tag
			item = QTemplateWidgetItem(parent)
			item.setName(name)		

		# Now, do we have some structured elements as a child ?
		if element.firstChildElement().isNull():
			# No - this is a leaf node
			if element.attribute("encoding") == "base64":
				item.setBinaryValue(QByteArray(base64.decodestring(element.text())))
			else:
				item.setValue(element.text())
		else:
			# We have a structure node below (normally only one - lists have been handled above)
			child = element.firstChildElement()
			while not child.isNull():
				self.__createItem(item, child)
				child = child.nextSiblingElement()

		return item

	def onItemActivated(self, item, col):
		try:
			if item.hasBinaryValue():
				dialog = WValueDialog(data = item.getBinaryValue(), binary = True, parent = self)
			else:
				dialog = WValueDialog(data = item.getValue(), binary = False, parent = self)
			dialog.exec_()

		except Exception, e:
			print str(e)


###############################################################################
# Transient Window for simple user feedbacks
###############################################################################

class WTransientWindow(QDialog):
	"""
	A simple widget used to provide the user with a feedback on an action.
	Like a QProgressDialog, but without the ProgressBar.
	"""
	def __init__(self, title = "", parent = None):
		QDialog.__init__(self, parent)
		self.setWindowTitle(title)
		self.__createWidgets()

	def __createWidgets(self):
		self.resize(QSize(200, 93))
		self.setModal(False)
		layout = QHBoxLayout(self)
		self.label = QLabel()
		layout.addWidget(self.label, 0, Qt.AlignHCenter | Qt.AlignVCenter)
		self.setLayout(layout)

	def setLabelText(self, txt):
		self.label.setText(txt)

	def showTextLabel(self, txt):
		self.label.setText(txt)
		self.show()
		QApplication.instance().processEvents()


###############################################################################
# MIME data
###############################################################################

def mimeDataToObjects(mimeType, mimeData):
	"""
	Create object from mime data
	
	@type  mimeType: string
	@param mimeType: type of the mime (i.e. application/x-qtesterman-parameters)
	@type  mimeData: QMimeData object
	@param mimeData: MIME data to convert
	
	@rtype: variant or None
	@return: the object if success, or None in case of error
	"""
	if not mimeData.hasFormat(mimeType):
		return None
	data = mimeData.data(mimeType)
	if not data:
		return None
	try:
		objects = pickle.loads(data.data())
		return objects
	except Exception, e:
		log("DEBUG: unable to deserialize %s mime data: %s" % (mimeType, str(e)))
		return None

def objectsToMimeData(mimeType, object):
	"""
	Create object from mime data
	
	@type  mimeType: string
	@param mimeType: type of the mime (i.e. application/x-qtesterman-parameters)
	@type  object: variant
	@param mimeData: object to convert (can be a list, a dict, a string, ...)
	
	@rtype: QMimeData object
	@return: QMimeData associated to object
	"""
	mimeData = QMimeData()
	mimeData.setData(mimeType, pickle.dumps(object))
	return mimeData
