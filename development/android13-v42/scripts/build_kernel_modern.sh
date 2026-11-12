#!/bin/bash
set -eu
base=/root/t110-build
mkdir -p "$base/out-modern"
cp "$base/out-security/.config" "$base/out-modern/.config"
cd "$base/kernel-modern"
scripts/config --file "$base/out-modern/.config" -e SECCOMP -e SECCOMP_FILTER
# This 3.4 Kconfig predates olddefconfig.
yes "" | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-modern" oldconfig > "$base/logs/modern-config.log" 2>&1
make -j6 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-modern" zImage > "$base/logs/modern-build.log" 2>&1
sha256sum "$base/out-modern/arch/arm/boot/zImage"
