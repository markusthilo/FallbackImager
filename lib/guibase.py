#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import Tk, PhotoImage, TclError
from tkinter.messagebox import askyesno, showerror
from .worker import Worker
from .guielements import ExpandedNotebook, ExpandedFrame, ExpandedScrolledText
from .guielements import LeftButton, RightButton, LeftLabel
from .guilabeling import BasicLabels
from .guiconfig import GuiConfig
from .guihelp import Help

class GuiBase(Tk):

	def __init__(self, name, version, parent_path, modules, settings, not_admin=False, debug=False):
		'''Add stuff to Tk'''
		if len(modules) < 1:
			showerror(
				title = BasicLabels.FATAL_ERROR,
				message = BasicLabels.MODULE_ERROR
			)
			raise ImportError(BasicLabels.MODULE_ERROR)
		self.app_name = name
		self.version = version
		self.debug = debug
		self.worker = None
		self.parent_path = parent_path
		self.settings = settings
		super().__init__()
		title = f'{self.app_name} v{self.version}'
		if not_admin:
			title += f' ({BasicLabels.NOT_ADMIN})'
		self.title(title)
		self.resizable(0, 0)
		self.appicon = PhotoImage(file=parent_path/'appicon.png')
		self.iconphoto(True, self.appicon)
		self.protocol('WM_DELETE_WINDOW', self._quit_app)
		frame = ExpandedFrame(self)
		LeftLabel(frame, BasicLabels.AVAILABLE_MODULES)
		RightButton(frame, BasicLabels.HELP, self._show_help)	
		self.notebook = ExpandedNotebook(self)
		self.modules = [(Cli, Gui(self)) for Cli, Gui in modules]
		try:
			self.notebook.select(self.settings.get('ActiveTab', section='Base'))
		except (KeyError, TclError):
			pass
		frame = ExpandedFrame(self)
		LeftLabel(frame, BasicLabels.JOBS)
		RightButton(frame, BasicLabels.REMOVE_LAST, self._remove_last_job,
			tip=BasicLabels.TIP_REMOVE_LAST_JOB)
		self.jobs_text = ExpandedScrolledText(self, GuiConfig.JOB_HEIGHT)
		frame = ExpandedFrame(self)
		LeftLabel(frame, BasicLabels.INFOS)
		RightButton(frame, BasicLabels.CLEAR_INFOS, self._clear_infos,
			tip=BasicLabels.TIP_CLEAR_INFOS)
		self.infos_text = ExpandedScrolledText(self, GuiConfig.INFO_HEIGHT)
		self.infos_text.bind('<Key>', lambda dummy: 'break')
		self.infos_text.configure(state='disabled')
		frame = ExpandedFrame(self)
		self.start_disabled = False
		self.start_button = LeftButton(frame, BasicLabels.START_JOBS, self._start_jobs,
			tip=BasicLabels.TIP_START_JOBS)
		RightButton(frame, BasicLabels.QUIT, self._quit_app)

	def _show_help(self):
		'''Show help, usually from __description__'''
		Help(self).start()
			
	def append_job(self, cmd):
		'''Append message in info box'''
		last = self.jobs_text.get('end-2l', 'end').strip(';\n')
		if not last or cmd != last:
			self.jobs_text.insert('end', f'{cmd};\n')
			self.jobs_text.yview('end')	

	def _remove_last_job(self):
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

	def _start_jobs(self):
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

	def _clear_infos(self):
		'''Clear info box'''
		self.infos_text.configure(state='normal')
		self.infos_text.delete('1.0', 'end')
		self.infos_text.configure(state='disabled')

	def enable_start(self):
		'''Enable start button'''
		self.start_button.configure(state='normal', text=BasicLabels.START_JOBS)
		self.start_disabled = False

	def disable_start(self):
		'''Disable start button'''
		self.start_button.configure(state='disabled', text=f'{BasicLabels.RUNNING}...')
		self.start_disabled = True

	def	_quit_app(self):
		'''Store configuration and quit application'''
		if askyesno(
					title = f'{BasicLabels.QUIT} {self.app_name}',
					message = BasicLabels.ARE_YOU_SURE
		):
			self.settings.set('ActiveTab', self.notebook.select(), section='Base')
			if err := self.settings.write():
				try:
					self.after(5000, self.destroy)
					showerror(title=BasicLabels.ERROR, message=err)
				except:
					pass
			self.destroy()
