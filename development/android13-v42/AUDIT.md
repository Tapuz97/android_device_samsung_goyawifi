# SM-T110 Android 13 bring-up audit

Date: 2026-11-05. Current status: SYSTEM read-fault repair verified; complete post-repair SYSTEM backup, full main-area eMMC read scan and stock boot/file verification passed. TWRP installed. Offline kernel backports compile and pass 18 focused ARM QEMU checks; no Android 13 userspace built or booted. See CURRENT-STATUS.md and STORAGE-REPAIR.md. Older sections below retain their original chronology.

## Result

The visyone lineage-20.0 attempt is not a complete Android 13 port. It mixes a renamed standalone T110 device tree with the older T110 common tree and KitKat hardware libraries. Its manifest fetches the common trees, but its standalone BoardConfig/product do not inherit those trees. Consequently, inspecting only the common BoardConfig gives a misleading picture of what would actually build.

The T210 is a useful Marvell donor. The cmlt02 CM13 device README explicitly calls its tree incomplete and says it should contain files needed for recovery. Neither its name nor its Android branch establishes a working Android 6 tablet build.

## Sources and reproducibility

Eight shallow source checkouts are under `sources/`. Exact repository URLs and revisions are in `sources.lock.json`. Original checkouts are unchanged. The working T110 device is under `work/device/samsung/goyawifi`. Its changes are exported in `patches/0001-product-and-source-wiring.patch`.

Primary upstreams:

- https://github.com/visyone/android_platform_manifest/tree/lineage-20.0
- https://github.com/visyone/android_device_samsung_goyawifi/tree/lineage-20.0
- https://github.com/visyone/android_device_samsung_goya-common/tree/lineage-20.0
- https://github.com/visyone/android_kernel_samsung_goya/tree/lineage-20.0
- https://github.com/T210-dev/android_device_samsung_lt02wifi/tree/cm-11.0
- https://github.com/cmlt02/android_device_samsung_lt02wifi/tree/creeper-1.0
- https://github.com/cmlt02/Marvell_Patches

Raw source snapshots under `evidence/` compare the candidate kernel with LineageOS 20 init, Binder, ADB and zygote. These are audit inputs, not a complete Android checkout.

## Fixed in the working tree

1. Register `lineage.mk` in PRODUCT_MAKEFILES; lunch choices alone do not register a product.
2. Inherit Android's full_base product before the device configuration.
3. Match TARGET_KERNEL_SOURCE to the manifest's `kernel/samsung/goya`.
4. Select the existing `cyanogenmod_goyawifi_defconfig` instead of the recovery defconfig. This is only an Android baseline; its missing features are listed below.
5. Match vendor inheritance to the actual `vendor/samsung/goya/goya-vendor.mk`; remove a reference to a vendor BoardConfig file absent from that repository.
6. Copy audio configuration files as files rather than naming their paths as modules.
7. Use the ramdisk module names already declared by rootdir/Android.mk and remove the nonexistent init.board.rc reference.
8. Correct the malformed `systemights.pxa988/etc` destinations and append device properties rather than replacing inherited properties.

## Build blockers still requiring implementation

| Finding | Evidence | Required work |
|---|---|---|
| Original manifest replaces Android 13 libhardware and libhardware_legacy with old forks | los13-manifest/roomservice.xml; evidence/los13-hal-head.txt points at a 2014 HWC patch | Keep modern upstream libraries; port required Marvell extensions deliberately. Do not replace the entire modern HAL foundation. |
| Binary paths are used as PRODUCT_PACKAGES entries, without corresponding prebuilt modules | device_goyawifi.mk | Define valid modules only for necessary compatible blobs; audit ELF dependencies and symbols. Prefer platform software codecs over old Stagefright binaries. |
| Old SELinux policy and old init/fstab layout | device/rootdir, device/sepolicy | Rework policy, root/system mount arrangement, init imports, service domains, property expansion and USB startup for Android 13. Select a deliberate legacy-partition boot design after reading the tablet. |
| Vendor tree provenance does not establish binary compatibility | goya-vendor.mk even retains a T210 generator comment | Compare extracted T110 binaries with donor binaries. Hashes and ELF imports are needed before choosing replacements. |
| README still prescribes JDK 6 | los13-manifest/README.md | Use the Android 13 build toolchain and Linux prerequisites; the inherited README is not a working build recipe. |

