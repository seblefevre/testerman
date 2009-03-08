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
# A graphical view of execution logs.
# Almost compliant with TTCN-3 graphical representation.
# 
##

# TODO: reimplement paint() for each item instead of using a graphics item group

from PyQt4.Qt import *

import time

from CommonWidgets import *
import Base

class GraphicsItemGroup(QGraphicsItemGroup):
	"""
	Modified class to support additional pythonic associated data
	(avoid the usage of QVariant with Python data)
	"""
	def __init__(self, parent = None):
		QGraphicsItemGroup.__init__(self, parent)
		self.__data = {}

	def setMyData(self, index, data):
		self.__data[index] = data

	def myData(self, index):
		if self.__data.has_key(index):
			return self.__data[index]
		return None

class GraphicsItem(QGraphicsItem):
	"""
	Modified class to support additional pythonic associated data
	(avoid the usage of QVariant with Python data)
	"""
	def __init__(self, parent = None):
		QGraphicsItem.__init__(self, parent)
		self.__data = {}

	def setMyData(self, index, data):
		self.__data[index] = data

	def myData(self, index):
		return self.__data.get(index, None)


class BoxedLabel(GraphicsItem):
	"""
	A label in a box. The label is centered in the box, with a margin on both sides.
	(0,0) is the origin of the box.
	
	Used for basic logs.
	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192)):
		GraphicsItem.__init__(self)
		self._bgColor = bgcolor
		self._fontPen = QPen()
		pen = QPen(QColor(160, 160, 160))
		pen.setWidth(2)
		pen.setCapStyle(Qt.RoundCap)
		self._pen = pen
		self._font = QFont()

		self._label = None
		self._boundingRect = None
		self._verticalMargin = 0
		self._horizontalMargin = 10
		self.setLabel(label)

	def boundingRect(self):
		return self._boundingRect

	def setLabel(self, label):
		self._label = label
		# Update bounding rect
		fm = QFontMetrics(self._font)
		br = fm.boundingRect(self._label)
		# Add some spaces around the text
		br.setWidth(br.width() + 2*self._horizontalMargin)
		br.setHeight(br.height() + 2*self._verticalMargin)
		self._boundingRect = QRectF(br)

	def paint(self, painter, option, widget = None):		
		painter.setPen(self._pen)
		painter.setFont(self._font)
		painter.setBrush(QBrush(self._bgColor))
		painter.drawRect(self.boundingRect())
		painter.setPen(self._fontPen)
		painter.drawText(self.boundingRect(), Qt.AlignCenter, self._label)

class RoundedBoxedLabel(BoxedLabel):
	"""
	Used to identify started behaviour
	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192)):
		BoxedLabel.__init__(self, label, bgcolor)

	def paint(self, painter, option, widget = None):		
		painter.setPen(self._pen)
		painter.setFont(self._font)
		painter.setBrush(QBrush(self._bgColor))
		painter.drawRoundedRect(self.boundingRect(), 7.0, 7.0)
		painter.setPen(self._fontPen)
		painter.drawText(self.boundingRect(), Qt.AlignCenter, self._label)

class HexaBoxedLabel(BoxedLabel):
	"""
	Used to verdict assignment notification.
	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192)):
		BoxedLabel.__init__(self, label, bgcolor)
		self._points = []
		self.updatePolyline()
	
	def updatePolyline(self):
		h = self.boundingRect().height()
		w = self.boundingRect().width()
		x = self.boundingRect().x()
		y = self.boundingRect().y()
		self._points = []
		self._points.append(QPoint(x + self._horizontalMargin, y))
		self._points.append(QPoint(x + w - self._horizontalMargin, y))
		self._points.append(QPoint(x + w, y + h/2))
		self._points.append(QPoint(x + w - self._horizontalMargin, y + h))
		self._points.append(QPoint(x + self._horizontalMargin, y + h))
		self._points.append(QPoint(x, y + h/2))
		self._polygon = QPolygon(self._points)
	
	def paint(self, painter, option, widget = None):		
		painter.setPen(self._pen)
		painter.setFont(self._font)
		painter.setBrush(QBrush(self._bgColor))
		painter.drawPolygon(self._polygon)
		painter.setPen(self._fontPen)
		painter.drawText(self.boundingRect(), Qt.AlignCenter, self._label)


class StartedTimerItem(GraphicsItem):
	"""
	A kind of hourglass with the label of the started timer to its left.
	      ____
	      \  /
	timer  \/___
	       /\
				/__\

	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192)):
		GraphicsItem.__init__(self)
		self._bgColor = bgcolor
		pen = QPen(QColor(160, 160, 160))
		pen.setWidth(1)
		pen.setCapStyle(Qt.RoundCap)
		self._pen = pen
		self._fontPen = QPen()
		self._font = QFont()

		self._label = None
		self._boundingRect = None
		self._hourglassHeight = 30
		self._hourglassWidth = 20
		self._horizontalMargin = -2 # space between the label and the hourglass
		self.setLabel(label)
		self.updatePolyline()

	def boundingRect(self):
		return self._boundingRect

	def updatePolyline(self):
		w = self.boundingRect().width()
		h = self.boundingRect().height()
		x = self.boundingRect().x()
		y = self.boundingRect().y()
		self._points = []
		self._points.append(QPoint(x + w, y + h/2))
		self._points.append(QPoint(x + w - self._hourglassWidth, y + h/2)) # hourglass center
		self._points.append(QPoint(x + w - self._hourglassWidth/2, y)) # top right
		self._points.append(QPoint(x + w - self._hourglassWidth*1.5, y)) # top left
		self._points.append(QPoint(x + w - self._hourglassWidth/2, y + h)) # bottom right
		self._points.append(QPoint(x + w - self._hourglassWidth*1.5, y + h)) # bottom left
		self._points.append(QPoint(x + w - self._hourglassWidth, y + h/2)) # back to hourglass center
		self._polygon = QPolygon(self._points)

	def setLabel(self, label):
		self._label = label
		# Update bounding rect
		fm = QFontMetrics(self._font)
		br = fm.boundingRect(self._label)
		# Add some space for the hourglass to the right of the label
		br.setWidth(br.width() + self._hourglassWidth*1.5 + self._horizontalMargin)
		br.setHeight(max(br.height(), self._hourglassHeight))
		self._boundingRect = QRectF(br)

	def paint(self, painter, option, widget = None):		
		painter.setPen(self._pen)
		painter.setFont(self._font)
		painter.setBrush(QBrush(self._bgColor))
		painter.drawPolyline(self._polygon)
		painter.setPen(self._fontPen)
		painter.drawText(self.boundingRect(), Qt.AlignVCenter, self._label)


