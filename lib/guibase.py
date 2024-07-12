#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import Tk, PhotoImage, TclError
from tkinter.messagebox import askyesno, showerror
from tkinter.font import nametofont
from tkinter.scrolledtext import ScrolledText
from .worker import Worker
from .guielements import ExpandedNotebook, ExpandedFrame, ExpandedScrolledText
from .guielements import LeftButton, RightButton, LeftLabel, ChildWindow
from .guielements import GridScrolledText, GridFrame, GridButton
from .guilabeling import BasicLabels
from .guiconfig import GuiConfig
try:
	from win32com.shell.shell import IsUserAnAdmin
	__not_admin__ = not IsUserAnAdmin()
except ModuleNotFoundError:
	__not_admin__ = False

class GuiBase(Tk):

	def __init__(self, name, version, parent_path, modules, settings, debug=False):
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
		if __not_admin__:
			title += f' ({BasicLabels.NOT_ADMIN})!'
		self.title(title)
		self.resizable(0, 0)
		self.appicon = PhotoImage(file=self.parent_path/'appicon.png')
		self.iconphoto(True, self.appicon)
		self.protocol('WM_DELETE_WINDOW', self._quit_app)
		font = nametofont('TkTextFont').actual()
		self.font_family = font['family']
		self.font_size = font['size']
		self.padding = int(self.font_size / GuiConfig.PAD)
		frame = ExpandedFrame(self)
		LeftLabel(frame, BasicLabels.AVAILABLE_MODULES)
		self.help_button = RightButton(frame, BasicLabels.HELP, self._show_help)
		self.notebook = ExpandedNotebook(self)
		self.modules = [(Cli, Gui(self)) for Cli, Gui in modules]
		try:
			self.notebook.select(self.settings.get('ActiveTab', section='Base'))
		except (KeyError, TclError):
			pass
		frame = ExpandedFrame(self)
		LeftLabel(frame, BasicLabels.JOBS)
		self.jobs_text = ExpandedScrolledText(self, GuiConfig.JOB_HEIGHT)
		RightButton(frame, BasicLabels.REMOVE_LAST, self._remove_last_job,
			tip=BasicLabels.TIP_REMOVE_LAST_JOB)
		frame = ExpandedFrame(self)
		self.start_button = LeftButton(frame, BasicLabels.START_JOBS, self._start_jobs,
			tip=BasicLabels.TIP_START_JOBS)
		RightButton(frame, BasicLabels.QUIT, self._quit_app)
		self.update()
		self.root_width = self.winfo_width()
		self.root_height = self.winfo_height()

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

	def _start_jobs(self):
		'''Start working job list'''
		self.start_button.configure(text=f'{BasicLabels.RUNNING}...')
		self.settings.write()
		self.info_window = ChildWindow(self, BasicLabels.INFOS,
			resizable = True,
			button = self.start_button,
			destroy = self._close_infos
		)
		self.infos_text = GridScrolledText(
			self.info_window,
			GuiConfig.ENTRY_WIDTH,
			int(self.root_height / (2*self.font_size)),
			ro=True
		)
		self.stop_button = GridButton(self.info_window, BasicLabels.STOP_WORK, self._close_infos, sticky='e')
		self.info_window.set_minsize()
		self.worker = Worker(self)
		self.worker.start()

	def finished_jobs(self):
		'''This is called from worker when all jobs are done.'''
		self.worker = None
		self.stop_button.configure(text=BasicLabels.QUIT)

	def	_close_infos(self):
		'''Close info window, ask to terminate worker in case it is still running.'''
		if self.worker:
			if askyesno(
				title = f'{BasicLabels.STOP_WORK}?',
				message = BasicLabels.ARE_YOU_SURE
			):
				self.worker.terminate()
			else:
				return
		self.worker = None
		self.start_button.configure(state='normal', text=BasicLabels.START_JOBS)
		self.info_window.destroy()

	def append_info(self, *msg, overwrite=False):
		'''Append message in info box'''
		self.infos_text.configure(state='normal')
		if overwrite:
			self.infos_text.delete('end-2l', 'end')
		self.infos_text.insert('end', ' '.join(f'{string}' for string in msg) + '\n')
		self.infos_text.configure(state='disabled')
		self.infos_text.yview('end')

	def	_quit_app(self):
		'''Store configuration and quit application'''
		msg = BasicLabels.ARE_YOU_SURE
		if self.worker:
			msg += f'\n\n{BasicLabels.JOB_RUNNING}'
		if askyesno(title=f'{BasicLabels.QUIT} {self.app_name}', message=msg):
			self.settings.set('ActiveTab', self.notebook.select(), section='Base')
			if err := self.settings.write():
				try:
					self.after(5000, self.destroy)
					showerror(title=BasicLabels.ERROR, message=err)
				except:
					pass
			self.destroy()

	def pixels(self, chars):
		'''Approximate pixel size from chars'''
		return self.font_size * chars

	def _show_help(self):
		'''Show help window'''
		help_window = ChildWindow(self, BasicLabels.HELP, resizable=True, button=self.help_button)
		help_text = GridScrolledText(
			help_window,
			GuiConfig.HELP_WIDTH,
			int(self.root_height / (2*self.font_size)),
			ro=True
		)
		utf_text = f'{self.app_name} v{self.version}\n\n{BasicLabels.DESCRIPTION}\n\n\n'
		try:
			utf_text += (self.parent_path/'help.txt').read_text(encoding='utf-8')
		except:
			utf_text += BasicLabels.HELP_ERROR
		help_text.echo(f'{utf_text}\n', end=False)
		GridButton(help_window, BasicLabels.QUIT, help_window.quit, sticky='e')
		help_window.set_minsize()
