#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
src="$base/kernel-display-i2c"
out="$base/out-netd-targets"
python3 - "$project" "$src" <<'PY'
from pathlib import Path
import hashlib,json,sys
p,src=map(Path,sys.argv[1:])
record=json.loads((p/'evidence/hardware-v35/uid-source.json').read_text())
for item in record['files']:
    assert hashlib.sha256((src/item['path']).read_bytes()).hexdigest()==item['after_sha256'],item['path']
assert (p/'evidence/hardware-v35/uid-qemu-result.json').is_file()
PY
mkdir -p "$out"
if [ ! -f "$out/.config" ]; then cp "$project/evidence/hardware-v35/netd-targets.config" "$out/.config"; fi
cd "$src"
yes '' | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldconfig \
    > "$base/logs/netd-targets-config.log" 2>&1 || test "${PIPESTATUS[1]}" -eq 0
cmp "$out/.config" "$project/evidence/hardware-v35/netd-targets.config"
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage modules \
    > "$base/logs/netd-targets-build.log" 2>&1
sha256sum "$out/arch/arm/boot/zImage" "$out/.config" > "$project/evidence/hardware-v35/compiled-kernel-netd-targets.txt"
echo NETD_TARGETS_KERNEL_BUILD_PASS
