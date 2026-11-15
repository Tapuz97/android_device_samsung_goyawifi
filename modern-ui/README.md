# Native modern UI on the working SM-T110 LineageOS14.1 base

This is a visual backport into Android7.1.2/API25, not an Android platform upgrade.
The working graphics compatibility, audio, camera, Wi-Fi, Bluetooth, key mapping,
sleep/wake changes and existing LineageOS features remain the base.

## First combined implementation

| Surface | Change | Verification |
| --- | --- | --- |
| Quick Settings | Large horizontal tiles; active/inactive colors; 2 portrait / 4 landscape columns | Captured on installed R2 in both orientations |
| Settings | Light surfaces, rounded cards, larger icon containers, native-search entry | Captured; search/results/keyboard exercised |
| Notifications | Rounded card backgrounds and dark shade | Captured on installed R2 |
| System menus | Rounded dialogs/popups, restyled native power action rows | Native power menu captured on R1; unchanged R2 resources |
| Recents | Rounded cards; pill-shaped native Clear all with icon | New Settings preview captured; Clear all exercised to empty stack |
| Launcher | Rounded app surfaces, compact/larger-icon defaults; preferences retained | Installed R2 compact drawer captured |
| Lock screen | Stronger clock weight; existing time format/security/weather retained | Installed frame inspected; finger check pending |
| Wallpapers | Current official Lineage artwork in both native pickers; old choices retained | Actual packaged catalogs verified; selection test pending |

Quick Settings still uses native tile actions, long press, accessibility and policy
handling. Settings still uses its existing categories and search implementation.
Physical and onscreen navigation settings are retained. The currently disabled
Power-to-Camera shortcut is a preserved user preference, not removed functionality.

The latest LineageOS default branches checked were lineage-24.0. Their visual
direction is a reference, not a claim that their APKs, Android APIs, dynamic color
engine, Quickstep overview or newer privacy features have been ported to API25.
The original single-line clock and stacked Recents behavior remain.

## Isolation and rollback

- Source: `/root/t110-lineage14/android` (native UI projects, device defaults and a device-gated libgui capture opt-in).
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

- Build identity: `T110_UI_20261114_R2` (Android7.1.2/API25).
- System bytes: `1594884096`, within the existing container size.
- System SHA256: `2778300b359e54c35966390e47c779c14cd11da1f5fb4ae0af3bddad1f49b400`.
- Transfer gzip SHA256: `ecf3ca9efd794ac5b8a8d7aea9838593e00c09dd20f844689999059c7474e4de`.
- The original boot image is reused without modification.
- Installed R2 captured-interface and injected-input checks passed. Owner physical display/finger confirmation remains pending.

## Capture and responsive-layout follow-up

Normal screenshot capture and new Settings task previews were black on the first
UI image, while the actual display buffer contained the correct rendered UI.
Nougat already has a renderbuffer/readPixels fallback selected by
`ro.bq.gpu_to_cpu_unsupported=1`. A controlled interface restart on the installed
R1 image verified that this existing path returns the rendered screen and fixes
new task previews. The GC1000 advertises the required `GL_OES_rgb8_rgba8` support.

R2 makes that configuration permanent. Bitmap captures already request the CPU
consumer path; the device-gated libgui change makes surface-consuming captures
request it too. The original SurfaceFlinger permission and secure-layer checks
remain unchanged. Production capture continues through the native capture API;
the read-only framebuffer utility is a development diagnostic only.

The earlier Android13 capture-owner patch is not directly applicable: Nougat's
Bitmap already retains its ScreenshotClient/CpuConsumer owner. Keep these
different mechanisms separate when continuing Android10/13 work.

R2 also uses the native match-parent landscape shade width, disables tile-label
hyphenation, selects the existing compact launcher default and removes unsupported
cellular/flashlight entries only from this Wi-Fi tablet's default tile list. The
stock tile catalog and launcher preferences remain available.

R1 images and private pre-UI data are preserved in `artifacts-r1` and
`hardware-test-r1`; the original working14.1 images remain in their original
artifact directory. The known baseline BootAnimation native crash still needs a
separate audit; it did not prevent the inspected R1 Home/Settings/shade sessions.

