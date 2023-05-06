#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-05'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI for FallbackImager'

from pathlib import Path
from sys import executable
from configparser import ConfigParser
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from tkinter import Tk, StringVar, BooleanVar, PhotoImage, E, W, END, RIGHT
from tkinter.ttk import Frame, LabelFrame, Label, Button, Notebook, Entry, Radiobutton
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askquestion, showwarning, showerror
from tkinter.filedialog import askopenfilename, askdirectory
from lib.extpath import ExtPath
from fileimager import CLI as FileImagerCLI

class Config(ConfigParser):
	'''Handle config file'''

	DEFAULT = 'DEFAULT'

	def __init__(self, path=None):
		'''Set path to config file, default is app or script name with .conf'''
		try:
			self.path = Path(path)
		except TypeError:
			script_path = Path(__file__)
			exe_path =  Path(executable)
			if script_path.stem != exe_path.stem:
				path = script_path
			else:
				path = exe_path
			self.path = path.parent/f'{path.stem.lower()}.conf'
		self.set_section()
		super().__init__()
		self.read()

	def set_section(self, *args):
		'''Set section to read or write'''
		if len(args) == 1 and isinstance(args[0], str):
			self._section = args[0]
		elif len(args) == 0:
			self._section = self.DEFAULT
		else:
			raise KeyError(args)

	def get_section(self, *args):
		'''Get section'''
		if len(args) == 1 and isinstance(args[0], str):
			return args[0]
		elif len(args) == 0 or args == (None, ):
			return self._section

	def get(self, key, section=None):
		'Get string from config'
		try:
			return self[self.get_section(section)][key]
		except KeyError:
			return ''

	def put(self, key, value, section=None):
		'Put value to config'
		self[self.get_section(section)][key] = value

	def read(self):
		'''Read config file'''
		super().read(self.path)

	def write(self):
		'''Write config file'''
		with open(self.path, 'w') as fh:
			super().write(fh)

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
		self.fileimager = FileImagerCLI(exit_on_error=False)

	def run(self):
		'''Start the work'''
		for job in self.jobs:
			cmd = ' '.join(job)
			self.echo(f'Processing >{cmd}<...')
			if job[0].lower() == 'fileimager':
				self.debug(f'job: {job}')
				self.fileimager.parse(job[1:])
				self.fileimager.run(echo=self.debug)
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
		self.config = Config()
		self.settings = dict()
		super().__init__()
		self.title('FallbackImager')
		self.resizable(0, 0)
		self.iconphoto(False, PhotoImage(data = icon_base64))
		self.mainframe = Frame(self)
		self.mainframe.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.notebook = Notebook()
		self.notebook.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		### File Imager ###
		section = 'FILEIMAGER'
		self.config.set_section = section
		self.settings[section] = dict()
		self.frame_fileimager = Frame(self.notebook)
		self.frame_fileimager.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.notebook.add(self.frame_fileimager, text=' File Imager ')
		frame = Frame(self.frame_fileimager)
		frame.pack(fill='both', expand=True)
		self.settings[section]['rootdir'] = StringVar(value=self.config.get('rootdir'))
		Button(frame,
			text = 'Source:',
			command = lambda: self.settings[section]['rootdir'].set(
				askdirectory(
					title = 'Select source',
					mustexist = False
				)
			)
		).grid(row=0, column=1, sticky=W, padx=self.PAD, pady=(self.PAD, 0))
		Entry(frame, textvariable=self.settings[section]['rootdir'], width=self.E_WIDTH).grid(
			row=0, column=2, sticky=W, padx=self.PAD, pady=(self.PAD, 0))
		self.settings[section]['destdir'] = StringVar(value=self.config.get('destdir'))
		Button(frame,
			text = 'Destination:',
			command = lambda: self.settings[section]['destdir'].set(
				askdirectory(
					title = 'Select destination directory',
					mustexist = False
				)
			)
		).grid(row=1, column=1, sticky=W, padx=self.PAD)
		Entry(frame, textvariable=self.settings[section]['destdir'], width=self.E_WIDTH).grid(
			row=1, column=2, sticky=W, padx=self.PAD)
		self.settings[section]['destfname'] = StringVar(value=self.config.get('destfname'))
		Label(frame, text='File name (no ext.)').grid(
			row=2, column=0, columnspan=2, sticky='w', padx=self.PAD)
		Entry(frame, textvariable=self.settings[section]['destfname'], width=self.E_WIDTH).grid(
			row=2, column=2, sticky='w', padx=self.PAD)
		value = self.config.get('use_list')
		if not value:
			value = 'none'
		self.settings[section]['use_list'] = StringVar(value=value)
		Radiobutton(frame, value='none', variable=self.settings[section]['use_list']).grid(
			row=3, column=0, sticky='w', padx=self.PAD)
		Label(frame, text='No filter').grid(row=3, column=1, padx=self.PAD)
		Radiobutton(frame, value='blacklist', variable=self.settings[section]['use_list']).grid(
			row=4, column=0, sticky='w', padx=self.PAD)
		self.settings[section]['blacklist'] = StringVar(value=self.config.get('blacklist'))
		Button(frame,
			text = 'Blacklist:',
			command = lambda: self.settings[section]['blacklist'].set(
				askopenfilename(
					title = 'Select blacklist',
					filetypes = (
						("Text files","*.txt"),
						("All files","*.*")
					)
				)
			)
		).grid(row=4, column=1, sticky=W, padx=self.PAD)
		Entry(frame, textvariable=self.settings[section]['blacklist'], width=self.E_WIDTH).grid(
			row=4, column=2, sticky=W, padx=self.PAD)
		Radiobutton(frame, value='whitelist', variable=self.settings[section]['use_list']).grid(
			row=5, column=0, sticky='w', padx=self.PAD)
		self.settings[section]['whitelist'] = StringVar(value=self.config.get('whitelist'))
		Button(frame,
			text = 'Whitelist:',
			command = lambda: self.settings[section]['whitelist'].set(
				askopenfilename(
					title = 'Select whitelist',
					filetypes = (
						("Text files","*.txt"),
						("All files","*.*")
					)
				)
			)
		).grid(row=5, column=1, sticky=W, padx=self.PAD)
		Entry(frame, textvariable=self.settings[section]['whitelist'], width=self.E_WIDTH).grid(
			row=5, column=2, sticky=W, padx=self.PAD)
		labelframe = LabelFrame(frame, text='Job')
		labelframe.grid(row=6, column=0, columnspan=2, sticky=W, padx=self.PAD, pady=self.PAD)
		Button(labelframe,
			text = 'Append',
			command = lambda: self.append_job('fileimage')
			).pack(padx=self.PAD, pady=self.PAD)
		value = self.config.get('image_type')
		if not value:
			value = 'udf'
		self.settings[section]['image_type'] = StringVar(value=value)
		labelframe = LabelFrame(frame, text='Output image format')
		labelframe.grid(row=6, column=2, sticky=W, padx=self.PAD, pady=self.PAD)
		Radiobutton(labelframe,
			text = 'UDF',
			value = 'udf',
			variable = self.settings[section]['image_type']
		).pack(side='left', padx=self.PAD)
		Radiobutton(labelframe,
			text = 'Joliet',
			value = 'joliet',
			variable = self.settings[section]['image_type']
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
		self.jobs.insert(END, 'fileimager -v -f test_joliet -j -b blacklist.txt C:\\Users\\THI\\Documents\\23-0160-0')
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
		self.quit_button = Button(frame, text="Quit", command=self.destroy)
		self.quit_button.pack(padx=self.PAD, pady=self.PAD, side='right')

	def append_job(self, job):
		'''Append job to job list'''
		self.jobs.insert(END, f'{job}\n')
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
