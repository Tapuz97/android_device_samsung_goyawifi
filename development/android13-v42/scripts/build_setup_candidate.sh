#!/bin/bash
set -eo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || exit 3
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
cp -a "$project/work/device/samsung/t110_bringup" device/samsung/
log=$base/logs/setup-canvas-$(date -u +%Y%m%dT%H%M%SZ).log
exec > >(tee "$log") 2>&1
echo "SETUP_CANDIDATE_LOG=$log"
export OUT_DIR=$base/out-system USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 LineageSetupWizard
mkdir -p "$project/evidence/offline-v32/setup-candidate"
cp "$base/out-system/target/product/t110_bringup/system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk" "$project/evidence/offline-v32/setup-candidate/LineageSetupWizard.apk"
echo SETUP_CANDIDATE_COMPILED
