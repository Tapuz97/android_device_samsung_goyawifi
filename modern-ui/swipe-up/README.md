# Home swipe-up launcher update - 2026-11-15

The full image was installed on 2026-11-15 after explicit authorization.
Its transfer and expanded-image readbacks matched; boot, recovery, user data and
the on-tablet original rollback were preserved. The former R2 image remains
backed up on the PC and online. See installation and acceptance JSON records.
The rendered Home/drawer and injected swipe/Back checks passed on the new boot.
The owner confirmed finger swipe-up opens the drawer and the button is hidden.
No continuous capture is running.

Swipe upward on Home or the dock to open Trebuchet's existing app drawer. The old
drawer button is invisible, non-clickable and excluded from accessibility. Both
native transition paths keep it hidden. A native accessibility "Apps" action on
the workspace provides an alternative to the gesture.

This uses the current app drawer, search, icons and preferences. It does not add
a replacement launcher or a new drawer implementation. The native reveal
animation runs on release; it does not follow the finger continuously.

Recognition rejects taps, short movement, horizontal/downward/diagonal gestures,
long presses, multiple pointers and cancelled gestures. Widget regions, folders,
dragging, resize mode and other launcher states are excluded. The hidden anchor
and reserved center dock rank are deliberately retained for saved-layout and
native animation compatibility; the dock slot has not been reclaimed.

Offline verification:

- All 21 pure-Java gesture checks passed.
- Native Trebuchet build on the existing ARM/API25 platform passed.
- Matching DEX is embedded, including the new detector and accessibility action.
- APK ZIP CRC and alignment passed.
- APK v1 and v2 signature checks passed; its certificate matches the launcher
  extracted from the saved installed R2 system image.
- Saved R2 system SHA256 remains
  2778300b359e54c35966390e47c779c14cd11da1f5fb4ae0af3bddad1f49b400.

Candidate: Trebuchet-T110-swipe-up-20261115.apk. Follow-up installation found that
this ROM explicitly blocks platform-package updates under /data/app, despite a
matching certificate. The standalone APK is therefore a build/signing reference,
not a usable user-storage update on this ROM. The complete rebuilt system image
includes the new launcher and matching ARM preoptimized code. Install through the
established loop-container method; never write the faulty physical SYSTEM
partition. The extracted original system APK is a signing/reference artifact:
it is dex-stripped and is not an installable rollback APK.

Further acceptance remains pending: physical portrait and landscape swipes from blank
Home, icons and dock; app launching/search; Home/Back; repeated open/close without
the button reappearing; sideways paging; long-press drag; widget scrolling;
multi-touch; accessibility Apps action. Physical responsiveness is not proven by
the classifier tests or build.

Backups: existing R2 draft release and original working 14.1 remain preserved.
The standalone APK remains a reference draft; the complete installable container
and verification records have a separate t110-lineage14-ui-swipe-image-20261115
draft release. Installed raw image SHA256:
eb38b38a506d10b0d8b7f405951dd58e50e6521a7528e2bd83ff2157bb7baa97.
This update does not change hardware drivers, navigation settings or Android API.
