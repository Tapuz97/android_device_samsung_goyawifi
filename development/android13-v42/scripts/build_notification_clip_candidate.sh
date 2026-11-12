#!/bin/bash
set -eo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || exit 3
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
log=$base/logs/notification-clip-$(date -u +%Y%m%dT%H%M%SZ).log
exec > >(tee "$log") 2>&1
echo "NOTIFICATION_CLIP_LOG=$log"
git -C frameworks/base apply --reverse --check "$project/patches/0076-systemui-t110-finite-notification-clips.patch"
export OUT_DIR=$base/out-system USE_RBE=false T110_SOONG_GOGC=30 NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j2 SystemUI
candidate="$project/evidence/offline-v40/systemui-candidate"
mkdir -p "$candidate"
cp "$base/out-system/target/product/t110_bringup/system/system_ext/priv-app/SystemUI/SystemUI.apk" "$candidate/SystemUI.apk"
cp "$log" "$candidate/build.log"
sha256sum "$candidate/SystemUI.apk"
echo SYSTEMUI_NOTIFICATION_CLIP_COMPILED
