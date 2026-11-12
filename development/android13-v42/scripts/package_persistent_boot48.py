"""Keep BOOT47's tested kernel/modules; make logging and swap policy persistent."""
from pathlib import Path
import gzip,hashlib,json,os,struct,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
stage_policy=e/'reclaim-policy-components';policy_meta=json.loads((stage_policy/'manifest.json').read_text())
assert policy_meta['status']=='STANDARD_POLICY_COMPILED_EXPORTED'
assert json.loads((e/'snapshot-optin-regressions.json').read_text())['status']=='PASS'
dest=p/'artifacts/android13-boot-v48';assert not dest.exists()
sha=lambda data:hashlib.sha256(data).hexdigest();ns={'__file__':str(p/'scripts/verify_v28_boot.py')}
exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
base=p/'artifacts/android13-boot-v47';old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text());assert sha(old[0])==parent['full_boot_sha256']
source=p/'work/core-boot/stage.c';text=source.read_text()
start=text.index('    /* Periodic full-ring writes');end=text.index('    pid_t child = fork();',start)
assert sha((text[:start]+text[end:]).encode())==parent['stage_source_sha256'],'Unrelated bootstrap source edits'
rc=(p/'work/core-boot/init.mrvl.rc').read_bytes();old_rc=old[3]['init.mrvl.rc']
replacement=b'    # Optional diagnostic file capture: start explicitly through init when needed.\n    # Normal Android logd remains available without continuous disk writes.\n'
assert old_rc.count(b'    start t110-logcat\n')==1 and rc==old_rc.replace(b'    start t110-logcat\n',replacement,1)
assert b'    write /proc/sys/vm/swappiness 100\n' in rc and b'    write /proc/sys/vm/page-cluster 0\n' in rc
policy=(stage_policy/'sepolicy').read_bytes();assert sha(policy)==policy_meta['bootstrap_policy_sha256']
dest.mkdir();binary=dest/'stage.init'
subprocess.run(['arm-linux-gnueabi-gcc','-static','-O2','-march=armv7-a','-std=gnu11','-Wall','-Wextra','-Werror','-DT110_FULL_BOOT',str(source),'-o',str(binary)],check=True)
changes={'init':binary.read_bytes(),'init.mrvl.rc':rc,'t110-preload-policy':policy}
assert changes['init'][:6]==b'\x7fELF\1\1' and struct.unpack_from('<H',changes['init'],18)[0]==40
raw=gzip.decompress(old[2]);offset=0;records=[];seen=set()
while True:
 h=bytearray(raw[offset:offset+110]);assert h[:6]==b'070701';fields=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=fields[6],fields[11]
 names=raw[offset+110:offset+110+namesize];name=names[:-1].decode();offset=(offset+110+namesize+3)&~3;body=raw[offset:offset+size];offset=(offset+size+3)&~3
 if name in changes:body=changes[name];h[54:62]=f'{len(body):08x}'.encode();seen.add(name)
 item=bytes(h)+names;item+=bytes(-len(item)%4);item+=body;item+=bytes(-len(item)%4);records.append(item)
 if name=='TRAILER!!!':break
assert seen==set(changes);raw=b''.join(records);raw+=bytes(-len(raw)%512);ramdisk=gzip.compress(raw,mtime=0);kernel=old[1]
header=bytearray(old[0][:2048]);struct.pack_into('<I',header,16,len(ramdisk));digest=hashlib.sha1()
for blob in [kernel,ramdisk,b'']:digest.update(blob);digest.update(struct.pack('<I',len(blob)))
header[576:608]=digest.digest()+bytes(12);align=lambda blob:blob+bytes(-len(blob)%2048)
boot=bytes(header)+align(kernel)+align(ramdisk);assert len(boot)<16777216;full=boot.ljust(16777216,b'\0');(dest/'KERNEL.img').write_bytes(full)
new=ns['unpack'](dest/'KERNEL.img');assert old[1]==new[1] and old[4]==new[4] and set(old[3])==set(new[3])
assert sorted(name for name in old[3] if old[3][name]!=new[3][name])==sorted(changes)
record={**parent,'status':'OFFLINE_VERIFIED_AWAITING_SYSTEM_PAIR','parent':'../android13-boot-v47','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),
 'stage_sha256':sha(changes['init']),'stage_source_sha256':sha(source.read_bytes()),'bootstrap_policy_sha256':sha(policy),'ramdisk_init_mrvl_sha256':sha(rc),
 'ramdisk_changed_files':sorted(changes),'ramdisk_bytes_unchanged':False,'boot_image_bytes':len(boot),'kernel_unchanged_from_boot47':True,
 'system_image_required':'lineage20-rom-v42-gapps','paired_system_sha256':None,'hardware_validated':False,
 'periodic_snapshots_default':False,'diagnostic_file_logcat_default':False,'persistent_init_swappiness':100,'normal_android_logd_retained':True}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n');print('BOOT48_PERSISTENT_TUNING_OFFLINE_VERIFIED',record['full_boot_sha256'],flush=True)
