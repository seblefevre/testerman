#!/usr/bin/python
##
# Tools to extract the docstring of selected classes (or function)
# in a Python source code.
#
# The source code does not need to be runnable (valid imports, etc),
# as this is done by parsing it.
#
##

import compiler
import gc
import sys
import logging
import optparse


def trim(docstring):
	"""
	docstring trimmer - from PEP 257 sample code
	"""
	if not docstring:
		return ''
	maxint = 2147483647
	# Convert tabs to spaces (following the normal Python rules)
	# and split into a list of lines:
	lines = docstring.expandtabs().splitlines()
	# Determine minimum indentation (first line doesn't count):
	indent = maxint
	for line in lines[1:]:
		stripped = line.lstrip()
		if stripped:
			indent = min(indent, len(line) - len(stripped))
	# Remove indentation (first line is special):
	trimmed = [lines[0].strip()]
	if indent < maxint:
		for line in lines[1:]:
			trimmed.append(line[indent:].rstrip())
	# Strip off trailing and leading blank lines:
	while trimmed and not trimmed[-1]:
		trimmed.pop()
	while trimmed and not trimmed[0]:
		trimmed.pop(0)
	# Return a single string:
	return '\n'.join(trimmed)

class DocstringAstVisitor(compiler.visitor.ASTVisitor):
	"""
	Visits a Python AST for several docstrings.
	Once visited, found docstrings, identified by their
	name in the code namespace, are available in
	the dict as returned by getResults().
	"""
	def __init__(self, searched_names):
		"""
		@type  searched_names: a list of string
		@param searched_names: a list of searched identifier ('MyClass', 'MyClass.my_method', ...)
		"""
		compiler.visitor.ASTVisitor.__init__(self)
		self._searched_names = searched_names
		self._results = {}
	
	def getResults(self):
		return self._results
	
	def walkChildren(self, node, parentName):
		for child in node.getChildNodes():
			self.dispatch(child, '%s.' % parentName)
	
	def visitClass(self, node, parent = None):
		return self._visitNode(node, parent)
		
	def visitFunction(self, node, parent = None):
		return self._visitNode(node, parent)
	
	def _visitNode(self, node, parent):
		if not parent:
			parent = ''

		name = parent + node.name
		if name in self._searched_names:
			self._results[name] = trim(node.doc)

		# Search for inner functions/classes
		self.walkChildren(node.code, name)


def extract_docstrings(code, names, logger):
	"""
	Extracts a docstring from a code.
	
	@type  code: string
	@param code: the code to parse to find the names.
	@type  name: list of strings
	@param name: list of identifiers
	
	@rtype: a dict[string] of strings, or None
	@returns: None in case of a parse error, or a 
	dict containing docstrings indexed by their names.
	No docstring for a found name -> ''
	Name not found -> entry not present in the returned dict
	"""
	res = {} 
	visitor = DocstringAstVisitor(names)
	try:
		mod = compiler.parse(code.strip())
		visitor.preorder(mod, visitor, None)
		res = visitor.getResults()
		del mod, visitor
	except SyntaxError, e:
		logger.warning("Syntax error, file not parsed: %s", str(e))
	gc.collect()
	
	return res

def extract_docstring(code, name, logger):
	res = extract_docstrings(code, [ name ], logger)
	return res.get(name, None)


def main():
	parser = optparse.OptionParser()

	group = optparse.OptionGroup(parser, "Basic Options")
	group.add_option("--filename", dest = "filename", metavar = "FILENAME", help = "python file to extract docstring from")
	group.add_option("--name", dest = "name", metavar = "NAME", help = "class or function name to extract docstring from")
	parser.add_option_group(group)
	(options, args) = parser.parse_args()
	
	if not options.filename:
		parser.error("Missing filename")
	if not options.name:
		parser.error("Missing name")

	with open(options.filename) as f:
		src = f.read()
	
	logger = logging.getLogger()
	ret = extract_docstring(src, options.name, logger)
	if ret:
		print ret

	sys.exit(0)
	
if __name__ == '__main__':
	main()

