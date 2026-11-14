# Complete Android13 image and production namespace checks — in progress

The phase3 source/component checkpoint is ce73cdbb2644e1919645068853657a5b9c3efa3c.
Its complete component builds,122 ARM helper checks,16 strict stock-audio ELF
checks and136 output hashes passed. The separately verified component archive
and both working/rollback14.1 ROM pairs are preserved.

Full systemimage compilation is now running at2 jobs, with high-memory jobs
limited to one. The first8-job invocation was stopped cleanly to apply the supported
2047 MiB loop-file geometry and use observed spare build-host capacity. All
completed outputs are retained. No failed/interrupted run counts as PASS.
This is a userdata loop file; no physical SYSTEM write is intended or performed.

The12-job run reached95% before the15 GiB WSL guest plus4 GiB swap exhausted
memory with multiple Java heaps. The Linux OOM log explicitly identifies Ninja
as the victim (exit137). The final2-job invocation reuses the completed outputs
and has approximately3005 actions remaining, rather than restarting compilation.
No compiler/type/policy check is disabled to address this host resource failure.
The final source also advertises the verified GLES2 version131072 explicitly;
that capability declaration was missing from the source product's properties.

The source product has no vendor VNDK version and uses Android's actual legacy
namespace configuration, with normal isolated APEX namespaces. Host linkerconfig
is part of the build. Namespace validation will use the assembled candidate's
flattened APEX mounts, generated configuration and actual serialized Bionic
properties. No LD_LIBRARY_PATH/LD_PRELOAD or target-SDK22 bypass is allowed.
Loader --list checks skip library constructors; audio dlopen/configuration tests
will not call hardware-device open functions. These are userspace link checks,
not emulation of the PXA988/GPU/radio or the tablet's Linux3.4 kernel.

Namespace tooling uses the exact pinned property serializer/parser source and a
small ARM diagnostic program outside PRODUCT_PACKAGES. The host compilation
includes algorithm/cstring explicitly for libstdc++ rather than depending on
libc++ transitive includes; no upstream serializer logic is modified.

The preserved13 bootv48 has already been parsed and hashed without modification.
Its kernel/module/stage and runtime logging/memory fixes remain available. The
bootstrap explicitly keeps window GPU rendering off; its diagnostic logcat is
disabled and requires manual start. A matching candidate boot/policy must be
reviewed before any physical test; the working14.1 boot is never repurposed.

The matched14 kernel is now verified to have exactly the same embedded13
configuration and byte-identical galcore module; only init/initramfs.c differs
from the old kernel baseline. The candidate boot builder carries that proven
archive-end correction,13 startup and the new policy forward. Its original
stager/module remain byte-identical. It retains disabled continuous logging and
zram tuning, corrects the legacy GPU-device alias, and enables the newly built
window path only after complete-image/policy/namespace gates pass.

Android13's actual ueventd places galcore under /dev/graphics, just as in the
qualified14.1 fix. The old13 rules configured only /dev/galcore. The exact real
node now has a normal vendor ueventd rule and gpu_device label; ordinary apps
must remain forbidden the unrelated graphics_device type. These late source
changes require the final cached full build before image verification.

Production tests use the real ARM linkerconfig and linker inside a private
read-only-image/overlay mount namespace. APEX bindings and factory activation
metadata come from the candidate's real manifests. Libraries are dependencies
of real PIE diagnostic executables for constructor-free loading. Actual audio
tests also exercise libhardware's module selection, proxy identity, three ALSA
plugin definitions and HIDL-library loading, with no hardware opens. No SDK
setter is present in these production probes. The native program/library
checks retain ordinary loader search behavior. The host generator is also built.

Wi-Fi/BT source already bounds module lengths and converts st_size to ARM32
size_t before raw init_module, preserving the prior ABI lesson. Vendor-init
audio chown/chmod and property changes are covered by existing standard policy;
the new actual-image policy check verifies that actor instead of guessing.

No full image/namespace PASS is claimed yet. No ADB, transfer, reboot, flash or
tablet operation has occurred. See phase4 tool/source checkpoints for resuming.

## Full-image build recovery

The12-job attempt reached95% before Linux killed Ninja for memory pressure.
The cached build now uses two jobs and one high-memory slot; the failure and
kernel OOM evidence remain in the build logs. No compilation check was disabled.

The next attempt exposed the pinned ARM WebView APK as a133-byte Git LFS pointer.
`restore_pinned_webview.py` fetches its exact98,126,751-byte payload through the
repository's declared public Gerrit LFS endpoint, then checks its pinned SHA256
and all ZIP entries. The source revision and WebView feature remain unchanged.
Build4 resumes with that verified payload; its log is complete-image-4.log.

Actual-image policy results now bind to the image and compiled-policy hashes.
Image extraction removes previous output files before each dump so a missing
candidate file cannot pass through a stale extraction. Matching boot/backup gates
require the same image hash in policy, namespace, and filesystem records.
