#!/bin/bash
set -euo pipefail
[[ ${WSL_DISTRO_NAME:-} == T110Build ]]
[[ $(cat /etc/machine-id) == cd27023803954a89ad7c30407399c847 ]]
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
out="$base/out-system"
cd "$base/lineage20"
python3 "$project/scripts/prepare_hwui_resolve.py" "$PWD"
log="$base/logs/combined-t110-$(date -u +%Y%m%dT%H%M%SZ).log"
printf '%s\n' "${log##*/}" > "$project/evidence/hardware-v35/hwui-system-build-log.txt"
exec > >(tee "$log") 2>&1
export OUT_DIR=$out USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
BUILD_NUMBER=$(cat "$out/soong/build_number.txt");BUILD_DATETIME=$(cat "$out/build_date.txt")
export BUILD_NUMBER BUILD_DATETIME
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 systemimage
