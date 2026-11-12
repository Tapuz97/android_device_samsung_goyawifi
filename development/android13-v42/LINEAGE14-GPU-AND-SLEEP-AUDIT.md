# SM-T110 Android 7.1 / LineageOS 14.1: graphics and sleep audit

2026-11-12. Source audit, not a working-ROM claim. No Nougat ROM build,
tablet reboot, flash, partition write or sleep/wake experiment was performed.
The Android 13 v42/BOOT48 pair remains installed and has an unresolved physical
black-screen report. An ADB connection or logical Awake state did not prove panel recovery.

## Decision

Proceed with a **small Nougat graphics/power compatibility target**, not a full
ROM build yet. Nougat retains the HWC1 path and a built-in gralloc0 adapter,
and its ART JIT uses ashmem rather than Android 13's blocked dual-view memfd
path. Those are concrete advantages. They do not establish that the old
Vivante driver can render a Nougat app correctly or survive suspend.

The first blockers are the **Marvell HWC binary layout and EGL handoff**, then
**buffer ownership/import and actual app drawing**. Sleep/wake has its own
**panel/runtime-PM, touch/shared-I2C and system-suspend sequence** to qualify.
No verified SM-T110 Lineage14.1 image or known-good complete Nougat donor has
been established. The T210 is a reference for related Marvell code, not a
drop-in board, kernel, partition table or proof of a working T110 ROM.

## Exact baseline and preservation

- Hardware: SM-T110/goyawifi, ARMv7 Cortex-A9/NEON, Marvell PXA986/988 family,
  Vivante legacy GPU. T113/T113NU firmware is a different platform.
- Use the matched T110XXUANI7 stock graphics stack as one coherent set:
  libGAL, libgcu, libgputex, EGL/GLES MRVL, gralloc.mrvl, hwcomposer.mrvl,
  libHWComposerGC and the matching galcore/kernel ABI. Do not mix arbitrary
  Vivante versions or T210 GPU binaries.
- Stock HWC SHA256: 66b02de15b357fb5127846f89288f81aebf5b93701e3d7c999b60922190f1f6f.
  Stock gralloc SHA256: da8e8887f877d5de012500cd390127742a68fb8b3b53d39b4560712f0c393c58.
- Keep current v42-GApps/BOOT48 and full v41-GApps/BOOT47 rollback, original
  stock/recovery backups, both Android data profiles, canonical source and
  patches. NEVER write physical SYSTEM p15. The existing read-only system
  file on userdata is the development mechanism.
- Local preservation details: backups/android13-before-lineage14-20261112/.
  The current-image/source archive passed every member hash on readback;
  the complete kernel-source archive also passed decompression/readback.
  See verification.json and kernel-source-export.json. The full E: source
  delta export completed:1242 projects,25 changed projects, no missing projects;
  all25 changed-project bases are reachable from their remotes. Online backup
  completion and post-download hashes are recorded in ONLINE-BACKUP.md.

## Graphics compatibility matrix

