#! /bin/bash

mkdir -pv dist-win/bin
echo 'Compiling c/zd-win.c to dist-win/bin/zd-win.exe'
x86_64-w64-mingw32-gcc -o dist-win/bin/zd-win.exe c/zd-win.c
