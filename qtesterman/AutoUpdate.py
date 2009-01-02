##
# -*- coding: utf-8 -*-
#
# Auto update management.
#
# $Id$
##

import PyQt4.Qt as qt

try:
	from Base import *
except:
	pass

################################################################################
# Autoupdate management
################################################################################

import tarfile
import StringIO
import os
import sys
import re

def isComponentVersionNewer(a, b):
	"""
	Given two component version strings a, b, returns True if a < b, else otherwise.

	Used to detect if (current / local) version a should be upgraded to (reference / remote) version b.
	
	@type  a: string
	@param a: the "current" version
	@type  b: string
	@param b: the "reference" version
	
	@rtype: bool
	@returns: True if we can upgrade from current to reference, (ie b > a), False otherwise.
	"""
	# Valid Testerman component versions are:
	# A.B.C and A.B.C-<keyword>-* where <keyword> in [ testing ] (for now)
	# Rules:
	# A.B.C < A+n.b.c
	# A.B.C < A.B+n.c
	# A.B.C < A.B.C+n
	# (ie when comparing A.B.C and a.b.c, lexigographic order is ok)

	# If no reference version, never gives a positive feedback.
	if not b: return False
	# If no current version, always gives a positive feedback to upgrade.
	if not a: return True

 	abcVersion = re.compile(r'(?P<base>(?P<A>[0-9]+)\.(?P<B>[0-9]+)\.(?P<C>[0-9]+))(-(?P<extension>.*))?')

	current = abcVersion.match(a)
 	reference = abcVersion.match(b)

 	# In case of an invalid local version, positive feedback, always
	if not current: return True
	# In case of an invalid remote version, negative feedback, always
 	if not reference: return False

	# Extension is only taken into account in case of local.base == remote.base
	# Otherwise, the base can decide for itself.
	if current.group('base') != reference.group('base'):
		return (current.group('base') < reference.group('base'))

	# OK, now we have the same A.B.C, we can compare extensions
	# We have an extension, not the remote: the remote version is newer (the 'final' version)
	if current.group('extension') and not reference.group('extension'):
		return True
	# We don't have an extension, but the remote has one: the local is newer (the 'final' version)
	if not current.group('extension') and reference.group('extension'):
		return False
	# Both have extensions:
	return (current.group('extension') < reference.group('extension'))

def checkForUpdates(acceptTestRelease = 0):
	# This first request to the server is a good opportunity to check the server availability
	try:
		onServer = getProxy().getLatestComponentVersion('qtesterman', getClientVersion(), acceptTestRelease)
	except Exception, e: # Socket.socketerror, in fact...
		import traceback
		traceback.print_stack()
		qt.QMessageBox.warning(None, getClientName() + " Auto update", "Unable to connect to the Testerman Server.\nPlease check the Testerman Server URI and/or your connections.")
		print "DEBUG: exception caught: " + str(e)
		sys.exit(1) # Don't continue, we may get too many problems after this one.

	if onServer is None:
		# No better version
		return

	if isComponentVersionNewer(getClientVersion(), onServer) or qt.QApplication.instance().get('autoupdate.force'):
		ret = qt.QMessageBox.question(None, getClientName() + " Auto update", "A new Qt Testerman Client version is available on the server\n(current: %s, available: %s).\nDo you want to update now ?" % (getClientVersion(), onServer), qt.QMessageBox.Yes, qt.QMessageBox.No)
		if ret == qt.QMessageBox.Yes:
			# We retrieve the archive
			archive = getProxy().getComponentArchive('qtesterman', onServer)
			if not archive:
				qt.QMessageBox.warning(None, getClientName() + " Auto update", "Unable to retrieve the new client from the server. Continuing with the current version.")
				return
			# We untar it into the current directory.
			archiveFileObject = StringIO.StringIO(archive)
			try:
				tfile = tarfile.TarFile.open('any', 'r', archiveFileObject)
				contents = tfile.getmembers()
				# untar each file into the qtesterman directory
				
				for c in contents:
					print str(c)
					tfile.extract(c, qt.QApplication.instance().get('basepath'))
					# TODO: make sure to set W right for future updates
				tfile.close()
			except Exception, e:
				qt.QMessageBox.warning(None, getClientName() + " Auto update", "Unable to install the new client from the server:\n%s.\nContinuing with the current version." % str(e))
				return

			archiveFileObject.close()

			# Propose to restart
			qt.QMessageBox.information(None, getClientName() + " Auto update", "Qt Testerman Client updated. You can now restart it.")

