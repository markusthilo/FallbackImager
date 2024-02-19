#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'WimMount'
__author__ = 'Markus Thilo'
__version__ = '0.4.0_2024-02-19'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Mount WIM Images, GUI to use with DismImager
'''

from sys import executable as __executable__
from win32com.shell.shell import IsUserAnAdmin
from pathlib import Path
from functools import partial
from subprocess import Popen
from tkinter import Tk, PhotoImage
from tkinter.ttk import Frame, LabelFrame, Label, Button, Separator
from tkinter.messagebox import askyesno, showerror, showwarning
from tkinter.filedialog import askdirectory, askopenfilename
from lib.winutils import WinUtils, OpenProc

if Path(__executable__).stem == __app_name__:
	__parent_path__ = Path(__executable__).parent
else:
	__parent_path__ = Path(__file__).parent

class Dism:
	'''Use Dism'''

	def __init__(self):
		'''Init subprocess for Dism without showing a terminal window'''
		self.dism_path = WinUtils.find_exe('dism.exe', __parent_path__,
		Path(__parent_path__/'DISM'),
		Path(__parent_path__/'bin'/'DISM'),
		Path('C:\\Program Files (x86)\\Windows Kits\\10\\Assessment and Deployment Kit\\Deployment Tools\\amd64\\DISM'))

	def get_mountedimageinfo(self):
		'''Dism  /Get-MountedImageInfo'''
		proc = OpenProc(f'{self.dism_path} /Get-MountedImageInfo')
		return proc.grep_stdout('Imageindex:',
			(-2, 'mnt'),
			(-1, 'path'),
			(0, 'index')
		)

	def get_imageinfo(self, image):
		'''Dism /Get-ImageInfo /ImageFile:$image'''
		proc = OpenProc(f'{self.dism_path} /Get-ImageInfo /ImageFile:"{image}"')
		return proc.grep_stdout('Index:',
			(0, 'index'),
			(1, 'name' ),
			(2, 'descr'),
			(3, 'size')
		)

	def mount_image(self, image, index, mnt):
		'''Dism /Mount-Image /ImageFile:$image /index:$i /MountDir:$mnt /ReadOnly'''
		proc = OpenProc(f'{self.dism_path} /Mount-Image /ImageFile:"{image}" /index:{index} /MountDir:{mnt} /ReadOnly')
		proc.wait()

	def unmount_image(self, mnt):
		'''Dism /Unmount-Image /MountDir:$mnt /discard'''
		proc = OpenProc(f'{self.dism_path} /Unmount-Image /MountDir:{mnt} /discard')
		proc.wait()

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	DESCR_WIDTH = -80

	def __init__(self, cwd, dism, icon_base64):
		'Open application window'
		self.dism = dism
		self.cwd = cwd
		super().__init__()
		self.title(f'{__app_name__} {__version__}')
		self.resizable(0, 0)
		self.iconphoto(False, PhotoImage(data = icon_base64))
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
			for image in self.dism.get_mountedimageinfo()
		}
		for file_path in self.file_paths:
			file_frame = Frame(dir_frame)
			file_frame.pack(padx=(4*self.PAD, self.PAD), fill='both', expand=True)
			Label(file_frame, text=file_path.name).pack(side='left')
			for image_info in self.dism.get_imageinfo(file_path):
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
		self.dism.mount_image(file_path, image_index, mnt_dir)
		self.refresh()

	def unmount(self, path):
		if self.ask_warning(f'{path}\n\nDismount?'):
			self.dism.unmount_image(path)
			self.refresh()

if __name__ == '__main__':  # start here
	if not IsUserAnAdmin():
		showerror(f'{__app_name__}: Error', 'Administrator privileges are reqired')
		exit()
	dism = Dism()
	if not dism.dism_path:
		showerror(f'{__app_name__}: Error', 'Unable to find dism.exe')
		exit()
	cwd = __parent_path__
	if not any(cwd.glob('*.wim')):
		showwarning(
			f'{__app_name__}: Error',
			f'{cwd}\n\nDid not find files in Windows Imaging Format (.wim) '
		)
		filename = askopenfilename(
			title = 'Select one image file (.wim)',
			filetypes=[('Image files', '*.wim'), ('All files', '*.*')]
		)
		if not filename:
			showerror(f'{__app_name__}: Error', 'No image files (*.wim*) to wirk with')
			exit()
		cwd = Path(filename).parent
	Gui(cwd, dism, '''
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
YII=''').mainloop()
