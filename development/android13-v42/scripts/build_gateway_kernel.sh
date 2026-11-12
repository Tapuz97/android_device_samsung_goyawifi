#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
src="$base/kernel-display-i2c"
out="$base/out-gateway"
python3 "$project/scripts/prepare_gateway_routes.py"
if [ ! -d "$out" ]; then cp -a --reflink=auto "$base/out-netd-targets" "$out";fi
cd "$src"
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage modules > "$base/logs/gateway-kernel-build.log" 2>&1
cmp "$out/.config" "$project/evidence/hardware-v35/netd-targets.config"
sha256sum "$out/arch/arm/boot/zImage" "$out/.config" > "$project/evidence/hardware-v35/compiled-kernel-gateway.txt"
echo GATEWAY_KERNEL_BUILD_PASS
