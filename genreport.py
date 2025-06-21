#/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.7.0_2025-06-21'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
The tool parses a template and replaces %jinsert{}{} or \\jinsert{}{} (one backslash) by values from a JSON file.
Example: report-example-template.txt
'''

from json import load
from re import compile as regcompile
from argparse import ArgumentParser

class GenerateReport:
	'''Parse JSON file throught template to generate report'''

	def __init__(self, json_path, template_path, echo=print):
		'''Generate object'''
		self._json_path = json_path
		self._template_path = template_path
		self._echo = echo
		self._reg = regcompile('[%\\\\]jinsert\\{([^}]*)\\}\\{([^}]+)\\}')

	def run(self):
		'''Run process'''
		with self._json_path.open() as fh:
			inserts = load(fh)
		self.text = ''
		self.errors = 0
		for line in self._template_path.read_text().splitlines():
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
				newline += line[position:]
				self._echo(newline)
				self.text += f'{newline}\n'
		return self.text

if __name__ == '__main__':	# start here if called as application
	arg_parser = ArgumentParser(description=__description__)
	arg_parser.add_argument('-j', '--json', type=Path, required=True,
			help='JSON file to parse (required)', metavar='FILE'
	)
	arg_parser.add_argument('-w', '--write', type=Path,
			help='File to write parsed output (default is STDOUT only)', metavar='FILE'
	)
	arg_parser.add_argument('template', nargs=1, type=Path,
			help='Template text file', metavar='FILE'
	)
	args = arg_parser.parse_args()
	genreport = GenerateReport(args.json, args.template[0])
	genreport.run()
	if args.write:
		args.write.write_text(genreport.text)
