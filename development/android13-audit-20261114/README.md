# Android13 audit against working Lineage14.1 — 2026-11-14

Status: two source fixes pass bounded host regressions. No complete Android13
build, image, hardware graphics qualification, tablet access or flash in this pass.
These changes are NOT a claim that Android13 graphics or wake is now fixed.

## Baselines and backup

Nougat source: ceebd0c9a6c3298765757522f88d75d0bd47b4eb, eleven platform diffs.
Its current and latest previous image pairs remain in the native14 artifacts.
All four boot/system files were fully SHA256-checked before this audit. The
current ROM/toolkit archives remain in unpublished GitHub release444868203;
GitHub server digests match the earlier verified archive manifest. No new copies
of large ROM images were created. See backup-verification.json.

Android13: device checkpoint40f5879 with v42/BOOT48 delta capsule SHA256
1be195bfbd0a73be2ebe551708be1e5f56b0b9f3c30164c201cb1e38a0e4a88d.
Pinned framework native915ad642 and hardware interfaces2f83e1bd are restored as
small selected source subsets. Their existing capsule diffs applied cleanly to
the exact pinned upstream files. They are not a complete Android build checkout.
upstream-provenance.json gives fetched source URLs and SHA256 identities.

## Graphics findings and changes

1. Android13's ordinary Surface deprecated dequeue callback lacked Nougat's
   bounded asynchronous-queue retry. Patch0001 ports that exact behavior, gated
   by ro.t110.legacy_gpu. Only INVALID_OPERATION is retried, for at most100ms.
   Existing fence ownership and cancellation remain intact. No global wait/ANR
   timeout is increased. libgui's pinned build file already links libcutils.
2. The Android13 CPU presenter cached its framebuffer yoffset across power
   transitions. If suspend resets the scanned page, its next back-page choice
   can be stale. Patch0002 reads actual mode/fixed data after successful unblank,
   validates the original mapping/layout and adopts the current yoffset. It
   rejects changed mapping/invalid offsets; it does not silently remap memory.
   This corrects stale-state handling, not a proven root cause of the black screen.
3. Ordinary app windows STILL default to software rendering through
   debug.hwui.t110_window_gpu=false in the preserved bootstrap. The custom CPU
   rotation/copy presenter and its cache synchronization remain. Neither is
   removed or enabled blindly by this audit.
4. Nougat's in-process EGL/HWC1 contract cannot simply be copied into Android13's
   separate composer service. The stock composer takes real same-process EGL
   objects. A bridge must preserve process ownership, handle lifetime, layer ABI,
   alpha, stride, transforms and completion before replacing CPU presentation.
5. The one-pixel read/resolve experiment in old patch0098 did not qualify full
   Android13 app rendering; later notes still recorded strips/lost text. Do not
   treat the fixture as a solved accelerated-window path.

## Cross-version hardware reconciliation

