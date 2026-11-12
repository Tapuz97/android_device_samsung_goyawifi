#!/bin/bash
set -euo pipefail
base=/root/t110-build
kernel=${T110_QEMU_KERNEL:-$base/out-qemu-random/arch/arm/boot/zImage}
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
root="$base/qemu-logging-test"
mkdir -p "$root/dev" "$root/proc" "$root/sys" "$root/stage-data"
test -s "$project/work/core-boot/logging-test-policy"
cp "$project/work/core-boot/logging-test-policy" "$root/policy"
cp "$project/work/core-boot/logging-test-policy" "$root/t110-preload-policy"
arm-linux-gnueabi-gcc -static -O2 -Wall -Wextra -Werror -DT110_FULL_BOOT "$project/work/core-boot/logging_test.c" -o "$root/init"
image=$(mktemp "$base/qemu-logging-test-XXXXXX.img")
printf '%s\n' "$image" > "$project/evidence/qemu-persistent-disk.txt"
truncate -s 64M "$image"
mkfs.ext4 -q -F -O ^64bit,^metadata_csum,^huge_file "$image"
cd "$root"
find . -print0 | cpio --quiet -o -0 -H newc | gzip -n > "$base/qemu-logging-test.cpio.gz"
QEMU_AUDIO_DRV=none timeout 90 qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 256M \
    -display none -monitor none -serial stdio -net none -no-reboot \
    -kernel "$kernel" \
    -initrd "$base/qemu-logging-test.cpio.gz" -drive "file=$image,if=sd,format=raw" \
    -append 'console=ttyAMA0 rdinit=/init panic=1' > "$base/logs/qemu-persistent-logging.log" 2>&1
cp "$base/logs/qemu-persistent-logging.log" "$project/evidence/qemu-persistent-logging.log"
debugfs -R 'cat /local/tmp/t110-bootlogs/boot-0001/checkpoints.txt' "$image" > "$project/evidence/qemu-persistent-checkpoints.txt" 2>/dev/null
grep LOG_TEST_AFTER_ENFORCING "$project/evidence/qemu-persistent-checkpoints.txt"
debugfs -R 'cat /local/tmp/t110-bootlogs/boot-0001/logger-status.txt' "$image" > "$project/evidence/qemu-persistent-logger-status.txt" 2>/dev/null
grep 'Kernel snapshot 3:' "$project/evidence/qemu-persistent-logger-status.txt"
if grep -i failed "$project/evidence/qemu-persistent-checkpoints.txt" "$project/evidence/qemu-persistent-logger-status.txt"; then exit 1; fi
debugfs -R 'cat /local/tmp/t110-bootlogs/boot-0001/kernel-1.txt' "$image" > "$project/evidence/qemu-persistent-kernel.txt" 2>/dev/null
grep 'enforcing=1' "$project/evidence/qemu-persistent-logger-status.txt"
echo PERSISTENT_LOGGING_ENFORCING_REBOOT_TEST_PASS
