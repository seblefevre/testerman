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

import glob
import os
import os.path
import re
import threading

class FileWatcherProbe(ProbeImplementationManager.ProbeImplementation):
	"""
Identification and Properties
-----------------------------

Probe Type ID: ``watcher.file``

Properties:

None.

Overview
--------

This probe watches one or more text files locally and sends notifications whenever a line
matching a pattern appeared in one of them.

You should first send a startWatchingFiles command, specifying the files to monitor (absolute paths, wildcards accepted)
and an optional list of regular expression patterns to match. These patterns may contain named group, such
as in ``r'resource (?P<name>.*) played'``. In this example, if a line matching this pattern is detected
in one of the watched files, you will receive a notification containing the source file filename, the
complete line that matched the pattern, and an additional ``matched_name`` string entry containing the matched group.

On start watching, the probe checks for new lines in the monitored files each second (by default). The interval
between two checks can be configured via the ``interval`` startWatchingFiles field. The probe is aware of reset/recreated
or new born files (when monitoring a file that has not been created yet). In case of a file reset, you may miss some
matching lines if new lines are created and the file is reset before the next file check, but this should not be a show-stopper
considering the typical use cases for this probe.

When you do not need to watch these files anymore, send a stopWatchingFiles command. 

The probe automatically stops watching files on unmap and when the current test case is over. 

If you send a startWatchingFiles command while the probe is already in watching mode, the monitoring is restarted
with the new watching parameters.

The ``patterns`` startWatchingFiles field may contain several regular expression. Only the first one that matches new lines in watched files
is used to generate ``matched_*`` notification fields.

WARNING: in most cases, you should set a pattern list that avoids raising a notification for each new line in watched files. This is
particularly true when watching application log files that may generate hundred lines per second, raising as many notifications
to the Testerman Test Executable, saturating the whole system.  

Possible use cases for this probe:

* Checking a log file, verifying that the application logs what we expect according to external stimuli
* Using a log file to check the application behaviour; for instance, when testing an IVR (Interactive Voice Response) server, it could be convenient to check in log files the file that is assumed to be played instead of using voice recognition or RTP pattern analysis.
* Applied to telecom systems, could be used to check CDR (Call Detail Reports) files, possibly in conjunction with a custom codec to apply to the notified lines
* Checking that no error is dumped in a log file during a test. In this case, the probe is probably controlled by a background, dedicated behaviour, setting its verdict to fail as soon as it received an error line notification.

Known Bugs
~~~~~~~~~~

This probe may not detect a file recreation on some file systems such as ext3,
in the following case:

* the file is recreated/replaced with a larger file than the initial one,
* AND the file's inode is not changed (which is the case with ext3, apparently).

In this case, only the delta lines between the old file and the new ones are
reported, instead of reporting all the lines of the file.

Availability
~~~~~~~~~~~~

All platforms.

Dependencies
~~~~~~~~~~~~

None.

See Also
~~~~~~~~

* :doc:`ProbeDirWatcher`, a probe that watches a directory for added/removed entries.

TTCN-3 Types Equivalence
------------------------

The test system interface port bound to such a probe complies with the `FileWatcherPortType` port type as specified below:

::

  type union WatchingCommand
  {
    StartWatchingFile startWatchingFiles,
    anytype           stopWatchingFiles
  }
  
  type record StartWatchingFiles
  {
    record of charstring files,
    record of charstring patterns optional, // defaulted to [ '.*' ]
    float interval optional, // defaulted to 1.0, in second
  }
  
  type record Notification
  {
    charstring filename,
    charstring line, // the matched line
    charstring matched_* optional, // matched groups, if defined in patterns
  }
  
  type port FileWatcherPortType message
  {
    in  WatchingCommand;
    out Notification;
  }
	"""
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
		# First pass: register watched files at the moment we start watching
		try:
			for f in self._files:
				for filename in glob.glob(f):
					if not self._watchedFiles.has_key(filename):
						# First look at the file. Just reference file info
						try:
							if os.path.isfile(filename):
								self._watchedFiles[filename] = os.stat(filename)
								self._probe.getLogger().debug("New file %s registered for watching" % filename)
						except Exception, e:
							self._probe.getLogger().debug("Unable to registered file %s: %s" % (filename, str(e)))
		except Exception, e:
			self._probe.getLogger().debug("Error while registered watched files: %s" % str(e))

		# Now, watch for file changes / reset / new files	
		while not self._stopEvent.isSet():
			try:
				for f in self._files:
					# Glob it - enabling to poll for new files with unknown names in a dir
					for filename in glob.glob(f):
						try:
							self._checkFile(filename)
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
		# Let's compute what we miss since the last watch
		# The offset in bytes, from the start of the file,
		# containing missed data
		offset = None

		if not self._watchedFiles.has_key(filename):
			# New file since the last tick
			if os.path.isfile(filename):
				# First look at the file. Just reference file info
				current = os.stat(filename)
				self._watchedFiles[filename] = current
				self._probe.getLogger().debug("New file %s created since the last tick" % filename)
				offset = 0
		
		else:
			# The file already existed during the last tick
			ref = self._watchedFiles[filename]
			current = os.stat(filename)
			self._watchedFiles[filename] = current
		
			# If the file was recreated in the meanwhile,
			# we should consider its whole content again.
			# The problem is to detect the file was recreated.
			#
			# ctime is platform- (or app- ?) dependent, leading to false positives
			# inode (st_ino) is file-system dependent (ext3 seems to reuse it)
			# we try a mixed approach here
			if current.st_size == ref.st_size:
				if current.st_ctime != ref.st_ctime:
					self._probe.getLogger().debug("File %s recreated since the last tick" % filename)
					offset = 0
				# same size and same ctime: no change
			elif current.st_size > ref.st_size:
				# Problem here.
				# The file may have been fully reset (with a larger content)
				# or just continued
				
				# The ctime test is not safe here; some write() op updates the ctime too
				
				# We try a inode test, but it is not perfect
				# On some filesystems (ext3...), we miss the recreation event
				if current.st_ino != ref.st_ino:
					self._probe.getLogger().debug("File %s recreated since the last tick" % filename)
					offset = 0
				else:
					self._probe.getLogger().debug("File %s has new data since the last tick" % filename)
					# Not recreated, but increased in size
					offset = ref.st_size
			elif current.st_size < ref.st_size:
				self._probe.getLogger().debug("File %s was reset (content replaced) or recreated since the last tick" % filename)
				# Not recreated, but reset in the meanwhile
				offset = 0
		
		if offset is None:
			# Nothing to do for the file
			return
		
		# OK, scan the file to get matching new lines
		self._probe.getLogger().debug("File %s changed since the last tick, starting at %d" % (filename, offset))
		f = open(filename, 'r')
		f.seek(offset)
		newlines = f.readlines()
		f.close()
		# Technically, the file may have grown since we took the ref size
		# We should lock the file until we complete our analysis and reading
		# but the current implementation should be enough for typical probe usages
		
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
