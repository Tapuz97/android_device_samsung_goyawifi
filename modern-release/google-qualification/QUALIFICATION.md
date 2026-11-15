# Modernized Google edition — hardware qualification, 2026-11-15

Current pass is in progress. Do not inherit a PASS from earlier ROMs.
Evidence is local/private under /root/t110-lineage14-ui/hardware-test-google-20261115.
No continuous capture/log writer is used.

| Check | Current result |
|---|---|
| Google image/source/ABI/filesystem/SELinux labels | OFFLINE PASS |
| All1847 original ROM files and symlinks retained | OFFLINE PASS |
| Accepted modernized rollback PC/online hashes | VERIFIED |
| Personal-data backup | Skipped at owner's request; existing ROM backups retained |
| On-tablet old-profile preservation | PASS; old directory retained separately |
| System readback; matched unchanged KERNEL/recovery | PASS |
| Full boot and process survival | Startup PASS; soak/reboot pending |
| Actual visible UI, modern icons/drawer, finger touch | Pending owner check |
| Settings navigation/search and keyboard | Pending |
| Google services/account/provider registration | All12 Google system packages present; actual sign-in pending |
| Wi-Fi association/DHCP/DNS/validated HTTPS | PASS: IPv4, framework VALIDATED and certificate-checked HTTPS204 |
| Google sign-in on tablet | Pending owner check; no credentials in chat |
| Play Store app install/open | Pending |
| Reboot retains sign-in/app and native UI | Pending |
| Memory/storage/ANR and responsiveness | zRAM active; about1.5GiB free at startup; no crash/ANR in first snapshot; longer checks pending |
| Bluetooth enable and off/on | PASS through native manager API; Wi-Fi HTTPS still204 afterward |
| Bluetooth scan/names/bond | Pending UI phase |
| Bluetooth audio | Needs owner audio peer name |
| Camera preview and still capture/reopen | Pending |
| Video recording with audio and playback | Pending |
| Built-in speaker tone | Pending owner hearing check |
| Microphone/Recorder save and non-silent WAV | Pending |
| Physical/onscreen navigation and Power lock/wake | Pending owner check |
| True unplugged suspend/wake; Wi-Fi after wake | Pending owner check |
| microSD read/write | Needs owner insert |
| Wired headphones and USB-OTG | Needs owner accessories |
| Advanced restart menu | Pending |
| Capacitive-key LED backend, GPS and double-tap wake | Unqualified; do not claim working |
| Normal-app root | Separate qualification; root ADB is not app root |

Fresh test profile preserves only authorized ADB keys and known Wi-Fi config.
The prior complete profile is retained separately. The owner explicitly requested
skipping any new personal-data backup; no checked private PC tar is claimed.
The accepted current modernized system is kept compressed on the tablet and as
verified PC/online images. The older pre-modern system remains backed up on PC.
Faulty physical SYSTEM is never written; no userdata format or partition changes.

During Google credential entry, stop screenshots/UI hierarchy capture. Only
sanitized outcomes may be put in public source/release documentation. Actual
network/account identifiers, camera images, audio recordings and raw logs stay
private.

## Installed image and first observations

- Google raw SHA256:
  d99aaa28603e11b357965121ffd209225099e1e73dc5af29fb22a907aaf6248a.
- Boot/recovery match the preceding accepted build and were not rewritten.
- All12 intended Google packages resolve to their exact system APK paths.
- Settings, Trebuchet, Camera2, Recorder, Eleven and LatinIME remain system apps.
- GLES reports Vivante Corporation / GC1000 core / OpenGL ES2.0. The established
  rotation and GPU-to-CPU screenshot compatibility flags are retained.
- Boot ID b4029312-8d0f-4bd2-b69e-bd8c18f3c4be; no Java/native crash or ANR in
  the bounded startup or radio-cycle snapshots. This is not a long stability soak.
- First boot compiled the new Google APKs, including Phonesky and PrebuiltGmsCore.
  Observer saw completion after184s from its start; that is not a cold-boot
  benchmark. A normal subsequent reboot remains pending.
- BMA254 accelerometer has changing sensor samples; rear MRVL HAL1 camera
  enumerates. Actual camera capture and visible preview remain untested this pass.
- Actual current volume is not yet heard, and finger interaction is not verified
  by a registered input driver or an injected event.

Current owner step: complete the visible native setup/Google sign-in and install
and open one compatible small Play Store app. No screenshots or UI hierarchy
are captured during that step. Do not drive other apps/reboot over the owner.
The global provisioned/user-setup flags were still0 at the last bounded check.
After the owner's reply, run native UI/camera/Recorder/speaker/Bluetooth-peer and
accessory/suspend checks, then one normal reboot and account/app persistence.
