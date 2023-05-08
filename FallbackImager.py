#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-07'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI for FallbackImager'

from pathlib import Path
from sys import executable
from json import load, dump
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from tkinter import Tk, StringVar, BooleanVar, PhotoImage, E, W, END, RIGHT
from tkinter.ttk import Frame, LabelFrame, Label, Button, Notebook, Entry, Radiobutton
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askquestion, showwarning, showerror
from tkinter.filedialog import askopenfilename, askdirectory
from lib.extpath import ExtPath
from pycdlibimager import PyCdlibCli

class Settings(dict):
	'''Handle settings'''

	def __init__(self, path):
		'''Set path to JSON config file, default is app or script name with .json'''
		self.path = path
		try:
			with self.path.open() as fh:
				loaded = load(fh)
		except FileNotFoundError:
			loaded = dict()
		self.update(loaded)

	def init_section(self, section):
		'''Open a section in settings'''
		self.section = section
		if not section in self:
			self[section] = dict()

	def get(self, key, section=None):
		'Get value'
		if not section:
			section = self.section
		try:
			value = self[section][key]
		except KeyError:
			return ''
		try:
			return value.get()
		except AttributeError:
			return value

	def init_stringvar(self, key, default=None, section=None):
		'''Generate StringVar for one setting'''
		value = self.get(key, section=section)
		if not value and default:
			self[self.section][key] = StringVar(value=default)
		else:
			self[self.section][key] = StringVar(value=value)

	def raw(self, key, section=None):
		'''Get value as it is'''
		if not section:
			section = self.section
		return self[self.section][key]

	def decoded(self):
		'''Decode settings using get method'''
		dec_settings = dict()
		for section in self:
			dec_section = dict()
			for key in self[section]:
				value = self.get(key, section=section)
				if value:
					dec_section[key] = value
			if dec_section != dict():
				dec_settings[section] = dec_section
		return dec_settings

	def write(self):
		'''Write config file'''
		with self.path.open('w') as fh:
			dump(self.decoded(), fh)

