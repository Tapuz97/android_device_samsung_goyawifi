#!/bin/bash
set -eu
base=/root/t110-build
cd "$base/kernel-binder-modern"
out="$base/out-qemu-binder-modern"
cp -n "$out/.config" "$out/config.before-core-boot"
scripts/config --file "$out/.config" -e MMC -e MMC_BLOCK -e MMC_ARMMMCI \
    -e EXT4_FS -e EXT4_FS_XATTR -e EXT4_FS_SECURITY
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig \
    > "$base/logs/qemu-core-config.log" 2>&1

# The Samsung MMC tree references sec_class, which the emulator board lacks.
source_file=drivers/mmc/core/core.c
backup=$(mktemp)
cp "$source_file" "$backup"
trap 'cp "$backup" "$source_file"; rm -f "$backup"' EXIT
sed -i '/if (host->index == SEC_SDCARD_INDEX) {/i #ifndef CONFIG_ARCH_VEXPRESS' "$source_file"
sed -i '/if (host->ops->get_cd \&\& host->ops->get_cd(host) == 0) {/i #endif' "$source_file"
make -j8 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage \
    > "$base/logs/qemu-core-kernel.log" 2>&1
cp "$out/arch/arm/boot/zImage" "$base/qemu-core-zImage"
