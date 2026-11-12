"""Install one verified loop-system/BOOT pair, retaining the prior Android profile.

The physical SYSTEM partition is NEVER written. Recovery remains untouched.
The obsolete on-device v27 image is removed only after its host rollback hashes
and the current v28 rollback have independently passed verification.
"""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,os,subprocess,tempfile,time
parser=argparse.ArgumentParser()
parser.add_argument('--combined',action='store_true')
parser.add_argument('--revision',type=int,default=31)
parser.add_argument('--from-recovery',action='store_true')
parser.add_argument('--resume-transfer',action='store_true',help='Resume only a verified, unactivated partial revision35 transfer')
parser.add_argument('--retry-restored',action='store_true',help='Retry revision35 only after verified rollback, without an extra boot')
options=parser.parse_args()
assert options.revision in (31,32,33,34,35)
assert not options.from_recovery or options.combined
version,boot_version,old_version,old_boot_version = (
    (f'v{options.revision}',f'v{options.revision+4}',f'v{options.revision-1}',f'v{options.revision+3}')
    if options.combined else ('v29','v33','v28','v32'))
if options.combined and options.revision == 33:
    # v32 was verified offline, then superseded after the native reboot test.
    old_version,old_boot_version='v31','v35'
if options.combined and options.revision == 35:
    boot_version,old_boot_version='v41','v40'
p=Path(__file__).resolve().parents[1];e=p/f'evidence/offline-v41/gapps-{version}-test';e.mkdir(exist_ok=True)
record_path=e/'installation.json'
assert not(options.resume_transfer and options.retry_restored)
if options.resume_transfer or options.retry_restored:
    assert options.combined and options.revision==35 and options.from_recovery
    saved=json.loads(record_path.read_text())
    allowed=('INSTALL_FAILED_PREVIOUS_PAIR_PROFILE_RESTORED','VERIFYING_EXISTING_RECOVERY') if options.retry_restored else ('TRANSFERRING_VERIFIED_PAIR','VERIFYING_EXISTING_RECOVERY')
    assert saved['status'] in allowed and saved['normal_boot_requests']==0
    if options.retry_restored and saved['status']=='VERIFYING_EXISTING_RECOVERY':assert saved.get('retry_after_verified_rollback') is True
else:
    assert not record_path.exists(),'Do not repeat an installation/boot trial'
a=p/f'artifacts/lineage20-rom-{version}-gapps';source=a/'system.raw.img';host=json.loads((a/'host-verification.json').read_text())
boot=p/f'artifacts/android13-boot-{boot_version}/KERNEL.img';prov=json.loads((boot.parent/'provenance.json').read_text())
def digest(f,kind='sha256'):
    with f.open('rb') as stream:return hashlib.file_digest(stream,kind).hexdigest()
assert source.stat().st_size==2146435072 and host['status']=='OFFLINE_VERIFIED_NOT_INSTALLED'
assert digest(source)==host['sha256'] and host['bootstrap_policy_sha256']==prov['bootstrap_policy_sha256']
assert boot.stat().st_size==16777216 and digest(boot)==prov['full_boot_sha256']
assert json.loads((p/'evidence/offline-v41/mindthegapps-signature.json').read_text())['status']=='PASS'
old_variant=old_version+'-gapps' if options.combined else old_version
old=p/f'artifacts/lineage20-rom-{old_variant}';oldhost=json.loads((old/'host-verification.json').read_text())
assert digest(old/'system.raw.img')==oldhost['sha256']
oldboot=p/f'artifacts/android13-boot-{old_boot_version}/KERNEL.img';oldbootsha=digest(oldboot)
expected_parent_boot=('013b70666b9110c5320396503c0377600352febf6053b628f13c07e150cac590'
                      if options.combined else 'eceaea1d4208c0f8297474c5be98e089102c3ea4ddad24b39b4ebc466735c2f5')
if options.combined and options.revision>=32:
    previous=json.loads((p/f'evidence/offline-v41/gapps-{old_version}-test/installation.json').read_text())
    assert previous['status']=='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING'
    assert previous['system_sha256']==oldhost['sha256']
    expected_parent_boot=previous['boot_sha256']
    if options.revision==35:
        kernel_install=json.loads((p/'evidence/hardware-v35/boot40-installation.json').read_text())
        assert kernel_install['status']=='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING'
        expected_parent_boot=kernel_install['boot_sha256']
