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
# Code Outine View
#
##

import Resources

from PyQt4.Qt import *

import compiler
import gc

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


def log(txt):
	print txt


################################################################################
# Tree Widget Items
################################################################################

class OutlineWidgetItem(QTreeWidgetItem):
	def __init__(self, label, fromLine, toLine, parent = None):
		QTreeWidgetItem.__init__(self, parent)
		self._label = label
		self._fromLine = fromLine
		self._toLine = toLine
		self.setText(0, label)
		self.setExpanded(True)
	
	def getBeginLine(self):
		return self._fromLine

	def getEndLine(self):
		return self._toLine
	
class FunctionOutlineWidgetItem(OutlineWidgetItem):
	def __init__(self, label, fromLine, toLine, parent = None):
		OutlineWidgetItem.__init__(self, label, fromLine, toLine, parent)
		self.setIcon(0, icon(':/icons/function'))
		self.setToolTip(0, "Function %s at line %s to %s" % (label, fromLine, toLine))

class MethodOutlineWidgetItem(OutlineWidgetItem):
	def __init__(self, label, fromLine, toLine, parent = None):
		OutlineWidgetItem.__init__(self, label, fromLine, toLine, parent)
		self.setIcon(0, icon(':/icons/method'))
		self.setToolTip(0, "Method %s at line %s to %s" % (label, fromLine, toLine))

class ClassOutlineWidgetItem(OutlineWidgetItem):
	def __init__(self, label, fromLine, toLine, parent = None):
		OutlineWidgetItem.__init__(self, label, fromLine, toLine, parent)
		self.setIcon(0, icon(':/icons/class'))
		self.setToolTip(0, "Class %s at line %s to %s" % (label, fromLine, toLine))

class TestCaseOutlineWidgetItem(OutlineWidgetItem):
	def __init__(self, label, fromLine, toLine, parent = None):
		OutlineWidgetItem.__init__(self, label, fromLine, toLine, parent)
		self.setIcon(0, icon(':/icons/testcase'))
		self.setToolTip(0, "TestCase %s at line %s to %s" % (label, fromLine, toLine))


class OutlineAstVisitor(compiler.visitor.ASTVisitor):
	def __init__(self, treeWidget):
		compiler.visitor.ASTVisitor.__init__(self)
		self._treeWidget = treeWidget
#		self._beingVisitedItems = []
	
	def walkChildren(self, node, parentItem):
#		self._beingVisitedItems.append(parentItem)
		for child in node.getChildNodes():
			self.dispatch(child, parentItem)
	
	def visitClass(self, node, parent = None):
#		self.endCurrentVisitedItem(node.lineno)
		if not parent:
			parent = self._treeWidget
		# Let's add an item
		fromLine = node.lineno
		toLine = node.code.getChildNodes()[-1].lineno
		if len(node.bases) > 0 and "TestCase" in [hasattr(x, 'name') and x.name or None for x in node.bases]:
			item = TestCaseOutlineWidgetItem(node.name, fromLine, toLine, parent)
		else:
			item = ClassOutlineWidgetItem(node.name, fromLine, toLine, parent)

		self._treeWidget.registerItem(item)
		# Search for methods/inner classes
		self.walkChildren(node.code, item)

	def visitFunction(self, node, parent = None):
#		self.endCurrentVisitedItem(node.lineno)
		if not parent:
			parent = self._treeWidget
		# Let's add an item
		fromLine = node.lineno
		toLine = node.code.getChildNodes()[-1].lineno
		label = '%s(%s)' % (node.name, ', '.join(node.argnames))
		if parent is not self._treeWidget and len(node.argnames) and node.argnames[0] == 'self':
			item = MethodOutlineWidgetItem(label, fromLine, toLine, parent)
		else:
			item = FunctionOutlineWidgetItem(label, fromLine, toLine, parent)

		self._treeWidget.registerItem(item)
		# Search for inner functions/classes
		self.walkChildren(node.code, item)

	def endCurrentVisitedItem(self, line = None):
		"""
		References the line as closing the current scope.
		If line is not provided, corresponds to the line of the code to parse.
		"""
		return
		
