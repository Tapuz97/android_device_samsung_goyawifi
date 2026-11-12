"""Enter existing TWRP only after the combined image has passed verification."""
from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).resolve().parents[1]
pair=json.loads((p/'artifacts/lineage20-rom-v24/rom-pair.json').read_text())
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
assert json.loads((p/'evidence/offline-v34/contents.json').read_text())['status']=='PASS'
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
    timeout_file=p/'evidence/offline-v34/screen-timeout-diagnostic.json'
    timeout_state=json.loads(timeout_file.read_text())
    current=run('settings get system screen_off_timeout').strip()
    if current==str(timeout_state['temporary_ms']):
        run('settings put system screen_off_timeout '+str(timeout_state['original_ms']))
        timeout_state['restored_ms']=timeout_state['original_ms']
    else:
        timeout_state['left_user_changed_value']=current
    timeout_state['restore_required']=False
    timeout_file.write_text(json.dumps(timeout_state,indent=2)+'\n')
    # Test the ROM's embedded APK next, not the temporary successful app update.
    receipt=run('pm uninstall-system-updates com.android.launcher3',timeout=120,check=False)
    assert 'Success' in receipt,receipt
    path=run('pm path com.android.launcher3').strip()
    assert path=='package:/system/system_ext/priv-app/TrebuchetQuickStep/TrebuchetQuickStep.apk',path
    (p/'evidence/offline-v34/launcher-candidate/update-removed-before-rom.json').write_text(
        json.dumps(dict(receipt=receipt,path=path),indent=2)+'\n')
    try:run(helper,check=False)
    except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+100
while time.monotonic()<deadline:
    try:
        state=run('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',timeout=8,check=False)
        if state.strip()==identity:
            print('TWRP_READY_FOR_V24',flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(3)
else:raise RuntimeError('Recovery did not enumerate; do not start another boot.')
