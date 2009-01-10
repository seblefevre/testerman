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
# Standalone QTesterman installer.
#
# Download and install the latest update available on the server.
#
# No dependencies on other QTesterman files.
##

from PyQt4.Qt import *

import sys
import base64
import tarfile
import time
import xmlrpclib
import zlib

import StringIO

##
# Lightweigth TestermanClient: Ws update part only
# (extracted from TestermanClient.py)
##
class DummyLogger:
	"""
	A Defaut logging.Logger-like implementation.
	"""
	def formatTimestamp(self, timestamp):
		return time.strftime("%Y%m%d %H:%M:%S", time.localtime(timestamp))  + ".%3.3d" % int((timestamp * 1000) % 1000)

	def info(self, txt):
		pass
	
	def debug(self, txt):
		pass
	
	def critical(self, txt):
		print "%s - CRITICAL - %s" % (self.formatTimestamp(time.time()), txt)
	
	def warning(self, txt):
		print "%s - WARNING - %s" % (self.formatTimestamp(time.time()), txt)

	def error(self, txt):
		print "%s - ERROR - %s" % (self.formatTimestamp(time.time()), txt)

class WsClient:
	"""
	Lightweight client: subset of Ws only: getFile.
	"""
	def __init__(self, serverUrl):
		self._logger = DummyLogger()
		self._serverUrl = serverUrl
		self.__proxy = xmlrpclib.ServerProxy(self._serverUrl, allow_none = True)

	def getLogger(self):
		return self._logger

	def getFile(self, filename):
		"""
		Gets a file.
		This implementation always request the file as compressed data
		(gzip + base64 encoding).
		
		@type  filename: string
		@param filename: complete path within the docroot of the filename to retrieve
		
		@throws Exception in case of a (technical) error.
		
		@rtype: (buffer) string, or None
		@returns: the file content, or None if the file was not found.
		"""
		start = time.time()
		self.getLogger().debug("Getting file %s..." % filename)
		try:
			content = self.__proxy.getFile(filename, True)
			if content:
				content = zlib.decompress(base64.decodestring(content))
				self.getLogger().debug("File decoded, loaded in %fs" % (time.time() - start))
		except Exception, e:
			self.getLogger().error("Unable to get file: " + str(e))
			raise e
		return content

	def getComponentVersions(self, component, branches = [ 'stable', 'testing', 'experimental' ]):
		"""
		Returns the available updates for a given component, with a basic filering on branches.
		
		Based on metadata stored into /updates.xml within the server's docroot:
		
		<updates>
			<update component="componentname" branch="stable" version="1.0.0" url="/components/componentname-1.0.0.tar">
				<!-- optional properties -->
				<property name="release_notes_url" value="/components/rn-1.0.0.txt />
				<!-- ... -->
			</update>
		</update>
		
		@type  component: string
		@param component: the component identifier ("qtesterman", "pyagent", ...)
		@type  branches: list of strings in [ 'stable', 'testing', 'experimental' ]
		@param branches: the acceptable branches. 
		
		@rtype: list of dict{'version': string, 'branch': string, 'url': string, 'properties': dict[string] of strings}
		@returns: versions info, as list ordered from the newer to the older. The url is a relative path from the docroot, suitable
		          for a subsequent getFile() to get the update archive.
		"""
		updates = None
		try:
			updates = self.getFile("/updates.xml")
		except:
			return []
		if updates is None:
			return []
		
		ret = []
		# Now, parse the updates metadata
		import xml.dom.minidom
		import operator
		
		doc = xml.dom.minidom.parseString(updates)
		rootNode = doc.documentElement
		for node in rootNode.getElementsByTagName('update'):
			c = None
			branch = None
			version = None
			url = None
			if node.attributes.has_key('component'):
				c = node.attributes.get('component').value
			if node.attributes.has_key('branch'):
				branch = node.attributes.get('branch').value
			if node.attributes.has_key('version'):
				version = node.attributes.get('version').value
			if node.attributes.has_key('url'):
				url = node.attributes.get('url').value
			
			if c and c == component and url and version and branch in branches:
				# Valid version detected. Add it to our return result
				entry = {'version': version, 'branch': branch, 'url': url, 'properties': {}}
				# Don't forget to add optional update properties
				for p in node.getElementsByTagName('property'):
					if p.attributes.has_key('name') and p.attribute.has_key('value'):
						entry['properties'][p.attributes['name']] = p.attributes['value']
				ret.append(entry)

		# Sort the results
		ret.sort(key = operator.itemgetter('version'))
		ret.reverse()
		return ret
	
	def installComponent(self, url, basepath):
		"""
		Download the component file referenced by url, and install it in basepath.
		
		@type  url: string
		@type  basepath: unicode string
		@param url: the url of the coponent archive to download, relative to the docroot
		"""
		# We retrieve the archive
		archive = self.getFile(url)
		if not archive:
			raise Exception("Archive file not found on server (%s)" % url)
		
		# We untar it into the current directory.
		archiveFileObject = StringIO.StringIO(archive)
		try:
			tfile = tarfile.TarFile.open('any', 'r', archiveFileObject)
			contents = tfile.getmembers()
			# untar each file into the qtesterman directory

			for c in contents:
				self.getLogger().debug("Unpacking %s to %s..." % (c.name, basepath))
				tfile.extract(c, basepath)
				# TODO: make sure to set write rights to allow future updates
				# os.chmod("%s/%s" % (basepath, c), ....)
			tfile.close()
		except Exception, e:
			archiveFileObject.close()
			raise Exception("Error while unpacking the update archive:\n%s" % str(e))

		archiveFileObject.close()


