#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/kernel-display-i2c"
patch="$project/patches/0090-cfg80211-report-interface-mac.patch"
if ! git apply --reverse --check "$patch" >/dev/null 2>&1; then
    git apply --check "$patch"
    git apply "$patch"
fi
make -j"${T110_KERNEL_JOBS:-1}" O="$base/out-display-i2c" ARCH=arm \
    CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" zImage
