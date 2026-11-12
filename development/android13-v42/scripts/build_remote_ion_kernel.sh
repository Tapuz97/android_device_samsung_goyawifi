#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
python3 "$project/scripts/prepare_ion_map_kernel.py" "$project"
cd "$base/kernel-display-i2c"
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-display-i2c" zImage modules > "$base/logs/ion-map-build-20261110.log" 2>&1
cp "$base/logs/ion-map-build-20261110.log" "$project/evidence/remote-fixes-20261110/ion-kernel-build.log"
sha256sum "$base/out-display-i2c/arch/arm/boot/zImage" "$base/out-display-i2c/drivers/marvell/graphics/galcore_src/galcore.ko"
echo ION_MAP_KERNEL_BUILT_OFFLINE
