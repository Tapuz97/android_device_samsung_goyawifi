#!/bin/bash
set -eu
base=/root/t110-build
src='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/scripts/seccomp_arm_test.c'
mkdir -p "$base/qemu-policy30-rootfs/dev" "$base/qemu-policy30-rootfs/proc"
arm-linux-gnueabi-gcc -static -O2 -pthread -DTEST_POLICY30 "$src" -o "$base/qemu-policy30-rootfs/init"
cp "$base/qemu-policy30.bin" "$base/qemu-policy30-rootfs/policy30.bin"
test -c "$base/qemu-policy30-rootfs/dev/console" || mknod "$base/qemu-policy30-rootfs/dev/console" c 5 1
(cd "$base/qemu-policy30-rootfs"; find . -print0 | cpio --null -o -H newc | gzip -n) > "$base/qemu-policy30-initramfs.cpio.gz"
timeout 45s qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M -display none -monitor none -serial stdio -net none -no-reboot -kernel "$base/out-qemu-policy30/arch/arm/boot/zImage" -initrd "$base/qemu-policy30-initramfs.cpio.gz" -append 'console=ttyAMA0 rdinit=/init panic=1 enforcing=0' > "$base/logs/qemu-policy30-test.log" 2>&1
cat "$base/logs/qemu-policy30-test.log"
grep -aq 'PASS SELinux policy30 with ioctl xperms result=0' "$base/logs/qemu-policy30-test.log"
grep -aq 'T110 SECCOMP ARM TEST RESULT failures=0' "$base/logs/qemu-policy30-test.log"
! grep -aq '^FAIL ' "$base/logs/qemu-policy30-test.log"