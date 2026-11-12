# Graphics donor audit — 2026-11-06

Status: research and source comparison only. No tablet command, flash, boot, ROM rebuild or runtime source change in this pass. The failed v22/v12 pair remains failed; last verified device state is TWRP.

## What actually has evidence of visible graphics

The T210/R CM11 port is a useful partial-success reference. Firsthand testers reported a visible Android interface and correct colors, but later reports still describe slow UI, severe 2D flickering and rotation artifacts. This establishes visible graphics, not a stable implementation or compatibility with Android 13. Original XDA thread 2783617 was inaccessible through the research tool; do not claim its developer posts were inspected.

Primary firsthand reports: https://www.htcmania.com/archive/index.php/t-843517.html (June 2014, January 2015, September 10 and 13 2015).

The gr8nole master device-tree README explicitly says it is incomplete and intended to contain the files required for recovery. A repository name, build flag or patch subject is not a successful ROM test. Local T210 CM11 and CM13 trees are already present; the latter is not proof of working Android 6.

## Exact donor changes inspected

The local cmlt02 Marvell_Patches/cherry-pick.sh points to suyouxin's android-5.0.0-xo4 branch. That is an adjacent Marvell donor, not an independently verified T110 or T210 hardware success. The inspected commits and their file patches are archived in evidence/graphics-donors/.

* Framework commit 641e7659e44a6cc216b5a74860bccb88e5a11b1e: preserves the real EGL display and window surface in the legacy HWC list; avoids replacing them with sentinel values or outbuf fields; wraps eglGetRenderBufferANDROID with the required display/surface unwrapping; obtains the display format from HWC; adjusts eglSwapBuffers handling for an empty layer list. It also contains unrelated allocator and debugging changes.
* Hardware commit b804d20e6bc23fbdbc62060cea71b195d1eeb8d9: adds Marvell composition types, flags and display-format query. It changes the numeric cursor composition type from 5 to 7. Copying this header globally into Android 13 would change an ABI used by other code.
* Framework commit f3f73dd6fcf0cbe7828a2fdeef46aed395016a20: changes BufferQueue waiting and removes a buffer-count workaround. There is no current evidence that buffer-count exhaustion explains our black frames.

Sources:
- https://github.com/suyouxin/android_frameworks_native/commit/641e7659e44a6cc216b5a74860bccb88e5a11b1e
- https://github.com/suyouxin/android_hardware_libhardware/commit/b804d20e6bc23fbdbc62060cea71b195d1eeb8d9
- https://github.com/suyouxin/android_frameworks_native/commit/f3f73dd6fcf0cbe7828a2fdeef46aed395016a20
- https://github.com/gr8nole/android_device_samsung_lt02wifi

## Comparison with our current renderer

| Boundary | Donor implementation | Current T110 Android 13 implementation | Decision |
|---|---|---|---|
| Render target | EGL window surface, swapBuffers, legacy HWC sees same-process EGL objects | GLESRenderEngine renders to an EGLImage-backed texture FBO | Main compatibility difference to investigate; not yet proven causal |
| Presentation | Vendor HWC and its Marvell extensions | Separate composer service copies a linear ION client target into fb0 | Legacy EGL pointers cannot be passed across this process boundary |
| Format | Query actual HWC display format; device config includes BGRA/RGBX workarounds | Validated RGBA/RGBX source plus explicit framebuffer-channel conversion | Preserve measured format conversion; don't blindly enable old BGRA macros |
| Synchronization | Legacy buffer lifecycle and blocking queue behavior | Retained gralloc owner, glFinish and PXA ION CPU-read synchronization | Already attempted in v12; no claim it cured black output |
| Texture upload | T210 BoardConfig sets TARGET_FORCE_CPU_UPLOAD | Modern GLES/Skia paths; old build flag alone has no demonstrated consumer here | Flag is a lead, not an implemented fix; traced CM11 TextureCache file did not contain it |

Current GLESRenderEngine bindFrameBuffer uses glEGLImageTargetTexture2DOES and glFramebufferTexture2D. Our v22 fbo.reset() drops the wrapper binding and returns to framebuffer zero; it does not itself issue glFramebufferTexture2D(..., 0) to detach the target texture. Therefore the comment claiming a tile-to-linear resolve is a hypothesis, not a verified driver guarantee. The logged handoff and glFinish do not prove nonblack pixels were produced.

The old stock HWC's same-process EGL/native-window requirement was already identified locally. This audit strengthens the donor basis for investigating it; it does not erase the earlier incompatible-HWC experiment or establish a new fix.

## Recommended implementation direction

Retain Android 13 and the measured T110 framebuffer presenter. Develop a device-only EGL window compatibility path at the renderer boundary, using the donor's actual window-buffer lifecycle rather than transplanting all of old SurfaceFlinger or changing global HWC structs. The same-process EGL window must wrap the exact allocated client target and correctly implement dequeue, queue, cancellation, buffer references and synchronization. The legacy driver must complete its window swap before the target is handed to the separate presenter. Using an EGL window is a proposed compatibility route, not a guarantee that it fixes rendering.

Before integrating that larger change, compare the old and current paths in a focused native rendering harness: known clear and textured draw, GPU readback, mapped native-buffer readback, and window-swap vs EGLImage-FBO output. Compile it offline with the matched T110 blobs and explicit handle/format checks. Running the Vivante GPU requires this hardware; QEMU cannot validate those pixels. Any later hardware run needs to be planned with the user's restriction against repeated boot experiments, rather than silently starting a new boot loop.

If the source texture is already black, the fix belongs in its producer/import path, not in the final window swap. If GPU readback is colored but native memory is black, focus on resolve/cache visibility. If memory is colored but the panel is black, revisit scanout. These distinctions avoid claiming one architectural difference is the proven cause.

The independent ART GC/mutator lock assertion from v22 still needs correction. No graphics donor patch addresses it. Do not disable the assertion or describe a graphical build as a working ROM until Android startup and an actual visible UI both succeed.
