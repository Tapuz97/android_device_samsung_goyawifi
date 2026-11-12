#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
src="$base/kernel-display-i2c"
out="$base/out-qemu-netd-targets"
label=${2:-netd-targets}
[[ $label =~ ^[a-z0-9-]+$ ]]
log="$project/evidence/hardware-v35/$label-qemu.log"
mkdir -p "$out"
if [ "${1:-}" != '--run-only' ]; then
if [ ! -f "$out/.config" ]; then cp "$base/out-qemu-uid-routing/.config" "$out/.config"; fi
cd "$src"
scripts/config --file "$out/.config" -e NETFILTER -e NETFILTER_ADVANCED -e NETFILTER_XTABLES \
    -e NF_CONNTRACK -e NF_CONNTRACK_IPV4 -e NF_CONNTRACK_IPV6 \
    -e IP_NF_IPTABLES -e IP6_NF_IPTABLES -e IP_NF_MANGLE -e IP6_NF_MANGLE \
    -e NETFILTER_XT_MARK -e NETFILTER_XT_CONNMARK -e NETFILTER_XT_TARGET_IDLETIMER
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig \
    > "$base/logs/qemu-netd-targets-config.log" 2>&1 || test "${PIPESTATUS[1]}" -eq 0
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage \
    > "$base/logs/qemu-netd-targets-build.log" 2>&1
fi
root="$base/uid-routing-backport/guest-netd"
mkdir -p "$root/proc" "$root/sys" "$root/dev"
for pair in 'netd_target_probe.c:netd-target-probe' 'uid_routing_regression.c:uid-regression' 'netd_guest_init.c:init'; do
    arm-linux-gnueabi-gcc -static -O2 -Wall -Wextra -Werror \
        "$project/scripts/${pair%%:*}" -o "$root/${pair##*:}"
done
test -e "$root/dev/console" || mknod "$root/dev/console" c 5 1
cd "$root"
find . -print0 | cpio --quiet -o -0 -H newc | gzip -n > "$base/uid-routing-backport/guest-netd.cpio.gz"
QEMU_AUDIO_DRV=none timeout 60 qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M \
    -display none -monitor none -serial stdio -net none -no-reboot \
    -kernel "$out/arch/arm/boot/zImage" -initrd "$base/uid-routing-backport/guest-netd.cpio.gz" \
    -append 'console=ttyAMA0 rdinit=/init panic=1' > "$log" 2>&1
grep -a 'NETD_TARGET_PROBE_PASS checks=10 failed=0' "$log"
grep -a 'UID_ROUTING_REGRESSION_PASS tests=71 failed=0' "$log"
