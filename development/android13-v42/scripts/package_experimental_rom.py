"""Package the verified v8 system and v18 boot for this tablet's TWRP."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / 'releases/lineage-20.0-20261106-UNOFFICIAL-SM-T110-experimental'
out.mkdir(parents=True, exist_ok=False)
system = root / 'artifacts/lineage20-rom-v8/system.raw.img'
boot = root / 'artifacts/android13-full-v18/KERNEL.img'
pair = json.loads((boot.parent / 'system-pair.json').read_text())
for path, expected in [(system, pair['system_sha256']), (boot, pair['boot_sha256'])]:
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected

installer = r'''#!/sbin/sh
set -eu
export PATH=/sbin:/system/bin:/system/xbin
fd="$2"
zip="$3"
ui() { echo "ui_print $*" > /proc/self/fd/"$fd"; echo ui_print > /proc/self/fd/"$fd"; }
fail() { ui "INSTALL ABORTED: $*"; exit 1; }
test -x /sbin/recovery || fail 'TWRP is required'
test "$(id -u)" = 0 || fail 'Root recovery required'
test "$(cat /sys/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL || fail 'This package is pinned to Gal SM-T110'
test "$(cat /sys/class/block/mmcblk0p10/start)" = 163840 || fail 'BOOT layout differs'
test "$(cat /sys/class/block/mmcblk0p10/size)" = 32768 || fail 'BOOT size differs'
test "$(md5sum /dev/block/mmcblk0p9 | cut -d' ' -f1)" = cd9793e1ee8f284c9056b225885b5b1a || fail 'Recovery differs'
test -z "$(losetup -a)" || fail 'A loop image is currently in use'
grep -q ' /data ' /proc/mounts || mount /data
grep -q '^/dev/block/mmcblk0p16 /data ext4 ' /proc/mounts || fail 'Unexpected userdata mount'
ui 'SM-T110 Android 13 experimental ROM: display and boot completion unresolved.'
mkdir -p /data/local/tmp
dest=/data/local/tmp/t110-rom-system.raw
incoming=/data/local/tmp/t110-rom-system.installing
test ! -e "$incoming" || fail 'An earlier incoming install exists; preserve it for review'
unzip -p "$zip" boot.img > /tmp/t110-rom-install-boot.img
test "$(md5sum /tmp/t110-rom-install-boot.img | cut -d' ' -f1)" = 29c11a3436510ed2b3277035c8853088 || fail 'BOOT payload hash mismatch'
if test -f "$dest" && test "$(md5sum "$dest" | cut -d' ' -f1)" = d768d098d329c339de7fd6bdd3567b9f; then
    ui 'Matching system image already installed.'
else
    free=$(df -k /data | tail -n 1 | awk '{print $(NF-2)}')
    test "$free" -gt 1580000 || fail 'Need at least 1.51 GiB free userdata space'
    ui 'Extracting and verifying system image...'
    unzip -p "$zip" system.raw.img > "$incoming" || fail 'System extraction failed'
    test "$(md5sum "$incoming" | cut -d' ' -f1)" = d768d098d329c339de7fd6bdd3567b9f || fail 'System payload hash mismatch'
    mv "$incoming" "$dest"
    sync
fi
old=$(md5sum /dev/block/mmcblk0p10 | cut -d' ' -f1)
case "$old" in
  7847f1b7e68e49e9ca590e052f0f76c4|c0bb2086abdb5c7eb285e6abca369d0c|29c11a3436510ed2b3277035c8853088) ;;
  *) fail 'Unrecognized installed BOOT; no BOOT write performed' ;;
esac
backup=/data/local/tmp/t110-boot-before-rom-$old.img
if test ! -e "$backup"; then
    dd if=/dev/block/mmcblk0p10 of="$backup" bs=4096 count=4096
fi
test "$(md5sum "$backup" | cut -d' ' -f1)" = "$old" || fail 'BOOT backup hash mismatch'
ui 'Installing matching kernel and startup image...'
dd if=/tmp/t110-rom-install-boot.img of=/dev/block/mmcblk0p10 bs=4096 count=4096
sync
test "$(md5sum /dev/block/mmcblk0p10 | cut -d' ' -f1)" = 29c11a3436510ed2b3277035c8853088 || fail 'BOOT readback mismatch; stay in TWRP'
test "$(md5sum /dev/block/mmcblk0p9 | cut -d' ' -f1)" = cd9793e1ee8f284c9056b225885b5b1a || fail 'Recovery readback mismatch'
ui 'Experimental ROM installed. Original SYSTEM and TWRP preserved.'
ui 'No automatic reboot. This build is not a working daily-use ROM.'
'''
readme = '''# SM-T110 LineageOS 20 / Android 13 experimental ROM

This is the actual v8 Android system image paired with the v18 kernel/startup
image, packaged for the existing TWRP on Gal's SM-T110. It is not boot-complete:
the previous graphics-fixed trial still showed the Samsung logo. The latest
trial was stopped at the user's request. No usable Android UI is validated.

The package includes the retained GPU-buffer ownership fix, the stock shader
compiler, disabled shader warmup, enforcing SELinux and persistent boot logs.
Audio currently uses a silent stub. Wi-Fi, media and normal app use are not
validated. The installer itself has not been executed on hardware.

Installation layout: the system image is stored in userdata at
/data/local/tmp/t110-rom-system.raw and mounted read-only by the included boot
image. Android has a separate t110-rom-data directory. Original SYSTEM and
recovery partitions remain untouched. A ten-minute watchdog returns an
incomplete boot to recovery. This is an engineering ROM, not a conventional
SYSTEM-partition installation.

If explicitly choosing to install later: copy the ZIP to a microSD card or USB
OTG storage, open TWRP Install, select it and swipe. Do not wipe or format data:
the ROM image lives there. The installer is pinned to this tablet's CID and
existing recovery, verifies payloads, backs up BOOT, and verifies BOOT readback.
No additional installation is needed for the tablet currently holding v18/v8.

Recovery: enter TWRP with Power + Home + Volume Up. The verified original stock
BOOT is retained on the PC at backups/20261104T201457Z/KERNEL.img; restoring that
BOOT returns to the preserved stock SYSTEM. Do not flash another model's boot.
'''
(out / 'README.md').write_text(readme, encoding='utf-8')
(out / 'update-binary').write_bytes(installer.encode())
pair.update(package_status='EXPERIMENTAL_NOT_BOOT_COMPLETE', installer_hardware_tested=False)
(out / 'manifest.json').write_text(json.dumps(pair, indent=2) + '\n', encoding='utf-8')
archive = out / (out.name + '.zip')
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
    z.write(system, 'system.raw.img')
    z.write(boot, 'boot.img')
    info = zipfile.ZipInfo('META-INF/com/google/android/update-binary')
    info.create_system = 3
    info.external_attr = 0o100755 << 16
    z.writestr(info, installer)
    z.writestr('META-INF/com/google/android/updater-script', '# Installation is handled by update-binary.\n')
    z.writestr('README.md', readme)
    z.writestr('manifest.json', json.dumps(pair, indent=2) + '\n')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name, expected in [('system.raw.img', pair['system_sha256']), ('boot.img', pair['boot_sha256'])]:
        with z.open(name) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
(out / 'SHA256SUMS').write_text(digest + '  ' + archive.name + '\n')
print(json.dumps(dict(package=str(archive.resolve()), bytes=archive.stat().st_size, sha256=digest, zip_crc_and_payload_hashes='PASS')))
