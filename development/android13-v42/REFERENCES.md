# Primary references for resuming T110 work

- [Lineage14 SurfaceFlinger build](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/services/surfaceflinger/Android.mk)
- [Lineage14 legacy HWComposer](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/services/surfaceflinger/DisplayHardware/HWComposer_hwc1.cpp)
- [Lineage14 gralloc loader](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/libs/ui/Gralloc1.cpp) and [gralloc0 adapter](https://github.com/LineageOS/android_frameworks_native/blob/cm-14.1/libs/ui/Gralloc1On0Adapter.cpp)
- [Lineage14 linker textrel option](https://github.com/LineageOS/android_bionic/blob/cm-14.1/linker/Android.mk) and [runtime check](https://github.com/LineageOS/android_bionic/blob/cm-14.1/linker/linker.cpp)
- [Lineage14 suspend selection](https://github.com/LineageOS/android_system_core/blob/cm-14.1/libsuspend/autosuspend.c)
- [Lineage14 ART JIT](https://github.com/LineageOS/android_art/blob/cm-14.1/runtime/jit/jit_code_cache.cc)
- [Marvell framework donor641e765](https://github.com/suyouxin/android_frameworks_native/commit/641e7659e44a6cc216b5a74860bccb88e5a11b1e)
- [Marvell hardware donor b804d20](https://github.com/suyouxin/android_hardware_libhardware/commit/b804d20e6bc23fbdbc62060cea71b195d1eeb8d9)
- [Original GOYA kernel base3c50b45](https://github.com/visyone/android_kernel_samsung_goya/tree/3c50b450af74d42f8c5d360c692f71002b3bb0af)
- [T110 CM11 source](https://github.com/T110-android/android_device_samsung_goyawifi/tree/cm-11.0), a historical reference, not a verified Lineage14.1 ROM.
- [T210 CM13 donor](https://github.com/cmlt02/android_device_samsung_lt02wifi): its README calls it incomplete/recovery-oriented. T113 is a different platform.
- [Official Gerrit submission guide](https://lineageos.github.io/lineage_wiki/how-to/submitting-patches/)
- [GitHub draft release access](https://docs.github.com/en/rest/releases/releases): draft listings require push access; our individual release/asset URLs were also checked anonymously and returned404.

Pinned revisions, exact diffs, original donor patches, ELF audit, source excerpts and hardware logs are in the restoration archive. Public source and review links are in LINKS.md.
