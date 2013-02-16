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
|| Name || Type || Default value || Description ||
|| ``local_ip`` || string || (empty - system assigned) || Local IP address to use when sending packets ||
|| ``local_port`` || integer || ``0`` (system assigned) || Local port to use when sending packets ||
|| ``listening_ip`` || string || ``0.0.0.0`` || Listening IP address, if listening mode is activated (see below) ||
|| ``listening_port`` || integer || ``0`` || Set it to a non-zero port to start listening on mapping ||
|| ``style`` || string in ``'tcp'``, ``'udp'`` || ``'tcp'`` || SCTP style: UDP or TCP (stream) ||
|| ``enable_notifications`` || boolean || ``False`` || If set, you may get connection/disconnection notification and connectionConfirm/Error notification messages ||
|| ``default_sut_address`` || string (ip:port) || ``None`` || If set, used as a default SUT address if none provided by the user ||
"""		


table = parseTWTable(test)
print toRstTable(table)
print
print toRstCsvTable(table)

			
