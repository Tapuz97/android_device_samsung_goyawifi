#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
arm-linux-gnueabi-gcc -static -O2 -Wall -Wextra -Werror \
    "$project/scripts/uid_routing_regression.c" -o "$base/uid-routing-backport/uid_regression"
root="$base/uid-routing-backport/guest"
mkdir -p "$root/proc" "$root/sys" "$root/dev"
cp "$base/uid-routing-backport/uid_regression" "$root/init"
test -e "$root/dev/console" || mknod "$root/dev/console" c 5 1
cd "$root"
find . -print0 | cpio --quiet -o -0 -H newc | gzip -n > "$base/uid-routing-backport/guest.cpio.gz"
QEMU_AUDIO_DRV=none timeout 60 qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M \
    -display none -monitor none -serial stdio -net none -no-reboot \
    -kernel "$base/out-qemu-uid-routing/arch/arm/boot/zImage" \
    -initrd "$base/uid-routing-backport/guest.cpio.gz" \
    -append 'console=ttyAMA0 rdinit=/init panic=1' \
    > "$project/evidence/hardware-v35/uid-qemu.log" 2>&1
tail -n 65 "$project/evidence/hardware-v35/uid-qemu.log"
grep 'UID_ROUTING_REGRESSION_PASS' "$project/evidence/hardware-v35/uid-qemu.log"
