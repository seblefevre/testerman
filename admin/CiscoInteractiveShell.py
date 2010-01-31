# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2010 Sebastien Lefevre and other contributors
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
# A cisco-like command-line shell, using
# "inline" value tree representations,
# based on a syntax that could be described with ASN.1 primitives
# (sequence, choice, integer, string)
#
# Enables support for command completion,
# command argument parsing (value tree), and command
# execution.
# 
#
# Low-level input handling, however, is based on readline or other adapters.
#
#
# Usage:
# - create a CommandContext and register one or multiple commands
# in it. These commands have a syntax tree based on a SequenceNode.
# - ... 
# 
#
##

import sys

def getBacktrace():
	import traceback
	import StringIO
	backtrace = StringIO.StringIO()
	traceback.print_exc(None, backtrace)
	ret = backtrace.getvalue()
	backtrace.close()
	return ret

##
# Tools/output pretty printers
##

def formatTable(header = [], distList = []):
	"""
	Pretty format the list of dict according to the header list.
	Header names not found in the dict are not displayed, and
	only header names found in the dict are displayed.
	
	Header is a list of either simple string (name) or tuple (name, label).
	If it is a tuple, label is used to display the header, and name
	to look for the element in the dicts.
	"""
	def formatRow(cols, widths):
		"""
		Formatting helper: row pretty print.
		"""
		line = " %s%s " % (cols[0], (widths[0]-len(cols[0]))*' ')
		for i in range(1, len(cols)):
			line = line + "| %s%s " % (cols[i], (widths[i]-len(cols[i]))*' ')
		return line

	# First, we compute the max widths for each col
	colLabels = []
	widths = []
	for h in header:
		try:
			name, label = h
		except:
			label = h
		widths.append(len(label))
		colLabels.append(label)

	lines = [ ]
	for entry in distList:
		i = 0
		line = []
		for h in header:
			try:
				name, label = h
			except:
				name = h
			if entry.has_key(name):
				e = str(entry[name])
				if len(e) > widths[i]: widths[i] = len(e)
				line.append(e)
			else:
				line.append('') # element not found for this dict entry
			i += 1
		lines.append(line)

	# Then we can display them
	res = formatRow(colLabels, widths)
	res += "\n"
	res += '-'*len(res) + "\n"
	for line in lines:
		res += formatRow(line, widths) + "\n"
	return res

def formatForm(header = [], values = {}):
	"""
	Pretty format the dict according to the header list, as a form.
	Header names not found in the dict are not displayed, and
	only header names found in the dict are displayed.
	
	Header is a list of either simple string (name) or tuple (name, label).
	If it is a tuple, label is used to display the header, and name
	to look for the element in the dict of values.
	
	Support multiline values.
	"""
	# First, we compute the max width for the label column
	labelWidth = 0
	for h in header:
		try:
			name, label = h
		except:
			label = h
		labelWidth = max(labelWidth, len(label))
	
	labelWidth += 1 # includes the automatically added ':'

	lines = [ ]
	for h in header:
		try:
			name, label = h
		except:
			name = h
			label = h
		
		value = ""
		if values.has_key(name):
			value = str(values[name])
		
		# Support for multilines
		value = value.split('\n')
		lines.append((" %%-%ss  %%s" % labelWidth) % (label+":", value[0]))
		for v in value[1:]:
			lines.append((" %%-%ss  %%s" % labelWidth) % ("", v))

	return "\n".join(lines)		


##
# Some usual exceptions
##

class ParsingException(Exception):
	"""
	An exception forward mechanism enables
	to reconstruct the path to the node that raises
	the exception on the fly.
	"""
	def __init__(self, error = ""):
		self._error = error
		self._forwarded = False

	def forwardAs(self, name):
		if not self._forwarded:
			# first node naming
			self._error = "%s: %s" % (name, self._error)
			self._forwarded = True
		else:
			# Continue to construct the node path
			self._error = "%s.%s" % (name, self._error)
		raise self

	def __str__(self):
		return self._error

class InvalidSyntax(ParsingException):
	pass

class UnexpectedToken(ParsingException):
	pass

class MissingToken(ParsingException):
	pass

class ShellExit(Exception):
	pass



##
# Supported command syntax trees
##

