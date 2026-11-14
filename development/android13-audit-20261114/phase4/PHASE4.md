# Android 13 complete image and production namespace verification — 2026-11-14

The complete LineageOS20/Android13 ARM image and matching boot image are built.
Offline gates passed. No tablet access, transfer, reboot or flash was performed.
This is an engineering candidate, with real GPU/audio behavior still unqualified.

## Candidate identity

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Raw system image | 2146435072 | 470961893c93aa228c5722108ab15b364b970d6d143c3a5546401bb6ac7563ee |
| Matching boot image | 16777216 | f2d735c3fea57b853147b6a846fc80ff0ed9e2df3d168ef398fc7d3a1a8365c7 |
| Gzip system backup | 639987015 | 767b46e5e729615e34956d0564523de7a99ed91c2df85f806a8ee7dcd2221ab7 |

Native artifacts: `/root/t110-android13-audit/complete-image` and
`/root/t110-android13-audit/complete-candidate-backup` in Ubuntu WSL on internal C:.
The external SSD is not used. The raw image is for the preserved read-only
userdata loop mechanism, **never the faulty physical SYSTEM partition**.
The immutable13 stager expects `/stage-data/local/tmp/t110-rom-system.raw` and
`/stage-data/local/tmp/t110-rom-data`; these strings were checked in its binary.
Live userdata free space has not been checked. This is not a recovery-install ZIP.

## Build changes and recovered inputs

- Full pinned1242-project source plus the original deltas and phase3 integration
  built with the ARMv7-A/NEON Cortex-A9 configuration and JDK11.
- The filesystem container is2047MiB, within the preserved bootstrap's supported
  loop geometry and below signed32-bit file offsets. No physical partition grew.
- The kernel carries the working14.1 initramfs archive-end correction. Only
  `init/initramfs.c` differs from the old kernel source baseline. Embedded kernel
  configuration and galcore module hashes match the prior13 components exactly.
- The actual `/dev/graphics/galcore` node now receives0666 DAC and `gpu_device`
  labeling, with the legacy `/dev/galcore` alias retained. Generic graphics-device
  access remains forbidden to ordinary apps. GLES2 capability is declared as131072.
- The matched boot uses the new compiled policy, enables the built accelerated
  window path, retains Canvas fallback, and preserves the13 stage, module,
  disabled continuous logging and memory tuning. No14 userspace is mixed into13.
- The pinned ARM WebView was a Git LFS pointer after restoration. Its exact
  98,126,751-byte object was restored through the repository's declared Gerrit
  LFS endpoint, with SHA256 and complete ZIP validation. Its revision did not
  change; WebView remains included.
- Build2 reached95% before Linux killed Ninja for memory pressure. Cached
  compilation with two jobs completed. Compiler and policy checks were retained.
  The successful final build log is `complete-image-4.log`.

## Offline results

| Gate | Result and scope |
|---|---|
| Complete system build | PASS; full system image and host linkerconfig built |
| Filesystem | PASS; e2fsck read-only clean,4096-byte blocks, old-kernel-compatible feature allowlist,719773696 free bytes |
| Image contents | PASS;142 extracted hashes, actual properties, exact GPU rules and audio SELinux xattrs checked |
| Compiled image policy | PASS; actual vendor-init audio actions, HAL clock/property access, exact app/compositor/allocator GPU access; generic graphics restriction retained |
| Production namespace resolution | PASS;279 native program/library targets,10 generated namespace configurations, zero failures |
| Audio module selection | PASS; real libhardware selected the modern T110 proxy, not the raw legacy HAL |
| Audio loading/configuration | PASS; stock HAL, three ALSA plugins and modern HIDL audio/effect libraries load; all three actual ALSA type paths resolve |
| DSP exception boundary | PASS; an identical DSP at an unrelated data path is rejected for text relocations |
| Matching boot | PASS offline; legacy header, CPIO contents/metadata, kernel/config/module/policy and unchanged stager checked |
|14.1 preservation | PASS; current and rollback boot/system pairs match known hashes; source tree remains clean |
| Physical key layouts | Both13 key layouts match the working14.1 source exactly;13 hardware behavior remains untested |
| Local backup | PASS; gzip fully decompressed and hashed back to the complete raw system; verification ZIP integrity checked |

The production tests mount the actual image read-only with a private overlay,
activate its own flattened APEX manifests, initialize its actual property
contexts/values and invoke its real ARM linkerconfig/linker under QEMU. They use
no guest LD_LIBRARY_PATH/LD_PRELOAD override, no SDK lowering and no device opens.
The isolated host QEMU runtime is not included in guest library search paths.

## Test corrections and retained conclusions

The first namespace attempt produced38 failures. `--strict` stopped namespace
resolution at `libdexfiled.so`, the debug-only ART library intentionally excluded
by this product's optimized release ART choice. Android init invokes the
generator without that switch. Normal production-mode generation resolves the
remaining manifest dependencies correctly; it emits no generator diagnostics.
The strict debug-library diagnostic is preserved separately in the final report.
No APEX library was removed and no namespace isolation was disabled to get PASS.

The standalone GLES checks also needed their real load context. Android's pinned
`frameworks/native/opengl/libs/EGL/Loader.cpp` loads EGL before GLES1/GLES2; the
shader compiler is then loaded in that driver context. Constructor-free test
executables model that existing EGL dependency without changing stock DSOs or
adding search directories. GPU constructors, rendering, swap, suspend and panel
output are not validated by these checks.

The initial failure report remains in
`namespace-fixtures/20261114T162518Z/strict-attempt-verification.json`.
The final `production-namespace-verification.json` contains real command results,
all generated configuration hashes, audio checks and the rejected-path control.

## Backups and next hardware boundary

Source branch: `t110/android13-offline-audit-20261114` in
[Tapuz97/android_device_samsung_goyawifi](https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/t110/android13-offline-audit-20261114/development/android13-audit-20261114/phase4).
Restore prerequisites remain the original private capsule and phase3 complete
project deltas/additions. Phase4 contains changed product files and all new tools.

Candidate assets use a separate unpublished release tag
`t110-android13-image-candidate-20261114`. The online verification receipt is
written only after every uploaded asset has been downloaded and hash-verified.
Existing14.1 engineering, original restoration and phase3 component releases
remain unchanged. See `online-backup-verification.json` after upload completes.

Before any later hardware test, check userdata capacity and preserve recovery.
The next combined test must verify actual panel graphics and touch, boot/user
unlock, sound/microphone, Wi-Fi, Bluetooth, navigation and suspend/wake. Camera,
hardware acceleration performance and complete13 functionality are not claimed.
SELinux permission analysis was offline; live enforcement and the Linux3.4
hardware behavior were not emulated. Google apps are not added by this build.
