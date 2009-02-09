#!/usr/bin/env python
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
# (Pluggable) Script to get/set a value in a INI file.
#
# INI file format:
# all values are in a [section]
# comments are ; or # or configurable substrings via property 'comments'
#
# Usage:
# thisfile.py get <filename> <keypath>
# thisfile.py del <filename> <keypath>
# thisfile.py set <filename> <keypath> <value>
#
# where keypath of the form section/key (case insensitive)
#
# If multiple keys are found, only the value of the *last* of them is returned.
# When setting or deleting a key that has multiple values, all of them are
# updated/deleted.
#
# When creating a new key or section, the case provided in the keypath is
# respected.
# The search for a key to update or to get is case insensitive on both section
# and key name.
##


import os
import sys
import string
import ConfigParser
import re
import tempfile


SUPPORTED_CONF_FILE_FORMATS = [ 'ini' ]

class INIParser:
	"""
	This INIParser keeps the case of keys and section names.
	Yet, when getting a section or key, you have to reference it in lowercase
	only.
	
	__sections is a dict[sectionnameinlowercase] = dict of options
	a dict of options is a dict[optionameinlowercase] = (KeyRealNameWithCase, value)
	"""
	def __init__(self, useSpace = True, comments = [ ';', '#' ]):
		# contains (dict of keys) indexed by the sectionamewithoutcase
		# the dict of keys contains (keyWithCase, value) indexed by the keywithoutcase
		# For each section, the key __name__ contains the (sectionNameWithCase, sectionNameWithCase)
		self.__sections = {} 
		self.__useSpace = useSpace
		self.__comments = comments

	def sections(self):
		"""Return a list of section names, excluding [DEFAULT]"""
		# self.__sections will never have [DEFAULT] in it
		return self.__sections.keys()

	def add_section(self, section):
		"""Create a new section in the configuration.

		Raise DuplicateSectionError if a section by the specified name
		already exists.
		"""
		realsection = section
		section = self.sectionxform(section)
		if self.__sections.has_key(section):
			raise ConfigParser.DuplicateSectionError(section)
		self.__sections[section] = { '__name__' : (realsection, realsection) }

	def has_section(self, section):
		"""Indicate whether the named section is present in the configuration.

		The DEFAULT section is not acknowledged.
		"""
		section = self.sectionxform(section)
		return section in self.sections()

	def options(self, section):
		"""Return a list of option names for the given section name."""
		section = self.sectionxform(section)
		try:
			opts = self.__sections[section].copy()
		except KeyError:
			raise ConfigParser.NoSectionError(section)
		if opts.has_key('__name__'):
			del opts['__name__']
		return opts.keys()

	def read(self, filenames):
		"""Read and parse a filename or a list of filenames.

		Files that cannot be opened are silently ignored; this is
		designed so that you can specify a list of potential
		configuration file locations (e.g. current directory, user's
		home directory, systemwide directory), and all existing
		configuration files in the list will be read.	A single
		filename may also be given.
		"""
		for filename in filenames:
			try:
				fp = open(filename)
			except IOError:
				continue
			self.__read(fp, filename)
			fp.close()

	def readfp(self, fp, filename=None):
		"""Like read() but the argument must be a file-like object.

		The `fp' argument must have a `readline' method.	Optional
		second argument is the `filename', which if not given, is
		taken from fp.name.	If fp has no `name' attribute, `<???>' is
		used.

		"""
		if filename is None:
			try:
				filename = fp.name
			except AttributeError:
				filename = '<???>'
		self.__read(fp, filename)

	def get(self, section, option, raw=0, vars=None):
		"""Get an option value for a given section.

		All % interpolations are expanded in the return values, based on the
		defaults passed into the constructor, unless the optional argument
		`raw' is true.	Additional substitutions may be provided using the
		`vars' argument, which must be a dictionary whose contents overrides
		any pre-existing defaults.

		The section DEFAULT is special.
		"""
		section = self.sectionxform(section)
		try:
			sectdict = self.__sections[section].copy()
		except KeyError:
			raise ConfigParser.NoSectionError(section)
		option = self.optionxform(option)
		try:
			rawval = sectdict[option][0]
		except KeyError:
			raise ConfigParser.NoOptionError(option, section)

		return rawval

	def get_case_option_name(self, section, option):
		"""
		Get an option real name (with possible lower/uppercase).
		option is in lowercase.
		"""
		section = self.sectionxform(section)
		try:
			sectdict = self.__sections[section].copy()
		except KeyError:
			raise ConfigParser.NoSectionError(section)
		option = self.optionxform(option)
		try:
			rawval = sectdict[option][1]
		except KeyError:
			raise ConfigParser.NoOptionError(option, section)

		return rawval

	def __get(self, section, conv, option):
		return conv(self.get(section, option))

	def optionxform(self, optionstr):
		return optionstr.lower()
	
	def sectionxform(self, sectionstr):
		return sectionstr.lower()

	def has_option(self, section, option):
		"""Check for the existence of a given option in a given section."""
		section = self.sectionxform(section)
		if not self.has_section(section):
			return 0
		else:
			option = self.optionxform(option)
			return self.__sections[section].has_key(option)

	def set(self, section, option, value):
		"""Set an option."""
		section = self.sectionxform(section)
		try:
			sectdict = self.__sections[section]
		except KeyError:
			raise ConfigParser.NoSectionError(section)
		cleanedoption = self.optionxform(option)
		if sectdict.has_key(cleanedoption):
			option = sectdict[cleanedoption][1] # we retrieve the real option label
		sectdict[cleanedoption] = (value, option)

	def write(self, fp):
		"""Write an .ini-format representation of the configuration state."""
		s = self.sections()
		s.sort()
		for section in s:
			fp.write("[" + self.__sections[section]['__name__'][1] + "]\n")
			sectdict = self.__sections[section]
			k = sectdict.items()
			k.sort()
			for (key, value) in k:
				if key == "__name__":
					continue
				if value[0] is None:
					continue
				if self.__useSpace:
					fp.write("%s = %s\n" % (value[1], value[0]))
				else:
					fp.write("%s=%s\n" % (value[1], value[0]))
			fp.write("\n")

	def remove_option(self, section, option):
		"""Remove an option."""
		section = self.sectionxform(section)
		try:
			sectdict = self.__sections[section]
		except KeyError:
			raise ConfigParser.NoSectionError(section)
		option = self.optionxform(option)
		existed = sectdict.has_key(option)
		if existed:
			del sectdict[option]
		return existed

	def remove_section(self, section):
		"""Remove a file section."""
		section = self.sectionxform(section)
		if self.__sections.has_key(section):
			del self.__sections[section]
			return 1
		else:
			return 0

	#
	# Regular expressions for parsing section headers and options.	Note a
	# slight semantic change from the previous version, because of the use
	# of \w, _ is allowed in section header names.
	SECTCRE = re.compile(
		r'\['								 # [
		r'(?P<header>[^]]+)'					# very permissive!
		r'\]'								 # ]
		)
	# option, spaces/tabs, : or =, spaces/tabs, value [ ;comments]
	OPTCRE = re.compile(
		r'(?P<option>[]\-[\w_.*,(){}$#]+)'
		r'(?P<s1>[ \t]*)(?P<vi>[:=])(?P<s2>[ \t]*)'
		r'(?P<value>.*)$'
		)

	def __read(self, fp, fpname):
		"""Parse a sectioned setup file.

		The sections in setup file contains a title line at the top,
		indicated by a name in square brackets (`[]'), plus key/value
		options lines, indicated by `name: value' format lines.
		Continuation are represented by an embedded newline then
		leading whitespace.	Blank lines, lines beginning with a '#',
		and just about everything else is ignored.
		"""
		cursect = None							# None, or a dictionary
		optname = None
		lineno = 0
		e = None									# None, or an exception
		while 1:
			line = fp.readline()
			if not line:
				break
			lineno = lineno + 1
			# comment or blank line?
			line = line.strip()
			if not line:
				continue
			discard = False
			for c in self.__comments:
				if line.startswith(c):
					discard = True
			if discard:
				continue
			else:
				# is it a section header?
				mo = self.SECTCRE.match(line)
				if mo:
					sectname = self.sectionxform(mo.group('header'))
					if self.__sections.has_key(sectname):
						cursect = self.__sections[sectname]
					else:
						cursect = {'__name__': (mo.group('header'), mo.group('header'))}
						self.__sections[sectname] = cursect
					# So sections can't start with a continuation line
					optname = None
				# no section header in the file?
				elif cursect is None:
					raise ConfigParser.MissingSectionHeaderError(fpname, lineno, `line`)
				# an option line?
				else:
					# Check if this is a key = value line
					# option, spaces/tabs, : or =, spaces/tabs, value [ ;comments]
					OPTWITHCOMMENTSCRE = re.compile(
						r'(?P<option>[]\-[\w_.*,(){}$#]+)'
						r'(?P<s1>[ \t]*)(?P<vi>[:=])(?P<s2>[ \t]*)'			 
						'(?P<value>.*)(?P<comments>\s+[%s].*)$' % '|'.join(self.__comments)
						)

					# First attempt: ignore comments
					mo = OPTWITHCOMMENTSCRE.match(line)
					if not mo:
						mo = self.OPTCRE.match(line)

					if mo:
						optname, vi, optval = mo.group('option', 'vi', 'value')
						optval = optval.strip()
						# allow empty values
						if optval == '""':
							optval = ''
						cursect[self.optionxform(optname)] = (optval, optname) # we backup the real optname, with case information
					else:
						# a non-fatal parsing error occurred.	set up the
						# exception but keep going. the exception will be
						# raised at the end of the file and will contain a
						# list of all bogus lines
						if not e:
							e = ConfigParser.ParsingError(fpname)
