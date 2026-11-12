"""Preserve this interrupted boot's recovery evidence; do not reboot or flash."""
from pathlib import Path
import datetime,json,os,re,subprocess,time
p=Path(__file__).resolve().parents[1];root=p/'evidence/offline-v41';e=root/'recovery-after-codec'
e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=40):return subprocess.run(adb+args,capture_output=True,timeout=timeout)
def sh(cmd,timeout=40):return call(['shell',cmd],timeout)
end=time.monotonic()+180
while time.monotonic()<end:
    try:
        r=sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',5)
        if r.stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL':break
    except subprocess.TimeoutExpired:pass
    time.sleep(3)
else:print('RECOVERY_NOT_CONNECTED_NO_CHANGES');raise SystemExit(2)
def save(name,cmd,timeout=50):
    r=sh(cmd,timeout);f=e/name
    if f.exists() and f.stat().st_size:
        assert not r.stdout or f.read_bytes()==r.stdout,'Do not replace preserved evidence: '+name
    else:f.write_bytes(r.stdout)
    (e/(name+'.stderr')).write_bytes(r.stderr)
    print(name,r.returncode,len(r.stdout),flush=True);return r
# The previous kernel ring buffer is most vulnerable to another reboot.
save('last-kmsg.txt','cat /proc/last_kmsg',70)
save('recovery-state.txt','cat /proc/sys/kernel/random/boot_id; cat /proc/uptime; cat /proc/mounts; cat /sys/block/mmcblk0/device/cid; id')
save('recovery-dmesg.txt','dmesg')
if sh('test -d /data/local/tmp/t110-rom-data && echo MOUNTED').stdout.strip()!=b'MOUNTED':
    save('data-mount.txt','mount /data; cat /proc/mounts')
assert sh('test -d /data/local/tmp/t110-rom-data && echo MOUNTED').stdout.strip()==b'MOUNTED'
data='/data/local/tmp/t110-rom-data'
save('codec-report.json','cat '+data+'/data/dev.tapuz.t110.audit/files/report.json')
save('persistent-log-list.txt','ls -l /data/local/tmp/t110-bootlogs; ls -l '+data+'/local/tmp/t110-logcat.txt*')
bootnames=sh('ls /data/local/tmp/t110-bootlogs').stdout.decode().splitlines()
bootnames=sorted(n for n in bootnames if re.fullmatch(r'boot-\d{4}',n))
for boot in bootnames[-3:]:
    for name in ['checkpoints.txt','logger-status.txt','kernel-0.txt','kernel-1.txt']:
        save(boot+'-'+name,'cat /data/local/tmp/t110-bootlogs/'+boot+'/'+name)
for suffix in ['','.1','.2']:
    save('android-logcat.txt'+suffix,'cat '+data+'/local/tmp/t110-logcat.txt'+suffix,70)
anrs=sh('ls '+data+'/anr').stdout.decode().splitlines()
for name in anrs:
    if re.fullmatch(r'anr_2026-11-10-19-41-\d{2}-\d{3}',name):save(name,'cat '+data+'/anr/'+name,70)
save('partition-hashes.txt','sha256sum /dev/block/mmcblk0p10 /dev/block/mmcblk0p9',90)
save('saved-tombstone-list.txt','ls -l '+data+'/tombstones')
(e/'capture.json').write_text(json.dumps({'captured_at':datetime.datetime.now().astimezone().isoformat(),'state':'TWRP','reboot_requested':False,'firmware_written':False,'data_mount_requested':(e/'data-mount.txt').exists(),'persistent_boots':bootnames[-3:]},indent=2)+'\n')
print('INTERRUPTED_BOOT_EVIDENCE_CAPTURED_RECOVERY_RETAINED',flush=True)
