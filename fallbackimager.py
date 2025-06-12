#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.6.0_2025-04-02'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI for libewf'

from pathlib import Path
from argparse import ArgumentParser
from lib.config import Config
from lib.gui import Gui

class Gui(GuiBase):
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
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-c', '--config', type=Path, help='Config file (default: ~/.config/fallbackimager.conf.json)')
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	parent_path = Path(__file__).parent
	Gui(
		__version__,
		Config(config if config else __parent_path__ / 'config.json'),
		Config(__parent_path__ / 'gui.json'),
		Config(__parent_path__ / 'labels.json'),
		debug = args.debug
	).mainloop()
