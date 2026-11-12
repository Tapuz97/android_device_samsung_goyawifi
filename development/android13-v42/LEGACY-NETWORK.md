# T110 Android 13 legacy networking integration

Status: source changes are being compiled. Networking, the framework, and a graphical boot are **not validated** by these patches.

The full v2 image reached BpfLoader in QEMU after the getrandom kernel fix. The kernel has no eBPF syscall or cgroup v2. BpfLoader failed, slept, and init then aborted while iterating an inaccessible `/proc/<pid>/fd` directory to diagnose the delay. Evidence: `evidence/qemu-full-init-v11-native-log.log`.

## Implemented changes

- `0021`: init uses the nonthrowing filesystem iterator API for process diagnostics. Missing and inaccessible directories are logged without aborting init.
- `0022`: the T110-only `ro.t110.legacy_bpf` flag, together with a pre-3.18 kernel check, allows loader startup to finish without eBPF. The existing `bpf.progs_loaded` property is used to release dependent services; it **does not mean programs were loaded** in this compatibility mode. Other configurations retain the original failure checks.
- `0023`: with that flag, netd may continue after absent cgroup v2/BPF initialization or bandwidth-accounting failure. Errors remain visible; unsupported BPF operations still return errors. This is not a complete replacement for BPF policy enforcement.
- `0024`: on pre-3.18 kernels, unavailable BPF maps remain invalid objects so existing callers can handle failures. Modern-kernel FD and map-size abort checks remain intact.
- `0025`: imports the UL null-map guard and legacy qtaguid statistics parsers. Failed BPF partial results are cleared before falling back. The tablet kernel enables `CONFIG_NETFILTER_XT_MATCH_QTAGUID` and `CONFIG_ANDROID_PARANOID_NETWORK`; runtime behavior and permissions remain to be checked.
- `0026`: fixes fatal-reboot command-line parsing to use the string's length rather than `sizeof(std::string)`. New full-boot packages request `androidboot.init_fatal_reboot_target=recovery`; actual Samsung bootloader handling still needs hardware verification.
- `0027`: explicitly labels four read-only T110 compatibility flags as readable platform properties, rather than allowing them to fall through to `default_prop`.

These are engineering bring-up changes. Per-app traffic accounting, Data Saver, metered-network restrictions, VPN lockdown, tethering/offload and firewall behavior must not be represented as working until exercised. The changes do not provide a new eBPF implementation.

## Source basis

The audited donors are the LineageOS-UL `lineage-20.0` repositories:

- [BPF loader compatibility](https://github.com/LineageOS-UL/android_system_bpf/commit/4968dc77cda1fffbf7f9ce52159c9601235008ca), adapted to an explicit T110 flag and kernel-version gate instead of ignoring arbitrary loading failures.
- [Netd startup](https://github.com/LineageOS-UL/android_system_netd/commit/79c122a2b4bb301e820336d6a608d2066ef8eedf) and [bandwidth startup](https://github.com/LineageOS-UL/android_system_netd/commit/8f675a2a3e0cb71276b812c34f011639317ec7e2), adapted to the T110 flag and missing cgroup-v2 case.
- [Invalid BPF map handling](https://github.com/LineageOS-UL/android_frameworks_libs_net/commit/4181eef30d2ea3cdc7393aff303ee56e7d7dfa16), narrowed to pre-eBPF kernels without changing modern validation.
- [Null UID map guard](https://github.com/LineageOS-UL/android_packages_modules_Connectivity/commit/59e502cd564ce8df4d7e43d378d51d82c696c053) and [qtaguid statistics](https://github.com/LineageOS-UL/android_packages_modules_Connectivity/commit/ff018f7a656e7958a42db6d6893f5df35bd985ed). Original patches are retained in `sources/ul-network/`.

No donor build scripts were executed. The full UL framework was not substituted for the pinned Lineage checkout.

## Validation

`evidence/init-diagnostics-regression.log` tests the actual extracted init functions: missing process directory, permission-denied directory, accessible own-process directory, and reboot targets at the end or middle of the command line. All passed. The full system rebuild and subsequent QEMU/hardware tests are still pending at this checkpoint.

The getrandom backport is separate: `patches/0020-kernel-seeded-getrandom.patch`, `artifacts/kernel-random/`, and `evidence/qemu-getrandom-test.log`. Both actual BoringSSL self-tests exited zero in full-system QEMU. No crypto self-test was bypassed.
