"""Install the verified small image delta and matched BOOT, retaining all data."""
from pathlib import Path
import hashlib,json,os,subprocess,time,datetime
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41/gapps-v30-test';e.mkdir(exist_ok=True)
assert not(e/'installation.json').exists(),'No duplicate boot trials'
a=p/'artifacts/lineage20-rom-v30-gapps';host=json.loads((a/'host-verification.json').read_text())
old=p/'artifacts/lineage20-rom-v29-gapps';oldhost=json.loads((old/'host-verification.json').read_text())
boot=p/'artifacts/android13-boot-v34/KERNEL.img';prov=json.loads((boot.parent/'provenance.json').read_text())
oldboot=p/'artifacts/android13-boot-v33/KERNEL.img'
def digest(f,kind='sha256'):
    with f.open('rb') as stream:return hashlib.file_digest(stream,kind).hexdigest()
assert host['status']=='OFFLINE_VERIFIED_NOT_INSTALLED' and host['bytes']==2146435072
assert digest(a/'system.raw.img')==host['sha256'] and digest(old/'system.raw.img')==host['parent_sha256']==oldhost['sha256']
assert digest(boot)==prov['full_boot_sha256'] and prov['bootstrap_policy_sha256']==host['bootstrap_policy_sha256']
oldbootsha=digest(oldboot);assert oldbootsha=='49d950e636e78f9b1a91544b7b815941d9907975810d813175ca1cec68207796'
delta=host['delta_ranges'];end=0
for row in delta:
    assert row['block']>=end and row['count']*4096==row['bytes'];end=row['block']+row['count'];assert end*4096<=host['bytes']
    for side in ['new','old']:
        f=a/'delta'/row[side+'_file'];assert f.stat().st_size==row['bytes'] and digest(f)==row[side+'_sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(args,r.stdout[-1000:],r.stderr[-1000:])
    return r.stdout.decode(errors='replace').strip()
def sh(s,timeout=45,check=True):return call(['shell',s],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('cat /sys/block/mmcblk0/device/cid')==cid and sh('cat /proc/sys/kernel/random/boot_id')=='dd03b95b-3f7e-4a1e-8c27-84cd94056813'
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==oldbootsha
helper='/stage-data/local/tmp/t110-rom-data.pre-gapps/local/tmp/t110_full_return_to_recovery'
assert sh('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
record={'status':'HOST_PAIR_AND_DELTA_VERIFIED','host_time':datetime.datetime.now().astimezone().isoformat(),
 'system_sha256':host['sha256'],'boot_sha256':prov['full_boot_sha256'],'previous_system_sha256':oldhost['sha256'],'previous_boot_sha256':oldbootsha,
 'data_preserved':True,'old_pre_gapps_profile_preserved':True,'physical_system_written':False,'normal_boot_requests':0,'delta_bytes':host['delta_bytes']}
def save():(e/'installation.json').write_text(json.dumps(record,indent=2)+'\n')
save()
try:sh(helper,20,False)
except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+160
while time.monotonic()<deadline:
    try:
        if sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',8,False)==cid:break
    except subprocess.TimeoutExpired:pass
    time.sleep(3)
else:raise RuntimeError('Recovery not connected; no image update attempted')
assert not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==oldbootsha
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
target='/data/local/tmp/t110-rom-system.raw'
assert sh('test -f '+target+' && test ! -L '+target+' && readlink -f '+target)==target
assert sh("stat -t "+target+" | cut -d' ' -f2")=='2146435072'
assert sh('md5sum '+target,240).split()[0]==oldhost['md5']
assert sh('test -d /data/local/tmp/t110-rom-data.pre-gapps && echo PRESERVED')=='PRESERVED'
remote='/data/local/tmp/t110-v30-update';assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT'
sh('mkdir '+remote)
for row in delta:
    for side in ['new','old']:
        name=row[side+'_file'];call(['push',a/'delta'/name,remote+'/'+name],90)
        assert sh('sha256sum '+remote+'/'+name).split()[0]==row[side+'_sha256']
backup='/data/local/tmp/t110-boot-v33.rollback.img';incoming=remote+'/KERNEL.img'
assert sh('test ! -L '+backup+' && echo SAFE')=='SAFE'
sh('dd if=/dev/block/mmcblk0p10 of='+backup+' bs=4096 && sync',90)
assert sh('sha256sum '+backup).split()[0]==oldbootsha
call(['push',boot,incoming],90);assert sh('sha256sum '+incoming).split()[0]==prov['full_boot_sha256']
record['status']='DELTA_AND_ROLLBACK_STAGED_VERIFIED';save()
def apply(side):
    assert not sh('losetup -a')
    for row in delta:
        sh(f'dd if={remote}/{row[side+"_file"]} of={target} bs=4096 seek={row["block"]} count={row["count"]} conv=notrunc',90)
    sh('sync',90)
try:
    apply('new');assert sh('md5sum '+target,240).split()[0]==host['md5']
    sh('dd if='+incoming+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
    assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==prov['full_boot_sha256']
    assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery
except Exception:
    apply('old');sh('dd if='+backup+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
    assert sh('md5sum '+target,240).split()[0]==oldhost['md5']
    record['status']='INSTALL_FAILED_PREVIOUS_PAIR_RESTORED';save();raise
for row in delta:
    for side in ['new','old']:sh('rm '+remote+'/'+row[side+'_file'])
sh('rm '+incoming+' && rmdir '+remote)
empty='/data/local/tmp/t110-rom-data/local/tmp/t110-unsupported-gesture-lib.empty'
if sh('test -e '+empty+' && echo EXISTS',check=False)=='EXISTS':
    assert sh('test ! -L '+empty+' && readlink -f '+empty)==empty
    assert sh("stat -t "+empty+" | cut -d' ' -f2")=='0';sh('rm '+empty)
record.update(status='INSTALLED_VERIFIED_STARTING_ONE_FULL_BOOT',normal_boot_requests=1,recovery_sha256=recovery);save()
print('V30_BOOT34_INSTALLED_VERIFIED_STARTING_FULL_BOOT',flush=True)
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
deadline=time.monotonic()+900
while time.monotonic()<deadline:
    try:
        if sh('getprop sys.boot_completed',8,False)=='1':
            record.update(status='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING',boot_id=sh('cat /proc/sys/kernel/random/boot_id'),system_server=sh('pidof system_server'),uptime=sh('cat /proc/uptime'));save();print(json.dumps(record,indent=2),flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(4)
else:record['status']='BOOT_COMPLETION_TIMEOUT';save();raise RuntimeError('Preserve logs before another boot')
