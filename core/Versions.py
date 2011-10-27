# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008,2009,2010 Sebastien Lefevre and other contributors
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
# Testerman server related version strings.
#
##

#: Main TS implementation version
TESTERMAN_SERVER_VERSION = '1.4.4'

#: Main TACS implementation version
TESTERMAN_AGENT_CONTROLLER_VERSION = '1.4.0'

#: API versions: major.minor
#: major += 1 if not backward compatible,
#: minor += 1 if feature-enriched, backward compatible
XC_VERSION = '1.1'
IA_VERSION = '1.1'
IL_VERSION = '1.0'
XA_VERSION = '1.1'

def getServerVersion():
	return TESTERMAN_SERVER_VERSION

def getXcVersion():
	return XC_VERSION

def getAiVersion():
	return AI_VERSION

def getWsVersion():
	import WebServices
	return WebServices.WS_VERSION

def getAgentControllerVersion():
	return TESTERMAN_AGENT_CONTROLLER_VERSION

def getIlVersion():
	return IL_VERSION

def getXaVersion():
	return XA_VERSION