class SyntaxNode:
	"""
	Syntax tree node base class.
	
	A syntax node enables to define syntax trees
	for command arguments.
	
	The name and description of the node are properties of the
	association between the node and its parent.
	
	This way, a SyntaxNode with child could be considered
	as a fully resuable type, registered into different
	context with different description and naming.
	"""

	# type description - to override in each subclass
	_typeName = "<undefined>"
	
	def __init__(self):
		pass
	
	def __str__(self):
		return "%s" % (self._typeName)	
	
	# To implement in sub-classes
	
	def suggestNextTokens(self, tokens):
		"""
		Returns a list of possible next tokens to continue
		the current tokenized line.
		
		Returns it as a list of (token, description), followed by a flag
		indicating whether this node requires one of these
		completion suggestions, or if the branch is already
		completed (all mandatory tokens are already provided), followed
		by the remaining tokens (exactly as in parse())
		
		(True = one of these suggestions is required. False: I'm ok with
		 what I have now)
		
		This requires a value tree computation. May raise a syntax
		error/unexpected token exception if needed.
		"""
		return [], False, tokens
	
	def parse(self, tokens):
		"""
		Generates a value tree by parsing the tokenized line (list of strings).
		The first token of this list corresponds to this syntax node.
		The syntax node is guaranteed to accept it as a valid value
		as isValid() is called on it prior to be passed to a getValue().
		
		The Testerman usual struct representation convention is used:
		dict for "sequence"-like parameters (normal command parameters),
		tuple (name, value) for	choices.
		Value lists are currently not supported.
		
		@raises InvalidSyntax in case of a syntax error
		@raises UnexpectedToken in case of an invalid continuation
		@raises MissingToken in case of a missing mandatory continuation
		
		@type  tokens: list of strings
		@param tokens: tokenized line, starting at the value to be parsed
		               by this syntax node (and the next one, if any)
		
		@rtype: tuple (object, list of strings)
		@returns: the parsed value as a value tree, and
		          the list of unconsummed tokens.
		"""
		raise InvalidSyntax()
		
	
##
# Primitive syntax nodes
##

class StringNode(SyntaxNode):
	"""
	Simple string node.
	"""
	_typeName = "<string>"
	
	def __init__(self):
		SyntaxNode.__init__(self)

	def parse(self, tokens):
		if not tokens:
			raise MissingToken("missing value")

		return (tokens[0], tokens[1:])
	
	def suggestNextTokens(self, tokens):
		if not tokens:
			# Suggest the user to enter a string value
			return [ (None, "a string value") ], True, tokens
		else:
			# no suggestion
			return [], False, tokens[1:]
		

class IntegerNode(SyntaxNode):
	"""
	Simple integer node.
	"""
	
	_typeName = "<integer>"
	
	def __init__(self):
		SyntaxNode.__init__(self)

	def parse(self, tokens):
		if not tokens:
			raise MissingToken("missing value") 
		try:
			int(tokens[0])
		except:
			raise InvalidSyntax("integer value expected")
		return (int(tokens[0]), tokens[1:])

	def suggestNextTokens(self, tokens):
		if not tokens:
			# Suggest to enter an integer value
			return [ (None, "an integer value") ], True, tokens
		else:
			try:
				int(tokens[0])
			except:
				raise InvalidSyntax("integer value expected")
			return [], False, tokens[1:]


class NullNode(SyntaxNode):
	"""
	'constant'-like. Useful in choices.
	"""
	
	_typeName = "<null>"
	
	def __init__(self):
		SyntaxNode.__init__(self)

	def parse(self, tokens):
		return (None, tokens)

	def suggestNextTokens(self, tokens):
		# nothing to suggest
		return [], False, tokens