assert oldbootsha==expected_parent_boot
if not options.combined:
    v27=p/'artifacts/lineage20-rom-v27';v27host=json.loads((v27/'host-verification.json').read_text())
    assert digest(v27/'system.raw.img')==v27host['sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
    if args and args[0]=='push':
        for retry in range(2):
            if r.returncode==0:break
            error=r.stderr.decode(errors='replace')
            if not any(t in error for t in ('cannot connect to daemon','failed to get feature set','daemon still not running')):break
            # Retry only an owned regular-file upload. Activation writes and
            # renames are deliberately not retried after ambiguous disconnects.
            subprocess.run(adb[:1]+['start-server'],capture_output=True,timeout=30)
            time.sleep(2)
            identity=subprocess.run(adb+['shell','cat /sys/block/mmcblk0/device/cid'],capture_output=True,timeout=20)
            assert identity.returncode==0 and identity.stdout.decode(errors='replace').strip()=='1101003030384745T110_ADB_SERIAL'
            r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(args,r.stdout[-1500:],r.stderr[-1500:])
    return r.stdout.decode(errors='replace').strip()
def sh(s,timeout=45,check=True):return call(['shell',s],timeout,check)
cid='1101003030384745T110_ADB_SERIAL';recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert sh('id -u')=='0' and sh('cat /sys/block/mmcblk0/device/cid')==cid
if not options.combined:
    assert sh('cat /proc/sys/kernel/random/boot_id')=='046c74cc-c706-4b07-8105-bd06c5818ffe'
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==oldbootsha
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery
fresh='/stage-data/local/tmp/t110-rom-data.gapps-v29'
if not options.combined:
    assert sh('test ! -e '+fresh+' && test ! -L '+fresh+' && echo ABSENT')=='ABSENT'
    sh('mkdir '+fresh+' && chmod 0771 '+fresh+' && chown 1000:1000 '+fresh+' && chcon u:object_r:system_data_root_file:s0 '+fresh)
    assert 'u:object_r:system_data_root_file:s0' in sh('ls -ldZ '+fresh)
record={'status':'HOST_PAIR_VERIFIED','host_time':datetime.datetime.now().astimezone().isoformat(),
 'system_sha256':host['sha256'],'system_bytes':host['bytes'],'boot_sha256':prov['full_boot_sha256'],
 'previous_system_sha256':oldhost['sha256'],'previous_boot_sha256':oldbootsha,'recovery_sha256':recovery,
 'old_profile_preserved_at':'/data/local/tmp/t110-rom-data.pre-gapps','normal_boot_requests':0,
 'physical_system_written':False,'google_account_actions_taken':False}
if options.resume_transfer or options.retry_restored:
    for key in ['system_sha256','boot_sha256','previous_system_sha256','previous_boot_sha256','recovery_sha256']:
        assert saved[key]==record[key],key
    record=saved
    record.setdefault('transfer_resumptions',[]).append(datetime.datetime.now().astimezone().isoformat())
    if options.retry_restored:
        (e/'installation-before-restored-retry.json').write_text(json.dumps(saved,indent=2)+'\n',encoding='utf-8')
        record['retry_after_verified_rollback']=True
def save():record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
save()
if options.from_recovery:
    assert sh('test -x /sbin/recovery && echo RECOVERY')=='RECOVERY'
    record['entered_from_recovery']=True
    record['status']='VERIFYING_EXISTING_RECOVERY';save()
else:
    helper=('/stage-data/local/tmp/t110-rom-data.pre-gapps/local/tmp/t110_full_return_to_recovery'
            if options.combined else '/data/local/tmp/t110_full_return_to_recovery')
    assert sh('sha256sum '+helper).split()[0]=='d329829238474623f89b865f599fee09ef1f63bd13af4f7afa66beef3d38d1ba'
    record['status']='ENTERING_RECOVERY';save()
    try:sh(helper,20,False)
    except subprocess.TimeoutExpired:pass
end=time.monotonic()+160
while time.monotonic()<end:
    try:
        if sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid',8,False)==cid:break
    except subprocess.TimeoutExpired:pass
    time.sleep(3)
else:raise RuntimeError('Recovery ADB unavailable; no system/BOOT/data profile changed')
assert sh('id -u')=='0' and not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==oldbootsha
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
target='/data/local/tmp/t110-rom-system.raw';incoming=f'/data/local/tmp/t110-rom-system-{version}-gapps.incoming';chunk=f'/data/local/tmp/t110-gapps-{version}.chunk.gz'
old_image=f'/data/local/tmp/t110-rom-{old_version}.rollback.raw';old_profile='/data/local/tmp/t110-rom-data.pre-gapps'
data='/data/local/tmp/t110-rom-data';fresh='/data/local/tmp/t110-rom-data.gapps-v29'
assert sh('test -f '+target+' && test ! -L '+target+' && readlink -f '+target)==target
assert sh('md5sum '+target,180).split()[0]==oldhost['md5']
for name in [old_image] if options.resume_transfer else [incoming,chunk,old_image]:
    assert sh('test ! -e '+name+' && test ! -L '+name+' && echo ABSENT')=='ABSENT'
if options.resume_transfer:
    assert sh('test -f '+incoming+' && test ! -L '+incoming+' && readlink -f '+incoming)==incoming
    assert sh('test ! -L '+chunk+' && { test ! -e '+chunk+' || test -f '+chunk+'; } && echo SAFE')=='SAFE'
assert sh('test -d '+data+' && test ! -L '+data+' && echo SAFE')=='SAFE'
if options.combined:
    assert sh('test -d '+old_profile+' && test ! -L '+old_profile+' && echo PRESERVED')=='PRESERVED'
else:
    assert sh('test ! -e '+old_profile+' && test ! -L '+old_profile+' && test -d '+fresh+' && test ! -L '+fresh+' && echo SAFE')=='SAFE'
# Drop only an obsolete generated image with independently verified host rollback.
if not options.combined:
    obsolete='/data/local/tmp/t110-rom-v27.rollback.raw'
    assert sh('test -f '+obsolete+' && test ! -L '+obsolete+' && readlink -f '+obsolete)==obsolete
    assert sh('md5sum '+obsolete,180).split()[0]==v27host['md5']
    assert sh("stat -t "+obsolete+" | cut -d' ' -f2")=='1594884096'
    sh('rm '+obsolete+' && sync',90)
    record['removed_obsolete_generated_image']={'path':obsolete,'sha256':v27host['sha256'],'host_rollback_verified':True};save()
def free_bytes():
    row=[line.split() for line in sh('df -k /data').splitlines() if '/data' in line][-1]
    i=next(i for i,v in enumerate(row) if v.endswith('%'));return int(row[i-1])*1024
offset=int(sh("stat -t "+incoming+" | cut -d' ' -f2")) if options.resume_transfer else 0
assert 0<=offset<=source.stat().st_size
if options.resume_transfer:
    assert record['bytes_staged']<=offset<=min(source.stat().st_size,record['bytes_staged']+16*1024*1024)
    prefix=hashlib.md5()
    with source.open('rb') as stream:
        remaining=offset
        while remaining:
            prefix_bytes=stream.read(min(8*1024*1024,remaining));assert prefix_bytes;prefix.update(prefix_bytes);remaining-=len(prefix_bytes)
    assert sh('md5sum '+incoming,180).split()[0]==prefix.hexdigest(),'Partial image does not match the verified host prefix'
    record['resumed_prefix_verified_bytes']=offset
assert free_bytes()>source.stat().st_size-offset+64*1024*1024
if not options.resume_transfer:sh('test ! -e '+incoming+' && : > '+incoming)
record.update(status='TRANSFERRING_VERIFIED_PAIR',bytes_staged=offset);save()
with tempfile.TemporaryDirectory(prefix='t110-gapps-transfer-') as temp,source.open('rb') as stream:
    stream.seek(offset)
    while block:=stream.read(16*1024*1024):
        packed=gzip.compress(block,compresslevel=1,mtime=0);local=Path(temp)/'chunk.gz';local.write_bytes(packed)
        call(['push',local,chunk],180)
        md5=hashlib.md5(packed).hexdigest()
        command=f'''set -e
[ -x /sbin/recovery ]
[ -z "$(losetup -a)" ]
[ "$(stat -t {incoming} | cut -d' ' -f2)" = {offset} ]
[ "$(md5sum {chunk} | cut -d' ' -f1)" = {md5} ]
gzip -dc {chunk} >> {incoming}
[ "$(stat -t {incoming} | cut -d' ' -f2)" = {offset+len(block)} ]
rm {chunk}
echo CHUNK_OK'''
        assert 'CHUNK_OK' in sh(command,90)
        offset+=len(block);record['bytes_staged']=offset;save()
        if offset%(128*1024*1024)==0 or offset==source.stat().st_size:print(f'TRANSFER {offset}/{source.stat().st_size}',flush=True)
assert sh('md5sum '+incoming,240).split()[0]==host['md5']
boot_backup=f'/data/local/tmp/t110-boot-{old_boot_version}.rollback.img'
boot_incoming=f'/data/local/tmp/t110-boot-{boot_version}.incoming.img'
for name in (boot_backup,boot_incoming):
    if options.retry_restored:
        assert sh('test ! -L '+name+' && echo SAFE')=='SAFE'
        if sh('test -e '+name+' && echo EXISTS',check=False)=='EXISTS':
            assert sh('test -f '+name+' && readlink -f '+name)==name
            expected=oldbootsha if name==boot_backup else prov['full_boot_sha256']
            assert sh('sha256sum '+name,90).split()[0]==expected
    elif options.combined:
        assert sh('test ! -e '+name+' && test ! -L '+name+' && echo ABSENT')=='ABSENT'
    else:
        assert sh('test ! -L '+name+' && echo SAFE')=='SAFE'
sh('dd if=/dev/block/mmcblk0p10 of='+boot_backup+' bs=4096 && sync',90)
assert sh('sha256sum '+boot_backup,90).split()[0]==oldbootsha
call(['push',boot,boot_incoming],120);assert sh('sha256sum '+boot_incoming).split()[0]==prov['full_boot_sha256']
assert isinstance(data,str) and data=='/data/local/tmp/t110-rom-data'
assert sh('test -d '+data+' && echo PRESENT')=='PRESENT'
if options.combined:
    assert sh('test -d '+old_profile+' && echo PRESERVED')=='PRESERVED'
candidate_keep=incoming+'.verified-keep'
assert sh('test ! -e '+candidate_keep+' && test ! -L '+candidate_keep+' && echo ABSENT')=='ABSENT'
sh('ln '+incoming+' '+candidate_keep+' && sync',60)
record['verified_candidate_keep']=candidate_keep
record['status']='SYSTEM_BOOT_AND_ROLLBACK_VERIFIED';save()
try:
    if prov['full_boot_sha256']!=oldbootsha:
        sh('dd if='+boot_incoming+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
    else:
        record['boot_write_skipped_identical']=True;save()
    assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==prov['full_boot_sha256']
    sh('mv '+target+' '+old_image+' && mv '+incoming+' '+target+' && sync',90)
    if not options.combined:
        sh('mv '+data+' '+old_profile+' && mv '+fresh+' '+data+' && sync',90)
    assert sh('md5sum '+target,240).split()[0]==host['md5']
    assert sh('test -d '+old_profile+' && test -d '+data+' && echo PRESERVED')=='PRESERVED'
    assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery
except Exception:
    # Keep recovery open and restore the existing profile and known old BOOT.
    sh('dd if='+boot_backup+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
    if sh('test -f '+old_image+' && echo EXISTS',check=False)=='EXISTS':sh('mv '+old_image+' '+target+' && sync',90)
    if not options.combined and sh('test -d '+old_profile+' && echo EXISTS',check=False)=='EXISTS':
        if sh('test -d '+data+' && echo EXISTS',check=False)=='EXISTS':sh('mv '+data+' '+fresh)
        sh('mv '+old_profile+' '+data+' && sync',90)
    record['status']='INSTALL_FAILED_PREVIOUS_PAIR_PROFILE_RESTORED';save();raise
# The host rollback image is verified. Reclaim its unmounted duplicate for userdata.
assert sh('md5sum '+old_image,180).split()[0]==oldhost['md5'] and not sh('losetup -a')
assert sh('test ! -L '+old_image+' && readlink -f '+old_image)==old_image
sh('rm '+old_image+' && sync',90)
assert sh('md5sum '+candidate_keep,240).split()[0]==host['md5']
sh('rm '+candidate_keep+' && sync',90)
if options.combined:
    sh('rm '+boot_incoming)
record.update(status='INSTALLED_VERIFIED_STARTING_ONE_FULL_BOOT',normal_boot_requests=1,free_userdata_bytes=free_bytes())
record['boot_started_host_time']=datetime.datetime.now().astimezone().isoformat()
boot_started=time.monotonic()
save();print('GOOGLE_ROM_AND_BOOT_VERIFIED_STARTING_ONE_FULL_BOOT',flush=True)
try:sh('/sbin/reboot recovery_done',30,False)
except subprocess.TimeoutExpired:pass
end=time.monotonic()+900
while time.monotonic()<end:
    try:
        if sh('getprop sys.boot_completed',8,False)=='1':
            # adbd changes identity as startup completes; retry empty/transient
            # shell responses, while retaining strict checks on actual values.
            current_cid=sh('cat /sys/block/mmcblk0/device/cid',8,False)
            current_boot=sh('cat /proc/sys/kernel/random/boot_id',8,False)
            current_server=sh('pidof system_server',8,False)
            if not current_cid or not current_boot or not current_server:continue
            assert current_cid==cid
            record.update(status='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING',boot_id=current_boot,system_server=current_server,uptime=sh('cat /proc/uptime'),seconds_to_boot_completed=round(time.monotonic()-boot_started,2))
            save();print(json.dumps(record,indent=2),flush=True);break
    except subprocess.TimeoutExpired:pass
    time.sleep(4)
else:
    record['status']='BOOT_COMPLETION_TIMEOUT';save();raise RuntimeError('Capture logs before another boot')
