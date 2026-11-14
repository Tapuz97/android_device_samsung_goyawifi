# Android13 full component integration — offline checks passed

Date: 2026-11-14. No ADB, reboot, transfer or flash was performed.

## Completed build gates

The exact1242-project Android13 checkpoint and original25 project deltas were
restored to Ubuntu `/root/t110-android13/android`, on the internal drive. The
working14.1 checkout and images were not used as build output or modified.

The real Android build completed for ARMv7-A/NEON, Cortex-A9:

- HWUI/libgui and the linker, including the T110 window/dequeue/textrel changes.
- SurfaceFlinger, RenderEngine's custom EGL window, framebuffer compositor,
  allocator and mapper. These are complete platform targets, not header stubs.
- The forwarding audio HAL, compatibility library, audio7.1 HIDL implementation,
  effects7.0 implementation and standard audio service.
- All16 exact stock audio libraries/plugins with strict ELF dependency/symbol
  checks enabled. No `allow_undefined_symbols` exemption was introduced.
- SELinux compilation, file/property context checks, compatibility and freeze
  tests. No new permissive domain or disabled neverallow was introduced.
- All60 stock audio configuration/calibration files plus the primary policy,
  volume tables and service override were installed and verified by hash/XML.

`full-build-verification.json` records136 output hashes and successful build-log
hashes. The final vendor driver rerun was a successful no-work build after
changing its probe target to the uninstalled executable. `vendor-audio-5.log`
contains the actual16 ELF checks and full compositor build; earlier failed runs
are retained as diagnostic history and are not counted as passes.

## Fixes made during integration

The existing Android13 vendor libeffects provider is retained, avoiding a second
stock implementation at the same install path. The old primary HAL and libacm
have explicit dependencies for the list shim and libcrypto respectively.

The product importer expands inherited paths differently from a normal included
makefile. Generated audio copy rules now use explicit source-root paths. All60
rules are requested explicitly so a component-only build cannot silently omit
the routing data. Unchanged build definitions are not rewritten on regeneration.

Stock ALSA1.0.23 supports type-level `lib` configuration entries. These select
the three vendor-side codec/phone plugins explicitly. No system/usr executable
plugin directory is added to the vendor namespace. The service gets
`ALSA_CONFIG_PATH`; the original groups, profiles and capabilities are retained.

Strict checks identified26 imported functions retained by real Bionic under
LIBC_PRIVATE but excluded from the vendor SDK stubs. The device-private shim
forwards exactly these ARM helpers/stdio functions to an explicit libc handle.
PIC ARM tail trampolines preserve arguments, SP/LR and multi-register divmod
results. They do not reimplement floating-point math or FILE internals. Only10
stock libraries importing these helpers receive that dependency. The new shim
itself has no TEXTREL. The original stock inputs remain unchanged.

The DSP's actual text relocations have an opt-in linker exception limited to
`/vendor/lib/libippsp.so` and its system/vendor alias. The dedicated SELinux type
can receive execmod only from hal_audio_default. Exact proc clock labels and
HAL-readable labels for the three stock clock properties replace broad guesses.
Compiled-policy queries confirm all required clock/property/config accesses and
the exclusive DSP permission. Live policy and API33 definitions stay synchronized.

## Additional offline evidence

- Actual Soong-built ARM bridge/probe, running under Android13 Bionic and Cortex-A9
  QEMU:122 checks passed across all26 helpers, cold/cached paths, signed/unsigned
  32/64-bit divmod and buffered file IO. No target-SDK lowering was used here.
- Updated stock primary HAL and allthree plugins load/relocate, and ALSA resolves
  the explicit codec library path in the real Android loader diagnostic.
- That second diagnostic still uses a process-only SDK22 setting for the DSP
  TEXTREL and has no production linkerconfig. It is not a production namespace,
  SELinux runtime, audio-device or microphone test. No SDK lowering occurs in
  the HAL or product.
- Diagnostic code is excluded from PRODUCT_PACKAGES. The driver builds its raw
  executable target; the earlier identical installed probe copy was removed
  from vendor/bin. It must not become a ROM payload.

## Backups and restoration

Source branch: `t110/android13-offline-audit-20261114` in
https://github.com/Tapuz97/android_device_samsung_goyawifi.

`phase3/complete-project-deltas` contains complete deltas against the pinned
upstream HEADs, replacing the five corresponding old capsule patches.
`project-additions` contains the actual current custom framebuffer/EGL/navigation
sources ignored by upstream Git. Copy these over the restored capsule additions;
patch files alone would miss their edits. `projects.json` records every hash.
See RESTORE-NOTES.md. Other capsule deltas/assets remain prerequisites.

`product/audio` is current source and generated build definitions. Stock binary
payload/configuration comes from the verified existing stock backup and the
packaging script; it is not committed to public source Git. Run the bridge
generator after restoring the full checkout, then regenerate packaging before
the vendor build. The loader closure metadata and all build/check scripts are
preserved. The earlier private restoration capsules remain available online.

The new component ZIP contains136 verified outputs, policy/configuration and
diagnostic logs. It is **NOT FLASHABLE** and is not a complete ROM. It is stored
separately in the existing draft Android13 component backup;14.1 release assets
and original Android13 capsules are unchanged. Online verification is recorded
in `phase3-backup-verification.json` after upload/readback.

Both14.1 boot/system pairs passed fresh full SHA256 checks and their device
checkout remains clean at `ceebd0c9a6c3298765757522f88d75d0bd47b4eb`.
See preserved-rom-verification.json. Never overwrite them with these components.

## Remaining gates before a physical trial

This is a verified component integration, not hardware qualification or a new
complete system image. Production linker namespaces still need validation in
the assembled candidate. The GPU window path remains opt-in; its fallback is
preserved. Build/verify the complete candidate and its contents before any flash.
Runtime GPU rendering, sound/microphone, radio/navigation preservation and real
suspend/wake still need a combined physical test after those gates. Camera work
is not claimed complete by this audio/graphics integration.
