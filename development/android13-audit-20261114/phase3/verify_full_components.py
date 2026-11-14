"""Validate the outputs of the real pinned Android13 build, without a device."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/t110-android13')
audit = Path('/root/t110-android13-audit')
source = root / 'android/device/samsung/t110_bringup'
product = root / 'out/target/product/t110_bringup'
records = []

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def record(path, elf=False):
    assert path.is_file() and path.stat().st_size, path
    item = dict(path=str(path.relative_to(root)), bytes=path.stat().st_size, sha256=sha(path))
    if elf:
        header = subprocess.check_output(['readelf', '-h', str(path)], text=True)
        assert 'ELF32' in header and re.search(r'Machine:\s+ARM\b', header), path
        item['architecture'] = 'ELF32 ARM'
    records.append(item)

expected = (
    'system/lib/libhwui.so', 'system/lib/libgui.so', 'system/bin/surfaceflinger',
    'system/vendor/lib/hw/audio.primary.t110.so',
    'system/vendor/lib/libt110_audio_legacy_compat.so',
    'system/vendor/lib/hw/android.hardware.audio@7.1-impl.so',
    'system/vendor/lib/hw/android.hardware.audio.effect@7.0-impl.so',
    'system/vendor/bin/hw/android.hardware.audio.service',
    'system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service',
    'system/vendor/lib/hw/android.hardware.graphics.allocator@2.0-impl.so',
    'system/vendor/lib/hw/android.hardware.graphics.mapper@2.0-impl.so',
    'system/apex/com.android.runtime/bin/linker',
)
for name in expected:
    record(product / name, elf=True)

for item in json.loads((audit / 'vendor-audio-packaging.json').read_text()):
    path = product / 'system' / item['path']
    assert sha(path) == item['packaged_sha256'], path
    record(path, elf=True)

config_count = 0
for line in (source / 'audio/vendor-audio.mk').read_text().splitlines():
    if 'device/samsung/t110_bringup/audio/config/' not in line:
        continue
    src, dest = line.strip().rstrip('\\').strip().split(':', 1)
    src = root / 'android' / src
    dest = dest.replace('$(TARGET_COPY_OUT_VENDOR)', 'system/vendor')
    dest = dest.replace('$(TARGET_COPY_OUT_SYSTEM)', 'system')
    assert '$(' not in dest, dest
    installed = product / dest
    assert sha(installed) == sha(src), installed
    if installed.suffix == '.xml':
        ET.parse(installed)
    record(installed)
    config_count += 1
assert config_count == 60, config_count

for name in ('audio_policy_configuration.xml', 'primary_audio_policy_configuration.xml',
             'r_submix_audio_policy_configuration.xml', 'audio_policy_volumes.xml',
             'default_volume_tables.xml', 'surround_sound_configuration_5_0.xml'):
    path = product / 'system/vendor/etc' / name
    ET.parse(path)
    record(path)
for name in ('primary_audio_policy_configuration.xml', 'init.t110.audio.rc'):
    rel = 'system/vendor/etc/' + ('init/' if name.endswith('.rc') else '') + name
    assert sha(product / rel) == sha(source / 'audio' / name), rel
record(product / 'system/vendor/etc/init/init.t110.audio.rc')

for rel in ('system/etc/selinux', 'system/vendor/etc/selinux', 'system/system_ext/etc/selinux'):
    for path in sorted((product / rel).rglob('*')):
        if path.is_file() and path.stat().st_size:
            record(path)
assert (product / 'obj/ETC/sepolicy_test_intermediates/sepolicy_test').exists()
assert (product / 'fake_packages/sepolicy_freeze_test-timestamp').exists()
policy_result = json.loads((audit / 'compiled-audio-policy.json').read_text())
assert policy_result['status'] == 'PASS'

symbols = subprocess.check_output(['readelf', '--dyn-syms', '-W', str(product / expected[3])], text=True)
assert re.search(r'\bGLOBAL\s+DEFAULT\s+\d+\s+HMI\b', symbols), 'Missing exported HAL module'
for name, marker in (
    ('system/lib/libhwui.so', b'ro.t110.legacy_gpu'),
    ('system/lib/libgui.so', b'ro.t110.legacy_gpu'),
    ('system/apex/com.android.runtime/bin/linker', b'ro.t110.legacy_audio'),
):
    assert marker in (product / name).read_bytes(), (name, marker)

logs = []
for name, marker in (
    ('full-components-5.log', 'T110_FULL_COMPONENT_BUILD_PASS'),
    ('vendor-audio.log', 'T110_VENDOR_AUDIO_BUILD_PASS'),
):
    path = root / 'logs' / name
    text = path.read_text(errors='replace')
    assert marker in text and 'FAILED:' not in text, path
    logs.append(dict(path=name, sha256=sha(path)))

result = dict(status='PASS', scope='Offline full Android ARM component and policy build; no hardware validation',
              vendor_audio_libraries=16, stock_configuration_files=config_count, outputs=records, logs=logs,
              compiled_audio_policy=policy_result,
              flashed=False, gpu_runtime_qualified=False, audio_hardware_qualified=False)
(audit / 'full-build-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'PASS: {len(records)} outputs, 16 vendor audio ELFs and {config_count} configuration files verified.')
