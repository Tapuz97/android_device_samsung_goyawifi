# v26 BOOT / v17 LineageOS system

Both requested corrections were implemented and verified offline before tablet staging on 2026-11-07. The user authorized flashing after these checks.

## Changes

- Codec2 initializes allocator metadata even when opening ION fails; failed allocations retain the original error. This prevents the null-traits crash without pretending memory allocation succeeded.
- The app EGL loader and legacy gralloc path explicitly initialize the Vivante process before using its APIs. The stock library has no automatic ELF initializer; its exported constructor has its own PID guard.
- Only the GPU and ION device nodes receive app-accessible modes. The device policy adds the ION write access needed by legacy gralloc for normal apps and system_server; isolated apps remain excluded and SELinux remains enforcing.
- The previously tested kernel, matching GPU module, user-unlocking correction, SystemUI AppOps guard, and earlier graphics/startup changes are retained.

## Offline evidence

The full ARM system build completed successfully (`system-image-20261107T082859Z.log`). Extracted production-code regressions passed with host ASan/UBSan, including failed allocator opens and graphics initialization ordering/failure handling. These use API doubles and do not establish hardware behavior.

The actual exported image passed ext4 checks, binary and SystemUI DEX inspection, compiled-policy access checks, and source/export hashes. Its raw size is 1,594,884,096 bytes, matching SYSTEM capacity. It will continue using the existing read-only loop image on userdata.

The matching boot image passed independent unpacking, header ID, partition size, kernel/module, CPIO metadata and policy verification. Only `init.mrvl.rc`, `ueventd.mrvl.rc` and the bootstrap policy changed from v25.

Evidence: `evidence/offline-v26/{regressions,contents,policy-after,embedded-policy,systemui-dex-verification,boot-verification}.json` and `artifacts/lineage20-rom-v17/{host-verification,system-verification}.json`.

Pair manifest: `artifacts/android13-full-v26/system-pair.json`.

- SYSTEM SHA256: `1dfc038e7dbf5ed45c747dd0a8a50574e035d2b53533afe81c54de6e9acb71d1`
- SYSTEM MD5: `89a74dd23767c22cb60a1f06ccd8cc15`
- BOOT SHA256: `d74618b0fb22aec87f2a2309df88cbf8db2bd7dcd51280d72d9fa703ec6099fd`
- BOOT MD5: `f3f30815e1823ea4425847e3020a7d4b`

## Hardware verification boundary

No Android/emulator/tablet boots were used during preparation. A single full boot follows staging and flash verification. A boot-completed property alone does not prove usable UI: user unlock, SystemUI/launcher stability and an actual screen observation are required. Other unported hardware and codec functionality remain unvalidated.

## Single hardware boot result

Flashed once after all offline checks. Android unlocked and status/navigation UI rendered into the framebuffer. The two original native crash signatures were absent, but missing Wi-Fi service repeatedly killed setup, sdcard aborted, and a later NetworkStats exception restarted system_server. Full usable boot failed. The tablet was returned to verified TWRP, with v26/v17 still installed. See `hardware-tests/20261107-105547-core/result.json`. No extra boot or live configuration workaround was used.
