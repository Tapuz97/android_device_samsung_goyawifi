#!/bin/bash
set -euo pipefail
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
native=/root/t110-build/lineage20/frameworks/native
patch="$project/patches/0065-renderengine-t110-reuse-idle-swap-spares.patch"
if ! git -C "$native" apply --reverse --check "$patch" >/dev/null 2>&1; then
    git -C "$native" apply --check "$patch"
    git -C "$native" apply "$patch"
fi
for file in T110EglWindow.cpp T110EglWindow.h T110WindowSlots.h; do
    cp "$native/libs/renderengine/gl/$file" "$project/work/device/samsung/t110_bringup/graphics/$file"
done
export T110_BUILD_JOBS=2
log=/root/t110-build/logs/gpu-readback-probe-20261110.log
trap 'tail -16 "$log"' EXIT
bash "$project/scripts/build_native_bootstrap.sh" t110_gpu_readback_probe t110_graphic_import_probe > "$log" 2>&1
