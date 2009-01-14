# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 Sebastien Lefevre and other contributors
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
# File watcher
# Monitors a particular text file, raise events whenever new lines
# are created (and matching a regexp pattern).
#
# Useful for logs, CDR files, ...
# 
##


import ProbeImplementationManager

import os
import re
import threading

class FileWatcherProbe(ProbeImplementationManager.ProbeImplementation):
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()
		self._watchingThread = None

	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def onTriMap(self):
		self.stopWatching()
	
	def onTriUnmap(self):
		self.stopWatching()
	
	def onTriExecuteTestCase(self):
		self.stopWatching()
	
	def onTriSAReset(self):
		self.stopWatching()

	def onTriSend(self, message, sutAddress):
		(cmd, args) = message
		if cmd == 'startWatchingFiles':
			self._checkArgs(args, [ ('files', None), ('interval', 1.0), ('patterns', [ r'.*' ])] )
			compiledPatterns = [ re.compile(x) for x in args['patterns']]
			self.startWatching(files = args['files'], interval = args['interval'], patterns = compiledPatterns)
		elif cmd == 'stopWatchingFiles':
			self.stopWatching()
		else:
			raise ProbeImplementationManager.ProbeException("Invalid message format (%s)" % cmd)
	
	def startWatching(self, files, interval, patterns):
		self.stopWatching()
		self._lock()
		self._watchingThread = WatchingThread(self, files, interval, patterns)
		self._watchingThread.start()
		self._unlock()
	
	def stopWatching(self):
		self._lock()
		t = self._watchingThread
		self._watchingThread = None
		self._unlock()
		if t:
			t.stop()

class WatchingThread(threading.Thread):
	def __init__(self, probe, files, interval, patterns):
		threading.Thread.__init__(self)
		self._probe = probe
		self._stopEvent = threading.Event()
		self._files = files
		self._interval = interval
		self._patterns = patterns
		#: last file info indexed by absolute filename
		self._watchedFiles = {}
	
	def run(self):
		self._probe.getLogger().debug("Starting watching files %s with %s every %ss" % (self._files, self._patterns, self._interval))
		self._watchedFiles = {}
		while not self._stopEvent.isSet():
			try:
				for f in self._files:
					try:
						self._checkFile(f)
					except Exception, e:
						self._probe.getLogger().debug("Unable to watch file %s: %s" % (filename, str(e)))
			except Exception, e:
				self._probe.getLogger().debug("Error while watching files: %s" % str(e))
			self._stopEvent.wait(self._interval)
	
	def stop(self):
		self._stopEvent.set()
		self.join()
		self._probe.getLogger().debug("Watching thread stopped")
	
	def _checkFile(self, filename):
		if not self._watchedFiles.has_key(filename):
			# First look at the file. Just reference file info
			self._watchedFiles[filename] = os.stat(filename)
		
		ref = self._watchedFiles[filename]
		current = os.stat(filename)
		self._watchedFiles[filename] = current
		
		# Let's compute what we miss since the last watch
		# The offset in bytes, from the start of the file,
		# containing missed data
		offset = None
		
		# If the file was recreated in the meanwhile,
		# we should consider it globally
		# ctime is platform-dependent, so we'll use inode
		if current.st_ino != ref.st_ino:
			self._probe.getLogger().debug("File %s recreated since the last tick" % filename)
			offset = 0
		elif current.st_size > ref.st_size:
			self._probe.getLogger().debug("File %s has new data since the last tick" % filename)
			# Not recreated, but increased in size
			offset = ref.st_size
		elif current.st_size < ref.st_size:
			self._probe.getLogger().debug("File %s was reset since the last tick" % filename)
			# Not recreated, but resetted in the meanwhile
			offset = 0
		
		if offset is None:
			return
		
		self._probe.getLogger().debug("File %s changed since the last tick, starting at %d" % (filename, offset))
		f = open(filename, 'r')
		f.seek(offset)
		newlines = f.readlines()
		f.close()
		
		for line in newlines:
			for pattern in self._patterns:
				m = pattern.match(line)
				if m:
					event = { 'filename': filename, 'line': line.strip() } # Should we strip the line ?
					for k, v in m.groupdict().items():
						event['matched_%s' % k] = v
					self._probe.triEnqueueMsg(event)			
					# A line can be matched only once.
					break
				# else no match
		

ProbeImplementationManager.registerProbeImplementationClass("watcher.file", FileWatcherProbe)
