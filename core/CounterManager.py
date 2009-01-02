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
# -*- coding: utf-8 -*-
# A general purpose Stat class for counter-based statistics.
#
# A CounterManager is a thread-safe class managing counters.
# A counter can be incremented, decremented. A counter has also some extensible properties, denoted _<property name>, for instance _max.
#
# A counter is identified by a path in python-like module notation ("path.to.counter.and.the.like").
# 
# To get a property value, use CounterManager.get("path.to.counter") or CounterManager.get("path.to.counter._max"), etc.
# The counter native value is acutally stored in a property named "default".
#
# Counters are naturally ordered in a tree, and retrieving a property for a non-terminal counter returns the sum
# of the property for the descendent terminal counters.
#
# Properties can only be retrieved through get(), and not inc()'d or dec()'d (or reset()'d) - i.e. Properties are Read Only.
# Counters can only be inc()'d and dec()'d (and reset()'d), and cannot be get()'d (you get the 'default' property, in fact).
# i.e. Counters are Write only.
#
# inc()'d or dec()'d counters are automatically added/created if needed.
# You may assign new properties to a counter at any time, but they'll be updated only thereafter, of course.
#
# addCounter(path) enables to explicitly create a counter.
#
##

import time
import threading

class CounterProperty:
	"""
	A Property is a value that can be updated through property-dependent rules.
	Base class for these properties.
	
	methods inc/dec are called whenever the associated counter is inc/dec.
	"""
	def __init__(self, name):
		self.name = name
		self.value = 0
	
	def get(self):
		return self.value
	
	def inc(self, v = 1):
		self.value += v
	
	def dec(self, v):
		self.value -= v
	
	def reset(self):
		self.value = 0


class MaxCounterProperty(CounterProperty):
	"""
	Manage a max for a counter.
	"""
	def __init__(self):
		CounterProperty.__init__(self, 'max')
		self.__current = 0
	
	def inc(self, v = 1):
		self.__current += v
		if self.__current > self.value:
			self.value = self.__current
	
	def dec(self, v = 1):
		self.__current -= v

class AverageCounterProperty(CounterProperty):
	"""
	Manage an average over time for the associated counter.
	"""
	def __init__(self):
		CounterProperty.__init__(self, 'max')
		self.__count = 0
		self.__lasttime = None
		self.__current = 0
	
	def inc(self, v = 1):
		t = time.time()
		
		self.__lasttime = t
		self.__current += v
	
	def get(self):
		"""
		Reimplemented to take the duration spent at current value into account
		"""
		return 0
	


class Counter:
	"""
	A counter is the object that manager a... counter and associated properties.
	On a counter, you may call:
	inc()
	dec()
	reset()
	get()
	get(propertyName), for instace get("max"), get("min"), etc, depending on the properties set on the counter.
	get() is equivalent to get("default"), corresponding to a default counter.
	"""
	def __init__(self, name):
		self.name = name
		self.properties = {}
		self.addProperty(CounterProperty("default"))
	
	def addProperty(self, p):
		self.properties['_' + p.name] = p

	def reset(self):
		for k, v in self.properties.items():
			v.reset()
	
	def inc(self, val = 1):
		for k, v in self.properties.items():
			v.inc(val)

	def dec(self, val = 1):	
		for k, v in self.properties.items():
			v.dec(val)

	def get(self, propertyName = "default"):
		p = "_" + propertyName
		if self.properties.has_key(p):
			return self.properties[p].get()
		else:
			return 0

class CounterNode:
	"""
	Boxing class for a counter within a counter tree, with possible childrens.
	"""
	def __init__(self, name):
		"""
		name is a local name within the counter tree.
		"""
		# This is not optimised: the counter is actually used only if terminal.
		# If we have children, is ignored.
		self.counter = Counter(name)
		# Optional child counters, indexed by their local name.
		self.children = {}

	def get(self, propertyName = "default"):
		"""
		Get the value for a node.
		If we have children, this is the cumulative value for all children.
		Else this is the counter.
		"""
		if self.children != {}:
			ret = 0
			for k, v in self.children.items():
				ret += v.get(propertyName)
			return ret
		else:
			return self.counter.get(propertyName)
	
	def reset(self):
		# Maybe we are a terminal node
		self.counter.reset()
		# Maybe not
		for k, v in self.children.items():
			v.reset()


class CounterManager:
	"""
	Main class managing counters within a tree.
	Can add and retrieve counters, etc.
	"""
	def __init__(self):
		# Root counters.
		self.root = CounterNode("root")
		self.mutex = threading.RLock()

	def __getCounters(self, path):
		"""
		counterName is a string, a path to the counter.
		Returns a list of counters matchin the path that may contain wildcards.
		Returns a single counter object list if only one counter matched the path
		Returns an empty list if no counter was found.
		
		path is in dot notation (a.path.to.a.counter)
		* is the only wildcard accepted, as a complete path element only 
		(a.*.to.a.counter is valid, a.pa*.to.a.counter is not)
		"""
		if "_" in path: # No property in such a path.
			return []
		names = path.split('.')
		res = []
		currentNode = self.root
		for name in names:
