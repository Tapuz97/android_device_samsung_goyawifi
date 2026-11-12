#!/bin/bash
set -eu
echo 'RETIRED: this loop/DrvFS image suffered write failures. Use the T110Build WSL distro.' >&2
exit 4
mkdir -p /mnt/e /mnt/t110-lineage20
mountpoint -q /mnt/e || mount -t drvfs E: /mnt/e
image=/mnt/e/T110-build/lineage20.ext4.img
test -f "$image"
[ "$(blkid -s UUID -o value "$image")" = 08f93775-a14c-4213-8438-f90f198d75e4 ]
if ! mountpoint -q /mnt/t110-lineage20; then
 mount -o loop,noatime "$image" /mnt/t110-lineage20
fi
[ "$(findmnt -n -o UUID /mnt/t110-lineage20)" = 08f93775-a14c-4213-8438-f90f198d75e4 ]
df -h /mnt/t110-lineage20
