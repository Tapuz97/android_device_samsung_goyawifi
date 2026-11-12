#!/bin/bash
set -euo pipefail
uuid=897592f3-1bd0-4be7-8abf-2b090bb91093
dev=$(blkid -U "$uuid")
[ -b "$dev" ]
[ "$(blkid -s TYPE -o value "$dev")" = ext4 ]
[ "$(blkid -s UUID -o value "$dev")" = "$uuid" ]
if findmnt -rn -S "$dev" | grep -q .; then echo 'Refusing mounted filesystem'; exit 3; fi
evidence='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence'
checker=/root/t110-build/host-tools/e2fsprogs-1.47.3/e2fsck/e2fsck
undo=/root/t110-build/host-tools/t110-build-after-enclosure-journal.e2undo
if [ "${1:-}" = repair ]; then
    grep -qx 'JOURNAL_REPLAY_EXIT=0' "$evidence/e-native-vhdx-journal-replay.log"
    grep -qx 'E2FSCK_EXIT=4' "$evidence/e-native-vhdx-fsck-after-journal-replay.log"
    undo=/root/t110-build/host-tools/t110-build-after-enclosure-fsck.e2undo
    [ ! -e "$undo" ]
    log="$evidence/e-native-vhdx-preen-repair.log"
    set +e
    "$checker" -p -f -z "$undo" "$dev" > "$log" 2>&1
    status=$?
    set -e
    echo "PREEN_EXIT=$status" | tee -a "$log"
    tail -n 22 "$log"
    [ "$status" -le 1 ]
    exec bash "$(dirname "$0")/check_build_volume_readonly.sh" after-enclosure-repair
fi
[ ! -e "$undo" ]
set +e
"$checker" -p -E journal_only -z "$undo" "$dev" > "$evidence/e-native-vhdx-journal-replay.log" 2>&1
status=$?
set -e
echo "JOURNAL_REPLAY_EXIT=$status" | tee -a "$evidence/e-native-vhdx-journal-replay.log"
tail -n 18 "$evidence/e-native-vhdx-journal-replay.log"
[ "$status" -le 1 ]
bash "$(dirname "$0")/check_build_volume_readonly.sh" after-journal-replay
