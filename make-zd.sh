#! /bin/bash

mkdir -pv dist-lin/bin
echo 'Compiling c/zd.c to dist-lin/bin/zd'
gcc -o dist-lin/bin/zd c/zd.c