#							e.append(lineno, `line`)
		# if any parsing errors occurred, raise an exception
		if e:
			raise e

	def rewrite(self, srclines, fp, useSpace = False):
		"""
		srclines is a readlines()'d file that is used to template what we should write to fp.
		fp the target file descriptor where we should write the target file.

		Write current key and values in it:
		- substituting skel values for existing keys,
		- adding new key=values at the end of each sections.
		"""
		
		writtenkeys = []
		writtensections = []
		cursect = None
		
		# We scan line per line, and make local replacements when needed.
		
		for l in srclines:
			modifiedline = l
			
			# Check if the line starts a new section
			m = self.SECTCRE.match(modifiedline)
			if m:
				# OK, so prior to start a new section, let's write new keys in the section we've just closed
				if cursect:
					# A section was closed, let's add new keys.
					keyadded = False
					for (option, value) in self.__sections[cursect].items():
						# internal keys start with __, for instance __name__
						if not option.startswith('__') and self.optionxform(option) not in writtenkeys: 
							if value[0] is not None:
								fp.write("%s=%s\n" % (value[1], value[0]))
								keyadded = True
					if keyadded:
						fp.write('\n')

				# Now we start a new section:
				# reset the written keys list for the section,
				# store the current section name in cursect
				writtenkeys = []
				cursect = self.sectionxform(m.group('header'))
				fp.write(modifiedline)
				writtensections.append(cursect)
				continue
			
			if not cursect: # no key matching outside a section.
				fp.write(modifiedline)
				continue

			# Check if this is a key = value line
			# option, spaces/tabs, : or =, spaces/tabs, value [ ;comments]
			OPTWITHCOMMENTSCRE = re.compile(
				r'(?P<option>[]\-[\w_.*,(){}$#]+)'
				r'(?P<s1>[ \t]*)(?P<vi>[:=])(?P<s2>[ \t]*)'			 
				'(?P<value>.*)(?P<comments>\s+[%s].*)$' % '|'.join(self.__comments)
				)

			m = OPTWITHCOMMENTSCRE.match(modifiedline)
			if not m:
				m = self.OPTCRE.match(modifiedline)
			if m:
				# OK, operate changes in place
				comments = ''
				if m.lastgroup == 'comments':
					comments = m.group('comments')
				if self.__sections[cursect].has_key(self.optionxform(m.group('option'))):
					value = self.__sections[cursect][self.optionxform(m.group('option'))][0]
					if value is not None:
						modifiedline = m.group('option') + m.group('s1') + m.group('vi') + m.group('s2') + \
							value + comments + '\n'
					else:
						# Remove the option, i.e. remove the line.
						modifiedline = ''
					writtenkeys.append(self.optionxform(m.group('option')))

			fp.write(modifiedline)

		# Now we parsed all lines in the file.
		# Let's check thatt we don't have to add some key in the last known section
		if cursect:
			# A section was closed, let's add new keys.
			for (option, value) in self.__sections[cursect].items():
				# internal keys start with __, for instance __name__
				if not option.startswith('__') and self.optionxform(option) not in writtenkeys: 
					if value[0] is not None:
						fp.write("%s=%s\n" % (value[1], value[0]))
		
		# Finally we add new sections at the end of the file.
		for section, options in self.__sections.items():
			if not section in writtensections:
				fp.write("\n[%s]\n" % section)
				for option, value in options.items():
					if not option.startswith('__'):
						if value[0] is not None:
							fp.write("%s=%s\n" % (value[1], value[0]))
		
		
