##
# A GSM 03.38 (GSM default alphabet) codec.
#
# Note: this maps unicode to GSM default alphabet, i.e.
# manages the GSM 03.38 coding.
# The encoding is independent from this alphabet (8 bits, 7 bits, etc).
#
# However, this codec can only decode 8 bit representations of the
# GSM string.
#
# Adapted from Martin v. Loewis's post:
# (http://mail.python.org/pipermail/python-list/2002-October/167271.html)
##



mapping = [
	('\x00', u'\u0040'),	#	COMMERCIAL AT
	('\x00', u'\u0000'),	#	NULL (see note above)
	('\x01', u'\u00A3'),	#	POUND SIGN
	('\x02', u'\u0024'),	#	DOLLAR SIGN
	('\x03', u'\u00A5'),	#	YEN SIGN
	('\x04', u'\u00E8'),	#	LATIN SMALL LETTER E WITH GRAVE
	('\x05', u'\u00E9'),	#	LATIN SMALL LETTER E WITH ACUTE
	('\x06', u'\u00F9'),	#	LATIN SMALL LETTER U WITH GRAVE
	('\x07', u'\u00EC'),	#	LATIN SMALL LETTER I WITH GRAVE
	('\x08', u'\u00F2'),	#	LATIN SMALL LETTER O WITH GRAVE
	('\x09', u'\u00E7'),	#	LATIN SMALL LETTER C WITH CEDILLA
	('\x09', u'\u00C7'),	#	LATIN CAPITAL LETTER C WITH CEDILLA (see note above)
	('\x0A', u'\u000A'),	#	LINE FEED
	('\x0B', u'\u00D8'),	#	LATIN CAPITAL LETTER O WITH STROKE
	('\x0C', u'\u00F8'),	#	LATIN SMALL LETTER O WITH STROKE
	('\x0D', u'\u000D'),	#	CARRIAGE RETURN
	('\x0E', u'\u00C5'),	#	LATIN CAPITAL LETTER A WITH RING ABOVE
	('\x0F', u'\u00E5'),	#	LATIN SMALL LETTER A WITH RING ABOVE
	('\x10', u'\u0394'),	#	GREEK CAPITAL LETTER DELTA
	('\x11', u'\u005F'),	#	LOW LINE
	('\x12', u'\u03A6'),	#	GREEK CAPITAL LETTER PHI
	('\x13', u'\u0393'),	#	GREEK CAPITAL LETTER GAMMA
	('\x14', u'\u039B'),	#	GREEK CAPITAL LETTER LAMDA
	('\x15', u'\u03A9'),	#	GREEK CAPITAL LETTER OMEGA
	('\x16', u'\u03A0'),	#	GREEK CAPITAL LETTER PI
	('\x17', u'\u03A8'),	#	GREEK CAPITAL LETTER PSI
	('\x18', u'\u03A3'),	#	GREEK CAPITAL LETTER SIGMA
	('\x19', u'\u0398'),	#	GREEK CAPITAL LETTER THETA
	('\x1A', u'\u039E'),	#	GREEK CAPITAL LETTER XI
	('\x1C', u'\u00C6'),	#	LATIN CAPITAL LETTER AE
	('\x1D', u'\u00E6'),	#	LATIN SMALL LETTER AE
	('\x1E', u'\u00DF'),	#	LATIN SMALL LETTER SHARP S (German)
	('\x1F', u'\u00C9'),	#	LATIN CAPITAL LETTER E WITH ACUTE
	('\x20', u'\u0020'),	#	SPACE
	('\x21', u'\u0021'),	#	EXCLAMATION MARK
	('\x22', u'\u0022'),	#	QUOTATION MARK
	('\x23', u'\u0023'),	#	NUMBER SIGN
	('\x24', u'\u00A4'),	#	CURRENCY SIGN
	('\x25', u'\u0025'),	#	PERCENT SIGN
	('\x26', u'\u0026'),	#	AMPERSAND
	('\x27', u'\u0027'),	#	APOSTROPHE
	('\x28', u'\u0028'),	#	LEFT PARENTHESIS
	('\x29', u'\u0029'),	#	RIGHT PARENTHESIS
	('\x2A', u'\u002A'),	#	ASTERISK
	('\x2B', u'\u002B'),	#	PLUS SIGN
	('\x2C', u'\u002C'),	#	COMMA
	('\x2D', u'\u002D'),	#	HYPHEN-MINUS
	('\x2E', u'\u002E'),	#	FULL STOP
	('\x2F', u'\u002F'),	#	SOLIDUS
	('\x30', u'\u0030'),	#	DIGIT ZERO
	('\x31', u'\u0031'),	#	DIGIT ONE
	('\x32', u'\u0032'),	#	DIGIT TWO
	('\x33', u'\u0033'),	#	DIGIT THREE
	('\x34', u'\u0034'),	#	DIGIT FOUR
	('\x35', u'\u0035'),	#	DIGIT FIVE
	('\x36', u'\u0036'),	#	DIGIT SIX
	('\x37', u'\u0037'),	#	DIGIT SEVEN
	('\x38', u'\u0038'),	#	DIGIT EIGHT
	('\x39', u'\u0039'),	#	DIGIT NINE
	('\x3A', u'\u003A'),	#	COLON
	('\x3B', u'\u003B'),	#	SEMICOLON
	('\x3C', u'\u003C'),	#	LESS-THAN SIGN
	('\x3D', u'\u003D'),	#	EQUALS SIGN
	('\x3E', u'\u003E'),	#	GREATER-THAN SIGN
	('\x3F', u'\u003F'),	#	QUESTION MARK
	('\x40', u'\u00A1'),	#	INVERTED EXCLAMATION MARK
	('\x41', u'\u0041'),	#	LATIN CAPITAL LETTER A
	('\x41', u'\u0391'),	#	GREEK CAPITAL LETTER ALPHA
	('\x42', u'\u0042'),	#	LATIN CAPITAL LETTER B
	('\x42', u'\u0392'),	#	GREEK CAPITAL LETTER BETA
	('\x43', u'\u0043'),	#	LATIN CAPITAL LETTER C
	('\x44', u'\u0044'),	#	LATIN CAPITAL LETTER D
	('\x45', u'\u0045'),	#	LATIN CAPITAL LETTER E
	('\x45', u'\u0395'),	#	GREEK CAPITAL LETTER EPSILON
	('\x46', u'\u0046'),	#	LATIN CAPITAL LETTER F
	('\x47', u'\u0047'),	#	LATIN CAPITAL LETTER G
	('\x48', u'\u0048'),	#	LATIN CAPITAL LETTER H
	('\x48', u'\u0397'),	#	GREEK CAPITAL LETTER ETA
	('\x49', u'\u0049'),	#	LATIN CAPITAL LETTER I
	('\x49', u'\u0399'),	#	GREEK CAPITAL LETTER IOTA
	('\x4A', u'\u004A'),	#	LATIN CAPITAL LETTER J
	('\x4B', u'\u004B'),	#	LATIN CAPITAL LETTER K
	('\x4B', u'\u039A'),	#	GREEK CAPITAL LETTER KAPPA
	('\x4C', u'\u004C'),	#	LATIN CAPITAL LETTER L
	('\x4D', u'\u004D'),	#	LATIN CAPITAL LETTER M
	('\x4D', u'\u039C'),	#	GREEK CAPITAL LETTER MU
	('\x4E', u'\u004E'),	#	LATIN CAPITAL LETTER N
	('\x4E', u'\u039D'),	#	GREEK CAPITAL LETTER NU
	('\x4F', u'\u004F'),	#	LATIN CAPITAL LETTER O
	('\x4F', u'\u039F'),	#	GREEK CAPITAL LETTER OMICRON
	('\x50', u'\u0050'),	#	LATIN CAPITAL LETTER P
	('\x50', u'\u03A1'),	#	GREEK CAPITAL LETTER RHO
	('\x51', u'\u0051'),	#	LATIN CAPITAL LETTER Q
	('\x52', u'\u0052'),	#	LATIN CAPITAL LETTER R
	('\x53', u'\u0053'),	#	LATIN CAPITAL LETTER S
	('\x54', u'\u0054'),	#	LATIN CAPITAL LETTER T
	('\x54', u'\u03A4'),	#	GREEK CAPITAL LETTER TAU
	('\x55', u'\u0055'),	#	LATIN CAPITAL LETTER U
	('\x55', u'\u03A5'),	#	GREEK CAPITAL LETTER UPSILON
	('\x56', u'\u0056'),	#	LATIN CAPITAL LETTER V
	('\x57', u'\u0057'),	#	LATIN CAPITAL LETTER W
	('\x58', u'\u0058'),	#	LATIN CAPITAL LETTER X
	('\x58', u'\u03A7'),	#	GREEK CAPITAL LETTER CHI
	('\x59', u'\u0059'),	#	LATIN CAPITAL LETTER Y
	('\x5A', u'\u005A'),	#	LATIN CAPITAL LETTER Z
	('\x5A', u'\u0396'),	#	GREEK CAPITAL LETTER ZETA
	('\x5B', u'\u00C4'),	#	LATIN CAPITAL LETTER A WITH DIAERESIS
	('\x5C', u'\u00D6'),	#	LATIN CAPITAL LETTER O WITH DIAERESIS
	('\x5D', u'\u00D1'),	#	LATIN CAPITAL LETTER N WITH TILDE
	('\x5E', u'\u00DC'),	#	LATIN CAPITAL LETTER U WITH DIAERESIS
	('\x5F', u'\u00A7'),	#	SECTION SIGN
	('\x60', u'\u00BF'),	#	INVERTED QUESTION MARK
	('\x61', u'\u0061'),	#	LATIN SMALL LETTER A
	('\x62', u'\u0062'),	#	LATIN SMALL LETTER B
	('\x63', u'\u0063'),	#	LATIN SMALL LETTER C
	('\x64', u'\u0064'),	#	LATIN SMALL LETTER D
	('\x65', u'\u0065'),	#	LATIN SMALL LETTER E
	('\x66', u'\u0066'),	#	LATIN SMALL LETTER F
	('\x67', u'\u0067'),	#	LATIN SMALL LETTER G
	('\x68', u'\u0068'),	#	LATIN SMALL LETTER H
	('\x69', u'\u0069'),	#	LATIN SMALL LETTER I
	('\x6A', u'\u006A'),	#	LATIN SMALL LETTER J
	('\x6B', u'\u006B'),	#	LATIN SMALL LETTER K
	('\x6C', u'\u006C'),	#	LATIN SMALL LETTER L
	('\x6D', u'\u006D'),	#	LATIN SMALL LETTER M
	('\x6E', u'\u006E'),	#	LATIN SMALL LETTER N
	('\x6F', u'\u006F'),	#	LATIN SMALL LETTER O
	('\x70', u'\u0070'),	#	LATIN SMALL LETTER P
	('\x71', u'\u0071'),	#	LATIN SMALL LETTER Q
	('\x72', u'\u0072'),	#	LATIN SMALL LETTER R
	('\x73', u'\u0073'),	#	LATIN SMALL LETTER S
	('\x74', u'\u0074'),	#	LATIN SMALL LETTER T
	('\x75', u'\u0075'),	#	LATIN SMALL LETTER U
	('\x76', u'\u0076'),	#	LATIN SMALL LETTER V
	('\x77', u'\u0077'),	#	LATIN SMALL LETTER W
	('\x78', u'\u0078'),	#	LATIN SMALL LETTER X
	('\x79', u'\u0079'),	#	LATIN SMALL LETTER Y
	('\x7A', u'\u007A'),	#	LATIN SMALL LETTER Z
	('\x7B', u'\u00E4'),	#	LATIN SMALL LETTER A WITH DIAERESIS
	('\x7C', u'\u00F6'),	#	LATIN SMALL LETTER O WITH DIAERESIS
	('\x7D', u'\u00F1'),	#	LATIN SMALL LETTER N WITH TILDE
	('\x7E', u'\u00FC'),	#	LATIN SMALL LETTER U WITH DIAERESIS
	('\x7F', u'\u00E0'),	#	LATIN SMALL LETTER A WITH GRAVE

#	('\x1B', u'\u00A0'),	#	ESCAPE TO EXTENSION TABLE (or displayed as NBSP)
]

