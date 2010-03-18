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
# Some basic tools.
#
##

import glob
import os
import re
import resource
import time
import traceback

import StringIO

def getBacktrace():
	"""
	Gets the current backtrace.
	"""
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

def fileExists(f):
	try:
		os.stat(f)
		return True
	except:
		return os.path.islink(f)


################################################################################
# Pretty formatters
################################################################################

def formatTimestamp(timestamp):
	return time.strftime("%Y%m%d %H:%M:%S", time.localtime(timestamp))  + ".%3.3d" % int((timestamp * 1000) % 1000)

def formatTable(headers = [], rows = [], order = None, notAvailableLabel = "(n/a)"):
	"""
	Pretty format the list of dict (rows) according to the header list (headers)
	Header names not found in the dict are not displayed, and
	only header names found in the dict are displayed.
	
	Header is a list of either simple string (name) or tuple (name, label, [formatter]).
	If it is a tuple, label is used to display the header, and name
	to look for the element in the dicts.
	The optional formatter is a function that will take the value to format as single arg.
	"""
	def formatRow(cols, widths):
		"""
		Formatting helper: row pretty print.
		"""
		line = " %s%s " % (cols[0], (widths[0]-len(cols[0]))*' ')
		for i in range(1, len(cols)):
			line = line + "| %s%s " % (cols[i], (widths[i]-len(cols[i]))*' ')
		return line

	def expand(header):
		"""
		Returns the name, label, and formatter for a header entry.
		"""
		if isinstance(header, tuple):
			if len(header) == 2:
				return header[0], header[1], lambda x: x
			elif len(header) == 3:
				return header
			else:
				raise Exception("Invalid header")
		else:
			return header, header, lambda x:x

	headers = map(expand, headers)

	# First, we initialize the widths for each column
	colLabels = []
	widths = []
	for name, label, _ in headers:
		widths.append(len(label))
		colLabels.append(label)

	if order:
		rows.sort(lambda x, y: cmp(x.get(order), y.get(order)))

	lines = [ ]
	for entry in rows:
		i = 0
		line = []
		for name, label, formatter in headers:
			if entry.has_key(name):
				e = str(formatter(entry[name]))
			else:
				e = notAvailableLabel
			if len(e) > widths[i]: widths[i] = len(e)
			line.append(e)
			i += 1
		lines.append(line)

	# Then we can display them
	res = formatRow(colLabels, widths)
	res += "\n"
	res += '-'*len(res) + "\n"
	for line in lines:
		res += formatRow(line, widths) + "\n"
	return res


################################################################################
# Tools: get a whole process tree (as a flat list of pids)
################################################################################

def parseStatusFile_linux(filename):
	pid_ = None
	ppid_ = None
	try:
		f = open(filename)
		lines = f.readlines()
		f.close()
		for line in lines:
			if not pid_:
				m = re.match(r'Pid:\s+(.*)', line)
				if m:
					pid_ = int(m.group(1))
			elif not ppid_:
				m = re.match(r'PPid:\s+(.*)', line)
				if m:
					ppid_ = int(m.group(1))
			elif ppid_ and pid_:
				break
	except Exception, e:
		pass
	return (pid_, ppid_)

def parseStatusFile_solaris(filename):
	"""
	according to /usr/include/sys/procfs.h
	
	typedef struct pstatus {
        int     pr_flags;       /* flags (see below) */
        int     pr_nlwp;        /* number of active lwps in the process */
        pid_t   pr_pid;         /* process id */
        pid_t   pr_ppid;        /* parent process id */
	...
	}
	"""
	pid_ = None
	ppid_ = None
	try:
		f = open(filename)
		buf = f.read()
		f.close()
		
		(_, _, pid_, ppid_) = struct.unpack('IIII', buf[:struct.calcsize('IIII')])
	except:
		pass
	return (pid_, ppid_)

