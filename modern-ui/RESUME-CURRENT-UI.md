# Current installed T110 UI - 2026-11-15

Android7.1.2/API25/LineageOS14.1, retaining the working hardware backend.
Build fingerprint still contains T110_UI_20261114_R2; use the image hashes and
receipts to distinguish later native UI/icon revisions.

Current installed raw image:
eb9d8955ef8df81f04f424f2b3d0c4bc2d3451395ed36ca7648fd696212067f1

Transfer gzip:
1e585dd848217cb686432205ac0879e512da0f9d31873f8f2fde2d6c008e844b

- Images: /root/t110-lineage14-ui/artifacts-settings-lock-20261115.
- Private data backup and installation/boot receipts:
  /root/t110-lineage14-ui/hardware-test-settings-lock-20261115.
- Git branch: t110/lineage14-modern-ui-20261114 under
  https://github.com/Tapuz97/android_device_samsung_goyawifi .
- Verified draft image backup: t110-lineage14-ui-settings-lock-20261115.
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

The earlier icon-artwork installation removed only the regenerable Trebuchet
app_icons.db cache and sidecars. The latest Settings update leaves that cache alone.
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


Latest Settings/lock update:

- One Gestures & Navigation tile, retaining all 45 native button/navigation keys.
  The original gesture page is nested under it, with its deep links preserved.
- Category headers use the standard mirrored Back arrow; the old drawer is locked
  closed without disabling native category/package-update receiver lifetimes.
- Search stays at the toolbar end beside Settings; the duplicate large row is gone.
- Native category Back, nested gestures Back and refreshed search results passed.
- Lock uses MODE_FADE with a bufferless compositor dim layer, skipping the rotated
  screenshot/EGL/shader path. Automatic screen-off selected mode2 and wake returned
  to Settings; physical Power-transition appearance awaits owner confirmation.
- Native mode-fade cleanup handles a null Surface; fade timing uses the normal
  short animation duration and respects global animator settings.
- Search indexing uses device-protected data under user_de/0/com.android.settings.
  Only shared_prefs/index.xml indexing flags were refreshed, with the search DB
  hash unchanged; saved queries and actual settings remain. CE data/data is wrong.
- Native UI screenshots must follow settled UI hierarchy to avoid outgoing frames.
- The known BootAnimation native SIGSEGV was observed separately; there was no new
  Java crash in these bounded tests. No live logger/capture is left running.

Receipts and acceptance: modern-ui/settings-navigation-lock in the source branch;
private logs and screenshots: SM-T110/tests/settings-navigation-20261115.