#			if name == '*':
			if currentNode.children.has_key(name):
				res = [ currentNode.children[name].counter ]
				currentNode = currentNode.children[name]
			else:
				res = []
				break
		
		# Termination: names consumed, selected counters are in res.
		return res

	def __getNodeByPath(self, path):
		"""
		Retrive a CounterNode based on a explicit path (no property, no wildcards)
		"""
		if "*" in path or "_" in path:
			return None

		currentNode = self.root
		for name in path.split('.'):
			if currentNode.children.has_key(name):
				currentNode = currentNode.children[name]
			else:
				return None # non-existing counter, default value.
		return currentNode

	def inc(self, path, val = 1):
		"""
		Increment one counter.
		path is a wildcard-less and property-less string (otherwise do nothing)
		If the counter does not exist, create it on the fly.
		
		NB: incrementing or decrementing a non-terminal node is useless, since when we'll get a value, only children values will be used.
		"""
		self.mutex.acquire()
		node = self.__getNodeByPath(path)
		if not node:
			counter = self.addCounter(path)
		else:
			counter = node.counter

		counter.inc(val)
		self.mutex.release()

	def dec(self, path, val = 1):
		self.mutex.acquire()
		node = self.__getNodeByPath(path)
		if not node:
			counter = self.addCounter(path)
		else:
			counter = node.counter

		counter.dec(val)
		self.mutex.release()
	
	def addCounter(self, path):
		"""
		Add a new counter in the tree, and return it.
		"""
		if "*" in path or "_" in path:
			return None
		
		counters = self.__getCounters(path)
		if not (counters == []):
			return counters[0] # already exists, return it.
		
		currentNode = self.root
		for name in path.split("."):
			if currentNode.children.has_key(name):
				currentNode = currentNode.children[name]
			else:
				currentNode.children[name] = CounterNode(name)
				currentNode = currentNode.children[name]
		
		return currentNode.counter		

	def get(self, path):
		"""
		Returns the value of the counter identified by path.
		path may contain a property.
		
		If the counter is not final (i.e. has children), the sum of all the children is returned, with regards to the optional property.
		
		Returns None if the counter cannot be found.
		"""
		self.mutex.acquire()
		names = path.split(".")
		if len(names) > 0 and names[-1].startswith('_'):
			propertyName = names[-1][1:]
			names = names[:-1]
		else:
			propertyName = "default"

		node = self.__getNodeByPath('.'.join(names))		
		
		if node:
			ret = node.get(propertyName)
		else:
			ret = None
		self.mutex.release()
		return ret

	def reset(self, path):
		ret = False
		self.mutex.acquire()
		node = self.__getNodeByPath(path)		
		
		if node:
			node.reset()
			ret = True
		self.mutex.release()
		return ret
		
	def __getTerminalValues(self, baseNode, basename):	
		"""
		Return a dict of { path: value } for all terminal counters.
		Useful for debug.
		"""
		ret = {}
		currentNode = baseNode
		for (name, node) in currentNode.children.items():
			if basename:
				path = basename + '.' + name
			else:
				path = name
			if node.children == {}:
				ret[path] = node.counter.get()
			else:
				# Merge dict with the one from the recursive call
				for k, v in self.__getTerminalValues(baseNode = node, basename = path).items():
					ret[k] = v
		return ret

	def getAllTerminalValues(self):
		self.mutex.acquire()
		ret = self.__getTerminalValues(baseNode = self.root, basename = None)
		self.mutex.release()
		return ret


TheCounterManager = None

def instance():
	global TheCounterManager
	if TheCounterManager is None:
		TheCounterManager = CounterManager()
	return TheCounterManager



##
# Some tests
##

def autotest():
	cm = CounterManager()
	finalCounters = [ 'server.requests.fail', 'server.requests.pass', 'server.requests.timeout', 'server.uptime', 'maxclients' ]
	nonFinalCounters = [ 'server', 'server.requests', 'maxclients' ]
	
	for c in finalCounters:
		print "%s: %s" % (c, str(cm.get(c)))
		
	for c in finalCounters:
		cm.inc(c)

	print		
	for c in finalCounters:
		print "%s: %s" % (c, str(cm.get(c)))

	print		
	for c in nonFinalCounters:
		print "%s: %s" % (c, str(cm.get(c)))

	for c in finalCounters:
		cm.dec(c)
	
	cm.inc('server.requests.pass')
	cm.inc('server.requests.pass')
	cm.inc('server.requests.pass')
	cm.inc('server.requests.pass')
	cm.inc('server.requests.newstate')

	print		
	for c in finalCounters:
		print "%s: %s" % (c, str(cm.get(c)))

	print		
	for c in nonFinalCounters:
		print "%s: %s" % (c, str(cm.get(c)))
	

	c = cm.addCounter('server.running.job.ats')
	c.addProperty(MaxCounterProperty())
	c = cm.addCounter('server.running.job.campaign')
	c.addProperty(MaxCounterProperty())
	
	cm.inc('server.running.job.ats', 5)
	cm.inc('server.running.job.ats')
	cm.inc('server.running.job.ats')
	cm.dec('server.running.job.ats')
	cm.inc('server.running.job.ats')
	cm.dec('server.running.job.ats')
	cm.inc('server.running.job.campaign')
	cm.dec('server.running.job.ats')
	cm.dec('server.running.job.ats')
	cm.inc('server.running.job.ats')
	

	# A complete summary
	print
	allCounters = cm.getAllTerminalValues().items()
	allCounters.sort()
	for e in all:
		print "%s: %d" % e

	print
	c = 'server.running.job.ats'
	print "%s: %s" % (c, str(cm.get(c)))
	c = 'server.running.job'
	print "%s: %s" % (c, str(cm.get(c)))
	c = 'server.running.job.ats._max'
	print "%s: %s" % (c, str(cm.get(c)))
	c = 'server.running.job.campaign._max'
	print "%s: %s" % (c, str(cm.get(c)))
	c = 'server.running.job._max'
	print "%s: %s" % (c, str(cm.get(c)))
	
if __name__ == '__main__':
	autotest()


	

