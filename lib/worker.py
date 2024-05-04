#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
from shlex import split as ssplit
from .guilabeling import BasicLabels

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
			echo(f'{BasicLabels.RUNNING}: {cmd_line}')
			args = ssplit(cmd_line)
			if len(args) == 0 or not args[0]:
				continue
			cmd = args[0]
			for Cli, Gui  in self.gui.modules:
				if args[0].lower() == Gui.MODULE.lower():
					break
			else:
				echo(BasicLabels.UNDETECTED)
				echo()
				continue
			if self.gui.debug:
				module = Cli()
				module.parse(args[1:])
				module.run(echo=echo)
			else:
				try:
					module = Cli()
					module.parse(args[1:])
					module.run(echo=echo)
				except Exception as ex:
					echo(ex)
					ex_cnt += 1
		if cmd:
			echo(BasicLabels.FINISHED_ALL_JOBS)
			echo()
			if ex_cnt > 0:
				echo(BasicLabels.EXCEPTIONS)
				echo()
		else:
			echo(BasicLabels.NOTHING2DO)
			echo()
		self.gui.enable_start()
