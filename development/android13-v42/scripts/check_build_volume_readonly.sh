#!/bin/bash
set -euo pipefail
uuid=897592f3-1bd0-4be7-8abf-2b090bb91093
dev=$(blkid -U "$uuid")
[ -b "$dev" ]
[ "$(blkid -s TYPE -o value "$dev")" = ext4 ]
[ "$(blkid -s UUID -o value "$dev")" = "$uuid" ]
if findmnt -rn -S "$dev" | grep -q .; then echo 'Refusing mounted filesystem'; exit 3; fi
label=${1:-readonly}
[[ "$label" =~ ^[a-z0-9-]+$ ]]
log="/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence/e-native-vhdx-fsck-$label.log"
echo "Read-only filesystem check: $dev UUID=$uuid"
set +e
timeout 300s /root/t110-build/host-tools/e2fsprogs-1.47.3/e2fsck/e2fsck -f -n "$dev" > "$log" 2>&1
status=$?
set -e
echo "E2FSCK_EXIT=$status" | tee -a "$log"
tail -n 30 "$log"
exit "$status"
