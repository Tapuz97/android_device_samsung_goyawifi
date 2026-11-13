# Prior graphics and startup reconciliation ג€” 2026-11-13

This supersedes any implication that successful EGL creation, shader compilation,
boot_completed, or a focused pixel fixture proves a usable ROM.

## Current observed failure

Installed boot SHA256 0e226023c53ec8c50edbb1a207b72b4ec7c728889dc68fb7ef1d840aede5fad5,
system SHA256 64a39bd58b1aabc6bf670b7ce1a517d6e96334447454a156be7b4a9fc5f9698c.
Android7.1.2 completed startup at approximately58 seconds from host observation.
Owner reported black/glitched screen. SetupWizard had an actual ANR, waiting on
RenderThread while EGL Init loaded the stock libraries. Later the threads became
idle, so this is not established as an endless lock deadlock. Camera also crashed.
Current evidence: tests/lineage14-shader-gpu-node.

## Sources actually read

Archive root: Ubuntu:/root/t110-lineage14/reference/device-checkpoint/development/android13-v42.
Read LEGACY-GRAPHICS.md, GRAPHICS-DONOR-AUDIT.md,
LINEAGE14-GPU-AND-SLEEP-AUDIT.md, PERSISTENT-TUNING.md, current checkpoint and
achievements, relevant functional-checklist entries, patches0034/0036/0037,
0053/0054,0047/0048/0078 and0098, and scripts prepare_hwui_resolve.py,
qualify_v35_ui.py and checkpoint_ui_anr_20261112.py.
Read current Nougat EGL loader/wrapper, HWUI EglManager, HWC1 composer,
Surface queue hooks, Gralloc1On0Adapter ownership, GraphicsEnvironment and
Lineage DisplayColorCalibration. Also compared the local jakaco Nougat patches.
Historical documentation is evidence, not an instruction to rerun old installers.

## Boundary-by-boundary disposition

| Boundary | Prior result | Current Nougat disposition |
|---|---|---|
| Recovery exit / safe storage | recovery_done required; physical SYSTEM p15 faulty | Carried over. Verified wrapped boot and loop system; never write p15. |
| Kernel / USB | initrd range, FunctionFS descriptor lifetime, shared-I2C/touch fixes | Preserved kernel lineage and module ABI. Original USB serial and early authenticated ADB restored. Nougat ADB already uses synchronous I/O. |
| Native init services | A bootstrap must import the real service graph | Fixed /system/etc/init import; actual packed-image check covers45 services. |
| Vendor set / shader compiler | Coherent ANI7 GPU set; compiler is loaded dynamically, absent from DT_NEEDED | Matched blobs and libGLESv2SC now included; actual image/hash checks. Hardware compiled26 shaders. |
| GPU process initialization | libGAL has no ELF initializer; fork/import-only clients need constructor | Current libEGL and libui initialize via their loaded module handles before callbacks; actual binaries checked. |
| GPU device / display permissions | Correct GPU node and exact vsync node required | Nougat /dev/graphics/galcore mapped and permissions verified on hardware. |
| Gralloc lifetime | Android13 HIDL allocator freed owner too early | Nougat has no HIDL allocator boundary. Reviewed adapter: allocated handles retained in mBuffers until final release; imported handles register/unregister separately. Do not transplant Gralloc2 owner map blindly. Cross-process hardware rendering still needs qualification. |
| HWC ABI / EGL objects | Stock Marvell layer stride100, alpha field, same-process display/surface objects | Actual ARM ABI checks and explicit prepare/set handoff present; wrapper unwraps framework EGL handles. Alpha set on normal setPlaneAlpha and framebuffer target. Default-state alpha initialization can be hardened; no evidence it alone causes current black frame. |
| EGL window producer resolve | Patch0098 one-pixel read passed six focused fixtures; glFinish alone did not | Missing from current HWUI. Restore as a scoped candidate. Crucially, subsequent full Android13 app windows STILL lost text/strips; safe boot forced software windows. This is NOT a proven complete graphics fix. |
| EGL queue timing | Old vendor can queue asynchronously after swap returns | Current boot records max-dequeued exhaustion and vendor cannot-dequeue error for BootAnimation. Nougat donor has bounded retry. Restore retry only for deprecated legacy dequeue, retaining queue/fence ownership. |
| Startup GPU contention | Zygote GL preload unsafe; background initialization storm is a Nougat-specific issue | Zygote preload already off. Donor limits eager EGL init to home/persistent apps; current SetupWizard ANR and many simultaneous EGL loader threads support adapting it only for T110. No ANR timeout increases. |
| Scanout / orientation | Android13 required explicit window resolve, CPU ION cache sync, padded portrait scanout and one rotation owner | Nougat uses native HWC1/window path, not the Android13 CPU-copy HWC2 presenter. Preserve physical1024x600/logical600x1024, rotation270. Do not transplant CPU-copy geometry/cache ioctl into unrelated GPU buffer paths. Correct pixels/scanout not yet established. |
| SurfaceFlinger capture | GPU success not proof of scanout; CPU cache visibility separately matters | Awake screenshots are black too, but screenshot uses GPU/copy paths and is not independent proof of black producer buffers. Preserve both capture and physical observation. |
| LiveDisplay | Native Lineage color transforms may force GPU composition | Current secondary color transform was active; clearing it temporarily enabled HWC but screenshot stayed black. Therefore disabling LiveDisplay is NOT a demonstrated fix. No permanent feature removal. |
| Retirement / vblank | No kernel sync fence support; old buffers must not be reused before scanout completes | Native no-sync fallback selected. Donor retirement worker is not imported wholesale: current dump has GLES composition, while its optional worker applies to HWC-only composition. Need exact evidence before changing lifetime. |
| HWUI partial damage | Old stack may not support modern preservation assumptions | Donor has a short property alias (original exceeds Nougat property-key limit). Current driver lacks buffer-age extension; no evidence yet that this alone explains black UI. Do not claim fixed by adding a property with no consumer. |
| Android13-specific startup failures | ART checkpoint, GNSS service detection, keystore, Codec2, HIDL services | Different Nougat code paths; do not transplant unrelated workarounds or disable normal features. Current recorded ANR is EGL warmup, not proven old ART assertion. |
| Logging / memory | Continuous writers caused hangs | No periodic writer or live serial feed. Keep bounded host-side captures. Do not hide ANRs or claim idle process liveness is usability. |
| Sleep / wake | Android13 final owner report still black after logical wake | Still unqualified. Current logical powerMode2 and correct framework display dimensions do not prove panel recovery; retain kernel shared-I2C fix. No sleep-cycle test or deep-sleep PASS. |

