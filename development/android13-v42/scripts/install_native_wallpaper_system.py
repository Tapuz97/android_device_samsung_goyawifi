"""Install the checked system using existing recovery and retain v29 BOOT/data."""
from pathlib import Path
import argparse,gzip,hashlib,json,os,subprocess,tempfile,time
parser=argparse.ArgumentParser()
parser.add_argument('--system-version',type=int,default=26,choices=[26,27,28])
parser.add_argument('--previous-version',type=int,default=25,choices=[25,26,27])
parser.add_argument('--evidence',default='offline-v39',choices=['offline-v39','offline-v40','offline-v41'])
parser.add_argument('--boot-artifact',choices=['android13-boot-v31'])
parser.add_argument('--expected-boot',default='275faee0-2b16-4672-8b2c-c59f0efc388f')
args=parser.parse_args();assert args.system_version==args.previous_version+1

p=Path(__file__).resolve().parents[1];e=p/'evidence'/args.evidence;a=p/f'artifacts/lineage20-rom-v{args.system_version}'
source=a/'system.raw.img';host=json.loads((a/'host-verification.json').read_text())
contents=json.loads((e/'contents.json').read_text());old=p/f'artifacts/lineage20-rom-v{args.previous_version}'
installed_boot_sha=contents.get('previous_boot_sha256',contents['boot_sha256'])
new_boot=p/'artifacts'/args.boot_artifact/'KERNEL.img' if args.boot_artifact else None
oldhost=json.loads((old/'host-verification.json').read_text())
assert host['status']=='VERIFIED' and contents['status']=='PASS'
assert host['sha256']==contents['system_sha256'] and source.stat().st_size==1594884096
def digest(file,kind):
    with file.open('rb') as f:return hashlib.file_digest(f,kind).hexdigest()
assert digest(source,'sha256')==host['sha256']
assert digest(old/'system.raw.img','sha256')==oldhost['sha256'],'Verified host rollback required'
if new_boot:
    assert args.system_version==28 and args.previous_version==27
    assert new_boot.stat().st_size==16777216 and digest(new_boot,'sha256')==contents['boot_sha256']
    assert digest(p/'artifacts/android13-boot-v29/KERNEL.img','sha256')==installed_boot_sha
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(args,r.stdout,r.stderr)
    return r.stdout.decode(errors='replace').strip()
