#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from .guilabeling import BasicLabels
from .guiconfig import GuiConfig
from .guielements import ChildWindow, ExpandedFrame, ExpandedTree, LeftButton, RightButton
from .linutils import LinUtils
from .stringutils import StringUtils

class DiskSelectGui(ChildWindow, BasicLabels):
	'''GUI to select disk (Linux)'''

	def __init__(self, root, title, select, physical=False, exclude=None):
		'''Window to select disk'''
		try:
			if root.child_win_active:
				return
		except AttributeError:
			pass
		self.root = root
		self._select = select
		self.physical = physical
		self.exclude = exclude
		self.root.child_win_active = True
		ChildWindow.__init__(self, self.root, title)
		self._main_frame()

	def _main_frame(self):
		'''Main frame'''
		self.main_frame = ExpandedFrame(self)
		self.lsblk(self.main_frame)
		frame = ExpandedFrame(self.main_frame)
		LeftButton(frame, self.REFRESH, self._refresh)
		RightButton(frame, self.QUIT, self.destroy)

	def lsblk(self, root):
		'''Frame with of lsblk tree'''
		frame = ExpandedFrame(root)
		blkdevs = LinUtils.lsblk(physical=self.physical, exclude=self.exclude)
		self.tree = ExpandedTree(frame,
			text = 'name',
			width = GuiConfig.LSBLK_NAME_WIDTH,
			columns = GuiConfig.LSBLK_COLUMNS_WIDTH
		)
		for path, details in LinUtils.lsblk(physical=self.physical, exclude=self.exclude).items():
			values = (
				details['type'],
				details['size'],
				StringUtils.str(details['label']),
				StringUtils.str(details['vendor']),
				StringUtils.str(details['model']),
				StringUtils.join(details['mountpoints'], delimiter=', ')
			)
			self.tree.insert(details['parent'], 'end', text=path, values=values, iid=path, open=True)
		self.tree.bind("<Double-1>", self._choose)

	def _choose(self, event):
		'''Run on double click'''
		item = self.tree.identify('item', event.x, event.y)
		self._select.set(self.tree.item(item)['text'])
		self.destroy()

	def _refresh(self):
		'''Destroy and reopen Target Window'''
		self.main_frame.destroy()
		self._main_frame()
