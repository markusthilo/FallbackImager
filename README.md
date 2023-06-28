# FallbackImager

Imager for forensic work as complement and fallback to the commercial tools.

In this testing state only Windows is supported.

This is work in progress.

## Modules:

### MkIsoImager
Imaging a logical file structure as ISO using mkisofs

### OscdImager
Imaging a logical file structure as ISO using oscdimg.exe (MS tool, Win only)

### IsoVerify
Verifying/comparing ISO to a logical file structure (using PyCdlib)

### DismImager
Imaging a logical file structure as WIM (Admin privileges required, uses dism.exe, Win only)

### ZipImager
Imaging a logical file structure as ZIP file

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
