#! /bin/bash

mkdir -pv dist-lin/bin
echo 'Compiling c/rod.c to dist-lin/bin/readonlydaemon'
gcc -o dist-lin/bin/readonlydaemon c/rod.c
