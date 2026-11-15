# [ROM][UNOFFICIAL][7.1.2][SM-T110/goyawifi] Modernized LineageOS 14.1

**Draft — release downloads and Google-enabled installation are being qualified.
This text has not been posted to XDA.**

A working LineageOS14.1 port for the **Samsung Galaxy Tab3 Lite Wi-Fi SM-T110**,
with a native UI revamp inspired by newer LineageOS. It keeps the Android7.1.2
backend needed by this tablet's legacy drivers.

## Two editions, the same modern UI

**Modernized — without Google apps:** native Lineage applications and services.

**Modernized — with Google apps:** the same UI and applications, with compatible
Google account services, Play services and Play Store. Qualification pending;
do not advertise the candidate as ready until real sign-in/download tests pass.

Both editions retain:

- Updated circular system-app icons using official Lineage artwork.
- Swipe up from Home to open Apps; swipe down from the top of Apps to close.
  No visible drawer button or alphabet strip.
- Modernized native Settings, inline toolbar Search and standard category Back.
- One **Gestures & Navigation** category with the original native controls.
- Rounded notifications, dialogs, power menu and Recents; native Clear all.
- Updated quick-settings layout and native wallpapers/picker.
- Native physical navigation controls and the onscreen-navigation option.
- Clean lock fading without the old rotated-screenshot flash.

This is an API25 visual backport. It does not provide Android13 APIs, dynamic
color or current Android security support.

## Compatibility and tested status

**Only SM-T110/goyawifi. Not T111, T113, T116, T210 or Xiaomi gauguin.**

| Function | Status |
|---|---|
| Display and finger touch | Working; physically confirmed |
| Modern drawer and icons | Working; physically confirmed |
| Settings Back/search/navigation category | Working in bounded runtime checks |
| Power lock/wake appearance | Owner confirmed clean lock and normal wake |
| Hardware navigation and onscreen alternative | Working in prior hardware checks |
| Wi-Fi scanning, connection and internet | Working in prior functional checks |
| Bluetooth discovery, pairing and file transfer | Working; received file confirmed |
| Bluetooth headphones/speaker audio | Not qualified |
| Camera preview and photos | Working; moving preview and touch confirmed |
| Video recording with sound | Partial; needs final combined qualification |
| Built-in speaker | Working; owner confirmed clear sound |
| Microphone/Recorder | Non-silent recording and failure handling checked |
| Unplugged suspend/wake | One real suspend cycle passed on working14.1 base |
| microSD, wired headset, USB OTG, GPS | Not fully qualified |
| Capacitive-key LED brightness controls | Hardware backend not established |
| App root | Not qualified; developer ADB root is not app root |
| Google sign-in and Play Store | Candidate awaiting device qualification |

## Important installation layout

The development tablet's physical SYSTEM partition has read faults. This port
uses an ext4 system image stored on userdata, mounted read-only by a matching
bootstrap boot image. It **does not flash physical SYSTEM**.

The ROM archive contains matched boot/system files and instructions. It is a
computer-side transport archive, **not a ZIP to select in TWRP Install or Odin**.
A public clean-install/rollback installer remains a release gate. Do not use
generic partition-ROM or generic GApps-flashing instructions for this layout.

Formatting userdata after installation erases both the ROM container and its
isolated Android data. Keep model-specific stock/recovery backups. Do not change
PIT, select Re-Partition/Nand Erase or restore another tablet's EFS.

## Downloads — keep draft until final checks pass

- ROM, checksums, source and installation guide: this project's versioned release
  (final public asset links to be inserted after qualification).
- [Original SM-T110 TWRP2.7.0.1 by gr8nole](https://androidfilehost.com/?fid=23329332407589909).
- [Odin3.07 linked by the recovery developer](https://androidfilehost.com/?fid=23501681358545965).
  Our retained Windows toolkit uses Odin3.13.1; do not mislabel these versions.
- [Samsung USB driver](https://developer.samsung.com/android-usb-driver).
- [Google platform-tools/ADB](https://developer.android.com/tools/releases/platform-tools).
- [Compatible Google input: OpenGApps ARM7.1pico20220215](https://sourceforge.net/projects/opengapps/files/arm/20220215/open_gapps-arm-7.1-pico-20220215.zip/download).
  Use only the qualified loop-image integration procedure once published.
  Do not flash this upstream ZIP directly or use Android10/13 GApps.

The local release folder includes our retained matching TWRP/Odin files for
preparation. Public third-party distribution uses original upstream references.

## Known limits

This remains an experimental, permissive-SELinux, unencrypted development port
with legacy security patches and a known native BootAnimation fault seen during
startup. The interface can still be slow on this hardware. No claim is made that
all current Google apps support Android7.1 or that this is a fully qualified
daily-driver release. OTA, normal app-root and the untested rows above are not
advertised as supported.

## Sources and credits

- [Device tree, compatibility work and modern native UI sources](https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/release/lineage14.1-modern-t110-20261115).
- LineageOS, CyanogenMod and AOSP contributors; original application/artwork
  licenses and provenance are retained in the source tree's modern-ui records.
- Samsung/Marvell original device/kernel/vendor work; device kernel provenance
  and compatibility patches are retained in the device repository.
- gr8nole for the original SM-T110 TWRP.
- OpenGApps contributors; upstream packages remain upstream and are not mirrored.

Please report the exact model, release checksum, issue and reproducible steps.
Remove personal information from any logs before sharing.
