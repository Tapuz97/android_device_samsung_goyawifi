#!/bin/bash
set -eu
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
out="$base/out-platform"
mkdir -p "$out"
if [ ! -f "$out/.config" ]; then
    cp "$project/artifacts/kernel-native-init-ffs/kernel.config" "$out/.config"
fi
cd "$base/kernel-platform"
scripts/config --file "$out/.config" --set-str CMDLINE "androidboot.hardware=mrvl" -e CMDLINE_EXTEND -d CMDLINE_FROM_BOOTLOADER
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig > "$base/logs/platform-kernel-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage modules > "$base/logs/platform-kernel-build.log" 2>&1
