"""Prepare (do not apply) the T110 Android 13 process-group compatibility patch."""
import difflib
import json
import subprocess
import sys
from pathlib import Path

source = Path('/root/t110-build/lineage20/system/core')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
relative = 'libprocessgroup/processgroup.cpp'
original = subprocess.check_output(['git', '-C', str(source), 'show', 'HEAD:' + relative], text=True)
text = original
assert '#include <sys/stat.h>' in text
text = text.replace('#include <sys/stat.h>', '#include <sys/stat.h>\n#include <sys/vfs.h>\n#include <linux/magic.h>')
fallback = '''// Android's host glibc 2.17 sysroot predates the cgroup-v2 magic constant.
#ifndef CGROUP2_SUPER_MAGIC
#define CGROUP2_SUPER_MAGIC 0x63677270
#endif

'''
marker = 'static bool CgroupGetMemcgAppsPath(std::string* path) {'
helper = '''// T110 bring-up: use a real v1 hierarchy for process lifetime tracking when
// explicitly enabled. Do not pretend an ordinary directory is a cgroup, and
// never write v2 activation controls to a v1 hierarchy.
static bool GetProcessGroupHierarchy(std::string* path, bool* activate = nullptr) {
    if (activate) *activate = true;
    if (!GetBoolProperty("ro.t110.legacy_processgroups", false)) {
        return CgroupGetControllerPath(CGROUPV2_CONTROLLER_NAME, path);
    }

    struct statfs fs;
    auto unified = CgroupMap::GetInstance().FindController(CGROUPV2_CONTROLLER_NAME);
    if (unified.HasValue() && unified.IsUsable() && statfs(unified.path(), &fs) == 0 &&
        fs.f_type == CGROUP2_SUPER_MAGIC) {
        *path = unified.path();
        return true;
    }

    auto legacy = CgroupMap::GetInstance().FindController("cpuacct");
    if (!legacy.HasValue() || legacy.version() != 1 || !legacy.IsUsable() ||
        statfs(legacy.path(), &fs) != 0 || fs.f_type != CGROUP_SUPER_MAGIC) {
        LOG(ERROR) << "No usable v2 or T110 cpuacct process-group hierarchy";
        return false;
    }
    *path = legacy.path();
    if (activate) *activate = false;
    return true;
}

'''
assert text.count(marker) == 1
text = text.replace(marker, fallback + helper + marker)
old = 'if (CgroupGetControllerPath(CGROUPV2_CONTROLLER_NAME, &path)) {'
assert text.count(old) == 1
text = text.replace(old, 'if (GetProcessGroupHierarchy(&path)) {')
old = '    CgroupGetControllerPath(CGROUPV2_CONTROLLER_NAME, &hierarchy_root_path);'
assert text.count(old) == 1
text = text.replace(old, '    if (!GetProcessGroupHierarchy(&hierarchy_root_path)) return -ENOENT;')
old = '''    CgroupGetControllerPath(CGROUPV2_CONTROLLER_NAME, &cgroup);
    return createProcessGroupInternal(uid, initialPid, cgroup, true);'''
assert text.count(old) == 1
text = text.replace(old, '''    bool activate_controllers;
    if (!GetProcessGroupHierarchy(&cgroup, &activate_controllers)) return -ENOENT;
    return createProcessGroupInternal(uid, initialPid, cgroup, activate_controllers);''')
patch = ''.join(difflib.unified_diff(original.splitlines(keepends=True),
                                   text.splitlines(keepends=True),
                                   fromfile='a/' + relative, tofile='b/' + relative))
patch_path = project / 'patches/0009-android13-t110-legacy-processgroups.patch'
patch_path.write_text(patch)
subprocess.run(['git', '-C', str(source), 'apply', '--cached', '--check', str(patch_path)], check=True)
if '--apply' in sys.argv:
    current = (source / relative).read_text()
    assert current in [original, text, text.replace(fallback, '')], 'Unexpected local edits'
    (source / relative).write_text(text)
revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
(project / 'evidence/legacy-processgroups-preparation.json').write_text(json.dumps({
    'base_system_core_revision': revision,
    'patch': patch_path.name,
    'status': 'PATCH_APPLIES_NOT_COMPILED_OR_RUNTIME_TESTED',
    'activation_property': 'ro.t110.legacy_processgroups=true',
    'kernel_requirements': ['CONFIG_CGROUPS=y', 'CONFIG_CGROUP_CPUACCT=y'],
    'userspace_requirement': 'Mounted v1 cpuacct controller registered in cgroups.json',
    'scope': 'Create, kill and cleanup of process groups; not cgroup-v2 freezer or memory-controller emulation'
}, indent=2) + '\n')
print('Prepared and apply-checked:', patch_path.name)
