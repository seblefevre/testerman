##
# -*- coding: utf-8 -*-
#
# $Id$
##

import PyQt4.Qt as qt
import time
import re

import Resources


################################################################################
# Non-GUI related code
################################################################################

CLIENT_VERSION = "1.0.0"

CLIENT_NAME = "QTesterman"

################################################################################
# Versioning
################################################################################

def getClientVersion():
	return CLIENT_VERSION

def getClientName():
	return CLIENT_NAME

################################################################################
# Some pretty formaters/printers
################################################################################

def formatTimestamp(timestamp):
	return time.strftime("%Y%m%d %H:%M:%S", time.localtime(timestamp))  + ".%3.3d" % int((timestamp * 1000) % 1000) #str(time.ctime())

def log(txt):
	print "%s - " % formatTimestamp(time.time()) + txt

################################################################################
# URI management
################################################################################

def urlParse(url):
	"""
	Returns a dict containing:
	scheme, netloc, path.
	Empty items are set to "".
	"""
	r = re.match(r'(?P<scheme>[a-zA-Z0-9_]+)://(?P<netloc>[a-zA-Z0-9-:\._@]*)(?P<path>/.*)', url)
	if r:
		return { "scheme": r.group("scheme"), "netloc": r.group("netloc"), "path": r.group("path") }
	else:
		return { "scheme": "", "netloc": "", "path": "" }


################################################################################
# Aliases
################################################################################

def icon(resource):
	return qt.QApplication.instance().icon(resource)

def getProxy():
	return qt.QApplication.instance().getProxy()