def parseStatusFile(filename):
	"""
	Parse a /proc/<pid>/status file,
	according to the current OS.
	
	@rtype: tuple of int 
	@returns: pid, ppid (any of those may be None if not parsed)
	
	Supported:
	- Linux 2.6.x
	- Solaris
	"""
	if sys.platform in [ 'linux', 'linux2' ]:
		return parseStatusFile_linux(filename)
	elif sys.platform in [ 'sunos5' ]:
		return parseStatusFile_solaris(filename)
	else:
		return (None, None)

def getChildrenPids(pid):
	"""
	Retrieves all the children pids for a given pid, 
	including the pid itself as the first element of the returned list of PIDs

	Returns them as a list.
	
	WARNING: only Linux and Solaris-compatible for now,
	as it relies on /proc/<pid>/status pseudo file.
	
	@type  pid: int
	@param pid: the parent pid whose we should retrieve children
	
	@rtype: list of int
	@returns: first the pid itself, then its children's pids
	"""
	pids = [] # a list of current (pid, ppid)
	# Let's scan /proc/...
	# No other way to do it ?
	statusFilenames = glob.glob("/proc/[0-9]*/status")
	for filename in statusFilenames:
		try:
			pid_, ppid_ = parseStatusFile(filename)
			if pid_ and ppid_:
				pids.append( (pid_, ppid_) )
		except:
			pass
	
	# Now let's construct the tree for the looked up pid
	ret = [ pid ]
	ppids = [ pid ]
	while ppids:
		currentPpid = ppids.pop()
		for (pid_, ppid_) in pids:
			if ppid_ == currentPpid:
				if pid_ not in ppids: ppids.append(pid_)
				if pid_ not in ret: ret.append(pid_)
	
	return ret


################################################################################
# Daemon management
################################################################################

def daemonize(pidFilename = None, stdout = None, stderr = None, displayPid = False):
	"""
	Daemonize.
	If pidFilename is provided, used to cat the daemon PID.
	stdout and stderr are file descriptors.
	
	@type  pidFilename: string, or None
	@param pidFilename: if provided, the filename to cat the pid to.
	@type  stdout: fd, or None
	@param stdout: if provided, the FD to redirect stdout to
	@type  stderr: fd, or None
	@param stderr: if provided, the FD to redirect stderr to
	
	@rtype: None
	@returns: None
	"""
	try:
		# First fork
		pid = os.fork()
		if pid:
			# Exit the parent
			os._exit(0)
		
		# Create a new session
		os.setsid()
		
		# Second fork
		pid = os.fork()
		if pid:
			# Exit the original child
			os._exit(0)
		
		# Display some info before closing all std fds
		if displayPid:
			print "Server started as daemon (pid %d)" % os.getpid()
			print "Use kill -SIGINT %d to stop the server when needed." % os.getpid()

		# UMask
		os.umask(0)
		# Workding dir
		os.chdir("/")
	
		# We cat our pid to pidfile
		# (before chaging dir so that relative pidfilenames are possible)
		if pidFilename:
			try:
				f = open(pidFilename, 'w')
				f.write(str(os.getpid()))
				f.close()
			except:
				pass

		# Close file descriptors
		maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
		if maxfd == resource.RLIM_INFINITY:
			maxfd = 65536
		for fd in range(0, maxfd):
			# Only close TTYs, not files, etc
			try:
				os.ttyname(fd)
			except Exception, e:
				continue
			try:
				os.close(fd)
			except Exception, e:
				pass
		
		# Finally we redirect std fds
		if hasattr(os, "devnull"):
			devnull = os.devnull
		else:
			devnull = "/dev/null"
		n = os.open(devnull, os.O_RDWR)
		if stdout is not None: os.dup2(stdout, 1)
		else: os.dup2(n, 1)
		if stderr is not None: os.dup2(stderr, 2)
		else: os.dup2(n, 2)
		return os.getpid()

	except Exception, e:
		# What should we do ?...
		raise e

def cleanup(pidFilename = None):
	"""
	Remove a pid file, if any.
	"""
	if pidFilename and fileExists(pidFilename):
		try:
			os.unlink(pidFilename)
		except:
			pass
		
