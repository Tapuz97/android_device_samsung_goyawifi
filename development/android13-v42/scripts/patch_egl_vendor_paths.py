"""Reproduce the hardware-tested, same-length stock EGL path correction."""
import hashlib
import json
from pathlib import Path

project = Path(__file__).resolve().parents[1]
path = project / 'work/device/samsung/t110_bringup/graphics/egl/libEGL_MRVL.so'
original = '0152cddd578d837ae7cd235351ba458fe022d361a6bd99aa7aa7b691c3403716'
patched = '76abd39bbf8b8014d984d8fda812894fd31a25b48cf18ed849cd713092063986'
data = path.read_bytes()
digest = hashlib.sha256(data).hexdigest()
assert digest in (original, patched), 'Unexpected stock EGL blob'
if digest == original:
    assert data.count(b'/system/lib/egl/') == 4
    data = data.replace(b'/system/lib/egl/', b'/vendor/lib/egl/')
    assert hashlib.sha256(data).hexdigest() == patched
    path.write_bytes(data)
checksums = path.parent.parent / 'SHA256SUMS'
text = checksums.read_text()
text = text.replace(original + '  egl/libEGL_MRVL.so', patched + '  egl/libEGL_MRVL.so')
checksums.write_text(text)
for line in text.splitlines():
    expected, filename = line.split()
    assert hashlib.sha256((checksums.parent / filename).read_bytes()).hexdigest() == expected
report = {'original_sha256': original, 'patched_sha256': patched,
          'same_length_path_replacements': 4,
          'hardware_evidence': 'hardware-tests/20261106-091749-core/after-egl-pathfix-latest.txt'}
(project / 'evidence/egl-vendor-path-fix.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
