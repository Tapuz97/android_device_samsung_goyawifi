# [ROM][EXPERIMENTAL][7.1.2][SM-T110/goyawifi] Modernized LineageOS 14.1 | Google apps optional

This is an unofficial LineageOS14.1 port for the **Samsung Galaxy Tab3 Lite
Wi-Fi SM-T110**, with a native interface revamp inspired by newer LineageOS.
It retains Android7.1.2 for the tablet's legacy drivers. It is not Android13.

**SM-T110/goyawifi only. Do not use these files on T111, T113, T116 or T210.**

## What changed

- Updated circular icons for13 system apps, with native launcher integration.
- Swipe up from Home to open Apps; swipe down from the top of the app grid to
  close. The old drawer button and alphabet strip are hidden.
- Modernized native Settings, toolbar Search and category Back navigation.
- One **Gestures & Navigation** category for hardware and onscreen navigation.
- Updated Quick Settings, rounded notifications/dialogs and Recents/Clear all.
- Native wallpaper selection and clean lock/wake fading.
- Permanent display-format correction: physical blues now match screenshots.
- A scoped software-drawing compatibility path for Google's account web view;
  the normal Android compositor remains GPU accelerated.

## Editions and downloads

Both editions have the same modernized interface and colour correction.

- [Without Google apps — ROM archive](https://github.com/Tapuz97/android_device_samsung_goyawifi/releases/download/t110-lineage14-modern-final-20261116/SM-T110-Lineage14.1-Modernized-20261116-without-Google-apps.zip)
- [With Google apps — local build kit](https://github.com/Tapuz97/android_device_samsung_goyawifi/releases/download/t110-lineage14-modern-final-20261116/SM-T110-Lineage14.1-Modernized-20261116-Google-build-kit.zip)
- [Installation guide and verification tools](https://github.com/Tapuz97/android_device_samsung_goyawifi/releases/download/t110-lineage14-modern-final-20261116/SM-T110-Modernized-20261116-Guide-and-tools.zip)
- [Checksums](https://github.com/Tapuz97/android_device_samsung_goyawifi/releases/download/t110-lineage14-modern-final-20261116/SHA256SUMS-PUBLIC.txt)
- [Device source and compatibility patches](https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/release/lineage14.1-modern-t110-20261116)

The tested Google edition uses **OpenGApps ARM / Android7.1 / pico / 20220215**,
not a MindTheGapps package for a newer Android version. The build kit takes the
Google-free ROM and your original upstream GApps download, checks their hashes
and assembles the Google edition on your computer. It preserves the native UI
and original Google APK signatures. Read GOOGLE-EDITION.md in the guide.

Google downloads remain upstream in accordance with the project's
[no-mirror policy](https://opengapps.org/blog/post/2016/03/18/the-no-mirror-policy/).

## Required recovery and Windows tools

- [Original T110 TWRP2.7.0.1 by gr8nole](https://androidfilehost.com/?fid=23329332407589909)
- [Odin3.07 linked by the recovery developer](https://androidfilehost.com/?fid=23501681358545965)
- [Samsung USB driver](https://developer.samsung.com/android-usb-driver)
- [Google platform-tools / ADB](https://developer.android.com/tools/releases/platform-tools)
- [Exact tested OpenGApps input](https://sourceforge.net/projects/opengapps/files/arm/20220215/open_gapps-arm-7.1-pico-20220215.zip/download), if choosing Google apps

Our retained Windows toolkit was Odin3.13.1. This is a different version from
the developer-linked3.07; do not confuse or rename them.

## Installation — read before flashing

**These ROM ZIPs are computer transport archives, not TWRP update ZIPs or Odin
AP packages. Do not select them in TWRP Install or flash the raw image to SYSTEM.**

The development tablet has read faults in physical SYSTEM. The included boot
image mounts an ext4 system file stored on userdata, with a separate Android
data directory. This layout is essential to this build. Formatting userdata
after installation erases the ROM container as well as its isolated data.

1. Confirm SM-T110/goyawifi and make your own matching boot/recovery/data backups.
2. Install the matching T110 TWRP if needed. In Odin use AP/PDA for its recovery
   tar.md5, Auto Reboot off, Re-Partition and Nand Erase off. After PASS, boot
   directly into recovery with Power + Home + Volume Up.
3. Verify/extract the chosen ROM on your computer using the supplied Python tools.
4. Follow **INSTALLATION.md**, including model, partition-size, ext4, free-space
   and image-hash checks. Stage and verify the system container before writing
   the matched boot image. Recovery, bootloader, PIT, EFS and physical SYSTEM
   are not part of the ROM write operation.
5. The recovery handoff used on our tablet is `adb -s SERIAL shell /sbin/reboot recovery_done`.
   Generic Reboot System previously returned to recovery; do not repeatedly
   reflash bootloaders to work around that.

The manual engineering procedure and matching layout have been exercised on
the development tablet. **An independent clean install on another SM-T110 has
not been qualified.** This release is for experienced testers; it is not being
presented as a proven universal installer. First boot can take several minutes
while Android prepares apps. Confirm the physical screen and touch, not just a
boot-completed property. Rollback instructions are included in the guide.

## Tested and still open

| Item | Result |
|---|---|
| Display colours and Google account form | Physically confirmed correct after the fixes |
| Touch, modern drawer and updated icons | Confirmed on this tablet |
| Native Settings/navigation/lock changes | Bounded checks passed; lock/wake confirmed |
| Google sign-in and Play Store | Owner reported working; no named app test receipt |
| Wi-Fi scanning/connection/internet | Confirmed; HTTP/HTTPS checks passed |
| Bluetooth discovery/pairing/file transfer | Confirmed on the14.1 base |
| Camera preview/photos and speaker | Physically confirmed on the14.1 base |
| Recorder/microphone | Non-silent recording and failure handling checked on the base |
| True unplugged suspend/wake | One real suspend cycle passed on the base |
| Video with audio, Bluetooth audio, microSD/headset/OTG, GPS | Not fully qualified in the final Google edition |
| Capacitive-key LED brightness, double-tap wake, app root, OTA | Not advertised as supported |

Older base results are identified above; they are not a claim that every test
was repeated on the final Google-enabled image. The Google-free image contains
the exact checked colour-fix libraries and native payload, but its final archive
was not separately reflashed after this release preparation.

Known limitations: legacy security patches, permissive SELinux, unencrypted
userdata and limited performance on this hardware. A native BootAnimation exit
fault was recorded although Android continued to the working interface. Google's
account-page Skip works but remains at bottom-left; its requested right-side
placement is unfinished. No claim of current Android security support, Play
Integrity certification or compatibility with every modern Play Store app.

## Sources and credits

Thanks to LineageOS/CyanogenMod/AOSP contributors; Samsung, Marvell and Vivante
device work; gr8nole for T110 recovery; the goyawifi/T210 reference developers;
and OpenGApps contributors. T210 code is a development reference, not a
flash-compatible ROM.

[Corresponding kernel source](https://github.com/Tapuz97/android_kernel_samsung_goya/tree/e7d7b1f23e999539c74761216d20f432fd63e052)
and exact platform pins/patches, configuration, artwork provenance and build
notes are linked in SOURCE-AND-CREDITS.md and the device repository.

For bug reports, include the exact model, edition, release checksum, steps and
sanitized logs. Do not post account details, device identifiers or personal files.
