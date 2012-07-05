
"""
Copyright (C) 2012 Steve Ward

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import string
import sys

#-------------------------------------------------------------------------------

__version__ = '2011-10-23'

#-------------------------------------------------------------------------------

"""
From the C++ standard:

2.14.3 Character literals

simple-escape-sequence: one of
	\' \" \? \\
	\a \b \f \n \r \t \v
"""
simple_escape_sequence = {
	'\a': r'\a', # alert
	'\b': r'\b', # backspace
	'\t': r'\t', # horizontal tab
	'\n': r'\n', # new line
	'\v': r'\v', # vertical tab
	'\f': r'\f', # form feed
	'\r': r'\r', # carriage return
	'\"': r'\"', # double quote
	'\'': r'\'', # single quote
	'\?': r'\?', # question mark
	'\\': r'\\', # backslash
}


def escape_char_to_octal(c):
	"""Escape the character to a simple-escape-sequence or an octal-escape-sequence."""

	if c in simple_escape_sequence:
		return simple_escape_sequence[c]
	else:
		return r'\{:03o}'.format(ord(c))


def escape_char_to_hexadecimal(c):
	"""Escape the character to a simple-escape-sequence or a hexadecimal-escape-sequence."""

	if c in simple_escape_sequence:
		return simple_escape_sequence[c]
	else:
		return r'\x{:02X}'.format(ord(c))


def escape_non_printable_char_to_octal(c):
	"""Escape the non-printable character to octal digits.  \
If the character is printable, it is not escaped."""

	if c.isprintable():
		return c
	else:
		return escape_char_to_octal(c)


def escape_non_printable_char_to_hexadecimal(c):
	"""Escape the non-printable character to hexadecimal digits.  \
If the character is printable, it is not escaped."""

	if c.isprintable():
		return c
	else:
		return escape_char_to_hexadecimal(c)

#-------------------------------------------------------------------------------

def literal(s):
	"""Do not quote the string."""

	return s


def shell_always(s):
	"""Quote the string (in all cases) for a shell.  \
Escape single quotes, and surround the result with single quotes."""

	return "'" + s.replace("'", r"'\''") + "'"


def shell(s):
	"""Quote the string (in some cases) for a shell.  \
If the string contains special characters specified by the POSIX.1-2008 standard, then quote the string for a shell.  \
<http://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_02>"""

	pattern = r'''[\t\n "#$%&'()*;<=>?[\\`|~]'''

	if re.search(pattern, s):
		return shell_always(s)
	else:
		return s


def escape(s):
	"""Escape non-printable characters, spaces, and backslashes."""

	# Escape spaces and backslashes.
	pattern = r'([ \\])'
	replacement = r'\\\1'

	s = re.sub(pattern, replacement, s)

	# Escape non-printable characters.
	pattern2 = '([^\x20-\x7E])'

	def replacement2(match_object):
		return escape_char_to_octal(match_object.group(1))

	s = re.sub(pattern2, replacement2, s)

	return s


def c(s):
	"""Quote the string for a C string literal.  \
Escape non-printable characters, double quotes, backslashes, and trigraphs, and surround the result with double quotes."""

	# Escape double quotes and backslashes.
	pattern = r'(["\\])'
	replacement = r'\\\1'

	s = re.sub(pattern, replacement, s)

	# Escape non-printable characters.
	pattern2 = '([^\x20-\x7E])'

	def replacement2(match_object):
		return escape_char_to_octal(match_object.group(1))

	s = re.sub(pattern2, replacement2, s)

	# Look for trigraphs.
	# Escape the second '\?' in what would otherwise be a trigraph.
	pattern3 = r"\?\?([!'()\-/<=>])"
	replacement3 = r'?\\?\1'

	s = re.sub(pattern3, replacement3, s)

	# Surround the result with double quotes.
	return '"' + s + '"'


def c_maybe(s):
	"""Quote the string (in some cases) for a C string literal.  \
Escape non-printable characters, double quotes, backslashes, and trigraphs, and surround the result with double quotes.  \
If no characters were escaped, the original string is returned."""

	# Look for double quotes and backslashes.
	pattern = r'["\\]'

	# Look for non-printable characters.
	pattern2 = '[^\x20-\x7E]'

	# Look for trigraphs.
	pattern3 = r"\?\?([!'()\-/<=>])"

	if re.search(pattern, s) or re.search(pattern2, s) or re.search(pattern3, s):
		return c(s)
	else:
		return s


def pcre(s):
	"""Escape non-alphanumeric characters and non-underscore characters for a Perl Compatible Regular Expression (PCRE)."""

	pattern = '([^A-Za-z0-9_])'
	replacement = r'\\\1'

	return re.sub(pattern, replacement, s)


def csv(s, field_separator = ',', record_separator = '\n'):
	"""Quote the string (in some cases) for a CSV field.  \
If the string contains a double quote, then escape double quotes, and surround the result with double quotes.  \
If the string contains a field separator, contains a record separator, begins with whitespace, or ends with whitespace, then surround the result with double quotes."""

	if '"' in s:
		# Replace double quotes with 2 double quotes.
		# Surround the result with double quotes.
		return '"' + s.replace('"', '""') + '"'

	if (field_separator in s) or (record_separator in s) or ((len(s) > 0) and ((s[0] in string.whitespace) or (s[-1] in string.whitespace))):
		# Surround the result with double quotes.
		return '"' + s + '"'

	return s


