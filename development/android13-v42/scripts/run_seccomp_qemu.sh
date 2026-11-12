#!/bin/bash
set -eu
base=/root/t110-build
source_file=${1:?Pass the absolute path to seccomp_arm_test.c}
mkdir -p "$base/qemu-rootfs/dev" "$base/qemu-rootfs/proc"
arm-linux-gnueabi-gcc -static -O2 -pthread "$source_file" -o "$base/qemu-rootfs/init"
test -c "$base/qemu-rootfs/dev/console" || mknod "$base/qemu-rootfs/dev/console" c 5 1
(cd "$base/qemu-rootfs"; find . -print0 | cpio --null -o -H newc | gzip -n) > "$base/qemu-seccomp-initramfs.cpio.gz"
timeout 45s qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M \
 -display none -monitor none -serial stdio -net none -no-reboot \
 -kernel "$base/out-qemu/arch/arm/boot/zImage" \
 -initrd "$base/qemu-seccomp-initramfs.cpio.gz" \
 -append 'console=ttyAMA0 rdinit=/init panic=1' > "$base/logs/qemu-seccomp-test-latest.log" 2>&1
cat "$base/logs/qemu-seccomp-test-latest.log"
grep -aq 'T110 SECCOMP ARM TEST RESULT failures=0' "$base/logs/qemu-seccomp-test-latest.log"
! grep -aq '^FAIL ' "$base/logs/qemu-seccomp-test-latest.log"
