#!/usr/bin/bash


rootuuid=`cat /mnt/archimager/etc/fstab \
| grep '/efi' | grep -o 'UUID=[^ ]*'`
liminecfg='TIMEOUT=5\n\n:ArchImager\n    PROTOCOL=linux\n    KERNEL_PATH=boot:///vmlinuz-linux\n'
liminecfg+="    CMDLINE=root=${rootuuid} rw\n    MODULE_PATH=boot:///initramfs-linux.img\n"
echo -e "${liminecfg}" | sudo tee /mnt/archimager/boot/limine.cfg
