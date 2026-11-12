#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
if [ ! -d "$base/kernel-display-i2c" ] && [ ! -d "$base/out-display-i2c" ]; then
    python3 "$project/scripts/prepare_display_i2c_kernel.py"
else
    test -d "$base/kernel-display-i2c" && test -d "$base/out-display-i2c"
    python3 - "$project" <<'PY'
from pathlib import Path
import hashlib,json,sys
p=Path(sys.argv[1]);b=Path('/root/t110-build')
r=json.loads((p/'evidence/offline-v34/display-i2c-source.json').read_text())
assert hashlib.sha256((b/'kernel-display-i2c'/r['source']).read_bytes()).hexdigest()==r['after_sha256']
assert hashlib.sha256((b/'out-display-i2c/.config').read_bytes()).hexdigest()==r['config_sha256']
PY
fi
python3 "$project/scripts/prepare_touch_charge_kernel.py"
python3 "$project/scripts/prepare_ion_map_kernel.py" "$project"
python3 "$project/scripts/prepare_ion_mapping_bounds.py" "$project"
python3 "$project/scripts/prepare_goya_reboot_alias.py"
cd "$base/kernel-display-i2c"
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-display-i2c" zImage modules > "$base/logs/display-i2c-build.log" 2>&1
echo DISPLAY_I2C_KERNEL_BUILD_PASS
