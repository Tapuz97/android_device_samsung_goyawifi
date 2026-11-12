#!/bin/bash
set -eu
base=/root/t110-build
cd "$base/kernel-platform"
source_file="$base/kernel-platform/drivers/mmc/core/core.c"
backup=$(mktemp)
cp "$source_file" "$backup"
trap 'cp "$backup" "$source_file"; rm -f "$backup"' EXIT
sed -i '/if (host->index == SEC_SDCARD_INDEX) {/i #ifndef CONFIG_ARCH_VEXPRESS' "$source_file"
sed -i '/if (host->ops->get_cd \&\& host->ops->get_cd(host) == 0) {/i #endif' "$source_file"
scripts/config --file "$base/out-qemu-platform/.config" -e EXT4_FS_XATTR -e EXT4_FS_SECURITY
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-qemu-platform" oldconfig > "$base/logs/qemu-label-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-qemu-platform" zImage > "$base/logs/qemu-label-build.log" 2>&1
echo QEMU_EXT4_SECURITY_COMPILED