class StoppedTimerItem(GraphicsItem):
	"""
	A kind of hourglass with the label of the started timer to its left.
	      
	      \  /
	timer  \/___
	       /\
				/  \

	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192)):
		GraphicsItem.__init__(self)
		self._bgColor = bgcolor
		pen = QPen(QColor(160, 160, 160))
		pen.setWidth(1)
		pen.setCapStyle(Qt.RoundCap)
		self._pen = pen
		self._fontPen = QPen()
		self._font = QFont()

		self._label = None
		self._boundingRect = None
		self._hourglassHeight = 30
		self._hourglassWidth = 20
		self._horizontalMargin = -2 # space between the label and the hourglass
		self.setLabel(label)
		self._lines = []
		self.updateLines()

	def boundingRect(self):
		return self._boundingRect

	def updateLines(self):
		w = self.boundingRect().width()
		h = self.boundingRect().height()
		x = self.boundingRect().x()
		y = self.boundingRect().y()
		self._lines = []
		self._lines.append(QLine(x + w - self._hourglassWidth/2, y, x + w - self._hourglassWidth*1.5, y + h)) # top right -> bottom left
		self._lines.append(QLine(x + w - self._hourglassWidth*1.5, y, x + w - self._hourglassWidth/2, y + h)) # top left -> bottom right
		self._lines.append(QLine(x + w - self._hourglassWidth, y + h/2, x + w, y + h/2)) # center -> TC line

	def setLabel(self, label):
		self._label = label
		# Update bounding rect
		fm = QFontMetrics(self._font)
		br = fm.boundingRect(self._label)
		# Add some space for the hourglass to the right of the label
		br.setWidth(br.width() + self._hourglassWidth*1.5 + self._horizontalMargin)
		br.setHeight(max(br.height(), self._hourglassHeight))
		self._boundingRect = QRectF(br)

	def paint(self, painter, option, widget = None):		
		painter.setPen(self._pen)
		painter.setFont(self._font)
		painter.setBrush(QBrush(self._bgColor))
		painter.drawLines(self._lines)
		painter.setPen(self._fontPen)
		painter.drawText(self.boundingRect(), Qt.AlignVCenter, self._label)


class TimeoutTimerItem(StoppedTimerItem):
	"""
	A kind of hourglass with the label of the started timer to its left.
	      
	      \  /
	timer  \/__\
	       /\  /
				/  \

	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192)):
		StoppedTimerItem.__init__(self, label, bgcolor)

	def updateLines(self):
		w = self.boundingRect().width()
		h = self.boundingRect().height()
		x = self.boundingRect().x()
		y = self.boundingRect().y()
		self._lines = []
		self._lines.append(QLine(x + w - self._hourglassWidth/2, y, x + w - self._hourglassWidth*1.5, y + h)) # top right -> bottom left
		self._lines.append(QLine(x + w - self._hourglassWidth*1.5, y, x + w - self._hourglassWidth/2, y + h)) # top left -> bottom right
		self._lines.append(QLine(x + w - self._hourglassWidth, y + h/2, x + w, y + h/2)) # center -> TC line
		self._lines.append(QLine(x + w - self._hourglassWidth/3, y + h/2 - self._hourglassWidth/3, x + w, y + h/2)) # top arrow -> TC line
		self._lines.append(QLine(x + w - self._hourglassWidth/3, y + h/2 + self._hourglassWidth/3, x + w, y + h/2)) # bottom arrow -> TC line
		

