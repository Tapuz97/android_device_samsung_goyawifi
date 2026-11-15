# Installed native swipe-up update

- Full LineageOS14.1/API25 UI system container installed and booted on 2026-11-15.
- Raw image SHA256: eb38b38a506d10b0d8b7f405951dd58e50e6521a7528e2bd83ff2157bb7baa97.
- Source branch: https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/t110/lineage14-modern-ui-20261114
- Image backup draft tag: t110-lineage14-ui-swipe-image-20261115.
- WSL artifacts: /root/t110-lineage14-ui/artifacts-swipe-20261115.
- Installation/boot receipts and PRIVATE setup backup:
  /root/t110-lineage14-ui/hardware-test-swipe-20261115.
- Original R2 images remain under /root/t110-lineage14-ui/artifacts and in their
  original verified online draft. The original working14 rollback remains on the
  tablet as /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui in recovery.
- Kernel and recovery unchanged; physical SYSTEM was never written.

Same-certificate adb install -r is BLOCKED for platform packages in this ROM
(INSTALL_FAILED_INVALID_INSTALL_LOCATION: Cannot install platform packages to
user storage). Do not retry the standalone APK as a user update. It is retained
as a signed build/reference artifact. Use the full image and matching ARM odex.

The safe recovery exit is /sbin/reboot recovery_done, as in earlier development.
Available tablet space did not permit three expanded images: only the redundant,
unmounted R2 device copy was removed after its PC/online backups were verified.
Original rollback and data were retained.

Installed acceptance: native Home capture drawn, injected upward swipe opens the
native drawer, Back returns Home, old drawer button absent before/after. No Java
crash in the bounded snapshot. Physical finger confirmation is still pending.
Screens/XML: SM-T110/tests/swipe-up-20261115 (private crash snapshot kept local).
No live screen feed, periodic logger or capture process is running.

Native screenshot PNG has the framebuffer orientation (1024x600); input and UI
hierarchy on portrait use 600x1024. Use hierarchy bounds for injected coordinates.
Nonsecure swipe keyguard ignored KEYCODE_MENU; a normal upward unlock gesture
worked. The check never bypasses PIN/password authentication.

Remaining gesture acceptance: physical finger, landscape, widgets/long presses,
accessibility Apps action. Existing launcher and Lineage features are retained.
The invisible center dock anchor/rank remains reserved for layout compatibility.
