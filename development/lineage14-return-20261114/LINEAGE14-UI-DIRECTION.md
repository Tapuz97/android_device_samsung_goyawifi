# Active direction: restore14.1, then refine its native UI

Owner decision,2026-11-14: stop the Android13 port and return to the previous
working LineageOS14.1 / Android7.1.2 media build. Develop a nicer UI on that base.
The Android13 source, candidate pair and hardware-test conclusions stay backed
up; no further13 builds or boot tests are part of the active work.

## Protected baseline

- Working14.1 system: `01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea`.
- Working14.1 boot: `93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2`.
- Source baseline: `ceebd0c9a6c3298765757522f88d75d0bd47b4eb`.
- Native C: artifacts: `/root/t110-lineage14/artifacts/lineage14-first-build`.
- Online engineering release:444868203. Previous rollback pair remains separate.
- Retain the user's original `t110-lineage14-data` directory, normal Lineage
  wallpaper settings, keyboard, navigation settings and working hardware buttons.
- The camera double-Power shortcut is now disabled in the restored user's secure
  settings (`camera_double_tap_power_gesture_disabled=1`). The owner confirmed
  that a single physical Power press turns the screen off afterward. Preserve
  this preference; do not remap Power to Camera during UI work.
- The faulty physical SYSTEM partition remains excluded. Use the established
  userdata-backed system file and matching KERNEL; preserve TWRP.

## Visual direction

Use the owner's earlier Android13-inspired preference as the starting direction,
implemented with native14.1 components and selective resource changes. Preserve
features and performance; the13 framework/graphics stack is not being imported.

First review the restored UI and establish its current settings/screenshot
baseline. Then prepare a coherent first visual batch:

1. High-quality static default wallpapers through the existing Lineage picker.
2. Consistent color palette, typography, readable icons and spacing.
3. Cleaner Settings and notification/Quick Settings presentation.
4. A consistent launcher grid and icon treatment using existing Trebuchet options
   where available, before adding code or replacement applications.

Keep the physical/onscreen navigation choices intact. Do not regress button
mapping, audio, camera, Wi-Fi or sleep/wake while changing resources. Preserve
the separate LED-control request and determine hardware support from evidence;
do not invent a brightness control for an unqualified interface.

Avoid expensive blur, live wallpapers, unnecessary animation layers and feature
removal used to hide bugs. Compare Settings scrolling, notification shade, touch
and launcher frame behavior against the working14.1 baseline. Do not claim smooth
performance solely because compilation succeeds.

After the UI pass, the owner requested a tested Google-apps-enabled edition and
actual XDA publication with the ROM, correct TWRP and Odin downloads. See
[publication plan](release/PUBLICATION-PLAN.md). Rooting remains separately
qualified before being advertised. Existing14.1 limitations (including video-with-audio
and Bluetooth audio) remain recorded; returning to14.1 is not a new claim that
every hardware feature has passed. The owner's current decision prioritizes UI
work on the working base over further Android13 compatibility experiments.
