#!/bin/bash
set -eu
echo 'RETIRED: use the native T110Build WSL virtual disk on E:.' >&2
exit 4
mkdir -p /mnt/e /mnt/t110-lineage20
mountpoint -q /mnt/e || mount -t drvfs E: /mnt/e
image=/mnt/e/T110-build/lineage20.ext4.img
test -f "$image"
test "$(stat -c %s "$image")" = 450971566080
if blkid "$image"; then echo 'Already formatted - refusing'; exit 3; fi
mkfs.ext4 -F -m 0 -L T110_LINEAGE20 -E lazy_itable_init=1,lazy_journal_init=1 "$image"
mount -o loop,noatime "$image" /mnt/t110-lineage20
df -h /mnt/t110-lineage20
