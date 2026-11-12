#!/bin/bash
set -eu
base=/root/t110-build
src='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/scripts/seccomp_arm_test.c'
mkdir -p "$base/qemu-binder-rootfs/dev" "$base/qemu-binder-rootfs/proc"
arm-linux-gnueabi-gcc -static -O2 -pthread -DTEST_POLICY30 -DTEST_BINDER -I "$base/kernel-binder/drivers/staging/android" "$src" -o "$base/qemu-binder-rootfs/init"
cp "$base/qemu-policy30.bin" "$base/qemu-binder-rootfs/policy30.bin"
sed '/^(allow kernel_t kernel_t (binder /s/ call / /' "$base/qemu-policy30.cil" > "$base/qemu-policy30-deny-binder.cil"
secilc -M false -c 30 -o "$base/qemu-binder-rootfs/policy30-deny-binder.bin" -f "$base/qemu-binder-file-contexts" "$base/qemu-policy30-deny-binder.cil"
test -c "$base/qemu-binder-rootfs/dev/console" || mknod "$base/qemu-binder-rootfs/dev/console" c 5 1
(cd "$base/qemu-binder-rootfs"; find . -print0 | cpio --null -o -H newc | gzip -n) > "$base/qemu-binder-initramfs.cpio.gz"
timeout 45s qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M -display none -monitor none -serial stdio -net none -no-reboot -kernel "$base/out-qemu-binder/arch/arm/boot/zImage" -initrd "$base/qemu-binder-initramfs.cpio.gz" -append 'console=ttyAMA0 rdinit=/init panic=1 enforcing=0' > "$base/logs/qemu-binder-test.log" 2>&1
grep -aE 'PASS |FAIL |TEST RESULT|avc:|Binder|binder:' "$base/logs/qemu-binder-test.log"
grep -aq 'PASS Binder protocol7 cross-process roundtrip' "$base/logs/qemu-binder-test.log"
grep -aq 'PASS Binder SELinux denies call in enforcing mode' "$base/logs/qemu-binder-test.log"
grep -aq 'T110 SECCOMP ARM TEST RESULT failures=0' "$base/logs/qemu-binder-test.log"
! grep -aq '^FAIL ' "$base/logs/qemu-binder-test.log"