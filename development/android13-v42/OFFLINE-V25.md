# Keystore and System UI corrections for SM-T110

Status: **OFFLINE VERIFIED, NOT BOOT TESTED**. Both corrections are built into the v25/v16 pair. No tablet access, flash, kernel/emulator boot or tablet boot occurred in this pass. The previous failed hardware result is unchanged.

## Keystore and user unlocking

The saved v24 logs show `Cannot check permission without calling_sid` in keystore2's `get_state` call, followed by response code 4. `LockSettingsService.ensureProfileKeystoreUnlocked` calls `KeyStore.state`, which asserts on that unexpected error. The framework process exits; this is not evidence of damaged keys or a wrong password. Other key-generation calls fail for the same absent caller label.

All three relevant keystore2 interfaces already set `set_requesting_sid: true`. Android 13's libbinder already sends `FLAT_BINDER_FLAG_TXN_SECURITY_CTX` and understands `BR_TRANSACTION_SEC_CTX`. The existing 3.4 Binder backport lacked both kernel-side pieces.

Patch 0044 adds the requested per-node delivery. It snapshots the opener's SELinux SID at `binder_open`, resolves the SID into a context through the LSM, and places that context in a reserved transaction-buffer tail. The sender's scatter/gather area excludes this tail. Overflow, missing context and allocation failures reject the transaction, and temporary LSM context allocations are released on success and failure. The read path supplies the extended transaction structure while retaining legacy transaction/reply sizes and synchronous reply-stack handling. Plain nodes and replies retain their previous protocol. Extended context-manager registration is not added; keystore's registered service nodes use ordinary flagged-node transactions.

The design follows the upstream [Binder security-context ABI](https://android.googlesource.com/kernel/common/+/36d178b3bca51d77a83383451359fc67552396ad/drivers/android/binder.c) and the [opener-credential identity correction](https://android.googlesource.com/kernel/common/+/4d5b5539742d2554591751b4248b0204d20dcc9d). This old kernel stores the immutable opener SID directly rather than adding a new credential-security API. Its existing unrelated Binder permission hooks are unchanged.

Keystore permission checks, lock-screen checks and the `KeyStore.state` assertion are not bypassed. Existing alarm, graphics, runtime and logging fixes remain in the parent kernel and system.

## System UI

`AppOpsService.getPackagesForOps` initializes its result to null and can return it when no matching operations have been recorded. System UI's `fetchCurrentActiveOps` iterated that result unconditionally, causing a `NullPointerException` while constructing `KeyguardService`.

Patch 0045 treats that valid null response as an empty initial snapshot. Active-operation callbacks are already registered and remain registered. Existing active operations are still reported normally. The actual method is checked with null, empty, active and inactive operation lists.

## Validation and limits

Host tests compile extracted production Binder allocation/copy/cleanup blocks with address and undefined-behavior sanitizers. They exercise valid payloads, context lookup errors, malformed context, allocation failure, size overflow, reserved-tail separation and cleanup. These use API doubles and do not execute the kernel driver. The actual Binder header also passes 32-bit structure-size and command checks. The extracted System UI method passes Java tests with API doubles.

Completed checks include both full ARM builds, actual-image DEX and precompiled-app checks, unchanged keystore/framework/services binaries, ext4 integrity, partition fit, Linux/Windows hashes and an unpacked matching kernel/module/boot check. The existing boot cannot be reused unchanged: the keystore correction is in the new kernel.

A successful unlock, usable UI and driver behavior on the tablet remain unverified until a later authorized test. GPS positioning, audio and other unported hardware are outside this correction. The media codec crash captured during v24 is also still unresolved. No boot test is scheduled by this workflow.

The initial system build was interrupted by repeated SSD read retries. After the user reconnected the drive, the final system build, export and checks completed. This is an offline-ready candidate; successful user unlocking and usable UI are not yet established.

## Verified outputs

- [System raw image](artifacts/lineage20-rom-v16/system.raw.img), with sparse `system.img` alongside it.
- [Matching boot and system manifest](artifacts/android13-full-v25/system-pair.json).
- [Kernel and module provenance](artifacts/kernel-binder-secctx/provenance.json).
- [Image contents](evidence/v16-startup-fixes-contents.json), [actual SystemUI DEX](evidence/offline-v25/systemui-dex-verification.json), and [host checks](evidence/offline-v25/regressions.json).
- [Filesystem/partition checks](artifacts/lineage20-rom-v16/system-verification.json) and [Windows hash verification](artifacts/lineage20-rom-v16/host-verification.json).

Raw system SHA-256: `a37faa553bf9827d77293e4935350ba49fc6f9e78747979ab4691a7db20d7607`.

Padded BOOT SHA-256: `a63c1b36d9ce32aeae48a22b7e5b8e3dc5aaf06184fda3b420e2f5cf271450b6`.

The raw image is 1,594,884,096 bytes and fits the existing SYSTEM partition. The boot package fits the 16 MiB BOOT partition. The kernel configuration matches the parent, and the boot image was unpacked to verify kernel/module hashes and unchanged ramdisk contents. The new Binder command is present in the ARM object code. These checks do not replace a future hardware boot test.
