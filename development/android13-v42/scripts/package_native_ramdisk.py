"""Package a RAM-only Android 13 diagnostic. No device access or flashing."""
import gzip
import argparse
import hashlib
import json
import re
import shutil
import stat
import struct
import subprocess
from pathlib import Path

PROJECT = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
SOURCE = Path('/root/t110-build/lineage20')
OUT = Path('/root/t110-build/out-native/soong')
INTER = OUT / '.intermediates'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version', default='v1')
parser.add_argument('--kernel', type=Path)
parser.add_argument('--kernel-sha256')
args = parser.parse_args()
assert re.fullmatch(r'v[0-9]+', args.version)
assert bool(args.kernel) == bool(args.kernel_sha256)
DEST = PROJECT / ('artifacts/android13-ramdisk-' + args.version)
ROOT = Path('/root/t110-build/native-ramdisk-' + args.version)
VARIANT = 'android_recovery_arm_armv7-a-neon_cortex-a9'
records = {}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def elf(path):
    header = subprocess.check_output(['readelf', '-h', str(path)], text=True)
    assert re.search(r'Class:\s+ELF32', header), path
    assert re.search(r'Machine:\s+ARM\s*\n', header), path
    dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
    return re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)

def unique(pattern):
    paths = [p for p in INTER.glob(pattern) if p.is_file() and not p.is_symlink()]
    assert len(paths) == 1, (pattern, paths)
    return paths[0]

def install(source, target, mode=0o644, binary=False):
    data = source.read_bytes()
    path = ROOT / target
    assert not path.exists(), target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)
    records[target] = {'source': str(source), 'sha256': digest(data), 'bytes': len(data)}
    if binary:
        records[target]['needed'] = elf(source)
    return path

assert not DEST.exists() and not ROOT.exists(), 'Refusing to overwrite prior package'
ROOT.mkdir()
DEST.mkdir(parents=True)
binaries = {
    'init': unique('system/core/init/init_first_stage/android_ramdisk_arm_armv7-a-neon_cortex-a9/init'),
    'system/bin/init': unique(f'system/core/init/init_second_stage/{VARIANT}/init'),
    'system/bin/adbd': unique(f'packages/modules/adb/adbd/{VARIANT}/adbd'),
    'system/bin/sh': unique(f'external/mksh/sh/{VARIANT}/sh'),
    'system/bin/toybox': unique(f'external/toybox/toybox/{VARIANT}/toybox'),
    'system/bin/toolbox': unique(f'system/core/toolbox/toolbox/{VARIANT}/toolbox'),
    'system/bin/linker': OUT / 'target/product/t110_bringup/recovery/root/system/bin/linker',
    'system/bin/recovery': unique('device/samsung/t110_bringup/t110_recovery_watchdog/android_arm_armv7-a-neon_cortex-a9/t110_recovery_watchdog'),
    'system/bin/t110_bionic_probe': PROJECT / 'artifacts/android13-native/t110_bionic_probe',
    'system/bin/t110_processgroup_probe': unique('device/samsung/t110_bringup/t110_processgroup_probe/android_arm_armv7-a-neon_cortex-a9/t110_processgroup_probe'),
    'system/bin/t110_path_probe': unique('device/samsung/t110_bringup/t110_path_probe/android_arm_armv7-a-neon_cortex-a9/t110_path_probe'),
}
pending = []
for target, source in binaries.items():
    install(source, target, 0o755, True)
    pending.extend(elf(source))
while pending:
    name = pending.pop()
    assert '/' not in name and name.endswith('.so'), name
    target = f'system/lib/{name}'
    if target in records:
        continue
    source = unique(f'**/{VARIANT}_shared/{name}')
    install(source, target, binary=True)
    pending.extend(elf(source))

for module, filename, target in [
    ('sepolicy.recovery', 'sepolicy', 'sepolicy'),
    ('plat_file_contexts.recovery', 'plat_file_contexts', 'system/etc/selinux/plat_file_contexts'),
    ('plat_property_contexts.recovery', 'plat_property_contexts', 'system/etc/selinux/plat_property_contexts'),
]:
    install(unique(f'system/sepolicy/**/{module}/**/{filename}'), target)

inputs = PROJECT / 'work/native-ramdisk'
for name, target in {
    'init.rc': 'system/etc/init/hw/init.rc',
    'ueventd.rc': 'system/etc/ueventd.rc',
    'prop.default': 'prop.default',
    'ld.config.txt': 'system/etc/ld.config.txt',
    'cgroups.json': 'system/etc/cgroups.json',
}.items():
    install(inputs / name, target)
install(SOURCE / 'system/core/libprocessgroup/profiles/task_profiles.json', 'system/etc/task_profiles.json')
(ROOT / 't110-native-diagnostic').write_text('Android 13 RAM-only diagnostic ' + args.version + '\n')
for name in ['dev', 'proc', 'sys', 'data', 'tmp', 'mnt', 'linkerconfig', 'vendor', 'odm',
             'debug_ramdisk', 'second_stage_resources', 'apex']:
    (ROOT / name).mkdir(exist_ok=True)
links = {'etc': '/system/etc', 'system/bin/ueventd': 'init', 'sbin': '/system/bin'}
toybox_bp = (SOURCE / 'external/toybox/Android.bp').read_text()
symlinks = re.search(r'toybox_symlinks\s*=\s*\[(.*?)\]', toybox_bp, re.S).group(1)
for name in re.findall(r'"([a-zA-Z0-9_.\[\]-]+)"', symlinks):
    links[f'system/bin/{name}'] = 'toybox'
