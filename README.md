# Release preparation — 2026-11-14

See [the release guide](release/README.md) for the current installed image pair,
post drafts, downloads and measured limitations. This branch preserves the exact
tested source plus release materials. Older bring-up notes below are historical.

---

# Samsung Galaxy Tab 3 Lite SM-T110 - LineageOS 14.1 bring-up

Android7.1.2 full tablet product. Hardware qualification follows the first complete
build; source compilation alone is not a claim of a usable or secure ROM.

## Hardware and preserved baseline

Marvell PXA986/988, Vivante GC1000, ARMv7-A NEON. Use the matched T110XXUANI7
stock graphics/camera/audio HALs and their private library closure. The proprietary
inputs and generated prebuilt kernel/modules are excluded from this source tree.
Their hashes are in the local vendor-inputs.json and build-verification.json.
The original kernel baseline is the preserved Android13 BOOT48 checkpoint, SHA256
b9409c55499df551ecd960f38a5f313304c6ca9e4d3f81c77243fda72a2ed8a6.
Its complete source is Tapuz97/android_kernel_samsung_goya tag
t110-android13-v42-20261112 (3eb98fe728aefa780638a1bb2f487e19ba6fadcb).
The Wi-Fi/Bluetooth/GPU modules must match this exact kernel.

## Source integration

- Native Nougat HWC1 and gralloc0 adapter, no Android13 HIDL graphics services.
- Product-scoped Marvell ABI: ARM32 layer100, crop28, frame44, region60,
  acquireFence68, planeAlpha76; device116, getDisplayAttributes96, fbPrePost100.
  These match the historical Marvell header in a fresh 32-bit compile probe.
- Explicit same-process primary DisplayDevice EGL handles survive prepare/set;
  eglGetRenderBufferANDROID unwraps the framework display/surface for the driver.
- Legacy non-const Binder getCallingPid forwards to the actual const method.
- Read-only trusted libGAL textrel exception for fresh application identities;
  arbitrary app-provided textrel libraries retain the normal linker rejection.
- Original 270-degree panel mounting and mdpi density160.
- Normal Nougat ART/JIT and accelerated application rendering remain enabled.
- Standard LineageOS launcher, settings, keyboard and wallpaper facilities.
- Qualified prior board radio loaders and physical Home/Back/Recents keymaps.

## Build and image layout

lunch lineage_goyawifi-userdebug
make -j12 systemimage bootimage

Use the accompanying source patches against the recorded pinned manifest.
A prebuilt kernel requires genuine exported headers from the same source in
out/target/product/goyawifi/obj/KERNEL_OBJ/usr before building tinyalsa/ION users.

The final packager keeps the proven boot header/kernel, installs the new static
bootstrap and Nougat ramdisk, and recovers the original init/ueventd dispatch.
Physical SYSTEM p15 is faulty and MUST NOT be flashed. The new system is a
read-only loop file /data/local/tmp/t110-lineage14-system.raw; the data profile is
/data/local/tmp/t110-lineage14-data, separate from the preserved Android13 profile.
No standard OTA ZIP with partition-writing assertions is generated for this layout.

This first bring-up build uses permissive SELinux and includes no Google apps.
Full hardware/UI/sleep/wake and enforcing-policy qualification remain required.

## Current verification and limitations

See OFFLINE-VERIFICATION.md and docs/FUNCTIONAL-TESTS-LINEAGE14.md. The complete
candidate passed offline checks; hardware boot has reached native services and ADB,
but SurfaceFlinger failed to create an EGL context in the preceding test. Native
Buttons settings preserve physical navigation and allow touch navigation to
suppress only the built-in Home/Back/Recents inputs. Independent LED controls
are implemented for a genuine backend, but remain hidden on this kernel until
its physical LED control is established. GPS remains a separate integration item.

compat-patches contains all seven exact platform project diffs, newly authored
source and the pinned repo manifest. Apply each patch in its projects.json
project at the recorded upstream HEAD, then copy the corresponding untracked
files into that project. No old stock platform libraries should shadow Nougat
EGL, XML or ICU. Proprietary inputs and kernel/module binaries are excluded.
The original kernel source and fixed checkpoint tag above remain preserved.

tools contains the actual final packaging and verification scripts. Their native
working root is /root/t110-lineage14. Initial transformation scripts are not the
canonical source. Use only the final wrapped boot/system pair after verification;
the ordinary out/.../boot.img does not contain the loop-image bootstrap.

Current kernel provenance is pinned in kernel-source.json. It adds only the GOYA
initramfs archive-end fix with byte-identical configuration and matching module
release. The exact installed-recovery exit is /sbin/reboot recovery_done; see
docs/RECOVERY-HANDOFF.md. The saved Android13 EGL-path, process-initialization, display-permission and USB
startup fixes are now adapted to Nougat. See docs/PRIOR-WORK-CARRYOVER.md and run
tools/verify_prior_graphics_fixes.py against the actual artifacts before flashing.
A usable Android screen and completed startup are not yet confirmed.
