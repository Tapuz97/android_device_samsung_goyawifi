#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
variant=${1:-baseline}
[[ $variant == baseline || $variant == corrected ]]
out="$base/out-qemu-netd-targets"
if [[ $variant == corrected ]]; then
 cd "$base/kernel-display-i2c"
 make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage > "$base/logs/qemu-gateway-build.log" 2>&1
fi
root="$base/uid-routing-backport/guest-gateway"
mkdir -p "$root/proc" "$root/sys" "$root/dev"
for pair in 'gateway_route_regression.c:gateway-regression' 'gateway_guest_init.c:init'; do
 arm-linux-gnueabi-gcc -static -O2 -Wall -Wextra -Werror "$project/scripts/${pair%%:*}" -o "$root/${pair##*:}"
done
test -e "$root/dev/console" || mknod "$root/dev/console" c 5 1
cd "$root"
find . -print0 | cpio --quiet -o -0 -H newc | gzip -n > "$base/uid-routing-backport/guest-gateway.cpio.gz"
QEMU_AUDIO_DRV=none timeout 60 qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M \
 -display none -monitor none -serial stdio -net none -no-reboot \
 -kernel "$out/arch/arm/boot/zImage" -initrd "$base/uid-routing-backport/guest-gateway.cpio.gz" \
 -append 'console=ttyAMA0 rdinit=/init panic=1' > "$project/evidence/hardware-v35/gateway-$variant-qemu.log" 2>&1
grep -a -e UID_TEST -e GATEWAY_ "$project/evidence/hardware-v35/gateway-$variant-qemu.log"
if [[ $variant == corrected ]]; then grep -a 'GATEWAY_ROUTE_REGRESSION_PASS' "$project/evidence/hardware-v35/gateway-$variant-qemu.log";fi
