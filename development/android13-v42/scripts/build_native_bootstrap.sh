#!/bin/bash
set -eo pipefail
logdir=${T110_LOG_ROOT:-/root/t110-build/logs}
mkdir -p "$logdir"
log=$logdir/native-bootstrap-$(date -u +%Y%m%dT%H%M%SZ).log
exec > >(tee "$log") 2>&1
echo "Build log: $log"
root=${T110_SOURCE_ROOT:-/root/t110-build/lineage20}
# Default is the partial checkout; set T110_SOURCE_ROOT after the E: sync completes.
cd "$root"
mkdir -p device/samsung
cp -a '/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/work/device/samsung/t110_bringup' device/samsung/
export OUT_DIR=${T110_OUT_ROOT:-/root/t110-build/out-native}
# E: loop image reported I/O errors. Rebuild native tools on the internal ext4
# filesystem; do not reuse any output from the affected image.
free_kb=$(df -Pk "$(dirname "$OUT_DIR")" | awk 'NR==2 {print $4}')
[ "$free_kb" -gt 20971520 ] || { echo 'Less than 20 GiB free for native bootstrap'; exit 3; }
if [ "${WSL_DISTRO_NAME:-}" = Ubuntu ]; then
    host_free_kb=$(df -Pk /mnt/c | awk 'NR==2 {print $4}')
    [ "$host_free_kb" -gt 20971520 ] || { echo 'C: has less than 20 GiB free'; exit 3; }
    export ALLOW_MISSING_DEPENDENCIES=true
else
    unset ALLOW_MISSING_DEPENDENCIES
fi
export USE_RBE=false
source build/envsetup.sh
lunch lineage_t110_bringup-eng
if [ "$#" = 0 ]; then set -- t110_bionic_probe; fi
# These native probes are Soong modules. This supported mode avoids unrelated
# Make-only SDK packaging; it still validates each target's actual dependencies.
m --soong-only -j"${T110_BUILD_JOBS:-4}" "$@"
