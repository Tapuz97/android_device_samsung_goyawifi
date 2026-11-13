# Android13 lessons carried into Lineage14 - 2026-11-13

This comparison uses the restored Android13 v42 source, scripts and evidence under
`/root/t110-lineage14/reference/device-checkpoint/development/android13-v42`.
Do this comparison before diagnosing a familiar failure as a new problem.

| Prior result | Nougat disposition and evidence |
|---|---|
| Recovery loop | Use exactly `/sbin/reboot recovery_done`, from install_canonical_boot46.py and AUDIT.md. Confirmed on this tablet. |
| Faulty physical SYSTEM | Keep verified userdata-backed read-only system, separate data, p10-only boot writes and intact p9 recovery. Never write p15. |
| Bootloader initrd span | Current GOYA archive-end kernel correction is built on the preserved v42 kernel source/config. |
| Existing kernel fixes | Current kernel commit e7d7b1f descends directly from preserved 3eb98fe7; all prior kernel changes remain, including USB parser, Binder, ION, shared-I2C, touch and reclaim work. Same config and module release verified. |
| Raw init_module | Use bounded size_t on ARM32. Actual last_kmsg now confirms galcore loads and identifies GC1000. |
| Init handoff and no mount_all | Use N7 --second-stage, real cache directory, standard nonencrypted trigger. Import /system/etc/init explicitly because mount_all is absent. Current test confirmed native services start. |
| USB startup | Restore explicit early start adbd and iSerial from old work/core-boot/init.mrvl.rc. Current test connected as placeholder 0123456789ABCDEF; ro.serialno independently verified actual3004523270272200. |
| Old FunctionFS transport | N7 usb_linux_client.cpp already uses synchronous adb_read/adb_write; Android13 AIO workaround is unnecessary. The current N7 boot actually enumerated and transferred logs. |
| EGL absolute driver paths | Old scripts/patch_egl_vendor_paths.py identifies four /system/lib/egl strings. N7 instead preserves original blob hashes and adds aliases for the three real GLES2 drivers to the same vendor inodes. GLES3 is absent in stock and remains unsupported. Actual failed boot showed missing GLES2 path and EGLContext creation failed. |
| Per-process GPU setup | Adapt patches0047/0048/0078 to N7 EGL loader and common Gralloc1 loader. Resolve gcoOS_ModuleConstructor through the loaded driver's handle, before EGL entrypoints or gralloc callbacks. No success cache across fork; covers import-only clients. |
| Display timing permissions | Restore exact /sys/devices/platform/pxa168-fb.0/vsync chown/chmod from old init.mrvl.rc. Current boot independently reproduced permission denied at the equivalent class path. |
| GPU/ION permissions | N7 ueventd already preserves0666 system:graphics for the two actual device nodes. Current bring-up is permissive; production enforcing qualification remains required. |
| Driver ABI and dependencies | Actual ARM32 HWC offsets, same-instance EGL handles, legacy exports and42 private ELF closures remain checked. No replacement stock platform libraries. Native N7 HWC1 supersedes the Android13 software presenter. |
| Orientation/scanout | Retain physical1024x600, rotation270 and density160. Do not carry Android13 software-transpose/stride workarounds into native HWC1 without evidence. |
| Emulated storage | N7 persist.sys.sdcardfs=force_off selects its real FUSE path, avoiding the old Samsung sdcardfs mismatch. |
| Memory/logging | No continuous snapshot writer/live feed. Standard zram enabled with swappiness100/page-cluster0. Prior Android13 stalls were exacerbated by continuous capture. |
| Keys/navigation | Original GPIO and touch-key mappings and native Lineage touch-nav filtering are retained. LED backend still unproven; do not expose fake controls. |
| Android13-only repairs | APEX, keystore2, HIDL GNSS discovery, Codec2, Skia software-window and Android13 UI fixes do not automatically apply to N7. Preserve their failure lessons, not incompatible framework code. |

## Current hardware result

Service-import candidate reached real Android7 services and shell ADB.
Boot was blocked by SurfaceFlinger repeatedly aborting on EGLContext creation;
logs show missing hard-coded EGL/GLES driver paths and vsync permission denied.
Logs are in tests/lineage14-service-import-fix. Boot completion is NOT established.
The tablet was returned to TWRP through authenticated ADB before further editing.

## Combined candidate

Boot SHA256: 5e2a0bab384c020f174596c23353a30f048c539eb501d5af4986262de55e5b11
System SHA256: 5a24d1b543508c2b177199a15d35073e7950f38c0e054a5e753f4f256ac30aa0
Actual-image checks cover native service imports, all three required hard-coded
driver aliases, explicit constructor calls in libEGL/libui, display permissions,
early USB/serial settings,164 critical file comparisons and clean ext4.
Both full original proprietary drivers and matched kernel/module hashes remain.
Full ARM rebuild completed successfully. Hardware validation remains pending.

## Follow-up: runtime-only compiler and Nougat device-node placement

The next hardware boot retained SurfaceFlinger PID145 and started bootanimation,
Zygote and system_server. It did not complete startup or establish usable graphics.
Logs are in tests/lineage14-restored-prior-fixes. Shader compilation failed, and
camera/app processes failed GPU access. Actual device listing proved that N7
ueventd creates /dev/graphics/galcore (0660 system:graphics), not /dev/galcore.
The previous permission rule named the missing path. This distinction must be
checked on the actual Android version, not inferred from the old init script.

The shader compiler was explicitly documented in Android13 LEGACY-GRAPHICS.md
and scripts/extract_shader_compiler.py, but the initial N7 vendor integration
followed only DT_NEEDED and omitted that runtime dependency. This omission is fixed:
libGLESv2SC.so527012bytes, SHAad6e492a98834b34079eb32024fc70e77b8df543b5118e762a4fe8d96c64706f.
A scan of literal shared-library names in all selected private drivers found this
as the only missing library also present in the exact stock extraction. This scan
does not establish all dynamically generated paths or all hardware functionality.

The final combined correction explicitly roots this compiler in vendor extraction,
labels and grants0666 system:graphics on the actual /dev/graphics/galcore node,
and creates the legacy /dev/galcore alias after coldboot. Both early and actual
paths are now checked in the packed ramdisk.43 ELF closures and165 extracted
image-file comparisons pass, along with fsck and the existing GPU ABI checks.

Full rebuild passed. The export uses the prior verified image plus one added
compiler inode with explicit uid/gid/mode and SELinux label. Read-only fsck passes.
Reversible4KiB delta557056bytes preserves the remainder byte-for-byte, following
our Android13 update method. Ordinary build output contains the same selected files.

Boot0e226023c53ec8c50edbb1a207b72b4ec7c728889dc68fb7ef1d840aede5fad5
System64a39bd58b1aabc6bf670b7ce1a517d6e96334447454a156be7b4a9fc5f9698c
Rollback for the preceding pair: artifacts/prior-graphics-parent in native root.
Delta and reverse chunks: artifacts/shader-gpu-node-delta.

On the owner's engineering userdata only, standard Lineage persist.sys.root_access
was set to2 and adb root was enabled for diagnostics. ROM defaults still require
ADB authentication and do not enable root access for apps.
