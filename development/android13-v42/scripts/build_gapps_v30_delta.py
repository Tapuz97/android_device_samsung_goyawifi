"""Derive the corrected private image and a guarded forward/reverse block delta.

Native apps and Google APKs are retained byte for byte. Only Google's optional
gesture JNI library, which SIGILLs on Cortex-A9, is omitted; native LatinIME
already contains the working AOSP backend and existing load-failure fallback.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build')
product=b/'out-system/target/product/t110_bringup';e=p/'evidence/offline-v41/swap-label-fix';e.mkdir(exist_ok=True)
parent=p/'artifacts/lineage20-rom-v29-gapps';a=p/'artifacts/lineage20-rom-v30-gapps';native=b/'export-lineage20-rom-v30-gapps'
resume='--resume-delta' in sys.argv
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
assert (not a.exists() and not native.exists()) or (resume and a.is_dir() and native.is_dir() and not (a/'host-verification.json').exists())
def digest(f,kind='sha256'):
    with f.open('rb') as stream:return hashlib.file_digest(stream,kind).hexdigest()
old=json.loads((parent/'host-verification.json').read_text());base=parent/'system.raw.img'
assert digest(base)==old['sha256']
raw=(native/'system.raw.img') if resume else b/'export-lineage20-rom-v29-gapps/system.raw.img'
assert raw.is_file() and not raw.is_symlink() and raw.stat().st_size==2146435072
if not resume:assert digest(raw)==old['sha256']
policy=(product/'root/sepolicy').read_bytes();assert policy==(product/'system/vendor/etc/selinux/precompiled_sepolicy').read_bytes()
logfile=Path((p/'evidence/offline-v41/swap-label-build-log.txt').read_text().strip())
assert 'build completed successfully' in logfile.read_text(errors='replace')
assert b'allow init swap_block_device:blk_file swapon;' in (p/'work/device/samsung/t110_bringup/sepolicy/t110_bootlog.te').read_bytes()
# Preserve the existing platform export; do not duplicate it in vendor contexts.
src=p/'work/device/samsung/t110_bringup/sepolicy/property_contexts'
shutil.copyfile(src,b/'lineage20/device/samsung/t110_bringup/sepolicy/property_contexts')
property_file=e/'vendor_property_contexts'
old_props=(product/'system/vendor/etc/selinux/vendor_property_contexts').read_text()
line='ro.t110.legacy_gpu u:object_r:exported_default_prop:s0 exact bool'
assert line not in old_props
assert line in (product/'system/etc/selinux/plat_property_contexts').read_text()
property_file.write_text(old_props)
checker=b/'out-system/host/linux-x86/bin/property_info_checker'
context_files=[f for f in [product/'system/etc/selinux/plat_property_contexts',product/'system/system_ext/etc/selinux/system_ext_property_contexts',product/'system/product/etc/selinux/product_property_contexts'] if f.is_file()]+[property_file]
r=subprocess.run([str(checker),str(product/'root/sepolicy'),*map(str,context_files)],capture_output=True,text=True)
(e/'property-info-check.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
property_check_exit=r.returncode
native.mkdir(exist_ok=resume)
if not resume:
    target=native/'system.raw.img';raw.rename(target);raw=target
def debug(command,binary=False):
    r=subprocess.run(['debugfs','-R',command,str(raw)],capture_output=True,check=True)
    return r.stdout if binary else r.stdout.decode(errors='replace')
updates={n:product/n for n in ['system/vendor/etc/selinux/precompiled_sepolicy','system/vendor/etc/selinux/vendor_sepolicy.cil','system/vendor/etc/selinux/vendor_file_contexts']}
assert '/dev/block/zram0' in updates['system/vendor/etc/selinux/vendor_file_contexts'].read_text()
context=native/'system-file-context.bin';context.write_bytes(b'u:object_r:system_file:s0\0')
commands=[]
for name,f in updates.items():
    assert debug('stat /'+name)
    commands += ['rm /'+name,f'write {f} /{name}',f'set_inode_field /{name} mode 0100644',f'set_inode_field /{name} uid 0',f'set_inode_field /{name} gid 0',f'ea_set -f {context} /{name} security.selinux']
excluded='system/product/lib/libjni_latinimegoogle.so'
if not resume:assert hashlib.sha256(debug('cat /'+excluded,True)).hexdigest()==old['gapps_files'][excluded]
commands.append('rm /'+excluded)
batch=native/'update.debugfs';batch.write_text('\n'.join(commands)+'\n')
if not resume:
    r=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,text=True)
    (native/'update.log').write_text(r.stdout+r.stderr);assert r.returncode==0
assert not debug('stat /'+excluded)
new_hashes={n:digest(f) for n,f in updates.items()}
for n,h in new_hashes.items():assert hashlib.sha256(debug('cat /'+n,True)).hexdigest()==h
for n,h in old['native_components_unchanged'].items():assert hashlib.sha256(debug('cat /'+n,True)).hexdigest()==h
google={n:h for n,h in old['gapps_files'].items() if n!=excluded}
for n,h in google.items():assert hashlib.sha256(debug('cat /'+n,True)).hexdigest()==h
assert hashlib.sha256(debug('cat /system/product/lib/libjni_latinime.so',True)).hexdigest()=='ea8a4d30d8eee4f98d9e98aa9e5fbae1f1a1cd901b76f59900ac31c4465e9ccc'
ns={};exec((p/'scripts/verify_system_image_fit.py').read_text().split('if __name__',1)[0],ns)
fs=ns['inspect_ext4'](raw);assert fs['fsck_exit']==0 and fs['ext4_features']==old['ext4']['ext4_features']
a.mkdir(exist_ok=resume);delta=a/'delta';delta.mkdir(exist_ok=resume);ranges=[]
# Consecutive changed ext4 blocks are grouped, capped at one MiB per piece.
with base.open('rb',buffering=16*1024*1024) as before,raw.open('rb',buffering=16*1024*1024) as after:
    start=None;old_bytes=bytearray();new_bytes=bytearray();block=0
    def flush():
        if start is None:return
        number=len(ranges);fwd=delta/f'{number:04d}.new.bin';rev=delta/f'{number:04d}.old.bin'
        fwd.write_bytes(new_bytes);rev.write_bytes(old_bytes)
        ranges.append({'block':start,'count':len(new_bytes)//4096,'bytes':len(new_bytes),'new_file':fwd.name,'old_file':rev.name,'new_sha256':digest(fwd),'old_sha256':digest(rev),'new_md5':digest(fwd,'md5'),'old_md5':digest(rev,'md5')})
    while True:
        old_block=before.read(4096);new_block=after.read(4096)
        assert len(old_block)==len(new_block)
        if not old_block:flush();break
        if old_block!=new_block:
            if start is None:start=block
            old_bytes.extend(old_block);new_bytes.extend(new_block)
            if len(new_bytes)==1024*1024:flush();start=None;old_bytes=bytearray();new_bytes=bytearray()
        elif start is not None:flush();start=None;old_bytes=bytearray();new_bytes=bytearray()
        block+=1
assert ranges and sum(r['bytes'] for r in ranges)<8*1024*1024
record={'status':'OFFLINE_VERIFIED_NOT_INSTALLED','bytes':raw.stat().st_size,'sha256':digest(raw),'md5':digest(raw,'md5'),
 'parent_sha256':old['sha256'],'parent_md5':old['md5'],'fits_physical_system':False,'storage':'loop file on userdata; NEVER physical SYSTEM',
 'bootstrap_policy_sha256':hashlib.sha256(policy).hexdigest(),'updated_files':new_hashes,'native_components_unchanged':old['native_components_unchanged'],
 'gapps_files':google,'gapps_optional_library_excluded':{'file':excluded,'reason':'Proven SIGILL at SDIV +0x61520; Cortex-A9 has no integer divide instruction','native_AOSP_keyboard_retained':True,'optional_Google_gesture_typing_supported':False},
 'google_APKs_removed':[],'gapps_zip_sha256':old['gapps_zip_sha256'],'property_info_checker_exit':property_check_exit,'ext4':fs,
 'source_build_log':str(logfile),'source_build_succeeded':True,'source_wrapper_postexport_failed_due_inflight_edit':True,
 'delta_block_size':4096,'delta_ranges':ranges,'delta_bytes':sum(r['bytes'] for r in ranges),'hardware_validated':False}
shutil.copyfile(raw,a/'system.raw.incoming');assert digest(a/'system.raw.incoming')==record['sha256'];(a/'system.raw.incoming').rename(a/'system.raw.img')
(a/'host-verification.json').write_text(json.dumps(record,indent=2)+'\n');(e/'image-verification.json').write_text(json.dumps(record,indent=2)+'\n')
for name in ['root/sepolicy']:
    f=e/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(product/name,f)
print('V30_OFFLINE_VERIFIED_DELTA_BYTES',record['delta_bytes'],record['sha256'],flush=True)
