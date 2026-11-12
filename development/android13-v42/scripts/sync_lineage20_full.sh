#!/bin/bash
set -euo pipefail
echo 'RETIRED: the loop/DrvFS image is unverified after write failures. Use sync_lineage20_wsl.sh.' >&2
exit 4
work=/mnt/t110-lineage20
[ "$(findmnt -n -o UUID "$work")" = 08f93775-a14c-4213-8438-f90f198d75e4 ]
cd "$work/source"
.repo/repo/repo init -g default,-darwin --git-lfs
mkdir -p "$work/logs"
# On disk-constrained hosts a full source checkout must leave room for output.
free_kb=$(df -Pk "$work" | awk 'NR==2 {print $4}')
[ "$free_kb" -gt 157286400 ] || { echo 'Less than 150 GiB free before full source sync'; exit 3; }
.repo/repo/repo sync -c -j4 --no-clone-bundle --no-tags --fail-fast 2>&1 | tee "$work/logs/full-source-sync.log"
# pipefail is set by the invocation below / future callers.
.repo/repo/repo manifest -r -o "$work/manifest-pinned.xml"
