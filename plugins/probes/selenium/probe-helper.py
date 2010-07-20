# Helper to build the Selenium Testerman Probe.
#
# Turns some parts of the selenium.py source code into something usable to build
# a Testerman probe.


import re

# Contains command prototypes as a list of keyword args per command name.
# Will be used to generate TTCN-3 equivalent doc for the probe
# as well as generating probe command validator.
commands = {}

def command_to_prototype(cmd):
	global commands
	m = re.match(r'\s*(return |)\s*self\.do_command\("(?P<cmd>[a-zA-Z]+)\s*", \[(?P<args>.*)\]\)', cmd)
	if m:
		args = m.group('args')
		commands[m.group('cmd')] = {'method': 'do_command', 'treturnType': None, 'args': [x for x in args.split(',') if x]}
		return m.group('cmd')

	m = re.match(r'\s*(return |)\s*self\.get_boolean\("(?P<cmd>[a-zA-Z]+)\s*", \[(?P<args>.*)\]\)', cmd)
	if m:
		args = m.group('args')
		commands[m.group('cmd')] = {'method': 'get_boolean', 'treturnType': 'boolean', 'args': [x for x in args.split(',') if x]}
		return m.group('cmd')

	m = re.match(r'\s*(return |)\s*self\.get_string\("(?P<cmd>[a-zA-Z]+)\s*", \[(?P<args>.*)\]\)', cmd)
	if m:
		args = m.group('args')
		commands[m.group('cmd')] = {'method': 'get_string', 'treturnType': 'charstring', 'args': [x for x in args.split(',') if x]}
		return m.group('cmd')

	m = re.match(r'\s*(return |)\s*self\.get_string_array\("(?P<cmd>[a-zA-Z]+)\s*", \[(?P<args>.*)\]\)', cmd)
	if m:
		args = m.group('args')
		commands[m.group('cmd')] = {'method': 'get_string_array', 'treturnType': 'record of charstring', 'args': [x for x in args.split(',') if x]}
		return m.group('cmd')
		
	m = re.match(r'\s*(return |)\s*self\.get_number\("(?P<cmd>[a-zA-Z]+)\s*", \[(?P<args>.*)\]\)', cmd)
	if m:
		args = m.group('args')
		commands[m.group('cmd')] = {'method': 'get_number', 'treturnType': 'integer', 'args': [x for x in args.split(',') if x]}
		return m.group('cmd')
	
	m = re.match(r'\s*(return |)\s*self\.get_number_array\("(?P<cmd>[a-zA-Z]+)\s*", \[(?P<args>.*)\]\)', cmd)
	if m:
		args = m.group('args')
		commands[m.group('cmd')] = {'method': 'get_number_array', 'treturnType': 'record of integer', 'args': [x for x in args.split(',') if x]}
		return m.group('cmd')
	
	m = re.match(r'\s*(return |)\s*self\.get_boolean_array\("(?P<cmd>[a-zA-Z]+)\s*", \[(?P<args>.*)\]\)', cmd)
	if m:
		args = m.group('args')
		commands[m.group('cmd')] = {'method': 'get_boolean_array', 'treturnType': 'record of boolean', 'args': [x for x in args.split(',') if x]}
		return m.group('cmd')

	return None


def to_ttcn3(commands):
	"""
	Turns commands prototypes into a TTCN-3 equivalent documentation.
	"""
	items = commands.items()
	items.sort()
	
	ret = []
	
	ret.append('type union SeleniumStrictCommand')
	ret.append('{')
	
	for cmd, val in items:
		if val['args']:
			ret.append("\trecord { %s } %s, %s" % (", ".join(['charstring %s' %x for x in val['args']]), cmd, val['treturnType'] and "// then expect a response as %s" % val['treturnType'] or ""))
		else:
			ret.append("\trecord {} %s, %s" % (cmd, val['treturnType'] and "// then expect a response as %s" % val['treturnType'] or ""))
		
	ret.append('}')
	
	return '\n'.join(ret)


def main():
	f = open('selenium.py', 'r')
	lines = f.readlines()
	f.close()
	for line in lines:
		ret = command_to_prototype(line)
		if ret:
			print "Added new command choice: " + ret

	# Display a dict that will be used to define selenium commands prototype in the probe	
	print repr(commands)
	
	print
	# Display what will be used to document the probe
	print to_ttcn3(commands)
	

if __name__ == '__main__':
	main()

		
		
	
	
