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

	def __init__(self, notebook):
		'''Settings Notebook for Linux'''
		super().__init__(notebook)
		notebook.add(self, text=SettingsLabels.SETTINGS)
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
		self.set_ro = Checker(
			self,
			BooleanVar(),
			SettingsLabels.SET_NEW_RO,
			tip = SettingsLabels.TIP_SET_NEW_RO
		)

	def _become_root(self):
		'''Executet to use root privileges'''
		print('DEBUG:', self.sudo.get())