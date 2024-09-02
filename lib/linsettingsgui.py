#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import StringVar, BooleanVar
from tkinter.messagebox import askyesno, showerror
from .linutils import LinUtils
from .guielements import ExpandedFrame, GridSeparator, StringSelector, GridLabel
from .guielements import Checker, LeftButton, RightButton, LeftLabel, ChildWindow
from .guielements import GridScrolledText, GridFrame, GridButton
from .guilabeling import SettingsLabels

class SettingsFrame(ExpandedFrame):

	def __init__(self, root):
		'''Settings Notebook for Linux'''
		super().__init__(root.notebook)
		root.notebook.add(self, text=SettingsLabels.SETTINGS)
		GridSeparator(self)
		self.row = 1
		if not LinUtils.i_am_root():
			GridLabel(self, SettingsLabels.SUDO)
			self.sudo = StringSelector(
			self,
			StringVar(),
			SettingsLabels.PASSWORD,
			show='*',
			command = self._become_root,
			tip = SettingsLabels.TIP_SUDO
		)
			GridSeparator(self)
		GridLabel(self, SettingsLabels.WRITE_PROTECTION)
		self._ro = Checker(
			self,
			BooleanVar(),
			SettingsLabels.SET_NEW_RO,
			command = self._change_rorw,
			tip = SettingsLabels.TIP_SET_NEW_RO,
			columnspan = 3
		)
		self._disks = set(LinUtils.get_disks())
		self.root = root
		#self._blockdevs()

	def _blockdevs(self):
		'''Handle blockdevs'''
		old_disks = self._disks
		self._disks = set(LinUtils.get_disks())
		new_disks = self._disks - old_disks
		for disk in new_disks:
			print('DEBUG', disk)
		self.root.after(10000, self._blockdevs())

	def _become_root(self):
		'''Executet to use root privileges'''
		print('DEBUG:', self.sudo.get())

	def _change_rorw(self):
		'''Execute when RO/RW checker changes'''
		print('DEBUG', self._ro.get())
