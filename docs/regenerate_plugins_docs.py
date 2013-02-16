#!/usr/bin/python
##
# Testerman doc tool that extracts (reST-formatted) docstrings from
# Plugin classes and put them into plugins/autogen as RST documents.
#
# Also create a plugins/autogen/toc.rst file that is included in a toctree in plugins/index.rst
#
##

import plugins_docs
import get_docstring
import logging
import os.path
import sys

# Path to this file
SELF_PATH = os.path.abspath(os.path.dirname(sys.modules[globals()['__name__']].__file__))
# The Testerman source tree root,
# from which plugins will be found
TESTERMAN_SRCROOT = os.path.abspath(os.path.join(SELF_PATH, '..'))

OUTPUT_DOC_PATH = "plugins/autogen"

TOC_FILE = os.path.join(SELF_PATH, OUTPUT_DOC_PATH, "toc.rst")
TESTERMAN_PLUGINS_ROOT = os.path.join(TESTERMAN_SRCROOT, 'plugins')


logger = logging.getLogger()

logging.basicConfig(format = '%(asctime)-15s - %(message)s', level = logging.INFO)



plugins_index = []

for (title, filename, name, docname) in plugins_docs.PLUGINS:
	with open(os.path.join(TESTERMAN_PLUGINS_ROOT, filename)) as f:
		src = f.read()

	doc = get_docstring.extract_docstring(src, name, logger)
	if doc:
		docfilename = os.path.join(SELF_PATH, OUTPUT_DOC_PATH, docname + '.rst')
		logger.info("Creating RST document %s from %s::%s..." % (docname, filename, name))
		try:
			os.mkdir(OUTPUT_DOC_PATH)
		except:
			pass
		with open(docfilename, 'w') as f2:		
			# We add a 'title' to the document
			f2.write(title + '\n')
			f2.write('='*len(title) + '\n\n')
			f2.write(doc)
			plugins_index.append('%s.rst' % (docname))
	

# Now, let's create the toc.rst file, ready to be included into an existing toctree
# in another reST document.
toc = """.. toctree::

%s
""" % '\n'.join([ "   "+x for x in plugins_index])

with open(TOC_FILE, "w") as f:
	f.write(toc)
	logger.info("Plugins toc file %s created." % TOC_FILE)


	
