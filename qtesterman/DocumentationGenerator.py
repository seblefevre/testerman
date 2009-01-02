##
# -*- coding: utf-8 -*-
#
# Documentation generator.
# Wrapper over epydoc CLI.
# Manages doc generation to a cache system.
#
##

from PyQt4.Qt import *

import os
import os.path
import tempfile
import sys
import md5
import tempfile

def log(txt):
	print txt


CACHE_INDEX_FILENAME = "cache.index"

class DocumentationCacheManager(QObject):
	"""
	Manage a cache containing documentations for documentable files (i.e. mainly modules).

	The cache is identified by a cacheRoot directory.

	The cache is a persistent directory (the cache root) (typically in the user home dir)
	containing:
	- cache.index:
		a utf-8 encoded file containing lines:
		key;digest;path
		where:
		- key is a key identifying the resource whose doc is cached (typically a module ID)
		- digest is a md5/sha sum corresponding to the resource, enabling to know if we should
			regenerate the cache or not
		- path is the path relative to the cache root that contains the doc entry point (index.html)
	- one directory per resource, containing its associated docs. The directory name is
		unique and 'random'.
	"""
	def __init__(self, cacheRoot, parent = None):
		"""
		Initialize a cache manager using cacheRoot as cache root directory.
		The cache is initialized upon creation (dir and cache index created).
		So you may get an exception in case of incorrect writing rights.

		@type  cacheRoot: unicode string
		@param cacheRoot: the cache root directory
		"""
		QObject.__init__(self, parent)

		self.cacheRoot = cacheRoot
		self.cacheIndexFilename = self.cacheRoot + '/' + CACHE_INDEX_FILENAME
		
		# Initial directory and index creation
		if not os.path.isdir(self.cacheRoot):
			# May raise some exception if we can't create the dir. Let's the caller get them
			os.makedirs(self.cacheRoot)
		if not os.path.isfile(self.cacheIndexFilename):
			self.saveCacheIndex({})

	def generateDocumentation(self, content, key, force = False):
		"""
		Conditionally generates the doc for the given content.
		If force is True, always regenerates it. Otherwise generate it only if
		the content for this key has been updated or the doc has never been generated.

		@type  content: unicode string
		@param content:
		@type  key: unicode string
		@param key: the key enabling to retrieve the doc later from the cache
		@type  force: boolean
		@param force: if True, force regeneration, regardless of the current cache status

		@rtype: unicode string, or None
		@returns: the complete path to the generated documentation entry point in the cache,
		or None in case of an error.
		"""
		digest = self.getDigest(content)
		e = self.getCacheEntry(key)

		# Cache hit ?
		if not force:
			if e and e[1] == digest:
				log("Documentation cache hit.")
				return os.path.normpath(self.cacheRoot + '/' + e[2] + '/index.html')

		# In all other cases, we have to regenerate the doc.
		# If the entry exists in the case, we reuse its directory
		if e:
			outputDir = self.cacheRoot + '/' + e[2]
		else:
			outputDir = tempfile.mkdtemp(dir = self.cacheRoot)

		(fd, inputFilename) = tempfile.mkstemp()
		f = os.fdopen(fd, 'w')
		f.write(content.encode('utf-8'))
		f.close()

		if self.epydocDocumentation(unicode(key.split('/')[-1]), inputFilename, os.path.normpath(outputDir)):
			os.remove(inputFilename)
			docPath = outputDir[len(self.cacheRoot + '/'):]
			# Finally let's update our cache index.
			self.updateCacheEntry(key, digest, docPath)

			return os.path.normpath(outputDir + '/index.html')

		os.remove(inputFilename)
		return None

	def epydocDocumentation(self, name, inputFilename, outputDir):
		"""
		Calls epydoc to generate (HTML) documentation for filename inputFilename to outputDir.

		@type  name: unicode string
		@param name: the name of the item to document
		@type  inputFilename: unicode string
		@param inputFilename: a path to the file (typically a module) to document with epydoc
		@type  outputDir: unicode string
		@param outputDir: the output directory. Will be created if it does not exist.
		
		@rtype: boolean
		@returns: True if OK, False otherwise
		"""
		cmd = sys.executable
		args = [ '-m', 'epydoc.cli', '--html', 
						 '--fail-on-error', '--parse-only',
						 '--no-frames', # Not supported by QTextBrowser (< Qt 4.4); will be OK for Qt 4.4/WebKit
						 '-n', name,
						 '-o', outputDir, inputFilename ]
		process = QProcess(self)
		process.setProcessChannelMode(QProcess.MergedChannels)
		env = QProcess.systemEnvironment()
		env.append("PYTHONPATH=%s" % QApplication.instance().get('qtestermanpath'))
		process.setEnvironment(env)
		log("Starting documentation generation: " + unicode(args))
		process.start(cmd, args)
		if not process.waitForFinished():
			log("ERROR: unable to finish on time: epydoc output: " + unicode(process.readAll()))
			return False
		else:
			if process.exitCode():
				log("ERROR: epydoc output: " + unicode(process.readAll()))
				return False
			else:
				log("FYI: epydoc output: " + unicode(process.readAll()))
				return True

	def getDigest(self, content):
		"""
		Generates a digest/signature for a content.
		In this implementation, this returns a md5 hash.

		@type  content: unicode string
		@param content: the content to digest

		@rtype: string
		@returns: an ascii string representing the digest.
		"""
		return md5.md5(content.encode('utf-8')).hexdigest()

	def loadCacheIndex(self):
		"""
		Loads the cache index as a dict[key] = (key, digest, docPath)

		@rtype: dict[unicode] of (unicode, string, unicode)
		@returns: the cache index, empty dict is possible or in case of a read error.
		"""
		res = {}
		f = open(self.cacheIndexFilename, 'r')
		lines = f.readlines()
		f.close()
		for line in lines:
			try:
				(key, digest, docPath) = line.strip().split(';')
			except Exception:
				# invalid line, ignore it
				log("Invalid line in cache index (%s), ignoring" % line)
			k = key.decode('utf-8')
			res[k] = ((k, digest, docPath.decode('utf-8')))
		return res

	def getCacheEntry(self, key):
		"""
		Gets the complete cache entry for a key.

		@type  key: unicode string
		@param key: unicode string
		@rtype: tuple (unicode string, string, unicode string) or None
		@returns: a tuple (key, digest, docPath) if the key was found, None otherwise
		"""
		index = self.loadCacheIndex()
		if index.has_key(key):
			return index[key]
		return None

	def updateCacheEntry(self, key, digest, docPath):
		"""
		Updates the cache index with a key;digest;docPath entry.

		@type  docPath: unicode string or string
		@type  key: unicode string or string
		@type  digest: string
		"""
		key = unicode(key).encode('utf-8')
		docPath = unicode(docPath).encode('utf-8')

		index = self.loadCacheIndex()
		index[key] = (key, digest, docPath)
		self.saveCacheIndex(index)

	def saveCacheIndex(self, index):
		"""
		Save the cache index to the persistent storage.

		@type  index: dict[unicode] of (unicode, string, unicode)
		@param index: the cache index, as built by loadCacheIndex()
		"""
		f = open(self.cacheIndexFilename, 'w')
		for key, (_, digest, docPath) in index.items():
			f.write('%s;%s;%s\n' % (key.encode('utf-8'), digest, docPath.encode('utf-8')))
		f.close()
	


