#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
name=${1:-lineage20-rom-v1}
[[ "$name" =~ ^lineage20-rom-v[0-9]+$ ]]
log=${2:-system-image-20261105T185011Z.log}
[[ "$log" =~ ^system-image-[0-9]{8}T[0-9]{6}Z.log$ ]]
destination="$project/artifacts/$name"
test ! -e "$destination"
mkdir "$destination"
image="$base/out-system/target/product/t110_bringup/system.img"
native="$base/export-$name"
test ! -e "$native"
mkdir "$native"
cp --reflink=auto "$image" "$native/system.img"
simg2img "$native/system.img" "$native/system.raw.img"
python3 "$project/scripts/verify_system_image_fit.py" "$native/system.raw.img" --report "$native/system-verification.json"
cp "$native/system.img" "$native/system.raw.img" "$native/system-verification.json" "$destination/"
cp "$base/out-system/target/product/t110_bringup/root/init.environ.rc" "$project/work/core-boot/init.environ.rc"
cp "$base/logs/$log" "$destination/system-build.log"
debugfs -R 'stat /system/vendor/lib/libGAL.so' "$native/system.raw.img" 2>&1
debugfs -R 'ea_list /system/vendor/lib/libGAL.so' "$native/system.raw.img" 2>&1
debugfs -R 'ls /system/vendor/bin/hw' "$native/system.raw.img" 2>&1
cd "$native"
sha256sum system.img system.raw.img > "$destination/SHA256SUMS"
