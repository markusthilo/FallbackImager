#!/usr/bin/bash

# Copy scripts needed for Linux Distros to dist-lin

mkdir -pv dist-lin/lib
while read file # copy main scripts to dist-lin
do
    cp -ufv "${file}" dist-lin
done << EOF
appicon.png
archimager.py
axchecker.py
ewfchecker.py
ewfimager.py
fallbackimager.py
fallbackimager.sh*
hashedcopy.py
help.txt
LICENSE
README.md
reporter-example-template.txt
reporter.py
sqlite.py
wipe-log-head.txt
wiper.py
zipimager.py
EOF
while read file # copy libraries to dist-lin/lib
do
    cp -ufv "lib/${file}" dist-lin/lib
done << EOF
axcheckergui.py
diskselectgui.py
ewfcheckergui.py
ewfimagergui.py
guibase.py
guiconfig.py
guielements.py
guilabeling.py
hashedcopygui.py
hashes.py
linsettingsgui.py
linutils.py
logger.py
mfdbreader.py
pathutils.py
reportergui.py
settings.py
sqlitegui.py
sqliteutils.py
stringutils.py
timestamp.py
wipergui.py
worker.py
zipimagergui.py
EOF
./make-zd.sh
./make-rod.sh