class GetSet:
	def __init__(self):
		self.properties = { 'comments': [ ';', '#' ] }
	
	def setProperty(self, name, value):
		self.properties[name] = value
	
	def getProperty(self, name, defaultValue):
		return self.properties.get(name, defaultValue)

	def setValue(self, filename, keypath, value):
		"""
		Adds or updates a value,
		automatically creating the section or option key if
		If the keypath selects more that one value, all values are updated.

		If value is None, the key is removed.

		@type  filename: string
		@param filename: the full path to the file to update
		@type  keypath: string
		@param keypath: an xpath path to the value to update
		@type  value: string
		@param value: the value to update

		@rtype: boolean
		@returns: True if OK, False otherwise.
		"""
		try:
			section = '/'.join(keypath.split('/')[:-1])
			key = keypath.split('/')[-1]

			config = INIParser(comments = self.properties['comments'])
			config.read([filename])
			try:
				config.set(section, key, value)
			except ConfigParser.NoSectionError:
				# Do not add a section to remove a key in it :-)
				if value is not None:
					config.add_section(section)
					config.set(section, key, value)

			t = open(filename, "r")
			skeleton = t.readlines()
			t.close()

			tmpfile = tempfile.TemporaryFile()
			try:
				config.rewrite(skeleton, tmpfile, 0)
			except Exception, e:
				tmpfile.close()
				raise Exception("Unable to update %s (%s)" % (filename, str(e)))
			
			tmpfile.seek(0)
			output = tmpfile.read()
			tmpfile.close()

			# unlink the original file to avoid open file problems
			os.remove(filename)
			# WARNING: here we have a risk to lose our file -
			# if we were able to delete it, but unable to recreate it.
			f = open(filename, 'w')
			f.write(output)
			f.close()

			return True
		except Exception, e:
			raise Exception("Unable to update %s (%s)" % (filename, str(e)))

	def getValue(self, filename, keypath):
		"""
		Returns the value corresponding to the keypath.

		@type  filename: string
		@param filename: the full path to the file to read
		@type  keypath: string
		@param keypath: an xpath path to the value to get

		@rtype: string
		@returns: the value, if found, or None otherwise
		"""
		try:
			section = '/'.join(keypath.split('/')[:-1]).lower()
			key = keypath.split('/')[-1].lower()

			config = INIParser(comments = self.properties['comments'])
			config.read([filename])
			value = config.get(section, key)
		except ConfigParser.NoSectionError:
			return None
		except ConfigParser.NoOptionError:
			return None
		except Exception, e:
			raise Exception("Unable to get %s in %s (%s)" % (keypath, filename, str(e)))
		return str(value)



