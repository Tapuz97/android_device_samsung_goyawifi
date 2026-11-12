"""Install the two verified board startup corrections; keep the v37 system unchanged."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';out=e/'boot44-installation.json';assert not out.exists()
old=json.loads((e/'v37-installation.json').read_text());boot=p/'artifacts/android13-boot-v44/KERNEL.img';meta=json.loads((boot.parent/'provenance.json').read_text())
sha=lambda data:hashlib.sha256(data).hexdigest();digest=sha(boot.read_bytes());assert digest==meta['full_boot_sha256'] and boot.stat().st_size==16777216
assert meta['kernel_unchanged_from_boot43'] and meta['paired_system_sha256']==old['system_sha256'] and not meta['system_payload_changed']
wsl='T110Build';linux='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
r=subprocess.run(['wsl.exe','-d',wsl,'--','/root/t110-build/out-system/host/linux-x86/bin/host_init_verifier',linux+'/evidence/hardware-bt-sd/boot44-init.mrvl.rc'],capture_output=True,timeout=90)
(e/'boot44-init-verifier.txt').write_bytes(r.stdout+r.stderr);assert r.returncode==0
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
 r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
 return r.stdout.decode(errors='replace').strip()
def sh(command,timeout=45,check=True):return call(['shell',command],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('id -u')=='0' and sh('cat /sys/block/mmcblk0/device/cid')==cid
assert sh('cat /proc/sys/kernel/random/boot_id')==old['boot_id'] and sh('getprop sys.boot_completed')=='1'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old['boot_sha256']
assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
rollback='/stage-data/local/tmp/t110-v37-bt-sd-delta/boot43.img'
assert sh('test -f '+rollback+' && test ! -L '+rollback+' && sha256sum '+rollback).split()[0]==old['boot_sha256']
text=sh('env LD_LIBRARY_PATH=/vendor/lib/hw /system/bin/linker --list /vendor/bin/hw/android.hardware.bluetooth@1.1-service')
(e/'boot44-library-resolution.txt').write_text(text+'\n');assert 'android.hardware.bluetooth@1.0-impl.so => /system/vendor/lib/hw/' in text and 'not found' not in text
remote='/data/local/tmp/t110-bt-boot44.img';assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT'
state=dict(status='INIT_SYNTAX_AND_LIBRARY_RESOLUTION_PASS',host_time=datetime.datetime.now().astimezone().isoformat(),previous_boot_id=old['boot_id'],
 system_sha256=old['system_sha256'],boot_sha256=digest,previous_boot_sha256=old['boot_sha256'],system_image_changed=False,recovery_written=False,
 physical_system_written=False,data_profiles_preserved=True,normal_boot_requests=0,init_verifier_exit=0,actual_hal_libraries_resolved=True,hal_main_executed_by_resolution_check=False)
def save():out.write_text(json.dumps(state,indent=2)+'\n');print(state['status'],flush=True)
save();call(['push',boot,remote],90);assert sh('sha256sum '+remote).split()[0]==digest
try:
 sh('dd if='+remote+' of=/dev/block/mmcblk0p10 bs=4096 count=4096 conv=fsync',90)
 assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==digest
 assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
except Exception:
 sh('dd if='+rollback+' of=/dev/block/mmcblk0p10 bs=4096 count=4096 conv=fsync',90)
 assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old['boot_sha256']
 state['status']='BOOT43_RESTORED_NO_REBOOT';save();raise
state.update(status='BOOT44_VERIFIED_BOOTING',normal_boot_requests=1);save();started=time.monotonic()
try:call(['reboot'],20,False)
except subprocess.TimeoutExpired:pass
while time.monotonic()-started<900:
 time.sleep(5)
 try:
  if sh('getprop sys.boot_completed',8,False)!='1':continue
  identity=sh('cat /sys/block/mmcblk0/device/cid',8,False);current=sh('cat /proc/sys/kernel/random/boot_id',8,False)
  if not identity or not current or current==old['boot_id']:continue
  assert identity==cid and sh('getprop debug.hwui.t110_window_gpu')=='false' and sh('getenforce')=='Enforcing'
  state.update(status='ANDROID_BOOT_COMPLETED_NATIVE_QUALIFICATION_PENDING',boot_id=current,system_server=sh('pidof system_server'),
   seconds_to_boot_completed=round(time.monotonic()-started,2),selinux='Enforcing')
  save();print(json.dumps(state,indent=2));break
 except subprocess.TimeoutExpired:pass
else:state['status']='BOOT_NOT_CONFIRMED';save();raise RuntimeError(state['status'])
