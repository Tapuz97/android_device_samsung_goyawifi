#!/bin/bash
set -euo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || exit 3
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
cp "$project/work/device/samsung/t110_bringup/sepolicy/file_contexts" device/samsung/t110_bringup/sepolicy/file_contexts
cp "$project/work/device/samsung/t110_bringup/sepolicy/t110_bootlog.te" device/samsung/t110_bringup/sepolicy/t110_bootlog.te
cp "$project/work/device/samsung/t110_bringup/sepolicy/property_contexts" device/samsung/t110_bringup/sepolicy/property_contexts
export OUT_DIR=$base/out-system USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
export BUILD_NUMBER=$(cat "$OUT_DIR/soong/build_number.txt")
export BUILD_DATETIME=$(cat "$OUT_DIR/build_date.txt")
log=$base/logs/swap-label-policy-$(date -u +%Y%m%dT%H%M%SZ).log
printf '%s\n' "$log" > "$project/evidence/offline-v41/swap-label-build-log.txt"
exec > >(tee "$log") 2>&1
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
# Use the product's standard image dependency graph, which compiles the actual
# installed policy, contexts and neverallow checks. The broader selinux_policy
# aggregate additionally compares frozen platform API snapshots; existing legacy
# device compatibility edits fail that unrelated API-freeze comparison.
m -j2 systemimage
python3 - "$project" "$OUT_DIR" <<'PY'
from pathlib import Path
import sys,shutil,hashlib,json
p=Path(sys.argv[1]);o=Path(sys.argv[2]);product=o/'target/product/t110_bringup';e=p/'evidence/offline-v41/swap-label-fix';e.mkdir(exist_ok=True)
paths=['root/sepolicy','system/vendor/etc/selinux/precompiled_sepolicy','system/vendor/etc/selinux/vendor_file_contexts','system/vendor/etc/selinux/vendor_property_contexts']
assert (product/paths[0]).read_bytes()==(product/paths[1]).read_bytes()
assert '/dev/block/zram0' in (product/paths[2]).read_text()
record={}
for name in paths:
 f=product/name;target=e/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);record[name]=hashlib.sha256(f.read_bytes()).hexdigest()
(e/'compiled.json').write_text(json.dumps(record,indent=2)+'\n')
print('SWAP_LABEL_POLICY_COMPILED')
PY
