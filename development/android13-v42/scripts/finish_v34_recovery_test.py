"""Record the native-menu recovery target and return the installed ROM to Android.

No images or partitions are written. Run only after selecting Recovery in System UI.
"""
from pathlib import Path
import datetime,json,os,subprocess,time

p=Path(__file__).resolve().parents[1]
out=p/'evidence/functional-followup-20261111/v34-recovery-target.json'
assert not out.exists(), 'Do not repeat this recorded target test'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=15):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('test -x /sbin/recovery && echo TWRP')=='TWRP'
assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]=='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
record=dict(status='NATIVE_RECOVERY_TARGET_PASS',host_time=datetime.datetime.now().astimezone().isoformat(),
            recovery_boot_id=sh('cat /proc/sys/kernel/random/boot_id'),recovery_uptime=sh('cat /proc/uptime'),
            entry_action_evidence='v34-recovery-target-action.txt',physical_system_written=False,
            partitions_written=False,return_to_android_requested=False)
def save():out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
save()
record['return_to_android_requested']=True;save()
started=time.monotonic()
try:sh('/sbin/reboot recovery_done',20)
except (AssertionError,subprocess.TimeoutExpired):pass
deadline=started+480
while time.monotonic()<deadline:
    time.sleep(5)
    try:
        if sh('getprop sys.boot_completed',8)=='1':
            assert sh('getprop ro.product.device')=='t110_bringup'
            record.update(return_status='ANDROID_BOOT_COMPLETED',android_boot_id=sh('cat /proc/sys/kernel/random/boot_id'),
                          system_server=sh('pidof system_server'),android_uptime=sh('cat /proc/uptime'),
                          seconds_to_android_completed=round(time.monotonic()-started,2))
            save();print(json.dumps(record,indent=2));break
    except (AssertionError,subprocess.TimeoutExpired):pass
else:
    record['return_status']='ANDROID_NOT_CONFIRMED_WITHIN_480_SECONDS';save()
    raise RuntimeError(record['return_status'])
