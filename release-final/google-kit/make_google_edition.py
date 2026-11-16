#!/usr/bin/env python3
"""Build the Google edition locally from the release ROM and original OpenGApps.

Linux/WSL: python3, lzip and e2fsprogs; allow 8 GiB temporary disk space.
Never connects to a tablet. Google APKs are obtained from the user's upstream ZIP.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from verify_modern_package import verify

HERE = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk := f.read(1024 * 1024): h.update(chunk)
    return h.hexdigest()

def command(*args):
    p = subprocess.run(list(map(str, args)), capture_output=True, text=True, check=True)
    return p.stdout

def safe(relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts: raise ValueError('Unsafe member path')
    return p

def build(rom, gapps, output):
    reference = json.loads((HERE / 'google-payload-manifest.json').read_text())
    native = json.loads((HERE / 'native-tree-manifest.json').read_text())
    if output.exists(): raise ValueError('Output already exists; choose a new filename')
    base_manifest = verify(rom)
    if base_manifest['google_apps'] or base_manifest['system_raw_sha256'] != reference['base_raw_sha256']:
        raise ValueError('Use the exact Google-free ROM for this release')
    if sha(gapps) != reference['upstream_zip_sha256']:
        raise ValueError('Wrong OpenGApps ZIP; require ARM 7.1 pico 20220215, exact SHA256 in README')
    for tool in ('debugfs', 'e2fsck', 'lzip'):
        if not shutil.which(tool): raise RuntimeError('Missing Linux tool: ' + tool)
    expected = {r['file']: r for r in reference['files']}
    overlay_relative = 'vendor/overlay/T110SetupLayout.apk'
    if sha(HERE / 'T110SetupLayout.apk') != expected[overlay_relative]['sha256']:
        raise ValueError('Setup overlay checksum mismatch')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='t110-google-') as temporary:
        tmp = Path(temporary)
        image = tmp / 'system.raw.img'
        stage = tmp / 'payload'
        stage.mkdir()
        with zipfile.ZipFile(rom) as package:
            with package.open('system.raw.img.gz') as compressed, gzip.GzipFile(fileobj=compressed) as raw, image.open('wb') as target:
                shutil.copyfileobj(raw, target)
            (tmp / 'boot.img').write_bytes(package.read('boot.img'))
        if sha(image) != reference['base_raw_sha256']: raise ValueError('Raw base mismatch')
        with zipfile.ZipFile(gapps) as archive:
            for name in reference['selected_archives']:
                print('Reading upstream ' + name, flush=True)
                data = subprocess.check_output(['lzip', '-dc'], input=archive.read(name))
                with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as tar:
                    members = tar.getmembers()
                    densities = {PurePosixPath(m.name).parts[1] for m in members if len(PurePosixPath(m.name).parts) > 1}
                    density = '240' if '240' in densities else 'nodpi'
                    for member in members:
                        parts = safe(member.name).parts
                        if len(parts) < 3 or parts[1] not in ('common', density): continue
                        if member.isdir(): continue
                        if not member.isfile(): raise ValueError('Unexpected archive link/device')
                        relative = str(safe(str(PurePosixPath(*parts[2:]))))
                        if relative not in expected: raise ValueError('Unexpected payload: ' + relative)
                        target = stage / relative
                        if target.exists(): raise ValueError('Duplicate payload: ' + relative)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(tar.extractfile(member).read())
        overlay = stage / overlay_relative
        overlay.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / 'T110SetupLayout.apk', overlay)
        actual = {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}
        if actual != set(expected): raise ValueError('Payload list mismatch')
        for relative, record in expected.items():
            if sha(stage / relative) != record['sha256']: raise ValueError('Payload hash mismatch: ' + relative)
        context = tmp / 'context.bin'
        context.write_bytes(b'u:object_r:system_file:s0\0')
        edits, directories, labeled = [], set(), set()
        for relative in sorted(expected):
            if 'Inode:' in command('debugfs', '-R', 'stat /' + relative, image):
                raise ValueError('Refusing to overwrite a native file: ' + relative)
            for parent in reversed(PurePosixPath(relative).parents):
                if str(parent) == '.' or str(parent) in directories: continue
                directories.add(str(parent))
                if 'Inode:' not in command('debugfs', '-R', 'stat /' + str(parent), image):
                    edits += ['mkdir /' + str(parent), 'set_inode_field /' + str(parent) + ' mode 040755',
                              'set_inode_field /' + str(parent) + ' uid 0',
                              'set_inode_field /' + str(parent) + ' gid 0',
                              'ea_set -f ' + str(context) + ' /' + str(parent) + ' security.selinux']
                    labeled.add(str(parent))
            edits += ['write ' + str(stage / relative) + ' /' + relative,
                      'set_inode_field /' + relative + ' mode 0100644',
                      'set_inode_field /' + relative + ' uid 0',
                      'set_inode_field /' + relative + ' gid 0',
                      'ea_set -f ' + str(context) + ' /' + relative + ' security.selinux']
            labeled.add(relative)
        script = tmp / 'edits.txt'
        script.write_text('\n'.join(edits) + '\n')
        p = subprocess.run(['debugfs', '-w', '-f', str(script), str(image)], capture_output=True, text=True)
        if p.returncode or any(s in p.stderr for s in ('File not found', 'Could not', 'Usage:')):
            raise RuntimeError('Image construction failed: ' + p.stderr[-1200:])
        command('e2fsck', '-fn', image)
        tree = tmp / 'readback'
        tree.mkdir()
        command('debugfs', '-R', 'rdump / ' + str(tree), image)
        combined = {r['file']: r['sha256'] for r in native['files']}
        combined.update({name: r['sha256'] for name, r in expected.items()})
        actual_files = {str(p.relative_to(tree)) for p in tree.rglob('*') if p.is_file() and not p.is_symlink()}
        if actual_files != set(combined): raise ValueError('Final image inventory mismatch')
        for relative, digest in combined.items():
            if sha(tree / relative) != digest: raise ValueError('Final file mismatch: ' + relative)
        import os
        actual_links = {str(p.relative_to(tree)): os.readlink(p) for p in tree.rglob('*') if p.is_symlink()}
        if actual_links != native['symlinks']: raise ValueError('Native symlink mismatch')
        for relative in sorted(labeled):
            readback = tmp / 'label.bin'
            command('debugfs', '-R', 'ea_get -f ' + str(readback) + ' /' + relative + ' security.selinux', image)
            if readback.read_bytes() != context.read_bytes(): raise ValueError('SELinux label mismatch')
        compressed = tmp / 'system.raw.img.gz'
        with image.open('rb') as source, compressed.open('wb') as target:
            with gzip.GzipFile(fileobj=target, mode='wb', mtime=0, compresslevel=6) as stream:
                shutil.copyfileobj(source, stream)
        manifest = dict(base_manifest)
        manifest.update(edition='Modernized with Google apps (locally assembled)', google_apps=True,
            system_raw_sha256=sha(image), public_upload_allowed=False,
            qualification='FILE_CONTENT_EQUIVALENT_TO_OWNER_TESTED_GOOGLE_EDITION_NOT_SEPARATELY_BOOT_TESTED')
        manifest['files'] = {name: {'bytes': (tmp / name).stat().st_size, 'sha256': sha(tmp / name)}
                             for name in ('boot.img', 'system.raw.img.gz')}
        with zipfile.ZipFile(rom) as base, zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as package:
            for item in base.infolist():
                if item.filename in ('boot.img', 'system.raw.img.gz', 'manifest.json'): continue
                package.writestr(item, base.read(item.filename))
            for name in ('boot.img', 'system.raw.img.gz'): package.write(tmp / name, name)
            package.writestr('manifest.json', json.dumps(manifest, indent=2) + '\n')
        verify(output)
        receipt = {'status': 'PASS_ALL_NATIVE_AND_GOOGLE_FILE_CONTENT_MATCHES_TESTED_PAYLOAD',
                   'files_checked': len(combined), 'symlinks_checked': len(actual_links),
                   'new_raw_sha256': manifest['system_raw_sha256'], 'archive_sha256': sha(output),
                   'note': 'Filesystem timestamps may change the raw-image hash; every payload byte is checked.'}
        output.with_suffix(output.suffix + '.verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--gapps', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.rom, args.gapps, args.output)
