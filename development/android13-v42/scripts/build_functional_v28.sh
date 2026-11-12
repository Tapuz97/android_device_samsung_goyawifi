#!/bin/bash
set -euo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || exit 3
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
evidence="$project/evidence/offline-v41"
mkdir -p "$evidence"
export T110_SYSTEM_LOG_STAMP=$(date -u +%Y%m%dT%H%M%SZ)
export T110_SYSTEM_JOBS=2
printf '%s\n' "system-image-$T110_SYSTEM_LOG_STAMP.log" > "$evidence/system-build-log-name.txt"
driver=/root/t110-build/logs/functional-v28-driver.log
trap 'tail -18 "$driver"' EXIT
bash "$project/scripts/build_system_image.sh" > "$driver" 2>&1
echo FUNCTIONAL_V28_SYSTEM_BUILD_COMPLETED
