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
# Low-level input handling, however, is based on readline.
#
#
# Usage:
# - create a CommandContext and register one or multiple commands
# in it. These commands have a syntax tree based on a SequenceNode.
# - ... ?
# 
#
##

import sys

##
# Some usual exceptions
##

class InvalidSyntax(Exception):
	pass

class UnexpectedToken(Exception):
	pass

class MissingToken(Exception):
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
	"""
	def __init__(self, typeName, description):
		self._typeName = typeName
		self._description = description
	
	def getDescription(self):
		return self._description

	def __str__(self):
		return "%s (%s)" % (self._typeName, self._description)	
	
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
	def __init__(self, description = None):
		SyntaxNode.__init__(self, '<string>', description)

	def parse(self, tokens):
		if not tokens:
			raise MissingToken("%s: missing value" % self) 

		return (tokens[0], tokens[1:])
	
	def suggestNextTokens(self, tokens):
		if not tokens:
			return [ (self._typeName, self.getDescription()) ], True, tokens
		else:
			return [], False, tokens[1:]
		

class IntegerNode(SyntaxNode):
	"""
	Simple integer node.
	"""
	def __init__(self, description = None):
		SyntaxNode.__init__(self, '<integer>', description)

	def parse(self, tokens):
		if not tokens:
			raise MissingToken("%s: missing value" % self) 
		try:
			int(tokens[0])
		except:
			raise InvalidSyntax("%s: integer expected" % self)
		return (int(tokens[0]), tokens[1:])

	def suggestNextTokens(self, tokens):
		if not tokens:
			return [ (self._typeName, self.getDescription()) ], True, tokens
		else:
			try:
				int(tokens[0])
			except:
				raise InvalidSyntax("%s: integer expected" % self)
			return [], False, tokens[1:]


class NullNode(SyntaxNode):
	"""
	'constant'-like. Useful in choices.
	"""
	def __init__(self, description = None):
		SyntaxNode.__init__(self, '<null>', description)

	def parse(self, tokens):
		return (None, tokens)

	def suggestNextTokens(self, tokens):
		return [], False, tokens


class SequenceNode(SyntaxNode):
	"""
	Contains named values.
	
	When valuated, returns a dict.
	
	MyType ::= SEQUENCE {
		field1 INTEGER optional,
		field2 String
	}
	
	would be declared as:
	MyType = SequenceNode()
	MyType.addField("field1", IntegerNode(), True)
	MyType.addField("field2", StringNode())
	"""
	def __init__(self, description = None):
		SyntaxNode.__init__(self, "<sequence>", description)
		self._fields = {}
	
	def addField(self, fieldName, syntaxNode, optional = False):
		"""
		Declares a new field in the sequence.
		""" 
		self._fields[fieldName] = (syntaxNode, optional)

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
				raise UnexpectedToken("%s: duplicated field %s" % (self, fieldName))
			parsedFields.append(fieldName)

			v, nextTokens = self._fields[fieldName][0].parse(nextTokens[1:])
			ret[fieldName] = v
			
		# Check if we have all mandatory fields
		for fieldName, (node, optional)  in self._fields.items():
			if not optional and not fieldName in parsedFields:
				raise MissingToken("%s: missing mandatory field %s" % (self, fieldName))

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
				raise UnexpectedToken("%s: duplicated field %s" % (self, fieldName))
			parsedFields.append(fieldName)
			
			# Check if the current field wants to complete something or not
			suggestions, completionRequired, nextTokens = self._fields[fieldName][0].suggestNextTokens(nextTokens[1:])

			if completionRequired:
				if nextTokens:
					# well, this field could have consumed other tokens,
					# but it did not: missing a token somewhere
					raise MissingToken("%s: field %s misses a value" % (self, fieldName))
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
				for fieldName, (node, optional) in self._fields.items():
					if not fieldName in parsedFields:
						# we prefix the description with a * for mandatory fields
						suggestions.append((fieldName, (not optional and "*" or "") + node.getDescription()))
						if not optional:
							# At least one non-optional field: completion required.
							completionRequired = True
				return suggestions, completionRequired, nextTokens

		else:
			# The line has not been consumed completely - just check that
			# we have all our mandatory fields
			for fieldName, (node, optional)  in self._fields.items():
				if not optional and not fieldName in parsedFields:
					raise MissingToken("%s: missing mandatory field %s" % (self, fieldName))

			# OK, we have everything, and nothing can't be completed at
			# our level (i.e. in this node branch) anymore
			return [], False, nextTokens
	

class ChoiceNode(SyntaxNode):
	"""
	Equivalent of a ASN.1 CHOICE:
	
	MyType ::= CHOICE {
		choice1 INTEGER,
		choice2 String
	}
	
	translates into:
	MyType = ChoiceNode()
	MyType.addChoice("choice1", IntegerNode())
	MyType.addChoice("choice2", StringNode())
	"""
	def __init__(self, description = None):
		SyntaxNode.__init__(self, "<choice>", description)
		self._choices = {}
	
	def addChoice(self, choiceName, syntaxNode):
		self._choices[choiceName] = syntaxNode
		return self

	def addChoices(self, choices):
		for choiceName, syntaxNode in choices:
			self.addChoice(choiceName, syntaxNode)
		return self
	
	def parse(self, tokens):
		"""
		For a choice, returns a tuple (choiceName, value)
		"""
		if not tokens:
			raise MissingToken("%s: missing choice name" % self) 
		# Check that we have one of or choice names
		choiceName = tokens[0]
		if choiceName in self._choices:
			v, remaining = self._choices[choiceName].parse(tokens[1:])
			return ( (choiceName, v), remaining )
		else:
			raise InvalidSyntax("%s: invalid choice name (%s)" % (self, choiceName))

	def suggestNextTokens(self, tokens):
		if not tokens:
			# Suggest one choice
			suggestions = []
			for choiceName, node in self._choices.items():
				suggestions.append((choiceName, node.getDescription()))
			return suggestions, True, tokens

		else:
			# Delegate to the selected choice
			choiceName = tokens[0]
			if choiceName in self._choices:
				return self._choices[choiceName].suggestNextTokens(tokens[1:])
			else:
				raise InvalidSyntax("%s: invalid choice name (%s)" % (self, choiceName)) 



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
	Do not instanciate directly.
	Instead, call ContextManager.getNewContext(contextName, description, parent = None)
	"""
	def __init__(self, description):
		ChoiceNode.__init__(self, description)
		self.__commands = {}
		# Automatically injected by the context manager (upon registration)
		self._parentContext = None
		self._contextManager = None
		self._name = None
		
	def __str__(self):
		return "%s" % self._name

	##
	# "Private" methods
	##

	def _execute(self, tokens):
		"""
		Parse and execute the command provided by the tokenized line.
		"""
		if not tokens:
			return
		
		value, remainingTokens = self.parse(tokens)
		if remainingTokens:
			raise UnexpectedToken("%s: unexpected token at: %s" % (self, remainingTokens[0]))

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
			raise UnexpectedToken("%s: unexpected token at: %s" % (self, remainingTokens[0]))

		if not tokens[-1]:
			# Command completion
			# We don't have the beginning of a token.
			# Simply suggest pure continuations	
			return suggestions
		
		else:
			# Word/token completion
			# Try to match the beginning of the token with a possible continuation
			tokenToComplete = tokens[-1]
			
			adjustedSuggestions = [ x for x in suggestions if x[0].startswith(tokenToComplete) ]
			return adjustedSuggestions				

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
	
	def setContextName(self, name):
		self._name = name
	
	def error(self, txt):
		self._contextManager.write("%% error: %s\n" % txt)

	def out(self, txt):
		self._contextManager.write(txt)

	def notify(self, txt):
		self._contextManager.write(txt + "\n")
	
	def registerCommand(self, commandName, node, callback):
		"""
		Register a new command into the context.
		The callback is a function that will take arguments according
		to the node field names.
		
		Node is the syntaxNode representing the command arguments.
		"""
		self.addChoice(commandName, node)
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

	# Factory-oriented method	
	def createRootContext(self, contextName, description = None):
		context = self.createContext(contextName, description, None)
		self.setCurrentContext(context)
		return context
	
	# Factory-oriented method	
	def createContext(self, contextName, description, parentContext):
		context = CommandContext(description)
		return self.registerContext(contextName, context, parentContext)
	
	# Registration-oriented method	
	def registerContext(self, contextName, context, parentContext):
		# Some injections
		context._parentContext = parentContext
		context._contextManager = self
		context.setContextName(contextName)
		
		if parentContext:
			# Register a way to navigate to the context
			parentContext.registerCommand(contextName, NullNode("enter " + context.getDescription() + " context"), lambda: self.setCurrentContext(context))
			# Register a way to exit the context
			context.registerCommand("exit", NullNode("exit to parent context"), self.goUp)
		else:
			context.registerCommand("exit", NullNode("exit"), self.goUp)
		
		return context
		
	def getCurrentContextName(self):
		return self._currentContext.getContextName()
	
	def setCurrentContext(self, context):
		self._currentContext = context
	
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

