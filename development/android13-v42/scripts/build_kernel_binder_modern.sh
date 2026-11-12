#!/bin/bash
set -eu
base=/root/t110-build
mode=${1:?Use t110 or qemu}
case "$mode" in
 t110) out="$base/out-binder-modern"; seed="$base/out-policy30/.config";;
 qemu) out="$base/out-qemu-binder-modern"; seed="$base/out-qemu-policy30/.config";;
 *) exit 2;;
esac
mkdir -p "$out"
cp "$seed" "$out/.config"
cd "$base/kernel-binder-modern"
scripts/config --file "$out/.config" -d USER_NS -e STAGING -e ANDROID -e ANDROID_BINDER_IPC -e ANDROID_BINDER_IPC_32BIT --set-str ANDROID_BINDER_DEVICES binder,hwbinder,vndbinder -e DEVTMPFS
if [ "$mode" = qemu ]; then scripts/config --file "$out/.config" -d ANDROID_TIMED_OUTPUT -d ANDROID_TIMED_GPIO; fi
yes "" | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig > "$base/logs/binder-modern-$mode-config.log" 2>&1
# Prevent Kconfig dependencies from silently removing the Binder backport.
grep -qx 'CONFIG_ANDROID_BINDER_IPC=y' "$out/.config"
grep -qx 'CONFIG_ANDROID_BINDER_IPC_32BIT=y' "$out/.config"
grep -qx 'CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"' "$out/.config"
grep -qx '# CONFIG_USER_NS is not set' "$out/.config"
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage > "$base/logs/binder-modern-$mode-build.log" 2>&1