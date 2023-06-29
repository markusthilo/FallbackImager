#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import Tk
from .settings import Settings
from .worker import Worker
from .guielements import ExpandedNotebook, ExpandedFrame
from .guielements import ExpandedScrolledText, LeftButton, RightButton, LeftLabel
from .guihelp import Help

class GuiBase(Tk):

	def __init__(self, name, version, icon_path, settings_path, debug=False):
		'''Add stuff to Tk'''
		self.app_name = name
		self.version = version
		self.debug = debug
		self.icon_path = icon_path
		self.settings = Settings(settings_path)
		self.worker = None
		super().__init__()
		self.title(f'{self.app_name} v{self.version}')
		self.resizable(0, 0)
		self.iconbitmap(self.icon_path)
		frame = ExpandedFrame(self, self)
		LeftLabel(self, frame, self.DESCRIPTION)
		RightButton(self, frame, self.HELP, self.show_help)	
		self.notebook = ExpandedNotebook(self)
		self.imagers = [ImagerGui(self) for ImagerGui in self.IMAGERS]
		frame = ExpandedFrame(self, self)
		LeftLabel(self, frame, self.JOBS)
		self.rm_last_job_button = RightButton(self,
			frame, self.REMOVE_LAST, self.remove_last_job)
		self.jobs_text = ExpandedScrolledText(self, self, self.JOB_HEIGHT)
		frame = ExpandedFrame(self, self)
		LeftLabel(self, frame, self.INFOS)
		self.clear_info_button = RightButton(self, frame, self.CLEAR_INFOS, self.clear_infos)
		self.infos_text = ExpandedScrolledText(self, self, self.INFO_HEIGHT)
		self.infos_text.bind('<Key>', lambda dummy: 'break')
		self.infos_text.configure(state='disabled')
		frame = ExpandedFrame(self, self)
		self.start_disabled = False
		self.start_button = LeftButton(self, frame, self.START_JOBS, self.start_jobs)
		self.quit_button = RightButton(self, frame, self.QUIT, self.quit_app)

	def show_help(self):
		'''Show help, usually from __description__'''
		Help(self).start()
			
	def append_job(self, cmd):
		'''Append message in info box'''
		last = self.jobs_text.get('end-2l', 'end').strip(';\n')
		if not last or cmd != last:
			self.jobs_text.insert('end', f'{cmd};\n')
			self.jobs_text.yview('end')	

	def remove_last_job(self):
		'''Delete last line in job box'''
		if self.jobs_text.get('end-1l', 'end').strip(';\n'):
			self.jobs_text.delete('end-1l', 'end')
		else:
			self.jobs_text.delete('end-2l', 'end')

	def pop_first_job(self):
		'''Read 1st ine in job box and delete'''
		line = self.jobs_text.get('1.0', '2.0')
		self.jobs_text.delete('1.0', '2.0')
		return line.strip('; \n\t')

	def enable_jobs(self):
		'''Enable editing in jobs box'''
		self.jobs_text.configure(state='normal')

	def disable_jobs(self):
		'''Disable editing in jobs box'''
		self.jobs_text.configure(state='disabled')

	def start_jobs(self):
		'''Start working job list'''
		if self.start_disabled or (self.worker and self.worker.is_alive()):
			return
		self.settings.write()
		self.worker = Worker(self)
		self.worker.start()

	def append_info(self, *msg, overwrite=False):
		'''Append message in info box'''
		self.infos_text.configure(state='normal')
		if overwrite:
			self.infos_text.delete('end-2l', 'end')
		self.infos_text.insert('end', ' '.join(f'{string}' for string in msg) + '\n')
		self.infos_text.configure(state='disabled')
		self.infos_text.yview('end')

	def clear_infos(self):
		'''Clear info box'''
		self.infos_text.configure(state='normal')
		self.infos_text.delete('1.0', 'end')
		self.infos_text.configure(state='disabled')

	def enable_start(self):
		'''Enable start button'''
		self.start_button.configure(state='normal', text=self.START_JOBS)
		self.start_disabled = False

	def disable_start(self):
		'''Disable start button'''
		self.start_button.configure(state='disabled', text=f'{self.RUNNING}...')
		self.start_disabled = True

	def	quit_app(self):
		'''Store configuration and quit application'''
		self.settings.write()
		self.destroy()