def getInstance():
	ret = GetSet()
	# ret.setProperty('comments', [ ';', '//', '#' ])
	return ret


if __name__ == '__main__':
	def usage():
		print"""Usage:
  %(name)s get <filename> <keypath>
  %(name)s del <filename> <keypath>
  %(name)s set <filename> <keypath> <value>

  where keypath of the form section/key (lowercase only).""" % dict(name = sys.argv[0])
	
	if len(sys.argv) < 3:
		usage()
		sys.exit(1)
	
	try:
		op = sys.argv[1]
		if op == 'set':
			ret = getInstance().setValue(filename = sys.argv[2], keypath = sys.argv[3], value = sys.argv[4])
			if ret:
				print "Value set."
				status = 0
			else:
				print "Unable to set value."
				status = 1
		elif op == 'del':
			ret = getInstance().setValue(filename = sys.argv[2], keypath = sys.argv[3], value = None)
			if ret:
				print "Value deleted."
				status = 0
			else:
				print "Unable to delete value."
				status = 1
		else:
			value = getInstance().getValue(filename = sys.argv[2], keypath = sys.argv[3])
			print value
			if value is None:
				status = 1
			else:
				status = 0
	except Exception, e:
		print "Configuration script exception: %s" % str(e)
		status = 1
	sys.exit(status)

