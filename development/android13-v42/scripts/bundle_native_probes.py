"""Bundle only freshly built ARM Android libraries; never use stock binaries."""
import hashlib
import argparse
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

root = Path('/root/t110-build/lineage20')
out = Path('/root/t110-build/out-native/soong')
product = out / 'target/product/t110_bringup'
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--hwbinder', action='store_true')
args = parser.parse_args()
destination = project / ('artifacts/android13-hwbinder/bundle' if args.hwbinder else 'artifacts/android13-native/bundle')

def elf_info(path):
    header = subprocess.check_output(['readelf', '-h', str(path)], text=True)
    assert re.search(r'Class:\s+ELF32', header), path
    assert re.search(r'Machine:\s+ARM\s*\n', header), path
    dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
    return re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)

def find_built(name, binary=False):
    subdir = 'bin' if binary else 'lib'
    for path in [product / 'system' / subdir / 'bootstrap' / name,
                 product / 'system' / subdir / name]:
        if path.is_file() and not path.is_symlink():
            return path
    candidates = [p for p in (out / '.intermediates').rglob(name)
                  if p.is_file() and not p.is_symlink() and
                  '/unstripped/' not in str(p) and
                  re.search(r'/android_arm_armv7-a-neon_cortex-a9(?:_shared)?/', str(p))]
    assert len(candidates) == 1, (name, candidates)
    return candidates[0]

names = ['linker', 't110_hwbinder_probe'] if args.hwbinder else ['linker', 't110_libbinder_probe', 't110_processgroup_probe']
bins = {name: find_built(name, True) for name in names}
libs = {}
pending = list(bins.values())
while pending:
    for name in elf_info(pending.pop()):
        assert '/' not in name and name.endswith('.so'), name
        if name not in libs:
            libs[name] = find_built(name)
            pending.append(libs[name])

assert not destination.exists(), 'Refusing to overwrite an existing bundle'
metadata = {'status': 'COMPILED_NOT_RUNTIME_TESTED', 'files': {},
            'system_core_revision': subprocess.check_output(
                ['git', '-C', str(root / 'system/core'), 'rev-parse', 'HEAD'], text=True).strip(),
            'system_core_patch': 'patches/0009-android13-t110-legacy-processgroups.patch',
            'system_core_patch_sha256': hashlib.sha256((project /
                'patches/0009-android13-t110-legacy-processgroups.patch').read_bytes()).hexdigest(),
            'source_pins': 'evidence/android13-native-source-pins.json'}
if args.hwbinder:
    metadata['hidl_source_revisions'] = {name: subprocess.check_output(
        ['git', '-C', str(root/name), 'rev-parse', 'HEAD'], text=True).strip()
        for name in ['system/libhwbinder', 'system/libhidl', 'system/libfmq']}
    metadata['probe_source_sha256'] = hashlib.sha256((project / 'work/device/samsung/t110_bringup/hwbinder_probe.cpp').read_bytes()).hexdigest()
for directory, files in [('bin', bins), ('lib', libs)]:
    (destination / directory).mkdir(parents=True)
    for name, source in sorted(files.items()):
        target = destination / directory / name
        shutil.copyfile(source, target)
        target.chmod(0o755 if directory == 'bin' else 0o644)
        metadata['files'][f'{directory}/{name}'] = {
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'bytes': target.stat().st_size,
            'source': str(source), 'needed': elf_info(source)}
(destination / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
archive = destination.parent / ('t110-hwbinder.tar' if args.hwbinder else 't110-native-probes.tar')
with tarfile.open(archive, 'x') as tar:
    for path in sorted(destination.rglob('*')):
        if path.is_file():
            info = tar.gettarinfo(str(path), arcname=('t110-hwbinder/' if args.hwbinder else 't110-native/') + path.relative_to(destination).as_posix())
            info.uid = info.gid = 0
            info.uname = info.gname = 'root'
            info.mode = 0o755 if '/bin/' in info.name else 0o644
            with path.open('rb') as stream:
                tar.addfile(info, stream)
print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size,
                  'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'binaries': list(bins), 'libraries': sorted(libs)}, indent=2))
