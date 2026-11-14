# Android13 hardware test1 — booted, not fully qualified

One full candidate boot was run on2026-11-14. No second candidate boot was run.
Android13 remains installed. The preserved14.1 images and source were not changed.

## Installed identity and rollback

- System SHA256: `470961893c93aa228c5722108ab15b364b970d6d143c3a5546401bb6ac7563ee`.
- KERNEL SHA256: `f2d735c3fea57b853147b6a846fc80ff0ed9e2df3d168ef398fc7d3a1a8365c7`.
- Recovery SHA256: `f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e`, unchanged.
- Candidate system and KERNEL were fully hashed after transfer/write. Physical
  SYSTEM was never written. Normal boot used the proven `recovery_done` exit.
- Boot ID throughout the test: `5f038d19-5f66-4f51-9f06-6468c4d3c23f`.
- Working14.1 system/boot remain under Ubuntu
  `/root/t110-lineage14/artifacts/lineage14-first-build`, with the rollback pair
  in `artifacts/media-suspend-parent`. All four images were freshly hash-checked
  and the14.1 source was clean. Online14.1 release444868203 remains intact.
- The14.1 system file on tablet userdata was compared against the C: backup and
  then removed to make room. **Its isolated `t110-lineage14-data` directory remains
  on the tablet.** Rollback requires restoring the14.1 system file and matching
  KERNEL from the verified C: copies; switching KERNEL alone will not suffice.
- Old13 data, pre-GApps data and boot logs were first archived privately to C:
  with tar owner/mode metadata. Full gzip readback and19,644 tar entries checked.
  Archive SHA256: `597c9ce59840c17125cfccad463738e22389130079a594263e995f477932d6da`.
  Private archive lives in `/root/t110-android13-audit/hardware-test-20261114`.
  It was not uploaded.13 booted with fresh isolated data and the owner's public
  ADB key; no private key was copied into an image.

## Results

| Check | Actual result |
|---|---|
| Full userspace boot | PASS with serious startup defects; SDK33, user0 unlocked, `sys.boot_completed=1` first observed at279.4seconds of the host monitor, not a precise cold-boot benchmark |
| Physical panel | PARTIAL; owner saw Lineage animation and dialogs, then completed setup and reached the launcher |
| Rendering quality | FAIL; owner reported top-left artifacts; the final600x1024 Android screenshot also contains white bars in that corner |
| Touch input | PASS for tested flow;26 contact-start events in the final bounded trace; owner confirmed Start responds and completed setup with fingers |
| Startup responsiveness | FAIL; owner saw Process system/System UI ANRs, and traces confirm real timeouts; recovery afterward does not erase these failures |
| Speaker playback | FAIL/BLOCKED before audible playback; normal Eleven12second WAV test returned MediaPlayer(1,-19), no primary output stream/PCM opened |
| Bluetooth | Additional failure observed, not a successful qualification; native stack aborted waiting for its HAL/controller |
|14.1 preservation | PASS; source and both C: image pairs unchanged,14.1 data retained, online package still present |

`device_provisioned=1`, `user_setup_complete=1`, and the focused activity became
Trebuchet QuickstepLauncher on the same boot. Physical feedback is the basis for
screen/touch results; Android reporting boot-complete alone was never a screen PASS.

## Audio: concrete missed runtime dependency

The phase4 offline tests checked the real proxy,16 direct stock dependencies,
three ALSA plugin definitions and HIDL loading. They **missed a second class of
dynamically selected modules**: `audio_path.*.mrvl.so`. This is a gap in that
audit's coverage, not evidence of a defective physical speaker.

The working14.1 vendor tree contains all six modules below; the13 image contains
none. Their source hashes/dependencies are in `audio-routing-gap.json`:

- `audio_path.hifi.mrvl.so`
- `audio_path.adda.mrvl.so`
- `audio_path.fm.mrvl.so`
- `audio_path.vc.mrvl.so`
- `audio_path.voip.mrvl.so`
- `audio_path.vt.mrvl.so`

During the as-installed speaker attempt AudioPolicyManager was null and output
creation failed with NO_INIT(-19). One bounded **same-boot audio-service
reinitialization** was then recorded to reveal the lost startup messages:

1. The HIDL factory loads the real primary interface successfully.
2.44100Hz, stereo PCM16, PRIMARY output is requested for speaker device0x2.
3. The stock HAL cannot obtain any `hifi` path handler and cannot find the ALSA
   device name; it rejects open_output_stream.
4. No primary output survives policy initialization, leaving AudioPolicyManager
   null. Eleven cannot create its playback track; no audible PASS was claimed.

`audio_path_config.xml` is **already copied to `/system/etc`** in this image.
Do not add another duplicate configuration as a substitute for the missing modules.
The default policy-engine fallback is also not the immediate missing-handler cause.
There is a separate `/NVM/audio_effect_config.xml` warning to audit after routing.

Next offline audio work must include actual `audio_path` module identity/loading
checks, not only DT_NEEDED closure. Port their full14.1 dependency closure with
strict checks, including the extra `libMarvellWireless.so` dependency of VT,
without substituting old platform libraries or claiming cellular/FM functionality.
Then validate real hardware output opening and routing; successful dlopen alone
is insufficient. The candidate's immutable images were not modified by this test.

## Startup, display and Bluetooth evidence

- System main thread initially waited for default runtime permission provisioning
  in `PermissionPolicyService.grantOrUpgradeDefaultRuntimePermissionsIfNeeded`.
- SystemUI's ImageWallpaper service ANR trace caught main-thread float parsing
  (`FDBigInteger`/`FloatingDecimal`) during Tonal palette/Dagger initialization.
- Another system main-thread trace shows ART class linking while instantiating
  FusedLocationService. This is not proof of a GNSS HAL wait or a GPU deadlock.
- Audit actual loaded AOT/preoptimization state and the expensive initializers
  before changing timeouts or removing Lineage features. ANR collection itself
  also costs CPU; do not run a continuous diagnostic snapshot writer.
- The top-left artifact exists in Android's composed screenshot, localizing it
  before panel scanout. Wallpaper/vector portions draw; audit the text/glyph
  rendering and buffer paths against14.1. The exact rendering cause is unproven.
- Bluetooth tombstone: `Unable to get a Bluetooth service after500ms, start the
  HAL before starting Bluetooth`; another stack-start assertion waited for its
  controller. Do not mark Bluetooth working from the native service process alone.

At one point Android had gone Asleep with a60second screen timeout. A wake request
and temporary USB stay-awake were used for the subsequent physical check. The
framework then reported Awake and CPUs0-1 online, versus CPU0 alone while asleep.
The CPU was already at the stock maximum1205000kHz; a low frequency cap is not
established as the cause. The original USB stay-awake value0 was restored.

All event/log captures are bounded and host-side. The optional on-device logcat
writer was never enabled; no getevent/logcat/screenrecord test process remained.
Raw ANRs, tombstone, screenshots and logs remain private/local under
`SM-T110/tests/android13-complete-20261114`. A private evidence ZIP is kept in the
native hardware-test directory. Do not publish raw logs or the old userdata archive.

## Next step

Fix audio's omitted dynamic modules and investigate startup/rendering offline.
Keep the14.1 recovery path intact. Another full candidate boot needs a fresh user
request; this turn's one full boot test has been used. The phase4 online images
remain an engineering candidate, not a fully working or public release.
