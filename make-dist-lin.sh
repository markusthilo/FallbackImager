#!/usr/bin/bash

# Copy scripts needed for Linux Distros to dist-lin

mkdir -pv dist-lin/lib
while read file # copy main scripts to dist-lin
do
    cp -ufv "${file}" dist-lin
done << EOF
fallbackimager.py
fallbackimager-root.sh
ewfimager.py
ewfchecker.py
hashedcopy.py
zipimager.py
sqlite.py
reporter.py
axchecker.py
wiper.py
appicon.png
help.txt
LICENSE
README.md
wipe-log-head.txt
reporter-example-template.txt
EOF
while read file # copy libraries to dist-lin/lib
do
    cp -ufv "lib/${file}" dist-lin/lib
done << EOF
extpath.py
fsreader.py
diskselectgui.py
guibase.py
guiconfig.py
guilabeling.py
guielements.py
hashes.py
linutils.py
logger.py
mfdbreader.py
settings.py
sqliteutils.py
stringutils.py
timestamp.py
worker.py
ewfimagergui.py
ewfcheckergui.py
hashedcopygui.py
zipimagergui.py
sqlitegui.py
reportergui.py
axcheckergui.py
wipergui.py
EOF
./make-zd.sh