quoting_style_to_function_map = {
	'literal'      : literal     ,
	'shell-always' : shell_always,
	'shell'        : shell       ,
	'escape'       : escape      ,
	'c'            : c           ,
	'c-maybe'      : c_maybe     ,
	'pcre'         : pcre        ,
	'csv'          : csv         ,
}


def quote(s, quoting_style):

	if quoting_style in quoting_style_to_function_map:
		return quoting_style_to_function_map[quoting_style](s)
	else:
		return s

#-------------------------------------------------------------------------------


def main(argv = None):

	import getopt
	import os.path
	import signal

	#---------------------------------------------------------------------------

	if argv is None:
		argv = sys.argv

	#---------------------------------------------------------------------------

	program_name = os.path.basename(argv[0])

	program_authors = ['Steve Ward']

	#---------------------------------------------------------------------------

	# valid values
	valid_quoting_styles = sorted(quoting_style_to_function_map.keys())

	# default values
	default_quoting_style = 'literal'
	default_delimiter = os.linesep

	# mutable values
	quoting_style = default_quoting_style
	delimiter = default_delimiter

	#---------------------------------------------------------------------------

	def print_help():
		"""Print the help message and exit."""

		print("""Usage: {} [OPTION]... [FILE]...
Quote the lines of FILE according to a quoting style.

If FILE is absent, or if FILE is '-', read standard input.

OPTIONS

-V, --version
    Print the version information and exit.

-h, --help
    Print this message and exit.

-q, --quoting-style=STYLE
    Use quoting style STYLE to quote lines. See below for descriptions of all quoting styles.
    (default: {})
    (valid: {})

-0, --null
    Use NULL as the line delimiter instead of NEWLINE.
""".format(
			program_name,
			default_quoting_style,
			','.join(valid_quoting_styles),
			))

		print("QUOTING STYLES")
		print()
		for key in sorted(quoting_style_to_function_map):
			value = quoting_style_to_function_map[key]
			print("'{}' : {}".format(key, value.__doc__))
			print()


	def print_version():
		"""Print the version information and exit."""
		print("{} {}".format(program_name, __version__))
		print("Written by {}".format(', '.join(program_authors)))


	def print_warning(s):
		"""Print the warning message and continue."""
		print("Warning: {}".format(s), file=sys.stderr)


	def print_error(s):
		"""Print the error message and exit."""
		print("Error: {}".format(s), file=sys.stderr)
		print("Try '{} --help' for more information.".format(program_name), file=sys.stderr)

	#---------------------------------------------------------------------------

	def signal_handler(signal_num, execution_frame):
		sys.exit(0)

	signal.signal(signal.SIGINT, signal_handler) # Interactive attention signal. (Ctrl-C)
	signal.signal(signal.SIGTERM, signal_handler) # Termination request. (kill default signal)

	#---------------------------------------------------------------------------

	short_options = 'Vhq:0'
	long_options = ['version', 'help', 'quoting-style=', 'null']

	try:
		(options, remaining_args) = getopt.getopt(argv[1:], short_options, long_options)
	except getopt.GetoptError as err:
		print_error(err)
		return 1

	for (option, value) in options:
		if option in ['-V', '--version']:
			print_version()
			return
		elif option in ['-h', '--help']:
			print_help()
			return
		elif option in ['-q', '--quoting-style']:
			quoting_style = value
		elif option in ['-0', '--null']:
			delimiter = '\0'
		else:
			print_error("Unhandled option '{}'.".format(option))
			return 1

	#---------------------------------------------------------------------------
	# Validate quoting_style.

	if quoting_style not in valid_quoting_styles:
		print_error("{} is not a valid quoting style.".format(quoting_style))
		return 1

	#---------------------------------------------------------------------------

	def quote_lines(lines):

		quote_function = quoting_style_to_function_map[quoting_style]

		for line in lines:
			print(quote_function(line.rstrip(delimiter)), end=delimiter)

	def quote_file_data(file_data):

		lines = file_data.split(delimiter)

		# If the last line ended with the delimiter,
		if len(lines[-1]) == 0:
			del lines[-1]

		quote_lines(lines)

	#---------------------------------------------------------------------------

	# No file was given.
	if len(remaining_args) == 0:
		remaining_args.append('-')

	for file_name in remaining_args:

		file_data = None

		try:

			if file_name == '-':

				# Read standard input.

				if delimiter == os.linesep:
					quote_lines(sys.stdin)
				else:
					quote_file_data(sys.stdin.read())

			else:

				# Read the file.

				with open(file_name, 'r') as f:

					if delimiter == os.linesep:
						quote_lines(f)
					else:
						quote_file_data(f.read())

		except (OSError, UnicodeDecodeError) as err:
			print_error(err)
			return 1


#-------------------------------------------------------------------------------

if __name__ == '__main__':
	sys.exit(main())
