#!/bin/bash
set -euo pipefail
[[ ${WSL_DISTRO_NAME:-} == T110Build ]]
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
python3 "$project/scripts/prepare_netd_idletimer.py" "$PWD"
log="$base/logs/netd-idletimer-$(date -u +%Y%m%dT%H%M%SZ).log"
printf '%s\n' "$log" > "$project/evidence/hardware-v35/netd-event/build-log.txt"
exec > >(tee "$log") 2>&1
export OUT_DIR=$base/out-system USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
BUILD_NUMBER=$(cat "$OUT_DIR/soong/build_number.txt");BUILD_DATETIME=$(cat "$OUT_DIR/build_date.txt");export BUILD_NUMBER BUILD_DATETIME
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 netd netd_idletimer_event_test
