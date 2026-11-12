#!/system/bin/sh
# First boot check. The verified raw image is staged as a file under stock /data.
# Run inside the known v5 ramdisk. The stock SYSTEM partition is never mounted.
set -eu

[ "$(id -u)" = 0 ] && [ -f /t110-native-diagnostic ] || exit 2
[ "$(cat /sys/class/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL ]
[ "$(cat /sys/class/block/mmcblk0p15/size)" = 3115008 ]
[ "$(cat /sys/class/block/mmcblk0p16/size)" = 10760192 ]
[ "$#" = 2 ]
sha=$1
bytes=$2
case "$sha" in *[!0-9a-f]*) exit 2;; esac
case "$bytes" in ''|*[!0-9]*) exit 2;; esac
[ "${#sha}" = 64 ] && [ "$bytes" -gt 0 ] && [ "$bytes" -le 1594884096 ] || exit 2

work=/mnt/t110-stage-$$
mkdir -m 0700 "$work"
data="$work/data"
image_root="$work/image"
loop=/dev/block/loop0
root="$work/root"
mkdir "$data" "$image_root" "$root"
data_mounted=false
loop_attached=false
image_mounted=false
system_bound=false
apex_bound=false
dev_mounted=false
proc_mounted=false

cleanup() {
    set +e
    if "$proc_mounted"; then umount "$root/proc"; fi
    if "$dev_mounted"; then umount "$root/dev"; fi
    if "$apex_bound"; then umount "$root/apex"; fi
    if "$system_bound"; then umount "$root/system"; fi
    if "$image_mounted"; then umount "$image_root"; fi
    if "$loop_attached" && [ -e /sys/class/block/loop0/loop/backing_file ]; then losetup -d "$loop"; fi
    if "$data_mounted"; then umount "$data"; fi
    if [ -f "$root/linkerconfig/ld.config.txt" ]; then rm "$root/linkerconfig/ld.config.txt"; fi
    rmdir "$root/apex" "$root/system" "$root/linkerconfig" "$root/dev" "$root/proc" 2>/dev/null
    rmdir "$root" "$image_root" "$data" "$work" 2>/dev/null
}
trap 'status=$?; cleanup; exit "$status"' EXIT

mount -t ext4 -o ro,noload,nodev,nosuid,noexec /dev/block/mmcblk0p16 "$data"
data_mounted=true
image="$data/local/tmp/t110-stage-system.raw"
[ -f "$image" ] && [ ! -L "$image" ] && [ "$(stat -c %s "$image")" = "$bytes" ] || exit 2
[ "$(sha256sum "$image" | cut -d' ' -f1)" = "$sha" ]
echo STAGED_SYSTEM_HASH_VERIFIED

# Stock Android left this temporary file unlabeled. Android eng policy allows
# the loop worker to read shell_data_file. Change only this verified file's
# xattr, then return the backing filesystem to read-only before creating a loop.
if ! ls -Z "$image" | grep -q 'u:object_r:shell_data_file:s0'; then
    inode=$(stat -c %i "$image")
    umount "$data"
    data_mounted=false
    mount -t ext4 -o rw,nodev,nosuid,noexec /dev/block/mmcblk0p16 "$data"
    data_mounted=true
    [ -f "$image" ] && [ ! -L "$image" ] && [ "$(stat -c %i "$image")" = "$inode" ] || exit 2
    chcon u:object_r:shell_data_file:s0 "$image"
    sync
    mount -t ext4 -o remount,ro /dev/block/mmcblk0p16 "$data"
fi
ls -Z "$image" | grep 'u:object_r:shell_data_file:s0'

[ -b "$loop" ] && [ "$(cat /sys/class/block/loop0/dev)" = 7:0 ] || exit 2
losetup -r "$loop" "$image"
loop_attached=true
[ "$(cat /sys/class/block/loop0/ro)" = 1 ]
mount -t ext4 -o ro,noload,nodev,nosuid "$loop" "$image_root"
image_mounted=true
echo T110_KERNEL_MOUNTED_SYSTEM_READ_ONLY

system="$image_root"
if [ -d "$image_root/system/bin" ]; then system="$image_root/system"; fi
[ -x "$system/bin/init" ] && [ -x "$system/bin/toybox" ] || exit 2
[ -d "$system/apex/com.android.runtime" ]
mkdir -p "$root/system" "$root/apex" "$root/linkerconfig" "$root/dev" "$root/proc"
mount --bind "$system" "$root/system"
system_bound=true
mount --bind "$system/apex" "$root/apex"
apex_bound=true
mount -t tmpfs -o mode=0755,nosuid,noexec tmpfs "$root/dev"
dev_mounted=true
mknod -m 0444 "$root/dev/urandom" c 1 9
mknod -m 0666 "$root/dev/null" c 1 3
mount -t proc -o ro,nodev,nosuid,noexec proc "$root/proc"
proc_mounted=true
cat > "$root/linkerconfig/ld.config.txt" <<'CONFIG'
dir.system = /system/bin

[system]
namespace.default.isolated = false
namespace.default.search.paths = /system/lib:/apex/com.android.runtime/lib/bionic:/apex/com.android.runtime/lib
CONFIG
chroot "$root" /apex/com.android.runtime/bin/linker --list /system/bin/init
chroot "$root" /apex/com.android.runtime/bin/linker /system/bin/toybox true
echo T110_SYSTEM_IMAGE_LINKER_AND_TOYBOX_PASS
