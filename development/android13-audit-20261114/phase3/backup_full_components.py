"""Archive verified component outputs separately from the working ROM backups."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path('/root/t110-android13')
audit = Path('/root/t110-android13-audit')
report = json.loads((audit / 'full-build-verification.json').read_text())
assert report['status'] == 'PASS' and report['flashed'] is False
output = audit / 'phase3-component-backup'
output.mkdir(exist_ok=True)
archive = output / 't110-android13-full-components-20261114.zip'
readme = '''# Offline component backup - NOT FLASHABLE

This archive contains verified Android13 ARM graphics/audio components, stock
audio dependencies, configuration and compiled SELinux policy from the pinned
source build. It is not a complete ROM, recovery ZIP or boot image. Do not flash
it or copy individual files onto the working14.1 installation.

The included build verification record identifies every payload hash. Source
and reproducible restoration instructions are backed up in branch
t110/android13-offline-audit-20261114, development/android13-audit-20261114/phase3.
The older complete development capsules remain prerequisites for restoration.

Offline build/policy success does not qualify GPU acceleration, sound output,
microphone, service namespaces or suspend/wake on the physical tablet. No tablet
action occurred during these checks. The known working14.1 images are preserved
in their separate existing backup.
'''
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.writestr('README-NOT-FLASHABLE.md', readme)
    for item in report['outputs']:
        path = root / item['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], path
        z.write(path, 'build/' + str(path.relative_to(root)))
    for name in ('full-build-verification.json', 'compiled-audio-policy.json',
                 'vendor-audio-packaging.json', 'audio-load-probe.json'):
        z.write(audit / name, 'verification/' + name)
    for name in ('full-components-5.log', 'vendor-audio.log', 'vendor-audio-1.log', 'vendor-audio-2.log'):
        z.write(root / 'logs' / name, 'logs/' + name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for item in report['outputs']:
        name = 'build/' + item['path']
        assert hashlib.sha256(z.read(name)).hexdigest() == item['sha256'], name
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(output / 'SHA256SUMS-phase3.txt').write_text(f'{digest}  {archive.name}\n')
(output / 'archive.json').write_text(json.dumps(dict(name=archive.name, size=archive.stat().st_size,
                                                     sha256=digest, entries=len(report['outputs']),
                                                     flashable=False), indent=2) + '\n')
print((output / 'archive.json').read_text())
