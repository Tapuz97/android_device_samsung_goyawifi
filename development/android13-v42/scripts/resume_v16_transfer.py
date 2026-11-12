"""Transfer v16 in compressed chunks, verifying any retained prefix first."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

project = Path(__file__).resolve().parents[1]
adb = Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk/platform-tools/adb.exe'
serial = 'T110_ADB_SERIAL'
incoming = '/data/local/tmp/t110-rom-system-v16.incoming'
chunk_remote = '/data/local/tmp/t110-rom-v16-tail.chunk'
source = project / 'artifacts/lineage20-rom-v16/system.raw.img'
report = json.loads((source.parent / 'host-verification.json').read_text())

def run(*args, timeout=45):
    result = subprocess.run([str(adb), '-s', serial, *map(str, args)],
                            capture_output=True, text=True, errors='replace',
                            timeout=timeout)
    if result.returncode:
        print(result.stdout + result.stderr, flush=True)
        result.check_returncode()
    return result.stdout

guard = '''set -e
[ "$(id -u)" = 0 ]
[ -x /sbin/recovery ]
[ "$(cat /sys/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL ]
[ "$(md5sum /dev/block/mmcblk0p10 | cut -d' ' -f1)" = 54325830bda64adfb02b3f1b204ea4de ]
[ "$(md5sum /dev/block/mmcblk0p9 | cut -d' ' -f1)" = cd9793e1ee8f284c9056b225885b5b1a ]
[ -z "$(losetup -a)" ]
[ ! -L /data/local/tmp/t110-rom-system.raw ]
[ ! -L /data/local/tmp/t110-rom-system-v16.incoming ]
[ ! -e /data/local/tmp/t110-rom-v16-tail.chunk ]
echo GUARDS_PASS
'''
assert 'GUARDS_PASS' in run('shell', guard)
with source.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == report['sha256'] == 'a37faa553bf9827d77293e4935350ba49fc6f9e78747979ab4691a7db20d7607'
size_command = f"stat -t {incoming} | cut -d' ' -f2"
if run('shell', f'test -f {incoming} && echo EXISTS').strip() != 'EXISTS':
    run('shell', f'test ! -e {incoming} && : > {incoming}')
offset = int(run('shell', size_command).strip())
assert 0 <= offset <= source.stat().st_size
prefix = hashlib.md5()
with source.open('rb') as stream:
    remaining = offset
    while remaining:
        block = stream.read(min(8 * 1024 * 1024, remaining))
        assert block
        prefix.update(block)
        remaining -= len(block)
assert run('shell', f'md5sum {incoming}', timeout=180).split()[0] == prefix.hexdigest()
assert int(run('shell', size_command).strip()) == offset
print(f'VERIFIED_EXISTING_PREFIX {offset}/{source.stat().st_size}', flush=True)
with tempfile.TemporaryDirectory(prefix='t110-v16-') as scratch, source.open('rb') as stream:
    stream.seek(offset)
    while block := stream.read(32 * 1024 * 1024):
        local = Path(scratch) / 'tail.chunk'
        compressed = gzip.compress(block, compresslevel=1, mtime=0)
        local.write_bytes(compressed)
        run('push', local, chunk_remote, timeout=180)
        digest = hashlib.md5(compressed).hexdigest()
        command = f'''set -e
[ -x /sbin/recovery ]
[ -z "$(losetup -a)" ]
[ "$({size_command})" = {offset} ]
[ "$(md5sum {chunk_remote} | cut -d' ' -f1)" = {digest} ]
gzip -dc {chunk_remote} >> {incoming}
[ "$({size_command})" = {offset + len(block)} ]
rm {chunk_remote}
echo CHUNK_PASS
'''
        assert 'CHUNK_PASS' in run('shell', command)
        offset += len(block)
        print(f'TRANSFER {offset}/{source.stat().st_size}', flush=True)
actual = run('shell', f'md5sum {incoming}', timeout=180).split()[0]
assert actual == report['md5'] == '4c4c6f665218d1f471303e052d295517'
assert 'GUARDS_PASS' in run('shell', guard)
run('shell', f'mv {incoming} /data/local/tmp/t110-rom-system.raw && sync', timeout=90)
(project / 'evidence/v16-tablet-stage.json').write_text(json.dumps({
    'status': 'STAGED_VERIFIED_NO_BOOT', 'system_md5': actual,
    'system_sha256': report['sha256'], 'compressed_chunk_transfer': True,
    'installed_boot_md5': '54325830bda64adfb02b3f1b204ea4de',
    'tablet_state': 'TWRP', 'hardware_boots_this_pass': 0,
}, indent=2) + '\n')
print('STAGED_VERIFIED_NO_BOOT', flush=True)
