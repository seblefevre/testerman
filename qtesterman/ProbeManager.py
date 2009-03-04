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
# A probe manager widget.
# Displays available probes, interfaces probe-related actions.
#
##

from PyQt4.Qt import *

from Base import *

import AgentView

################################################################################
# View Controller
################################################################################

class ViewController(QObject):
	"""
	The bridge between view signals and the business logic.
	"""
	def __init__(self, parent = None):
		QObject.__init__(self, parent)
	
	def addView(self, view):
		self.connect(QApplication.instance(), SIGNAL('testermanServerUpdated(QUrl)'), lambda: view.refresh)

################################################################################
# A Dock bridging views and a controller
################################################################################

class WProbeManagerDock(QDockWidget):
	def __init__(self, parent):
		QDockWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.controller = ViewController(self)
		self.agentTree = AgentView.WAgentView(self)
		self.agentTree.setClient(getProxy())
		self.controller.addView(self.agentTree)
		self.setWidget(self.agentTree)
		self.setWindowTitle("Probe manager")
