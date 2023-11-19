# FallbackImager

This is a modular utility for forensic work as a complement or fallback to the commercial and/or established tools. The modules write log files into given output directories. Multiple jobs can be generated an will be executed sequentially.

In this testing state only Windows (10/11) is supported.

This is work in progress.

## Installation

### Out of the box
The easiest way is to download the latest release und unpack the Zip anywhere. To use the compiled executables no Python or othere dependencies are needed.

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
Evere module is represented by a tab in the upper part of the window.

Most modules have a button and field "Source" to select the source for the operation (e.g. directory or logical drive). Fields can be edited directly. In most cases the buttons let you choose a folder or file.

The modules hneed a "Destination" (or "Logging") to be set. "Filename" sets the name base part for generated files. The related button gives a default proposal in most modules (sometimes dependent on the source).

### Add job

When the usage of a module is defined in the tab above, a command can be added to the task list ("Jobs"). It is possible to edit the command directly ot to write one completly from scratch. A command has to end with a semicolon. The last entry can be removed withe button "Remove last" on the right.

### Start jobs

The execution job after job ist startet with the button "Start jobs" on the left obove the info field. The jobs will show infos and progress.

## Modules:

### MkIsoImager
This tool generates an ISO file (UDF file system) using *mkisofs.exe*. It will log files that cannot be handled properly. The location of the executable can be set in "Configuration".

### OscdImager
The modul uses *oscdimg.exe* (from the Windows ADK Package) to generate an ISO file (UDF file system).

### IsoVerify
Verifying/comparing ISO to a logical file structure (using PyCdlib)

### DismImager
Imaging a logical file structure as WIM (Admin privileges required, uses dism.exe, Win only)

### ZipImager
Imaging a logical file structure as ZIP file

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