class Worker(Thread):
	'''Work jab after job'''

	def __init__(self, jobs, echo=print, debug=False):
		'''Give job list and info handler to Worker object'''
		self.jobs = jobs
		self.echo = echo
		if debug:
			self.debug = print
		else:
			self.debug = FileImagerCLI.no_echo
		self.imager = PyCdlibCli(exit_on_error=False)

	def run(self):
		'''Start the work'''
		for job in self.jobs:
			cmd = ' '.join(job)
			self.echo(f'Processing >{cmd}<...')
			if job[0].lower() == 'pycdlib':
				self.debug(f'job: {job}')
				self.imager.parse(job[1:])
				self.imager.run(echo=self.debug)
				self.echo('Job done.')
			else:
				self.echo(f'Unknown command >{job[0]}<')
		self.echo('All done.')

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	T_WIDTH = 80
	T_HEIGHT = 8
	E_WIDTH = 72

	def __init__(self, icon_base64):
		'Define the main window'
		script_path = Path(__file__)
		exe_path =  Path(executable)
		if script_path.stem != exe_path.stem:
			self.app_path = script_path
		else:
			self.app_path = exe_path
		self.app_name = self.app_path.stem
		self.app_full_name = f'{self.app_name} v{__version__}'
		super().__init__()
		self.title(self.app_full_name)
		self.resizable(0, 0)
		self.iconphoto(False, PhotoImage(data = icon_base64))
		self.mainframe = Frame(self)
		self.mainframe.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.notebook = Notebook()
		self.notebook.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.settings = Settings(self.app_path.parent/f'{self.app_path.stem.lower()}.json')
		### PyCdlib ###
		self.settings.init_section('pycdlib')
		self.frame_fileimager = Frame(self.notebook)
		self.frame_fileimager.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.notebook.add(self.frame_fileimager, text=' PyCdlib ')
		frame = Frame(self.frame_fileimager)
		frame.pack(fill='both', expand=True)
		self.settings.init_stringvar('rootdir')
		Button(frame,
			text = 'Source:',
			command = lambda: self.settings.raw('rootdir').set(
				askdirectory(
					title = 'Select source',
					mustexist = False
				)
			)
		).grid(row=0, column=1, sticky=W, padx=self.PAD, pady=(self.PAD, 0))
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
		### Jobs ###
		labelframe = LabelFrame(self, text='Jobs')
		labelframe.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.jobs = ScrolledText(labelframe,
			padx = self.PAD,
			pady = self.PAD,
			width = self.T_WIDTH,
			height = self.T_HEIGHT
		)
		self.jobs.pack(fill='both', padx=self.PAD, pady=self.PAD, side='left')
		### Infos ###
		labelframe = LabelFrame(self, text='Infos')
		labelframe.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.infos = ScrolledText(labelframe,
			padx = self.PAD,
			pady = self.PAD,
			width = self.T_WIDTH,
			height = self.T_HEIGHT
		)
		self.infos.bind("<Key>", lambda e: "break")
		self.infos.insert(END, 'Infos will be here')
		self.infos.pack(fill='both', padx=self.PAD, pady=self.PAD, side='left')
		### Quit button ###
		frame = Frame(self)
		frame.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.start_button = Button(frame, text= 'Start jobs', command = self.start_jobs)
		self.start_button.pack(padx=self.PAD, pady=self.PAD,side='left')
		self.quit_button = Button(frame, text="Quit", command=self.quit_app)
		self.quit_button.pack(padx=self.PAD, pady=self.PAD, side='right')

	def	quit_app(self):
		'''Store configuration and quit application'''
		self.settings.write()
		self.destroy()

	def append_job_pycdlib(self):
		'''Append job for fileimager to job list'''
		self.settings.section = 'pycdlib'
		rootdir = self.settings.get('rootdir')
		destdir = self.settings.get('destdir')
		destfname = self.settings.get('destfname')
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

	def start_jobs(self):
		'''Start working job list'''
		self.infos.config(state='normal')
		self.infos.delete('1.0', END)
		self.infos.insert(END, 'Starting jobs...\n')
		self.infos.configure(state='disabled')
		self.jobs.configure(state='disabled')
		work = Worker(
			(job.split() for job in self.jobs.get('1.0', END).split('\n') if job != ''),
			echo = self.append_info,
			debug = True
		)
		work.run()

	def append_info(self, msg):
		'''Append message in info box'''
		self.infos.configure(state='normal')
		self.infos.insert(END, f'{msg}\n')
		self.infos.configure(state='disabled')
		self.infos.yview(END)

