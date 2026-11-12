"""Record the v33 normal-Android recovery result, then restore normal Android.

This does not install or alter any image, profile, or partition.
"""
from pathlib import Path
import datetime,json,os,subprocess,time
p=Path(__file__).resolve().parents[1]
e=p/'evidence/offline-v41/gapps-v33-test'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']

def call(args,timeout=45,check=True):
    r=subprocess.run(adb+args,capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(r.stdout[-1000:],r.stderr[-1000:])
    return r.stdout.decode(errors='replace').strip()
def sh(s,timeout=45,check=True):return call(['shell',s],timeout,check)

assert sh('test -x /sbin/recovery && echo TWRP')=='TWRP'
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
installed=json.loads((e/'installation.json').read_text())
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==installed['boot_sha256']
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==installed['recovery_sha256']
recovery_boot=sh('cat /proc/sys/kernel/random/boot_id')
assert recovery_boot!=installed['boot_id']
call(['pull','/proc/last_kmsg',str(e/'normal-recovery-last-kmsg.txt')])
kmsg=(e/'normal-recovery-last-kmsg.txt').read_text(errors='replace')
assert 'reboot_target: recovery' in kmsg
assert 'Device will enter recovery mode on next booting' in kmsg
advanced=json.loads((e/'advanced-restart.json').read_text())
advanced.update(status='NORMAL_ANDROID_RECOVERY_BACKEND_PASS_MENU_PHYSICAL_PENDING',
                recovery_boot_id=recovery_boot,recovery_image_unchanged=True,
                kernel_recovery_target_confirmed=True)
(e/'advanced-restart.json').write_text(json.dumps(advanced,indent=2)+'\n')
record=dict(status='RESTORING_NORMAL_ANDROID_AFTER_RECOVERY_TEST',
            started_host_time=datetime.datetime.now().astimezone().isoformat(),
            recovery_boot_id=recovery_boot,additional_installs=0,
            additional_normal_boot_requests=1)
def save():(e/'restoration.json').write_text(json.dumps(record,indent=2)+'\n')
save();started=time.monotonic()
print('NORMAL_ANDROID_RECOVERY_BACKEND_PASS_RESTORING_ANDROID',flush=True)
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
while time.monotonic()-started<900:
    try:
        if sh('getprop sys.boot_completed',8,False)=='1':
            current=sh('cat /proc/sys/kernel/random/boot_id')
            assert current not in (installed['boot_id'],recovery_boot)
            record.update(status='ANDROID_RESTORED_AFTER_RECOVERY_TEST',boot_id=current,
                          system_server=sh('pidof system_server'),uptime=sh('cat /proc/uptime'),
                          seconds_to_boot_completed=round(time.monotonic()-started,2),
                          user_unlocked='RUNNING_UNLOCKED' in sh('dumpsys user'),
                          selinux=sh('getenforce'),
                          stay_on_while_plugged_in=sh('settings get global stay_on_while_plugged_in'),
                          wlan0_present=sh('test -d /sys/class/net/wlan0 && echo YES')=='YES',
                          board_recovery_property=sh('getprop ro.t110.reboot_without_misc'))
            save();assert record['stay_on_while_plugged_in']=='0'
            print(json.dumps(record,indent=2),flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(4)
else:
    record['status']='ANDROID_RESTORATION_BOOT_TIMEOUT';save()
    raise RuntimeError('Capture logs; do not repeat a boot')
