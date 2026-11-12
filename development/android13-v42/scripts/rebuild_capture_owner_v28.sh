#!/bin/bash
set -euo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || exit 3
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
patch="$project/patches/0080-gui-t110-retain-capture-buffer-owner.patch"
if ! git -C frameworks/native apply --reverse --check "$patch" >/dev/null 2>&1; then
    git -C frameworks/native apply --check "$patch"
    git -C frameworks/native apply "$patch"
fi
export OUT_DIR=$base/out-system USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
# Continue the same v28 build identity; avoid rebuilding every resource tool/APK
# merely because this targeted native correction starts in a later shell.
export BUILD_NUMBER=$(cat "$OUT_DIR/soong/build_number.txt")
if [ -f "$OUT_DIR/build_date.txt" ]; then export BUILD_DATETIME=$(cat "$OUT_DIR/build_date.txt"); fi
stamp=$(date -u +%Y%m%dT%H%M%SZ)
log=$base/logs/system-image-$stamp.log
if [ ! -e "$project/evidence/offline-v41/initial-system-build-log-name.txt" ]; then
    cp "$project/evidence/offline-v41/system-build-log-name.txt" "$project/evidence/offline-v41/initial-system-build-log-name.txt"
fi
printf '%s\n' "system-image-$stamp.log" > "$project/evidence/offline-v41/system-build-log-name.txt"
exec > >(tee "$log") 2>&1
set +u # Android's supported envsetup/lunch scripts use unset shell variables.
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 systemimage
echo CAPTURE_OWNER_V28_REBUILD_COMPLETED
