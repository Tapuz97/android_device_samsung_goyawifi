"""Archive matched tablet kernel/module only after syscall and full-ROM crypto tests."""
from pathlib import Path
import hashlib
import json
import shutil
import re

project = Path(__file__).resolve().parents[1]
base = Path('/root/t110-build')
out = base / 'out-random'
test = project / 'evidence/qemu-getrandom-test.log'
full = project / 'evidence/qemu-full-init-v2-getrandom.log'
assert 'T110_GETRANDOM_REGRESSION_PASS' in test.read_text(errors='replace')
assert re.search(r"Service 'boringssl_self_test32_vendor'.*exited with status 0", full.read_text(errors='replace'))
destination = project / 'artifacts/kernel-random'
destination.mkdir()
modules = list(out.rglob('galcore.ko'))
assert len(modules) == 1
files = {'zImage': out / 'arch/arm/boot/zImage', 'galcore.ko': modules[0],
         'kernel.config': out / '.config', 'build.log': base / 'logs/random-tablet-build.log'}
records = {}
for name, source in files.items():
    shutil.copyfile(source, destination / name)
    records[name] = {'bytes': source.stat().st_size, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
config = (out / '.config').read_text()
assert 'CONFIG_CMDLINE="androidboot.hardware=mrvl"' in config
assert 'CONFIG_CMDLINE_EXTEND=y' in config
assert '# CONFIG_USER_NS is not set' in config
metadata = {
    'status': 'COMPILED_GETRANDOM_REGRESSION_AND_ANDROID_CRYPTO_SELFTEST_PASSED_HARDWARE_PENDING',
    'files': records,
    'parent_kernel': 'artifacts/kernel-platform/provenance.json',
    'incremental_patch': 'patches/0020-kernel-seeded-getrandom.patch',
    'rng_donor': 'android-common-3.4:40bb591cb6abaf540bf9a988e3fac0ca86368865',
    'getrandom_upstream': 'c6e9d6f38894798696f23c8084ca7edbf16ee895',
    'arm_syscall': 384,
    'validation': [str(test.relative_to(project)), str(full.relative_to(project))],
    'note': 'No crypto self-test bypass. Entropy injection appears only in isolated QEMU syscall test, never ROM.'
}
(destination / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, indent=2))
