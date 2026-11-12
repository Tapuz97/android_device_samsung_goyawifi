"""Stage the verified v25 image in TWRP using resumable compressed chunks."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

project=Path(__file__).resolve().parents[1]
adb=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'
serial='T110_ADB_SERIAL'
incoming='/data/local/tmp/t110-rom-system-v25.incoming'
chunk_remote='/data/local/tmp/t110-rom-v25-tail.chunk'
source=project/'artifacts/lineage20-rom-v25/system.raw.img'
report=json.loads((source.parent/'host-verification.json').read_text())
pair=json.loads((source.parent/'rom-pair.json').read_text())
assert report['status']=='VERIFIED'
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
assert pair['system_sha256']==report['sha256'] and pair['system_md5']==report['md5']
assert json.loads((project/'evidence/offline-v35/contents.json').read_text())['status']=='PASS'
boot_check=json.loads((project/'evidence/offline-v34/boot-verification.json').read_text())
assert boot_check['status']=='PASS' and boot_check['boot_sha256']==pair['boot_sha256']
chunk_size=16*1024*1024

def run(*args,timeout=45):
    result=subprocess.run([str(adb),'-s',serial,*map(str,args)],capture_output=True,
                          text=True,errors='replace',timeout=timeout)
    if result.returncode:
        print(result.stdout+result.stderr,flush=True)
        result.check_returncode()
    return result.stdout

guard='''set -e
[ "$(id -u)" = 0 ]
[ -x /sbin/recovery ]
[ "$(cat /sys/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL ]
[ "$(md5sum /dev/block/mmcblk0p10 | cut -d' ' -f1)" = 9c5b938f9ee286c08dec6eed9c4f9493 ]
[ "$(md5sum /dev/block/mmcblk0p9 | cut -d' ' -f1)" = cd9793e1ee8f284c9056b225885b5b1a ]
[ -z "$(losetup -a)" ]
[ ! -L /data/local/tmp/t110-rom-system.raw ]
[ ! -L /data/local/tmp/t110-rom-system-v25.incoming ]
[ ! -e /data/local/tmp/t110-rom-v25-tail.chunk ]
echo GUARDS_PASS
'''
assert 'GUARDS_PASS' in run('shell',guard)
with source.open('rb') as stream:
    assert hashlib.file_digest(stream,'sha256').hexdigest()==report['sha256']
assert source.stat().st_size==1594884096
size_command=f"stat -t {incoming} | cut -d' ' -f2"
if run('shell',f'test -f {incoming} && echo EXISTS').strip()!='EXISTS':
    assert 'CREATED' in run('shell',f'test ! -e {incoming} && : > {incoming} && echo CREATED')
offset=int(run('shell',size_command).strip())
assert 0<=offset<=source.stat().st_size
space=[line.split() for line in run('shell','df /data').splitlines() if '/data' in line][-1]
percent=next(i for i,value in enumerate(space) if value.endswith('%'))
assert int(space[percent-1])*1024 > source.stat().st_size-offset+chunk_size+16*1024*1024,space
prefix=hashlib.md5()
with source.open('rb') as stream:
    remaining=offset
    while remaining:
        block=stream.read(min(8*1024*1024,remaining))
        assert block
        prefix.update(block)
        remaining-=len(block)
assert run('shell',f'md5sum {incoming}',timeout=180).split()[0]==prefix.hexdigest()
assert int(run('shell',size_command).strip())==offset
print(f'VERIFIED_PREFIX {offset}/{source.stat().st_size}',flush=True)
with tempfile.TemporaryDirectory(prefix='t110-v25-') as scratch,source.open('rb') as stream:
    stream.seek(offset)
    while block:=stream.read(chunk_size):
        local=Path(scratch)/'tail.chunk'
        compressed=gzip.compress(block,compresslevel=1,mtime=0)
        local.write_bytes(compressed)
        run('push',local,chunk_remote,timeout=240)
        digest=hashlib.md5(compressed).hexdigest()
        command=f'''set -e
[ -x /sbin/recovery ]
[ -z "$(losetup -a)" ]
[ "$({size_command})" = {offset} ]
[ "$(md5sum {chunk_remote} | cut -d' ' -f1)" = {digest} ]
gzip -dc {chunk_remote} >> {incoming}
[ "$({size_command})" = {offset+len(block)} ]
rm {chunk_remote}
echo CHUNK_PASS
'''
        assert 'CHUNK_PASS' in run('shell',command,timeout=90)
        offset+=len(block)
        print(f'TRANSFER {offset}/{source.stat().st_size}',flush=True)
actual=run('shell',f'md5sum {incoming}',timeout=180).split()[0]
assert actual==report['md5']
assert 'GUARDS_PASS' in run('shell',guard)
assert 'STAGED_AND_SYNCED' in run('shell',f'mv {incoming} /data/local/tmp/t110-rom-system.raw && sync && echo STAGED_AND_SYNCED',timeout=90)
(project/'evidence/v25-tablet-stage.json').write_text(json.dumps(dict(
    status='STAGED_VERIFIED_NO_BOOT',system_md5=actual,system_sha256=report['sha256'],
    compressed_chunk_transfer=True,installed_boot_md5='9c5b938f9ee286c08dec6eed9c4f9493',
    tablet_state='TWRP',hardware_boots_this_pass=0),indent=2)+'\n')
print('STAGED_VERIFIED_NO_BOOT',flush=True)