| Area | Working14.1 lesson | Preserved Android13 / disposition |
|---|---|---|
| Recovery / storage | recovery_done handoff; readonly userdata system file | Already present. Preserve bootloader/partition guards; never write faulty p15. |
| Kernel / touch / USB | Matched module ABI, initramfs end fix, shared-I2C recovery | Preserve current kernel lineage. Do not replace it with a generic donor kernel. |
| Buffer allocation | Original Vivante allocation stays alive through imports | Android13 already has an owner-retaining libui path. Do not reapply an older allocator rewrite over it. Cross-process imports remain essential to test. |
| EGL windows | Bounded deprecated dequeue retry, process-local initialization | Retry was absent; patch0001 added. Keep constructor/warmup fixes; GPU app path still blocked. |
| Scanout / wake | Real unplugged suspend passed once on14.1 | Android13 custom presenter differs. Patch0002 repairs stale post-wake state; actual panel/touch/GPU wake remains unqualified. |
| Audio | API2 short stream prefixes,44100Hz primary, ALSA/libacm closure, MD5 linker shim, AP/GSSP clocks, local HiFi keys, STREAM_IN_ACTIVE lifecycle | Android13 product selects audio.primary.default stub and generic policy. Missing integration, not merely a volume setting. Needs an API/stream adapter at the HIDL service boundary, exact library namespaces/dependency checks, policy and scoped SELinux labels. Do not copy Nougat audioflinger or replace modern crypto. Stub selection remains unchanged until the real adapter can be compiled/verified. |
| Wi-Fi | Global wpa socket and UID routing ABI20 mattered | Android13 uses standard AIDL supplicant, plus retained netlink/BPF/idle-timer and kernel routing patches. Kernel patch0095 already specifies UID_RANGE20. Keep this matched pair; do not transplant Nougat socket init or overwrite Android13 rules using its older userspace header layout. |
| Bluetooth | SD8777 packet transport, LE/GATT feature and successful OPP | Android13 already declares LE and has contiguous H4 packet writes plus installed-service/watchdog fixes. Preserve them. Pairing/OPP success on14.1 does not qualify Android13 A2DP/SCO/PAN. |
| Camera | Exact ION allocation, Vector/MemoryBase ABI, preview detach lifetime, uio0 encoder access | The Android13 custom product has no enabled stock-camera/provider integration. Needs a legacy camera provider plus ARM32 ABI/dependency adaptation; permissions alone cannot create support. Carry the proven ION and lifetime requirements into that adapter. |
| Navigation | HOME/BACK/APP_SWITCH layout and physical-only suppression | Android13 keylayout already maps139 APP_SWITCH,158 BACK,102 HOME. Device-name-scoped suppression and native navbar settings exist. Preserve injected/virtual-device behavior and test input separately from rendering. |
| Button lights | Owner's stock observation; no proven kernel brightness node | Still unresolved on14.1. No invented PWM, false brightness support or shared-touch power writes. |
| Memory / logging | Avoid periodic writes/streaming; measure actual interaction | Android13 v42 already persisted512MiB zram,swappiness100,page-cluster0 and disabled recurring writers. Keep scoped SELinux changes. Repeating tuning is not a graphics fix. |
| Startup / keystore / codecs | Driver problems must not hide feature failures | Preserve Android13's existing keystore/unlock/Codec2/GNSS/startup repairs. Nougat implementations are not interchangeable. GPS itself remains pending. |

## Offline validation and limits

- Actual modified dequeue callback compiled with host ASan/UBSan: six cases
  cover immediate/delayed success,100ms timeout, other-device isolation, an
  unrelated error and failed-fence cancellation/ownership.
- Actual modified enableScreen callback compiled with host ASan/UBSan: nine
  cases cover reset/retained pages, blanking, bad input, ioctl failure, changed
  mapping and invalid offsets. Initial fixture omitted TRUECOLOR; correcting the
  fixture made it represent the validated presenter geometry. No production
  geometry check was weakened to make the test pass.
- These use controlled external boundaries, not real GPU/driver/kernel calls.
  They are not a full ARM compile, full platform test or suspend qualification.
- Both incremental patches pass git apply --cached --check against the restored
  checkpoint and reverse checks against changed source; whitespace checks pass.
- The validated14.1 source and image pair remain unchanged. No ADB command,
  reboot, live override, build-image transfer or flash occurred.

## Next offline work

Restore enough Android13 headers/build context to compile actual changed ARM
libraries. Audit HWUI/Skia producer and cross-process mapper/composer together;
design a same-process legacy-HWC bridge without transporting EGL pointers across
processes. Integrate real audio via its HIDL boundary with the documented ANI7
contract. Inventory and adapt the camera provider. Keep radio/navigation patches
and add image-level checks so no build silently reintroduces stubs or old defaults.
Only after a complete corrected build passes its gates should a single combined
physical boot test be prepared. Do not flash these two standalone patches.

Full Android13 source syncing and a ROM build have NOT been started by this audit.
