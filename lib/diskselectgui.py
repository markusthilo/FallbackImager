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
		RightButton(frame, self.QUIT, self.quit)

	def lsblk(self, root):
		'''Frame with of lsblk tree'''
		frame = ExpandedFrame(root)
		blkdevs = LinUtils.lsblk(physical=self.physical, exclude=self.exclude)
		self.tree = ExpandedTree(
			frame,
			GuiConfig.LSBLK_NAME_WIDTH * self.root.font_size,
			int(self.root.root_height / (3*self.root.font_size)),
			text = 'name',
			columns = { name: width * self.root.font_size for name, width in GuiConfig.LSBLK_COLUMNS}
			#columns = GuiConfig.LSBLK_COLUMNS_WIDTH
		)
		for path, details in LinUtils.lsblk(physical=self.physical, exclude=self.exclude).items():
			values = (
				details['type'],
				details['size'],
				StringUtils.str(details['label']),
				StringUtils.str(details['vendor']),
				StringUtils.str(details['model']),
				StringUtils.str(details['rev']),
				StringUtils.join(details['mountpoints'], delimiter=', ')
			)
			self.tree.insert(details['parent'], 'end', text=path, values=values, iid=path, open=True)
		self.tree.bind("<Double-1>", self._choose)

	def _choose(self, event):
		'''Run on double click'''
		item = self.tree.identify('item', event.x, event.y)
		self.button.set(self.tree.item(item)['text'])
		self.quit()

	def _refresh(self):
		'''Destroy and reopen Target Window'''
		self.main_frame.destroy()
		self._main_frame()
