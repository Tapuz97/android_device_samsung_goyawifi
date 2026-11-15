# Current installed T110 UI - 2026-11-15

Android7.1.2/API25/LineageOS14.1, retaining the working hardware backend.
Build fingerprint still contains T110_UI_20261114_R2; use the image hashes and
receipts to distinguish later native UI/icon revisions.

Current installed raw image:
fe204df8498ce7dac3e18cc66ae80a9a78c9be12790506dc30df5fee2e66a9c3

Transfer gzip:
099522657524390bf6225e680037a4876ad6d1ac6aedfd7fd3de18f03ba1e318

- Images: /root/t110-lineage14-ui/artifacts-icons-20261115.
- Private data backup and installation/boot receipts:
  /root/t110-lineage14-ui/hardware-test-icons-20261115.
- Git branch: t110/lineage14-modern-ui-20261114 under
  https://github.com/Tapuz97/android_device_samsung_goyawifi .
- Verified draft image backup: t110-lineage14-ui-icons-20261115.
- Original, R1, R2, swipe-up and drawer-refinement images remain preserved on PC
  and online. Original working14 rollback remains on the tablet.
- Boot and recovery are unchanged. Physical SYSTEM was not written.
- Recovery exit remains /sbin/reboot recovery_done.

Owner-confirmed features:

- Finger swipe-up opens the native drawer; old drawer button stays hidden.
- Swipe-down closes it from the top of the app list; alphabet footer is gone.
- New circular system-app icons look correct on the physical tablet.

Native icon changes cover AudioFX, Browser, Calculator, Calendar, Camera2,
Clock, Contacts, Email, Files, Gallery2, Music/Eleven, Recorder and Settings.
Official artwork is converted at build time; the existing app code is retained.
The launcher has no icon-pack manager. No workaround icon app was installed.
Email retains its upstream older design with the same circular normalization.

Do not reintroduce XML bitmap aliases under mipmap: AAPT1 packages those as raw
XML, causing invalid resources. The final implementation uses five PNG density
resources and direct native manifest icon references. Camera uses
packages/apps/Camera2 and logo_camera_color_44in48dp, not the unused Snap project.
Sources, Git blob provenance, copyright/licenses and render conversion are
backed up in modern-ui/icon-reference; actual-image verification checked all
13 APKs, 65 density images and resolved launcher-component icon IDs.

Only the regenerable Trebuchet app_icons.db cache and sidecars were removed.
launcher.db was hash-checked before/after, retaining Home layouts. Never clear
all launcher data to refresh icons.

Bounded screen checks passed for Home, the drawer, upward/downward gestures and
absence of the old button/alphabet footer. No Java crash in the snapshot.
Screens/XML are under SM-T110/tests/native-icons-20261115. Screenshot PNG has
native framebuffer orientation; input coordinates use UI-hierarchy bounds.
Keyguard can sleep during UIAutomator waits: wake immediately before its normal
swipe unlock. Temporary unlocked-screen timeout was restored to 60000.
No continuous capture or logger is running.

Native light/dark preferences, search, app scrolling, long press and Widgets
preferences remain. More exhaustive landscape/widget/a11y gesture checks remain
separate from the owner-confirmed basic drawer behavior.

Android13 work stays archived. Rooting, Google-enabled distribution and XDA
publication still need their separate qualification; this remains an API25
visual backport, without newer Android APIs or the dynamic color engine.