| Boundary | Verified finding | Work required before full ROM | Evidence / gate |
|---|---|---|---|
| Composer architecture | cm-14.1 SurfaceFlinger Android.mk selects SurfaceFlinger_hwc1.cpp / HWComposer_hwc1.cpp when TARGET_USES_HWC2 is not true | Select HWC1; do not bring the Android13 HIDL composer/allocator services into this target | Primary Android.mk, HWC1 source |
| Allocation | Nougat's GraphicBufferAllocator calls gralloc1, but Gralloc1::Loader adapts a gralloc0 module through Gralloc1On0Adapter | Use this adapter first; verify allocate, retain/import, unregister and free with real stock handles | Gralloc1.cpp:385 onward; adapter:313 onward |
| HWC layer ABI | The Marvell donor adds a 32-bit alpha before sourceCrop and repurposes reserved function slots; composition values differ, including cursor7 versus standard5 | Compile ARM32 sizeof/offsetof probes for both headers; match the exact stock binary accesses. Scope the compatibility header to this product, and initialize alpha deliberately | Local donor patches e36f0ea / ab83455; hwcomposer_defs.h |
| HWC EGL pointers | Nougat HWC1 prepare sets dpy/sur to 0xDEADBEEF for 1.1/1.2, while commit populates real EGL objects only for pre1.1 | Port the Marvell same-process display/surface handoff to BOTH prepare and set; preserve virtual-display/outbuf handling. Never change the reported HAL version just to evade this branch | HWComposer_hwc1.cpp:705-718 and798-818; donor641e765 |
| EGL wrapping | Marvell donor explicitly unwraps framework EGL display/surface for eglGetRenderBufferANDROID | Audit/port that wrapper rather than sending opaque framework EGL handles directly into vendor code | Donor641e765; cm14.1 eglApi.cpp |
| Framebuffer/HWC lifetime | Stock-oriented donor modifies framebuffer-HAL lifetime and exposes fbPrePost/stretchBlit/getBackBuffer | Determine which callbacks this exact HWC uses; do not blindly keep or close mFbDev based on an unrelated donor macro | HWC1 constructor:118-128; donor ab83455 |
| Buffer ownership | Android13 needed retained stock allocation ownership across the allocator/import boundary | Nougat removes the HIDL boundary, but apps still import buffers across processes. Prove original allocation stays alive until consumer release and that unregister/free are paired correctly | Gralloc1On0Adapter release/import paths; current work/ renderer |
| Native-window ABI | Android13 used an explicit old-layout compatibility window for the vendor driver | Audit Nougat ANativeWindow and ANativeWindowBuffer layout/callback ABI against the stock expectation. Test dequeue/queue/cancel, fences, usage, stride and references; do not assume its C++ GraphicBuffer layout is Android4.2-compatible | Canonical T110EglWindow source and stock buffer probes |
| Linker | Fresh readelf finds DT_TEXTREL in libGAL.so, not the other five inspected graphics roots | Use the existing TARGET_NEEDS_PLATFORM_TEXT_RELOCATIONS option for baseline bring-up, but also check the process target-SDK condition described below. Resolve actual imports with narrow shims | blob-textrel.json; cm14.1 linker/Android.mk:57 and linker.cpp:4064 onward |
| Application rendering | GLES2 compositor tests and visible animation are insufficient; Android13 GPU app windows had missing text/strips | Test HWUI glyphs, texture uploads, layers, alpha and scrolling in an actual accelerated app; keep no permanent software-rendering escape hatch as a PASS | Gate G3 below |
| Formats/geometry | Actual panel is1024x600; current port has a measured600x1024 logical portrait path | Choose one owner for rotation; preserve measured fb line_length, bpp, virtual page size and scanout extent. Query formats instead of copying BGRA/RGBX flags from T210 | T110Framebuffer / T110Scanout, historical physical verification |
| ION/cache/fences | T110 uses a PXA cache ioctl with five32-bit fields, command0xc0144907; stock handle path validated as2FD/34ints in the existing presenter | Check exact allocation type before using that layout; do not apply it to every handle. Verify GPU completion and CPU cache visibility separately; stock gralloc unlock alone was too late for CPU readers | T110Framebuffer.cpp; existing ION bounds patch |
| Vsync/sync | Tested kernel config has CONFIG_SYNC disabled; old donor can select fake vsync | Measure real callback/fence behavior. Use the existing no-sync/fallback paths only where applicable; never wait forever on a nonexistent fence or invent a signalled fence | HWC1 build flags and kernel config |

Initial product settings to evaluate (not a complete or tested device tree):

    TARGET_ARCH := arm
    TARGET_ARCH_VARIANT := armv7-a-neon
    TARGET_CPU_VARIANT := cortex-a9
    TARGET_USES_HWC2 := false
    TARGET_NEEDS_PLATFORM_TEXT_RELOCATIONS := true
    USE_OPENGL_RENDERER := true

Trace every donor macro to an actual cm-14.1 source consumer. Old BoardConfig
names such as MRVL_HARDWARE, BOARD_EGL_NEEDS_LEGACY_FB or TARGET_FORCE_CPU_UPLOAD
do nothing where the corresponding code was removed. Do not copy Android13
debug properties, renderer disables, HIDL manifests or no-JIT defaults into Nougat.

