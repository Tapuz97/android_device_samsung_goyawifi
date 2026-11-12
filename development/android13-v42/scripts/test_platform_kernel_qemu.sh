#!/bin/bash
set -eu
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
out="$base/out-qemu-platform"
mkdir -p "$out"
cp "$base/out-qemu-binder-modern/.config" "$out/.config"
cd "$base/kernel-platform"
source_file="$base/kernel-platform/drivers/mmc/core/core.c"
backup=$(mktemp)
cp "$source_file" "$backup"
trap 'cp "$backup" "$source_file"; rm -f "$backup"' EXIT
sed -i '/if (host->index == SEC_SDCARD_INDEX) {/i #ifndef CONFIG_ARCH_VEXPRESS' "$source_file"
sed -i '/if (host->ops->get_cd \&\& host->ops->get_cd(host) == 0) {/i #endif' "$source_file"
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig > "$base/logs/qemu-platform-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage > "$base/logs/qemu-platform-build.log" 2>&1
root="$base/qemu-ambient-test"
mkdir -p "$root/dev" "$root/proc"
arm-linux-gnueabi-gcc -static -O2 -Wall -Wextra -Werror "$project/work/core-boot/ambient_test.c" -o "$root/init"
cd "$root"
find . -print0 | cpio --quiet -o -0 -H newc | gzip -n > "$base/qemu-ambient-test.cpio.gz"
QEMU_AUDIO_DRV=none timeout 40 qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M \
    -display none -monitor none -serial stdio -net none -no-reboot \
    -kernel "$out/arch/arm/boot/zImage" -initrd "$base/qemu-ambient-test.cpio.gz" \
    -append 'console=ttyAMA0 rdinit=/init panic=1' > "$project/evidence/qemu-ambient-test.log" 2>&1
grep T110_AMBIENT_REGRESSION_PASS "$project/evidence/qemu-ambient-test.log"
