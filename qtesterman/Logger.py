##
# A QTextEdit based logging handler
#
##

import logging

from PyQt4.Qt import *

class QtStreamHandler(logging.Handler, QObject):
	"""
	This StreamHandler turns logging requests into Qt signals.
	They can be then connected to a QTextEdit for display.
	
	@emits: loggingEvent(const QString &)
	"""
	def __init__(self, parent = None):
		logging.Handler.__init__(self)
		QObject.__init__(self, parent)
		self._formater = logging.Formatter('%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s')

	def emit(self, record):
		txt = self._formater.format(record)
		QObject.emit(self, SIGNAL('loggingEvent(const QString &)'), QString(txt))


class WLogging(QTextEdit):
	def __init__(self, parent = None):
		QTextEdit.__init__(self, parent)
			

def getLogger():
	return logging.getLogger()
