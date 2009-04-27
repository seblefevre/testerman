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
# A QTextEdit based logging handler
#
##


from PyQt4.Qt import *

import CommonWidgets

import logging

class QLoggingStream(QObject):
	"""
	This Stream turns logging requests into Qt signals.
	They can be then connected to a QTextEdit for display.
	
	Implemented as a singleton.
	
	@emits: loggingEvent(const QString &)
	"""
	def __init__(self, parent = None):
		QObject.__init__(self, parent)
	
	def flush(self):
		"""
		Simulates a file object
		"""
		pass
	
	def write(self, data):
		"""
		Simulates a file object
		"""
		data = data.strip()
		# Copy to stdout
		print data
		# Then emit our signal
		QObject.emit(self, SIGNAL('loggingEvent(const QString &)'), QString(data))


class WLogger(QTextEdit):
	"""
	A Logging window that can be used as a stream
	for the logging.StreamHandler.
	
	Automatically configure the logging system on create.
	"""
	def __init__(self, parent = None):
		QTextEdit.__init__(self, parent)

		self.setWindowTitle("Logs")
		self.setReadOnly(True)
		self.setWordWrapMode(QTextOption.NoWrap)
		self.resize(QSize(800, 600))
		
		self._clearAction = CommonWidgets.TestermanAction(self, "Clear", self.clear)
		
		self.connect(getLoggingStream(), SIGNAL('loggingEvent(const QString &)'), self.append)
		logging.getLogger().info("Logger initialized.")

	def contextMenuEvent(self, event):
		menu = self.createStandardContextMenu()
		menu.addSeparator()
		menu.addAction(self._clearAction)
		menu.exec_(event.globalPos())

##
# Automatic initialization on import
##

TheLoggingStream = QLoggingStream()

def getLoggingStream():
	return TheLoggingStream

logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s.%(msecs)03d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S', stream = getLoggingStream())