for name in ['getprop', 'setprop', 'start', 'stop']:
    links[f'system/bin/{name}'] = 'toolbox'
for name, target in links.items():
    if not (ROOT / name).exists():
        (ROOT / name).symlink_to(target)

verifier = OUT / 'host/linux-x86/bin/host_init_verifier'
check = subprocess.run([str(verifier), '--property-contexts=' + str(ROOT / 'system/etc/selinux/plat_property_contexts'),
                        str(ROOT / 'system/etc/init/hw/init.rc')], text=True, capture_output=True)
(DEST / 'init-verifier.txt').write_text(check.stdout + check.stderr)
assert check.returncode == 0, check.stdout + check.stderr

# Deterministic newc archive: all ownership root, no host filesystem xattrs.
archive = bytearray()
def entry(name, mode, data, ino):
    fields = [ino, mode, 0, 0, 2 if stat.S_ISDIR(mode) else 1, 0, len(data), 0, 0, 0, 0,
              len(name.encode()) + 1, 0]
    archive.extend(b'070701' + ''.join(f'{n:08x}' for n in fields).encode())
    archive.extend(name.encode() + b'\0')
    archive.extend(b'\0' * (-len(archive) % 4))
    archive.extend(data)
    archive.extend(b'\0' * (-len(archive) % 4))
for ino, path in enumerate(sorted(ROOT.rglob('*')), 1):
    mode = path.lstat().st_mode
    data = str(path.readlink()).encode() if path.is_symlink() else b'' if path.is_dir() else path.read_bytes()
    entry(path.relative_to(ROOT).as_posix(), mode, data, ino)
entry('TRAILER!!!', 0, b'', ino + 1)
archive.extend(b'\0' * (-len(archive) % 512))
ramdisk = gzip.compress(bytes(archive), compresslevel=9, mtime=0)
(DEST / 'ramdisk.cpio.gz').write_bytes(ramdisk)

template = (PROJECT / 'hardware-tests/20261105-modern-diagnostic/boot.img').read_bytes()
assert template[:8] == b'ANDROID!'
ks, ka, rs, ra, ss, sa, ta, page, dt, unused = struct.unpack_from('<10I', template, 8)
assert page == 2048 and ss == 0 and dt == 0
align = lambda n: (n + page - 1) // page * page
assert len(template) == page + align(ks) + align(rs), 'Unexpected template tail'
kernel = template[page:page + ks]
assert digest(kernel) == 'f4e735162c5050a7e7d2dbee1f1cff41ff26158ff5905375d140c7ce10377eb6'
def image_id(k, r):
    h = hashlib.sha1()
    for data in (k, r, b''):
        h.update(data)
        h.update(struct.pack('<I', len(data)))
    return h.digest() + bytes(12)
old_rd = template[page + align(ks):page + align(ks) + rs]
assert template[576:608] == image_id(kernel, old_rd)
if args.kernel:
    kernel = args.kernel.read_bytes()
    assert digest(kernel) == args.kernel_sha256
ks = len(kernel)
header = bytearray(template[:page])
struct.pack_into('<I', header, 8, ks)
struct.pack_into('<I', header, 16, len(ramdisk))
header[576:608] = image_id(kernel, ramdisk)
image = bytes(header) + kernel + bytes(align(ks) - ks) + ramdisk + bytes(align(len(ramdisk)) - len(ramdisk))
assert len(image) <= 16777216, ('BOOT partition overflow', len(image))
(DEST / 'boot.img').write_bytes(image)
full = image + bytes(16777216 - len(image))
(DEST / 'KERNEL.img').write_bytes(full)
metadata = {'status': 'PACKAGED_NOT_BOOT_TESTED', 'image_bytes': len(image), 'partition_bytes': len(full),
            'kernel_sha256': digest(kernel), 'ramdisk_sha256': digest(ramdisk),
            'full_boot_sha256': digest(full), 'full_boot_md5': hashlib.md5(full).hexdigest(),
            'init_rc_validation': 'PASS', 'files': records,
            'scope': 'Modern init/ADB RAM-only diagnostic; no stock partition mounts; not a full OS',
            'fallback': 'Recovery process requests installed recovery after 120s unless /dev/t110-keepalive exists'}
patch = PROJECT / 'patches/0009-android13-t110-legacy-processgroups.patch'
shutil.copyfile(patch, DEST / patch.name)
metadata['processgroup_patch_sha256'] = digest(patch.read_bytes())
adb_patch = PROJECT / 'patches/0013-adbd-t110-synchronous-functionfs.patch'
if adb_patch.exists():
    shutil.copyfile(adb_patch, DEST / adb_patch.name)
    metadata['adbd_compatibility_patch_sha256'] = digest(adb_patch.read_bytes())
    metadata['adbd_source_revision'] = subprocess.check_output(
        ['git', '-C', str(SOURCE / 'packages/modules/adb'), 'rev-parse', 'HEAD'], text=True).strip()
if args.kernel:
    patch = PROJECT / 'patches/0010-kernel-opath-fstat.patch'
    shutil.copyfile(patch, DEST / patch.name)
    metadata['additional_kernel_patch_sha256'] = digest(patch.read_bytes())
    provenance = json.loads((args.kernel.parent / 'build-provenance.json').read_text())
    assert provenance['sha256'] == args.kernel_sha256
    for item in provenance['patches']:
        assert digest((PROJECT / item['file']).read_bytes()) == item['sha256']
    (DEST / 'kernel-build-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
(DEST / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps({k: v for k, v in metadata.items() if k != 'files'}, indent=2))
