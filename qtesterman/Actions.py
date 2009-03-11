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
# Client-wide 'business logic' actions.
#
##


from Base import *
from CommonWidgets import *

import os.path

from PyQt4.Qt import *


################################################################################
# Some Client-wide actions, callable from anywhere.
################################################################################

def deleteAssociatedFiles(path, force = False, selectAssociatedFiles = True):
	"""
	Perform the necessary actions to delete the file 'path', according to
	the extension of the file (i.e. its type).

	Necessary actions:
	- discard/ignore/do nothing (too dangerous, not implemented, etc)
	- ask for a confirmation if force = False
	- automatically select the associated files if selectAssociatedFiles = True

	returns 1 if the action was performed, 0 if it was cancelled.
	"""

	(basedir, basename) = os.path.split(path)
	pathtype = basename.split('.')[-1]
	basename = '.'.join(basename.split('.')[:-1]) # without the extension

	if pathtype == 'log':
		log = basename + ".log"
		ats = basename + ".ats"
		if not force:
			label = "Are you sure you want to delete log file %s ?" % log
			checkBoxLabel = None
			if getProxy().fileExists(basedir + '/' + ats):
				# We can propose to delete the associated ATS
				checkBoxLabel = "Also delete associated ATS"
			dialog = WDeleteFileConfirmation(label, (checkBoxLabel, selectAssociatedFiles), QApplication.instance().get('gui.mainwindow'))
			if dialog.exec_() == QDialog.Accepted:
				getProxy().removeFile(basedir + '/' + log)
				if dialog.checkBoxChecked():
					getProxy().removeFile(basedir + '/' + ats)
				return 1
			else:
				return 0
		else:
			getProxy().removeFile(basedir + '/' + log)
			if selectAssociatedFiles:
				getProxy().removeFile(basedir + '/' + ats)
			return 1


	# ATS can be deleted as well. If an associated log exists (i.e. we are in the archive dir),
	# we'll delete it as well upon confirmation.
	if pathtype == 'ats':
		log = basename + ".log"
		ats = basename + ".ats"
		if not force:
			label = "Are you sure you want to delete ATS file %s ?" % ats
			checkBoxLabel = None
			if getProxy().fileExists(basedir + '/' + log):
				# We can propose to delete the associated log.
				checkBoxLabel = "Also delete associated log"
			dialog = WDeleteFileConfirmation(label, (checkBoxLabel, selectAssociatedFiles), QApplication.instance().get('gui.mainwindow'))
			if dialog.exec_() == QDialog.Accepted:
				getProxy().removeFile(basedir + '/' + ats)
				if dialog.checkBoxChecked():
					getProxy().removeFile(basedir + '/' + log)
				return 1
			else:
				return 0
		else:
			getProxy().removeFile(basedir + '/' + log)
			if selectAssociatedFiles:
				getProxy().removeFile(basedir + '/' + ats)
			return 1

	# other pathtype not supported (.py for modules, directories, etc)


def deleteFile(path, force = False):
	"""
	Perform the necessary actions to delete the file 'path'.
	Ask for a confirmation if force = False

	returns 1 if the action was performed, 0 if it was cancelled.
	"""

	(basedir, basename) = os.path.split(path)
	pathtype = basename.split('.')[-1]
#	basename = '.'.join(basename.split('.')[:-1]) # without the extension

	canDelete = False
	if force:
		canDelete = True
	else:
		msg = "Are you sure you want to delete the file %s ?" % basename
		ret = QMessageBox.question(QApplication.instance().get('gui.mainwindow'), getClientName(), msg, QMessageBox.Yes | QMessageBox.No)
		canDelete = (ret == QMessageBox.Yes)

	if canDelete:
		ret = getProxy().removeFile(path)
		if not ret:
			return 1
		else:
			# Display an error message: cannot remove this folder: not empty.
			msg = "Unable to remove this file: " + str(ret)
			QMessageBox.information(QApplication.instance().get('gui.mainwindow'), getClientName(), msg)
			return 0
	else:
		return 0


def deleteDirectory(path, force = False):
	"""
	Perform the necessary actions to delete the directory 'path'.

	Ask for a confirmation if force = False.
	The current server implementation only accept to delete empty folders.

	returns 1 if the action was performed, 0 if it was cancelled or not feasible on the server.
	"""

	canDelete = False
	if force:
		canDelete = True
	else:
		msg = "Are you sure you want to delete the folder %s ?" % path
		ret = QMessageBox.question(QApplication.instance().get('gui.mainwindow'), getClientName(), msg, QMessageBox.Yes | QMessageBox.No)
		canDelete = (ret == QMessageBox.Yes)

	if canDelete:
		ret = getProxy().removeFile(path)
		if not ret:
			return 1
		else:
			# Display an error message: cannot remove this folder: not empty.
			msg = "Cannot remove this folder: not empty."
			QMessageBox.information(QApplication.instance().get('gui.mainwindow'), getClientName(), msg)
			return 0
	else:
		return 0

