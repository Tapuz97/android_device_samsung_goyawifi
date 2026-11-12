# Startup corrections for the SM-T110

**Hardware update, 2026-11-07:** The subsequent single test failed usable UI despite an observed boot-completed flag. Permission/location startup improved, but SystemUI and keystore/user-unlock errors remain. Tablet returned to verified TWRP. See [test result](hardware-tests/20261107-001850-core/result.json). The offline report below is historical.

Status: **OFFLINE VERIFIED, NOT BOOT TESTED**. The corrected v24/v15 ROM is built and checked. No tablet access, flash, or boot test was performed this pass. The previous v23/v13 test failed; its evidence remains unchanged in `hardware-tests/20261106-211758-core`.

## Findings and changes

The first system-server process exceeded the watchdog limit while awaiting default permission initialization. The naturally restarted process completed that step in 39.776 seconds, then exceeded the limit during boot phase 600. Its sampled stack was in GNSS initialization, which eventually returned after 13.364 seconds. This was accumulated startup latency, not evidence of an infinite GPS deadlock.

**Runtime and app compilation.** The saved thread traces loaded `libartd.so` and spent seconds in debug-only garbage-collector verification. In this Android source, `JniInvocationGetLibraryWith` prefers an installed debug runtime over the `persist.sys.dalvik.vm.lib.2` property. The device product requests the standard ART APEX. Because product inheritance evaluates the runtime package node separately, patch 0043 also selects it at that node for lineage_t110_system only. The initial v14 export exposed this inheritance issue and was rejected offline. The engineering build and debugging access remain. App precompilation is enabled instead of limiting it to the boot classpath and system-server JARs; PermissionController, SystemUI and TrebuchetQuickStep request the `speed` compiler filter. JIT remains disabled because its mapping requirements are not supported by the current kernel. The previous ART first-fork locking fix remains in the standard runtime.

**PermissionController packaging, patch 0042.** Android normally excludes APEX applications from precompilation even when app preopt is enabled. An explicit T110 build option now permits selected speed-critical apps in flattened APEXes. The compiler uses the actual versioned `/apex/com.android.permission/priv-app/PermissionController@TQ3A.230901.001/PermissionController.apk` location. Its compiled artifacts are required by the APEX and installed under `/system/framework/oat/arm`, using the existing encoded APEX path convention that ART checks for every DEX file on `/apex`. The APK remains inside its original APEX; it is not duplicated or moved. Normal and unbundled/updatable builds retain their existing behavior.

**GPS initialization, patch 0040.** The current build has no ported modern GPS provider or GNSS manifest entry. With VINTF enforcement disabled, each ordinary HIDL lookup sleeps for a second, including `tryGetService`, then tries an absent provider. The T110 path now checks the manifest transport before calling HIDL lookup, skips undeclared versions, uses non-waiting lookup for declared providers, and checks rather than waits for AIDL services. The switch has an explicit readable property context. Other devices retain the original path. GPS positioning is still unavailable until its driver/provider is ported; this change prevents missing support from delaying startup. A declared provider that is not ready can also be reported unavailable; future GPS integration must ensure provider readiness.

**Memory-manager reconnect churn, patch 0041.** The saved logs repeatedly show `Failed to retrieve sender credentials`. This kernel's `unix_accept` does not inherit the listener's socket credential flag. LMKD now explicitly enables `SO_PASSCRED` on accepted sockets before reading requests. It still requires kernel-supplied `SCM_CREDENTIALS`; configuration failure closes the socket. No credentials are fabricated and no authorization check is bypassed.

Watchdog limits and permission-grant completion requirements are unchanged. The working EGL window path, framebuffer ownership/synchronization, alarm kernel and recovery safeguards are retained.

## Offline validation

`scripts/test_v24_startup_offline.py` compiles the changed GNSS constructor/helper against host service API doubles with ASan/UBSan. It covers missing, declared, not-ready and failed transports, AIDL/HIDL fallback, and the unchanged normal-device path. This is not a live Binder or hardware test.

The same script compiles the actual LMKD socket configuration against real Linux AF_UNIX sockets. It reproduces the missing inherited flag, validates credentials on subsequent and queued-before-accept packets, and verifies rejection on setup failure. The old kernel behavior is simulated by clearing the accepted socket flag; no kernel boot is performed.

The completed image passed the ARM build, ext4/partition checks, release-ART and debug-ART-absence checks, embedded fix/property checks, and inspection of actual compiled app artifacts. `verify_v15_contents.py` records those results. `finalize_offline_v24.py` accepts only verified outputs and pairs the system with byte-identical, reverified v23 boot inputs; the kernel and ramdisk do not need rebuilding for these system-only changes.

The pairing manifest is authoritative for readiness. Offline checks cannot establish full boot completion, usable UI/touch, or startup duration on the tablet. No subsequent boot test is scheduled by these scripts.

## Completed output

- [System image](artifacts/lineage20-rom-v15/system.raw.img), with sparse `system.img` in the same folder.
- [Matching boot files and pairing manifest](artifacts/android13-full-v24/system-pair.json).
- [Actual image contents and source provenance](evidence/v15-startup-fixes-contents.json).
- [Filesystem/partition report](artifacts/lineage20-rom-v15/system-verification.json).
- [Windows export hash verification](artifacts/lineage20-rom-v15/host-verification.json).
- [Host regression report](evidence/offline-v24/regressions.json).

Final build `system-image-20261106T202931Z.log` completed successfully in 07:28. Actual-image inspection confirms standard ART and absence of debug ART, compiled GNSS and credential fixes, retained graphics/ART corrections, and three speed-compiled ARM app artifacts whose DEX checksums match the packaged APKs. Ext4 checks passed with exit 0, the raw image fits the 1,594,884,096-byte SYSTEM partition, and raw/sparse hashes match between Linux and Windows. The matching boot image was unpacked and its current inputs reverified; its bytes are unchanged because these corrections are system-only.

The initial v14 export is rejected and marked DO NOT FLASH. The corrected output is v15. Neither was booted during this offline pass. A usable Android screen, touch, GPS positioning and improved physical startup time have not been established by these checks.

Raw system SHA-256: `05b2eecfb98c71d160b18926389ae67d7e9d19c5a8a8145026f9b5a38b4b0d7e`.

BOOT SHA-256: `811a3dbfa08e83005236def1b86eae3495bca49f5c1f13a43e82c804d9c195b5`.
