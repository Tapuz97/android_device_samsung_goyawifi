#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
root=$(mktemp -d "$base/qemu-random-test-XXXXXX")
chmod 0755 "$root"
mkdir -p "$root/dev"
arm-linux-gnueabi-gcc -static -O2 -Wall -Wextra -Werror "$project/work/core-boot/getrandom_test.c" -o "$root/init"
cd "$root"
find . -print0 | cpio --quiet -o -0 -H newc | gzip -n > "$base/qemu-random-test.cpio.gz"
QEMU_AUDIO_DRV=none timeout 40 qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M \
    -display none -monitor none -serial stdio -net none -no-reboot \
    -kernel "$base/out-qemu-random/arch/arm/boot/zImage" -initrd "$base/qemu-random-test.cpio.gz" \
    -append 'console=ttyAMA0 rdinit=/init panic=1' > "$project/evidence/qemu-getrandom-test.log" 2>&1
grep T110_GETRANDOM_REGRESSION_PASS "$project/evidence/qemu-getrandom-test.log"
