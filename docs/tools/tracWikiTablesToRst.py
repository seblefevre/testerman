##
# Convert a TracWiki formatted table into a reStructuredText table.
##

"""
Input:

|| Header || Line ||
|| Values 1 || Value 2 ||

Output:

+----------+---------+
| Header   | Line    |
+==========+=========+
| Values 1 | Value 2 |
+----------+---------+
"""

def parseTWTable(table):
	"""
	Generate a table model from a TracWiki table.
	"""
	res = []
	colCount = None
	for line in table.splitlines():
		if not line.strip():
			continue
		values = [x.strip() for x in line.split('||')][1:-1]
		if colCount is None:
			colCount = len(values)
		elif colCount != len(values):
			raise Exception("Invalid number of columns on row:\n%s" % line)
		res.append(values)
	return res

def toRstTable(table, header = True):
	"""
	Convert a table model to a reST table.
	table is a list of entries, and the first entry is a header if header == True.
	Empty columns are removed.
	"""
	# Get the max length for each column
	lengths = len(table[0]) * [ 0 ]
	for row in table:
		i = 0
		for col in row:
			if len(col) > lengths[i]:
				lengths[i] = len(col)
			i += 1
	
	# Now we can format everything. We add a space before and after the value in a cell.
	if not table:
		return

	res = []
	
	def printRowSeparator(sep = "-"):
		return "+" + "+".join([ (l+2)*sep for l in lengths ]) + "+"

	def printRow(row):
		r = ""
		i = 0
		for l in row:
			r += "+ " + l.ljust(lengths[i]) + " "
			i += 1
		return r + "+"

	res.append(printRowSeparator('-'))
	res.append(printRow(table[0]))
	res.append(printRowSeparator(header and '=' or '-'))
	for row in table[1:]:
		res.append(printRow(row))
		res.append(printRowSeparator('-'))
	
	return "\n".join(res)
	

def toRstCsvTable(table, header = True):
	"""
	Convert a table model to a reST table using the csv-table directive.
	table is a list of entries, and the first entry is a header if header == True.
	"""
	# Now we can format everything. We add a space before and after the value in a cell.
	if not table:
		return

	res = []
	
	def toCsv(row):
	 return ','.join([ ('"%s"' % x.replace('"', '""').replace("\\", "\\\\")) for x in row])
	
	res.append('.. csv-table::')
	if header:
		res.append('   :header: ' + toCsv(table[0]))
		res.append('')
		table = table[1:]
	for row in table:
		res.append('   ' + toCsv(row))
	
	return "\n".join(res)
	

test = """
|| Name || Type || Default value || Description. ||
|| ``host`` || string || ``'localhost'`` || to host to connect onto to execute the commands. ||
|| ``username`` || string || (none) || the username to use to log onto ``host``to execute the commands. ||
|| ``password`` || string || (none) || the ``username``'s password on ``host``. ||
|| ``timeout`` || float || ``5.0`` || the maximum amount of time, in s, allowed to __start__ executing the command on ``host``. Includes the SSH login sequence. ||
|| ``convert_eol``|| boolean || ``True`` || if set to True, convert ``\\r\\n`` in output to ``\\n``. This way, the templates are compatible with ProbeExec. ||
|| ``working_dir``|| string || (none) || the diretory to go to before executing the command line. By default, the working dir is the login directory (usually the home dir). ||
|| ``strict_host``|| boolean || ``True`` || if set to False, the probe removes the target host from $HOME/.ssh/known_hosts to avoid failing when connecting to an updated host. Otherwise, the connection fails if the SSH key changed. ||
|| ``max_line_length``|| integer || ``150`` || the max number of characters before splitting a line over multiple lines with a \\-based continuation. Currently the splitting algorithm is pretty dumb and may split your command line in the middle of a quoted argument, possibly changing its actual value. Increasing this size may be a workaround in such cases.||
"""		


table = parseTWTable(test)
print toRstTable(table)
print
print toRstCsvTable(table)

			
