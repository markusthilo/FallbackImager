#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.7.0_2025-06-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI for libewf and more'

from pathlib import Path
from argparse import ArgumentParser
from classes.config import Config
from classes.gui import Gui

if __name__ == '__main__':  # start here
	config = Config()
	argp = ArgumentParser(description=__description__, epilog=f'{__author__} ({__email__}), License: {__license__}')
	argp.add_argument('-c', '--config',
		type = Path,
		default = config.path,
		help = f'Config file (default: {config.path}'
	)
	argp.add_argument('-d', '--debug', action='store_true', help='Debug mode')
	argp.add_argument('-l', '--lang',
		type = str,
		help = f'Force to use this language at start (default: English / "en")'
	)
	args = argp.parse_args()
	config.update_path(args.config)
	if config.load():
		raise ex
	config.set('app_name', __app_name__, force=True)
	config.set('version', __version__, force=True)
	Gui(config, lang=args.lang, debug=args.debug).mainloop()
