# Modernized LineageOS 14.1 release preparation

Both editions use the same current modernized SM-T110 build. The owner expressly
rejected reverting the edition without Google apps to the old/default UI.
Use the names **Modernized — without Google apps** and
**Modernized — with Google apps**. Do not label the former an unmodified UI.

Shared base: Android7.1.2/API25/ARM32, system raw SHA256
eb9d8955ef8df81f04f424f2b3d0c4bc2d3451395ed36ca7648fd696212067f1.
Matched bootstrap KERNEL SHA256
93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2.

Both retain native modernized Settings, Back/search/navigation grouping,
swipe-up/down drawer with no visible drawer button/alphabet strip, the 13
updated official Lineage app icons, native apps, wallpapers, physical navigation,
working graphics/audio/radio/camera compatibility and screenshot-free lock fade.
Owner confirmed clean Power locking and normal waking on2026-11-15.

The Google candidate adds compatible ARM/API25 services to a separate ext4 copy.
The integration verifies all original regular files and symlink targets unchanged,
checks added APK package identities/minimum SDK/ARM availability, and checks the
actual filesystem and readback hashes. It retains native ExtServices/ExtShared,
keyboard, browser/WebView, TTS, camera and Trebuchet. No Google launcher or icon
manager replaces our UI. Google framework/account components, Play services,
Play Store, tablet setup, contacts/calendar sync and minimal support components
come from the exact verified upstream7.1pico archive.

## Release gates

- [x] Current Google-free base physically works; drawer/icons/Power confirmed.
- [x] Current base and previous working14.1 rollback are backed up online.
- [x] Upstream Google input: ZIP CRC + upstream MD5 + local SHA256 checked.
- [x] Separate Google candidate passes final offline checks:1847 native files unchanged,12 compatible APKs,36 verified SELinux labels; no tablet test yet.
- [ ] Fresh isolated Google profile boot, native setup handoff and responsiveness.
- [ ] Owner Google sign-in, Play download/install and reboot persistence.
- [ ] Public clean-install and rollback flow qualified; current manual recipe is
      engineering documentation, not a universal recovery update.
- [ ] Complete sources/notices and public-download access checked.
- [ ] XDA draft and attachments rechecked against final candidate hashes.

The original tablet stays on the accepted Google-free modernized build during
offline preparation. No physical SYSTEM write, formatting, flashing, account
entry or XDA publication is performed by the preparation scripts.

## Distribution

The local Google image is for private integration/qualification. Do not upload
the official OpenGApps archive or a derivative payload to bypass its no-mirror
policy. Public delivery must use an exact upstream download with a qualified
local loop-image integration process, or separately established distribution
rights. Open installer source does not confer Google APK distribution rights.

Retain the original correctly matched T110 TWRP and Odin toolkit locally and
keep their developer/upstream references in the post. Exclude diagnostic TWRP,
userdata, raw private logs, account identifiers and signing credentials.

Release source branch:
https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/release/lineage14.1-modern-t110-20261115

Do not publish the old engineering post: it describes an obsolete UI and an
unqualified archive. The new post must distinguish tested hardware from pending
Bluetooth audio, video+sound, SD/OTG/GPS and normal-app root qualification.

## Reproduce the private candidate

Local Linux preparation order: prepare_google_input.py, build_google_candidate.py,
then assemble_modern_release.py. The scripts use the checked existing source/image
layout and refuse to overwrite a candidate directory. The historical
finish_google_context_check.py records and repairs the first candidate label
terminator audit; the main builder now performs that check itself.
No script mounts tablet storage or installs the upstream recovery ZIP.
