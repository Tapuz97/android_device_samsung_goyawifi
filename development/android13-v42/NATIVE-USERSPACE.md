# Android 13 native userspace checkpoint — 2026-11-05

Status: diagnostic v5 boots actual Android 13 init and root USB ADB on the tablet. Native probes, two-process Binder, bidirectional USB transfer and reconnection pass. Global SELinux is enforcing with permissive engineering recovery/su domains. Stock BOOT has been restored and stock Android boot_completed=1 verified. [NATIVE-BOOT.md](NATIVE-BOOT.md) owns current evidence and reproduction details. A full graphical Android 13 OS is not yet booted.

## Build target

`work/device/samsung/t110_bringup` defines a small ARMv7/NEON, 32-bit Binder engineering product without the original attempted ROM's legacy platform-library replacements. It is not a complete ROM product.

- `t110_bionic_probe`: static Android bionic test for pthread/TLS, monotonic clock, eventfd/epoll, getrandom/getentropy fallback, and fork/exec.
- `t110_libbinder_probe`: two-process Android Parcel roundtrip on the unused diagnostic `/dev/vndbinder` context, with a 20-second alarm. It requires root recovery and must not run on a live vendor service-manager context. Android 13 disables the device static libbinder variant, so this uses the normal shared library and must be bundled with its matching modern linker and dependency closure.
- `t110_processgroup_probe`: intended for the later modern diagnostic ramdisk; verifies a real v1 cgroup filesystem, creates a private child process group, checks descendant membership, then exercises Android's kill/cleanup APIs. It is compiled; runtime validation awaits modern init and mounted cgroups.

The build accepts `lineage_t110_bringup-eng`, compiles/tests Soong's host tools, generates its module graph, and builds the bionic probe. It uses the supported `--soong-only` mode for these native targets; unrelated Make SDK packaging is not required for the probes. `ALLOW_MISSING_DEPENDENCIES` is limited to the temporary partial checkout; missing dependencies of requested targets still fail the build. This is not full-build validation.

## Boot design, now packaged as diagnostic v3

Use actual Android 13 first-stage init, recovery second-stage init and recovery adbd in a self-contained boot ramdisk, within the measured 16 MiB BOOT partition. Preserve the separate installed TWRP recovery and stock SYSTEM. Establish modern init plus USB ADB before graphics or a SYSTEM replacement.

Verified source details:

- `system/core/init/util.cpp` detects recovery through `/system/bin/recovery`; `first_stage_mount.cpp` skips first-stage partition mounting in this mode.
- First-stage init executes `/system/bin/init selinux_setup`. `selinux.cpp` supports a monolithic `/sepolicy`; the real Android policy must be built and integrated. The synthetic QEMU policy fixtures must never be included.
- `system/sepolicy/build/soong/policy.go` selects binary policy version 30, matching the backported parser. This is not proof that the complete policy will load or enforce correctly.
- `packages/modules/adb/daemon/usb_ffs.cpp` retries legacy FunctionFS V1 descriptors when V2 fails. The T110 Android gadget includes FunctionFS through `android.c` despite the standalone CONFIG_USB_FUNCTIONFS option being unset. End-to-end modern USB ADB remains untested.
- The upstream recovery rc assumes binderfs, which this kernel lacks. The diagnostic rc must use the existing independent Binder character devices and must not mount stock SYSTEM over the ramdisk's `/system`.
- Android 13 `libprocessgroup` unconditionally selects the cgroup-v2 hierarchy when creating service process groups, and init treats a creation failure as a service-start failure. The T110 kernel has v1 cpu/cpuset/cpuacct but no v2. Patch `0009-android13-t110-legacy-processgroups.patch` adds an explicit `ro.t110.legacy_processgroups` opt-in to use a mounted v1 cpuacct hierarchy for create/kill/cleanup. It avoids v2 activation controls on v1. Apply-check and device compilation passed. The host build exposed a missing cgroup-v2 magic constant in its old glibc sysroot; a guarded constant definition fixes that build dependency. Runtime lifecycle validation is still pending. Configuration inputs are under `work/native-ramdisk`.
- Android's linker supports direct invocation; use a matching `LD_LIBRARY_PATH` for an isolated dynamic probe. It does not implement a `--library-path` argument.

## Host storage incident

The initial E: raw ext4 image, mounted through loop/DrvFS, suffered WSL `GFP_NOIO` page-allocation failures in `p9_fcall_init`, followed by loop write errors and ext4 warnings about potential data loss. Builds/downloads were terminated and the image unmounted. A bounded read-only filesystem check was canceled at its timeout and did not certify the image. No repair or reuse is implied. Logs are in `evidence/e-volume-io-failure.log` and `evidence/e-volume-fsck-readonly.log`.

A dedicated `T110Build` Ubuntu 24.04 WSL distribution was installed at `E:\T110-build\WSL\ext4.vhdx` (420 GiB logical capacity), using the native WSL block-device path. Its 30 GB source seed copy and follow-up reconciliation completed; the full Lineage sync has restarted there. The original image is unverified and its mount/sync scripts are retired. The SSD's physical failure has not been established.

The temporary native build continues in the original Ubuntu distribution at `/root/t110-build/out-native`, rebuilt from scratch rather than reusing output from the affected image. Source revisions are recorded in `evidence/android13-native-source-pins.json`. See BUILD-WORKSPACE.json for the current host paths.

## Hardware native milestone, 2026-11-05

Actual Android 13 static bionic passes pthread/TLS, clock, eventfd/epoll, getentropy fallback and fork/exec on both stock and patched T110 kernels. On the patched kernel, actual Android 13 libbinder also passes a two-process Parcel roundtrip on the unused diagnostic `/dev/vndbinder` context, using only the matching modern linker/library bundle. Both patched-kernel tests ran with SELinux enforcing. Logs and hashes are in `artifacts/android13-native/*-result.json` and `hardware-tests/20261105-android13-native/`.

First-stage init, recovery second-stage init/adbd, real recovery SELinux policy, shell/tools and a bounded recovery fallback are built and packaged. `scripts/package_native_ramdisk.py` checks ELF closure, init syntax, boot geometry and partition fit. QEMU startup and the failed-to-enumerate tablet trial are recorded in NATIVE-BOOT.md. Full services, libhwbinder and graphics remain unvalidated.