## Kernel and early-boot blockers

The candidate kernel identifies itself as Linux 3.4.5. Its Android defconfig has CONFIG_SECURITY, CONFIG_CGROUPS, CONFIG_EXT4_FS_SECURITY and CONFIG_SECCOMP disabled. CONFIG_USB_FUNCTIONFS is disabled, but that standalone gadget option does not govern the FunctionFS code included directly by Samsung android.c.

- **SELinux:** modern init loads policy and treats failures as fatal. Permissive mode does not substitute for absent kernel SELinux support. Enable the required kernel security/filesystem-label features and assess the old SELinux implementation against Android 13 policy before trying userspace boot.
- **ADB:** the old USB rc configures Samsung's `adb` gadget function. Modern ADB's USB implementation uses FunctionFS. Samsung android.c already includes f_fs.c and registers ffs_function. Gadget composition, supported descriptor versions, endpoints, init mount and permissions still need modern-ADB validation.
- **Cgroups:** enable and validate the controllers expected by the chosen Android task profiles. The current candidate disables cgroups entirely.
- **Seccomp:** kernel/seccomp.c implements only strict mode (`NR_SECCOMP_MODES 1`). Turning on CONFIG_SECCOMP cannot supply the missing filter implementation. A backport and ARM syscall integration are needed for normal Android 13 sandboxing. Zygote has a permissive-mode diagnostic bypass in some paths; that is not completion of the port.
- **Binder:** the old driver advertises protocol 7. Android 13 headers support protocol 7 under BINDER_IPC_32BIT and protocol 8 otherwise. Align the configured ABI and transaction features; do not claim that the version numbers alone prove impossibility. New transaction/security-context support still requires auditing/backporting.
- **Syscalls:** the old ARM syscall table lacks entries for newer calls such as memfd_create and getrandom. Audit real call sites and fallbacks; absence alone does not establish which call is the first boot failure.

## T210 donor assessment

Both board configurations use ARMv7/NEON Cortex-A9, Marvell hardware, Vivante gralloc integration and related legacy framebuffer paths. The T210 patch script changes SurfaceFlinger/BufferQueue behavior, libhardware HWC structures and system/core multimedia support. Those changes are useful design references, not a patch series that can be blindly cherry-picked into Android 13.

The T110 common-tree HWC patch adds `alpha` to hwc_layer_1 and vendor function pointers such as fbPrePost/stretchBlit/getBackBuffer. This changes layout and expected behavior across the binary boundary. A modern composer adapter or explicitly compatible software-rendering path must be designed and tested before expecting SurfaceFlinger to start.

Keep T110 board drivers and validate its boot-image header/addresses against the actual stock boot image. The standalone and common T110 configurations disagree about addresses. T210 boot/recovery partition sizes are 12 MiB; the T110 trees specify 16 MiB. Never use donor partition geometry as device evidence.

## Next executable milestones

1. Read the connected tablet's identity, kernel, boot command line, partition links and framebuffer/USB state with `scripts/inspect_tablet.py`. This script does not request root or modify the tablet. Obtain stock/recovery backup images separately before boot-image work.
2. Reproduce a T110 kernel/recovery baseline with its matching old cross-toolchain. Capture build logs and verify image sizes/header against the hardware. A recovery boot with logs/ADB is the first hardware checkpoint.
3. Backport/enable kernel support in independent changes, validating that the baseline still boots. Establish modern ADB and init before spending time on the Android UI.
4. Replace the old whole-library manifest overrides, resolve modules, then run the full Android product configuration/build. Implement a minimal software-rendered graphics path or a tested Marvell composer adaptation.
5. Progress from init + ADB to servicemanager/Binder, zygote, SurfaceFlinger, launcher; only then add audio, wireless, camera and acceleration individually.

Android 13 remains an experimental target, not a promised working version. A lower Android baseline can be useful to test donor hardware support, but should not be presented as the requested final modern OS.

## Environment and validation

