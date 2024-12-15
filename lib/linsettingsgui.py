#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter import StringVar
from .linutils import LinUtils, OpenProc
from .guielements import ExpandedFrame, GridSeparator, StringSelector, GridLabel
from .guielements import Checker, LeftButton, RightButton, LeftLabel, ChildWindow
from .guielements import GridScrolledText, GridFrame, GridButton, Error
from .diskselectgui import DiskSelectGui
from .guilabeling import SettingsLabels

class SettingsFrame(ExpandedFrame):
	'''Notebook tab'''

	def __init__(self, root):
		'''Settings Notebook for Linux'''
		root.settings.this_section = SettingsLabels.SETTINGS
		super().__init__(root.notebook)
		root.notebook.add(self, text=SettingsLabels.SETTINGS)
		GridSeparator(self)
		self.row = 1
		if LinUtils.i_am_root():
			self.sudo = None
		else:
			GridLabel(self, SettingsLabels.SUDO)
			self.sudo = StringSelector(
				self,
				StringVar(),
				SettingsLabels.SET_PASSWORD,
				show='*',
				command = self._become_root,
				tip = SettingsLabels.TIP_SUDO
			)
			GridSeparator(self)
		
		self.rod_path = LinUtils.find_bin('rod', Path(__file__).parent.parent)
		self.rod_proc = None

		self.set_ro = Checker(
			self,
			root.settings.init_boolvar('RUNROD'),
			'Run rod',
			tip = 'DEBUG'
		)

		GridLabel(self, SettingsLabels.WRITE_PROTECTION)
		self.open_config_button = GridButton(self, SettingsLabels.OPEN_CONFIG_WINDOW, self._launch_dev_win,
			tip=SettingsLabels.TIP_CONFIG_WINDOW)
		if not LinUtils.i_am_root() and not LinUtils.no_pw_sudo():
			self.open_config_button.config(state='disabled')
		root.linutils = LinUtils()
		self.root = root

	def _become_root(self):
		'''Executet to use root privileges'''
		self.root.linutils = LinUtils(password=self.sudo.get())
		if self.root.linutils.i_have_root():
			self.sudo.config(state='disabled')
			self.open_config_button.config(state='normal')
		else:
			self.sudo.set('')
			Error(SettingsLabels.NOT_ADMIN)

	def _start_rod(self):
		'''Launch rod process'''
		self.rod_proc = OpenProc(self.rod_path,
			sudo = self.root.linutils.sudo,
			password = self.root.linutils.password,
			indie = True
		)

	def _stop_rod(self):
		'''Kill rod process'''
		if self.rod_proc:
			self.rod_proc.kill()
			self.rod_proc = None

	def _launch_dev_win(self):
		'''Launch child window for RO/RW control'''
		BlockDevGui(self.root, SettingsLabels.BLOCKDEVS, self.open_config_button)

class BlockDevGui(DiskSelectGui):
	'''Child window for RO/RW control'''

	def __init__(self, root, title, button, physical=False, exclude=None):
		'''Window to select disk'''
		self.root = root
		self.button = button
		self.physical = physical
		self.exclude = exclude
		ChildWindow.__init__(self, self.root, title, button=self.button)
		self._main_frame()

	def _main_frame(self):
		'''Main frame'''
		self.main_frame = ExpandedFrame(self)
		self.lsblk(self.main_frame)
		frame = ExpandedFrame(self.main_frame)
		LeftButton(frame, self.REFRESH, self._refresh)
		LeftButton(frame, SettingsLabels.SET_RW, self._set_rw)
		LeftButton(frame, SettingsLabels.SET_RO, self._set_ro)
		RightButton(frame, self.QUIT, self.quit)

	def _set_rw(self):
		'''Set block device to rw'''
		item = self.tree.focus()
		self.root.linutils.set_rw(self.tree.item(item)['text'])
		self.tree.focus(item)
		self._refresh()

	def _set_ro(self):
		'''Set block device to ro'''
		item = self.tree.focus()
		self.root.linutils.set_ro(self.tree.item(item)['text'])
		self.tree.focus(item)
		self._refresh()

	def _choose(self, event):
		'''Run on double click'''
		item = self.tree.identify('item', event.x, event.y)
		self.root.linutils.set_ro(self.tree.item(item)['text'])
		self.tree.see(item)
		self.tree.focus(item)
		self._refresh()