# Taken from AutoUpdate.py
def updateComponent(proxy, basepath, component, currentVersion = None, branches = [ "stable" ]):
	"""
	Checks for updates, and proposes the user to update if a newer version is available.

	@type  basepath: QString 
	@param basepath: the application basepath were we should unpack the update archive

	@throws exceptions
	
	@rtype: bool
	@returns: True if the component was updated. False otherwise (on error or user abort)
	"""
	updates = proxy.getComponentVersions(component, branches)

	if not updates:
		# No updates available - nothing to do
		print "No updates available on this server."
		return False

	print "Available updates:"
	print "\n".join([ "%s (%s)" % (x['version'], x['branch']) for x in updates])

	# Versions rules
	# A.B.C < A+n.b.c
	# A.B.C < A.B+n.c
	# A.B.C < A.B.C+n
	# (ie when comparing A.B.C and a.b.c, lexicographic order is ok)
	
	# Let's check if we have a better version than the current one
	if not currentVersion or (currentVersion < updates[0]['version']):
		newerVersion = updates[0]['version']
		url = updates[0]['url']
		branch = updates[0]['branch']
		print "Newer version available: %s" % newerVersion

		ret = QMessageBox.question(None, "Update manager", "A new QTesterman Client version is available on the server:\n%s (%s)\nDo you want to update now ?" % (newerVersion, branch), QMessageBox.Yes, QMessageBox.No)
		if ret == QMessageBox.Yes:
			# Download and unpack the archive

			try:			
				proxy.installComponent(url, unicode(basepath))
			except Exception, e:
				QMessageBox.warning(None, "Update manager", "Unable to install the update:\n%s\nContinuing with the current version." % str(e))
				return False

			QMessageBox.information(None, "Update manager", "Update succesfully installed.")
			# Let the caller propose a restart
			return True


