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
	

test = """
|| *message* || *template* || *matched ?* || *comments* ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || ``|| no || ||
|| `[ 1, 2, 3, 4, 5, 6  <]`>`_` || `[ 1, 2, 3, 4, 5, 6, 7 ]` || no || ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ 6, 5, 4, 3, 2, 1 ]` || no || not in the correct order ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ 1, 2, 3, 4, 5, 6 ]` || yes || ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ 1, 2, any(), 4, 5, 6 ]` || yes || `any()` can replace any single element... ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ 1, 2, 3, any(), 4, 5, 6 ]` || no || ...but this element must be present ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ 1, 2, any_or_none(), 5, 6 ]` || yes || `any_or_none()` can replace any number of elements... ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ 1, 2, 3, any_or_none(), 4, 5, 6 ]` || yes || ...even zero ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ any_or_none(), 3, any(), 5, 6 ]` || yes || you may combine `any()` and `any_or_none()` ||
|| `[ 1, 2, 3, 4, 5, 6 ]` || `[ any_or_none(), 3, any_or_none() ]` || yes || equivalent to `superset(3)`, which may be more readable ||
"""		


print toRstTable(parseTWTable(test))
			
