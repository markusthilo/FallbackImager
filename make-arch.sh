#!/usr/bin/bash
#
#########################
# Make ArchImager image #
#########################
#
# Uses:
# 
# sfdisk
# sudo
# losetup
# mount
# pacstrap
# genfstab
# tee
# arch-chroot
#
#####

rawfile='archimager.raw'
mountpoint='/mnt/archimager'
imagesize='4'

#####

echo "Creating ${rawfile}"
dd if=/dev/zero of="${rawfile}" bs=1GiB count="${imagesize}"
sfdisk "${rawfile}" << EOF
label: gpt
size=1GiB, type=U, name=EFI
size=+, type=L, name=ROOT
EOF
loopdev=`sudo losetup -fP --show "${rawfile}"`
echo "Loop device: ${loopdev}"
sudo mkfs.ext4 "${loopdev}p2"
sudo mkfs.vfat -n EFI "${loopdev}p1"
sudo mount --mkdir "${loopdev}p2" "${mountpoint}"
sudo mount --mkdir "${loopdev}p1" "${mountpoint}/efi"
sudo pacstrap -K "${mountpoint}" base linux linux-firmware
rootuuid=`genfstab -U "${mountpoint}" | sudo tee "${mountpoint}/etc/fstab" | grep '/' | cut -f 1`
sudo mkdir -p "${mountpoint}/efi/EFI/BOOT"
sudo cp /usr/share/limine/BOOTX64.EFI "${mountpoint}/efi/EFI/BOOT"

#sudo efibootmgr --create --disk "${loopdev}" --part 1 --loader '/EFI/BOOT/BOOTX64.EFI' --label 'Limine' --unicode
sudo cp /usr/share/limine/limine-bios.sys "${mountpoint}/boot/"
#sudo limine bios-install "${loopdev}"
liminecfg='TIMEOUT=5\n\n:ArchImager\n    PROTOCOL=linux\n    KERNEL_PATH=boot:///vmlinuz-linux\n'
liminecfg+="    CMDLINE=root=${rootuuid} rw\n    MODULE_PATH=boot:///initramfs-linux.img\n"
echo -e "${liminecfg}" | sudo tee "${mountpoint}/boot/limine.cfg"


#sudo arch-chroot "${mountpoint}"
#pacman -S efibootmgr limine xorg-server xorg-xrandr i3-wm tk python libewf


#




exit

# VBoxManage convertfromraw archimager.raw archimager.vdi
