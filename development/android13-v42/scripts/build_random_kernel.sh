#!/bin/bash
set -eu
base=/root/t110-build
mode=${1:?tablet or qemu}
case "$mode" in
tablet) out="$base/out-random"; original="$base/out-platform"; targets='zImage modules' ;;
qemu) out="$base/out-qemu-random"; original="$base/out-qemu-platform"; targets=zImage ;;
*) exit 2 ;;
esac
mkdir -p "$out"
test -f "$out/.config" || cp "$original/.config" "$out/.config"
cd "$base/kernel-random"
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig > "$base/logs/random-$mode-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" $targets > "$base/logs/random-$mode-build.log" 2>&1
echo "RANDOM_KERNEL_BUILD_PASS $mode"
