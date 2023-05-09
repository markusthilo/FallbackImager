#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-08'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Release'
__description__ = 'Mounter for WMI Images'

from pathlib import Path
from subprocess import Popen, PIPE, STARTUPINFO
from sys import executable
from tkinter import Tk, StringVar, BooleanVar, PhotoImage, E, W, END, RIGHT
from tkinter.ttk import Frame, LabelFrame, Label, Button, Notebook, Entry, Radiobutton
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askquestion, showwarning, showerror
from tkinter.filedialog import askopenfilename, askdirectory

class Powershell(Popen):
	'''Powershell via subprocess'''

	def __init__(self, cmd):
		'''Init subprocess without showing a terminal window'''
		super().__init__(
			['powershell', '-Command'] + cmd,
			startupinfo = STARTUPINFO(),
			stdout = PIPE,
			stderr = PIPE,
			universal_newlines = True
		)

	@staticmethod
	def get_clean(stream):
		'''Clean from blanks'''
		cleaned = list()
		for line in stream:
			line = line.strip()
			if line:
				cleaned.append(line)
		return cleaned

	@staticmethod
	def decode(stream, delimiter=':'):
		'''Decode to dict'''
		decoded = dict()
		for line in stream:
			try:
				key, value = line.split(delimiter, 1)
			except ValueError:
				continue
			key = key.strip()
			value = value.strip()
			if key in decoded:
				decoded[key].append(value)
			else:
				decoded[key] = [value]
		return decoded

	@staticmethod
	def grep(key, stream, delimiter=':'):
		'''Grep for keyword and give values as set'''
		return {
			line.split(delimiter, 1)[1].strip()
			for line in stream
			if line.startswith(key)
		}

class GetImageInfos(Powershell):
	'''Get-WindowsImage -ImagePath $imagepath'''

	def __init__(self, imagepath):
		super().__init__(['Get-WindowsImage', '-ImagePath', imagepath])
		self.stdout = self.get_clean(self.stdout)

	def decode(self):
		return super().decode(self.stdout)

class GetMounted(Powershell):
	'''Get-WindowsImage -Mounted'''

	def __init__(self):
		super().__init__(['Get-WindowsImage', '-Mounted'])
		self.stdout = self.get_clean(self.stdout)

	def imagepaths(self):
		return super().grep('ImagePath', self.stdout)

class MountImage(Powershell):
	'''Mount-WindowsImage -ImagePath $imagepath -Index $index -Path $path -ReadOnly'''

	def __init__(self, imagepath, path, index=1):
		super().__init__(['Mount-WindowsImage',
			'-ImagePath', imagepath,
			'-Index', f'{index}',
			'-Path', path,
			'-ReadOnly'
		])
		self.stdout = self.get_clean(self.stdout)

class DismountImage(Powershell):
	'''Dismount-WindowsImage -Path $path -Discard'''

	def __init__(self, path):
		super().__init__(['Dismount-WindowsImage', '-Path', path, '-Discard'])
		self.stdout = self.get_clean(self.stdout)

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
		self.mounted_imagepaths = GetMounted().imagepaths()
		
		print(self.mounted_imagepaths)
		
		self.mainframe = Frame(self)
		self.mainframe.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		for imagepath in self.app_path.parent.rglob('*.wim'):	# files
			if imagepath.is_file():
				
				print(imagepath.name)
				image_info = GetImageInfos(imagepath)
				print(image_info.decode())


if __name__ == '__main__':  # start here
	infos = GetImageInfos('C:\\Users\\THI\Documents\\test_destination\\test.wim')
	#print(infos.stdout)
	#print(infos.decode())
	#mounted = GetMounted()
	#print(mounted.stdout)
	#print(mounted.imagepaths())
	#exit()
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