#!/bin/bash
set -eu
base=/root/t110-build
mode=${1:?tablet or qemu}
case "$mode" in
 tablet) out="$base/out-alarm"; targets='zImage modules';;
 qemu) out="$base/out-qemu-alarm"; targets=zImage;;
 *) exit 2;;
esac
cd "$base/kernel-alarm"
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig > "$base/logs/alarm-$mode-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" $targets > "$base/logs/alarm-$mode-build.log" 2>&1
echo "ALARM_KERNEL_BUILD_PASS $mode"
