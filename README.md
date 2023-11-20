# FallbackImager

This is a modular utility for forensic work as a complement or fallback to the commercial and/or established tools. The modules write log files into given output directories, calculate hashes and/or lists of copied files etc. Multiple jobs can be generated and executed sequentially.

In this testing state only Windows (10/11) is supported.

This is work in progress.

## Installation

### Out of the box
The easiest way is to download the latest release and unpack the Zip anywhere. To use the compiled executables no Python or other dependencies are needed.

### Python
To use the python sources you need Python (3.11 or newer), the cloned git and the libraries *pycdlib*, *pyinstaller*, *pywin32* and *WMI*. You might want to use
```
$ pip install -r requirements.txt
```
to install them. The scripts *make-FallbackImager-exe.py*, *make-WimMount-exe.py* and *make-win-cli-apps-exe.py* uses *PyInstaller* to generate the executables if needed.

### C
To compile zerod.c you can use MSYS2, install and run MinGW-w64:
```
$ pacman -Syu
$ pacman -S mingw-w64-ucrt-x86_64-gcc
$ gcc -o bin/zerod.exe zerod.c
```

### 3rd party tools
You need a (sub-)directory *bin* with *mkisofs.exe* and *oscdimg.exe*. This folder is also the home for *WimMount.exe* and *zerod.exe*.

## Usage of the GUI

### Start

When used without admin privileges some features are not available.
Use the Python file with
```
$ python FallbackImager
```
or launch the executable (*FallbackImager.exe*).

### Tabs
Each module is represented by a tab in the upper part of the window.

Most modules have a button and field "Source" to select the source for the operation (e.g. directory or logical drive). Fields can be edited directly. In most cases the buttons let you choose a folder or file.

The modules need a "Destination" (or "Logging") to be set. "Filename" sets the name base part for generated files. The related button gives a default proposal in most modules (sometimes dependent on the source).

### Add job

When the usage of a module is defined in the tab above, a command can be added to the task list ("Jobs"). It is possible to edit the command directly or to write one completely from scratch. A command has to end with a semicolon. The last entry can be removed withe button "Remove last" on the right.

### Start jobs

The execution job after job is started with the button "Start jobs" on the left above the info field. The jobs will show infos and progress.

## Modules

### MkIsoImager
This tool generates an ISO file (UDF file system) using *mkisofs.exe*. It will log files that cannot be handled properly. The location of the executable can be set in "Configuration".

### OscdImager
The module uses *oscdimg.exe* (from the Windows ADK Package) to generate an ISO file (UDF file system).

### IsoVerify
This module is used by ISO generating modules to compare the UDF structure to the source file structure. Therefor it uses the *pycdlib* library. It can also be used to compare an existing image to a local file structure.

It is possible to skip paths using a whitelist or a blacklist. The patterns have to be given as regular expressions (Python/*re* syntax), one per line in a text file. Paths are handles in the POSIX format (no Windowish backslashes). When a local path matches to one line in the whitelist, the verification of this path is skipped. When a blicklist is given, the comparison is skipped if there is no match in the list of regular expressions. You can only use whitelist or blacklist at a time.

### DismImager
This module is only availible with Admin privileges.  It generates an image in the WIM format using DISM/*dism.exe*. The CLI tool is built into Windows. You can either generate and verify a WMI image or just verify an existing. When "Copy WimMount.exe to destination directory" a little GUI to mount and dismount is copied from *bin* to the destination. *WimMount.exe* needs to be run as admin.

### ZipImager
Using the Python library *zipfile* this module generates an ZIP archive from a source file structure.

### Sqlite
Work with Sqlite/SQL.

### AxChecker
Checking and comparing AXIOM case files, e.g. to X-Ways TSV lists

### HdZero
Wipe physical drives (Admin privileges required, Win only)

## Additional tool:

### WimMount

GUI for Dism to mount and unmount WIM images (Admin privileges required, Win only)


Respect GPL-3.
Use on your own risk.
This is not a commercial tool with an army of developers and a department for quality control behind it.
