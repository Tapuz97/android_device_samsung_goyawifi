# Full platform integration — build in progress

The exact1242-project Android13 source checkpoint has been restored on internal
C under Ubuntu /root/t110-android13/android. Original25 project deltas and the
private custom product are restored; graphics patches0001–0003 are applied.

The real audio adapter replaces the stub in the candidate product. Stock audio
libraries and plugins are selected with full ELF checks enabled. The duplicate
stock libeffects selection exposed by the full build was removed in favor of
Android13's existing vendor provider. The old HAL and libacm receive explicit
DT_NEEDED dependencies for the real list-operation shim and modern libcrypto.
These modified binary copies are generated locally from verified stock inputs;
the originals are unchanged and no binaries are published in source Git.

ALSA configuration selects vendor plugin paths through each plugin type's lib
entry. No /system/usr plugin directory is opened to the vendor namespace. Stock
data-only ALSA/card configuration and audio routing/calibration XMLs are preserved.
The standard audio service definition is retained with a device-only override
adding ALSA_CONFIG_PATH; normal groups/profiles/capabilities remain intact.

Real ARM Android13 loader diagnostics loaded the HAL and all three plugins and
parsed the explicit codec lib path without opening hardware. A diagnostic-only
process target SDK22 was needed because of libippsp text relocations. The candidate
linker now has a separate ro.t110.legacy_audio opt-in restricted to that exact DSP
library path. No target-SDK lowering occurs in the HAL or product. Existing GPU
exception remains unchanged. Production namespace and SELinux are build gates,
not claimed qualified by that diagnostic environment.

The new policy gives only the default audio HAL execmod access to its dedicated
DSP file type. Public neverallow rules still forbid other domains from receiving
that access, using the public hal_audio_server attribute. The exact two proc clock
nodes receive their own label/permissions. The exact three stock clock properties
use existing HAL-readable audio_config_prop instead of the broader persist.audio
prefix's system-internal type. Source and API33 definitions are synchronized.
No new permissive domains or disabled neverallow/freeze tests are introduced.

Full libhwui, libgui, linker, audio HIDL/service, adapter and SELinux build/test
targets passed in full-components-5.log (7799 actions, 15m19s). The compiled
policy's clock, configuration and property permissions pass direct queries;
the DSP execmod allow is restricted to hal_audio_default. The separate vendor
ELF/configuration and full compositor build remains pending. Logs live at
/root/t110-android13/logs/full-components*.log. The first driver attempt exposed
standard envsetup's unset-TOP convention; the driver no longer imposes nounset
on that shell API. A later build exposed duplicate libeffects packaging, fixed
above. Compilation was resumed at eight jobs after observing available memory;
completed outputs were retained. No failed or interrupted run counts as PASS.
The vendor configuration build exposed inherited-product path expansion bugs.
Generated copy rules now use explicit source-root paths rather than mutable
LOCAL_PATH or a custom variable stripped by product import. The 16 packaged
binary hashes remain identical across regeneration. All60 configuration copy
targets and the primary policy/service files are requested explicitly.

Strict vendor ELF checks then exposed26 imported ARM/compiler-runtime and stdio
helpers that Bionic retains under LIBC_PRIVATE but omits from LLNDK stubs. A
device-private shim now exports exact PIC ARM tail trampolines to the actual
libc implementations; it does not reimplement math or FILE layout. Multi-register
division results, original arguments, caller SP and LR are preserved. Only10
stock libraries importing these helpers receive the explicit shim dependency.
No undefined-symbol checks are disabled. A full Soong ARM probe exercises every
helper through the explicit shim handle, cold and warm, including integer64
divmod and buffered file IO. Probe results are still pending in this checkpoint.
The assembly and C++ files use distinct basenames to avoid Soong object collision.

Working14.1 images, source, online backups and tablet remain untouched. No ADB
command, boot, transfer or flash has been performed during this integration.
