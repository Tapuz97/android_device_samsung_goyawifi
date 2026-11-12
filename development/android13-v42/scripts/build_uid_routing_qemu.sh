#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
src="$base/kernel-display-i2c"
out="$base/out-qemu-uid-routing"
python3 - "$project" "$src" <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys
p,src=map(Path,sys.argv[1:])
record=json.loads((p/'evidence/hardware-v35/uid-source.json').read_text())
states=[]
for item in record['files']:
    digest=hashlib.sha256((src/item['path']).read_bytes()).hexdigest()
    assert digest in (item['before_sha256'],item['after_sha256']),item['path']
    states.append(digest==item['after_sha256'])
assert all(states) or not any(states),'Partially applied source'
if not all(states):
    subprocess.run(['patch','--dry-run','-p1','-i',str(p/'patches/0095-kernel-modern-uid-routing.patch')],cwd=src,check=True)
    subprocess.run(['patch','-p1','-i',str(p/'patches/0095-kernel-modern-uid-routing.patch')],cwd=src,check=True)
record['status']='APPLIED_BUILD_PENDING'
(p/'evidence/hardware-v35/uid-source.json').write_text(json.dumps(record,indent=2)+'\n')
PY
mkdir -p "$out"
if [ ! -f "$out/.config" ]; then
    cp "$project/evidence/hardware-v35/uid-upstream/vexpress_defconfig" "$out/.config"
fi
cd "$src"
scripts/config --file "$out/.config" -e NET -e INET -e IP_ADVANCED_ROUTER \
    -e IP_MULTIPLE_TABLES -e IPV6 -e IPV6_MULTIPLE_TABLES -e NETDEVICES \
    -e DUMMY -d SECURITY_SELINUX -e DEVTMPFS -e DEVTMPFS_MOUNT \
    -e BLK_DEV_INITRD -e RD_GZIP -e BINFMT_ELF -e BINFMT_SCRIPT -e PROC_FS \
    -e SYSFS -e TMPFS -d SEC_DEBUG -d SEC_DEBUG_SCHED_LOG -d SEC_LOG \
    -d MODULES -d SND -d FB -d USB_SUPPORT -d MMC -d MTD -d ATA -d SCSI \
    -d INPUT -d RTC_CLASS -d PROFILING -d OPROFILE --set-str CMDLINE 'console=ttyAMA0 rdinit=/init'
# Samsung's MMC hotplug branch references a board symbol absent on vexpress.
# Scope this existing QEMU adaptation to the virtual build, then restore it.
source_file="$src/drivers/mmc/core/core.c"
backup=$(mktemp)
cp "$source_file" "$backup"
trap 'cp "$backup" "$source_file"; rm -f "$backup"' EXIT
sed -i '/if (host->index == SEC_SDCARD_INDEX) {/i #ifndef CONFIG_ARCH_VEXPRESS' "$source_file"
sed -i '/if (host->ops->get_cd \&\& host->ops->get_cd(host) == 0) {/i #endif' "$source_file"
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig \
    > "$base/logs/qemu-uid-config.log" 2>&1 || test "${PIPESTATUS[1]}" -eq 0
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage \
    > "$base/logs/qemu-uid-build.log" 2>&1
echo QEMU_UID_KERNEL_BUILD_PASS
