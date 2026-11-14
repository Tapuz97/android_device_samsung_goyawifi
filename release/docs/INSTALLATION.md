# Engineering installation and recovery notes

**Publication status: draft. A clean installation on a second device has not
been qualified. This is the established layout/procedure, not a tested universal
one-click installer.** Keep stock recovery/boot/firmware backups appropriate to
your own tablet. Personal data is never included in this package.

## Layout

Only SM-T110 / goyawifi with the checked partition geometry is in scope:

| Purpose | Location | Expected geometry |
|---|---|---|
| KERNEL (boot) | /dev/block/mmcblk0p10 | 32768 sectors, 16777216 bytes |
| Recovery | /dev/block/mmcblk0p9 | preserved, not overwritten by ROM install |
| Physical userdata | /dev/block/mmcblk0p16 | 10760192 sectors |
| ROM system file in TWRP | /data/local/tmp/t110-lineage14-system.raw | 1594884096 bytes |
| Isolated Android data in TWRP | /data/local/tmp/t110-lineage14-data | directory |

Our tested tablet has a faulty SYSTEM partition (p15). This package never writes
it. Do not repartition, format /data, wipe SYSTEM or select Nand Erase. Formatting
userdata would erase both the system image and the isolated Android data.
The normal unwrapped Android build-output boot.img is incompatible with this
layout; use only the hash-matched boot.img in this release.

## Recovery setup (upstream procedure; separate from ROM)

If TWRP is already installed and working, retain it. Otherwise confirm the exact
SM-T110 model in Download Mode before using its recovery tar.md5 in Odin's AP
(PDA on older Odin) slot. Leave Re-Partition and Nand Erase off; Auto Reboot off.
After PASS, enter recovery directly with Power + Home + Volume Up. Release Power
at the Samsung logo while holding Home + Volume Up. Do not install an offered
SuperSU add-on. Original TWRP and the stock-kernel diagnostic are separate
artifacts; the diagnostic is not a generic upgrade recommendation.

## Verify and stage

1. Extract the engineering ROM ZIP on the computer. Run
   `python tools/verify_package.py .` there. It verifies compressed and raw system
   hashes, size and boot identity without connecting to or modifying a tablet.
2. In TWRP, select the correct device explicitly using `adb -s SERIAL` for every
   command. Verify root recovery ADB, model/device, block aliases and sector counts
   above. Mount physical userdata as /data, ext4; do not format it. If any identity,
   geometry, filesystem or storage check differs, stop and investigate.
3. Back up KERNEL and recovery to the computer, verify their complete SHA256
   hashes against hashes read on-device. Preserve any existing system image and
   isolated Android data. Do not publish these backups or device identifiers.
4. Confirm loop0 is unused and no Android instance is running. Allow roughly
   2.5 GiB free on physical userdata for staging the gzip, full image and boot,
   plus sufficient free space for the new data profile. Keep an old image on the
   host rather than deleting the sole rollback copy to make space.
5. Copy system.raw.img.gz and boot.img into a new staging directory on /data.
   Check their on-device SHA256 values against manifest.json. Decompress to a
   NEW regular file; verify its full size and hash before replacing the target
   system file. Never write the compressed file directly as a raw image.
6. Ensure /data/local/tmp exists as a real directory and create the isolated
   data directory only if absent. Preserve an existing 14.1 data directory.
   Rename the verified raw staging file to the exact ROM path above. Do not
   follow symlinks or use a mounted/active backing file.
7. Only after system verification, write the checked 16 MiB boot.img to KERNEL
   p10, sync, then hash the entire partition again. Verify recovery is unchanged.
   No command in this procedure writes recovery, bootloader, PIT, EFS or SYSTEM.

Our internal installer implements stricter identity and parent-image guards for
the original tablet. It is intentionally not presented as a universal installer.
The branch retains the exact bootstrap source and original engineering tools.

## First boot and boot-loop lesson

The established handoff from our old installed TWRP is:

```text
adb -s SERIAL shell /sbin/reboot recovery_done
```

Generic `adb reboot`, TWRP Reboot System and cold power-on previously returned to
recovery on the test device. Do not delete recovery or repeatedly reflash the
bootloader to work around this. Capture bounded logs if startup fails. The boot
bootstrap has a 20-minute safeguard; do not mistake a later recovery screen for
a successful Android boot. Confirm the actual visible UI and touch response.

## Rollback

Return to TWRP. Restore your matching saved system file and KERNEL image only
after checking their hashes and the same block mapping. Preserve the corresponding
data profile. On a tablet previously using stock partitions, restoring its own
stock KERNEL may return to its untouched stock SYSTEM, but that cannot work around
a physically unreadable SYSTEM partition. Do not restore another tablet's EFS,
serial/calibration data, or PIT. Restoring full stock firmware is a separate,
model-specific recovery procedure, not a universal repair for read faults.

GApps, OTA and normal-app root steps are deliberately not claimed working here;
see DOWNLOADS.md and RELEASE-CHECKLIST.md for the unresolved integration work.
