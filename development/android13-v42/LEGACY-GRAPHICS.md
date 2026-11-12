# T110 Android 13 graphics compatibility

Current status is tracked in `CURRENT-STATUS.md`. A successful EGL context alone
does not establish a graphical Android boot.

## Hardware evidence

The v16/v6 trial (`hardware-tests/20261106-101227-core`) automatically loaded
the matched galcore module, opened ION under SELinux enforcing, created a real
GC1000 OpenGL ES 2.0 context and connected the 1024x600 display. SurfaceFlinger
then crashed during buffer import; Android did not complete boot.

Two failures are recorded in `buffer-failure.txt` and
`kernel-buffer-failure.txt`:

* A 1024x600 client-target allocation with usage 0x1b00 produced an invalid FD
  (-1), which Binder rejected.
* A 128x128 GPU allocation reached stock registerBuffer, but
  gckOS_MapSignal returned NOT_FOUND. RenderEngine subsequently passed a null
  buffer handle to the stock EGL library.

The generic HIDL Gralloc0 allocator calls `freeBuffers` after its reply callback.
The stock driver stores GPU signals and surface objects in its allocation
owner; keeping transported FDs open does not retain them. Disassembly of the
verified stock gralloc shows same-process registerBuffer returns without
creating another surface reference (PID comparison at offsets 0x2e2e-0x2e3a).
Simply selecting a passthrough allocator would therefore still leave the
imported clone referring to a freed original surface.

## Patch 0030

The opt-in `ro.t110.legacy_gpu` branch in libui allocates through the legacy HAL
in the requesting process. It imports a clone into the normal mapper while
the original is alive, then retains the original until the mapper clone is
released. Error paths release every earlier allocation. Imports from other
processes continue using the normal mapper path.

It removes the old HW_FB allocation flag, making the client target a regular
GPU buffer that the separate HWC service can import. The original usage stays
in Android's buffer metadata. Raw FD-only allocation requests are explicitly
unsupported in this engineering path because they provide no callback for
releasing the legacy owner. Those callers need separate integration if used.

The legacy HAL is loaded only when this device flag is enabled. libui's normal
APEX dependency graph is unchanged. No SELinux or driver identity checks are
disabled. A separate exact sysfs label permits the composer to read the
observed display timestamp at
`/devices/platform/pxa168-fb.0/graphics/fb0/vsync_ts`.

## Verification

`scripts/test_legacy_gralloc_ownership.py` extracts the actual helper from the
patched source and exercises it with a strict mock HAL under ASan/UBSan. It
checks retained lifetime, unregister-before-release order, partial allocation,
import and stride-mismatch rollback, invalid request rejection, and isolation
of external handles. Evidence: `evidence/gralloc-owner-lifetime-regression.txt`.

The v17/v7 hardware trial confirmed allocation/import now succeeds. It reached
Skia shader setup instead of the null-handle crash. It exposed a missing dynamic
dependency: stock `/lib/libGLESv2SC.so`, SHA-256
`ad6e492a98834b34079eb32024fc70e77b8df543b5118e762a4fe8d96c64706f`.
Tombstone 28 confirms this library loaded after a temporary directory overlay.

The optional Skia shader warmup still aborted on an unsupported image
(`dataspace:513`). The supported `service.sf.prime_shader_cache=0` setting let
SurfaceFlinger remain alive, generate hundreds of internal boot-animation
frames, and allow system_server startup. The user still saw the Samsung logo.
These fixes are included in the pending v8 build; the panel output remains
unverified. The temporary overlay and property ended when the trial returned
to recovery.

The stock HWC 1.2 adapter reports CLIENT composition and no hardware vsync.
A planned reversible test will hide only the hwcomposer module in a temporary
copy of `/vendor/lib`, selecting the existing HWC2OnFbAdapter fallback through
HwcLoader. This should distinguish proprietary HWC handling from the stock
gralloc framebuffer post path. No result is claimed until the actual tablet
test and a visible screen change.