## Additional application-loader blocker: the textrel flag has a scope limit
+
+The cm-14.1 linker option is not an unconditional vendor-driver exception.
+Inside TARGET_NEEDS_PLATFORM_TEXT_RELOCATIONS it still rejects text relocations
+when the process target SDK is greater than22 AND differs from the linker's
+compile-time __ANDROID_API__. Resolve the actual macro value during component
+compilation rather than assuming it. Our fresh readelf confirms libGAL has
+DT_TEXTREL, and the stock-driver branch in cm-14.1 EGL Loader.cpp calls ordinary
+dlopen with no temporary target-SDK override. Consequently a platform/native
+probe passing does not establish that fresh accelerated third-party app
+processes with other target SDKs can load this GPU stack.
+
+G0/G3 must cover those process identities explicitly. If a narrow additional
+exception is required, restrict it to the product's exact trusted ARM32 libGAL
+path/label; preserve rejection of arbitrary app-supplied textrel libraries and
+normal linker/SELinux restrictions. Check fresh post-fork initialization and
+the actual app namespace/dependency resolution. Zygote preloading can conceal
+a loader failure while introducing invalid inherited Vivante objects; it is
+not a substitute for passing fresh-process app rendering.
+
+This is a source-confirmed limitation in the generic flag, not a report of an
+already-run Nougat app crash. The startup/loader compatibility target needs to
+resolve it before the full product build.
+
+## Sleep/wake: what the code actually does

1. **Panel off/on is runtime PM.** The matched PXA framebuffer driver maps
   FBIOBLANK into pm_runtime_put_sync_suspend / pm_runtime_get_sync. It changes
   is_blanked before those calls and does not propagate their errors in that
   entry point. A successful blank ioctl is therefore not proof that resume
   succeeded. Its resume enables the GOYA clock, enables the panel path, clears
   fb suspend, waits80ms, and restores the configured backlight path.
2. **The bridge owns regulators/reset and shares I2C.** The original VX5B3D
   panel-off path remuxes I2C1. Patch0061 keeps it available for GOYA without
   old early-suspend ordering. Keep this qualified fix; do not remove it merely
   because the Android version changed. The patch is not a blanket deep-sleep fix.
3. **Touch PM has two different implementations.** Current tested config has
   PM_SLEEP/AUTOSLEEP/WAKELOCK, no HAS_EARLYSUSPEND. The BT532 driver then selects
   runtime-PM callbacks when PM_RUNTIME is enabled, and only selects system-PM
   callbacks in the alternative branch. Resume performs POWER_ON_SEQUENCE,
   mini_init_touch and IRQ enable; suspend sends sleep and powers it off.
   This split must be checked during real whole-system suspend: do not assume
   runtime hooks alone handle every deep-sleep transition. Do not enable
   HAS_EARLYSUSPEND casually; it changes the panel/I2C/touch ordering again.
4. **Nougat userspace does not simply use CONFIG_PM_AUTOSLEEP.** Its libsuspend
   tries the old early-suspend backend first. The autosleep initializer is
   actually compiled out with #if0 in this branch; the fallback is wakeup_count.
   Validate actual /sys/power/state and /sys/power/wakeup_count behavior,
   writable labels/permissions, wakelocks and the selected backend. Avoid an
   init script and libsuspend both controlling suspend independently.
5. **The stock power HAL can affect devices too.** Its strings reference
   power_set_interactive, device power/control and runtime_status paths under
   input/graphics/video classes. Trace its exact per-device writes and effect
   alongside HWC blanking and init's TSP power/control=on writes; avoid two
   owners racing touch/panel runtime PM. The existence of a tiny stock HAL
   does not establish compatibility with the new lifecycle.
6. **Wake source is a separate requirement.** Board source marks physical Home
   as a wake source. Confirm actual Power/Home IRQ wake routing and wakeup
   configuration before USB-disconnected deep sleep. ADB-generated WAKEUP
   is not equivalent to a physical key waking a sleeping SoC.
7. **Double-tap-to-wake is not promised.** The present touch suspend path powers
   the controller off. It needs a supported low-power gesture/IRQ mode and
   wake wiring to become DT2W; a settings toggle alone cannot provide it.

The existing black-screen report has not isolated whether the last failure
was the framework display state, HWC blank/unblank, backlight, bridge, touch,
or a real system-suspend transition. Keep those hypotheses separate.

## Required gates, before a full Nougat ROM build

