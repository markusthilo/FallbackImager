#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.7.0_2025-06-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI for libewf'

from pathlib import Path
from argparse import ArgumentParser
#from lib.config import Config
#from lib.gui import Gui

class Gui:
	'''Define the GUI'''

	def __init__(self, config=None, debug=False):
		'''Build GUI'''
		super().__init__(
			__app_name__,
			__version__,
			Path(__file__).parent,
			[(Cli, Gui) for Module, Cli, Gui in self.CANDIDATES if Module().available],
			Settings(config) if config else Settings(Path.home() / '.config/fallbackimager.conf.json'),
			debug = debug
		)

if __name__ == '__main__':  # start here
	config_path = Path.home().joinpath('.config', 'fallbackimager.conf.json')
	argp = ArgumentParser(description=__description__, epilog=f'{__author__} ({__email__}, License: {__license__})')
	argp.add_argument('-c', '--config',
		type = Path,
		default = config_path,
		help = f'Config file (default: {config_path}'
	)
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	print(config_path)
	'''
	Gui(
		args.config_path,
		debug = args.debug
	).mainloop()
	'''