if __name__ == '__main__':  # start here
	Gui('''
iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAMAAADVRocKAAAAw1BMVEUAAAAAAACCgoJCQkLCwsIi
IiKhoaFhYWHi4uISEhKSkpJSUlLR0dExMTGysrJycnLx8fEJCQmJiYlKSkrJyckqKiqpqalpaWnq
6uoZGRmZmZlaWlrZ2dk5OTm6urp6enr6+voFBQWGhoZFRUXFxcUlJSWlpaVmZmbl5eUVFRWVlZVV
VVXW1tY1NTW2trZ2dnb19fUNDQ2Ojo5NTU3Nzc0uLi6tra1ubm7u7u4eHh6dnZ1dXV3e3t4+Pj6+
vr5+fn7///8PfNfhAAAF4UlEQVRo3u2ay26rOhSGEdeJZZAFNtcBYgJCgMFighDk/Z/qLLPbBJLd
lCQ+o3M8bFV/rKv/ZVe7/MtL+y8COOf/CsCbU+QveBoIIcPUplwpwEM4JvradYw5sBjrCJ0VAuaW
rC5sndSiKAyjKETN1nME7dz+erdtbmTNuK0mE4nehooAnh93Ti3k7lYUVVUVRVYwGklscmUAlsj9
g6jq81zL876vosBgsakGwBHtJGC0qlz7WnlfWQWbTDUxKH0c664xWr12W3llGc7gq8miEGoALSSo
tANBegkprORyivI9oY/Gwp1mha0iXPc+0rQqyBLdVNmLzIOPpAmia5U2O6YdozAWLFYKiPNHH4Uq
AcMR0FuN6HyFAJ4cATnkkWMrBLTHPP3jo3VWBpid6Lj/5iOXKis0MlZ3Fmw+IqEaQBpnQdRr9z4y
ktVXAYCWuhqNdW9Cb2Wiw28C9uqBlymc+DZx7mzoo0Y8rbVnAM/7W6BpdhcEwyH8LQAvw7/+4dzd
B0Gf3wJ45Q/ZMdfHINQdes+CHw1Pg2MQ3EW1NqXHSmBYMcAjxyA8a0fviF/TvauEOlYB4NyDFc5t
99AthP4RgM/IN5cWU1iYxo722C2c+Zbb/Cng4feXdKHxMAxxPIC61odYF/cAaYL97T2M7/Skdude
m/r7+kWUgGJ312Gi1B6AQNYHwBaF7ehHE3wJLp8AQjro+mB+F9iM9aQwCuGsU+sjKe90QrpGe3RS
JmLTnGB+WAcaPrMAPtiFD8YIzChxV4CgDgLLSoYWpWixiU7iWM8enFQFTVFvk0k3LE9jgIaOJXJ1
A0kM2N0CQQ2KOg8SlozaTwt06pjBVJKwdQqfZxFdQanDpGFItW5Ffa+dWhvBEIlL0l/StIRZQ4Bn
to/vc+3s6qOgMSBYy6914BMwYfv6qtfOry0MiUv574VmElYbclh6DRBBJjE7PFPJSGfC2ALwAgD0
S+HQ8FyrmG1HyIGvegEApVBjfrYXcSoJwQsAKeQpP9/svDgpsjHKXzHgB/n1Qzf1IdDHme83A4r2
pXbtEcjV4GyY+yxoEvO184AycNJJQk8XBiF+DbDIlnEYvbds/2tUoHqpIfT0JQCibUvqgxiF4T6C
8ntgTDJm0CboS4Ay5XA6JEVzdVMfWePQUnbvtkBmJzKKH4Y17anqWpwt1PDRPbTL2twy+C65tgN/
AUCXvnHom0wS5A0O5MnXyT4c62OTLLEEoHdUBXJlqC0LWtm3cgjZocSd7UdvAy4pk32pycRtjMHW
3oTevPDFgMNmfQ9wMR1hwGG1U4f+uI9C36GUFqAM/i7iTwiv2BFCOLsU8cUeUK0obYWo2eC9CUCu
kzh79Ym6XRD6pg0906mdbnpbm8agZPatDMU3QJ9IJYeYw3641zkDMPV1JxZKn7Krixwc/jGSdTF/
GzDT6x0s9+01uR4UY/vldn9dB/TBrePtnhrpcE5cm8W1+/i2jdQMICGByr5G4Or1FHmqJpxWNLde
9H0E8FDdCGWK5taK2FfoucIHCix2WiAf5ufz7usATgGwq+I45Tycvc8AfHejELbuzkVaP04wmPjl
ZwAP+dcgeqa+B+QRszFe5g8tQAv6tiE0u4Mei4rBpu2HgMuchjtl3BwABgA+teDor6nZn/qRiCk2
Q4WAMs72h36UAMBXCAhbBq3iVgiRIBM2PWUAPredsa+0qHGJrdRF3Nd3zUheFrnDohIAXhpu7VRe
CdYrVgu4lMnVR70EuFQx4NLdAWzFgNn4Bsj5XgK42hjo32dmLsd7kIxUKSBd/+jtXI4LwZgJZ8Uf
AfjhATzE28hQfb2YykdZprefvR/wsJy/ToQZu3KuCiwpt+WbL0hetj5/DDzTrku/xW3bUnmXJB9l
QWw3WWZs90Od/suj7zldhKd40NeOOfV2lbTtLd/dVxK3Sp4aUzoNRO9c5iRJXSewOXw5bU00//pk
fTKLQh/bYIT8twF58Yf9pwf9m2nqlTMc8D6aw1fS+r3b9/8BKtc/NFcHINi4Q8kAAAAASUVORK5C
YII='''
	).mainloop()