class SequenceNode(SyntaxNode):
	"""
	Contains named values.
	
	When valuated, returns a dict.
	
	MyType ::= SEQUENCE {
		field1 INTEGER optional, -- this is field1
		field2 String -- optional field2
	}
	
	would be declared as:
	MyType = SequenceNode()
	MyType.addField("field1", "this is field1", IntegerNode(), True)
	MyType.addField("field2", "optional field2", StringNode())
	"""
	
	_typeName = "<sequence>"
	
	def __init__(self):
		SyntaxNode.__init__(self)
		self._fields = {}
	
	def addField(self, fieldName, description, syntaxNode, optional = False):
		"""
		Declares a new field in the sequence.
		""" 
		self._fields[fieldName] = (description, syntaxNode, optional)
		return self

	def parse(self, tokens):
		"""
		Returns a dict {fieldName: value}
		
		All mandatory fields must be filled.
		If not, an exception is raised.
		"""
		ret = {}
		parsedFields = []

		nextTokens = tokens
		
		while nextTokens:
			fieldName = nextTokens[0]
			if not fieldName in self._fields:
				break
			
			if fieldName in parsedFields:
				raise UnexpectedToken("duplicated field %s" % (fieldName))
			parsedFields.append(fieldName)

			try:
				v, nextTokens = self._fields[fieldName][1].parse(nextTokens[1:])
			except ParsingException, e:
				e.forwardAs(fieldName)
			ret[fieldName] = v
			
		# Check if we have all mandatory fields
		for fieldName, (description, node, optional)  in self._fields.items():
			if not optional and not fieldName in parsedFields:
				raise MissingToken("missing mandatory field %s (%s)" % (fieldName, description))

		return (ret, nextTokens)		

	def suggestNextTokens(self, tokens):
		suggestions = []
		completionRequired = False
		parsedFields = []
		nextTokens = tokens
		
		# Parse
		while nextTokens:
			fieldName = nextTokens[0]
			if not fieldName in self._fields:
				break
			
			if fieldName in parsedFields:
				raise UnexpectedToken("duplicated field %s" % (fieldName))
			parsedFields.append(fieldName)
			
			# Check if the current field wants to complete something or not
			try:
				suggestions, completionRequired, nextTokens = self._fields[fieldName][1].suggestNextTokens(nextTokens[1:])
			except ParsingException, e:
				e.forwardAs(fieldName)

			if completionRequired:
				if nextTokens:
					# well, this field could have consumed other tokens,
					# but it did not: missing a token somewhere
					raise MissingToken("field %s misses a value" % (fieldName))
				else:
					# OK, first suggest to complete this token
					break
			
			# otherwise, just continue with the next possible field


		# Now, let's analyse our current state	
		if not nextTokens:
			# The line ends here - we can propose some suggestions to continue it
			if completionRequired:
				return suggestions, completionRequired, nextTokens
			else:
				# in this case, we may complete with:
				# optional tokens for the last started field branch
				# and any non-entered field names in the current sequence
				for fieldName, (description, node, optional) in self._fields.items():
					if not fieldName in parsedFields:
						# we prefix the description with a * for mandatory fields
						suggestions.append((fieldName, (not optional and "*" or "") + description))
						if not optional:
							# At least one non-optional field: completion required.
							completionRequired = True
				return suggestions, completionRequired, nextTokens

		else:
			# The line has not been consumed completely - just check that
			# we have all our mandatory fields
			for fieldName, (description, node, optional)  in self._fields.items():
				if not optional and not fieldName in parsedFields:
					raise MissingToken("missing mandatory field %s (%s)" % (fieldName, description))

			# OK, we have everything, and nothing can't be completed at
			# our level (i.e. in this node branch) anymore
			return [], False, nextTokens
	

class ChoiceNode(SyntaxNode):
	"""
	Equivalent of a ASN.1 CHOICE:
	
	MyType ::= CHOICE {
		choice1 INTEGER, -- this is choice 1
		choice2 String -- this is choice 2
	}
	
	translates into:
	MyType = ChoiceNode()
	MyType.addChoice("choice1", "this is choice 1", IntegerNode())
	MyType.addChoice("choice2", "this is choice 2", StringNode())
	"""
	
	_typeName = "<choice>"
	
	def __init__(self):
		SyntaxNode.__init__(self)
		self._choices = {}
	
	def addChoice(self, name, description, syntaxNode):
		self._choices[name] = (description, syntaxNode)
		return self # enable cascading multiple addChoice()

	def addChoices(self, choices):
		for choiceName, choiceDescription, syntaxNode in choices:
			self.addChoice(choiceName, choiceDescription, syntaxNode)
		return self
	
	def parse(self, tokens):
		"""
		For a choice, returns a tuple (choiceName, value)
		"""
		if not tokens:
			raise MissingToken("missing choice name") 
		# Check that we have one of or choice names
		choiceName = tokens[0]
		if choiceName in self._choices:
			try:
				v, remaining = self._choices[choiceName][1].parse(tokens[1:])
			except ParsingException, e:
				e.forwardAs(choiceName)

			return ( (choiceName, v), remaining )
		else:
			raise InvalidSyntax("invalid choice name (%s)" % (choiceName))

	def suggestNextTokens(self, tokens):
		if not tokens:
			# Suggest one choice
			suggestions = []
			for choiceName, (choiceDescription, node) in self._choices.items():
				suggestions.append((choiceName, choiceDescription))
			return suggestions, True, tokens

		else:
			# Delegate to the selected choice
			choiceName = tokens[0]
			if choiceName in self._choices:
				try:
					return self._choices[choiceName][1].suggestNextTokens(tokens[1:])
				except ParsingException, e:
					e.forwardAs(choiceName)
			else:
				raise InvalidSyntax("invalid choice name (%s)" % (choiceName)) 



