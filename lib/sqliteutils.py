#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlite3 import connect as SqliteConnect

class SQLiteExec:
	'''Execute statements'''

	QUOTES = '\'"'

	def __init__(self, sqlite_path):
		'''Open database'''
		self.db = SqliteConnect(sqlite_path)
		self.cursor = self.db.cursor()

	def from_file(self, statements_path):
		'''Read statements from file (.sql) and execute command after command'''
		statement = ''
		inside_quotes = None
		with statements_path.open(encoding='utf-8') as fh:
			for line in fh:
				for char in line:
					if char == '\n':
						continue
					statement += char
					if char == inside_quotes:
						inside_quotes = None
						continue
					if inside_quotes:
						continue
					if char in self.QUOTES:
						inside_quotes = char
						continue
					if char == ';' and not inside_quotes:
						try:
							self.cursor.execute(statement)
						except Exception as ex:
							yield ex
						yield None
						statement = ''

	def commit(self):
		'''Commit to SQLite database'''
		try:
			self.db.commit()
		except Exception as ex:
			return ex
		return None

	def close(self):
		'''Close database'''
		self.db.close()

class SQLiteReader:
	'''Read SQLite files'''

	NO_QUOTE_TYPES = ('INTEGER', 'REAL', 'NUMERIC')
	IGNORED_TYPES = ('BLOB',)

	def __init__(self, sqlite_path):
		'''Open database'''
		self.db = SqliteConnect(sqlite_path)
		self.cursor = self.db.cursor()

	def get_tables(self):
		'''List tables from scheme'''
		self.cursor.execute(f'SELECT name FROM sqlite_schema WHERE type="table"')
		for table in self.cursor.fetchall():
			yield table[0]

	def get_columns(self, table):
		'''Get column names for one table'''
		self.cursor.execute(f'SELECT name FROM pragma_table_info("{table}");')
		return (res[0] for res in self.cursor.fetchall())

	def count(self, table):
		'''Get number of lines in a table'''
		self.cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
		return self.cursor.fetchone()[0]

	def get_type(self, table, column):
		'''Get column type'''
		self.cursor.execute(f'SELECT typeof("{column}") FROM "{table}"')
		try:
			return self.cursor.fetchone()[0]
		except:
			return None
		
	def get_printable(self, table, column):
		'''Return non printable type, quotes or no quotes'''
		tp = self.get_type(table, column).upper()
		if tp in self.NO_QUOTE_TYPES:
			return ''
		if tp in self.IGNORED_TYPES:
			return tp.upper()
		return '"'

	def list_tables(self):
		'''List tables with column names from scheme'''
		for table in self.get_tables():
			yield table, self.get_columns(table)

	def fetch_table(self, table, column=None, columns=None, where=None):
		'''Fetch one table row by row'''
		if column and columns:
			raise ValueError('Argument "column=" or "columns=" is possible, not both')
		cmd = 'SELECT '
		if column:
			cmd += f'"{column}"'
		elif columns:
			cmd += ', '.join(f'"{column}"' for column in columns)
		else:
			cmd += '*'
		cmd += f' FROM "{table}"'
		if where:
			cmd += f' WHERE {where}'
		if column:
			for row in self.cursor.execute(cmd):
				yield row[0]
		else:
			for row in self.cursor.execute(cmd):
				yield row

	def close(self):
		'Close SQLite database'
		self.db.close()