class CmdContextManagerAdapter(ContextManager):
	"""
	This is an adapter class to glue the Context Manager
	logic to a cmd.Cmd access interface.
	"""
	class MyCmd(cmd.Cmd):
		def __init__(self, contextManager):
			cmd.Cmd.__init__(self)
			self._contextManager = contextManager
			
			# Warning: python 2.6+ only !
			try:
				readline.set_completion_display_matches_hook(self.displayCompletion)
				pass
			except:
				pass
			
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
			tokens = self.tokenize(line)
			ret = self._contextManager.getSuggestions(tokens)
			return [token for (token, desc) in ret]

		def completenames(self, text, *ignored):
			"""
			Overrides the cmd.Cmd implementation.
			Completes the first word (command).
			"""
			tokens = self.tokenize(text)
			ret = self._contextManager.getSuggestions(tokens)
			return [token for (token, desc) in ret]

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
				self._contextManager.goUp()
				return
			
			try:
				self._contextManager.execute(self.tokenize(line))
			except ShellExit:
				raise
			except Exception, e:
				self.stdout.write("%% error: %s\n" % str(e))
		
		def displayCompletion(self, substitute, matches, longest_match_length):
			"""
			This hook enables to retrieve the token descriptions
			provided through the CommandContext, and display then
			inline "a la Cisco".
			
			This is a hook to avoid re-implementing a readline-like lib with
			this enhanced suggestion display.
			"""
			suggestions = [ (x, "description") for x in matches ]
			
			maxTokenLength = max([ len(x[0]) for x in suggestions])
			fmt = " %%%ss  %%s\n" % maxTokenLength
			self.stdout.write("\n")
			for token, description in suggestions:
				self.stdout.write(fmt % (token, description))
			
			# a readline.redisplay() is not enough: for readline, nothing
			# has changed and it won't redisplay the prompt> line
			# Instead, we should call rl_forced_update_display,
			# but this is not exported through the Python wrapper.
#			readline.redisplay()
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

