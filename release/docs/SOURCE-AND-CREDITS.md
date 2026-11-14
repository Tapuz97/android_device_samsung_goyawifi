# Source, licenses and credits

- Device and eleven platform-project patches, exact tested source: https://github.com/Tapuz97/android_device_samsung_goyawifi/commit/ceebd0c9a6c3298765757522f88d75d0bd47b4eb
- Release branch: https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/release/lineage14.1-t110-20261114
- Exact upstream pins: `compat-patches/pinned-manifest.xml` and `projects.json`.
- Kernel source matching this image: https://github.com/Tapuz97/android_kernel_samsung_goya/commit/e7d7b1f23e999539c74761216d20f432fd63e052
- Kernel baseline: https://github.com/Tapuz97/android_kernel_samsung_goya/commit/3eb98fe728aefa780638a1bb2f487e19ba6fadcb
- Kernel metadata/config/toolchain: repository `kernel-source.json` and `release/docs/kernel.config`.
- LineageOS: https://github.com/LineageOS ; AOSP: https://android.googlesource.com/
- Samsung open source: https://opensource.samsung.com/
- gr8nole T110 recovery: https://androidfilehost.com/?fid=23329332407589909
- goyawifi reference and ramdisk-size correction: https://github.com/jakaco/lineageos-14.1-goyawifi
- T210 donor reference (different device, not flash-compatible): https://github.com/cmlt02/android_device_samsung_lt02wifi

Retain upstream copyright/license headers and applicable GPL/Apache notices.
Kernel and other copyleft binaries require corresponding-source compliance for
public distribution; a link to a vaguely similar kernel is not sufficient.
Stock Samsung/Marvell/Vivante libraries are proprietary vendor inputs; our source
patches do not transfer their ownership or grant a new redistribution license.

The build includes these inputs in the private/draft binary package. Before public
binary publication, finish the corresponding-source/notice audit and recovery
provenance check. Open GApps prebuilt mirrors are expressly prohibited by its
project; the guide links upstream and does not upload those packages.

The user's example XDA guide was used only as a requested reference link:
https://xdaforums.com/t/unlock-bootloader-unbrick-teclast-m50-m5m4-bootloader-unlock-android-14-row-v1-08-v0-1-0.4806075/
Its page could not be retrieved during preparation; this post is original text,
not a claimed reproduction or technical adaptation of that unrelated device guide.
