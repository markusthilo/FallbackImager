#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from time import sleep
from tkinter import StringVar
from .linutils import LinUtils, OpenProc
from .guielements import ExpandedFrame, GridSeparator, StringSelector, GridLabel, ExpandedLabelFrame
from .guielements import Checker, LeftButton, RightButton, LeftLabel, ChildWindow, GridBlank
from .guielements import GridScrolledText, GridFrame, GridButton, Error
from .diskselectgui import DiskSelectGui
from .guilabeling import SettingsLabels

class SettingsFrame(ExpandedFrame):
	'''Notebook tab'''

	ROD = 'readonlydaemon'
	SLEEP = .1

	def __init__(self, root):
		'''Settings Notebook for Linux'''
		root.linutils = LinUtils()
		self.root = root
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
		GridLabel(self, SettingsLabels.WRITE_PROTECTION)
		self.open_config_button = GridButton(self, SettingsLabels.OPEN_CONFIG_WINDOW, self._launch_dev_win,
			tip=SettingsLabels.TIP_CONFIG_WINDOW)
		if not LinUtils.i_am_root() and not LinUtils.no_pw_sudo():
			self.open_config_button.config(state='disabled')
		GridSeparator(self)
		GridButton(self, SettingsLabels.CHECK_ROD, self._check_rod, tip=SettingsLabels.TIP_ROD, incrow=False)
		GridButton(self, SettingsLabels.START_ROD, self._start_rod, tip=SettingsLabels.TIP_ROD, column=2, incrow=False)
		GridButton(self, SettingsLabels.STOP_ROD, self._stop_rod, tip=SettingsLabels.TIP_ROD, column=3)
		GridBlank(self)
		self.rod_var = root.settings.init_boolvar(self.ROD, section=SettingsLabels.SETTINGS, default=False)
		self.rod_path = LinUtils.find_bin(self.ROD, Path(__file__).parent.parent)
		self.rod_label = GridLabel(self, '', column=1)
		if root.settings.get(self.ROD, section=SettingsLabels.SETTINGS):
			self._start_rod()
		else:
			self._check_rod()

	def _become_root(self):
		'''Executet to use root privileges'''
		self.root.linutils = LinUtils(password=self.sudo.get())
		if self.root.linutils.i_have_root():
			self.sudo.config(state='disabled')
			self.open_config_button.config(state='normal')
		else:
			self.sudo.set('')
			Error(SettingsLabels.NOT_ADMIN)

	def	_rod_text(self):
		'''Return text for rod label'''
		return SettingsLabels.ROD_RUNNING if LinUtils.get_pid(self.ROD) else SettingsLabels.ROD_NOT_RUNNING

	def _check_rod(self):
		'''Checkif rod is running'''
		self.rod_label.config(text=self._rod_text())

	def _start_rod(self):
		'''Launch rod process'''
		if not LinUtils.get_pid(self.ROD):
			OpenProc(self.rod_path,
				sudo = self.root.linutils.sudo,
				password = self.root.linutils.password,
				indie = True
			)
			self.root.settings.set(self.ROD, True, section=SettingsLabels.SETTINGS)
			sleep(self.SLEEP)
		self._check_rod()

	def _stop_rod(self):
		'''Kill rod process'''
		self.root.linutils.killall(self.ROD)
		self.root.settings.set(self.ROD, False, section=SettingsLabels.SETTINGS)
		sleep(self.SLEEP)
		self._check_rod()

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