class SQLDump:
	'''Handle SQL dump file'''

	SQL_COMMANDS = (
		'*',
		'AND',
		'AS',
		'BETWEEN',
		'BY',
		'COMMIT',
		'CONSTRAINT',
		'COPY',
		'CREATE',
		'DATABASE',
		'DELETE',
		'DISTINCT',
		'DROP',
		'EXISTS',
		'FROM',
		'FULL',
		'FOREIGN',
		'GRANT',
		'GROUP',
		'HAVING',
		'IN',
		'INDEX',
		'INNER',
		'INSERT',
		'INTO',
		'JOIN',
		'KEY',
		'LEFT',
		'LIKE',
		'LOCK',
		'NOT',
		'OR',
		'ORDER',
		'PRIMARY',
		'REFERENCES',
		'REVOKE',
		'RIGHT',
		'ROLLBACK',
		'SAVEPOINT',
		'SELECT',
		'SET',
		'TABLE',
		'TABLES',
		'TOP',
		'TRUNCATE',
		'UNION',
		'UNIQUE',
		'UNLOCK',
		'UPDATE',
		'VIEW',
		'WHERE'
	)

	def __init__(self, dump_path):
		'''Create object for one sql dump file'''
		self.dump_path = dump_path

	def get_char(self, line):
		'''Fetch the next character'''
		if not line:
			return '', ''
		return line[0], line[1:]

	def get_word(self, line):
		'Get one word'
		word = ''
		while line:
			char, line = self.get_char(line)
			if char == None or char in ' \t,;()"\'\n':
				break
			word += char
		return word, char, line

	def fetch_quotes(self, quote, line):
		'Fetch everything inside quotes'
		text = ''
		while line:
			char, line = self.get_char(line)
			if not char:	# read next line if line is empty
				line = self.dumpfh.readline()
				if not line:	# eof
					break
				text += '\\n'	# generate newline char
				continue
			if char == '\\':	# get next char when escaped
				nextchar, line = self.get_char(line)
				if nextchar == None:
					continue
				text += char + nextchar
				continue
			if char == quote:
				break
			text += char
		return text, line

	def read_cmds(self):
		'Line by line'
		line = '\n'
		char = '\n'
		cmd = list()
		while char:	# loop until eof
			if char == ';':	# give back whole comment on ;
				yield cmd
				cmd = list()
			elif char == '\\':	# \.
				char, line = self.get_char(line)
				if char == '.':
					yield cmd
					cmd = list()
				else:
					cmd += '\\' + char
			elif char in '(),':	# special chars
				cmd.append(char)
			elif char.isalnum():	# instruction or argument
				word, char, line = self.get_word(char + line)
				cmd.append(word)
				continue
			elif char in '\'"`':	# skip everything inside quotes
				text, line = self.fetch_quotes(char, line)
				cmd.append(char + text + char)
			while not line or line == '\n':	# read from dumpfile
				line = self.dumpfh.readline()
				if not line:	# eof
					char = ''
					break
				line = line.lstrip(' \t')	# skip leading blanks
				if line[0] in '-/':	# ignore comments and unimportand lines
					line = ''
					continue
			char, line = self.get_char(line)	# char by char
		if cmd != list():	# tolerate missing last ;
			yield cmd

	def get_next(self, part_cmd):
		'Get next element'
		if part_cmd == list():	# to be save
			return '', list()
		return part_cmd[0], part_cmd[1:]

	def get_next_upper(self, part_cmd):
		'Get next element and normalize tu upper chars'
		if part_cmd == list():	# to be save
			return '', list()
		return part_cmd[0].upper(), part_cmd[1:]

	def check_strings(self, part_cmd, *strings):
		'Check for matching, strings must be uppercase'
		if part_cmd == list():	# to be save
			return '', list()
		if part_cmd[0].upper() in strings:
			return part_cmd[0], part_cmd[1:]
		return '', part_cmd

	def seek_strings(self, part_cmd, *strings):
		'Seek matching string'
		first_part_cmd = list()
		while part_cmd != list():
			matching, part_cmd = self.check_strings(part_cmd, *strings)
			if matching:
				return first_part_cmd, matching, part_cmd
			first_part_cmd.append(part_cmd[0])	# shift
			part_cmd = part_cmd[1:]
		return first_part_cmd, '', list()

	def skip_brackets(self, part_cmd):
		'Ignore everything inside brackets'
		bracket_cnt = 0
		while part_cmd != list():
			element, part_cmd = self.get_next(part_cmd)
			if element == ')' and bracket_cnt == 0:
				return part_cmd
			if element == '(':
				bracket_cnt += 1
			elif element == ')':
				bracket_cnt -= 1
		return list()

	def get_list(self, part_cmd):
		'Get comma seperated list, take only the first elements behind the comma'
		elements = list()
		matching = ','
		while part_cmd != list():
			element, part_cmd = self.get_next(part_cmd)
			if not element:
				return elements, part_cmd
			if matching in '),' and not element.upper() in self.SQL_COMMANDS:
				elements.append(element)
			first_part_cmd, matching, part_cmd = self.seek_strings(part_cmd, '(', ')', ',')
			if matching == '(':
				part_cmd = self.skip_brackets(part_cmd)
			elif not matching or matching == ')':
				return elements, part_cmd

	def el2str(self, elements):
		'Generate string from elements'
		return ' ' + ' '.join(elements)

	def list2str(self, in_brackets):
		'Generate string with brackets from a list of elements'
		return ' (' + ', '.join(in_brackets) + ')'

	def list2quotes(self, in_brackets):
		'Generate string with brackets from a list of elements'
		return ' (`' + '`, `'.join(in_brackets) + '`)'

	def list2qmarks(self, in_brackets):
		'Generate string linke (?, ?, ?) from a list of elements'
		return ' (' + '?, ' * (len(in_brackets) - 1) + '?)'

	def unbracket(self, in_brackets):
		'Remove brackets from strings in an iterable'
		return [ string.strip('\'"`') for string in in_brackets ]

	def translate_all(self):
		'''Fetch all tables'''
		with self.dump_path.open(encoding='utf8') as self.dumpfh:
			for raw_cmd in self.read_cmds():
				cmd_str, part_cmd = self.get_next_upper(raw_cmd)
				if cmd_str == 'CREATE':	# CREATE TABLE
					element, part_cmd = self.get_next_upper(part_cmd)
					if element != 'TABLE':
						continue
					cmd_str += ' TABLE'
					first_part_cmd, matching, part_cmd = self.seek_strings(part_cmd, '(')
					if not matching:	# skip if no definitions in ()
						continue
					cmd_str += self.el2str(first_part_cmd)
					in_brackets, part_cmd = self.get_list(part_cmd)
					if in_brackets == list():
						continue
					cmd_str += self.list2str(in_brackets) + ';'
					yield cmd_str, ()
					continue
				if cmd_str == 'INSERT':	# INSERT INTO
					element, part_cmd = self.get_next_upper(part_cmd)
					if element != 'INTO':
						continue
					cmd_str += ' INTO'
					first_part_cmd, matching, part_cmd = self.seek_strings(part_cmd, '(', 'VALUES')
					if not matching:	# skip if no nothing to insert
						continue
					if matching == '(':
						in_brackets, part_cmd = self.get_list(part_cmd)
						cmd_str += self.el2str(first_part_cmd) + self.list2str(in_brackets)
						first_part_cmd, matching, part_cmd = self.seek_strings(part_cmd, 'VALUES')
					base_str = cmd_str + self.el2str(first_part_cmd) + ' VALUES'
					while part_cmd != list():	# one command per value/row
						first_part_cmd, matching, part_cmd = self.seek_strings(part_cmd, '(')
						if not matching:	# skip if no values
							continue
						in_brackets, part_cmd = self.get_list(part_cmd)
						cmd_str = base_str + self.list2qmarks(in_brackets)
						first_part_cmd, matching, part_cmd = self.seek_strings(part_cmd, ',', ';')
						yield cmd_str + ';', self.unbracket(in_brackets)
						if matching == ';' :
							break
						continue
				if cmd_str == 'COPY':	# COPY FROM stdin
					first_part_cmd, matching, part_cmd = self.seek_strings(part_cmd, '(')
					if not matching:	# skip if no nothing to insert
						continue
					in_brackets, part_cmd = self.get_list(part_cmd)
					base_str = f'INSERT INTO `{first_part_cmd[0]}`' + self.list2quotes(in_brackets)
					values = next(self.read_cmds())
					set_len = len(in_brackets)
					base_str += ' VALUES' + self.list2qmarks(in_brackets) + ';'
					for value_ptr in range(0, len(values), set_len):	# loop through values
						yield base_str, values[value_ptr:value_ptr+set_len]
