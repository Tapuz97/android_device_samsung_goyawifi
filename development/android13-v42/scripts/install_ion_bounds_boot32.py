"""Install only the checked v32 BOOT against the unchanged v28 system; one boot."""
from pathlib import Path
import hashlib,json,os,subprocess,time,datetime
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41';dest=e/'boot32-test';dest.mkdir(exist_ok=True)
assert not(dest/'installation.json').exists(),'No repeat trial through this script'
image=p/'artifacts/android13-boot-v32/KERNEL.img';prov=json.loads((image.parent/'provenance.json').read_text());pair=json.loads((e/'contents.json').read_text())
assert image.stat().st_size==16777216 and hashlib.sha256(image.read_bytes()).hexdigest()==prov['full_boot_sha256']
assert pair['bootstrap_policy_sha256']==prov['bootstrap_policy_sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+args,capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(args,r.stdout[-1000:],r.stderr[-1000:])
    return r.stdout.decode(errors='replace').strip()
def sh(s,timeout=45,check=True):return call(['shell',s],timeout,check)
assert sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('id -u')=='0' and not sh('losetup -a')
old='5980c7546ffe987d287b59411bad3a60e16f7ff7c9646f8e7c01cc32356b53fd';rec='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==old
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==rec
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
assert sh('md5sum /data/local/tmp/t110-rom-system.raw',180).split()[0]==json.loads((p/'artifacts/lineage20-rom-v28/host-verification.json').read_text())['md5']
backup='/data/local/tmp/t110-boot-v31.rollback.img';incoming='/data/local/tmp/t110-boot-v32.incoming.img'
assert sh('test ! -L '+backup+' && test ! -L '+incoming+' && echo SAFE')=='SAFE'
if sh('test -e '+backup+' && echo EXISTS',check=False)!='EXISTS':sh('dd if=/dev/block/mmcblk0p10 of='+backup+' bs=4096 && sync',90)
assert sh('sha256sum '+backup,90).split()[0]==old
call(['push',str(image),incoming],120);assert sh('sha256sum '+incoming).split()[0]==prov['full_boot_sha256']
record={'status':'STAGED_VERIFIED','host_time':datetime.datetime.now().astimezone().isoformat(),'previous_boot_sha256':old,'target_boot_sha256':prov['full_boot_sha256'],'system_sha256':pair['system_sha256'],'system_replaced':False,'recovery_sha256':rec,'data_preserved':True,'normal_boot_requests':0,'kernel_change':'0081 bounded SG mmap','startup_change':'standard Android fs_mgr 512MiB zram'}
def save():(dest/'installation.json').write_text(json.dumps(record,indent=2)+'\n')
save()
try:
    sh('dd if='+incoming+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
    assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==prov['full_boot_sha256']
except Exception:
    sh('dd if='+backup+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90);assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==old
    record['status']='INSTALL_FAILED_PREVIOUS_BOOT_RESTORED';save();raise
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==rec
record.update(status='BOOT_INSTALLED_VERIFIED_RESTARTING',normal_boot_requests=1);save();print('BOOT32_VERIFIED_STARTING_ONE_COMBINED_BOOT',flush=True)
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
end=time.monotonic()+600
while time.monotonic()<end:
    try:
        if sh('getprop sys.boot_completed',7,False)=='1':
            record.update(status='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING',boot_id=sh('cat /proc/sys/kernel/random/boot_id'),system_server=sh('pidof system_server'),uptime=sh('cat /proc/uptime'));save();print(json.dumps(record,indent=2),flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(4)
else:record['status']='BOOT_COMPLETION_TIMEOUT';save();raise RuntimeError('Capture logs before another action')
