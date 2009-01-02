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
# A basic config (key/value) manager.
#
# Usual singleton model.
# 
##

import copy
import threading


class ConfigManager:
	def __init__(self):
		self._mutex = threading.RLock()
		self._values = {}
		
	def set(self, key, value):
		self._mutex.acquire()
		self._values[key] = value
		self._mutex.release()

	def get(self, key, defaultValue = None):
		self._mutex.acquire()
		ret = self._values.get(key, defaultValue)
		self._mutex.release()
		return ret

	def getValues(self):
		self._mutex.acquire()
		ret = copy.copy(self._values)
		self._mutex.release()
		return ret
	
def instance():
	global TheConfigManager
	if TheConfigManager is None:
		TheConfigManager = ConfigManager()
	return TheConfigManager


TheConfigManager = None

# Convenience shortcuts
def set(key, value):
	return instance().set(key, value)

def get(key, defaultValue = None):
	return instance().get(key, defaultValue)
