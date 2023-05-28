#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
from shlex import split as ssplit

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
		ex_cnt = 0
		while True:
			self.gui.enable_jobs()
			cmd_line = self.gui.pop_first_job()
			if not cmd_line:
				break
			self.gui.disable_jobs()
			echo(f'{self.gui.RUNNING}: {cmd_line}')
			args = ssplit(cmd_line)
			if len(args) == 0 or not args[0]:
				continue
			cmd = args[0]
			for ImagerGui, ImagerCli in self.gui.IMAGERS.items():
				if args[0].lower() == ImagerGui.CMD.lower():
					break
			else:
				echo(self.gui.UNDETECTED)
				continue
			if self.gui.debug:
				imager = ImagerCli()
				imager.parse(args[1:])
				imager.run(echo=echo)
			else:
				try:
					imager = ImagerCli()
					imager.parse(args[1:])
					imager.run(echo=echo)
				except Exception as ex:
					echo(ex)
					ex_cnt += 1
		if cmd:
			echo(self.gui.ALL_DONE)
			if ex_cnt > 0:
				echo(self.gui.EXCEPTIONS)
		else:
			echo(self.gui.NOTHING2DO)
		self.gui.enable_start()
