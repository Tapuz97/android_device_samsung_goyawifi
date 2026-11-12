#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
src="$base/kernel-display-i2c"
out="$base/out-gateway"
test "$WSL_DISTRO_NAME" = Ubuntu
test -f "$out/Module.symvers"
python3 "$project/scripts/prepare_bt_module.py"
sha256sum "$out/.config" "$out/Module.symvers" > "$project/evidence/hardware-bt-sd/module-build-inputs.txt"
make -C "$src" -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" \
    M=drivers/marvell/sd8787/mbtc_src modules > "$base/logs/bt-module-restricted.log" 2>&1
cp "$out/drivers/marvell/sd8787/mbtc_src/mbt8xxx.ko" "$project/evidence/hardware-bt-sd/mbt8xxx.ko"
"$base/toolchain/bin/arm-eabi-readelf" -p .modinfo "$project/evidence/hardware-bt-sd/mbt8xxx.ko" \
    > "$project/evidence/hardware-bt-sd/module-modinfo.txt"
python3 - "$project" "$out" <<'PY'
from pathlib import Path
import hashlib,json,struct,sys
p,out=map(Path,sys.argv[1:]);e=p/'evidence/hardware-bt-sd';f=e/'mbt8xxx.ko';data=f.read_bytes()
assert data[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',data,18)[0]==40
assert b'parm=require_fw_ready:' in data and b'parmtype=require_fw_ready:bool' in data
assert b'parmtype=drv_mode:int' in data and b'parmtype=debug_intf:int' in data
record=dict(module_sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),config_sha256=hashlib.sha256((out/'.config').read_bytes()).hexdigest(),
 source=json.loads((e/'module-source.json').read_text()),status='BUILT_NOT_LOADED')
(e/'module-build.json').write_text(json.dumps(record,indent=2)+'\n');print('BT_MODULE_COMPILED',record['module_sha256'])
PY
