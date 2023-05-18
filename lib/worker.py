#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'The worker for this app using threading'

from threading import Thread

class Worker(Thread):
	'''Work job after job'''

	def __init__(self, gui):
		'''Give job list and info handler to Worker object'''
		super().__init__()
		self.gui = gui

	def run(self):
		'''Start the work'''
		self.gui.disable_start()
		echo = self.gui.append_info
		cmd = None
		while True:
			self.gui.enable_jobs()
			cmd_line = self.gui.pop_first_job()
			if not cmd_line:
				break
			self.gui.disable_jobs()
			echo(f'{self.gui.RUNNING}: {cmd_line}')
			cmd, *args = cmd_line.split()
			for ImagerGui, ImagerCli in self.gui.IMAGERS.items():
				if cmd.lower() == ImagerGui.CMD.lower():
					break
			else:
				echo(self.gui.UNDETECTED)
				continue
			imager = ImagerCli()
			imager.parse(args)
			imager.run(echo=echo)
		if cmd:
			echo(self.gui.ALL_DONE)
		else:
			echo(self.gui.NOTHING2DO)
		self.gui.enable_start()