##
# Command Context
#
# A special container to register commands whose exec line
# is usually a sequence node.
#
# A context is created and managed by a ContextManager,
# enabling sub-context navigation.
##

class CommandContext(ChoiceNode):
	"""
	A special container to register commands whose exec line is
	usually a sequence node.
	
	A context must be registered into a ContextManager to
	be reachable. Such a registration enables context navigation.
	
	Once created, use ContextManager.registerContext(name, description, context, parent = None)
	to register the context.
	
	
	Alternatively, you may directly get a registered context with:
	ContextManager.createContext(contextName, description, parent = ...)
	or ContextManager.createRootContext(contextName, description)
	"""
	def __init__(self):
		ChoiceNode.__init__(self)
		self.__commands = {}
		# Automatically injected by the context manager (upon registration)
		self._parentContext = None
		self._contextManager = None
		self._name = None
		
	##
	# "Private" methods
	##
	
	def __str__(self):
		return self._name	

	def _execute(self, tokens):
		"""
		Parse and execute the command provided by the tokenized line.
		"""
		if not tokens:
			return
		
		value, remainingTokens = self.parse(tokens)
		if remainingTokens:
			raise UnexpectedToken("unexpected token at: %s" % (remainingTokens[0]))

		# Let's execute the command
		(commandName, args) = value
		if isinstance(args, dict):
			self.__commands[commandName](**args)
		elif args is None:
			self.__commands[commandName]()
		else:
			self.__commands[commandName](args)
	
	def _getSuggestions(self, tokens):
		if not tokens:
			return []
	
		# The last token is either empty or the beginning of a token.
		# We first retrieve all the suggestions for this last token,
		# then we try to match it against the non-empty last token, if any.
		suggestions, completionRequired, remainingTokens = self.suggestNextTokens(tokens[:-1])

		if remainingTokens:
			raise UnexpectedToken("unexpected token at: %s" % (remainingTokens[0]))

		if not tokens[-1]:
			# Command completion
			# We don't have the beginning of a token.
			# Simply suggest pure continuations	
			return completionRequired, suggestions
		
		else:
			# Word/token completion
			# Try to match the beginning of the token with a possible continuation
			tokenToComplete = tokens[-1]
			
			adjustedSuggestions = [ x for x in suggestions if x[0].startswith(tokenToComplete) ]
			
			if not adjustedSuggestions:
				raise InvalidSyntax("unrecognized command: %s" % tokenToComplete)
			return True, adjustedSuggestions

	def _getFormattedSuggestions(self, tokens):
		"""
		Format the suggestions "a la cisco":
		token    description
		token    description
		...
		"""
		ret = ""
		suggestions = self._getSuggestions(tokens)
	
		if not suggestions:
			ret = "(no suggestion)"
		else:
			maxTokenLength = max([ len(x[0]) for x in suggestions])
			format = " %%%ss  %%s\n" % maxTokenLength
			for token, description in suggestions:
				ret += format % (token, description)
		return ret

	##
	# "Public" methods that may be used in subclasses
	##	

	def getContextName(self):
		if self._parentContext:
			return self._parentContext.getContextName() + '/' + self._name
		else:
			return self._name

	def addContext(self, name, description, context):
		"""
		Add a sub-context.
		Convenience function, calls the context registration
		on the context manager.
		"""
		if not self._contextManager:
			raise Exception("Please register this context into a context manager before adding sub-contexts to it")
		self._contextManager.registerContext(name, description, context, self)

	def error(self, txt):
		self._contextManager.write("%% error: %s\n" % txt)

	def out(self, txt):
		self._contextManager.write(txt)

	def notify(self, txt):
		self._contextManager.write(txt + "\n")
	
	def printTable(self, headers, rows):
		self.notify(formatTable(headers, rows))

	def printForm(self, headers, rows):
		self.notify(formatForm(headers, rows))
	
	def addCommand(self, commandName, description, syntaxNode, callback):
		"""
		Register a new command into the context.
		The callback is a function that will take arguments according
		to the node field names.
		
		Node is the syntaxNode representing the command arguments.
		"""
		self.addChoice(commandName, description, syntaxNode)
		self.__commands[commandName] = callback
		return self


