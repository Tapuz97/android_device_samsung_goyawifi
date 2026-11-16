# Manual engineering installation — SM-T110 only

This is the established userdata-backed layout, **not a proven universal
installer**. An independent clean install on a second tablet is not qualified.
The read-only preflight helps reject mismatches; it is not an install test.
Do not run these steps on T111/T113/T116/T210 or merely assume a partition number.

The ROM ZIP is extracted on the computer. It is **not** a TWRP update ZIP or
Odin AP package. Never flash system.raw.img to physical SYSTEM. Do not use PIT,
Re-Partition, Nand Erase, Format Data or a generic GApps-flashing guide.

## 1. Recovery and files

Confirm the exact model on the tablet and in Download Mode. Keep its own stock
firmware/recovery route and personal-data backup. If TWRP is already working,
keep it. Otherwise use gr8nole's **T110.TWRP.2.7.0.1.tar.md5** in Odin AP/PDA,
Auto Reboot off and Re-Partition/Nand Erase off. After PASS, enter TWRP directly:
Power + Home + Volume Up; release Power at the Samsung logo, keep Home + Volume
Up held. Decline any offered SuperSU installation.

Choose Google-free or locally assembled Google edition before initial setup.
On Windows, run Python explicitly from the guide/tools folder:

```powershell
py -3 verify_modern_package.py path\to\ROM.zip
py -3 extract_rom.py path\to\ROM.zip extracted-rom
adb devices
py -3 preflight_t110.py --serial YOUR_TABLET_SERIAL
```

Use `adb -s YOUR_TABLET_SERIAL` throughout. If multiple devices are attached,
never omit `-s`. Mount **physical Data** in TWRP as ext4; do not format it.
Stop if any preflight check fails. At least2500MiB free is required before
staging, with additional room for an existing rollback and Android app data.

## 2. Verify mapping and save your own backups

Expected recovery mapping, checked by the preflight:

| Item | Path | Size |
|---|---|---|
| KERNEL/boot | /dev/block/mmcblk0p10 | 32768 sectors /16MiB |
| Recovery | /dev/block/mmcblk0p9 | 32768 sectors /16MiB |
| Physical userdata | /dev/block/mmcblk0p16 | 10760192 sectors |
| System container in recovery | /data/local/tmp/t110-lineage14-system.raw | 1594884096 bytes |
| Isolated Android data | /data/local/tmp/t110-lineage14-data | directory |

Save KERNEL and recovery to the computer before changing anything:

```text
adb -s YOUR_TABLET_SERIAL pull /dev/block/mmcblk0p10 stock-KERNEL.img
adb -s YOUR_TABLET_SERIAL pull /dev/block/mmcblk0p9 saved-RECOVERY.img
adb -s YOUR_TABLET_SERIAL shell sha256sum /dev/block/mmcblk0p10 /dev/block/mmcblk0p9
```

Compare these hashes with local `Get-FileHash`/`sha256sum`; keep the backups
private. If a system container or isolated data profile already exists, copy it
to the computer and verify it before continuing. Do not replace an active loop
backing file or follow symlinks. Never borrow another tablet's EFS/calibration.

## 3. Stage without overwriting the existing ROM

The following examples use a NEW staging directory. Replace the serial
placeholder and run only after the identity/geometry/backups above pass.

```text
adb -s YOUR_TABLET_SERIAL shell "test ! -e /data/local/tmp/t110-staging-20261116 && mkdir -p /data/local/tmp/t110-staging-20261116"
adb -s YOUR_TABLET_SERIAL push extracted-rom/system.raw.img.gz /data/local/tmp/t110-staging-20261116/
adb -s YOUR_TABLET_SERIAL push extracted-rom/boot.img /data/local/tmp/t110-staging-20261116/
adb -s YOUR_TABLET_SERIAL shell sha256sum /data/local/tmp/t110-staging-20261116/system.raw.img.gz /data/local/tmp/t110-staging-20261116/boot.img
```

Both hashes must match **your extracted manifest.json**. Decompress only after
they match; this writes a regular file, not a partition:

```text
adb -s YOUR_TABLET_SERIAL shell "/sbin/busybox gzip -dc /data/local/tmp/t110-staging-20261116/system.raw.img.gz > /data/local/tmp/t110-staging-20261116/system.raw.img"
adb -s YOUR_TABLET_SERIAL shell wc -c /data/local/tmp/t110-staging-20261116/system.raw.img
adb -s YOUR_TABLET_SERIAL shell sha256sum /data/local/tmp/t110-staging-20261116/system.raw.img
```

Require1594884096 bytes and the manifest's raw SHA256. If space is insufficient,
stop; do not erase a partition or your sole rollback to force it to fit.

## 4. Activate the checked container and matching boot

Only while still in recovery with loop0 unused:

- Preserve any existing system container under a unique backup name, after its
  host backup/hash has passed. The destination must not be a symlink.
- Move the verified staged `system.raw.img` to the exact system-container path
  in the table above. Never write it to `/dev/block/mmcblk0p15`.
- For a first install, create the isolated data directory if absent with
  owner1000:1000, mode0771. For an update of the same edition, preserve it. For
  an edition change, preserve the old directory under a unique backup name and
  create a new one; never format all physical userdata.

First-install directory creation (only if it does not already exist):

```text
adb -s YOUR_TABLET_SERIAL shell "test ! -e /data/local/tmp/t110-lineage14-data && mkdir /data/local/tmp/t110-lineage14-data && chown 1000:1000 /data/local/tmp/t110-lineage14-data && chmod 0771 /data/local/tmp/t110-lineage14-data"
```

Hash the final system-container path again. Then, and only with the confirmed
SM-T110 mapping, write the **matched16MiB boot.img** to KERNEL:

```text
adb -s YOUR_TABLET_SERIAL shell "dd if=/data/local/tmp/t110-staging-20261116/boot.img of=/dev/block/mmcblk0p10 bs=4096 && sync"
adb -s YOUR_TABLET_SERIAL shell sha256sum /dev/block/mmcblk0p10 /dev/block/mmcblk0p9
```

KERNEL must be
`93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2`.
Recovery must match **your own pre-write recovery hash**. Do not use the
ordinary unwrapped Android build-output boot image in place of the packaged one.
Do not write recovery, bootloader, PIT, EFS or physical SYSTEM in this ROM step.

## 5. Boot and check the actual screen

```text
adb -s YOUR_TABLET_SERIAL shell /sbin/reboot recovery_done
```

This handoff avoids the recovery-return issue observed with generic Reboot
System on our tablet. First boot can take several minutes while apps are
prepared. A later recovery screen is not a successful boot: confirm the actual
home/setup screen, correct colours and finger touch. Do not start erasing other
partitions to chase a boot loop.

If one short Power press opens Camera, disable the native double-press Power
camera shortcut; a physical key bounce was observed on the test device. Keep
hardware/onscreen navigation in the native Gestures & Navigation settings.

For Google edition, complete sign-in yourself and verify a compatible Play
Store app. Do not enter credentials while a screen recorder or diagnostics is
collecting the page. Google may perform account/setup checks; this does not
provide official OTA updates for this unofficial ROM.

After checking the installation and verified host rollback, disposable staging
copies can be removed. Keep your own boot/recovery/system/data backups. Never
wipe/format userdata after installation: it holds both the ROM and its data.
See ROLLBACK.md if boot or functionality fails.
