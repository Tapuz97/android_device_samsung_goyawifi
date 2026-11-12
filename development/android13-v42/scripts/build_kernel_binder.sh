#!/bin/bash
set -eu
base=/root/t110-build
mode=${1:?Use t110 or qemu}
case "$mode" in
 t110) out="$base/out-binder"; seed="$base/out-policy30/.config";;
 qemu) out="$base/out-qemu-binder"; seed="$base/out-qemu-policy30/.config";;
 *) exit 2;;
esac
mkdir -p "$out"
cp "$seed" "$out/.config"
cd "$base/kernel-binder"
scripts/config --file "$out/.config" -e STAGING -e ANDROID -e ANDROID_BINDER_IPC -e DEVTMPFS
if [ "$mode" = qemu ]; then scripts/config --file "$out/.config" -d ANDROID_TIMED_OUTPUT -d ANDROID_TIMED_GPIO; fi
yes "" | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig > "$base/logs/binder-$mode-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage > "$base/logs/binder-$mode-build.log" 2>&1