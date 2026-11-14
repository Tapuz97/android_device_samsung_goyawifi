# Native modern UI on the working SM-T110 LineageOS14.1 base

This is a visual backport into Android7.1.2/API25, not an Android platform upgrade.
The working graphics compatibility, audio, camera, Wi-Fi, Bluetooth, key mapping,
sleep/wake changes and existing LineageOS features remain the base.

## First combined implementation

| Surface | Change | Hardware qualification |
| --- | --- | --- |
| Quick Settings | Large horizontal tiles; active/inactive colors; 2 portrait / 4 landscape columns | Device check pending |
| Settings | Light surfaces, rounded cards, larger icon containers, native-search entry | Pending |
| Notifications | Rounded card backgrounds and dark shade | Pending |
| System menus | Rounded dialogs/popups, restyled native power action rows | Pending |
| Recents | Rounded cards; pill-shaped native Clear all with icon | Pending |
| Launcher | Rounded app surfaces and larger-icon default; existing preferences retained | Pending |
| Lock screen | Stronger clock weight; existing time format/security/weather retained | Pending |
| Wallpapers | Current official Lineage artwork in the existing picker; old choices retained | Pending |

Quick Settings still uses native tile actions, long press, accessibility and policy
handling. Settings still uses its existing categories and search implementation.
Physical and onscreen navigation settings are retained. The currently disabled
Power-to-Camera shortcut is a preserved user preference, not removed functionality.

The latest LineageOS default branches checked were lineage-24.0. Their visual
direction is a reference, not a claim that their APKs, Android APIs, dynamic color
engine, Quickstep overview or newer privacy features have been ported to API25.
The original single-line clock and stacked Recents behavior remain.

## Isolation and rollback

- Source: `/root/t110-lineage14/android` (the four UI projects only).
- Device checkpoint branch: `t110/lineage14-modern-ui-20261114`.
- Separate build output: `/root/t110-lineage14-ui/out`.
- Original source deltas, hashes and new files are saved before UI changes.
- Original image directory: `/root/t110-lineage14/artifacts/lineage14-first-build`.
- Working system SHA256: `01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea`.
- Unchanged boot SHA256: `93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2`.
- The faulty physical SYSTEM partition must never be written. This tablet uses a
  loop-mounted system image on userdata. Preserve the separate Android13 data.
- Do not install individual framework/SystemUI APKs from a mismatched build.

`build_modern_ui.sh` exports matching kernel headers and builds the complete
system image using the original JDK8/Jack environment. It never contacts a tablet.
`export_modern_ui.py` creates a before/after-hash-checked source bundle. Its
generated `apply.py` checks the complete baseline before writing any file.

## Required acceptance before calling this installed/working

1. Complete system build; Android7/API25, image size and filesystem checks.
2. Extract the actual image and verify all vendor inputs, radio/audio plugins,
   camera, graphics adapters, key layouts and Lineage applications.
3. Verify the old boot/recovery and both profiles remain preserved.
4. Install only the full checked image through the established loop-image path.
5. Physically inspect Home, Settings/search, shade, tiles in both orientations,
   notifications, Recents, volume and power menus; check touch and both nav modes.
6. Confirm Wi-Fi, Camera, speaker and sleep/wake remain functional.

Google-enabled distribution and XDA publication remain gated on their separate
qualification; this UI build is not a public release or a newer Android version.

## Complete-image offline result

The full ARM build and actual-image gates passed. The checked image includes both
native wallpaper catalogs, the new Settings/SystemUI resources and all selected
vendor dependencies. The compiled HWUI resolve-before-swap and legacy queue
deadline checks passed. Filesystem verification passed after normalizing only the
known unused inode-bitmap padding in the generated candidate copy.

- Build identity: `T110_UI_20261114` (Android7.1.2/API25).
- System bytes: `1594884096`, within the existing container size.
- System SHA256: `b9f9266db419ed790a0d975eb237369b9e803fc3c4fe7405558033b4483231cb`.
- Transfer gzip SHA256: `7605b778ec38156d13c0bbd8aa07f68740b0d4568bd14b855e79ba7545bcf385`.
- The original boot image is reused without modification.
- Physical screen, touch and menu acceptance remain pending installation.
