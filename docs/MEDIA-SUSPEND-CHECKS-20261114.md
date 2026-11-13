# LineageOS 14.1 media and suspend qualification

## Results before the combined installation

These are live replacements on boot `00f966eb-0d8c-4a30-b7f8-cc1253091d50`.
They do not yet qualify the newly packaged image.

| Function | Result | Evidence and limits |
|---|---|---|
| Real unplugged sleep/wake | PASS, one cycle | Owner left USB disconnected and screen off for about two minutes, then confirmed display and touch recovered. Kernel suspend at uptime1138.079, wake1269.910, resume1270.342; unchanged boot ID. |
| Wi-Fi after suspend | PASS | Certificate-verified HTTPS200 after reconnection. No long soak or repeated suspend-cycle claim. |
| Built-in speaker | PASS, owner confirmed | Latest generated440Hz three-second tone played through normal Lineage Eleven; owner said “it did play audio now!” Earlier attempts were silent and remain failures. |
| Built-in microphone | PARTIAL | Normal Recorder produced an8.20second mono44100Hz WAV, mean-42.2dB, peak-14.5dB; capture PCM closed after stop. Speech quality/replay still unqualified. |
| Recorder first permission run | FAIL, source fix built | Missing recording directory/file led to a null share-intent crash. Reopening allowed recording. New code checks file creation, skips missing-file sharing, clears stale status, flushes writer before conversion, and fixes WAV byte rate/block alignment. Installed-build retest pending. |
| Video recording | PARTIAL | H264640x480 MP4 fully decoded,31.85s/250frames (~7.85fps). Its AAC track was silent before microphone activation was fixed. Must retest video plus sound; do not advertise full video support. |
| Bluetooth audio | NOT QUALIFIED | Owner requested built-in speaker first. Prior S23 OPP transfer does not test A2DP. |

## Audio findings and permanent implementation

1. ANI7 primary output accepts44100Hz; its48000 rejection is not the framework's
   expected retry status. Advertise44100 only for primary output; keep A2DP rates.
2. Restore stock ALSA configurations at `/system/usr/share/alsa` and plugins at
   `/system/usr/lib/alsa-lib`. Include their dependency closure, including libacm.
3. libacm imports MD5_Init/Update/Final without a provider DT_NEEDED. Use Lineage's
   existing exact-path linker hook to add platform libcrypto only to this blob.
   Do not replace platform crypto. Native snd_ctl_open probe then succeeds.
4. Match actual ANI7 boot's AP-master clock properties; give system:audio0660
   access to ssp_master/gssp_master. PCM DMA interrupts then advance normally.
5. Exact-ANI7 audio stream proxy adds local HiFi routing parameters. Stock HAL at
   0x6260-0x6292 ignores routing unless path_handler and phone_volume are also
   supplied. Stock policy0x6168-0x61da supplies these; non-call volume is230.
   HAL's table at0xacf0 maps handler0 to hifi. Limit adaptation to local routes;
   Bluetooth uses its normal Nougat HAL. Runtime confirms speaker path ENABLE,
   PCM playback and path DISABLE, followed by the owner's audible confirmation.
6. Input proxy sends STREAM_IN_ACTIVE=1 before first read and0 on standby.
   Unlike modern HALs, ANI7 does not lazily open PCM on read. Recording now
   yields a non-silent signal and releases the capture device.

Static disassembly is ordinary ARM objdump evidence, not an REA decompiler result.
Raw logs, microphone recording and stock binaries are private/local.
No continuous logger remains. The temporary audio dump property was reset to0
and its two generated PCM files removed. Original USB stay-awake0 and unset
camera-double-power-disable setting were restored before recovery.

## Combined candidate

- Build: successful; actual-image comparison verifies208 critical files.
- Vendor audit:47 ELF dependency closures pass, including the verified linker hook.
- Real Recorder PcmConverter host regression test passes:10bytes of PCM with
  an8byte buffer produces exactly54bytes of WAV, correct mono alignment2,
  byte rate88200, and an unchanged final partial buffer.
- Boot:16777216bytes, SHA256 `93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2`.
- System:1594884096bytes, SHA256 `01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea`.
- Compressed transfer:383232412bytes, SHA256 `fd362c7c072d6720f78f135e2a0640d720747f8eed8c9ee85ab7272eeda10125`.
- Existing installed pair preserved and hashed in native `artifacts/media-suspend-parent`.
- Installation/boot qualification is pending until explicitly appended below.

Same-boot Recorder APK update was rejected: production APK is dex-stripped,
and the standard Lineage test-key policy rejects platform-signed data-app installs.
No policy bypass was introduced. Full ROM boot must restore/rescan the system app
and qualify the corrected Recorder; a temporary bind alone cannot restore its
PackageManager registration after that failed update.

## Installed-build verification

Full system and KERNEL readback matched the candidate hashes above. Recovery
is unchanged; physical SYSTEM was not written. Booted via the established
`recovery_done` path. New boot ID: `7189106d-b4e8-4f1c-aaee-f2d5d272fa6e`.
Boot completion was first observed at72seconds; that is an observation bound,
not a precise startup benchmark. Only the loop-mounted read-only system remains;
none of the previous live replacement bind mounts survived this reboot.

- Installed linker, libaudioflinger and Recorder hashes match the verified image.
- SSP controls are system:audio0660 and stock audio clock properties are present.
- Recorder was rescanned correctly as a system app.
- Forced storage failure: temporarily replaced its recording directory with a
  regular file, preserving and restoring the directory in a shell trap. Recorder
  logged `Cannot create recording directory`, stayed alive and did not start
  capture or show a stuck Recording state. Existing recording restored intact.
- Subsequent normal recording:13.02second WAV, mono44100Hz,1148408bytes,
  mean-37.2dB and peak-14.1dB. Fully decoded; capture device closed after stop.
- Crash buffer empty through these checks. Audioserver PID160 stayed alive.
- Normal Eleven tone playback activates and releases the stock speaker path.
  Owner missed the first post-install tone, so it was repeated for12seconds.
  Owner explicitly confirmed “Yes, clear sound” on this installed build.
- Wi-Fi rejoined automatically; certificate-verified HTTPS200 after boot.
- Temporary USB stay-awake restored to0; no continuous diagnostic writer.
- Real suspend result belongs to the preceding boot. Video recording with the
  repaired microphone and Bluetooth A2DP still need their own qualification.
