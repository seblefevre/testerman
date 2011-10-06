##
# A Compare widget that display the diff between two buffers.
#
#
# Mainly based on Eric4's CompareWidget widget
# Copyright (c) 2004 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#
##


from PyQt4 import QtCore, QtGui

import os
import sys
import re
from difflib import _mdiff, IS_CHARACTER_JUNK

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import Resources


################################################################################
# Local Icon Cache
################################################################################

#: may be shared in a common file.
#: however, copying it locally enables more independent modules.
class IconCache:
	def __init__(self):
		self._icons = {}

	def icon(self, resource):
		if not self._icons.has_key(resource):
			self._icons[resource] = QIcon(resource)
		return self._icons[resource]

TheIconCache = IconCache()

def icon(resource):
	return TheIconCache.icon(resource)


try:
	_fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
	_fromUtf8 = lambda s: s

class Ui_CompareWidget(object):
	def setupUi(self, CompareWidget):
		CompareWidget.setObjectName(_fromUtf8("CompareWidget"))
		CompareWidget.resize(950, 600)
		self.verticalLayout = QtGui.QVBoxLayout(CompareWidget)
		self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

		self.gridLayout = QtGui.QGridLayout()
		self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
		self.file1Label = QtGui.QLabel(CompareWidget)
		self.file1Label.setText(_fromUtf8(""))
		self.file1Label.setWordWrap(True)
		self.file1Label.setObjectName(_fromUtf8("file1Label"))
		self.gridLayout.addWidget(self.file1Label, 0, 0, 1, 1)
		self.file2Label = QtGui.QLabel(CompareWidget)
		self.file2Label.setText(_fromUtf8(""))
		self.file2Label.setWordWrap(True)
		self.file2Label.setObjectName(_fromUtf8("file2Label"))
		self.gridLayout.addWidget(self.file2Label, 0, 2, 1, 1)
		self.contents_1 = QtGui.QTextEdit(CompareWidget)
		self.contents_1.setFocusPolicy(QtCore.Qt.NoFocus)
		self.contents_1.setLineWrapMode(QtGui.QTextEdit.NoWrap)
		self.contents_1.setReadOnly(True)
		self.contents_1.setTabStopWidth(8)
		self.contents_1.setAcceptRichText(False)
		self.contents_1.setObjectName(_fromUtf8("contents_1"))
		self.gridLayout.addWidget(self.contents_1, 1, 0, 1, 1)
		self.vboxlayout = QtGui.QVBoxLayout()
		self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
		spacerItem = QtGui.QSpacerItem(20, 101, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
		self.vboxlayout.addItem(spacerItem)
		self.firstButton = QtGui.QToolButton(CompareWidget)
		self.firstButton.setEnabled(False)
		self.firstButton.setObjectName(_fromUtf8("firstButton"))
		self.vboxlayout.addWidget(self.firstButton)
		self.upButton = QtGui.QToolButton(CompareWidget)
		self.upButton.setEnabled(False)
		self.upButton.setObjectName(_fromUtf8("upButton"))
		self.vboxlayout.addWidget(self.upButton)
		self.downButton = QtGui.QToolButton(CompareWidget)
		self.downButton.setEnabled(False)
		self.downButton.setObjectName(_fromUtf8("downButton"))
		self.vboxlayout.addWidget(self.downButton)
		self.lastButton = QtGui.QToolButton(CompareWidget)
		self.lastButton.setEnabled(False)
		self.lastButton.setObjectName(_fromUtf8("lastButton"))
		self.vboxlayout.addWidget(self.lastButton)
		spacerItem1 = QtGui.QSpacerItem(20, 101, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
		self.vboxlayout.addItem(spacerItem1)
		self.gridLayout.addLayout(self.vboxlayout, 1, 1, 1, 1)
		self.contents_2 = QtGui.QTextEdit(CompareWidget)
		self.contents_2.setFocusPolicy(QtCore.Qt.NoFocus)
		self.contents_2.setLineWrapMode(QtGui.QTextEdit.NoWrap)
		self.contents_2.setReadOnly(True)
		self.contents_2.setTabStopWidth(8)
		self.contents_2.setAcceptRichText(False)
		self.contents_2.setObjectName(_fromUtf8("contents_2"))
		self.gridLayout.addWidget(self.contents_2, 1, 2, 1, 1)
		self.verticalLayout.addLayout(self.gridLayout)

		self.horizontalLayout = QtGui.QHBoxLayout()

		self.synchronizeCheckBox = QtGui.QCheckBox(CompareWidget)
		self.synchronizeCheckBox.setChecked(True)
		self.synchronizeCheckBox.setObjectName(_fromUtf8("synchronizeCheckBox"))
		self.horizontalLayout.addWidget(self.synchronizeCheckBox)
		self.horizontalLayout.addStretch()

		self.totalLabel = QtGui.QLabel(CompareWidget)
		self.totalLabel.setObjectName(_fromUtf8("totalLabel"))
		self.horizontalLayout.addWidget(self.totalLabel)
		self.changedLabel = QtGui.QLabel(CompareWidget)
		self.changedLabel.setObjectName(_fromUtf8("changedLabel"))
		self.horizontalLayout.addWidget(self.changedLabel)
		self.addedLabel = QtGui.QLabel(CompareWidget)
		self.addedLabel.setObjectName(_fromUtf8("addedLabel"))
		self.horizontalLayout.addWidget(self.addedLabel)
		self.deletedLabel = QtGui.QLabel(CompareWidget)
		self.deletedLabel.setObjectName(_fromUtf8("deletedLabel"))
		self.horizontalLayout.addWidget(self.deletedLabel)
		self.verticalLayout.addLayout(self.horizontalLayout)

		self.retranslateUi(CompareWidget)
		QtCore.QMetaObject.connectSlotsByName(CompareWidget)
		CompareWidget.setTabOrder(self.synchronizeCheckBox, self.firstButton)
		CompareWidget.setTabOrder(self.firstButton, self.upButton)
		CompareWidget.setTabOrder(self.upButton, self.downButton)
		CompareWidget.setTabOrder(self.downButton, self.lastButton)

	def retranslateUi(self, CompareWidget):
		CompareWidget.setWindowTitle(QtGui.QApplication.translate("CompareWidget", "File Comparison", None, QtGui.QApplication.UnicodeUTF8))
		self.firstButton.setToolTip(QtGui.QApplication.translate("CompareWidget", "Press to move to the first difference", None, QtGui.QApplication.UnicodeUTF8))
		self.upButton.setToolTip(QtGui.QApplication.translate("CompareWidget", "Press to move to the previous difference", None, QtGui.QApplication.UnicodeUTF8))
		self.downButton.setToolTip(QtGui.QApplication.translate("CompareWidget", "Press to move to the next difference", None, QtGui.QApplication.UnicodeUTF8))
		self.lastButton.setToolTip(QtGui.QApplication.translate("CompareWidget", "Press to move to the last difference", None, QtGui.QApplication.UnicodeUTF8))
		self.synchronizeCheckBox.setToolTip(QtGui.QApplication.translate("CompareWidget", "Select, if the scrollbars should be synchronized", None, QtGui.QApplication.UnicodeUTF8))
		self.synchronizeCheckBox.setText(QtGui.QApplication.translate("CompareWidget", "&Synchronize scrollbars", None, QtGui.QApplication.UnicodeUTF8))
		self.synchronizeCheckBox.setShortcut(QtGui.QApplication.translate("CompareWidget", "Alt+S", None, QtGui.QApplication.UnicodeUTF8))



def sbsdiff(a, b, linenumberwidth = 4):
	"""
	Compare two sequences of lines; generate the delta for display side by side.
	
	@param a first sequence of lines (list of strings)
	@param b second sequence of lines (list of strings)
	@param linenumberwidth width (in characters) of the linenumbers (integer)
	@return a generator yielding tuples of differences. The tuple is composed
		of strings as follows.
		<ul>
			<li>opcode -- one of e, d, i, r for equal, delete, insert, replace</li>
			<li>lineno a -- linenumber of sequence a</li>
			<li>line a -- line of sequence a</li>
			<li>lineno b -- linenumber of sequence b</li>
			<li>line b -- line of sequence b</li>
		</ul>
	"""
	def removeMarkers(line):
		"""
		Internal function to remove all diff markers.
		
		@param line line to work on (string)
		@return line without diff markers (string)
		"""
		return line\
			.replace('\0+', "")\
			.replace('\0-', "")\
			.replace('\0^', "")\
			.replace('\1', "")

	linenumberformat = "%%%dd" % linenumberwidth
	emptylineno = ' ' * linenumberwidth
	
	for (ln1, l1), (ln2, l2), flag in _mdiff(a, b, None, None, IS_CHARACTER_JUNK):
		if not flag:
			yield ('e', str(linenumberformat % ln1), l1,
						str(linenumberformat % ln2), l2)
			continue
		if ln2 == "" and l2 == "\n":
			yield ('d', str(linenumberformat % ln1), removeMarkers(l1),
						emptylineno, '\n')
			continue
		if ln1 == "" and l1 == "\n":
			yield ('i', emptylineno, '\n',
						str(linenumberformat % ln2), removeMarkers(l2))
			continue
		yield ('r', str(linenumberformat % ln1), l1,
					str(linenumberformat % ln2), l2)

class WCompareWidget(QWidget, Ui_CompareWidget):
	"""
	Class implementing a dialog to compare two files and show the result side by side.
	"""
	def __init__(self, parent = None):
		"""
		Constructor
		
		@param files list of files to compare and their label 
			(list of two tuples of two strings)
		@param parent parent widget (QWidget)
		"""
		QWidget.__init__(self,parent)
		self.setupUi(self)
		
		self.firstButton.setIcon(icon(':/icons/arrow-top'))
		self.upButton.setIcon(icon(':/icons/arrow-up'))
		self.downButton.setIcon(icon(':/icons/arrow-down'))
		self.lastButton.setIcon(icon(':/icons/arrow-bottom'))
		
		self.totalLabel.setText(self.trUtf8('Total: %1').arg(0))
		self.changedLabel.setText(self.trUtf8('Changed: %1').arg(0))
		self.addedLabel.setText(self.trUtf8('Added: %1').arg(0))
		self.deletedLabel.setText(self.trUtf8('Deleted: %1').arg(0))
		
		self.updateInterval = 20	# update every 20 lines
		
		self.vsb1 = self.contents_1.verticalScrollBar()
		self.hsb1 = self.contents_1.horizontalScrollBar()
		self.vsb2 = self.contents_2.verticalScrollBar()
		self.hsb2 = self.contents_2.horizontalScrollBar()
		
		self.on_synchronizeCheckBox_toggled(True)
		
		if sys.platform.startswith("win"):
			self.contents_1.setFontFamily("Lucida Console")
			self.contents_2.setFontFamily("Lucida Console")
		else:
			self.contents_1.setFontFamily("Monospace")
			self.contents_2.setFontFamily("Monospace")
		self.fontHeight = QFontMetrics(self.contents_1.currentFont()).height()
		
		self.cNormalFormat = self.contents_1.currentCharFormat()
		self.cInsertedFormat = self.contents_1.currentCharFormat()
		self.cInsertedFormat.setBackground(QBrush(QColor(190, 237, 190)))
		self.cDeletedFormat = self.contents_1.currentCharFormat()
		self.cDeletedFormat.setBackground(QBrush(QColor(237, 190, 190)))
		self.cReplacedFormat = self.contents_1.currentCharFormat()
		self.cReplacedFormat.setBackground(QBrush(QColor(190, 190, 237)))
		
		# connect some of our widgets explicitly
		self.connect(self.synchronizeCheckBox, SIGNAL("toggled(bool)"), 
					 self.on_synchronizeCheckBox_toggled)
		self.connect(self.vsb1, SIGNAL("valueChanged(int)"), self.__scrollBarMoved)
		self.connect(self.vsb1, SIGNAL('valueChanged(int)'),
			self.vsb2, SLOT('setValue(int)'))
		self.connect(self.vsb2, SIGNAL('valueChanged(int)'),
			self.vsb1, SLOT('setValue(int)'))
		
		self.diffParas = []
		self.currentDiffPos = -1
		
		self.markerPattern = "\0\+|\0\^|\0\-"
		
		self.clear()
		
	def __appendText(self, pane, linenumber, line, format, interLine = False):
		"""
		Private method to append text to the end of the contents pane.
		
		@param pane text edit widget to append text to (QTextedit)
		@param linenumber number of line to insert (string)
		@param line text to insert (string)
		@param format text format to be used (QTextCharFormat)
		@param interLine flag indicating interline changes (boolean)
		"""
		tc = pane.textCursor()
		tc.movePosition(QTextCursor.End)
		pane.setTextCursor(tc)
		pane.setCurrentCharFormat(format)
		if interLine:
			pane.insertPlainText("%s " % linenumber)
			for txt in re.split(self.markerPattern, line):
				if txt:
					if txt.count('\1'):
						txt1, txt = txt.split('\1', 1)
						tc = pane.textCursor()
						tc.movePosition(QTextCursor.End)
						pane.setTextCursor(tc)
						pane.setCurrentCharFormat(format)
						pane.insertPlainText(txt1)
					tc = pane.textCursor()
					tc.movePosition(QTextCursor.End)
					pane.setTextCursor(tc)
					pane.setCurrentCharFormat(self.cNormalFormat)
					pane.insertPlainText(txt)
		else:
			pane.insertPlainText("%s %s" % (linenumber, line))

	def clear(self):
		self.file1Label.setText('')
		self.file2Label.setText('')
		self.contents_1.clear()
		self.contents_2.clear()

	def doDiff(self, label1, buffer1, label2, buffer2):
		"""
		Public slot to analyze two buffers and display their diffs.
		"""
		self.file1Label.setText(label1)
		self.file2Label.setText(label2)

		# This normalizes EOL characters to \n for both buffers		
		lines1 = [x + '\n' for x in buffer1.splitlines()]
		lines2 = [x + '\n' for x in buffer2.splitlines()]
		
		self.contents_1.clear()
		self.contents_2.clear()
		
		# counters for changes
		added = 0
		deleted = 0
		changed = 0
		
		paras = 1
		self.diffParas = []
		self.currentDiffPos = -1
		oldOpcode = ''
		for opcode, ln1, l1, ln2, l2 in sbsdiff(lines1, lines2):
			if opcode in 'idr':
				if oldOpcode != opcode:
					oldOpcode = opcode
					self.diffParas.append(paras)
					# update counters
					if opcode == 'i':
						added += 1
					elif opcode == 'd':
						deleted += 1
					elif opcode == 'r':
						changed += 1
				if opcode == 'i':
					format1 = self.cNormalFormat
					format2 = self.cInsertedFormat
				elif opcode == 'd':
					format1 = self.cDeletedFormat
					format2 = self.cNormalFormat
				elif opcode == 'r':
					if ln1.strip():
						format1 = self.cReplacedFormat
					else:
						format1 = self.cNormalFormat
					if ln2.strip():
						format2 = self.cReplacedFormat
					else:
						format2 = self.cNormalFormat
			else:
				oldOpcode = ''
				format1 = self.cNormalFormat
				format2 = self.cNormalFormat
			self.__appendText(self.contents_1, ln1, l1, format1, opcode == 'r')
			self.__appendText(self.contents_2, ln2, l2, format2, opcode == 'r')
			paras += 1
			if not (paras % self.updateInterval):
				QApplication.processEvents()
		
		self.vsb1.setValue(0)
		self.vsb2.setValue(0)
		self.firstButton.setEnabled(False)
		self.upButton.setEnabled(False)
		self.downButton.setEnabled(len(self.diffParas) > 0)
		self.lastButton.setEnabled(len(self.diffParas) > 0)
		
		self.totalLabel.setText(self.trUtf8('Total: %1').arg(added + deleted + changed))
		self.changedLabel.setText(self.trUtf8('Changed: %1').arg(changed))
		self.addedLabel.setText(self.trUtf8('Added: %1').arg(added))
		self.deletedLabel.setText(self.trUtf8('Deleted: %1').arg(deleted))

	def __moveTextToCurrentDiffPos(self):
		"""
		Private slot to move the text display to the current diff position.
		"""
		value = (self.diffParas[self.currentDiffPos] - 1) * self.fontHeight
		self.vsb1.setValue(value)
		self.vsb2.setValue(value)
	
	def __scrollBarMoved(self, value):
		"""
		Private slot to enable the buttons and set the current diff position
		depending on scrollbar position.
		
		@param value scrollbar position (integer)
		"""
		tPos = value / self.fontHeight + 1
		bPos = (value + self.vsb1.pageStep()) / self.fontHeight + 1
		
		self.currentDiffPos = -1
		
		if self.diffParas:
			self.firstButton.setEnabled(tPos > self.diffParas[0])
			self.upButton.setEnabled(tPos > self.diffParas[0])
			self.downButton.setEnabled(bPos < self.diffParas[-1])
			self.lastButton.setEnabled(bPos < self.diffParas[-1])
			
			if tPos >= self.diffParas[0]:
				for diffPos in self.diffParas:
					self.currentDiffPos += 1
					if tPos <= diffPos:
						break
	
	@pyqtSignature("")
	def on_upButton_clicked(self):
		"""
		Private slot to go to the previous difference.
		"""
		self.currentDiffPos -= 1
		self.__moveTextToCurrentDiffPos()
	
	@pyqtSignature("")
	def on_downButton_clicked(self):
		"""
		Private slot to go to the next difference.
		"""
		self.currentDiffPos += 1
		self.__moveTextToCurrentDiffPos()
	
	@pyqtSignature("")
	def on_firstButton_clicked(self):
		"""
		Private slot to go to the first difference.
		"""
		self.currentDiffPos = 0
		self.__moveTextToCurrentDiffPos()
	
	@pyqtSignature("")
	def on_lastButton_clicked(self):
		"""
		Private slot to go to the last difference.
		"""
		self.currentDiffPos = len(self.diffParas) - 1
		self.__moveTextToCurrentDiffPos()

	@pyqtSignature("bool")
	def on_synchronizeCheckBox_toggled(self, sync):
		"""
		Private slot to connect or disconnect the scrollbars of the displays.
		
		@param sync flag indicating synchronisation status (boolean)
		"""
		if sync:
			self.hsb2.setValue(self.hsb1.value())
			self.connect(self.hsb1, SIGNAL('valueChanged(int)'),
				self.hsb2, SLOT('setValue(int)'))
			self.connect(self.hsb2, SIGNAL('valueChanged(int)'),
				self.hsb1, SLOT('setValue(int)'))
		else:
			self.disconnect(self.hsb1, SIGNAL('valueChanged(int)'),
				self.hsb2, SLOT('setValue(int)'))
			self.disconnect(self.hsb2, SIGNAL('valueChanged(int)'),
				self.hsb1, SLOT('setValue(int)'))



if __name__ == "__main__":
	import sys
	
	app = QApplication([])

	f1 = open(sys.argv[1]).read()
	f2 = open(sys.argv[2]).read()

	w = WCompareWidget()
	w.show()
	w.doDiff("file1", f1, "file2", f2)

	app.exec_()

