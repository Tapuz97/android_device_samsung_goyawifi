# Standard compressed-swap reclaim for the SM-T110 port

The qualified pre-BOOT47 kernel retained Samsung's ZRAM_FOR_ANDROID and
ZRAM_FOR_RTCC2 options. In mm/vmscan.c, the first option sets may_swap=0 in
normal direct reclaim, kswapd balancing and zone reclaim. The proprietary
compressor relies on its separate idle-worker policy. The port's standard
swapon_all setup did not make that idle policy service heavy Android13 load.

Measured on v40/BOOT46: zram0 activated with524284KiB swap, zero used, zero
swap-in/out. About1.6million pages had been reclaimed from file cache while
anonymous inactive pages remained resident. mmcqd/loop/kswapd consumed substantial
CPU and the notification shade hit an actual5005ms input timeout. CPU pressure
is measured; the kernel configuration directly explains unavailable normal
swap reclaim. It does not establish that every UI problem has the same cause.

BOOT47 changes exactly two configuration options to n: ZRAM_FOR_ANDROID and
ZRAM_FOR_RTCC2. SWAP and ZRAM remain y. All other qualified configuration values
are unchanged. The reusable fragment is
work/device/samsung/t110_bringup/kernel/lineage-reclaim.config.
build_standard_reclaim_kernel.py preserves out-gateway and builds a separate
out-standard-reclaim. Source MM code is unchanged; this selects its normal path.

The same kernel source's standard reclaim path passed an isolated Cortex-A9
guest test:128MiB RAM,128MiB compressed swap,160MiB touched anonymous allocation.
It swapped33139pages out and22679in and verified all40960pages' contents.
This tests actual ARM reclaim/swap, not Samsung display/radio hardware emulation.
See evidence/ui-system-hang-20261112/qemu-standard-reclaim.json and its log.

The rebuilt graphics, Wi-Fi and restricted Bluetooth modules were compared with
the qualified/installed references, including allocated sections, relocations
and symbol-version data. All four match; only nonfunctional build metadata may
differ. The existing device modules and exact BOOT46 ramdisk are retained.
See evidence/hardware-v35/module-equivalence-standard-reclaim-installed.json.

The combined candidate is v41-GApps/BOOT47. It also compiles the unchanged
private Search APK with the library paths reported by its actual classloader.
The preceding real-root bind fix made PackageManager select prebuilt code, but
runtime class-loader mismatch still occurred. Selection was not execution proof;
the initial map check also incorrectly treated an error line as a match and was
corrected. Qualify executable mappings, actual swap activity and fresh ANRs.

Results belong in evidence/ui-system-hang-20261112/v41-boot47-ui/result.json.
Do not claim responsive hardware or a completed UI fix from offline tests alone.
Some earlier log events are already present in the pre-interaction baseline;
the fused-location event is not independently established as a current startup
failure. Compare new events and ActivityManager's current last-ANR state.
