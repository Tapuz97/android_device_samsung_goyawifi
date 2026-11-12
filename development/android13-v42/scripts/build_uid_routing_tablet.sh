#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
src="$base/kernel-display-i2c"
out="$base/out-uid-routing"
mkdir -p "$out"
if [ ! -f "$out/.config" ]; then cp "$base/out-display-i2c/.config" "$out/.config"; fi
cd "$src"
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig \
    > "$base/logs/tablet-uid-config.log" 2>&1 || test "${PIPESTATUS[1]}" -eq 0
cmp "$out/.config" "$base/out-display-i2c/.config"
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage modules \
    > "$base/logs/tablet-uid-build.log" 2>&1
sha256sum "$out/arch/arm/boot/zImage" "$out/.config" > "$project/evidence/hardware-v35/compiled-kernel.txt"
echo TABLET_UID_KERNEL_BUILD_PASS
