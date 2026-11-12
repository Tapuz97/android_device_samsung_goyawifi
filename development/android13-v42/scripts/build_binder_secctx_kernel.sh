#!/bin/bash
set -euo pipefail
base=/root/t110-build
cd "$base/kernel-binder-secctx"
out="$base/out-binder-secctx"
mkdir -p "$base/logs"
make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldnoconfig > "$base/logs/binder-secctx-config.log" 2>&1
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage modules > "$base/logs/binder-secctx-build.log" 2>&1
echo BINDER_SECCTX_KERNEL_BUILD_PASS
