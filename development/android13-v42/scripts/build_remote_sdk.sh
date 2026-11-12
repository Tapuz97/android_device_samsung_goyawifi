#!/bin/bash
set -euo pipefail
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
export T110_BUILD_JOBS=2
export NINJA_ARGS="-k0"
# Resource tools consume the metadata normally written by Make main.mk, which
# --soong-only deliberately skips. This labels the internal component build.
mkdir -p /root/t110-build/out-native/soong
if [ ! -e /root/t110-build/out-native/soong/build_number.txt ]; then
    printf 'eng.root.%s' "$(date -u +%Y%m%d.%H%M%S)" > /root/t110-build/out-native/soong/build_number.txt
fi
log=/root/t110-build/logs/remote-sdk-driver-20261110.log
trap 'tail -18 "$log"' EXIT
bash "$project/scripts/build_native_bootstrap.sh" org.lineageos.platform lights.mrvl t110_lights_probe android.hardware.light@2.0-service android.hardware.light@2.0-impl > "$log" 2>&1
echo SDK_MODULE_COMPILED
