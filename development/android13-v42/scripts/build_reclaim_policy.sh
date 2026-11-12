#!/bin/bash
set -euo pipefail
[[ ${WSL_DISTRO_NAME:-} == T110Build ]]
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
target=Path('/root/t110-build/lineage20/device/samsung/t110_bringup/sepolicy')
changes={}
ledger=p/'evidence/ui-system-hang-20261112/reclaim-policy-source.json'
saved=json.loads(ledger.read_text()) if ledger.exists() else {}
for name in ['genfs_contexts','t110_bootlog.te']:
 source=p/'work/device/samsung/t110_bringup/sepolicy'/name
 previous=(target/name).read_bytes();new=source.read_bytes()
 assert b'proc_t110_swappiness' in new
 if previous==new:
  assert saved[name]['after']==hashlib.sha256(new).hexdigest()
  changes[name]=saved[name]
  continue
 assert b'proc_t110_swappiness' not in previous
 # Preserve every previous rule; only this exact node/type/permission is added.
 assert new.startswith(previous)
 (target/name).write_bytes(new)
 changes[name]={'before':hashlib.sha256(previous).hexdigest(),'after':hashlib.sha256(new).hexdigest()}
ledger.write_text(json.dumps(changes,indent=2)+'\n')
PY
log="$project/evidence/ui-system-hang-20261112/reclaim-policy-build.log"
exec > >(tee "$log") 2>&1
export OUT_DIR=$base/out-system USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
BUILD_NUMBER=$(cat "$OUT_DIR/soong/build_number.txt");BUILD_DATETIME=$(cat "$OUT_DIR/build_date.txt");export BUILD_NUMBER BUILD_DATETIME
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 selinux_policy
python3 "$project/scripts/export_reclaim_policy.py"
