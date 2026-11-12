"""Archive the newly built O_PATH kernel without overwriting tested artifacts."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
base = Path('/root/t110-build')
ffs = '--ffs' in sys.argv
mmap = '--mmap' in sys.argv or ffs
destination = project / ('artifacts/kernel-native-init-ffs' if ffs else 'artifacts/kernel-native-init-mmap' if mmap else 'artifacts/kernel-native-init')
assert not destination.exists()
log = base / ('logs/t110-functionfs-build.log' if ffs else 'logs/t110-mmap-build.log' if mmap else 'logs/t110-opath-build.log')
build_log = log.read_text()
assert 'Kernel: arch/arm/boot/zImage is ready' in build_log
destination.mkdir()
for source, name in [(base / 'out-binder-modern/arch/arm/boot/zImage', 'zImage'),
                     (base / 'out-binder-modern/.config', 'kernel.config'),
                     (log, 'build.log')]:
    shutil.copyfile(source, destination / name)
provenance = json.loads((project / 'artifacts/kernel-binder-modern/build-provenance.json').read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
if mmap:
    import re
    def config(path):
        return dict(re.findall(r'^(CONFIG_\w+)=(.*)$', path.read_text(), re.M))
    before = config(project / 'artifacts/kernel-binder-modern/kernel.config')
    after = config(destination / 'kernel.config')
    assert all(after.get(k) == v for k, v in before.items())
    assert set(after) - set(before) == {'CONFIG_HAVE_ARCH_MMAP_RND_BITS', 'CONFIG_ARCH_MMAP_RND_BITS_MIN', 'CONFIG_ARCH_MMAP_RND_BITS_MAX', 'CONFIG_ARCH_MMAP_RND_BITS'}
    assert after['CONFIG_ARCH_MMAP_RND_BITS_MAX'] == '16'
    provenance['config_sha256'] = sha(destination / 'kernel.config')
else:
    assert sha(destination / 'kernel.config') == provenance['config_sha256']
patch = project / 'patches/0010-kernel-opath-fstat.patch'
provenance['patches'].append({'file': str(patch.relative_to(project)), 'sha256': sha(patch)})
if mmap:
    patch = project / 'patches/0011-arm-mmap-entropy-control.patch'
    provenance['patches'].append({'file': str(patch.relative_to(project)), 'sha256': sha(patch)})
    provenance['changes'].append('Real bounded ARM mmap randomization sysctl from pinned Android common donor')
if ffs:
    patch = project / 'patches/0012-functionfs-string-table-lifetime.patch'
    provenance['patches'].append({'file': str(patch.relative_to(project)), 'sha256': sha(patch)})
    provenance['changes'].append('Retain FunctionFS USB string-table allocation through bind and normal cleanup; before/after ASan regression passes')
provenance['status'] = 'COMPILED_NOT_TABLET_TESTED'
provenance['sha256'] = sha(destination / 'zImage')
provenance['bytes'] = (destination / 'zImage').stat().st_size
provenance['runtime_validation'] = 'Parent kernel hardware tests do not establish this build; O_PATH hardware regression pending'
provenance['additional_upstream'] = '55815f70147dcfa3ead5738fd56d3574e2e3c1c2'
provenance['remaining'] = ['Hardware boot and O_PATH regression', 'Modern Android init/ADB bring-up', 'Full OS/HAL integration']
provenance['changes'].append('O_PATH fstat support required by Android 13 bionic realpath and SELinux restorecon')
(destination / 'build-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
diff = subprocess.check_output(['git', '-C', str(base / 'kernel-binder-modern'), 'diff', '--binary'])
(destination / 'cumulative-source.diff').write_bytes(diff)
print(provenance['sha256'])
