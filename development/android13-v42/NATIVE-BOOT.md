# Android 13 native boot checkpoint — 2026-11-05

**Current tablet state:** stock BOOT restored with full readback verified; stock Android 4.2.2 boot_completed=1 confirmed. Installed TWRP is unchanged. **Diagnostic v5 booted actual Android 13 init and root USB ADB on hardware.** This is a RAM-only native-userspace milestone, not a graphical/full OS boot.

V5 passed O_PATH/realpath, bionic subset, process-group create/inherit/kill/cleanup, Android 13 libbinder Parcel roundtrip, a 2,097,189-byte USB push/pull SHA256 match, and host ADB reconnection. Global SELinux was enforcing; the standard engineering recovery policy has permissive recovery/su domains, so these tests do not certify production enforcement. Logs and machine-readable results are in `hardware-tests/20261105-modern-init-v5/`.

## Completed hardware tests before this trial

Android 13 static bionic passes pthread/TLS, monotonic clock, eventfd/epoll, getentropy fallback and fork/exec on stock and the first patched kernel. Actual Android 13 libbinder passes a two-process Parcel roundtrip with its matching modern linker/libraries on the diagnostic vndbinder context. Both patched-kernel tests ran with SELinux enforcing. These are native component tests, not an Android 13 OS boot.

## Compiled modern userspace and reproduced fixes

Built Lineage 20 Android 13 first-stage init, recovery second-stage init, adbd, shell, toybox/toolbox, real recovery SELinux policy and contexts, and a small recovery fallback process. The image contains matching ARM recovery shared-library dependencies and no stock SYSTEM mount. Android's host init verifier accepts the rc file. The fallback requests installed recovery after 120 seconds unless `/dev/t110-keepalive` exists; it cannot rescue failures before its service starts.

- `0009`: opted-in real cgroup-v1 cpuacct process groups. The host sysroot also needed a guarded cgroup-v2 magic constant. QEMU now passes actual Android 13 create/inherit/kill/cleanup, including a grandchild.
- `0010`: upstream Linux `55815f70147dcfa3ead5738fd56d3574e2e3c1c2`, permitting fstat on O_PATH descriptors. Android 13 realpath failed with EBADF on the actual T110 before the fix. QEMU reproduced the resulting SELinux restorecon/init abort; the fix passes directory/file fstat and realpath, while O_PATH read and invalid fstat descriptors remain rejected.
- `0011`: native ARM mmap entropy control from pinned Android common 3.4 `40bb591cb6abaf540bf9a988e3fac0ca86368865`. Android 13 init otherwise aborts because `/proc/sys/vm/mmap_rnd_bits` is missing. The backport installs a real bounded sysctl and uses it in address selection; it does not bypass init's security check. For the T110 3GB address split, bounds are 8..16 and init selects 16. Two trailing-blank-line patch warnings were nonfatal.

The QEMU configuration was updated with cpu/cpuacct cgroups and a 3GB split to match those relevant T110 capabilities. QEMU v3 reaches real enforcing SELinux, second-stage init, ueventd/coldboot, mmap entropy setup, recovery watchdog and adbd startup. Path and process-group probes exit 0. QEMU has no T110 USB gadget; USB transport is not validated by this test. Some nonfatal policy denials and missing optional files remain logged.

## USB fixes after the first tablet trial

V3's saved `/proc/last_kmsg` proved that modern init, coldboot, mmap entropy setup and test services started before the kernel crashed in FunctionFS binding. Patch `0012` removes an erroneous early `kfree(d)` in the inherited T110 USB string parser. The actual parser reproduced a heap-use-after-free under ASan before the patch and passed valid ADB strings/table walking and malformed-input cleanup afterward. V4 then enumerated USB, passed the path and cgroup probes, and automatically returned to installed recovery after 120 seconds; its modern AIO-based adbd stayed offline.

The old FunctionFS driver has synchronous `.read`/`.write`, but no AIO operations. Patch `0013` adds an explicit `ro.t110.legacy_usb` opt-in synchronous backend to actual Android 13 adbd. Its chunked I/O follows AOSP Android 10's legacy transport approach; cancellation interrupts active syscalls before descriptor closure. The actual transport header passed 12 ASan/UBSan host cycles covering 128 KiB bidirectional framing, blocked read/write cancellation, repeated close and destruction notification. V5 then passed the real USB tests above. No old adbd binary was substituted.

## Latest artifacts

Android 13 HIDL Binder transport in `libhidlbase` passed a two-process 4,099-byte scatter/gather request and reply in QEMU and on the SM-T110. The tablet ran the existing v5 boot image with a matching ARM probe bundle loaded into RAM. The watchdog returned it to TWRP. Stock BOOT and recovery hashes matched after rollback and stock boot completed. See `hardware-tests/20261105-140246-hwbinder/result.json`. Full HIDL services still need integration.

- `artifacts/kernel-native-init-ffs/zImage`: SHA256 `ccbb784dc305c0e9134d432d02afaf873fde507cb5d501545e014dfe386458a3`.
- `artifacts/android13-ramdisk-v5/boot.img`: 11,206,656 bytes, within 16 MiB BOOT.
- Full-partition `KERNEL.img`: SHA256 `6ced895a4cb8a2357035ae877b1f95992ac5becb8b2cc6e89faf48c352acda39`; MD5 `1cbc47be853e2b5100d85be34ab73681`.
- Separate recovery p9 remains MD5 `cd9793e1ee8f284c9056b225885b5b1a` as verified after flashing.
- Stock BOOT rollback `backups/20261104T201457Z/KERNEL.img`: MD5 `7847f1b7e68e49e9ca590e052f0f76c4`.

Logs, file hashes, real policy, kernel config and cumulative source diff are archived beside the artifacts. V1 failed QEMU at O_PATH and V2 at mmap entropy; neither was flashed. V3, V4 and V5 hardware trials are separately preserved.

## Resume

1. The next product is `lineage_t110_system-eng`: a full Lineage system compilation target using the same ARM/32-bit-Binder settings. It is build-only and not approved by hardware tests for flashing. Graphics/HAL, normal-boot APEX/services and production policy remain unresolved.
2. Full-system compilation stopped after USB I/O failures, which recurred during a source audit with the replacement cable. The user switched to an RTL9210B enclosure. Check `BUILD-WORKSPACE.json` for filesystem recovery, source verification and build state. `scripts/build_system_image.sh` applies the tested process-group and adbd patches and passes GOGC=30 to Soong. It requires all dependencies.
3. For future diagnostic trials, keep installed recovery intact and use per-trial guarded BOOT writes/readbacks. The successful v5 rollback log is saved. The RAM-only image lacks a standalone reboot command; use `adb shell setprop sys.powerctl reboot` for normal reboot.
4. Poll ADB shell readiness directly: `adb wait-for-device` does not wake for this diagnostic's `recovery` state. Create `/dev/t110-keepalive` after verifying `/t110-native-diagnostic` to cancel the two-minute watchdog.

The full Lineage checkout completed in the native E: WSL distribution `T110Build`, `/root/t110-build/lineage20`; its pinned manifest is `evidence/lineage20-full-manifest-pinned.xml`. Do not reuse the retired loop/DrvFS image. Original Ubuntu native/kernel outputs remain independent of the full-system build.
