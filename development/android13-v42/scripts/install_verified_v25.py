"""Install the checked image, keep the verified v28 BOOT, perform one full boot."""
from pathlib import Path
import json,os,subprocess,sys,time
p=Path(__file__).resolve().parents[1]
pair=json.loads((p/'artifacts/lineage20-rom-v25/rom-pair.json').read_text());assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
assert json.loads((p/'evidence/offline-v35/contents.json').read_text())['status']=='PASS'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def shell(command,timeout=25,check=True):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(r.stdout,r.stderr)
    return r.stdout.decode(errors='replace').strip()
cid='1101003030384745T110_ADB_SERIAL'
assert shell('id -u; cat /sys/block/mmcblk0/device/cid').split()==['0',cid]
assert shell('md5sum /dev/block/mmcblk0p10',90).split()[0]==pair['boot_md5']
assert shell('md5sum /dev/block/mmcblk0p9',90).split()[0]=='cd9793e1ee8f284c9056b225885b5b1a'
if shell('test -x /sbin/recovery && echo RECOVERY',check=False)!='RECOVERY':
    assert shell('test -f /init.t110-core.rc && echo ANDROID')=='ANDROID'
    assert shell('pm path com.android.launcher3')=='package:/system/system_ext/priv-app/TrebuchetQuickStep/TrebuchetQuickStep.apk'
    for package,app in [('com.android.systemui','SystemUI'),('org.lineageos.lineageparts','LineageParts'),('com.android.settings','Settings')]:
        assert shell('pm path '+package)==f'package:/system/system_ext/priv-app/{app}/{app}.apk'
    helper='/data/local/tmp/t110_full_return_to_recovery'
    assert shell('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
    try:shell(helper,check=False)
    except subprocess.TimeoutExpired:pass
    deadline=time.monotonic()+100
    while time.monotonic()<deadline:
        try:
            if shell('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',8,False)==cid:break
        except subprocess.TimeoutExpired:pass
        time.sleep(3)
    else:raise RuntimeError('Recovery has not enumerated; no flash or additional boot attempted')
subprocess.run([sys.executable,str(p/'scripts/stage_v25_system.py')],check=True)
subprocess.run([sys.executable,str(p/'scripts/run_core_boot_tablet.py'),str(p/'artifacts/android13-full-v28'),'--sha256',pair['boot_sha256'],'--full','--system-md5',pair['system_md5'],'--from-recovery','--expected-boot-md5',pair['boot_md5'],'--reuse-boot','--stability-seconds','180'],check=True)