#		if self._beingVisitedItems:
#			item = self._beingVisitedItems.pop()
#			if not line:
#				line = 1 << 31
#			item._toLine = line - 1
#			print ">> DEBUG: node %s: from %s to %s" % (item._label, item._fromLine, item._toLine)


class WOutlineTreeWidget(QTreeWidget):
	"""
	This widget operates as a view over a string (utf-8) model
	that contains Python code.
	"""
	def __init__(self, parent = None):
		QTreeWidget.__init__(self, parent)
		# Enables to identify which item the cursor is in:
		# item, indexed  by its (starting) line.
		self._items = []
		self.headerItem().setHidden(True)
		self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem*, int)"), self.onItemActivated)
	
	def setModel(self, buf):
		"""
		Sets a new test buffer as a model (utf-8 encoded).
		Triggers the parsing and the construction of the tree,
		after resetting it.
		"""
		self.clear()
		self._items = []
		visitor = OutlineAstVisitor(self)
		try:
			mod = compiler.parse(buf)
			visitor.preorder(mod, visitor, None)
			visitor.endCurrentVisitedItem()
			del mod, visitor
		except SyntaxError:
			log("Syntax error, outline not created")
		finally:
			gc.collect()

	def updateModel(self, buf):
		"""
		To call whenever the model has been updated in a way
		that could impact the outline.
		
		We do not modify the current outline in case of a
		syntax error.
		"""
		try:
			mod = compiler.parse(buf)
		except SyntaxError:
			log("Syntax error, no outline updated")
			return
			
		self.clear()
		self._items = []
		visitor = OutlineAstVisitor(self)
		try:
			visitor.preorder(mod, visitor, None)
			visitor.endCurrentVisitedItem()
			del mod, visitor
		except SyntaxError:
			log("Syntax error, outline not created")
		finally:
			gc.collect()
	
	def registerItem(self, item):
		self._items.append(item)
	
	def setLine(self, line):
		"""
		Highlight the current item according to its line.
		"""
		# Select the shortest segment of code that contains the line number.
		# intersectingItems = filter(lambda x: x.getBeginLine() <= line and x.getEndLIne() >= line, self._items)

		# This list contains (code segment length, item) for intersection segments only
		# (i.e. segments of code that contain the line number)
		t = [ (x.getEndLine() - x.getBeginLine(), x) for x in self._items if (x.getBeginLine() <= line and x.getEndLine() >= line) ]
		activeItem = None
		minLength = 1 << 31
		for (length, item) in t:
			if length < minLength:
				minLength = length
				activeItem = item
		
		# activeItem may be None, too
		self.setCurrentItem(activeItem)
	
	def onItemActivated(self, item, column):
		self.emit(SIGNAL("outlineItemActivated(int)"), item.getBeginLine())

class WOutlineViewDock(QDockWidget):
	"""
	This dock acts as a view controller for the embedded outline tree widget,
	bridging the events between the main application (mainly text widget) and the outline view.
	"""
	def __init__(self, documentTabWidget, parent):
		QDockWidget.__init__(self, parent)
		self._documentTabWidget = documentTabWidget
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("Outline")
		self._outlineTreeWidget = WOutlineTreeWidget(self)
		self.setWidget(self._outlineTreeWidget)
		self.connect(self._documentTabWidget, SIGNAL("currentChanged(int)"), self.onDocumentTabWidgetChanged)
		self.connect(self._outlineTreeWidget, SIGNAL("outlineItemActivated(int)"), self.onOutlineItemActivated)
	
	def getOutlineView(self):
		return self._outlineTreeWidget

	def onDocumentTabWidgetChanged(self, index):
		documentModel = self._documentTabWidget.currentWidget().model
		self._outlineTreeWidget.setModel(documentModel.getBody().encode('utf-8'))
	
	def onOutlineItemActivated(self, line):
		self._documentTabWidget.currentWidget().goTo(line)

def test():
	start()
	test_call([ "this", 
		"hello",
		"fds",
		"fdsfds",
	])


# Basic test
if __name__ == "__main__":
	import sys

	app = QApplication([])

	w = WOutlineTreeWidget()
	w.show()
	w.setModel(open(sys.argv[1]).read())
	
	app.exec_()

