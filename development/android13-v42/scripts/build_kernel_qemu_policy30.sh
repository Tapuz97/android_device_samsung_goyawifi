#!/bin/bash
set -eu
base=/root/t110-build
mkdir -p "$base/out-qemu-policy30"
cp "$base/out-qemu/.config" "$base/out-qemu-policy30/.config"
cd "$base/kernel-policy30"
scripts/config --file "$base/out-qemu-policy30/.config" -e AUDIT -e SECURITY -e SECURITYFS -e SECURITY_NETWORK -e SECURITY_SELINUX -e SECURITY_SELINUX_BOOTPARAM -e SECURITY_SELINUX_DEVELOP -d DEFAULT_SECURITY_DAC -e DEFAULT_SECURITY_SELINUX --set-str DEFAULT_SECURITY selinux -e TMPFS_XATTR -e TMPFS_POSIX_ACL
# Existing Kconfig expects oldconfig.
yes "" | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-qemu-policy30" oldconfig > "$base/logs/qemu-policy30-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-qemu-policy30" zImage > "$base/logs/qemu-policy30-build.log" 2>&1
