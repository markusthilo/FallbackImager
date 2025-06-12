#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'Sqlite'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
The Sqlite module uses the Python library sqlite3. It can show the structure of a .db file or dump the content as CSV/TSV. In addition SQL code can be executed by the library. An alternative method is implemented that is designed to generate a .db file from a MySQL dump file in case sqlite3 fails.
'''

from sqlite3 import connect as SqliteConnect
from pathlib import Path
from argparse import ArgumentParser



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




class SQLite:
	'''The easy way to work with SQLite'''

	def __init__(self, echo=print):
		'''Generate object'''
		self.available = True
		self.echo = echo

	def open(self, db,
		filename = None,
		outdir = None,
		log = None
	):
		'''Prepare to create zip file'''
		self.db_path = Path(db)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.log = log

	def start_log(self):
		'''Start logging'''
		if not self.log:
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='sqlite.SQLite', echo=self.echo)

	def trans_ex(self, sql_path, executor):
		'''Read statements from file, translate and execute'''
		sqldump = SQLDump(sql_path)
		for cmd_str, values in sqldump.translate_all():
			try:
				executor.cursor.execute(cmd_str, values)
			except Exception as ex:
				yield ex
			yield None

	def execute(self, sql_path, alternative=False):
		'''Execute statements from SQL file'''
		self.start_log()
		self.log.info('Executing statements from SQL file', echo=True)
		executor = SQLiteExec(self.db_path)
		executed_cnt = 0
		warning_cnt = 0
		if alternative:
			gen_ex = self.trans_ex(sql_path, executor)
		else:
			gen_ex = executor.from_file(sql_path)
		if self.echo == print:
			echo = lambda msg: print(f'\r{msg}', end='')
		else:
			echo = lambda msg: self.echo(msg, overwrite=True)
		echo(1)
		for warning in gen_ex:
			if warning:
				self.log.warning(warning, echo=False)
				warning_cnt += 1
				continue
			executed_cnt += 1
			if executed_cnt % 10000 == 0:
				echo(executed_cnt)
				if msg := executor.commit():
					self.log.warning(msg, echo=False)
					warning_cnt += 1
		echo('')
		if msg := executor.commit():
			self.log.warning(msg)
			warning_cnt += 1 
		executor.close()
		self.log.info(f'Applied {executed_cnt} statement(s) to {self.db_path}', echo=True)
		if warning_cnt > 0:
			self.log.warning(f'SQLite library threw {warning_cnt} exception(s)')
		self.log.close()

	def dump(self, table=None, column=None, sort=False, uniq=False):
		'''Dump to text file'''
		self.start_log()
		self.log.info('Dumping to text/CSV file')
		reader = SQLiteReader(self.db_path)
		if table:
			tables = (table,)
		else:
			tables = reader.get_tables()
		for table in tables:
			try:
				len_table = reader.count(table)
			except Exception as ex:
				self.log.error(ex)
			if len_table == 0:
				self.log.info(f'Skipping table {table} - no items', echo=True)
			else:
				if column:
					tp = reader.get_printable(table, column)
					if tp != '' and tp != '"':
						self.log.info(f'{column} of {table} contains {len_table} of type {tp}')
						continue
					if not column in reader.get_columns(table):
						self.log.info(f'Table {table} does not have {column}', echo=True)
						continue
					with self.outdir.joinpath(f'{self.filename}_{table}_{column}.txt').open(mode='w', encoding='utf-8') as fh:
						for value in reader.fetch_table(table, column=column):
							print(value, file=fh)
					continue
				columns = tuple(col for col in reader.get_columns(table))
				types = tuple(reader.get_printable(table, col) for col in columns)
				self.log.info(f'Creating file for table {table}', echo=True)
				with self.outdir.joinpath(f'{self.filename}_{table}.csv').open(mode='w', encoding='utf-8') as fh:
					print('\t'.join(columns), file=fh)
					for row in reader.fetch_table(table, columns=columns):
						line = list()
						for i, item in enumerate(row):
							if types[i] == '':
								line.append(f'{item}')
							elif types[i] == '"':
								line.append(f'"{item}"')
							else:
								line.append(types[i])
						print('\t'.join(line), file=fh)
		self.log.info('Done', echo=True)
		reader.close()
		self.log.close()

	def schema(self):
		'''Get database schema'''
		self.start_log()
		self.log.info('Write database schema to text/CSV file')
		reader = SQLiteReader(self.db_path)
		with self.outdir.joinpath(f'{self.filename}_schema.txt').open(mode='w', encoding='utf-8') as fh:
			print('table (rows):\tcolumns (type)\t...', file=fh)
			for table, columns in reader.list_tables():
				line = f'{table} ({reader.count(table)}):'
				for column in columns:
					if col_type := reader.get_type(table, column):
						line += f'\t{column} ({col_type})'
					else:
						line += f'\t{column}'
				print(line, file=fh)
		self.log.info('Done', echo=True)
		reader.close()
		self.log.close()

	def list_tables(self):
		'''Get tables with columns'''
		reader = SQLiteReader(self.db_path)
		for name, columns in reader.list_tables():
			yield name, columns

	def get_schema(self):
		'''Get short version of database schema and print/echo'''
		schema = ''
		for name, columns in self.list_tables():
			schema += f'{name}: {", ".join(columns)}\n'
		return schema

class SQLiteCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, echo=print, **kwargs):
		'''Define CLI using argparser'''
		self.echo = echo
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-c', '--column', type=str,
			help='Column/field to dump'
		)
		self.add_argument('-l', '--list', default=False, action='store_true',
			help='List tables/schema, ignore other tasks', dest='echo_schema'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-r', '--read', type=Path,
			help='Read dump file and fill SQLite DB (alternative method to -x)', metavar='FILE'
		)
		self.add_argument('-s', '--schema', default=False, action='store_true',
			help='Write schema of database as text/TSV file'
		)
		self.add_argument('-t', '--table', type=str,
			help='Dump table'
		)
		self.add_argument('-x', '--execute', type=Path,
			help='Execute SQL statements from file an apply to database', metavar='FILE'
		)
		self.add_argument('db', nargs=1, type=Path,
			help='Database file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.db = args.db[0]
		self.column = args.column
		self.echo_schema = args.echo_schema
		self.filename = args.filename
		self.outdir = args.outdir
		self.read = args.read
		self.schema = args.schema
		self.table = args.table
		self.execute = args.execute

	def run(self):
		'''Run the imager'''
		sqlite = SQLite(echo=self.echo)
		sqlite.open(self.db,
			filename = self.filename,
			outdir = self.outdir,
		)
		if self.echo_schema:
			self.echo(sqlite.get_schema())
		else:
			if self.execute:
				sql_path = self.execute
				sqlite.execute(sql_path)
			elif self.read:
				sql_path = self.read
				sqlite.execute(sql_path, alternative=True)
			elif self.schema:
				sqlite.schema()
			else:
				sqlite.dump(table=self.table, column=self.column)

if __name__ == '__main__':	# start here if called as application
	app = SQLiteCli()
	app.parse()
	app.run()