class WInstallationDialog(QDialog):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		self.setWindowTitle("QTesterman installation")
		
		# Read the settings
		settings = QSettings()
		urllist = settings.value('connection/urllist', QVariant(QStringList(QString('http://localhost:8080')))).toStringList()

		self.urlComboBox = QComboBox()
		self.urlComboBox.setEditable(1)
		self.urlComboBox.addItems(urllist)
		self.urlComboBox.setMaxCount(5)
		self.urlComboBox.setMaximumWidth(250)

		# Default: current directory
		self.installationPathLineEdit = QLineEdit(QDir.currentPath())
		self.installationPathLineEdit.setMinimumWidth(150)

		layout = QVBoxLayout()

		paramLayout = QGridLayout()
		paramLayout.addWidget(QLabel("Server URL:"), 0, 0)
		paramLayout.addWidget(self.urlComboBox, 0, 1)
		paramLayout.addWidget(QLabel("Installation path:"), 1, 0)
		paramLayout.addWidget(self.installationPathLineEdit, 1, 1)
		self.browseDirectoryButton = QPushButton("Select installation path...")
		self.connect(self.browseDirectoryButton, SIGNAL('clicked()'), self.browseDirectory)
		paramLayout.addWidget(self.browseDirectoryButton, 2, 1)
		layout.addLayout(paramLayout)

		# Buttons
		buttonLayout = QHBoxLayout()
		self.okButton = QPushButton("Install", self)
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		self.cancelButton = QPushButton("Cancel", self)
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout.addStretch()
		buttonLayout.addWidget(self.okButton)
		buttonLayout.addWidget(self.cancelButton)
		buttonLayout.setMargin(4)

		layout.addLayout(buttonLayout)

		self.setLayout(layout)

	def updateModel(self):
		"""
		Update the data model.
		"""
		# URL List: the currently selected item should be the first of the saved list,
		# so that it is selected upon restoration (this requirement could be matched 
		# with other strategies, however)
		urllist = QStringList(self.urlComboBox.currentText())
		for i in range(0, self.urlComboBox.count()):
			if self.urlComboBox.itemText(i) !=  self.urlComboBox.currentText():
				urllist.append(self.urlComboBox.itemText(i))

		# We save them as settings
		settings = QSettings()
		settings.setValue('connection/urllist', QVariant(urllist))

	def checkModel(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		url = str(self.urlComboBox.currentText().toAscii())
		
		if not QUrl(url).scheme() == 'http':
			QErrorMessage(self).showMessage('The Testerman server URL must start with http://')
			return 0
		return 1
	
	def getServerUrl(self):
		return self.urlComboBox.currentText()
	
	def getInstallationPath(self):
		return self.installationPathLineEdit.text()

	def accept(self):
		if self.checkModel():
			QDialog.accept(self)

	def browseDirectory(self):
		path = QFileDialog.getExistingDirectory(self, "Installation directory", self.installationPathLineEdit.text())
		if not path.isEmpty():
			self.installationPathLineEdit.setText(path)

def main():
	# OK, now we can create some Qt objects.
	app = QApplication([])
	# These names enables the use of QSettings() without any additional parameters.
	app.setOrganizationName("Testerman")
	app.setApplicationName("QTesterman")

	print "Preparing to install QTesterman..."
	installationDialog = WInstallationDialog(None)
	
	if installationDialog.exec_() != QDialog.Accepted:
		print "Installation cancelled by user."
		sys.exit(0)

	url = str(installationDialog.getServerUrl().toAscii())
	basepath = unicode(installationDialog.getInstallationPath())
	
	proxy = WsClient(serverUrl = url)

	branches = [ 'stable' ]
	acceptUnstableUpdates = False # to read on command line ? to get from the installation widget ?
	if acceptUnstableUpdates:
		branches.append('testing')
		branches.append('experimental')
	if updateComponent(proxy = proxy, basepath = basepath, component = "qtesterman", currentVersion = None, branches = branches):
		# Update done. Restart ?
		# TODO: implement a real application restart
		QMessageBox.information(None, "Installation complete", "QTesterman was successfully installed.")
		sys.exit(0)
	else:
		# No update. Error ? something else ?
		QMessageBox.warning(None, "Installation failed", "QTesterman was not installed.\nYou may check the server URL or ask your Testerman's administrator to check for deployed updates.")
		sys.exit(1)
	


if __name__ == '__main__':
	main()