WSL Ubuntu works. At inspection it reported ~235 GiB virtual free space, but its Windows C: host had only ~122 GiB physically free; D: had ~169 GiB. Do not interpret the virtual disk's free-space figure as available physical capacity. The checked Ubuntu environment has gcc, but make, repo and Java were not found in PATH. No large Android sync or package installation was started.

Run `python scripts/preflight.py`. It writes preflight.json and deliberately exits 2 while unresolved findings remain. It is a static audit, not a compiler or boot test. Five wiring checks pass after the initial fixes. `inspect_tablet.py --help` was exercised; device collection is pending an authorized connected SM-T110.

No flashable image has been produced. No tablet partition has been modified.

## Hardware inspection completed 2026-11-04

ADB authorization was accepted and the read-only collector ran successfully. Raw results: `device-reports/20261104T195441Z.json`. Device: SM-T110/goyawifi, stock Android 4.2.2, build and bootloader T110XXUANI7, Linux 3.4.5-2751957. User reports no root or TWRP; shell runs as uid 2000.

Measured partition sizes match the source tree: KERNEL=p10 and RECOVERY=p9 are each 16,777,216 bytes; SYSTEM=p15 is 1,594,884,096 bytes; USER=p16 is 5,509,218,304 bytes. Machine-readable comparison: `stock/T110XXUANI7/partition-verification.json`.

Stock /proc/filesystems lists functionfs, although /dev/usb-ffs is absent and the running ADB transport uses /dev/android_adb. The source includes FunctionFS within Samsung android.c despite the standalone CONFIG_USB_FUNCTIONFS option being disabled; modern FunctionFS ADB is still untested. The GPU device is /dev/graphics/galcore, not /dev/galcore. Framebuffer reports GFX Layer with virtual size 1024x1800.

The stock kernel does not expose /proc/config.gz. /proc/cmdline is permission denied, and root init/fstab files are not shell-readable. Stock boot/recovery images remain to be obtained through matching firmware or an explicitly authorized privileged backup workflow. No boot-header address has yet been verified from the tablet.

Readable stock HAL, EGL and supporting libraries were pulled to `stock/T110XXUANI7/system`, with SHA-256 inventory. readelf confirms ARM ELF32 binaries. Stock hwcomposer.mrvl.so, gralloc.mrvl.so, camera.mrvl.so and power.mrvl.so exactly match the four files in the visyone device tree. Thus their provenance is verified for this firmware, while Android 13 ABI compatibility remains unresolved. `elf-audit.json` records DT_NEEDED dependencies; graphics depends on libHWComposerGC, libGAL, libgcu and legacy Android libraries. These local binaries are reference material, not a flashable package.

Collector caveat: this old ADB/shell combination can return host exit code 0 even when individual commands fail. Raw diagnostic text was inspected; missing uname/getenforce and permission failures are not counted as successful checks.

## Stock images and kernel compilation, 2026-11-04

Downloaded firmware SM-T110_T110XXUANI7_T110OJVANI1.zip from Internet Archive. AP matches the tablet; OJV is a different regional CSC, not a universal global firmware. No CSC installation is necessary for this port. Archive MD5 matches catalog; extracted CODE entry passes ZIP CRC and its appended tar MD5. firmware/verified-images.json records SHA-256 and boot geometry. This is a matching-build restore reference, not yet a byte-exact dump of this tablet.

Stock boot and recovery: kernel 0x10008000, ramdisk 0x11000000, tags 0x10000100, page size 2048, no DT payload, blank header command line. The standalone BoardConfig base/offset agrees; its inherited hard-coded cmdline still needs comparison with a privileged /proc/cmdline read.

Successfully built the unmodified visyone kernel 3c50b450af74d42f8c5d360c692f71002b3bb0af with cyanogenmod_goyawifi_defconfig and AOSP arm-eabi GCC 4.6 toolchain b4ecd7806d8f46cddeacaf9f8de92c191fb266e4. WSL build directory /root/t110-build. Artifacts and log: artifacts/kernel-baseline. zImage SHA-256 df0b2bce7fa3db9e8566c78e4ce389562f816e8ee428c5661b75627e263aac51. Host gcc11 failed on missing compiler-gcc11.h; the period-correct compiler succeeded. This proves compilation only, not hardware boot or Android 13 compatibility.

