# FallbackImager
This is a modular utility for forensic work as a complement or fallback to the commercial and/or established tools. The modules write log files into given output directories, calculate hashes and/or lists of copied files etc. Multiple jobs can be generated and executed sequentially.

The tool is currently developed for Linux based OS and Windows (>=10). It is work in progress.

## Installation

### Linux

#### Python
To use the python sources you need Python (3.11 or newer). To use the GUI, tk is needed. The installation depends on your distro, e.g.:
```
$ sudo apt install python3 python3-tk
```
```
$ sudo pacman install python tk
```
```
$ sudo dnf install python3 python3-tkinter
```
```
$ sudo zypper install python3 python3-tk
```

#### C
Pre-compiled versions of the wipe tool zd are included in the releases, so on64-bit Intel CPUs / AMD64 there is no need to compile.

To compile the source *gcc* is needed. You might use my make script:
```
$ cd FallbackImager
$ ./make-bin.sh
```
This is also executed when running:
```
$ ./make-dist-lin.sh
```

#### libewf
Install *libewf* (https://github.com/libyal/libewf) from your distro repos using something like:
```
$ sudo apt install lib-ewf
```
```
$ sudo pacman install libewf
```
```
$ sudo dnf install libewf
```
```
$ sudo zypper install libewf
```
FallbackImager tries to locate *ewfacquire*, *ewfmount*, *ewfinfo* and *ewfverify* in the (sub-) folder *bin*. Alternatively it tries to find the binaries in usual system paths (e.g. */usr/bin*).

### Windows

#### Out of the box
The easiest way is to download the latest release and unpack the ZIP-file anywhere. To use the compiled executables no Python or other dependencies are needed. Of course, you still might need the Microsoft tools (see below).

#### Python
To use the python sources you need Python (3.11 or newer), the cloned git and the libraries *pyinstaller*, *pywin32* and *WMI*. You might want to use
```
$ pip install -r requirements.txt
```
to install them. The scripts *make-FallbackImager-exe.py*, *make-WimMount-exe.py* and *make-win-cli-apps-exe.py* use *PyInstaller* to generate the executables if needed.

#### C
To compile zd-win.c you can use e.g. ArchLinux in WSL with MinGW-w64:
```
$ pacman -Syu
$ pacman -S mingw-w64-ucrt-x86_64-gcc
$ cd FalbackImager
$ ./make-zd-win.sh
```
The executable will be in */dist-win/bin/*.

#### PyInstaller
Windows Defender Realtime Protection needs to be turned off to run:
```
$ python.exe make-exe.py
```
The executables will be in */dist-win/*.


#### Microsoft tools
DismImager should come with your Windows but some Editions might not include it ("Home"?).
For OscdImager you need to install the Windows Assessment and Deployment Kit (Windows ADK) which is freely available from https://learn.microsoft.com/en-us/windows-hardware/get-started/adk-install. It is possible to put the tools in the *bin* subdirectory or just leave them at *C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64*. Windows ADK also includes a version of DismImager.

## Usage of the GUI

### Start
On Windows the executable *fallbackimager.exe* can be lauched by double clicking.
When used without admin privileges most features are not available.
If you have Python istalled, you can also open a PowerShell (as Administartor), go to the FallbackImager directory
and run:
```
$ python.exe FallbackImager.py
```
On Linux based Systems run from the terminal:
```
$ ./fallbackimager.sh
```
Shure, you can run directly with *python* or *python3*:
```
$ python fallbackimager.py
```

### Tabs
Each module is represented by a tab in the upper part of the window.

Most modules have a button and field "Source" to select the source for the operation (e.g. directory or logical drive). Fields can be edited directly. In most cases the buttons let you choose a folder or file.

The modules need a "Destination" (or "Logging") to be set. "Filename" sets the name base part for generated files. The related button gives a default proposal in most modules (sometimes dependent on the source).

### Add job
When the usage of a module is defined in the tab above, a command can be added to the task list ("Jobs"). It is possible to edit the command directly or to write one completely from scratch. A command has to end with a semicolon. The last entry can be removed withe button "Remove last" on the right.

### Start jobs
The execution job after job is started with the button "Start jobs" on the left above the info field. The jobs will show infos and progress.

## Modules

### EwfImager
This is a conveniant interface for *ewfacquire* from libewf. This module is not available on Windows.

### EwfChecker
The module simply uses *ewfinfo*. *ewfexport* and *ewfewfverify* to check an EWF/E01 image file. It is used by EwfImager. This is not available on Windows.

### OscdImager
The module uses *oscdimg.exe* (from the Windows ADK Package) to generate an ISO file (UDF file system). Obviously this module is only available on Windows.

### DismImager
This module is only availible on Windows with Admin privileges. It generates an image in the WIM format using DISM/*dism.exe*. The CLI tool is built into Windows. You can either generate and verify a WIM image or just verify an existing. When "Copy WimMount.exe to destination directory" is selected the little GUI tool *WimMount.exe* is copied from *bin* to the destination. *WimMount.exe* needs to be run as Admin and can mount and dismount WIM image files.

### ZipImager
Using the Python library *zipfile* this module generates an ZIP archive from a source file structure. The process is robust to unreadable paths and a TSV path list is generated.

### HashedCopy
Copies files and verifies by md5 and sha256. Paths and hashes are stored as TSV.

### Sqlite
The Sqlite module uses the Python library *sqlite3*. It can show the structure of a *.db* file ("Dump schema") or dump the content as CSV/TSV ("Dump content"). In addition SQL code can be executed ("Execute SQL") by the library. An alternative method is implemented ("Alternative") that is designed to generate a *.db* file from a MySQL dump file in case *sqlite3* fails.

### Reporter
The tool parses a template and replaces "%jinsert{}{}" or "\jinsert{}{}" by values from a JSON file.
Example: reporter-example-template.txt

### AxChecker
As Magnet's AXIOM has proven to be unreliable in the past, this module compares the files in an AXIOM *Case.mfdb* to a file list (CSV/TSV e.g. created with X-Ways) or a local file structure. Only one partition or subtree of the case file can be compared at a time.

Hits are files, that are represented in the artifacts. Obviously this tool can only support to find missing files. You will (nearly) never have the identical file lists. In detail AxChecker takes the file paths of the AXIOM case and tries to subtract normalized paths from the list or file system.

### WipeR/WipeW
This is a wipe tool designed for SSDs and HDDs. There is also the possibility to overwrite files but without erasing file system metadata.

By default only unwiped blocks (or SSD pages) are overwritten though it is possible to force the overwriting of every block or even use a two pass wipe (1st pass writes random values). Instead of zeros you can choose to overwrite with any other Byte given in hex (0 - ff).

Whe the target is a physical drive, you can create a partition where (after a successful wipe) the log is copied into. A custom head for this log can be defined in a text file ("Head of log file", *log_head.txt* by default).

Be aware that this module is extremely dangerous as it is designed to erase data! There will be no "Are you really really sure questions" as Windows users might be used to.

### Settings
The Linux version has an additional settings tab. The sudo password can be set for operations needing root previliges. Make sure your user account is configured for sudo. A GUI for *blockdev --setro/--setrw* is provided and a software writeblocker can be enabled ord disabled. Be aware that setting blockdevices to read-only is not 100% safe. Make sure you do not mount devices you want to keep untouched. Disable all auto-mounting as provided e.g. by graphical file managers. Best idea might be to use a pure window manager instead of full desktop environments for forensic work.

## Cli
Every module is executable from the Terminal. Use the parameter *-h* to get the command line arguments, e.g.:
```
$ python zipimager.py -h
```
On Windows use PowerShell or CMD:
```
$ python.exe zipimager.py -h
```
If you have the Windows executables you can run e.g.:
```
$ zipimager.exe -h
```

## Legal Notice

### License
Respect GPL-3: https://www.gnu.org/licenses/gpl-3.0.en.html

### Disclaimer
Use the software on your own risk.

This is not a commercial product with an army of developers and a department for quality control behind it.