class StoppedTcItem(GraphicsItem):
	"""
	Used to mark a stopped TC: a circle with a cross in it.
	The verdict is indicated to its right.
	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192)):
		GraphicsItem.__init__(self)
		self._bgColor = bgcolor
		pen = QPen(QColor(160, 160, 160))
		pen.setWidth(1)
		pen.setCapStyle(Qt.RoundCap)
		self._pen = pen
		self._fontPen = QPen()
		self._font = QFont()

		self._label = None
		self._boundingRect = None
		self._diameter = 30.0
		self._margin = 4.0 # space between the label and the circle at its left
		self.setLabel(label)
		self.updateLines()

	def boundingRect(self):
		return self._boundingRect

	def updateLines(self):
		w = self.boundingRect().width()
		x = self.boundingRect().x()
		y = self.boundingRect().y()
		self._circleCenter = QPointF(x + self._diameter/2.0, y + self._diameter/2.0)
		self._lines = []
		offset = 0.7*self._diameter/2.0  # 0.7 = sqrt(2)/2
		self._lines.append(QLine(self._circleCenter.x() - offset, self._circleCenter.y() - offset, self._circleCenter.x() + offset, self._circleCenter.y() + offset))
		self._lines.append(QLine(self._circleCenter.x() + offset, self._circleCenter.y() - offset, self._circleCenter.x() - offset, self._circleCenter.y() + offset))

	def setLabel(self, label):
		self._label = label
		# Update bounding rect
		fm = QFontMetrics(self._font)
		br = fm.boundingRect(self._label)
		# Add some space for the circle to the left of the label
		br.setWidth(br.width() + self._margin + self._diameter)
		br.setHeight(self._diameter)
		self._boundingRect = QRectF(br)

	def paint(self, painter, option, widget = None):		
		painter.setPen(self._pen)
		painter.setFont(self._font)
		painter.setBrush(QBrush(self._bgColor))
		painter.drawEllipse(self._circleCenter, self._diameter/2.0, self._diameter/2.0)
		painter.drawLines(self._lines)
		painter.setPen(self._fontPen)
		painter.drawText(self.boundingRect(), Qt.AlignRight | Qt.AlignVCenter, self._label)


class RightArrowBoxedLabel(GraphicsItemGroup):
	"""
	A label into a wide arrow, directed to the right.
	(0,0) is the top left origin of the visual item.
	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192), pen = QPen()):
		GraphicsItemGroup.__init__(self)
		self.__createWidgets(label, bgcolor, pen)

	def __createWidgets(self, text, bgcolor, pen):
		# The label
		label = QGraphicsSimpleTextItem(text)
		label.setZValue(100)

		rect = label.boundingRect()
		# the bounding arrow. The arrow body width is adapter to the label height,
		# and the final arrow is bevel pixel high and low its main body.
		bevel = 5 # pixels
		path = QPainterPath()
		path.lineTo(path.currentPosition() + QPointF(rect.width() + 20 - bevel, 0))
		path.lineTo(path.currentPosition() + QPointF(0, -bevel))
		path.lineTo(path.currentPosition() + QPointF(2*bevel, bevel + rect.height() / 2.0))
		path.lineTo(path.currentPosition() + QPointF(-2*bevel, bevel + rect.height() / 2.0))
		path.lineTo(path.currentPosition() + QPointF(0, -bevel))
		path.lineTo(path.currentPosition() + QPointF(- (rect.width() + 20 - bevel), 0))
		path.closeSubpath()

		box = QGraphicsPathItem(path)
		box.setPen(pen)
		box.setBrush(QBrush(bgcolor))
		box.setZValue(50)
		self.addToGroup(box)
		# We center the label in the box
		label.translate((box.boundingRect().width() - rect.width()) / 2.0, 0)
		self.addToGroup(label)


class LeftArrowBoxedLabel(GraphicsItemGroup):
	"""
	A label into a wide arrow, directed to the left.
	(0,0) is the top left origin of the visual item.
	"""
	def __init__(self, label, bgcolor = QColor(240, 240, 200, 192), pen = QPen()):
		GraphicsItemGroup.__init__(self)
		self.__createWidgets(label, bgcolor, pen)

	def __createWidgets(self, text, bgcolor, pen):
		# The label
		label = QGraphicsSimpleTextItem(text)
		label.setZValue(100)

		rect = label.boundingRect()
		# the bounding arrow. The arrow body width is adapter to the label height,
		# and the final arrow is bevel pixel high and low its main body.
		bevel = 5 # pixels
		path = QPainterPath()
		path.lineTo(path.currentPosition() + QPointF(-(rect.width() + 20 - bevel), 0))
		path.lineTo(path.currentPosition() + QPointF(0, -bevel))
		path.lineTo(path.currentPosition() + QPointF(-2*bevel, bevel + rect.height() / 2.0))
		path.lineTo(path.currentPosition() + QPointF(2*bevel, bevel + rect.height() / 2.0))
		path.lineTo(path.currentPosition() + QPointF(0, -bevel))
		path.lineTo(path.currentPosition() + QPointF( (rect.width() + 20 - bevel), 0))
		path.closeSubpath()

		box = QGraphicsPathItem(path)
		box.setPen(pen)
		box.setBrush(QBrush(bgcolor))
		box.setZValue(50)
		box.translate(rect.width() + 20 + bevel, 0)
		self.addToGroup(box)
		# We center the label in the box
		label.translate((box.boundingRect().width() - rect.width()) / 2.0, 0)
		self.addToGroup(label)