## Offline swipe-up follow-up - 2026-11-15

The native launcher now recognizes upward Home/dock swipes to open its existing
app drawer. Its former button stays invisible through creation and both state
transitions; an accessibility Apps action remains available. Widget gestures,
sideways paging, long presses and multi-touch are protected by eligibility and
recognition checks. See [swipe-up/README.md](swipe-up/README.md) for limitations.

The classifier passed 21 checks, native Trebuchet compiled and a self-contained
signed update APK passed DEX, CRC, alignment and Android v1/v2 signature checks.
Its signing certificate matches the original launcher extracted from installed
R2. The saved R2 image hash is unchanged. No tablet installation was attempted:
the owner requested offline preparation. Device gesture acceptance is pending.

A device installation attempt rejected the standalone update: this ROM blocks
platform packages in user storage. A complete image with matching launcher ARM
preoptimized code was therefore built and checked for loop-container installation.
The existing R2 system artifact still contains the earlier launcher; only the new
APK/source bundle contains this gesture. Hidden anchor/reserved dock rank remain
for layout/animation compatibility. Gesture details and test evidence are under
swipe-up; artifact verification is under swipe-up/verification.json.

## Installed swipe-up image - 2026-11-15

The full system container was installed after explicit owner authorization and
readback verification. The previous R2 is backed up on PC/online, the original
rollback stays on the tablet, and current user data has a private backup. Kernel
and recovery hashes were unchanged. The faulty physical SYSTEM was not written.

The new boot completed. Native screen captures and accessibility hierarchy show
Home drawing correctly, an injected swipe opening the native drawer, Back
returning Home, and the old drawer button absent before/after. No Java crash
appeared in the bounded snapshot. Physical finger confirmation and the broader
widget/landscape/accessibility gesture matrix remain pending. All observers and
capture commands are stopped; no live feed is running.

Installed raw image SHA256:
`eb38b38a506d10b0d8b7f405951dd58e50e6521a7528e2bd83ff2157bb7baa97`.
Draft image tag: `t110-lineage14-ui-swipe-image-20261115`.
Evidence is under `swipe-up`; private data archives and device logs are not in Git.

## Drawer refinement

Owner confirmed finger swipe-up opens the drawer and the button is hidden. The
next native change adds downward dismissal only for a gesture that starts with
the app list at the top, outside search/filter/drag. RecyclerView scrolling, app
taps, long-press drag and multi-touch retain their own event paths. The existing
recognizer is reused with inverted Y; all 29 behavior checks passed.

The Apps alphabet footer is disabled without changing the Widgets scrubber
preference or removing app search/vertical scrolling. Light/dark preferences
remain; a continuous surface replaces the disconnected drawer panels. Referenced
Lineage launcher paths/commit are recorded in reference/drawer-upstream.json.

## Native icon artwork

The working launcher has no icon-pack manager. Thirteen existing system apps now
select official newer Lineage artwork through normal PNG resources. Their code,
labels, components and permissions remain. All 65 density images, compiled
application/launcher icon selection and actual-image packaging passed verification.
See NATIVE-ICONS.md and icon-reference for immutable source/attribution and the
build conversion. No newer app APK, icon-pack app or runtime renderer is added.
The earlier XML-mipmap alias experiment failed offline and was never installed.

## Installed icon image - 2026-11-15

The full image was installed and read back; boot/recovery and the Home-layout
database remained unchanged. Only the regenerable icon cache was invalidated.
Native captures show the new artwork on Home and all 13 drawer entries. Up/down
gestures, the hidden button and absent alphabet footer passed on this boot. The
owner confirmed the new icons look correct; the prior drawer build's finger
gesture behavior was also confirmed. No Java crash appeared in the bounded
snapshot. Screen timeout is restored to 60000 and no live capture/logger remains.

Installed raw SHA256:
`fe204df8498ce7dac3e18cc66ae80a9a78c9be12790506dc30df5fee2e66a9c3`.
Verified draft backup: `t110-lineage14-ui-icons-20261115`. Current checkpoint:
[RESUME-CURRENT-UI.md](RESUME-CURRENT-UI.md). Prior working images/data remain
preserved; private data and device logs are excluded from Git.
