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
# Some global constants and singleton accessors for QTesterman
#
##


from PyQt4.Qt import *

import logging
import time
import re

import Resources


################################################################################
# Versioning
################################################################################

# Versioning scheme:
# A.B.C for 'releasable' versions. 
# A.B.C-svn[-YYYYMMDD] for work in progress versions that will eventually 
# be released as A.B.C+1 or A.B+1.0
# A += 1: major design changes. 
# B += 1: new significant features added
# C += 1: bugfixes and/or minor features added
CLIENT_VERSION = "1.1.99-svn-20090615"
CLIENT_NAME = "QTesterman"

def getClientVersion():
	return CLIENT_VERSION

def getClientName():
	return CLIENT_NAME

################################################################################
# Some pretty formaters/printers
################################################################################

def formatTimestamp(timestamp):
	return time.strftime("%Y%m%d %H:%M:%S", time.localtime(timestamp))  + ".%3.3d" % int((timestamp * 1000) % 1000) #str(time.ctime())

#def log(txt):
#	print "%s - " % formatTimestamp(time.time()) + txt

def log(txt):
	logging.getLogger().info(txt)

def getBacktrace():
	import TestermanNodes
	return TestermanNodes.getBacktrace()

################################################################################
# Aliases
################################################################################

def icon(resource):
	return QApplication.instance().icon(resource)

def getProxy():
	return QApplication.instance().client()


