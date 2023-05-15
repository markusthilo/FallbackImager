#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI plugin for Oscdimg'

from tkinter import StringVar, BooleanVar
from tkinter.ttk import Frame, LabelFrame, Label, Button, Entry, Radiobutton
from tkinter.messagebox import askquestion, showwarning, showerror
from tkinter.filedialog import askopenfilename, askdirectory

class OscdimgGui:
	'''GUI plugin for Oscdimg'''

	CMD = 'oscdimager'

	def __init__(self, root):
		'''Notebook page'''
		self.settings = root.settings
		self.settings.init_section(self.CMD)
		self.frame = root.ExpandedFrame(root.notebook)
		root.notebook.add(self.frame, text=f' {self.CMD} ')
		root.OutdirButton(self.frame, self.settings)
		
		'''
		Entry(frame, textvariable=self.settings.raw('rootdir'), width=self.E_WIDTH).grid(
			row=0, column=2, sticky=W, padx=self.PAD, pady=(self.PAD, 0))
		self.settings.init_stringvar('destdir')
		Button(frame,
			text = 'Destination:',
			command = lambda: self.settings.raw('destdir').set(
				askdirectory(
					title = 'Select destination directory',
					mustexist = False
				)
			)
		).grid(row=1, column=1, sticky=W, padx=self.PAD)
		Entry(frame, textvariable= self.settings.raw('destdir'), width=self.E_WIDTH).grid(
			row=1, column=2, sticky=W, padx=self.PAD)
		self.settings.init_stringvar('destfname')
		Label(frame, text='File name (no ext.)').grid(
			row=2, column=0, columnspan=2, sticky='w', padx=self.PAD)
		Entry(frame, textvariable=self.settings.raw('destfname'), width=self.E_WIDTH).grid(
			row=2, column=2, sticky='w', padx=self.PAD)
		self.settings.init_stringvar('use_list', default='none')
		Radiobutton(frame, value='none', variable=self.settings.raw('use_list')).grid(
			row=3, column=0, sticky='w', padx=self.PAD)
		Label(frame, text='No filter').grid(row=3, column=1, padx=self.PAD)
		Radiobutton(frame, value='blacklist', variable=self.settings.raw('use_list')).grid(
			row=4, column=0, sticky='w', padx=self.PAD)
		self.settings.init_stringvar('blacklist')
		Button(frame,
			text = 'Blacklist:',
			command = lambda: self.settings.raw('blacklist').set(
				askopenfilename(
					title = 'Select blacklist',
					filetypes = (
						("Text files","*.txt"),
						("All files","*.*")
					)
				)
			)
		).grid(row=4, column=1, sticky=W, padx=self.PAD)
		Entry(frame, textvariable=self.settings.raw('blacklist'), width=self.E_WIDTH).grid(
			row=4, column=2, sticky=W, padx=self.PAD)
		Radiobutton(frame, value='whitelist', variable=self.settings.raw('use_list')).grid(
			row=5, column=0, sticky='w', padx=self.PAD)
		self.settings.init_stringvar('whitelist')
		Button(frame,
			text = 'Whitelist:',
			command = lambda: self.settings.raw('whitelist').set(
				askopenfilename(
					title = 'Select whitelist',
					filetypes = (
						("Text files","*.txt"),
						("All files","*.*")
					)
				)
			)
		).grid(row=5, column=1, sticky=W, padx=self.PAD)
		Entry(frame, textvariable=self.settings.raw('whitelist'), width=self.E_WIDTH).grid(
			row=5, column=2, sticky=W, padx=self.PAD)
		labelframe = LabelFrame(frame, text='Job')
		labelframe.grid(row=6, column=0, columnspan=2, sticky=W, padx=self.PAD, pady=self.PAD)
		Button(labelframe, text='Append', command=self.append_job_pycdlib).pack(
			padx=self.PAD, pady=self.PAD)
		self.settings.init_stringvar('image_type', default='udf')
		labelframe = LabelFrame(frame, text='Output image format')
		labelframe.grid(row=6, column=2, sticky=W, padx=self.PAD, pady=self.PAD)
		Radiobutton(labelframe, 
			text = 'UDF',
			value = 'udf',
			variable = self.settings.raw('image_type')
		).pack(side='left', padx=self.PAD)
		Radiobutton(labelframe,
			text = 'Joliet',
			value = 'joliet',
			variable = self.settings.raw('image_type')
		).pack(side='left', padx=self.PAD)
		'''
	
	def gen_cmd(self):
		'''Generate command line'''
		self.settings.section = 'oscimg'
		root = self.settings.get('root')
		outdir = self.settings.get('outdir')
		filename = self.settings.get('filename')
		blacklist = self.settings.get('blacklist')
		whitelist = self.settings.get('whitelist')
		
		if not rootdir or not destdir or not destfname:
			showerror(
				title = f'{self.app_name}/{self.settings.section}',
				message = 'Source, destination directory and destination filename (without extension) are requiered'
			)
			return
		cmd = self.settings.section
		use_list = self.settings.get('use_list')
		if use_list == 'blacklist':
			blacklist = self.settings.get('blacklist')
			if blacklist:
				cmd += f' -b {blacklist}'
		elif use_list == 'whitelist':
			whitelist = self.settings.get('whitelist')
			if whitelist:
				cmd += f' -w {whitelist}'
		if self.settings.get('image_type') == 'joliet':
			cmd += ' -j'
		cmd += f' -o {destdir} -f {destfname} {rootdir}\n'
		self.jobs.insert(END, f'{cmd}')
		self.jobs.yview(END)
