#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .hashes import FileHash
from .guilabeling import ZipImagerLabels
from .guielements import NotebookFrame, SourceDirSelector, GridSeparator
from .guielements import GridLabel, OutDirSelector, FilenameSelector
from .guielements import AddJobButton, MissingEntry, Checker

class ZipImagerGui(ZipImagerLabels):
	'''Notebook page for ZipImager = BasicImagerTab'''

	MODULE = 'ZipImager'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		GridLabel(frame, self.SOURCE)
		self.source = SourceDirSelector(
			frame,
			self.root.settings.init_stringvar('Source'),
			tip = self.TIP_SOURCE
		)
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(
			frame,
			self.root.settings.init_stringvar('OutDir'),
			tip = self.TIP_OUTDIR
		)
		self.filename = FilenameSelector(
			frame,
			'{now}_zipimager',
			self.root.settings.init_stringvar('Filename')
		)
		GridSeparator(frame)
		GridLabel(frame, self.CALCULATE_HASHES)
		self.calc_hashes = [
			(alg, Checker(
				frame,
				self.root.settings.init_boolvar(alg.upper()),
				f'{alg}       ',
				tip = f'{self.TIP_HASHES} {alg}',
				column = (i%8)*2 + 3,
				incrow = i%8 == 7
			))
			for i, alg in enumerate(FileHash.get_algorithms())
		]
		AddJobButton(frame, 'ZipImager', self._add_job)

	def _add_job(self):
		'''Generate command line'''
		source = self.source.get()
		outdir = self.outdir.get()
		filename = self.filename.get()
		if not source:
			MissingEntry(self.SOURCE_REQUIRED)
			return
		if not outdir:
			MissingEntry(self.OUTDIR_REQUIRED)
			return
		cmd = f'zipimager --outdir "{outdir}"'
		if filename:
			cmd += f' --filename "{filename}"'
		hash_algs = [alg for alg, var in self.calc_hashes if var.get()]
		if hash_algs:
			cmd += f' --algorithms {",".join(hash_algs)}'
		else:
			cmd += ' --algorithms none'
		cmd += f' "{source}"'
		self.root.append_job(cmd)