| Gate | Focused check | Pass requirement | Current status |
|---|---|---|---|
| G0 | Offline ARM32 ABI/linker checks with matched blobs and small Nougat compatibility components | Correct struct offsets/callbacks, vendor imports resolved, textrel exception active only where required, no Android13 HIDL dependency | Source audit complete; component compile/runtime not performed |
| G1 | Native GLES2 window renderer using the Nougat EGL/gralloc compatibility path | Real Vivante renderer; textured draw, alpha, glyph-like atlas and window swaps; correct GPU readback and scanout, no SwiftShader/software masquerading as acceleration | Not tested on Nougat |
| G2 | HWC1 composition with the same minimal userspace | Correct full-screen pixels across damage/full redraw, rotation, layer alpha, swaps and buffer release; no top stripes, missing text or stale handles | Not tested on Nougat |
| G3 | One small hardware-accelerated Android app against the minimal Nougat framework | HWUI text and scrolling visibly correct; accelerated app confirmed in fresh processes with platform and newer target SDKs; bounded memory/fd growth; no CPU-only fallback, EGL crash or missing labels | Not tested on Nougat |
| P1 | Panel-only blank/unblank with autosuspend inhibited for isolation | Correct visible frame/backlight and immediate physical touch after each of20 cycles; no I2C timeout, stuck pm_runtime count or dead display thread | Not tested on Nougat |
| P2 | System suspend with known wake source; first RTC timeout safeguard, then physical Power/Home | Suspend/resume counters advance, panel visibly returns, touch works, GPU draws a fresh frame after resume;20 cycles including USB disconnected | Not tested on Nougat |
| P3 | Short idle soak with recording stopped | No spontaneous reset, lost touch, black panel, monotonic memory leak or diagnostic-write stall; sleep actually reduces activity | Not tested on Nougat |

G3 needs a small Android framework/app build, not the complete product image
with all bundled apps, GApps, camera/media integration and release packaging.
G1/G2 and early power tests can use a separate minimal userspace with matched
libraries while preserving installed Android13 and recovery. This is a planned
test target, not a completed executable or permission to flash an unqualified image.
Do not run the tests in this audit turn or start the full source sync/build.

QEMU can check ARM ABI, bootstrap, linker, ART and parts of suspend-control
logic. It does not emulate the T110 Vivante GPU, VX5B3D bridge, BT532, PMIC or
wake IRQs; it cannot certify G1-G3 or physical P1-P3.

## Reusable Android13 work versus baggage

Carry over measured partition identities, safe loop-image bootstrap/recovery,
device keymaps, coherent firmware extraction hashes, shared-I2C fix, ION bounds
validation, scanout geometry, tested standard-reclaim configuration and the
lesson that permanent debug writers caused stalls. Evaluate each kernel
backport against Nougat requirements; do not import all Android13 changes
as a prerequisite. Nougat's older ART design makes JIT plausible, not proven.
Keep app/software features and GApps out of the first hardware qualification.

## Primary references and evidence

- [Lineage14 HWC1 build selection](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/services/surfaceflinger/Android.mk)
- [Lineage14 HWC1 implementation](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/services/surfaceflinger/DisplayHardware/HWComposer_hwc1.cpp)
- [Lineage14 gralloc loader](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/libs/ui/Gralloc1.cpp)
- [Lineage14 gralloc0 adapter](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/libs/ui/Gralloc1On0Adapter.cpp)
- [Lineage14 linker](https://github.com/LineageOS/android_bionic/blob/cm-14.1/linker/linker.cpp)
- [Lineage14 libsuspend backend selection](https://github.com/LineageOS/android_system_core/blob/cm-14.1/libsuspend/autosuspend.c)
- [Lineage14 ART JIT](https://github.com/LineageOS/android_art/blob/cm-14.1/runtime/jit/jit_code_cache.cc)
- [Marvell framework donor641e765](https://github.com/suyouxin/android_frameworks_native/commit/641e7659e44a6cc216b5a74860bccb88e5a11b1e)
- [Marvell hardware-header donor b804d20](https://github.com/suyouxin/android_hardware_libhardware/commit/b804d20e6bc23fbdbc62060cea71b195d1eeb8d9)
- [GOYA kernel base](https://github.com/visyone/android_kernel_samsung_goya/tree/3c50b450af74d42f8c5d360c692f71002b3bb0af)

The restoration archive evidence/lineage14-audit contains fetched primary files, Git blob
identities/provenance, fresh stock ELF textrel inspection, stock power HAL
disassembly and the exact BT532 PM-source excerpt. Stock binaries are private
inputs, not part of a public source contribution. Historical donor descriptions
are leads, not substituted hardware validation.
