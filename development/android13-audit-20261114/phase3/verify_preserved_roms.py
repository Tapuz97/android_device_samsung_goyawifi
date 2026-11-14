from pathlib import Path
import hashlib
import json
import subprocess

base = Path('/root/t110-lineage14')
expected = {
    'artifacts/lineage14-first-build/boot.img': '93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2',
    'artifacts/lineage14-first-build/system.raw.img': '01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea',
    'artifacts/media-suspend-parent/boot.img': '55df8314699da4ae5b1736100bb798029d023aaf38a4202efb811b6725d8beaf',
    'artifacts/media-suspend-parent/system.raw.img': '37896dd65fac195e3d7c9291f0ee411a52ae6ab2011ac61eb3114d687e9bd00a',
}
results = []
for rel, digest in expected.items():
    path = base / rel
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    assert h.hexdigest() == digest, path
    results.append(dict(path=str(path), sha256=digest))
repo = base / 'android/device/samsung/goyawifi'
head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
status = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], text=True)
assert head == 'ceebd0c9a6c3298765757522f88d75d0bd47b4eb' and not status, (head, status)
Path('/root/t110-android13-audit/preserved-rom-verification.json').write_text(json.dumps(
    dict(status='PASS', source=head, source_clean=True, images=results), indent=2) + '\n')
print('PASS: both preserved14.1 boot/system pairs match known hashes; source remains clean.')
