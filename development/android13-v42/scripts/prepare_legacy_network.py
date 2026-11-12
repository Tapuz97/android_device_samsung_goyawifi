"""Adapt the audited LineageOS-UL no-BPF path for the T110 engineering product."""
from pathlib import Path
import difflib
import json
import os
import subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
base = Path('/root/t110-build')
if os.environ.get('WSL_DISTRO_NAME') == 'Ubuntu':
    donor = base / 'ul-audit/connectivity'
    dest = project / 'sources/ul-network'
    dest.mkdir(exist_ok=True)
    for commit in ['59e502cd564ce8df4d7e43d378d51d82c696c053', 'ff018f7a656e7958a42db6d6893f5df35bd985ed']:
        patch = subprocess.check_output(['git', '-C', str(donor), 'show', '--format=', '--binary', commit])
        (dest / (commit + '.patch')).write_bytes(patch)
    print('Exported two audited Connectivity changes; no donor scripts executed')
    raise SystemExit

assert os.environ.get('WSL_DISTRO_NAME') == 'T110Build'
root = base / 'lineage20'
original = {}

def change(repo, name, before, after):
    p = root / repo / name
    text = p.read_text()
    assert text.count(before) == 1, (repo, name, before[:80], text.count(before))
    original.setdefault((repo, name), text)
    p.write_text(text.replace(before, after))

change('system/core', 'init/init.cpp',
       '    for (const auto& entry : std::filesystem::directory_iterator(proc_dir)) {',
       '    std::filesystem::directory_iterator it(proc_dir, ec), end;\n'
       '    if (ec) {\n'
       '        LOG(ERROR) << prefix << "Cannot inspect " << proc_dir << ": " << ec.message();\n'
       '        return;\n'
       '    }\n'
       '    for (; it != end; it.increment(ec)) {\n'
       '        const auto& entry = *it;')
change('system/core', 'init/init.cpp',
       '    }\n}\n\nstatic void DumpFile(',
       '    }\n    if (ec) LOG(ERROR) << prefix << "Cannot finish inspecting " << proc_dir << ": " << ec.message();\n}\n\nstatic void DumpFile(')

change('system/bpf', 'bpfloader/BpfLoader.cpp',
       '    // Create all the pin subdirectories',
       '    // T110 engineering compatibility: no eBPF syscall exists on this kernel.\n'
       '    // This completes loader startup; it does not claim BPF programs are available.\n'
       '    if (android::base::GetBoolProperty("ro.t110.legacy_bpf", false) &&\n'
       '        !android::bpf::isAtLeastKernelVersion(3, 18, 0)) {\n'
       '        ALOGW("T110 legacy network mode: BPF accounting/offload/filtering unavailable");\n'
       '        return android::base::SetProperty("bpf.progs_loaded", "1") ? 0 : 1;\n'
       '    }\n\n    // Create all the pin subdirectories')

for name in ['server/main.cpp', 'server/Controllers.cpp']:
    change('system/netd', name, '#include <cinttypes>', '#include <cinttypes>\n#include <android-base/properties.h>')
change('system/netd', 'server/main.cpp',
       '    std::string cg2_path;\n',
       '    const bool legacy_bpf = android::base::GetBoolProperty("ro.t110.legacy_bpf", false);\n'
       '    std::string cg2_path;\n')
change('system/netd', 'server/main.cpp',
       '        ALOGE("Failed to find cgroup v2 root %s", strerror(errno));\n        exit(1);',
       '        ALOGE("Failed to find cgroup v2 root %s", strerror(errno));\n        if (!legacy_bpf) exit(1);')
change('system/netd', 'server/main.cpp',
       '        ALOGE("libnetd_updatable_init failed");\n        exit(1);\n    }\n    gLog.info("libnetd_updatable_init success");',
       '        ALOGE("libnetd_updatable_init failed");\n'
       '        if (!legacy_bpf) exit(1);\n'
       '        ALOGW("T110 legacy mode: BPF service unavailable; returning errors for BPF operations");\n'
       '    } else {\n        gLog.info("libnetd_updatable_init success");\n    }')
change('system/netd', 'server/Controllers.cpp',
       '        exit(1);\n    }\n    gLog.info("Enabling bandwidth control:',
       '        if (!android::base::GetBoolProperty("ro.t110.legacy_bpf", false)) exit(1);\n'
       '        gLog.error("T110 legacy mode: bandwidth accounting is unavailable");\n'
       '    }\n    gLog.info("Attempted bandwidth control setup:')

# Preserve all modern-kernel size/FD checks. On pre-eBPF kernels only, let the
# existing isValid/error-return paths handle an unavailable map, as in UL.
change('frameworks/libs/net', 'common/native/bpf_headers/include/bpf/BpfMap.h',
       '        mMapFd.reset(mapRetrieve(pathname, flags));\n        if (mMapFd < 0) abort();',
       '        mMapFd.reset(mapRetrieve(pathname, flags));\n'
       '        if (mMapFd < 0 && !isAtLeastKernelVersion(3, 18, 0)) return;\n'
       '        if (mMapFd < 0) abort();')
change('frameworks/libs/net', 'common/native/bpf_headers/include/bpf/BpfMap.h',
       '        mMapFd.reset(createMap(map_type, sizeof(Key), sizeof(Value), max_entries, map_flags));\n        if (mMapFd < 0) abort();',
       '        mMapFd.reset(createMap(map_type, sizeof(Key), sizeof(Value), max_entries, map_flags));\n'
       '        if (mMapFd < 0 && !isAtLeastKernelVersion(3, 18, 0)) return;\n'
       '        if (mMapFd < 0) abort();')

repo = 'packages/modules/Connectivity'
names = ['service-t/src/com/android/server/net/NetworkStatsService.java',
         'service-t/jni/com_android_server_net_NetworkStatsService.cpp']
for name in names:
    original[(repo, name)] = (root / repo / name).read_text()
for commit in ['59e502cd564ce8df4d7e43d378d51d82c696c053', 'ff018f7a656e7958a42db6d6893f5df35bd985ed']:
    patch = project / 'sources/ul-network' / (commit + '.patch')
    subprocess.run(['git', '-C', str(root / repo), 'apply', '--check', str(patch)], check=True)
    subprocess.run(['git', '-C', str(root / repo), 'apply', str(patch)], check=True)
# Do not add a partial failed BPF read to a successful legacy read.
name = names[1]
p = root / repo / name
s = p.read_text()
for call in ['parseIfaceStats(NULL, &stats)', 'parseIfaceStats(iface8.c_str(), &stats)', 'parseUidStats(uid, &stats)']:
    s = s.replace('        if (' + call, '        stats = {};\n        if (' + call)
p.write_text(s)

patch_names = {
    'system/core': '0021-init-nonthrowing-fd-diagnostics.patch',
    'system/bpf': '0022-bpfloader-t110-legacy-kernel.patch',
    'system/netd': '0023-netd-t110-legacy-startup.patch',
    'frameworks/libs/net': '0024-bpfmap-pre-ebpf-error-handling.patch',
    'packages/modules/Connectivity': '0025-connectivity-legacy-qtaguid.patch',
}
for repo, patch_name in patch_names.items():
    output = []
    for (r, name), before in original.items():
        if r != repo:
            continue
        after = (root / r / name).read_text()
        output.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/' + name, tofile='b/' + name))
    assert output
    (project / 'patches' / patch_name).write_text(''.join(output))
print(json.dumps(patch_names, indent=2))
