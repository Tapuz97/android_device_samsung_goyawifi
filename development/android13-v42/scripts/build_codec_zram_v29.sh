#!/bin/bash
set -euo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || exit 3
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
python3 "$project/scripts/prepare_codec_loader_swap_policy.py" "$project" "$PWD"
python3 "$project/scripts/prepare_codec_yv12_fallback.py" "$project" "$PWD"
cp "$project/work/device/samsung/t110_bringup/BoardConfig.mk" device/samsung/t110_bringup/BoardConfig.mk
cp "$project/work/device/samsung/t110_bringup/sepolicy/t110_bootlog.te" device/samsung/t110_bringup/sepolicy/t110_bootlog.te
export OUT_DIR=$base/out-system USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
export BUILD_NUMBER=$(cat "$OUT_DIR/soong/build_number.txt")
if [ -f "$OUT_DIR/build_date.txt" ]; then export BUILD_DATETIME=$(cat "$OUT_DIR/build_date.txt"); fi
stamp=$(date -u +%Y%m%dT%H%M%SZ)
log=$base/logs/system-image-$stamp.log
printf '%s\n' "system-image-$stamp.log" > "$project/evidence/offline-v41/system-v29-build-log-name.txt"
exec > >(tee "$log") 2>&1
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 systemimage
echo CODEC_ZRAM_V29_BUILD_COMPLETED
