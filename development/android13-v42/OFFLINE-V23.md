# Combined EGL window and Zygote correction

OFFLINE VERIFIED, NOT BOOT TESTED. Full Android build, exported image contents and hashes, partition fit, ext4 check and matching boot verification all passed. No tablet command, flash or boot occurred.

## Rendering

Patch 0038 replaces 0037, rather than stacking another workaround on it. The T110-only RenderEngine branch creates an EGL window around the exact client target, renders to the default framebuffer, calls eglSwapBuffers and completes GPU work before the separate composer reads the target. It preserves the existing retained gralloc allocation ownership and PXA ION synchronization.

The native window implements both old and fence-aware dequeue/queue/cancel entry points. It retains strong buffer references, supports two or three buffer slots, reserves a consumer slot, and never returns the published target to the driver. Spare buffers support a driver that dequeues the next frame during swap. Unsupported format, dimensions, protection and usage changes fail explicitly. Fences are consumed and closed. EGL teardown restores the renderer's original surface/context before releasing references. Projection, viewport and scissor are converted together from the off-screen convention to the EGL window convention.

This initial implementation creates a window for each composition. It favors explicit lifetime correctness over speed; creation and spare allocation can be expensive. It does not import the stock HWC into a separate process or change Android-wide HWC structure layouts. GLES2 limitations, app texture import, and the physical driver's behavior still require hardware validation.

## Startup

The saved failure occurs at the first Zygote fork immediately after preload/GC. The current Runtime::PreZygoteFork holds ScopedObjectAccess (the mutator lock) while calling MakeInitializedClassesVisiblyInitialized(wait=true). That function can block in Barrier::Increment, whose condition wait rejects the held lock. If checkpoints finish early, the wait is skipped, explaining why this ordering bug need not trigger on every attempt. The log has no usable native stack, so identification is based on the matching source path and timing, not a recovered backtrace.

Patch 0039 performs the class-visibility wait in kWaitingForCheckPointsToRun, before ScopedObjectAccess. It then reacquires normal object access for visiting JNI methods. ART's barrier and lock assertions are unchanged. This addresses the concrete pre-fork ordering violation; it is not proof that every remaining Android startup problem is fixed.

## Offline validation

* ASan/UBSan host tests exercise window slot exhaustion, consumer reservation, target publication, repeated cancellation, double buffering, rejected duplicate queue and invalid slots.
* A host regression compiles the actual pre-fork function extracted from both baseline and corrected ART source against lock-contract doubles. The baseline reproduces a mutator-lock wait failure; the corrected source passes 100 forced waits and 100 later-fork cases while requiring JNI visits to hold object access. This is not execution of the full ART runtime or an ARM boot test.
* Android ARM compilation/link passed. The actual system image contains the new renderer and rebuilt libart/libartd; all match build output. Raw size is 1,594,884,096 bytes; e2fsck passed. Windows raw and sparse hashes match native exports. Unpacked boot kernel/module/policy and startup event checks passed.

The original v22/v12 failed artifacts and logs remain unchanged. No boot-completed, visible-UI or hardware-success claim is made by this document.

## Outputs

* System: artifacts/lineage20-rom-v13/system.img (sparse) and system.raw.img (raw).
* Boot: artifacts/android13-full-v23/boot.img and padded KERNEL.img.
* Pairing and validation status: artifacts/android13-full-v23/system-pair.json.
* Build: system-image-20261106T175133Z.log, success in 07:55.

For a clean pinned source checkout, build_system_image.sh applies patches0038 and0039 (0037 is superseded). prepare_offline_v23.py migrates the existing v22 source tree and archives the cumulative graphics patch. The preserved first failed compile log records the matrix-constructor correction; the final artifacts come from the successful build.
