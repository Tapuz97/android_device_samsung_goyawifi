#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
version=${1:-26}
case "$version" in 26) evidence=offline-v39;; 27) evidence=offline-v40;; *) exit 3;; esac
native="$base/export-lineage20-rom-v$version"
destination="$project/artifacts/lineage20-rom-v$version"
logname=${2:-system-image-20261109T173012Z.log}
[[ "$logname" =~ ^system-image-[0-9]{8}T[0-9]{6}Z.log$ ]]
log="$base/logs/$logname"
grep -q 'build completed successfully' "$log"
mkdir -p "$native" "$destination"
if [ ! -e "$native/system.raw.img" ]; then
    simg2img "$base/out-system/target/product/t110_bringup/system.img" "$native/system.raw.img"
fi
python3 "$project/scripts/verify_system_image_fit.py" "$native/system.raw.img" --report "$native/system-verification.json"
python3 "$project/scripts/verify_native_wallpaper_system.py" --version "$version" --evidence "$evidence"
cp "$native/system.raw.img" "$native/system-verification.json" "$destination/"
cp "$log" "$destination/system-build.log"
cd "$destination"
sha256sum system.raw.img > SHA256SUMS
echo NATIVE_WALLPAPER_ROM_EXPORTED_AND_VERIFIED