##
# Context Manager
##

class ContextManager:
	"""
	This context manager manages the CommandContext tree
	and forwards the completion/execution requests to the current
	active context.
	
	Usage:
	
	cm = ContextManager()
	root = cm.createRootContext()
	
	Raise ShellExit exception when exit is called from the root context.
	"""
	def __init__(self):
		self._currentContext = None
		self._registeredContexts = {} # contexts, by complete name/path. Used for direct access.
		self._debug = False
	
	def setDebug(self, debug):
		self._debug = debug
	
	def isDebug(self):
		return self._debug

	# Factory-oriented method	
	def createRootContext(self, contextName, description = None):
		context = self.createContext(contextName, description, None)
		self.setCurrentContext(context)
		return context
	
	# Factory-oriented method	
	def createContext(self, contextName, description, parentContext):
		context = CommandContext()
		return self.registerContext(contextName, description, context, parentContext)
	
	# Registration-oriented method	
	def registerContext(self, contextName, description, context, parentContext):
		# Some injections
		context._parentContext = parentContext
		context._contextManager = self
		context._name = contextName
		
		if parentContext:
			# Register a way to navigate to the context
			parentContext.addCommand(contextName, "go to " + description + " context", NullNode(), lambda: self.setCurrentContext(context))
			# Register a way to exit the context
			context.addCommand("exit", "exit to parent context", NullNode(), self.goUp)
		else:
			context.addCommand("exit", "exit " + description, NullNode(), self.goUp)

		# Registration for direct access				
		self._registeredContexts[context.getContextName()] = context
		return context
		
	def getCurrentContextName(self):
		return self._currentContext.getContextName()
	
	def setCurrentContext(self, context):
		self._currentContext = context

	def goTo(self, contextPath):
		"""
		Directly go to the context identified by the contextPath (path/to/context)
		"""
		context = self._registeredContexts.get(contextPath)
		if not context:
			raise Exception("Unknown context: %s" % contextPath)
		else:
			self.setCurrentContext(context)
	
	def goUp(self):
		if self._currentContext._parentContext:
			self.setCurrentContext(self._currentContext._parentContext)
		else:
			raise ShellExit()
	
	def execute(self, tokens):
		"""
		Forward the execution signal to the current context
		"""
		self._currentContext._execute(tokens)
	
	def getFormattedSuggestions(self, tokens):
		"""
		Forward the signal to the current context
		"""
		self._currentContext._getFormattedSuggestions(tokens)

	def getSuggestions(self, tokens):
		"""
		Forward the signal to the current context
		"""
		return self._currentContext._getSuggestions(tokens)

	def write(self, txt):
		"""
		To be reimplemented in inherited adapters
		"""
		sys.stdout.write(txt)


################################################################################
# Adapter Classes
################################################################################

# These adapters enable to bind the context manager
# with an input/output manager.
#
# Could be a telnet layer, or raw input, readline, cmd.Cmd...

import cmd
import readline

