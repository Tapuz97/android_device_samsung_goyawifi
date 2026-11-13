# Leaving the installed T110 TWRP: established Android13 solution

Use exactly:

    adb -s <T110 serial> shell /sbin/reboot recovery_done

This was already used and boot-verified during Android13 development. Primary
local source references are the restored checkpoint:

- development/android13-v42/scripts/install_canonical_boot46.py:57
- development/android13-v42/scripts/run_core_boot_tablet.py:188
- development/android13-v42/scripts/install_netd_v36_delta.py normal-boot handoff

Generic adb reboot, adb reboot system, TWRP Reboot System, Power Off/Power and
BusyBox attempts returned to TWRP in this continuation. They are not replacements
for the established recovery_done handoff. Do not replace or delete recovery to
work around this behavior. Do not keep trying those known ineffective routes.

The recovered command selected the new kernel (#4) and ran the real Nougat
bootstrap. It mounted physical userdata and the verified read-only system loop.
The saved checkpoint identified the actual next failure: GPU module init_module
returned EFAULT (Bad address). This was a separate Nougat ARM32 vararg-width bug:
struct stat.st_size is64-bit, but raw init_module expects a32-bit unsigned long.
A bounded size_t argument preserves the parameter pointer. The radio loaders
already use size_t. A32-bit regression reproduced the NULL parameter slot and
passed with the corrected argument. No GPU/library success is claimed yet.

Capture the actual new kernel log, boot ID and Android release to distinguish a
normal boot from recovery. Do not count TWRP Android4.4.2 as the Android7 test.
Use only bounded captures; continuous snapshots/live screen streams stay off.