# Escaped characters
escaped_mapping = [
	('\x0A', u'\u000C'),	#	FORM FEED
	('\x14', u'\u005E'),	#	CIRCUMFLEX ACCENT
	('\x28', u'\u007B'),	#	LEFT CURLY BRACKET
	('\x29', u'\u007D'),	#	RIGHT CURLY BRACKET
	('\x2F', u'\u005C'),	#	REVERSE SOLIDUS
	('\x3C', u'\u005B'),	#	LEFT SQUARE BRACKET
	('\x3D', u'\u007E'),	#	TILDE
	('\x3E', u'\u005D'),	#	RIGHT SQUARE BRACKET
	('\x40', u'\u007C'),	#	VERTICAL LINE
	('\x65', u'\u20AC'),	#	EURO SIGN
]

# unicode -> GSM 03.38
regular_encode_dict = {}
for (g, u) in mapping:
	regular_encode_dict[u] = g

# unicode -> escaped GSM 03.38 characters ("\x1b" is the GSM 03.38 escape char)
escape_encode_dict = {}
for g, u in escaped_mapping:
	escape_encode_dict[u] = g

# GSM 03.38 -> unicode
# Only first corresponding unicode character is
# taken into account (see 0x41, etc)
regular_decode_dict = {}
for (g, u) in mapping:
	if not regular_decode_dict.has_key(g):
		regular_decode_dict[g] = u