class MessageArrow(GraphicsItemGroup):
	"""
	Better be a QGraphicsItem... but a group has the benefit of being clickable on
	different parts, triggering different actions.

	If fromX == toX, this is a loopback arrow.
	"""
	def __init__(self, label, message, fromX, toX, fromLabel = None, toLabel = None):
		GraphicsItemGroup.__init__(self)
		self.__createWidgets(label, message, fromX, toX, fromLabel, toLabel)

	def __createWidgets(self, label, message, fromX, toX, fromLabel, toLabel):
		"""
		Create an arrow oriented according to fromX/toX,
		with a clickable text label.
		The local coordinate 0, 0 corresponds to the start of the arrow
		(i.e. the array may points to negative or positivie X coordinates).

		Create a loopback arrow if fromX == toX.
		fromLabel and toLabel, if available, are x-aligned (not centered) on fromX, toX right/left according to the arrow direction.
		"""
		self.mainPen = QPen(QColor(160, 160, 160))
		self.mainPen.setWidth(2)
		self.mainPen.setCapStyle(Qt.RoundCap)

		self.label = QGraphicsSimpleTextItem(label)

		if fromX != toX:
			# Directed arrow
			if (toX - fromX) > 0:
				sign = 1
			else:
				sign = -1

			# The label is x-aligned to the terminated ("to") side,
			# ie the label BB is closed to the toX
			if sign < 0: # to the right
				xoffset = toX - fromX + 15
			else: # to the left
				xoffset = toX - fromX - 15 - self.label.boundingRect().width()

			self.label.translate(xoffset, -20) # -20: the label is above the arrow line,
			self.addToGroup(self.label)

			# The from/to labels are managed as tooltips.
			toolTip = QString("")
			if fromLabel: toolTip += fromLabel
			toolTip += " -> "
			if toLabel: toolTip += toLabel
			self.setToolTip(toolTip)

			# Main line
			# 2 is a margin from the extreme from/to - this makes the display cleaner, and avoir useless item collisions
			line = QGraphicsLineItem(sign*2, 0, toX - fromX  - sign*2, 0)
			line.setPen(self.mainPen)
			self.addToGroup(line)
			# around the toX, we draw two diag lines
			line = QGraphicsLineItem(toX - fromX - sign*2, 0, toX - fromX - sign*2 -sign*5, -5)
			line.setPen(self.mainPen)
			self.addToGroup(line)
			line = QGraphicsLineItem(toX - fromX - sign*2, 0, toX - fromX - sign*2 -sign*5, 5)
			line.setPen(self.mainPen)
			self.addToGroup(line)
		else:
			# Loopback arrow.
			# We draw a circle pie (?) with a final arrow. The circle arrow starts at (0, 0)
			# The label is inserted at mid-height, with transparency, x-centered on 0.
			radius = 10
			path = QPainterPath()
			path.moveTo(radius, 0)
			path.arcTo(0, 0, 2*radius, 2*radius, 90, -180)
			circle = QGraphicsPathItem(path)
			circle.setPen(self.mainPen)
			circle.translate(-radius + 2, 0) # 2 is the margin from the main actor axis

			self.addToGroup(circle)

			self.label.translate(- self.label.boundingRect().width() / 2.0, radius - self.label.boundingRect().height() / 2.0)
			self.addToGroup(self.label)

			sign = -1 # the final arrow is to the left
			# around the toX/fromX, we draw two diag lines
			line = QGraphicsLineItem(0, 2*radius, 2 , 2*radius - 5)
			line.setPen(self.mainPen)
			line.translate(2, 0) # 2 is the margin from the main actor axis
			self.addToGroup(line)
			line = QGraphicsLineItem(0, 2*radius, 5, 2*radius + 3)
			line.setPen(self.mainPen)
			line.translate(2, 0) # 2 is the margin from the main actor axis
			self.addToGroup(line)

			# The from/to labels are managed as tooltips.
			toolTip = QString("")
			if fromLabel: toolTip += fromLabel
			toolTip += " -> "
			if toLabel: toolTip += toLabel
			self.setToolTip(toolTip)


