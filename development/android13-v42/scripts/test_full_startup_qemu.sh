#!/bin/bash
set -euo pipefail
base=/root/t110-build
kernel=${T110_QEMU_KERNEL:-$base/out-qemu-platform/arch/arm/boot/zImage}
duration=${T110_QEMU_SECONDS:-300}
case "$duration" in *[!0-9]*|'') exit 2 ;; esac
label=${T110_QEMU_LABEL:-v2}
artifact=${T110_QEMU_ARTIFACT:-android13-full-v10}
[[ "$artifact" =~ ^android13-full-v[0-9]+$ ]]
system=${T110_QEMU_SYSTEM:-lineage20-rom-v2}
[[ "$system" =~ ^lineage20-rom-v[0-9]+$ ]]
case "$label" in *[!a-zA-Z0-9-]*) exit 2 ;; esac
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
root=$(mktemp -d "$base/qemu-full-init-XXXXXX")
chmod 0755 "$root"
cd "$root"
gzip -dc "$project/artifacts/$artifact/qemu-ramdisk.cpio.gz" | cpio --quiet -idm --no-absolute-filenames
python3 - "$root/init.mrvl.rc" <<'PY'
import sys
from pathlib import Path
p=Path(sys.argv[1])
s=p.read_text().replace('insmod /lib/modules/galcore.ko', 'insmod /nonexistent-qemu-galcore.ko')
s=s.replace('-b all -f /data/local/tmp/t110-logcat.txt -r 4096 -n 2', '-b main -b system -b crash -v brief -f /dev/ttyAMA0')
s='on early-init\n    mount tmpfs tmpfs /data nosuid nodev mode=0771,size=256m\n\n'+s
p.write_text(s)
PY
find . -print0 | cpio --quiet -o -0 -H newc | gzip -n > "$base/qemu-full-init.cpio.gz"
disk="$base/qemu-$system.img"
if test ! -e "$disk"; then
    cp "$project/artifacts/$system/system.raw.img" "$disk"
    truncate -s 2G "$disk"
fi
expected=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["sha256"])' "$project/artifacts/$system/system-verification.json")
head -c 1594884096 "$disk" | sha256sum | grep "^$expected "
set +e
QEMU_AUDIO_DRV=none timeout "$duration" qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -smp 2 -m 768M \
    -display none -monitor none -serial stdio -net none -no-reboot \
    -kernel "$kernel" -initrd "$base/qemu-full-init.cpio.gz" \
    -snapshot -drive "file=$disk,if=sd,format=raw" \
    -append 'console=ttyAMA0 rdinit=/init panic=1 androidboot.hardware=mrvl androidboot.init_fatal_reboot_target=recovery' > "$base/logs/qemu-full-init-$label.log" 2>&1
result=$?
set -e
cp "$base/logs/qemu-full-init-$label.log" "$project/evidence/qemu-full-init-$label.log"
echo "QEMU exit=$result; log=$project/evidence/qemu-full-init-$label.log"
test "$result" = 0 -o "$result" = 124