escape_decode_dict = {}
for g, u in escaped_mapping:
	escape_decode_dict[g] = u


###############################################################################
# Main functions
###############################################################################

def encode(input_, errors = 'strict'):
	"""
	@type input_: unicode string
	
	@rtype: buffer/string
	"""
	result = []
	for c in input_:
		try:
			result.append(regular_encode_dict[c])
		except KeyError:
			if escape_encode_dict.has_key(c):
				# OK, let's encode it as an escaped characters
				result.append('\x1b')
				result.append(escape_encode_dict[c])
			else:
				if errors == 'strict': raise UnicodeError("Invalid SMS character")
				elif errors == 'replace': result.append(chr(0x3f)) #question mark
				elif errors == 'ignore': pass
				else: raise UnicodeError("Unknown error handling")
	return ''.join(result)
		
def decode(input_, errors = 'strict'):
	"""
	@type input_: buffer/string
	
	@rtype: unicode string
	"""
	result = []
	index = 0
	while index < len(input_):
		c = input_[index]
		index += 1
		if c == '\x1b':
			if index < len(input_):
				c = input_[index]
				index += 1
				if escape_decode_dict.has_key(c):
					result.append(escape_decode_dict[c])
				else:
					# Not followed by an escapable character -> encoded as \u00A0
					result.append('\xa0')
			else:
				# Last character in the string -> \u00A0
				result.append('\xa0')
		else:
			try:
				result.append(regular_decode_dict[c])
			except KeyError:
				# error handling: unassigned byte, must be > 0x7f
				if errors == 'strict': raise UnicodeError("Unrecognized SMS character")
				elif errors == 'replace': result.append('?')
				elif errors == 'ignore': pass
				else: raise UnicodeError("Unknown error handling")
	return u"".join(result)