class TestCaseActor(QGraphicsItemGroup):
	"""
	Create an actor representation for the sequence diagram, i.e.
	a box with a text in it, and a vertical line.
	X-centered around the vertical line (on x = 0) in local coordinates.
	"""
	def __init__(self, name, parent = None, scene = None):
		QGraphicsItemGroup.__init__(self, parent, scene)
		self.__killed = False # actor killed: to life line anymore.
		self._state = 'running' # or 'stopped' or 'killed'
		self.__createWidgets(name)

	def __createWidgets(self, name):
		self.mainFont = QFont()
		self.mainPen = QPen(QColor(160, 160, 160))
		self.mainPen.setWidth(2)
		self.mainPen.setCapStyle(Qt.RoundCap)

		self.dashPen = QPen(QColor(200, 200, 200), 2, Qt.DotLine, Qt.RoundCap)

		#print "DEBUG: creating actor %s" % name
		self.titleText = QGraphicsSimpleTextItem(name)
		self.titleText.setZValue(10)
#		self.titleText.setFont(self.mainFont)
		rect = self.titleText.boundingRect()
		# X-centered on 0 (local coord)
		self.titleText.translate(- rect.width() / 2.0, 0)
		self.addToGroup(self.titleText)

		self.titleRect = QGraphicsRectItem(QRectF(rect.x(), rect.y(), rect.width() + 20, rect.height()))
		self.titleRect.setBrush(QBrush(QColor(220, 220, 250)))
		self.titleRect.setPen(self.mainPen)
		self.titleRect.setZValue(0)
		# X-centered on 0 (local coord)
		self.titleRect.translate(- self.titleRect.boundingRect().width() / 2.0, 0)
		self.addToGroup(self.titleRect)

		self.mainLine = QGraphicsLineItem(0, self.titleRect.boundingRect().height(), 0, 20)
		self.mainLine.setPen(self.mainPen)
		self.mainLine.setZValue(0)
		self.addToGroup(self.mainLine)
		
		# Let's make sure that arrows are always selectable even in front of the actor BB (Bounding Box)
		self.setZValue(-1000)

	def setStopped(self):
		self._state = 'stopped'
		# New line
		self.mainLine = QGraphicsLineItem(self.getSceneXAnchor(), self.mainLine.line().y2(), self.getSceneXAnchor(), self.mainLine.line().y2())
		self.mainLine.setPen(self.dashPen)
		self.mainLine.setZValue(0)
		self.addToGroup(self.mainLine)
	
	def setRunning(self):
		self._state = 'running'
		# New line
		self.mainLine = QGraphicsLineItem(self.getSceneXAnchor(), self.mainLine.line().y2(), self.getSceneXAnchor(), self.mainLine.line().y2())
		self.mainLine.setPen(self.mainPen)
		self.mainLine.setZValue(0)
		self.addToGroup(self.mainLine)

	def setKilled(self):
		"""
		Once an actor is killed, its main line is stopped.
		"""
		self._state = 'killed'
	
	def isKilled(self):
		return self._state == 'killed'

	def expandMainLine(self, toY):
		if self.isKilled():
			return
		# We can accept new events. But the life line is expanded in dash dots.
		if self.mainLine.line().y2() < toY:
			self.mainLine.setLine(self.mainLine.line().x1(), self.mainLine.line().y1() , self.mainLine.line().x2(), toY)

	def createKilledStickerItem(self, yOffset):
		"""
		Add a filled black rectangle.
		"""
		item = QGraphicsRectItem(QRectF(0.0, 0.0, 40.0, 5.0))
		item.setBrush(QBrush(QColor(0,0,0)))
		item.setPen(QPen())
		y = yOffset + 20
		x = self.getSceneXAnchor() - item.boundingRect().width() / 2.0
		item.translate(x, y)

		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		self.setKilled()
		return item

	def createStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		"""
		Add a rectangle "sticker" text on the main line and return the item.
		We have to move the created item to the scene coordinate corresponding to the scene position of the actor
		before attaching it.
		From Qt doc on addToGroup:
		The item will be reparented to this group, but its position and transformation relative to the scene will stay intact.
		"""
		group = BoxedLabel(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - group.boundingRect().width() / 2.0
		group.translate(x, y)

		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)

		return group

	def createRoundedStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		item = RoundedBoxedLabel(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - item.boundingRect().width() / 2.0
		item.translate(x, y)
		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		return item

	def createStartedStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		item = RoundedBoxedLabel(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - item.boundingRect().width() / 2.0
		item.translate(x, y)
		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		self.setRunning()
		return item

	def createHexaStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		item = HexaBoxedLabel(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - item.boundingRect().width() / 2.0
		item.translate(x, y)
		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		return item

	def createStartedTimerStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		item = StartedTimerItem(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - item.boundingRect().width() # align it against the TC line
		item.translate(x, y)
		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		return item

	def createStoppedTimerStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		if self.isKilled():
			return
		item = StoppedTimerItem(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - item.boundingRect().width() # align it against the TC line
		item.translate(x, y)
		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		return item

	def createTimeoutTimerStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		if self.isKilled():
			return
		item = TimeoutTimerItem(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - item.boundingRect().width() # align it against the TC line
		item.translate(x, y)
		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		return item

	def createStoppedStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		item = StoppedTcItem(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - item._diameter/2.0 - 0.5
		item.translate(x, y)
		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)
		self.setStopped()
		return item

	def createRightArrowStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		group = RightArrowBoxedLabel(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - group.boundingRect().width() / 2.0
		group.translate(x, y)

		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)

		return group

	def createLeftArrowStickerItem(self, text, yOffset, color = QColor(240, 240, 200, 192)):
		group = LeftArrowBoxedLabel(text, bgcolor = color)
		y = yOffset + 20
		x = self.getSceneXAnchor() - group.boundingRect().width() / 2.0
		group.translate(x, y)

		# main line growth, if needed
		if y > self.mainLine.line().y2():
			self.expandMainLine(y)

		return group

	def getSceneXAnchor(self):
		"""
		Return the X coordinate of an anchor for a message arrow, in the Scene coordinate
		"""
		return self.mapToScene(QPointF(0, 0)).x()

class TestCaseScene(QGraphicsScene):
	"""
	Manage only ONE testcase as a visual workflow.

	The workflow is constructed by sending events to this object.
	The events must be provisionned timestamp-ordered, otherwise the automatic layout mechanism won't work correctly.
	"""
	def __init__(self, parent = None):
		QGraphicsScene.__init__(self)

		# Some layout parameters
		self.actorXMin = 150
		self.actorXOffset = 150
		self.actorYMin = 0
		self.eventYMin = 50
		self.eventYOffset = 100 # Y space between two events in case of a layout collision
		self.timeScale = 10.0 # 1s = 10 pixels

		# Keep a refence on existing actors so that events can be added to them
		self.__actors = {}
		# This enables a kind of "scaling"
		self.__previousY = self.eventYMin
		self.__previousEventTimestamp = None
		self.__lastAddedItem = None
		self.__lastActorSlot = self.actorXMin
		self.__createWidgets()

	def __createWidgets(self):
		self.failedColor = QColor(250, 220, 220, 192)
		self.successColor = QColor(220, 250, 220, 192)
		self.startedColor = QColor(200, 220, 250, 192)
		self.timerStartedColor = QColor(200, 220, 250, 192)
		self.timerStoppedColor = QColor(220, 250, 250, 192)
		self.timerTimeoutColor = QColor(200, 0, 200, 192)

	def __addActor(self, name):
		"""
		This function create a new actor representation,
		translate it to the next available slot (one each 150 px in X),
		reference its name/position/actor representation so that
		links between actors (messages, actor related events) are easy to draw.
		"""
		a = TestCaseActor(name)
		a.translate(self.__lastActorSlot, self.actorYMin)
		self.addItem(a)
		self.__actors[name] = a
		# Ready for a next actor
		self.__lastActorSlot += self.actorXOffset

	def onEvent(self, domElement):
		"""
		This is the main entry point to the Visual workflow viewer.
		
		Parse 
		Add an event on an actor (verdict, user log, template match/mismatch)
		or an arrow between two actors (sentmessage) (with loopback arrow support),
		or an actor itself (testcomponent-created)
		
		@type  domElement: QDomElement
		@param domElement: the log event to parse/interpret
		
		@rtype: QGraphicsItem, or None
		@returns: the added QGraphicsItem, or None if no item was added
		"""
		(timestamp, status) = domElement.attribute("timestamp").toFloat()
		if not status:
			print "TestCaseScene: Invalid log event: incorrect timestamp"
			return None
		
		element = domElement.tagName()

		# Let's compute the Y position of the event, i.e. the way we'll layout it.
		# The algorithm is:
		# - Y is grown naturally with the timeScale.
		# - If we need to add an item, if we collide with the last displayed event,
		#   then we increment the Y position until we don't collide anymore.
		# The previous computed Y is always used as a base to compute the next one.
		# (Y(event #) is "croissant")

		# Y naturally growing based on timescale
		if not self.__previousEventTimestamp:
			self.__previousEventTimestamp = timestamp
		y = self.__previousY + (timestamp - self.__previousEventTimestamp) * self.timeScale
		self.__previousEventTimestamp = timestamp
		# the Y adjustment according to the last added item (last displayed event)
		# is performed when adding a new item only

		itemToAdd = None

		try:
			# TC events
			if element == "tc-created":
				actor = domElement.attribute("id")
				self.__addActor(actor)
				print "Added actor %s" % repr(actor)
			elif element == "tc-started":
				actor = domElement.attribute("id")
				behaviour = domElement.attribute("behaviour")
				itemToAdd = self.__actors[actor].createStartedStickerItem(behaviour, y, self.startedColor)
			elif element == "tc-stopped":
				actor = domElement.attribute("id")
				verdict = domElement.attribute("verdict")
				color = self.failedColor
				if verdict == "pass":
					color = self.successColor
				itemToAdd = self.__actors[actor].createStoppedStickerItem(verdict, y, color)
			elif element == "tc-killed":
				actor = domElement.attribute("id")
				itemToAdd = self.__actors[actor].createKilledStickerItem(y)

			# Timer events
			elif element == "timer-started":
				actor = domElement.attribute("tc")
				timerId = domElement.attribute("id")
				duration = domElement.attribute("duration")
				itemToAdd = self.__actors[actor].createStartedTimerStickerItem("%s (%s)" % (timerId, duration), y, self.timerStartedColor)
			elif element == "timer-stopped":
				actor = domElement.attribute("tc")
				timerId = domElement.attribute("id")
				itemToAdd = self.__actors[actor].createStoppedTimerStickerItem(timerId, y, self.timerStoppedColor)
			elif element == "timer-expiry":
				actor = domElement.attribute("tc")
				timerId = domElement.attribute("id")
				itemToAdd = self.__actors[actor].createTimeoutTimerStickerItem(timerId, y, self.timerTimeoutColor)

			# TestCase events
			elif element == "verdict-updated":
				actor = domElement.attribute("tc")
				verdict = domElement.attribute("verdict")
				color = self.failedColor
				if verdict == "pass":
					color = self.successColor
				itemToAdd = self.__actors[actor].createHexaStickerItem(verdict, y, color)
			
			# Message events
			elif element == "message-sent":
				fromActor = domElement.attribute("from-tc")
				toActor = domElement.attribute("to-tc")
				fromPort = domElement.attribute("from-port")
				toPort = domElement.attribute("to-port")
				encodedMessage = ''
				itemToAdd = self.createSentMessageItem(encodedMessage, fromActor, toActor, y, "%s.%s" % (fromActor, fromPort), "%s.%s" % (toActor, toPort))
				itemToAdd.setMyData(0, domElement.firstChildElement("message"))

			# Template matchin events
			elif element == "template-match":
				actor = domElement.attribute("tc")
				# If the actor does not exist, this probably means that we are handling a template-match on the internal Testerman queue (timer timeout, etc)
				if self.__actors.has_key(actor):
					itemToAdd = self.__actors[actor].createStickerItem("<match>", y, self.successColor)
					itemToAdd.setMyData(0, domElement.firstChildElement("message"))
					itemToAdd.setMyData(1, domElement.firstChildElement("template"))
			elif element == "template-mismatch":
				actor = domElement.attribute("tc")
				# If the actor does not exist, this probably means that we are handling a template-match on the internal Testerman queue (timer timeout, etc)
				if self.__actors.has_key(actor):
					itemToAdd = self.__actors[actor].createStickerItem("<mismatch>", y, self.failedColor)
					itemToAdd.setMyData(0, domElement.firstChildElement("message"))
					itemToAdd.setMyData(1, domElement.firstChildElement("template"))

			# System events
			elif element == "system-sent":
				actor = QString('system')
				itemToAdd = self.__actors[actor].createRightArrowStickerItem(domElement.firstChildElement("label").text(), y)
				itemToAdd.setMyData(0, domElement.firstChildElement("payload"))
			elif element == "system-received":
				actor = QString('system')
				itemToAdd = self.__actors[actor].createLeftArrowStickerItem(domElement.firstChildElement("label").text(), y)
				itemToAdd.setMyData(0, domElement.firstChildElement("payload"))

			# User log events
			elif element == "user":
				actor = domElement.attribute("tc")
				msg = domElement.text()
				itemToAdd = self.createUserLogItem(actor, msg, y)

		except KeyError, e:
			log("WARNING: unable to add visual event, possibly missed actor creation event (%s)" % getBacktrace())
			itemToAdd = None

		except Exception, e:
			log("WARNING: unable to add visual event (%s)" % getBacktrace())
			itemToAdd = None

		if itemToAdd:
			if self.__lastAddedItem:
				while itemToAdd.collidesWithItem(self.__lastAddedItem):
					# 6 is the minimal increment for Y-layout collision resolution.
					# This is a prime with 20, with is the typical height of most items.
					# As a consequence, we limit the chance of getting just adjacent items.
					itemToAdd.translate(0, 6)

			self.addItem(itemToAdd)
			self.__lastAddedItem = itemToAdd

			self.__previousY = self.__lastAddedItem.sceneBoundingRect().y() + self.__lastAddedItem.sceneBoundingRect().height()

		# Expand all actor main lines up to y at least
		for (name, a) in self.__actors.items():
			a.expandMainLine(self.__previousY)
		
		return itemToAdd

	def createUserLogItem(self, actor, msg, yPos):
		"""
		If the actor is an existing actor, attach a sticker to it as a user log.
		Else create a free label (control/ats level) on the left side of the workflow.
		"""
		if not self.__actors.has_key(actor):
			# Control level or TestCase level / not attached to a Test Component
			t = BoxedLabel(msg, bgcolor = QColor(128, 128, 192, 192))
			t.translate(0, yPos + 10)
			return t
		else:
			# Attached to an actor / test component
			a = self.__actors[actor]
			sticker = a.createStickerItem(msg, yPos)
			return sticker

	def createSentMessageItem(self, encodedMessage, fromActor, toActor, yPos, fromLabel, toLabel):
		"""
		Draw an arrow between fromActor to toActor, at level yOffset
		"""
#		print "Adding sent message %s -> %s at %s " % (str(fromActor), str(toActor), str(yPos))
		if not self.__actors.has_key(fromActor):
			# We missed something, let's recover (very convenient for system and <SUT> actors as well...
			self.__addActor(fromActor)
		if not self.__actors.has_key(toActor):
			# We missed something, let's recover (very convenient for system and <SUT> actors as well...
			self.__addActor(toActor)

		a = self.__actors[fromActor]
		b = self.__actors[toActor]
		arrow = MessageArrow(encodedMessage, None, a.getSceneXAnchor(), b.getSceneXAnchor(), fromLabel, toLabel) # no port label for readability
		arrow.translate(a.getSceneXAnchor(), yPos)
		return arrow


class WClickableGraphicsView(QGraphicsView):
	"""
	An enhanced QGraphicsView with signals when an item is selected.

	emits
	itemSelected(QGraphicsItem)
	"""
	def __init__(self, parent = None):
		QGraphicsView.__init__(self, parent)
		self.setRenderHint(QPainter.Antialiasing)
		self.setRenderHint(QPainter.TextAntialiasing)

	def mousePressEvent(self, event):
		item = self.itemAt(event.pos())
		if item:
			#print "Item available: " + unicode(item)
			# Crash if this is a text item... so we turned all QGraphicsTextItem into QGraphicsSimpleTextItem,
			# no problem anymore. Looks like a problem with the focus flags of the QGraphicsTextItem.
			# (after a google search)
			self.emit(SIGNAL("itemSelected(QGraphicsItem)"), item)
#			if not isinstance(item, QGraphicsTextItem.__class__):
#				self.emit(SIGNAL("itemSelected(QGraphicsItem)"), item)

	def wheelEvent(self, wheelEvent):
		if not (wheelEvent.modifiers() & Qt.ControlModifier):
			return QGraphicsView.wheelEvent(self, wheelEvent)
		delta = wheelEvent.delta()
		if delta > 0:
			self.scale(1.5, 1.5)
		else:
			self.scale(1.0/1.5, 1.0/1.5)
		wheelEvent.accept()


class WVisualTestCaseView(WClickableGraphicsView):
	"""
	A Visual viewer that can manage a TestCase - or any partial logs, in fact.
	"""
	def __init__(self, parent = None):
		WClickableGraphicsView.__init__(self, parent)
		self.__createWidgets()
		self.trackingActivated = False

	def setTracking(self, tracking):
		self.trackingActivated = tracking

	def __createWidgets(self):
		"""
		We have a treeview/listview presenting each detected TestCase.
		We also have a pane to display a WVisualTestCase view when we select
		an ATS in this treeview.

		Notice that control- and ats-level logs are not displayed in this widget
		since we only focus on TestCases.
		"""
		self.connect(self, SIGNAL('itemSelected(QGraphicsItem)'), self.onGraphicsItemSelected)
		# A local testCaseScene is needed to avoid a GC if we only do self.setScene(TestCaseScene())
		self.testCaseScene = TestCaseScene()
		self.setScene(self.testCaseScene)

	def onGraphicsItemSelected(self, item):
		# if item has 2 data (index 0 and 1), this is a match/mismatch.
		# if item has only 1 data (index 1), this is a single message.
		#print "DEBUG: >>>>> selected item " + unicode(item)
		try:
			# The itemGroup corresponding to interesting items (Arrow, Boxed/RoungedLabels) is (typically)
			# never selected (the text/rect item is returned instead; we have to click within the bounbingBox
			# of the group item but not on any of its item to return the group, which is pretty hard to do)
			# so we first tries to get data from the item (in case this is a group).
			# If not, we try the parent.
			# This is a workaround waiting for a better solution...
			try:
				message = item.myData(0)
			except:
				item = item.parentItem()
				message = item.myData(0)
			template = item.myData(1)
			if template:
				self.emit(SIGNAL("templateMatchSelected(QDomElement, QDomElement)"), message, template)
			else:
				self.emit(SIGNAL("messageSelected(QDomElement)"), message)
		except:
			pass

	def clearLog(self):
		self.testCaseScene = TestCaseScene()
		self.setScene(self.testCaseScene)

	def displayPartialLog(self, domElements):
		"""
		FFS
		"""
		for e in domElements:
			self.onEvent(e)

	def onEvent(self, domElement):
		"""
		Log event handler, as emitted by EventMonitor (parsed domElement)
		"""
		item = self.scene().onEvent(domElement)
		if item and self.trackingActivated:
			item.ensureVisible()



