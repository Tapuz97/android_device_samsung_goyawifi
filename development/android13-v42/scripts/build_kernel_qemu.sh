#!/bin/bash
set -eu
base=/root/t110-build
mkdir -p "$base/out-qemu"
cp "$base/android-common-3.4/arch/arm/configs/vexpress_defconfig" "$base/out-qemu/.config"
cd "$base/kernel-modern"
scripts/config --file "$base/out-qemu/.config" -e SECCOMP -e SECCOMP_FILTER -e DEVTMPFS -e DEVTMPFS_MOUNT -e BLK_DEV_INITRD -e RD_GZIP -e BINFMT_ELF -e BINFMT_SCRIPT -e PROC_FS -e SYSFS -e TMPFS -d SEC_DEBUG -d SEC_DEBUG_SCHED_LOG -d SEC_LOG -d MODULES -d SND -d FB -d USB_SUPPORT -d MMC -d MTD -d ATA -d SCSI -d NETDEVICES -d INPUT -d RTC_CLASS -d PROFILING -d OPROFILE --set-str CMDLINE "console=ttyAMA0 rdinit=/init"
yes "" | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-qemu" oldconfig > "$base/logs/qemu-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-qemu" zImage > "$base/logs/qemu-kernel-build.log" 2>&1
