# Persistent memory and diagnostic defaults

v42-GApps/BOOT48 makes the previous live improvements survive reboot. The kernel
is exactly BOOT47's standard-reclaim kernel; graphics and radio modules are
unchanged. All Lineage/Google apps and both data profiles are retained.

Normal startup activates512MiB compressed swap, writes swappiness100 and sets
page-cluster0. The SELinux fix labels only /proc/sys/vm/swappiness with
proc_t110_swappiness and grants init rw_file_perms to that type. Generic proc
access is not widened. SELinux stays Enforcing; the fork's pre-existing debug
permissive-domain set is unchanged.

The bootstrap saves one early kernel snapshot and checkpoints. It does not fork
the continuous snapshot writer by default. Its diagnostic opt-in is a root-owned,
regular, group/world-nonwritable marker:

- Android: /stage-data/local/tmp/t110-bootlogs/periodic-enabled
- TWRP: /data/local/tmp/t110-bootlogs/periodic-enabled

Keep that marker absent for ordinary operation. Snapshot fixture cases cover
default/explicit mode and symlink, writable-marker and directory rejection.

The t110-logcat file-writing service remains defined and disabled. It no longer
starts automatically. Explicit engineering capture can use init's existing
ctl.start/ctl.stop mechanism. Normal Android logd and one-shot ADB log inspection
remain available; no monitoring feed or continuous file writer is left running.

Validation is recorded in evidence/ui-system-hang-20261112/v42-persistence.
Checks ran on a fresh boot without setting any live override: init's100 value,
precise node label, no denial, active swap, no snapshot/file-log workers, normal
logd, and preserved early snapshot/checkpoints all passed. This verifies the
defaults; it does not certify all UI performance or unfinished hardware.

The security build's API reference check initially exposed pre-existing fork
changes. Patch0106 records only the independently audited GPU, legacy swapon and
device-property definitions in API33 references. Effective rules were unchanged
by that reference repair; no freeze/neverallow check was disabled. The complete
policy build passed before packaging, and permissive domains were compared from
the old/new compiled policies using checkpolicy's binary MLS-to-CIL conversion.
