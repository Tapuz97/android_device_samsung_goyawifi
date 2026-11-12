"""Align the ION/ADB boot candidate with the newly built system policy."""
from pathlib import Path
import gzip,hashlib,json,struct
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');product=Path('/root/t110-build/out-system/target/product/t110_bringup')
base=p/'artifacts/android13-boot-v30';dest=p/'artifacts/android13-boot-v31';e=p/'evidence/offline-v41'
sha=lambda data:hashlib.sha256(data).hexdigest()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
old=ns['unpack'](base/'KERNEL.img');prov=json.loads((base/'provenance.json').read_text());assert sha(old[0])==prov['full_boot_sha256']
policy=(product/'root/sepolicy').read_bytes();assert policy==(product/'system/vendor/etc/selinux/precompiled_sepolicy').read_bytes()
assert len(policy)>500000
replacements={'t110-preload-policy':policy,'init.environ.rc':(product/'root/init.environ.rc').read_bytes()}
raw=gzip.decompress(old[2]);offset=0;records=[];seen=set()
while True:
    header=bytearray(raw[offset:offset+110]);assert header[:6]==b'070701'
    fields=[int(header[i:i+8],16) for i in range(6,110,8)];size,namesize=fields[6],fields[11]
    namebytes=raw[offset+110:offset+110+namesize];name=namebytes[:-1].decode();offset=(offset+110+namesize+3)&~3
    data=raw[offset:offset+size];offset=(offset+size+3)&~3
    if name in replacements:data=replacements[name];header[54:62]=f'{len(data):08x}'.encode();seen.add(name)
    record=bytes(header)+namebytes;record+=bytes(-len(record)%4);record+=data;record+=bytes(-len(record)%4);records.append(record)
    if name=='TRAILER!!!':break
assert seen==set(replacements)
raw=b''.join(records);raw+=bytes(-len(raw)%512);rd=gzip.compress(raw,mtime=0)
page=2048;align=lambda data:data+bytes(-len(data)%page);header=bytearray(old[0][:page])
struct.pack_into('<I',header,16,len(rd));h=hashlib.sha1()
for data in [old[1],rd,b'']:h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12);boot=bytes(header)+align(old[1])+align(rd);assert len(boot)<16777216
dest.mkdir(exist_ok=False);full=boot.ljust(16777216,b'\0');(dest/'KERNEL.img').write_bytes(full)
new=ns['unpack'](dest/'KERNEL.img');assert new[1]==old[1] and new[4]==old[4] and set(new[3])==set(old[3])
changed=[k for k in old[3] if old[3][k]!=new[3][k]];assert set(changed)<=set(replacements) and 't110-preload-policy' in changed
assert sha(new[3]['lib/modules/galcore.ko'])==prov['module_sha256']
assert new[3]['init.mrvl.rc']==old[3]['init.mrvl.rc']
result={'status':'OFFLINE_VERIFIED_NOT_FLASHED','parent':'../android13-boot-v30','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),'kernel_sha256':sha(old[1]),'module_sha256':prov['module_sha256'],'bootstrap_policy_sha256':sha(policy),'boot_image_bytes':len(boot),'boot_partition_bytes':len(full),'ramdisk_changed_files':changed,'kernel_and_touch_config_retained':True,'policy_identical_to_new_system':True,'hardware_validated':False}
(dest/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');(dest/'SHA256SUMS').write_text(sha(full)+'  KERNEL.img\n')
(e/'boot-v31-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
