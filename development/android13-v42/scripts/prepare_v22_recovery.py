"""Remove the temporary setup update and enter existing TWRP for the verified ROM."""
from pathlib import Path
import hashlib,json,os,subprocess,time
p=Path(__file__).resolve().parents[1]
pair=json.loads((p/'artifacts/lineage20-rom-v22/rom-pair.json').read_text())
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
assert json.loads((p/'evidence/offline-v32/setup-candidate/installation.json').read_text())['visual_result']=='WELCOME_RENDERED_CORRECTLY'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def run(command,timeout=20,check=True):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(r.stdout,r.stderr)
    return r.stdout.decode(errors='replace')
assert run('test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid').strip()=='1101003030384745T110_ADB_SERIAL'
helper='/data/local/tmp/t110_full_return_to_recovery'
assert run('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
# This Android 13 shell implementation returns 1 after printing Success.
receipt=run('pm uninstall-system-updates org.lineageos.setupwizard',timeout=120,check=False)
assert 'Success' in receipt,receipt
path=run('pm path org.lineageos.setupwizard').strip()
assert path=='package:/system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk',path
(p/'evidence/offline-v32/setup-candidate/update-removed-before-rom.json').write_text(json.dumps(dict(receipt=receipt,path=path,reason='Verify next boot uses the corrected APK embedded in the ROM'),indent=2)+'\n')
print('TEMPORARY_APP_UPDATE_REMOVED_FOR_ROM_VALIDATION',flush=True)
try:run(helper,check=False)
except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+100
while time.monotonic()<deadline:
    try:
        state=run('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',timeout=8,check=False)
        if state.strip()=='1101003030384745T110_ADB_SERIAL':
            print('TWRP_READY_FOR_V22',flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(3)
else:raise RuntimeError('Recovery did not enumerate; physical help may be required. Do not start another boot.')
