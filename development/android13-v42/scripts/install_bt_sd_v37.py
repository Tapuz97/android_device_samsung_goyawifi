"""Install the verified BT/SD delta and matching policy boot, retaining rollback."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';receipt=e/'v37-installation.json';assert not receipt.exists()
a=p/'artifacts/lineage20-rom-v37-gapps';host=json.loads((a/'host-verification.json').read_text());parent=p/'artifacts/lineage20-rom-v36-gapps';old=json.loads((parent/'host-verification.json').read_text())
boot=p/'artifacts/android13-boot-v43/KERNEL.img';boot_meta=json.loads((boot.parent/'provenance.json').read_text());rollback=p/'artifacts/android13-boot-v42/KERNEL.img'
def sha(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert host['status']=='OFFLINE_VERIFIED_NOT_INSTALLED' and sha(a/'system.raw.img')==host['sha256']
assert sha(parent/'system.raw.img')==host['parent_sha256']==old['sha256']
old_boot='8b5dc0d14169d5cb6f898d2f0e978242ace8aaef621a90ac47515939c887c0ab';assert sha(rollback)==old_boot
assert sha(boot)==boot_meta['full_boot_sha256'] and boot.stat().st_size==rollback.stat().st_size==16777216
assert boot_meta['bootstrap_policy_sha256']==host['bootstrap_policy_sha256'] and boot_meta['paired_system_sha256']==host['sha256']
assert boot_meta['kernel_unchanged_from_boot42'] and json.loads((e/'h4-unit-tests.json').read_text())['status']=='PASS'
ranges=host['delta_ranges'];end=0
for row in ranges:
 assert row['block']>=end and row['count']*4096==row['bytes'];end=row['block']+row['count'];assert end*4096<=host['bytes']
 for side in ['new','old']:
  f=a/'delta'/row[side+'_file'];assert f.stat().st_size==row['bytes'] and sha(f)==row[side+'_sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
 r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,r.stderr.decode(errors='replace')+r.stdout.decode(errors='replace')
 return r.stdout.decode(errors='replace').strip()
def sh(command,timeout=45,check=True):return call(['shell',command],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('cat /sys/block/mmcblk0/device/cid')==cid and sh('id -u')=='0'
previous=sh('cat /proc/sys/kernel/random/boot_id');assert previous==json.loads((e/'controller-probe-legacy.json').read_text())['boot_id']
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot
helper='/stage-data/local/tmp/t110-rom-data.pre-gapps/local/tmp/t110_full_return_to_recovery'
assert sh('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
state=dict(status='HOST_PAIR_VERIFIED',host_time=datetime.datetime.now().astimezone().isoformat(),previous_boot_id=previous,
 system_sha256=host['sha256'],boot_sha256=boot_meta['full_boot_sha256'],previous_system_sha256=old['sha256'],previous_boot_sha256=old_boot,
 recovery_written=False,physical_system_written=False,data_profiles_preserved=True,delta_bytes=host['delta_bytes'],normal_boot_requests=0)
def save():
 receipt.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
 print(state['status'],flush=True)
save()
try:sh(helper,20,False)
except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+160
while time.monotonic()<deadline:
 time.sleep(3)
 try:
  if sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',8,False)==cid:break
 except subprocess.TimeoutExpired:pass
else:state['status']='RECOVERY_UNAVAILABLE_NO_IMAGE_WRITE';save();raise RuntimeError(state['status'])
assert not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot and sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
target='/data/local/tmp/t110-rom-system.raw'
assert sh('test -f '+target+' && test ! -L '+target+' && readlink -f '+target)==target
assert sh("stat -t "+target+" | cut -d' ' -f2")==str(host['bytes'])=='2146435072'
assert sh('md5sum '+target,240).split()[0]==old['md5']
assert sh('test -d /data/local/tmp/t110-rom-data && test -d /data/local/tmp/t110-rom-data.pre-gapps && echo PRESERVED')=='PRESERVED'
available=int(sh('df -k /data').splitlines()[-1].split()[-3])*1024
assert available>2*host['delta_bytes']+2*16777216+64*1024*1024,(available,host['delta_bytes'])
remote='/data/local/tmp/t110-v37-bt-sd-delta';assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT';sh('mkdir '+remote)
for row in ranges:
 for side in ['new','old']:
  name=row[side+'_file'];call(['push',a/'delta'/name,remote+'/'+name],90)
  assert sh('sha256sum '+remote+'/'+name).split()[0]==row[side+'_sha256']
for f,name,expected in [(boot,'boot43.img',boot_meta['full_boot_sha256']),(rollback,'boot42-rollback.img',old_boot)]:
 call(['push',f,remote+'/'+name],90);assert sh('sha256sum '+remote+'/'+name).split()[0]==expected
state['status']='REVERSIBLE_PAIR_STAGED_VERIFIED';state['reverse_delta_retained']=remote;save()
def apply(side):
 assert not sh('losetup -a')
 for row in ranges:sh(f'dd if={remote}/{row[side+"_file"]} of={target} bs=4096 seek={row["block"]} count={row["count"]} conv=notrunc',90)
 sh('sync',90)
try:
 apply('new');assert sh('md5sum '+target,240).split()[0]==host['md5']
 sh(f'dd if={remote}/boot43.img of=/dev/block/mmcblk0p10 bs=4096 count=4096',90);sh('sync',90)
 assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==boot_meta['full_boot_sha256']
 assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
except Exception:
 state['status']='PAIR_VERIFICATION_FAILED_RESTORING_V36';save()
 apply('old');assert sh('md5sum '+target,240).split()[0]==old['md5']
 sh(f'dd if={remote}/boot42-rollback.img of=/dev/block/mmcblk0p10 bs=4096 count=4096',90);sh('sync',90)
 assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot
 state['status']='OLD_PAIR_RESTORED_RECOVERY_RETAINED';save();raise
state.update(status='V37_BOOT43_VERIFIED_BOOTING',normal_boot_requests=1);save();started=time.monotonic()
print('BT_SD_PAIR_VERIFIED_STARTING_FULL_BOOT',flush=True)
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
while time.monotonic()-started<900:
 time.sleep(5)
 try:
  if sh('getprop sys.boot_completed',8,False)!='1':continue
  current=sh('cat /proc/sys/kernel/random/boot_id',8,False);identity=sh('cat /sys/block/mmcblk0/device/cid',8,False);server=sh('pidof system_server',8,False)
  if not current or not identity or not server or current==previous:continue
  assert identity==cid and sh('getprop debug.hwui.t110_window_gpu')=='false'
  state.update(status='ANDROID_BOOT_COMPLETED_NATIVE_BLUETOOTH_QUALIFICATION_PENDING',boot_id=current,system_server=server,
   seconds_to_boot_completed=round(time.monotonic()-started,2),selinux=sh('getenforce'))
  save();print(json.dumps(state,indent=2));break
 except subprocess.TimeoutExpired:pass
else:state['status']='BOOT_NOT_CONFIRMED';save();raise RuntimeError(state['status'])