class CmdContextManagerAdapter(ContextManager):
	"""
	This is an adapter class to glue the Context Manager
	logic to a cmd.Cmd access interface.
	"""
	class MyCmd(cmd.Cmd):
		def __init__(self, contextManager):
			cmd.Cmd.__init__(self)
			self._contextManager = contextManager
			readline.set_completer_delims(" ")
			
		def emptyline(self):
			"""
			Do not repeat the last command on empty line
			"""
			pass

		def completedefault(self, text, line, begidx, endidx):
			"""
			Overrides the cmd.Cmd implementation.
			Completes the words after the first one.
			"""
			return self.completenames(line)

		def completenames(self, text, *ignored):
			"""
			Overrides the cmd.Cmd implementation.
			
			Normally, we should only return a list of tokens to complete the current text.
			Actually, we also display the possible completion options, if any, directly here,
			as we display them "a la cisco", with an associated description (which is not
			the case of the standard way of readline displaying completion suggestions).
			
			In this case, we just "simulate" that there are no possible completions so
			that readline do not display them its own way.
			
			This avoids hooking the rl_completion_display_matches_hook via set_completion_display_matches (Python 2.6+)
			or ctypes/cdll manipulation in 2.5.
			"""
			ret = self._getSuggestions(text)
			if isinstance(ret, basestring):
				# a single suggestion was returned. Complete with it.
				return [ ret ]
			elif isinstance(ret, list):
				# multiple possibilities. Display them.
				self.showCompletionSuggestions(ret)
				# And do not complete anything
				return []
			else:
				# Error during completion. Do not complete anything.
				return []
		

		def _getSuggestions(self, text, *ignored):
			"""
			Returns a list of possible tokens or continuations, (list)
			or a single token (completion), (string)
			or None (error). (None)
			
			I'm not a big fan of dynamic return types, but it makes things easier here.
			"""
			tokens = self.tokenize(text)
			
			try:
				completionRequired, ret = self._contextManager.getSuggestions(tokens)
			except ParsingException, e:
				self.stdout.write("\n%% error: %s\n" % str(e))
				self.redisplay()
				return None

			# If we have a required completion, let's check if we have a single one.
			if completionRequired:
				if len(ret) == 1:
					# Single suggestion. A real one or a help suggestion ?
					token, description = ret[0]
					if token is not None:
						# If we have only one suggestion, autocomplete with it.
						return token
					else:
						# We have a None suggestion, i.e. we can't complete for the user (int/string value, ...)
						# Display it as a suggestion.
						return [ ("<value>", description) ]
				else:
					# We have multiple suggestions, display them.
					return ret
			
			else:
				# We may have multiple, optional completions, and the <CR> option, too
				# Display them
				return ret + [( '<CR>', '')]

		def tokenize(self, line):
			"""
			Tokenize a command line (simple version)
			"""
			return line.split(' ')
		
		def onecmd(self, line):
			# Support for ^Z
			line = line.strip()
			if not line:
				return
				
			if line == "EOF":
				self.stdout.write("\n")
				self._contextManager.goUp()
				return
			
			try:
				self._contextManager.execute(self.tokenize(line))
			except ShellExit:
				raise
			except Exception, e:
				if self._contextManager.isDebug():
					self.stdout.write(getBacktrace() + "\n")
				self.stdout.write("%% error: %s\n" % str(e))
		
		def showCompletionSuggestions(self, suggestions):
			"""
			Displays the completion suggestions "a la Cisco".
			"""
			suggestions.sort()
			maxTokenLength = max([ len(x[0]) for x in suggestions])
			fmt = " %%-%ss      %%s\n" % maxTokenLength
			self.stdout.write("\n")
			for token, description in suggestions:
				self.stdout.write(fmt % (token, description))
			self.redisplay()			

		def redisplay(self):
			# a readline.redisplay() is not enough: for readline, nothing
			# has changed and it won't redisplay the prompt> line
			# Instead, we should call rl_forced_update_display,
			# but this is not exported through the Python wrapper.
			# readline.redisplay()
			self.stdout.write(self.prompt + readline.get_line_buffer())
		
		
	def __init__(self, intro):
		ContextManager.__init__(self)
		self._cmd = self.MyCmd(self)
		self._cmd.intro = intro
	
	def run(self):
		self._cmd.cmdloop()
	
	def setCurrentContext(self, context):
		"""
		Overriden so that the cmd.prompt is updated
		when changing contexts
		"""
		self._currentContext = context
		self._cmd.prompt = self.getCurrentContextName() + "> "

	def write(self, txt):
		self._cmd.stdout.write(txt)

