#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'WmiMount'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-11'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Mount WMI Images'

from win32com.shell.shell import IsUserAnAdmin
from pathlib import Path
from functools import partial
from subprocess import Popen
from tkinter import Tk, PhotoImage
from tkinter.ttk import Frame, LabelFrame, Label, Button, Separator
from tkinter.messagebox import askyesno, showerror, showwarning
from tkinter.filedialog import askdirectory, askopenfilename
from lib.dism import GetImageInfo, GetMountedImageInfo, MountImage, UnmountImage

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	DESCR_WIDTH = -80

	def __init__(self, icon_base64):
		'Define the main window'
		super().__init__()
		self.title(f'{__app_name__} {__version__}')
		self.resizable(0, 0)
		self.iconphoto(False, PhotoImage(data = icon_base64))
		self.cwd = Path.cwd()
		if not any(self.cwd.glob('*.wim')):
			showwarning(
				f'{__app_name__}: Error',
				f'{self.cwd}\n\nDid not find files in Windows Imaging Format (WMI) '
			)
			filename = askopenfilename(
				title = 'Select one image file (WMI)',
				filetypes=[('Image files', '*.wim'), ('All files', '*.*')]
			)
			if not filename:
				self.cwd = None
				return
			self.cwd = Path(filename).parent
		self.mk_main_frame(self)

	def mk_main_frame(self, parent):
		self.main_frame = Frame(parent)
		self.main_frame.pack(padx=self.PAD, pady=self.PAD, fill='both', expand=True)
		dir_frame = LabelFrame(self.main_frame, text=self.cwd)
		dir_frame.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		Separator(dir_frame).pack(
			padx=self.PAD, pady=self.PAD, fill='both', expand=True)
		self.file_paths = [file_path	# paths of al image files as list
			for file_path in self.cwd.glob('*.wim')
			if file_path.is_file()
		]
		if not self.file_paths:
			showerror(f'{__app_name__}: Error', f'Did not find image files in\n{self.cwd}')
			self.destroy()
		mounted = {(Path(image['path']), image['index']): image['mnt']
			for image in GetMountedImageInfo().decode()
		}
		for file_path in self.file_paths:
			file_frame = Frame(dir_frame)
			file_frame.pack(padx=(4*self.PAD, self.PAD), fill='both', expand=True)
			Label(file_frame, text=file_path.name).pack(side='left')
			for image_info in GetImageInfo(file_path).decode():
				image_frame = LabelFrame(dir_frame, text=image_info['name'])
				image_frame.pack(
					padx=(8*self.PAD, self.PAD), fill='both', expand=True)
				frame = Frame(image_frame)
				frame.pack(fill='both', expand=True)
				Label(frame,
					text = image_info['descr'],
					width = self.DESCR_WIDTH,
					anchor = 'w'
				).pack(padx=self.PAD, side='left')
				Label(frame, text=image_info['size']).pack(
					padx=self.PAD, side='right')
				frame = Frame(image_frame)
				frame.pack(fill='both', expand=True)
				image = (file_path, image_info['index'])
				if image in mounted:
					path = mounted[image]
					Button(frame,
						text= 'Unmount',
						command = partial(self.unmount, path)
					).pack(padx=self.PAD, side='left')
					Label(frame, text=path).pack(
						padx=self.PAD, fill='both', expand=True)
				else:
					Button(frame,
						text = 'Mount',
						command = partial(self.mount, file_path, image_info['index'])
					).pack(padx=self.PAD, side='left')
			Separator(dir_frame).pack(
				padx=self.PAD, pady=self.PAD, fill='both', expand=True)
		frame = Frame(self.main_frame)
		frame.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		Button(frame, text= 'Refresh', command = self.refresh).pack(
			padx=self.PAD, pady=self.PAD, side='left')
		Button(frame, text="Quit", command=self.destroy).pack(
			padx=self.PAD, pady=self.PAD, side='right')

	def refresh(self):
		self.main_frame.destroy()
		self.mk_main_frame(self)

	def ask_warning(self, msg):
		return askyesno(f'{__app_name__}: Warning', msg, icon='warning')

	def check_error(self, proc):
		proc.read_all()
		if proc.stderr_str:
			showerror(f'{__app_name__}: Error', proc.stderr_str)
			return False
		return True

	def askdirectory(self):
		return askdirectory(title='Select directory to mount image', mustexist=False)

	def mount(self, file_path, image_index):
		mnt_dir = self.cwd / f'{file_path.stem}_{image_index}_mnt'
		if askyesno(self.cwd,
			f'Default destination:\n{mnt_dir}\n\nMount image to this directory?'
		):
			if mnt_dir.exists() and any(mnt_dir.iterdir()):
				if not self.ask_warning(
					f'{mnt_dir}\nis not an empty directory\n\nSelect other mount point?'
				):
					return
				mnt_dir = self.askdirectory()
		else:
			mnt_dir = self.askdirectory()
		if not mnt_dir:
			return
		mnt_dir = Path(mnt_dir)
		mnt_dir.mkdir(exist_ok=True)
		proc = MountImage(file_path, image_index, mnt_dir)
		if self.check_error(proc):
			Popen(['explorer', f'{mnt_dir}'])
			self.refresh()

	def unmount(self, path):
		if self.ask_warning(f'{path}\n\nDismount?'):
			proc = UnmountImage(path)
			if self.check_error(proc):
				self.refresh()

if __name__ == '__main__':  # start here
	if not IsUserAnAdmin():
		showerror(f'{__app_name__}: Error', 'Administrator privileges are reqired')
	else:
		gui = Gui('''
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
YII=''')
		if gui.cwd:
			gui.mainloop()
		else:
			showerror(f'{__app_name__}: Error', 'No image files (*.wim*) to wirk with')