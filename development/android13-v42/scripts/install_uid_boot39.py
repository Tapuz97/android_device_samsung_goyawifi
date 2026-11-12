"""Guarded boot-only update on the authorized SM-T110. Never write SYSTEM/recovery."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,time
parser=argparse.ArgumentParser();parser.add_argument('--revision',type=int,choices=(39,40),default=39);args=parser.parse_args();number=args.revision
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
record_path=e/f'boot{number}-installation.json';assert not record_path.exists(),'Never repeat a recorded install'
boot=p/f'artifacts/android13-boot-v{number}/KERNEL.img'
metadata=json.loads((boot.parent/'provenance.json').read_text())
parent=p/f'artifacts/android13-boot-v{number-1}/KERNEL.img'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert boot.stat().st_size==parent.stat().st_size==16777216
expected_parent='33462a6a2cffc1695ac8d8f986d42eac13b12b0708a5eb9db26f66c9baa73701' if number==40 else 'b5bab81d2693d3b8b3e479963275173c938b3110e3110fa20489f72cae5694c5'
assert sha(boot)==metadata['full_boot_sha256'] and sha(parent)==expected_parent
assert metadata['uid_qemu_regression_tests']==71 and metadata['uid_qemu_regression_failures']==0
if number==40:assert metadata['packet_target_qemu_checks']==10 and metadata['kernel_variant']=='netd-targets'
equivalence=json.loads((e/('module-equivalence-netd.json' if number==40 else 'module-equivalence.json')).read_text());assert all(x['status']=='ALLOC_AND_RELOCATIONS_IDENTICAL' for x in equivalence.values())
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,r.stderr.decode(errors='replace')
    return r.stdout.decode(errors='replace').strip()
def sh(command,timeout=45,check=True):return call(['shell',command],timeout,check)
assert sh('id -u')=='0'
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('getprop sys.boot_completed')=='1' and sh('getprop ro.product.device')=='t110_bringup'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==sha(parent)
recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
for name in ('mlan.ko','sd8xxx.ko'):
    item=equivalence['drivers/marvell/sd8787/wlan_src/'+name]
    assert sh('sha256sum /vendor/etc/wifi/modules/'+name).split()[0]==item['old_file_sha256']
target=f'/data/local/tmp/t110-network-boot{number}.img'
assert sh('test ! -e '+target+' && test ! -L '+target+' && echo ABSENT')=='ABSENT'
record=dict(status='HOST_AND_DEVICE_GUARDS_PASS',host_time=datetime.datetime.now().astimezone().isoformat(),
            parent_boot_sha256=sha(parent),boot_sha256=sha(boot),system_image_changed=False,
            physical_system_written=False,recovery_written=False,boot_requests=0,
            previous_boot_id=sh('cat /proc/sys/kernel/random/boot_id'))
def save():record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
save();call(['push',boot,target],60)
assert sh('sha256sum '+target).split()[0]==sha(boot)
record['status']='STAGED_BOOT_VERIFIED';save()
sh('dd if='+target+' of=/dev/block/mmcblk0p10 bs=4096 count=4096 conv=fsync',90)
if sh('sha256sum /dev/block/mmcblk0p10').split()[0]!=sha(boot):
    rollback=f'/data/local/tmp/t110-network-boot{number-1}-rollback.img'
    call(['push',parent,rollback],60)
    assert sh('sha256sum '+rollback).split()[0]==sha(parent)
    sh('dd if='+rollback+' of=/dev/block/mmcblk0p10 bs=4096 count=4096 conv=fsync',90)
    assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==sha(parent)
    record['status']='WRITE_VERIFICATION_FAILED_PARENT_RESTORED';save()
    raise RuntimeError(record['status'])
record['status']='BOOT_PARTITION_VERIFIED';save()
record['boot_requests']=1;record['status']='BOOTING';save();started=time.monotonic()
call(['reboot'],20,False)
while time.monotonic()-started<540:
    time.sleep(5)
    try:
        if sh('getprop sys.boot_completed',8,False)=='1':
            current=sh('cat /proc/sys/kernel/random/boot_id')
            if current==record['previous_boot_id']:continue
            assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
            assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==sha(boot)
            record.update(status='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING',boot_id=current,
                          system_server=sh('pidof system_server'),uptime=sh('cat /proc/uptime'),
                          seconds_to_boot_completed=round(time.monotonic()-started,2),kernel=sh('uname -a'))
            save();print(json.dumps(record,indent=2));break
    except subprocess.TimeoutExpired:pass
else:
    record['status']='BOOT_NOT_CONFIRMED_WITHIN_540_SECONDS';save();raise RuntimeError(record['status'])
