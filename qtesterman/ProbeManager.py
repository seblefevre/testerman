##
# -*- coding: utf-8 -*-
#
# A probe manager widget.
# Displays available probes, interfaces probe-related actions.
#
# $Id$
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
		# No signal to connect for now.
		pass

################################################################################
# A Dock bridging views and a controller
################################################################################

class WProbeManagerDock(qt.QDockWidget):
	def __init__(self, parent):
		qt.QDockWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		self.controller = ViewController(self)
		self.agentTree = AgentView.WAgentView(self)
		self.agentTree.setClient(getProxy())
		self.controller.addView(self.agentTree)
		self.setWidget(self.agentTree)
		self.setWindowTitle("Probe manager")
