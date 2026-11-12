"""Stage the verified v12 image in TWRP, without flashing or rebooting."""
from pathlib import Path
import json,os,subprocess
project=Path(__file__).resolve().parents[1]
adb=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'
serial='T110_ADB_SERIAL'
report=json.loads((project/'artifacts/lineage20-rom-v12/host-verification.json').read_text())
assert report['status']=='VERIFIED' and report['md5']=='abb0bf7da166b76157831c5174bb0fe9'
def run(*args,timeout=30):
    r=subprocess.run([str(adb),'-s',serial,*map(str,args)],check=True,capture_output=True,
                     text=True,errors='replace',timeout=timeout)
    print(r.stdout+r.stderr,flush=True)
    return r.stdout
guard='''set -e
[ "$(id -u)" = 0 ]
[ -x /sbin/recovery ]
[ "$(cat /sys/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL ]
[ ! -e /data/local/tmp/t110-rom-system-v12.incoming ]
[ ! -L /data/local/tmp/t110-rom-system.raw ]
[ -z "$(losetup -a)" ]
echo STAGING_GUARDS_PASS
'''
assert 'STAGING_GUARDS_PASS' in run('shell',guard)
space=[line.split() for line in run('shell','df /data').splitlines() if '/data' in line][-1]
percent=next(i for i,value in enumerate(space) if value.endswith('%'))
assert int(space[percent-1])>1630000,space
incoming='/data/local/tmp/t110-rom-system-v12.incoming'
run('push',project/'artifacts/lineage20-rom-v12/system.raw.img',incoming,timeout=420)
actual=run('shell','md5sum '+incoming,timeout=150).split()[0]
assert actual==report['md5'],actual
run('shell','''set -e
[ -x /sbin/recovery ]
[ -z "$(losetup -a)" ]
[ ! -L /data/local/tmp/t110-rom-system.raw ]
mv /data/local/tmp/t110-rom-system-v12.incoming /data/local/tmp/t110-rom-system.raw
sync
ls -l /data/local/tmp/t110-rom-system.raw
''',timeout=60)
(project/'evidence/v12-tablet-stage.json').write_text(json.dumps(dict(
    status='STAGED_VERIFIED_NO_BOOT',system_md5=actual,system_sha256=report['sha256'],
    installed_boot_md5='a1335e4d918a722a024dcb9be2744d89',
    tablet_state='TWRP',hardware_boots_this_pass=0),indent=2)+'\n')
