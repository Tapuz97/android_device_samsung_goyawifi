#!/bin/bash
set -euo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || { echo 'Run only in T110Build'; exit 3; }
work=/root/t110-build
cd "$work/lineage20"
mkdir -p "$work/logs"
exec > >(tee "$work/logs/full-source-sync.log") 2>&1
test "$(findmnt -n -o FSTYPE /)" = ext4
free_kb=$(df -Pk / | awk 'NR==2 {print $4}')
[ "$free_kb" -gt 157286400 ] || { echo 'Less than 150 GiB free before source sync'; exit 3; }
.repo/repo/repo init -g default,-darwin --git-lfs
.repo/repo/repo sync -c -j4 --no-clone-bundle --no-tags --fail-fast
.repo/repo/repo manifest -r -o "$work/manifest-pinned.xml"
