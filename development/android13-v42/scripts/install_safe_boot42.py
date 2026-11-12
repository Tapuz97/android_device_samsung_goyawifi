"""Install only the verified safe rendering default; retain v35 and Wi-Fi kernel."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';path=e/'boot42-installation.json';assert not path.exists()
boot=p/'artifacts/android13-boot-v42/KERNEL.img';metadata=json.loads((boot.parent/'provenance.json').read_text())
digest=hashlib.sha256(boot.read_bytes()).hexdigest();assert digest==metadata['full_boot_sha256'] and boot.stat().st_size==16777216
assert metadata['ramdisk_changed_files']==['init.mrvl.rc']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
 r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,r.stderr.decode(errors='replace')
 return r.stdout.decode(errors='replace').strip()
def sh(command,timeout=45,check=True):return call(['shell',command],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';parent='6d2930f8b48b45d82a8ff580cf64940eca002950d95673684d1984e9f1cbd8e4'
recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('id -u')=='0' and sh('cat /sys/block/mmcblk0/device/cid')==cid
previous=sh('cat /proc/sys/kernel/random/boot_id');assert previous=='8644e9ae-31e3-4e1a-a62f-1e0d58cdc01e'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==parent
assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
assert sh('getprop debug.hwui.t110_window_gpu')=='false'
# Retain the system_server dump requested just before this guarded restart.
for filename in sh('ls -t /data/anr').splitlines()[:6]:
 assert re.fullmatch('[a-zA-Z0-9_.-]+',filename)
 content=sh('cat /data/anr/'+filename,60)
 if re.search(r'^----- pid 312\b',content,re.M) and 'Cmd line: system_server' in content:
  (e/'v35-live-threads'/('server-'+filename)).write_text(content+'\n',encoding='utf-8')
target='/data/local/tmp/t110-safe-boot42.img';assert sh('test ! -e '+target+' && test ! -L '+target+' && echo ABSENT')=='ABSENT'
record=dict(status='VERIFIED_BEFORE_BOOT_WRITE',host_time=datetime.datetime.now().astimezone().isoformat(),
 boot_sha256=digest,parent_boot_sha256=parent,system_image_changed=False,physical_system_written=False,recovery_written=False,
 previous_boot_id=previous,normal_boot_requests=0,reason='Use software windows by default; preserve working native Wi-Fi')
def save():path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
save();call(['push',boot,target],60);assert sh('sha256sum '+target).split()[0]==digest
sh('dd if='+target+' of=/dev/block/mmcblk0p10 bs=4096 count=4096 conv=fsync',90)
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==digest
assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
record.update(status='SAFE_BOOT_VERIFIED_RESTARTING',normal_boot_requests=1);save();started=time.monotonic();call(['reboot'],20,False)
while time.monotonic()-started<600:
 time.sleep(5)
 try:
  if sh('getprop sys.boot_completed',8,False)!='1':continue
  identity=sh('cat /sys/block/mmcblk0/device/cid',8,False);current=sh('cat /proc/sys/kernel/random/boot_id',8,False)
  if not identity or not current or current==previous:continue
  assert identity==cid
  assert sh('getprop debug.hwui.t110_window_gpu')=='false'
  assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==digest
  record.update(status='ANDROID_BOOT_COMPLETED_SAFE_DEFAULT_VERIFIED',boot_id=current,system_server=sh('pidof system_server'),
   seconds_to_boot_completed=round(time.monotonic()-started,2),enforcing=sh('getenforce'),safe_gpu_flag=sh('getprop debug.hwui.t110_window_gpu'))
  save();print(json.dumps(record,indent=2));break
 except subprocess.TimeoutExpired:pass
else:
 record['status']='BOOT_COMPLETION_NOT_CONFIRMED';save();raise RuntimeError(record['status'])
