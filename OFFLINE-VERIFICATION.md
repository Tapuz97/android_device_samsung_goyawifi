# Current Nougat candidate: startup not yet qualified

Android7.1.2 / LineageOS14.1 builds and passes offline graphics-layout, vendor
closure, source-image and filesystem checks.164 actual files were extracted and
compared. No functional hardware item is marked passing.

The earlier generic restart attempts stayed in recovery because the established
Android13 exit command was not used. /sbin/reboot recovery_done selected kernel4
and mounted userdata/system. The precise next failure was GPU init_module EFAULT.
A64-bit stat length displaced the parameter pointer in Nougat ARM32's variadic
syscall. The bounded size_t fix passed a32-bit ABI regression. Its reversible
240KiB image delta and matching boot passed full tablet hash/read-back checks.
The subsequent boot stayed on Samsung logo without USB; saved logs are awaited.

Kernel source/config/toolchain pins are in kernel-source.json. Source changes
also restore bounded storage readiness and a real cache mountpoint. Startup
records are one-shot; no continuous snapshot writer or live screen feed runs.
This is permissive/userdebug with no Google apps. GPS and LED integration remain
pending. Normal Lineage components and physical-navigation support are retained.

- boot.img: 16777216bytes; SHA25689caa9dae53e77a8abe5d3838a1c475067e7451ebb816e744fc8a01cfff784ae
- system.raw.img: 1594884096bytes; SHA25660a0f45f77076d8b72a64d82cbb0159cf6f6a7bb0e4dca40ccb67e86069899bd