## Changes justified by this comparison

1. T110-only eager-EGL warmup restriction, adapted from the actual Nougat donor.
2. Bounded100ms legacy dequeue retry, supported by this boot's queue error.
3. Prior producer-side one-pixel resolve as an explicitly unqualified compatibility candidate.

These can be built offline together. They do not yet establish a complete fix
for producer pixels, texture import, composition or physical scanout. No new
flash until the comparison and offline checks are complete. Do not repackage
the unchanged failing image as a corrected release.

No blanket software-rendering switch, graphics feature deletion, timeout
increase, donor kernel transplant, or new continuous logging is justified.
The previous one-pixel fixture data is not present in this source-only archive;
the preserved preparation script checks it and later qualification scripts
explicitly record the continued native-window failure. Do not invent fresh passes.

## Same-boot diagnostic state

Temporary USB stay-awake was enabled (original setting saved in
tests/lineage14-shader-gpu-node/keepawake-original.txt). Secondary color matrix
was cleared with SurfaceFlinger1030 for one comparison; no persisted user setting
was changed. Restore stay-awake at the end of work. Owner asked to stop repeating
old investigations; no further live experiments or reboot during this audit.

## Offline build result

Full systemimage/bootimage build completed successfully in7m24s.
Compiled ARM inspection confirms glReadPixels precedes HWUI swap and the legacy
queue contains a clock-bounded relative condition wait. Compiled framework
contains the T110 warmup guard. All five changed runtime components/properties
were extracted from the actual new sparse system image and matched their build
hashes. The same known make_ext4fs inode-bitmap padding defect was normalized
in a disposable verification copy, then the read-only filesystem check passed.
The input sparse image remains unchanged; the existing packager performs that
normalization when preparing an installable raw image. All16 ARM ABI assertions,
kernel/module provenance and43 vendor ELF dependency checks passed.

Candidate system.img SHA256:
cfd8f3a3effaba6da95c438f677b1f01c5a4a9103bb7cca20d10ae42f65aa42d.
Evidence: Ubuntu:/root/t110-lineage14/records/window-contract/verification.json.
Not installed. No new boot. The currently installed black-screen pair remains
explicitly failed; this candidate is not a claim that full app graphics is fixed.
Temporary stay-awake has been restored to0 and verified.
