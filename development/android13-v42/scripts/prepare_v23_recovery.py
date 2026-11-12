"""Enter existing TWRP only after the combined image has passed verification."""
from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).resolve().parents[1]
pair=json.loads((p/'artifacts/lineage20-rom-v23/rom-pair.json').read_text())
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
assert json.loads((p/'evidence/offline-v33/contents.json').read_text())['status']=='PASS'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def run(command,timeout=20,check=True):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(r.stdout,r.stderr)
    return r.stdout.decode(errors='replace')
identity='1101003030384745T110_ADB_SERIAL'
assert run('id -u; cat /sys/block/mmcblk0/device/cid').split()==['0',identity]
if run('test -x /sbin/recovery && echo RECOVERY',check=False).strip()!='RECOVERY':
    assert run('test -f /init.t110-core.rc && echo ANDROID').strip()=='ANDROID'
    helper='/data/local/tmp/t110_full_return_to_recovery'
    assert run('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
    try:run(helper,check=False)
    except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+100
while time.monotonic()<deadline:
    try:
        state=run('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',timeout=8,check=False)
        if state.strip()==identity:
            print('TWRP_READY_FOR_V23',flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(3)
else:raise RuntimeError('Recovery did not enumerate; do not start another boot.')
