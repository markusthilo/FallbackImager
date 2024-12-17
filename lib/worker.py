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
		try:
			self.utils = gui.utils
		except AttributeError:
			self.utils = None

	def run(self):
		'''Start the work'''
		echo = self.gui.infos_text.echo
		cmd = None
		ex_cnt = 0
		while True:
			cmd_line = self.gui.pop_first_job()
			if not cmd_line:
				break
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
			try:
				module = Cli(echo=echo, utils=self.utils)
			except TypeError:
				module = Cli(echo=echo)
			if self.gui.debug:
				module.parse(args[1:])
				module.run()
			else:
				try:
					module.parse(args[1:])
					module.run()
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
		self.gui.finished_jobs()
