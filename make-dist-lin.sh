#!/usr/bin/bash

# Copy scripts needed for Linux Distros to dist-lin

mkdir -pv dist-lin/lib
while read file # copy main scripts to dist-lin
do
    cp -uv "${file}" dist-lin
done << EOF
fallbackimager.py
fallbackimager-root.sh
ewfimager.py
ewfchecker.py
hashedcopy.py
sqlite.py
reporter.py
axchecker.py
wiper.py
EOF
while read file # copy libraries to dist-lin/lib
do
    cp -uv "lib/${file}" dist-lin/lib
done << EOF
extpath.py
fsreader.py
guibase.py
guiconfig.py
guielements.py
hashes.py
linutils.py
logger.py
settings.py
sqliteutils.py
stringutils.py
timestamp.py
worker.py
ewfimagergui.py
ewfcheckergui.py
hashedcopygui.py
sqlitegui.py
reportergui.py
axcheckergui.py
wipergui.py
EOF
./make-zd.sh
