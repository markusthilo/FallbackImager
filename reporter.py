#/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'Reporter'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
The tool parses a template and replaces %jinsert{}{} or \\jinsert{}{} (one backslash) by values from a JSON file.
Example: reporter-example-template.txt
'''

from json import load
from re import compile as regcompile
from argparse import ArgumentParser
from lib.pathutils import PathUtils
from lib.timestamp import TimeStamp

class Reporter:
	'''Parse JSON file throught template to generate report'''

	def __init__(self, echo=None):
		'''Generate object'''
		self.available = True

	def parse(self, json, template):
		'''Parse json through template'''
		self.json_path = ExtPath.path(json)
		self.template = ExtPath.path(template)
		with self.json_path.open() as fh:
			inserts = load(fh)
		reg = regcompile('[%\\\\]jinsert\\{([^}]*)\\}\\{([^}]+)\\}')
		self.parsed_text = ''
		self.errors = 0
		for line in self.template.read_text().splitlines():
			newline = ''
			position = 0
			remove_line = False
			for m in reg.finditer(line):
				span = m.span()
				groups = m.groups()
				try:
					insert_text = inserts[groups[1]]
				except KeyError:
					if groups[0] == 'r':
						insert_text = ''
					elif groups[0] == 'rl':
						remove_line = True
						break
					else:
						insert_text = f'### ERROR: unable to find a value for "{groups[1]}" ###'
						self.errors += 1
				newline += line[position:span[0]] + insert_text
				position = span[1]
			if not remove_line:
				self.parsed_text += newline + line[position:] + '\n'
		return self.parsed_text

	def write(self, filename=None, outdir=None):
		'''Write parsed file'''
		self.outdir = PathUtils.mkdir(outdir)
		self.filename = filename if filename else self.json_path.name
		self.destination_path = (self.outdir/f'{self.filename}_report').with_suffix(self.template.suffix)
		self.destination_path.write_text(self.parsed_text)

class ReporterCli(ArgumentParser):
	'''CLI for EwfVerify'''

	def __init__(self, echo=print):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, prog=__app_name__.lower())
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-j', '--json', type=ExtPath.path, required=True,
			help='JSON file to parse (required)', metavar='FILE'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (STDOUT if not given)', metavar='DIRECTORY'
		)
		self.add_argument('template', nargs=1, type=ExtPath.path,
			help='Template text file', metavar='FILE'
		)
		self.echo = echo

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.template = args.template[0]
		self.json = args.json
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self):
		'''Run the verification'''
		reporter = Reporter()
		self.echo(reporter.parse(self.json, self.template))
		if reporter.errors > 0:
			raise RuntimeError(f'Parser reported {reporter.errors} error(s)')
		if self.outdir or self.filename:
			reporter.write(filename=self.filename, outdir=self.outdir)

if __name__ == '__main__':	# start here if called as application
	app = ReporterCli()
	app.parse()
	app.run()
