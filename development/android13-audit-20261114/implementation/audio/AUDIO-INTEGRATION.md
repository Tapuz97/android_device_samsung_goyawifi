# Real audio adapter integration

The adapter is a real forwarding HAL, not the old silent stub. It exposes a
full-size Android13 device and streams while retaining API2.0 and the exact
original allocation. The old dump slot is124 on ARM; modern get_microphones
occupies that slot. Copying or casting the complete old device is unsafe.

The standalone parameter container avoids depending on a cross-version
AudioParameter/String8 ABI. All retained stream callbacks forward their original
pointer. Unsupported modern operations stay absent or return ENOSYS. Local
speaker/headphone routing adds the stock HiFi keys,44100Hz rejection follows the
normal suggested-config protocol, and input activation/standby/close use
STREAM_IN_ACTIVE. No synthetic microphone samples or silent writes are returned.

## Build/package wiring to complete in the full candidate

- Install this directory's Android.bp and sources as the product's audio module.
  Select `audio.primary.t110` and `libt110_audio_legacy_compat`, remove the old
  `audio.primary.default` selection, and set `ro.hardware.audio.primary=t110`.
- Use the provided primary policy in place of primary_audio_policy_configuration_7_0.xml.
  Retain the standard service/effects/submix/volume configuration. Keep Bluetooth
  in its native separate module, adding its standard policy when qualifying audio.
- Install the original, hash-matched audio.primary.mrvl.so plus its complete
  dependency closure. The adapter opens ONLY that exact vendor path and validates
  the ANI7 module identity; it will not proxy arbitrary HALs.
- Extend the existing exact-path shim mechanism for
  `/vendor/lib/hw/audio.primary.mrvl.so|libt110_audio_legacy_compat.so` and
  `/vendor/lib/libacm.so|libcrypto.so`. Verify the resulting image/linker config.
  MD5 is required by this old calibration library; do not replace modern crypto.
- Restore stock ALSA configuration/plugins and all audio routing/calibration XMLs.
  Original libasound has hardcoded `/system/usr/share/alsa` and
  `/system/usr/lib/alsa-lib` paths. A vendor namespace cannot be assumed to load
  plugins from those paths. Resolve the exact config/plugin search and namespace
  placement before enabling the real module in an image. ALSA_CONFIG_PATH exists;
  an ALSA_PLUGIN_DIR environment override was not found in this stock library.
- Include init.t110.audio.rc before class-hal startup. In the candidate's compiled
  SELinux policy, label ONLY the two proc clock nodes and permit init setattr plus
  hal_audio access to that type. Do not enable global permissive mode or generic
  proc writes. Add the actual ALSA/config/plugin file labels and namespace rules.

The source and Android ARM module compile/link checks are complete for this pass.
The legacy blob's dynamic closure, full HIDL/service integration, policy build and
actual sound remain release blockers. These files are staged integration inputs;
the preserved product has not been switched from its stub in a flashable image.
