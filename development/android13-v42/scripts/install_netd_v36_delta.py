"""Apply the verified reversible netd delta to the unmounted userdata loop file."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/netd-event';record_path=e/'v36-installation.json';assert not record_path.exists()
a=p/'artifacts/lineage20-rom-v36-gapps';host=json.loads((a/'host-verification.json').read_text())
old=p/'artifacts/lineage20-rom-v35-gapps';parent=json.loads((old/'host-verification.json').read_text())
def digest(file):
 with file.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert host['status']=='OFFLINE_VERIFIED_NOT_INSTALLED' and host['netd_tests_passed']==8
assert digest(a/'system.raw.img')==host['sha256'] and digest(old/'system.raw.img')==host['parent_sha256']==parent['sha256']
assert host['bootstrap_policy_sha256']==json.loads((p/'artifacts/android13-boot-v42/provenance.json').read_text())['bootstrap_policy_sha256']
ranges=host['delta_ranges'];end=0
for row in ranges:
 assert row['block']>=end and row['count']*4096==row['bytes'];end=row['block']+row['count'];assert end*4096<=host['bytes']
 for side in ('new','old'):
  file=a/'delta'/row[side+'_file'];assert file.stat().st_size==row['bytes'] and digest(file)==row[side+'_sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
 r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,r.stderr.decode(errors='replace')
 return r.stdout.decode(errors='replace').strip()
def sh(cmd,timeout=45,check=True):return call(['shell',cmd],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';boot='8b5dc0d14169d5cb6f898d2f0e978242ace8aaef621a90ac47515939c887c0ab';recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('cat /sys/block/mmcblk0/device/cid')==cid and sh('id -u')=='0'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==boot
previous=sh('cat /proc/sys/kernel/random/boot_id');assert previous=='5730f721-68a5-4035-9800-13a3f8a0a99d'
helper='/stage-data/local/tmp/t110-rom-data.pre-gapps/local/tmp/t110_full_return_to_recovery'
assert sh('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
record=dict(status='HOST_DELTA_VERIFIED',host_time=datetime.datetime.now().astimezone().isoformat(),system_sha256=host['sha256'],
 previous_system_sha256=parent['sha256'],boot_sha256=boot,boot_written=False,recovery_written=False,physical_system_written=False,
 data_preserved=True,old_pre_gapps_profile_preserved=True,delta_bytes=host['delta_bytes'],normal_boot_requests=0,previous_boot_id=previous)
def save():record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
save()
try:sh(helper,20,False)
except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+160
while time.monotonic()<deadline:
 time.sleep(3)
 try:
  if sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',8,False)==cid:break
 except subprocess.TimeoutExpired:pass
else:raise RuntimeError('Recovery not available; system file unchanged')
assert not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==boot and sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
target='/data/local/tmp/t110-rom-system.raw'
assert sh('test -f '+target+' && test ! -L '+target+' && readlink -f '+target)==target
assert sh("stat -t "+target+" | cut -d' ' -f2")==str(host['bytes'])=='2146435072'
assert sh('md5sum '+target,240).split()[0]==parent['md5']
assert sh('test -d /data/local/tmp/t110-rom-data && test -d /data/local/tmp/t110-rom-data.pre-gapps && echo PRESERVED')=='PRESERVED'
remote='/data/local/tmp/t110-v36-netd-delta';assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT';sh('mkdir '+remote)
for row in ranges:
 for side in ('new','old'):
  filename=row[side+'_file'];call(['push',a/'delta'/filename,remote+'/'+filename],90)
  assert sh('sha256sum '+remote+'/'+filename).split()[0]==row[side+'_sha256']
record['status']='FORWARD_AND_REVERSE_DELTA_STAGED_VERIFIED';save()
def apply(side):
 assert not sh('losetup -a')
 for row in ranges:sh(f'dd if={remote}/{row[side+"_file"]} of={target} bs=4096 seek={row["block"]} count={row["count"]} conv=notrunc',90)
 sh('sync',90)
try:
 apply('new');assert sh('md5sum '+target,240).split()[0]==host['md5']
 assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==boot and sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
except Exception:
 apply('old');assert sh('md5sum '+target,240).split()[0]==parent['md5']
 record['status']='DELTA_FAILED_OLD_IMAGE_RESTORED_RECOVERY_RETAINED';save();raise
record.update(status='V36_VERIFIED_BOOTING',normal_boot_requests=1,reverse_delta_retained=remote);save();started=time.monotonic()
print('NETD_DELTA_VERIFIED_STARTING_FULL_BOOT',flush=True)
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
while time.monotonic()-started<900:
 time.sleep(5)
 try:
  if sh('getprop sys.boot_completed',8,False)!='1':continue
  identity=sh('cat /sys/block/mmcblk0/device/cid',8,False);current=sh('cat /proc/sys/kernel/random/boot_id',8,False);server=sh('pidof system_server',8,False)
  if not identity or not current or not server or current==previous:continue
  assert identity==cid and sh('getprop debug.hwui.t110_window_gpu')=='false'
  record.update(status='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING',boot_id=current,system_server=server,
   seconds_to_boot_completed=round(time.monotonic()-started,2),safe_gpu_flag='false')
  save();print(json.dumps(record,indent=2));break
 except subprocess.TimeoutExpired:pass
else:record['status']='BOOT_NOT_CONFIRMED';save();raise RuntimeError(record['status'])
