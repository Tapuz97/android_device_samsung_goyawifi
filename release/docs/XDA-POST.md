# Suggested thread title

[ROM][UNOFFICIAL][7.1.2][SM-T110/goyawifi] LineageOS 14.1 — experimental hardware bring-up

# Post draft

We have LineageOS 14.1 / Android 7.1.2 running on the Samsung Galaxy Tab 3 Lite
**SM-T110 (goyawifi)**, using its Marvell/Vivante hardware stack and a preserved
3.4.5 kernel with targeted compatibility fixes.

This is an experimental community port, not an official LineageOS release. It is
for SM-T110 only, not T111/T113/T116 or the non-Lite T210. We are sharing the
source, measured results and engineering package before calling it a daily driver.

## What we have demonstrated

- Visible Android setup/UI and responsive touchscreen on the test tablet.
- Wi-Fi scanning, connection, DNS and HTTPS internet access.
- Bluetooth discovery, pairing and a successful phone file transfer.
- Rear-camera live preview and saved photographs, including reopening Camera.
- Audible built-in speaker playback on the latest installed build.
- Non-silent microphone recordings and corrected Recorder save-error handling.
- One real USB-disconnected suspend/wake cycle with display and touch recovery
  on the preceding build. Repeated-cycle qualification remains to be done.

## Known limitations

Video recording is partial and slow; video audio needs a fresh test after the
microphone fix. Bluetooth audio, GPS, wired audio, microSD/OTG and long suspend
soaks remain unqualified. Button LED control is not established. General UI
performance still needs evaluation. Google apps and ordinary-app root are not
included. SELinux is permissive and the isolated Android data is unencrypted.

## Read before downloading

The tested tablet's SYSTEM partition has read faults. This build therefore uses
a system image on userdata with a matching custom boot image. **It is not a
standard TWRP flashable ZIP**, and wiping userdata removes the ROM. This does not
mean every T110 has that fault. Clean installation on another tablet is still a
release gate; the binary release is currently a maintainer-accessible draft.

Source and guide: https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/release/lineage14.1-t110-20261114

See `release/docs/INSTALLATION.md`, `STATUS.md`, `DOWNLOADS.md` and the SHA256
manifest before experimenting. The download catalog links the SM-T110 recovery,
Odin, platform-tools and the correct GApps family. ARM 7.1 Open GApps is only a
candidate until our loop-system integration is tested; do not flash Android10/13
MindTheGapps on this build.

## Reporting problems

State the exact model, release/hash, clean install or upgrade, reproduction steps,
what physically appeared on screen and whether touch/audio worked. Attach a short
log covering the failure after removing account names, network identifiers,
serials and personal files. A boot_completed property alone is not a hardware pass.

## Credits and next steps

Thanks to LineageOS/AOSP, Samsung's released kernel sources, gr8nole's T110
recovery/device work, jakaco's goyawifi work and the upstream maintainers credited
in `SOURCE-AND-CREDITS.md`. Our device/framework fixes and exact upstream revisions
are preserved on the source branch; the matching kernel source is linked there.

We will finish hardware qualification before cosmetic modernization. Android10 /
Lineage17.1 is a separate compatibility investigation, with this 14.1 build kept
as the rollback baseline. No Android10 release or performance promise yet.
