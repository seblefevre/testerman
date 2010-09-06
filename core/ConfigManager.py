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
# A basic config (key/value) manager.
#
# Usual singleton model.
# 
##

import copy
import threading
import re
import logging


################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('CM')


################################################################################
# Exceptions
################################################################################

# Unregistered key when setting something
class KeyException(Exception): pass

# Transformation error (on user set or commit)
class TransformException(Exception): pass


################################################################################
# ConfigManager
################################################################################


class ConfigManager:
	"""
	This configuration manager evolved slighlty.
	
	It manages two kinds of variables: persistent, and transient.
	Persistent variables may be read/written from/to a conf file.
	Transient variables are limited to memory usage only.
	
	Persistent keys must be registered explicitly before being set.
	Upon registration, we specify:
	- a defaut value (and indirectly a type)
	- a flag indicating that an update is taken into account without restarting
	 (dynamic vs static)

	Persistent keys have multiple values:
	- a default value - mandatory
	- a user-provided value (via set_user()) - must be the same type as
	  the default value (the usual coercion rules apply) - persisted
	- an actual value, provided internally (via set_actual()),
	  no constraint on type. This value is not persisted (i.e. is transient)


	Transient keys may be set at any time, and do not have a default value.
	They are just used as "system-wide" variables.
	"""
	def __init__(self):
		self._mutex = threading.RLock()
		self._persistent = {}
		self._transient = {}

	##
	# Persistent values management
	##
	def to_bool(self, v):
		if isinstance(v, (bool, int)):
			return bool(v)
		if isinstance(v, basestring):
			return v.lower() in [ '1', 'true', 't', 'on' ]
		return False	

	def register(self, key, default, dynamic = False, xform = lambda x: x):
		"""
		Registers a new persistent variable.
		
		xform is a transformation to apply when committing the value
		(i.e. when making it actual).
		"""
		# format is a friendly label for the format
		# user_xform is a transformation function to turn a user-set value
		# into an acceptable value (same type as the default one)
		if isinstance(default, basestring):
			user_xform = str
			format = "string"
		elif isinstance(default, bool):
			user_xform = self.to_bool
			format = "boolean"
		elif isinstance(default, int):
			user_xform = int
			format = "integer"
		elif isinstance(default, float):
			user_xform = float
			format = "float"
		else:
			raise Exception("Unable to register persistent variable %s: unsupported type" % (key))

		self._mutex.acquire()
		self._persistent[key] = dict(default = default, user_xform = user_xform, actual_xform = xform, dynamic = dynamic, format = format)
		self._mutex.release()
		
	def set_user(self, key, value, autoCommit = False, autoRegister = False):
		"""
		Updates a persistent variable.
		
		If the variable is static (non-dynamic),
		on first user-set, the value is also made actual, unless an actual value
		already exists.
		
		A None value does nothing
		(so that set_user(self, key, None) simply does not replace an
		 existing user-provided value).
		
		If the user-provided value is to be reset, use reset_user(key) instead.
		
		When autoCommit is set, the user-provided value is committed (thus transformed to
		an actual value) only if there is not an existing actual value.
		
		If autoRegister is set, allows a new key to be registered if it does not exist
		yet.
		"""
		if value is None:
			return
		ex = None
		self._mutex.acquire()
		try:
			if not self._persistent.has_key(key) and autoRegister:
				self.register(key, value)
			v = self._persistent[key]
			# transform the value into the correct type
			v["user"] = v["user_xform"](value)
			if autoCommit and not v.has_key("actual"):
				# Make actual - can be modified afterwards
				v["actual"] = v["actual_xform"](v["user"])
		except KeyError:
			ex = KeyException("Attempted to set unregistered configuration variable %s to user-provided value %s" % (key, value))
		except Exception:
			ex = TransformException("Unable to set persistent variable %s to %s - cannot convert to expected type" % (key, value))
		self._mutex.release()
		if ex:
			raise ex

	def reset_user(self, key):
		"""
		Indicates that the user explicitly reset the value he/she provided, or
		that he/she does not want a value to be taken into account for this parameter.
		"""
		self._mutex.acquire()
		try:
			v = self._persistent[key]
			v["user"] = None # reset the value
		except:
			getLogger().error("Attempted to reset unregistered configuration variable %s" % (key))
		self._mutex.release()
	
	def commit(self, key = None):
		"""
		Makes sure the current value (user or default) is made
		the actual value too.
		
		Raises exceptions on commit transformation errors.
		"""
		if key is None:
			return self.commitAll()

		ex = None
		self._mutex.acquire()
		try:
			v = self._persistent[key]
			if v.has_key("user"):
				v["actual"] = v["actual_xform"](v["user"])
			else:
				v["actual"] = v["actual_xform"](v["default"])
		except KeyError:
			ex = KeyException("Cannot commit unregistered persistent variable %s" % key)
		except Exception, e:
			ex = TransformException("Unable to commit persistent variable %s: transformation error (%s)" % (key, str(e)))
		self._mutex.release()
		if ex:
			raise ex

	def commitAll(self):
		"""
		Commits all existing values.
		"""
		for k in self.getKeys():
			self.commit(k)

	def set_actual(self, key, value):
		"""
		Explicitly sets an actual value for a persistent variable.
		This is the transient part of a persistent variable:
		
		The type can be different from the default/set value.
		
		Normally, this actual value is automatically computed when calling commit().
		However, the caller may want to override it with a more complex
		transformation, if needed.
		"""
		self._mutex.acquire()
		try:
			v = self._persistent[key]
			v["actual"] = value
		except KeyError:
			print ("Attempted to set unregistered configuration variable %s to actual value %s" % (key, value))
			getLogger().error("Attempted to set unregistered configuration variable %s to actual value %s" % (key, value))
		self._mutex.release()

	def get(self, key):
		"""
		Gets a persistent variable value.
		Returns the actual / or the user-provided / or the default value
		"""
		ret = None
		self._mutex.acquire()
		try:
			if self._persistent.has_key(key):
				v = self._persistent[key]
				# Current value (if any), or defaulted to defaut
				# Notice that None is a valid current value
				if v.has_key('actual'):
					ret = v['actual']
				elif v.has_key('user'):
					ret = v['user']
				else:
					ret = v['default']
		except Exception, e:
			print ("Error while accessing key %s: %s" % (key, str(e)))
			getLogger().error("Error while accessing key %s: %s" % (key, str(e)))
		self._mutex.release()
		return ret

	def getKeys(self):
		"""
		Returns persistent variable names only.
		"""
		self._mutex.acquire()
		ret = self._persistent.keys()
		self._mutex.release()
		return ret

	def getVariables(self):
		"""
		Returns the persisted variables and their current values
		(actual, user-provided, default)
		
		as a list of dict(actual, default, user, key, dynamic)
		"""
		ret = []
		self._mutex.acquire()
		for k, v in self._persistent.items():
			d = copy.copy(v)
			# strip the xforms
			del d['user_xform']
			del d['actual_xform']
			d['key'] = k
			ret.append(d)
		self._mutex.release()
		return ret
	
	def read(self, filename, autoRegister = False):
		"""
		Loads persistent variables from a file.
		"""
		try:
			f = open(filename)
			for l in f.readlines():
				m = re.match(r'\s*(?P<key>[^#].*)=(?P<value>.*)', l.strip())
				if m:
					try:
						self.set_user(m.group('key').strip(), m.group('value').strip(), autoRegister = autoRegister)
					except KeyException:
						pass
			f.close()
		except Exception, e:
			raise Exception("Unable to read configuration file '%s' (%s)" % (filename, str(e)))

	def write(self, filename):
		"""
		Writes persistent variables to a file.
		"""
		contents = ""
		values = self.getValues()
		values.sort(lambda x, y: cmp(x.get('key'), y.get('key')))
		contents = "\n".join([ "%s = %s" % (x['key'], x.get('user', x.get('default', ''))) for x in values])
		try:
			f = open(filename, "w")
			f.write(contents)
			f.close()
		except Exception, e:
			raise Exception("Unable to save current configuration to file '%s' (%s)" % (filename, str(e)))

	##
	# Transient variables management
	##
	def set_transient(self, key, value):
		self._mutex.acquire()
		self._transient[key] = value
		self._mutex.release()

	def get_transient(self, key, defaultValue = None):
		"""
		Gets a transient variable value. If not found, the defautValue is returned.
		"""
		self._mutex.acquire()
		ret = self._transient.get(key, defaultValue)
		self._mutex.release()
		return ret

	def getTransientVariables(self):
		self._mutex.acquire()
		ret = [ dict(key = k, value = v) for k, v in self._transient.items() ]
		self._mutex.release()
		return ret
	
	
def instance():
	global TheConfigManager
	if TheConfigManager is None:
		TheConfigManager = ConfigManager()
	return TheConfigManager

TheConfigManager = None

