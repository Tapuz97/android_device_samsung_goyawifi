"""Install only the host-preoptimized Search files, with an exact v39 rollback."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys,tarfile,time
persistent='--persistent' in sys.argv
reclaim='--reclaim' in sys.argv or persistent;version=42 if persistent else (41 if reclaim else 40)
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';receipt=e/f'v{version}-installation.json';assert not receipt.exists()
a=p/f'artifacts/lineage20-rom-v{version}-gapps';parent=p/f'artifacts/lineage20-rom-v{version-1}-gapps'
host=json.loads((a/'host-verification.json').read_text());old=json.loads((parent/'host-verification.json').read_text())
previous_install=json.loads(((e/'v41-installation.json') if persistent else ((e/'boot46-installation.json') if reclaim else (p/'evidence/hardware-bt-sd/v39-installation.json'))).read_text())
def sha(f):
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert host['status']=='OFFLINE_VERIFIED_NOT_INSTALLED' and sha(a/'system.raw.img')==host['sha256']
assert sha(parent/'system.raw.img')==host['parent_sha256']==old['sha256']
assert host['gapps_files']==old['gapps_files'] and host['native_components_unchanged']==old['native_components_unchanged']
old_boot=previous_install['boot_sha256']
boot=old_boot
if reclaim:
    candidate=p/('artifacts/android13-boot-v48/KERNEL.img' if persistent else 'artifacts/android13-boot-v47/KERNEL.img');boot_meta=json.loads((candidate.parent/'provenance.json').read_text());boot=boot_meta['full_boot_sha256']
    rollback=p/('artifacts/android13-boot-v47/KERNEL.img' if persistent else 'artifacts/android13-boot-v46/KERNEL.img')
    assert sha(candidate)==boot and sha(rollback)==old_boot and candidate.stat().st_size==rollback.stat().st_size==16777216
    assert boot_meta['status']=='OFFLINE_VERIFIED_NOT_INSTALLED' and boot_meta['paired_system_sha256']==host['sha256']
    assert boot_meta['standard_reclaim_enabled'] and boot_meta['module_equivalence_verified']
    if persistent:
        assert boot_meta['kernel_unchanged_from_boot47'] and not boot_meta['periodic_snapshots_default'] and not boot_meta['diagnostic_file_logcat_default']
        assert boot_meta['bootstrap_policy_sha256']==host['bootstrap_policy_sha256'] and boot_meta['normal_android_logd_retained']
new_boot_name='boot48.img' if persistent else 'boot47.img'
old_boot_name='rollback47.img' if persistent else 'rollback46.img'
assert host['paired_boot_sha256']==boot
ranges=host['delta_ranges'];end=0
for row in ranges:
    assert row['block']>=end and row['bytes']==row['count']*4096;end=row['block']+row['count'];assert end*4096<=host['bytes']
    for side in ['new','old']:
        f=a/'delta'/row[side+'_file'];assert f.stat().st_size==row['bytes'] and sha(f)==row[side+'_sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    return r.stdout.decode(errors='replace').replace('\r','').strip()
def sh(command,timeout=45,check=True):return call(['shell',command],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('cat /sys/block/mmcblk0/device/cid')==cid and sh('id -u')=='0'
previous=sh('cat /proc/sys/kernel/random/boot_id');assert previous==previous_install['boot_id']
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot
helper='/stage-data/local/tmp/t110-rom-data.pre-gapps/local/tmp/t110_full_return_to_recovery'
assert sh('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
state=dict(status='OFFLINE_AND_DEVICE_IDENTITY_VERIFIED',time=datetime.datetime.now().astimezone().isoformat(),previous_boot_id=previous,
           system_sha256=host['sha256'],previous_system_sha256=old['sha256'],boot_sha256=boot,previous_boot_sha256=old_boot,recovery_written=False,
           physical_system_written=False,boot_written=False,data_profiles_preserved=True,normal_boot_requests=0,ui_fixed=False,delta_bytes=host['delta_bytes'])
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
else:state['status']='RECOVERY_UNAVAILABLE_NO_IMAGE_WRITE';save();raise RuntimeError(state['status'])
assert not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot and sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
if reclaim:assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
target='/data/local/tmp/t110-rom-system.raw'
assert sh('test -f '+target+' && test ! -L '+target+' && readlink -f '+target)==target
assert sh("stat -t "+target+" | cut -d' ' -f2")==str(host['bytes'])=='2146435072'
assert sh('md5sum '+target,240).split()[0]==old['md5']
assert sh('test -d /data/local/tmp/t110-rom-data && test -d /data/local/tmp/t110-rom-data.pre-gapps && echo PRESERVED')=='PRESERVED'
available=int(sh('df -k /data').splitlines()[-1].split()[-3])*1024
assert available>2*host['delta_bytes']+64*1024*1024+(2*16777216 if reclaim else 0)
remote='/data/local/tmp/t110-v42-persistent-delta' if persistent else ('/data/local/tmp/t110-v41-reclaim-paths-delta' if reclaim else '/data/local/tmp/t110-v40-search-preopt-delta')
assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT';sh('mkdir '+remote)
if persistent:
    assert sh('test ! -e /data/local/tmp/t110-bootlogs/periodic-enabled && test ! -L /data/local/tmp/t110-bootlogs/periodic-enabled && echo DEFAULT_OFF')=='DEFAULT_OFF'
    files={row[side+'_file']:(a/'delta'/row[side+'_file'],row[side+'_sha256']) for row in ranges for side in ['new','old']}
    files.update({new_boot_name:(candidate,boot),old_boot_name:(rollback,old_boot)})
    archive=a/'transfer.tar.gz';assert not archive.exists()
    with tarfile.open(archive,'w:gz',format=tarfile.USTAR_FORMAT) as bundle:
        for name,(file,digest) in files.items():
            assert re.fullmatch(r'(?:[0-9]{4}\.(?:new|old)\.bin|boot48\.img|rollback47\.img)',name)
            bundle.add(file,arcname=name,recursive=False)
    call(['push',archive,remote+'/transfer.tar.gz'],120)
    assert sh('sha256sum '+remote+'/transfer.tar.gz').split()[0]==sha(archive)
    sh('tar -xzf '+remote+'/transfer.tar.gz -C '+remote,120)
    received={};names=list(files)
    for offset in range(0,len(names),128):
        hashes=sh('sha256sum '+' '.join(remote+'/'+name for name in names[offset:offset+128]),120)
        received.update({line.split()[1].rsplit('/',1)[-1]:line.split()[0] for line in hashes.splitlines()})
    assert received=={name:digest for name,(_,digest) in files.items()}
    sh('rm '+remote+'/transfer.tar.gz')
else:
    for row in ranges:
        for side in ['new','old']:
            name=row[side+'_file'];call(['push',a/'delta'/name,remote+'/'+name],90)
            assert sh('sha256sum '+remote+'/'+name).split()[0]==row[side+'_sha256']
    if reclaim:
        for name,file,digest in [(new_boot_name,candidate,boot),(old_boot_name,rollback,old_boot)]:
            call(['push',file,remote+'/'+name],90);assert sh('sha256sum '+remote+'/'+name).split()[0]==digest
state.update(status='REVERSIBLE_DELTA_STAGED_VERIFIED',reverse_delta_retained=remote);save()
def apply(side):
    assert not sh('losetup -a')
    if persistent:
        commands=[f'dd if={remote}/{row[side+"_file"]} of={target} bs=4096 seek={row["block"]} count={row["count"]} conv=notrunc' for row in ranges]
        for offset in range(0,len(commands),128):sh('set -e\n'+'\n'.join(commands[offset:offset+128]),180)
    else:
        for row in ranges:sh(f'dd if={remote}/{row[side+"_file"]} of={target} bs=4096 seek={row["block"]} count={row["count"]} conv=notrunc',90)
    sh('sync',90)
try:
    apply('new');assert sh('md5sum '+target,240).split()[0]==host['md5']
    if reclaim:
        sh('dd if='+remote+'/'+new_boot_name+' of=/dev/block/mmcblk0p10 bs=4096',90);sh('sync',90);state['boot_written']=True
    assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==boot and sh('sha256sum /dev/block/mmcblk0p9').split()[0]==recovery
except Exception:
    state['status']=f'POST_WRITE_CHECK_FAILED_RESTORING_V{version-1}';save();apply('old')
    if reclaim:sh('dd if='+remote+'/'+old_boot_name+' of=/dev/block/mmcblk0p10 bs=4096',90);sh('sync',90)
    assert sh('md5sum '+target,240).split()[0]==old['md5'] and sh('sha256sum /dev/block/mmcblk0p10').split()[0]==old_boot
    state['status']=f'V{version-1}_PAIR_RESTORED_RECOVERY_RETAINED';save();raise
if reclaim and not persistent:
    # The v41 reverse delta and BOOT46 now provide the complete immediate
    # rollback. Retain those; delete only the verified older v40 transfer set.
    stale='/data/local/tmp/t110-v40-search-preopt-delta'
    names=[row[side+'_file'] for row in old['delta_ranges'] for side in ['old','new']]
    assert all(re.fullmatch(r'[0-9]{4}\.(old|new)\.bin',name) for name in names)
    identity=sh('test -d '+stale+' && test ! -L '+stale+' && readlink -f '+stale,45,False)
    if identity==stale and set(sh('ls -1 '+stale).splitlines())==set(names):
        sh('rm '+' '.join(stale+'/'+name for name in names),90);sh('rmdir '+stale)
        state['superseded_v40_transfer_deleted_bytes']=2*old['delta_bytes']
        state['immediate_v40_rollback_preserved']=remote
state.update(status=f'V{version}_IMAGE_VERIFIED_STARTING_ONE_FULL_BOOT',normal_boot_requests=1);save();started=time.monotonic()
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
while time.monotonic()-started<900:
    time.sleep(5)
    try:
        if sh('getprop sys.boot_completed',8,False)!='1':continue
        current=sh('cat /proc/sys/kernel/random/boot_id',8,False)
        if not current or current==previous:continue
        assert sh('cat /sys/block/mmcblk0/device/cid')==cid and sh('getprop debug.hwui.t110_window_gpu')=='false'
        state.update(status='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING',boot_id=current,system_server=sh('pidof system_server'),
                     seconds_to_boot_completed=round(time.monotonic()-started,2),selinux=sh('getenforce'))
        save();break
    except subprocess.TimeoutExpired:pass
else:state['status']='BOOT_NOT_CONFIRMED';save();raise RuntimeError(state['status'])
