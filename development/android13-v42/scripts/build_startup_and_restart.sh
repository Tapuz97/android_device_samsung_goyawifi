#!/bin/bash
set -euo pipefail
[[ ${WSL_DISTRO_NAME:-} == T110Build ]]
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
out="$base/out-system"
test -s "$out/soong/build_number.txt"
test -s "$out/build_date.txt"
cd "$base/lineage20"
log="$base/logs/combined-t110-$(date -u +%Y%m%dT%H%M%SZ).log"
printf '%s\n' "$log"
exec > >(tee "$log") 2>&1
python3 "$project/scripts/prepare_startup_and_restart.py" "$PWD"
cp -a "$project/work/device/samsung/t110_bringup" device/samsung/
python3 "$project/scripts/prepare_sd8777_build.py" "$PWD"
scanout="$project/patches/0089-composer-t110-neon-scanout.patch"
if ! git -C hardware/interfaces apply --reverse --check "$scanout" >/dev/null 2>&1; then
    git -C hardware/interfaces apply --check "$scanout"
    git -C hardware/interfaces apply "$scanout"
fi
export OUT_DIR=$out USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1
export OVERRIDE_TARGET_FLATTEN_APEX=true
BUILD_NUMBER=$(cat "$out/soong/build_number.txt")
BUILD_DATETIME=$(cat "$out/build_date.txt")
export BUILD_NUMBER BUILD_DATETIME
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 systemimage
