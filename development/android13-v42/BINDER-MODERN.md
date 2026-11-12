# Binder transport backport â€” SM-T110

The separate `kernel-binder-modern` candidate ports Android common 3.18 Binder transport onto the T110's Linux 3.4 source. It adds independent `binder`, `hwbinder` and `vndbinder` contexts, scatter-gather request/reply commands, nested pointer buffers and FD arrays. It retains protocol 7 for the selected 32-bit userspace ABI.

Source donor: [Android common commit 71c88531171e6a1eb49da78e8260475310dc1e81](https://android.googlesource.com/kernel/common/+/71c88531171e6a1eb49da78e8260475310dc1e81/drivers/staging/android/), `deprecated/android-3.18-n-release`. Only its Binder files and Binder Kconfig entries were imported. The complete source snapshots and hashes are under `evidence/binder-donor-3.18-n`; no donor board drivers or partition geometry were used.

## Linux 3.4 adaptations

- Translate the newer kernel's UID interfaces to the older kernel's native UID representation. This port deliberately excludes `CONFIG_USER_NS`; the build script explicitly disables it and asserts that all Binder options remain enabled after Kconfig resolves dependencies. This does not disable mount, PID or network namespaces.
- Retain the T110 kernel's FD allocation/install/close operations, wrapped in the donor's per-process `files_lock` for file-table lifetime protection.
- Provide local list iteration, nice-limit, page alignment and exclusive freezer-wait compatibility helpers.
- Adapt `map_vm_area` to Linux 3.4's `struct page ***` argument, using a local page-array cursor. The first runtime test caught the unadapted call: Binder could not map its buffers.
- Remove the original kernel's global `-w` flag for Binder alone, and compile it with `-Werror`. Other board drivers retain their existing flags. Both final target builds must include Binder and pass these compiler checks before artifacts are archived.

## Corrected donor behavior

The donor called `binder_ioctl_set_ctx_mgr` before its SELinux authorization check. A denied caller therefore still claimed the context and recorded the owner UID. An enforcing-policy test reproduced this: the first ioctl returned EACCES, but a later authorized claim through another Binder file returned EBUSY.

The port checks `security_binder_set_context_mgr` before modifying context state. The same regression test now passes. Its failing-before and passing-after logs are preserved with the emulator artifacts. This is a focused fix, not a claim that the entire historical driver has received a security audit.

## Validation

Eighteen focused checks pass on a Cortex-A9 vexpress QEMU kernel built from the patched source:

- The previous SELinux policy-30 parser and nine seccomp checks.
- Basic protocol-7 request/reply and three simultaneously registered independent device contexts, each handling its own client transaction.
- Nested PTR relocation in both a scatter-gather request and reply.
- Two FD-array descriptors transferred in a reply to a client requesting `TF_ACCEPT_FDS`; readable contents, close-on-exec flags and automatic close on `BC_FREE_BUFFER` are checked. A legacy context-manager node rejects unsolicited incoming FDs, so the test uses the permitted reply path.
- Invalid parent indices and insufficient extra-buffer space are rejected; a valid transaction subsequently succeeds on the same connection.
- Enforcing SELinux denial of a Binder call and denial of a context-manager claim without occupying the slot.

The ARM compiler also compares 24 base/scatter-gather ABI sizes, offsets and command values against the saved Android 13 header with `BINDER_IPC_32BIT`: all match. Runtime tests use synthetic C clients and test-only policies, not Android's actual libbinder/libhwbinder processes.

The exported patch applies cleanly to the preceding `kernel-binder` worktree. An in-memory replay of `prepare_modern_binder.py` reproduces all seven changed/new source files exactly. `evidence/binder-modern-source-verification.json` records their hashes.

Final T110 zImage: 3,937,192 bytes; SHA-256 `f4e735162c5050a7e7d2dbee1f1cff41ff26158ff5905375d140c7ce10377eb6`. Both target configurations and strict Binder compiler flags passed archive verification.

## Artifacts and reproduction

Patch: `patches/0008-binder-contexts-scatter-gather-backport.patch`, applied after 0004â€“0007. Preserve the earlier kernel candidates for comparison.

Final T110 files belong in `artifacts/kernel-binder-modern`; emulator kernel, config, test initramfs, source, policy fixtures and logs belong in `artifacts/qemu-binder-modern`. A valid final archive includes `build-provenance.json` for the T110 build and `validation.json` for the emulator. `archive_modern_binder.py` rejects missing Binder options, incomplete builds, source/hash mismatches, missing strict compiler flags or failed tests.

Existing WSL layout: `/root/t110-build/kernel-binder-modern`, `out-binder-modern`, `out-qemu-binder-modern`. Scripts are under the Windows project's `scripts` directory and assume the recorded WSL paths:

1. `prepare_modern_binder.py` creates the candidate from the pinned T110 base plus preceding patches, then imports/adapts the donor.
2. `build_kernel_binder_modern.sh qemu` and `build_kernel_binder_modern.sh t110` configure and build the two targets.
3. `run_binder_modern_qemu.sh` builds the static ARM test initramfs and checks all 18 results; it uses the existing policy30 fixture.
4. `compare_modern_binder_abi.py`, `export_modern_binder_patch.py` and `archive_modern_binder.py` verify ABI/source reproduction and save evidence.

No tablet flash, root installation, wipe or filesystem repair is part of these scripts. Hardware boot remains untested. The subsequent targeted SYSTEM repair cleared the storage hold; see STORAGE-REPAIR.md for verification and remaining physical-cause uncertainty. Transaction security contexts, newer optional Binder features, full Android policy and actual Android userspace integration remain unvalidated or absent. This is not a finished Android 13 ROM.
## Subsequent hardware validation — 2026-11-05

The archived T110 zImage booted on the tablet with a diagnostic TWRP ramdisk in BOOT. Fifteen seccomp/Binder checks passed on actual hardware; user confirmed display and touch. SELinux was temporarily permissive for these probes and then restored; QEMU policy fixtures were not loaded. Actual Android 13 libraries and userspace remain unvalidated. Stock BOOT was restored and normal boot verified. A full SYSTEM read returned all bytes but logged one recovered MMC timeout. See HARDWARE-KERNEL.md.
