# T110 achieved results and remaining limits

2026-11-12 preservation checkpoint.

- Built and booted a custom Android13/Lineage20 engineering port on SM-T110 using its matched Marvell/Vivante stack and a read-only system-image file on userdata. Never write physical SYSTEM p15. Recovery and both Android data profiles were preserved.
- Physically verified full colored output, a Lineage setup interface and responding touch in earlier boots. Hardware key mapping and normal Lineage button-mode behavior were demonstrated. These are partial successes, not complete hardware qualification.
- Backported required kernel Binder/security/syscall/USB/network/ION functionality; current source is on the kernel checkpoint branch. Standard compressed-swap reclaim and removal of persistent diagnostic writers were validated.
- Current installed v42-GApps/BOOT48 hashes and full rollback v41-GApps/BOOT47 were verified before preservation. v42 fresh-boot logging/memory persistence passed. It took229.66seconds to boot completion in that test; no2.3second full-boot claim is valid.
- The owner later reported a physically black/unresponsive display. ADB remained connected; logical Awake did not recover the visible panel. App GPU windows and JIT remain disabled. Camera/audio/native Bluetooth/sensors/key LEDs/MTP and complete Wi-Fi/accessory/UI qualification remain unfinished. Do not call the port stable or smooth.
- Submitted the tested Binder32bit host/device Soong fix to LineageOS Gerrit513083. Submission is not merger or official device support. Public kernel/device fixes also have fork branches and PRs listed in LINKS.md.
- Audited Android7.1/Lineage14.1 source before a complete product build: HWC1 exists, gralloc0 has a built-in adapter, stock libGAL needs the available platform textrel option, and Marvell HWC/EGL ABI plus physical suspend/resume remain unqualified. No Android7.1 ROM or GPU/sleep hardware test has been built/run here.

Next development work is the small compatibility target and the explicit graphics/power gates in LINEAGE14-GPU-AND-SLEEP-AUDIT.md. Restore source first; do not restart with a complete ROM build or repeat unplanned boot tests.