Original gr8nole T110 TWRP 2.7.0.1 obtained from developer AFH file 23329332407589909; MD5 92c58f5d9e7cf0243623668d2449b676 matches listing. Tar contains only recovery.img; header geometry matches stock; ramdisk identifies SM-T110/goyawifi and fstab uses confirmed partition names. Stock recovery reference retained before recovery replacement. A dump taken after TWRP installation will contain TWRP in RECOVERY, not the original stock recovery.

## Recovery hardware checkpoint

User flashed gr8nole TWRP 2.7.0.1 in Odin and reported PASS. Initial reboot entered stock Android. `adb reboot recovery` then successfully started TWRP: recovery.log reports version 2.7.0.1, framebuffer 1024x600, and ADB shell uid=0. No wipe, root installer or system modification was requested. TWRP automatically mounts data/cache RW; system was unmounted during backup.

Firmware backup script `scripts/dump_firmware.py` checks model, root, TWRP log, partition mapping, byte counts and remote/local MD5, and records SHA-256. Old adbd lacks exec-out; transfer uses ADB sync/pull directly from block devices. USER and CACHE are excluded. EFS remains local. Backup run: backups/20261104T201457Z. The first failed exec-out attempt produced only a zero-byte partial file in 20261104T201431Z; it is not a backup.

Dumped KERNEL begins with an exact byte-for-byte match to the entire downloaded stock boot.img, proving matching AP boot content despite the CSC difference. The rest of KERNEL is partition padding. `stock-boot-comparison.json` records comparison. RECOVERY after installation is TWRP, not original stock recovery.

The kernel diagnostic package `artifacts/test-baseline-kernel-UNTESTED.tar.md5` contains only boot.img and remains unflashed. `artifacts/restore-stock-boot.tar.md5` is the separate rollback. `artifacts/TEST-PLAN.md` describes the checkpoint. The legacy repacker validates the original Android SHA-1 image ID, preserves header geometry and trailing bytes, checks partition size, and passed an exact original-image round trip. This validates packaging, not hardware boot.

## Security/cgroup kernel candidate compiled

A second experimental zImage also compiled successfully after enabling SELinux as the default LSM, auditing, cgroup freezer/device/cpuset/CPU accounting/scheduling, ext4 security labels, tmpfs xattrs, and /proc/config.gz. The first configuration pass left DEFAULT_SECURITY_DAC selected; this was corrected to DEFAULT_SECURITY_SELINUX and rebuilt successfully. This candidate has not been flashed. Reproduction script: scripts/build_kernel_security.sh. Configuration delta: patches/0002-kernel-security-config.diff. Binary, full config, build log and provenance: artifacts/kernel-security. SHA-256 61f1c77782516c86f8f05cb96c9e365eb96e6c9ff847ee7b29ff0c90a730ae0a. Seccomp filter support and modern userspace/Binder/policy integration remain unresolved; do not equate enabling old SELinux with full Android 13 compatibility.

## Material backup limitation: SYSTEM read errors

Thirteen non-USER/non-CACHE firmware partitions verified; SYSTEM transfer stopped at 1,026,928,640 of 1,594,884,096 bytes with mmcblk0 DATA TIMEOUT (-110) / I/O errors. A bounded read reproduced failure at absolute sector 3398360 while nearby sectors were readable. A bounded continuation encountered another error at logical SYSTEM block 250728. Stop treating SYSTEM as a complete backup. No zero-filled or stock-reconstructed data has been labeled as an exact dump.

Read-only debugfs on the partial image maps first failing SYSTEM 4K block 250715 to inode 1253, /hdic/zh.hdb (Chinese dictionary), extent 249237-250840. This explains why stock Android may still boot; it does not establish whether media wear or recovery-kernel behavior causes the failure. No filesystem repair or format has been performed.

Both 4 MiB eMMC boot hardware regions and the 4 MiB prefix before partition 1 were pulled and checksum-verified separately (emmc-regions.json). Prefix dd wrote only to recovery RAM /tmp. This preserves partition-table/boot-region evidence in addition to named firmware partitions.

Prepared, but not flashed, artifacts/twrp-stock-kernel-diagnostic-UNTESTED.tar.md5: existing working TWRP ramdisk with verified stock AP kernel, recovery.img only. This is the next controlled A/B test for the read failure. The original verified gr8nole recovery package remains the rollback. Defer testing the newly compiled OS kernel until this storage behavior is understood.

