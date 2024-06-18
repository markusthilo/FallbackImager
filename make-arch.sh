#!/usr/bin/bash

#############################
# Make ArchImager ISO image #
#############################
#
# Uses:
# 
# archiso
#
#####

cp -r /usr/share/archiso/configs/baseline/ archlive
cp -rv archimager/* archlive/airootfs/

mkarchiso -v -w archiso_work_dir -o archiso_out_dir archlive
