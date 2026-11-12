"""Install checked bootstrap namespace correction, retaining exact BOOT45 rollback."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';receipt=e/'boot46-installation.json';assert not receipt.exists()
candidate=p/'artifacts/android13-boot-v46/KERNEL.img';meta=json.loads((candidate.parent/'provenance.json').read_text())
previous=json.loads((e/'v40-installation.json').read_text());system=json.loads((p/'artifacts/lineage20-rom-v40-gapps/host-verification.json').read_text())
old_boot='2ca5248c7bc8bf814421cb6d4c6e7c060429a621b66141e5fd4afdbec4b905fa'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(candidate)==meta['full_boot_sha256'] and candidate.stat().st_size==16777216
rollback=p/'artifacts/android13-boot-v45/KERNEL.img';assert sha(rollback)==old_boot
assert meta['kernel_unchanged_from_boot45'] and meta['paired_system_sha256']==system['sha256']==previous['system_sha256']
assert json.loads((e/'canonical-root-regressions.json').read_text())['status']=='PASS'
assert meta['bootstrap_policy_sha256']==system['bootstrap_policy_sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    return r.stdout.decode(errors='replace').strip()
def sh(command,timeout=45,check=True):return call(['shell',command],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('cat /sys/block/mmcblk0/device/cid')==cid and sh('id -u')=='0'
assert sh('cat /proc/sys/kernel/random/boot_id')==previous['boot_id']
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot
helper='/stage-data/local/tmp/t110-rom-data.pre-gapps/local/tmp/t110_full_return_to_recovery'
assert sh('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
state=dict(status='BOOT46_OFFLINE_AND_DEVICE_IDENTITY_VERIFIED',time=datetime.datetime.now().astimezone().isoformat(),previous_boot_id=previous['boot_id'],
           system_sha256=system['sha256'],boot_sha256=meta['full_boot_sha256'],previous_boot_sha256=old_boot,
           recovery_written=False,physical_system_written=False,system_image_written=False,data_profiles_preserved=True,normal_boot_requests=0,ui_fixed=False)
def save():receipt.write_text(json.dumps(state,indent=2)+'\n');print(state['status'],flush=True)
save()
try:sh(helper,20,False)
except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+160
while time.monotonic()<deadline:
    time.sleep(3)
    try:
        if sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',8,False)==cid:break
    except subprocess.TimeoutExpired:pass
else:state['status']='RECOVERY_UNAVAILABLE_NO_BOOT_WRITE';save();raise RuntimeError(state['status'])
assert not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot and sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
assert sh('md5sum /data/local/tmp/t110-rom-system.raw',240).split()[0]==system['md5']
assert sh('test -d /data/local/tmp/t110-rom-data && test -d /data/local/tmp/t110-rom-data.pre-gapps && echo PRESERVED')=='PRESERVED'
remote='/data/local/tmp/t110-boot46-canonical-roots';assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT';sh('mkdir '+remote)
for name,file,digest in [('boot46.img',candidate,meta['full_boot_sha256']),('rollback45.img',rollback,old_boot)]:
    call(['push',file,remote+'/'+name],90);assert sh('sha256sum '+remote+'/'+name).split()[0]==digest
try:
    sh('dd if='+remote+'/boot46.img of=/dev/block/mmcblk0p10 bs=4096',90);sh('sync',90)
    assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==meta['full_boot_sha256']
    assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
except Exception:
    sh('dd if='+remote+'/rollback45.img of=/dev/block/mmcblk0p10 bs=4096',90);sh('sync',90)
    assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot
    state['status']='BOOT45_RESTORED_RECOVERY_RETAINED';save();raise
state.update(status='BOOT46_VERIFIED_STARTING_ONE_FULL_BOOT',boot_written=True,reverse_boot_retained=remote+'/rollback45.img',normal_boot_requests=1);save();started=time.monotonic()
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
while time.monotonic()-started<900:
    time.sleep(5)
    try:
        if sh('getprop sys.boot_completed',8,False)!='1':continue
        current=sh('cat /proc/sys/kernel/random/boot_id',8,False)
        if not current or current==previous['boot_id']:continue
        assert sh('cat /sys/block/mmcblk0/device/cid')==cid and sh('getprop debug.hwui.t110_window_gpu')=='false'
        assert sh('test -d /system_ext && test ! -L /system_ext && test -d /product && test ! -L /product && echo REAL_ROOTS')=='REAL_ROOTS'
        state.update(status='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING',boot_id=current,system_server=sh('pidof system_server'),
                     seconds_to_boot_completed=round(time.monotonic()-started,2),selinux=sh('getenforce'))
        save();break
    except subprocess.TimeoutExpired:pass
else:state['status']='BOOT_NOT_CONFIRMED';save();raise RuntimeError(state['status'])