## Recovery reboot loop resolved (2026-11-04)

After normal/download/power-off attempts returned to TWRP, live checks confirmed KERNEL and RECOVERY MD5 still matched the original backups: stock boot and original gr8nole TWRP. The diagnostic recovery had NOT been flashed. Key sysfs reported RELEASE, /cache/recovery/command was absent, and last_kmsg showed a recovery-origin reboot. Goya kernel source supports the Samsung recovery_done reboot reason; the actual TWRP kernel binary also contains recovery_done/reboot-notifier strings.

`adb shell /sbin/reboot recovery_done` exited the loop. Windows re-enumerated VID_04E8 PID_6860 with normal Samsung MTP and the user confirmed the Android home/lock screen. No firmware write, format or wipe was used for this repair. Exact underlying persistent flag was not read directly; do not overstate the mechanism. Prior eMMC read errors remain unclassified pending a read of /system/hdic/zh.hdb under the stock kernel. Evidence: device-reports/boot-loop-20261104T203203Z.

## Stock-kernel read cross-check (2026-11-04)

After the user re-enabled USB debugging, ADB confirmed normal stock Android, sys.boot_completed=1, kernel 3.4.5-2751957. Pulling readable /system/hdic/zh.hdb (6,567,404 bytes) failed with remote I/O error after exactly 6,053,888 bytes. This matches the offset of the first failing block in the TWRP raw SYSTEM dump: (250715 - 249237) * 4096 = 6,053,888. The failure therefore reproduces under both stock Samsung and TWRP kernels at the same file location. A TWRP-only driver bug cannot explain it. The exact physical storage/controller cause is not yet diagnosed; no claim that reflashing repairs the device is justified.

Evidence: stock/T110XXUANI7/read-check/result.json; truncated file explicitly named zh.hdb.partial. Stock dmesg denied shell access. sysfs eMMC name 008GE0, manfid 0x11; life_time/pre_eol_info unavailable. The exposed date 02/1999 is raw driver output, not independently verified manufacture date. No further flash, format or wipe occurred. Installing a persistent Android root package is unnecessary for this cross-check: TWRP already provides root, and the stock file is shell-readable. The proposed stock-kernel TWRP diagnostic is no longer necessary solely to distinguish the two kernels' read behavior.


## Offline kernel port and validation checkpoint

See CURRENT-STATUS.md for the complete 2026-11-04 checkpoint, pinned source references, patch sequence, artifacts and remaining work. Latest candidate: artifacts/kernel-binder; 12 checks pass in artifacts/qemu-binder. Full stock system extraction and ELF dependency inventory are complete. The original seccomp/policy gaps are addressed in separate compiled candidates, not yet integrated into the Android product. Hardware experiments remain held because the stock-kernel SYSTEM read fault persists. No new flash, root installation, format or wipe occurred during this offline phase.


## Modern Binder transport milestone

Completed the separate Android common 3.18 Binder backport: independent device contexts, scatter-gather, PTR/FDA transport, Linux 3.4 compatibility and a reproduced context-manager authorization ordering fix. T110 and QEMU builds include Binder with compiler warnings enabled as errors. The T110 build explicitly disables unsupported USER_NS and checks that Kconfig did not omit Binder. All 18 focused emulator checks and 24 ABI comparisons pass. See BINDER-MODERN.md, artifacts/kernel-binder-modern, artifacts/qemu-binder-modern and patches/0008-binder-contexts-scatter-gather-backport.patch. Android userspace integration and tablet boot remain untested; no tablet action occurred during this milestone.

## 2026-11-05 storage blocker resolved

Restored four verified dictionary blocks from matching stock AP (16,384 bytes), with immediate direct readback. After reboot, all 7,818,182,656 main-area eMMC bytes read without error. Complete post-repair SYSTEM backup checksums passed. Stock Android booted and the entire dictionary hash matched stock under the Samsung kernel. The original partial dump remains incomplete and preserved. Physical cause remains unproven; storage hold cleared for controlled testing. See STORAGE-REPAIR.md and storage-diagnostics/LATEST-RESULT.json.
