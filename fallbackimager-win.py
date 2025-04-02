#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager for Windows'
__author__ = 'Markus Thilo'
__version__ = '0.6.0_2025-04-02'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a modular utility for forensic work as a complement
or fallback to the commercial and/or established tools.
The modules write log files into given output directory,
calculate hashes and/or lists of copied files etc.
Multiple jobs can be generated and executed sequentially.
This is the GUI but I would recommand the CLI tools that
are provided alongside. This is work in progress.
'''

from pathlib import Path
from argparse import ArgumentParser
from lib.settings import Settings
from lib.guibase import GuiBase
from sys import executable as __exe__
from hashedrobocopy import HashedRoboCopy, HashedRoboCopyCli
from lib.hashedrobocopygui import HashedRoboCopyGui
from zipimager import ZipImager, ZipImagerCli
from lib.zipimagergui import ZipImagerGui
from sqlite import SQLite, SQLiteCli
from lib.sqlitegui import SQLiteGui
from reporter import Reporter, ReporterCli
from lib.reportergui import ReporterGui
from axchecker import AxChecker, AxCheckerCli
from lib.axcheckergui import AxCheckerGui
from wipew import WipeW, WipeWCli
from lib.wipewgui import WipeWGui

class Gui(GuiBase):
	'''Define the GUI'''

	CANDIDATES = (
		(HashedRoboCopy, HashedRoboCopyCli, HashedRoboCopyGui),
		(ZipImager, ZipImagerCli, ZipImagerGui),
		(SQLite, SQLiteCli, SQLiteGui),
		(Reporter, ReporterCli, ReporterGui),
		(AxChecker, AxCheckerCli, AxCheckerGui),
		(WipeW, WipeWCli, WipeWGui)
	)

	def __init__(self, config=None, debug=False):
		'''Build GUI'''
		exe_path = Path(__exe__)
		parent_path = Path(__file__).parent if exe_path.name == 'python.exe' else exe_path.parent
		super().__init__(
			__app_name__,
			__version__,
			parent_path,
			[(Cli, Gui) for Module, Cli, Gui in self.CANDIDATES if Module().available],
			Settings(config) if config else Settings(parent_path / 'config.json'),
			debug = debug
		)

if __name__ == '__main__':  # start here
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-c', '--config', type=Path, help='Config file (default: config.json in app folder)')
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	Gui(config=args.config, debug=args.debug).mainloop()