def sh(s,timeout=45,check=True):return call(['shell',s],timeout,check)
cid='1101003030384745T110_ADB_SERIAL'
assert sh('cat /sys/block/mmcblk0/device/cid')==cid
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==installed_boot_sha
recovery_sha=sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]
assert sh('md5sum /dev/block/mmcblk0p9',90).split()[0]=='cd9793e1ee8f284c9056b225885b5b1a'
record={'status':'HOST_AND_DEVICE_VERIFIED','boot_sha256':installed_boot_sha,'target_boot_sha256':contents['boot_sha256'],'system_sha256':host['sha256'],'system_md5':host['md5'],'recovery_sha256':recovery_sha,'data_preserved':True,'boot_replaced':False}
def save():(e/'installation.json').write_text(json.dumps(record,indent=2)+'\n')
save()
if sh('test -x /sbin/recovery && echo RECOVERY',check=False)!='RECOVERY':
    assert sh('cat /proc/sys/kernel/random/boot_id')==args.expected_boot
    helper='/data/local/tmp/t110_full_return_to_recovery'
    assert sh('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
    record['status']='ENTERING_RECOVERY';save()
    try:call(['shell',helper],20,False)
    except subprocess.TimeoutExpired:pass  # Reboot can disconnect before acknowledgement.
    end=time.monotonic()+160
    while time.monotonic()<end:
        try:
            if sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',8,False)==cid:break
        except subprocess.TimeoutExpired:pass
        time.sleep(3)
    else:raise RuntimeError('Recovery ADB not ready; no system changed')
assert sh('id -u')=='0' and not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==installed_boot_sha
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery_sha
target='/data/local/tmp/t110-rom-system.raw';incoming=f'/data/local/tmp/t110-rom-system-v{args.system_version}.incoming';remote=f'/data/local/tmp/t110-v{args.system_version}.chunk'
assert sh(f"test -f {target} && test ! -L {target} && stat -t {target} | cut -d' ' -f2")=='1594884096'
assert sh('md5sum '+target,180).split()[0]==oldhost['md5']
old_inode=sh("stat -t "+target+" | cut -d' ' -f8")
assert sh(f'test ! -L {incoming} && test ! -e {remote} && echo SAFE')=='SAFE'
existing=sh(f"test -f {incoming} && stat -t {incoming} | cut -d' ' -f2",check=False)
offset=int(existing) if existing else 0
assert 0<=offset<=source.stat().st_size
needed=source.stat().st_size-offset
def free_bytes():
    line=[line.split() for line in sh('df -k /data').splitlines() if '/data' in line][-1]
    percent=next(i for i,v in enumerate(line) if v.endswith('%'))
    return int(line[percent-1])*1024
if free_bytes()<needed+64*1024*1024:
    obsolete='/data/local/tmp/t110-stage-system.raw'
    assert sh(f'test -f {obsolete} && test ! -L {obsolete} && readlink -f {obsolete}')==obsolete
    assert sh("stat -t "+obsolete+" | cut -d' ' -f2")=='1594884096' and not sh('losetup -a')
    record['removed_obsolete_diagnostic']={'path':obsolete,'bytes':1594884096,'reason':'Old non-full Android diagnostic loop image; current ROM uses distinct t110-rom-system.raw. Current ROM rollback verified on host; no active loop mounts in recovery.'};save()
    sh('rm '+obsolete+' && sync',90)
assert free_bytes()>needed+32*1024*1024
if sh(f'test -f {incoming} && echo EXISTS',check=False)!='EXISTS':sh(f'test ! -e {incoming} && : > {incoming}')
offset=int(sh("stat -t "+incoming+" | cut -d' ' -f2"));assert 0<=offset<=source.stat().st_size
prefix=hashlib.md5()
with source.open('rb') as f:
    remaining=offset
    while remaining:
        v=f.read(min(8*1024*1024,remaining));assert v;prefix.update(v);remaining-=len(v)
assert sh('md5sum '+incoming,180).split()[0]==prefix.hexdigest()
record.update(status='TRANSFERRING_IN_RECOVERY',bytes_staged=offset);save()
with tempfile.TemporaryDirectory(prefix='t110-native-wallpaper-') as temp,source.open('rb') as f:
    f.seek(offset)
    while block:=f.read(16*1024*1024):
        data=gzip.compress(block,compresslevel=1,mtime=0);local=Path(temp)/'chunk.gz';local.write_bytes(data)
        call(['push',local,remote],180)
        md5=hashlib.md5(data).hexdigest()
        command=f'''set -e
[ -x /sbin/recovery ]
[ -z "$(losetup -a)" ]
[ "$(stat -t {incoming} | cut -d' ' -f2)" = {offset} ]
[ "$(md5sum {remote} | cut -d' ' -f1)" = {md5} ]
gzip -dc {remote} >> {incoming}
[ "$(stat -t {incoming} | cut -d' ' -f2)" = {offset+len(block)} ]
rm {remote}
echo CHUNK_VERIFIED'''
        assert 'CHUNK_VERIFIED' in sh(command,90)
        offset+=len(block);record['bytes_staged']=offset;save()
        if offset%(128*1024*1024)==0 or offset==source.stat().st_size:print(f'TRANSFER {offset}/{source.stat().st_size}',flush=True)
assert sh('md5sum '+incoming,180).split()[0]==host['md5']
assert not sh('losetup -a') and sh("stat -t "+target+" | cut -d' ' -f8")==old_inode
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==installed_boot_sha
new_inode=sh("stat -t "+incoming+" | cut -d' ' -f8")
if new_boot:
    image_backup=f'/data/local/tmp/t110-rom-v{args.previous_version}.rollback.raw'
    boot_backup='/data/local/tmp/t110-boot-v29.rollback.img';boot_incoming='/data/local/tmp/t110-boot-v31.incoming.img'
    assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
    assert sh(f'test ! -e {image_backup} && test ! -L {boot_backup} && test ! -L {boot_incoming} && echo SAFE')=='SAFE'
    sh('dd if=/dev/block/mmcblk0p10 of='+boot_backup+' bs=4096 && sync',90)
    assert sh('sha256sum '+boot_backup,90).split()[0]==installed_boot_sha
    call(['push',new_boot,boot_incoming],120)
    assert sh('sha256sum '+boot_incoming,90).split()[0]==contents['boot_sha256']
    record.update(status='PAIR_STAGED_ROLLBACK_VERIFIED',image_rollback=image_backup,boot_rollback=boot_backup);save()
    try:
        sh('dd if='+boot_incoming+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
        assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==contents['boot_sha256']
        sh('mv '+target+' '+image_backup+' && mv '+incoming+' '+target+' && sync',90)
        assert sh('md5sum '+target,180).split()[0]==host['md5']
    except Exception:
        # Recovery remains running; restore the independently verified old pair.
        sh('dd if='+boot_backup+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
        assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==installed_boot_sha
        if sh('test -f '+image_backup+' && echo BACKUP',check=False)=='BACKUP':
            sh('mv '+image_backup+' '+target+' && sync',90)
        assert sh('md5sum '+target,180).split()[0]==oldhost['md5']
        record.update(status='INSTALL_FAILED_OLD_PAIR_RESTORED_RECOVERY_RETAINED');save();raise
    record.update(boot_replaced=True,boot_sha256=contents['boot_sha256']);save()
else:
    sh('mv '+incoming+' '+target+' && sync',90)
assert sh("stat -t "+target+" | cut -d' ' -f8")==new_inode and sh("stat -t "+target+" | cut -d' ' -f2")=='1594884096'
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery_sha
record.update(status='SYSTEM_INSTALLED_VERIFIED_RESTARTING',system_image_verified=True);save()
print('SYSTEM_AND_BOOT_VERIFIED; starting the checked LineageOS pair',flush=True)
call(['shell','/sbin/reboot recovery_done'],30,False)
end=time.monotonic()+600
while time.monotonic()<end:
    try:
        if sh('getprop sys.boot_completed',8,False)=='1':
            record.update(status='ANDROID_BOOT_COMPLETED_UI_PENDING',boot_id=sh('cat /proc/sys/kernel/random/boot_id'),system_server=sh('pidof system_server'));save()
            print(json.dumps(record,indent=2),flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(4)
else:
    record['status']='BOOT_COMPLETION_TIMEOUT';save()
    raise RuntimeError('No boot completion; capture logs before further action')
