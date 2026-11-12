# Pending native diagnostic ramdisk inputs

These are source inputs, not a complete or flashable ramdisk. The Android 13 init/ADB binaries and real SELinux policy are not built yet.

`cgroups.json` is intended for `/system/etc/cgroups.json`, with `/etc` linking to `/system/etc` before Android init's SetupCgroups action. It uses controllers enabled in the tested T110 kernel. Set `ro.t110.legacy_processgroups=true` and `ro.config.per_app_memcg=false` in the ramdisk's `/prop.default`, and apply patch 0009 to system/core. Without the patch, Android 13 still assumes a cgroup-v2 hierarchy for service process groups.

The fallback must be tested for create, child membership, kill, and cleanup on the real kernel before being considered usable. It does not implement cgroup-v2 freezer semantics or memory controls. Keep it out of any release image until those limits are resolved or deliberately disabled.
