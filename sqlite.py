#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'Sqlite'
__author__ = 'Markus Thilo'
__version__ = '0.2.2_2023-10-10'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Work with SQLite (for RDSv3 e.g.)
'''

from pathlib import Path
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.sqliteutils import SQLiteExec, SQLiteReader
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.guielements import BasicFilterTab

class SQLite:
	'''Imager using ZipFile'''

	def __init__(self, db,
		filename = None,
		outdir = None,
		echo = print,
		log = None
	):
		'''Prepare to create zip file'''
		self.echo = echo
		self.db_path = Path(db)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.log = log

	def start_log(self):
		'''Start logging'''
		if not self.log:
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='sqlite.SQLite', echo=self.echo)

	def schema(self):
		'''Get database schema'''
		self.echo('Getting schema from database')
		reader = SQLiteReader(self.db_path)
		for name, columns in reader.list_tables():
			col_names = ', '.join(columns)
			self.echo(f'{name}: {col_names}')
		reader.close()

	def execute(self, sql_path):
		'''Execute statements from SQL file'''
		self.log.info('Executing statements from SQL file', echo=True)
		executor = SQLiteExec(self.db_path)
		statement_cnt = executor.alter(sql_path)
		self.log.info(f'Applied {statement_cnt} statements from {sql_path} to {self.db_path}', echo=True)

	def dump(self, table, field, sort=False, uniq=False):
		'''Dump to text file'''
		self.echo('Dumping to text file')
		reader = SQLiteReader(self.db_path)
		with ExtPath.child(f'{self.filename}_{table}.txt', parent=self.outdir
			).open(mode='w', encoding='utf-8') as fh:
			if sort or uniq:
				if sort and uniq:
					dump = sorted(list({entry for entry in reader.fetch_table(table, field)}))
				elif sort and not uniq:
					dump = sorted([entry for entry in reader.fetch_table(table, field)])
				else:
					dump = list({entry for entry in reader.fetch_table(table, field)})
				for entry in dump:
					print(entry, file=fh)
				cnt = len(dump)
			else:
				cnt = 0
				for entry in reader.fetch_table(table, field):
					print(entry, file=fh)
					cnt += 1
		self.log.info(f'Wrote {cnt} entries/values', echo=True)
		reader.close()

class SQLiteCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(**kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-c', '--column', type=str,
			help='Column/field to dump'
		)
		self.add_argument('-l', '--schema', default=False, action='store_true',
			help='List tables/schema, ignore other tasks'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-s', '--sort', default=False, action='store_true',
			help='Sort dump lines'
		)
		self.add_argument('-t', '--table', type=str,
			help='Dump table'
		)
		self.add_argument('-u', '--uniq', default=False, action='store_true',
			help='Unique dump lines'
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
		self.filename = args.filename
		self.outdir = args.outdir
		self.schema = args.schema
		self.sort = args.sort
		self.table = args.table
		self.uniq = args.uniq
		self.execute = args.execute

	def run(self, echo=print):
		'''Run the imager'''
		sqlite = SQLite(self.db,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		if self.schema:
			sqlite.schema()
		else:
			sqlite.start_log()
			if self.execute:
				sqlite.execute(self.execute)
			if self.table:
				sqlite.dump(self.table, self.column, sort=self.sort, uniq=self.uniq)
			sqlite.log.close()

class SQLiteGui(BasicFilterTab):
	'''Notebook page'''
	CMD = __app_name__
	DESCRIPTION = __description__
	def __init__(self, root):
		super().__init__(root)

if __name__ == '__main__':	# start here if called as application
	app = SQLiteCli(description=__description__.strip())
	app.parse()
	app.run()
