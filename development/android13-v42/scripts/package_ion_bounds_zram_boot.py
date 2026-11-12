"""Pair the bounded ION kernel with standard Android compressed-RAM startup."""
from pathlib import Path
import gzip,hashlib,json,struct
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41';base=p/'artifacts/android13-boot-v31';dest=p/'artifacts/android13-boot-v32';k=p/'artifacts/kernel-ion-bounds'
sha=lambda b:hashlib.sha256(b).hexdigest()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text());kernel=(k/'zImage').read_bytes();provenance=json.loads((k/'provenance.json').read_text())
assert sha(old[0])==parent['full_boot_sha256'] and sha(kernel)==provenance['kernel_sha256']
assert sha(old[3]['lib/modules/galcore.ko'])==provenance['module_sha256']
rc=(p/'work/core-boot/init.mrvl.rc').read_bytes();fstab=(p/'work/core-boot/fstab.t110.zram').read_bytes()
addition=b'    # The kernel exposes zram0 but it was left at disksize=0. Use Android\'s\n    # standard swap setup before zygote/main services to relieve boot pressure.\n    swapon_all /fstab.t110.zram\n'
assert rc.replace(addition,b'')==old[3]['init.mrvl.rc'] and rc.count(addition)==1
assert [line for line in fstab.decode().splitlines() if line and not line.startswith('#')]==['/dev/block/zram0 none swap defaults zramsize=536870912']
def record(header,name,data):
    namebytes=name.encode()+b'\0';header=bytearray(header)
    header[54:62]=f'{len(data):08x}'.encode();header[94:102]=f'{len(namebytes):08x}'.encode()
    r=bytes(header)+namebytes;r+=bytes(-len(r)%4);r+=data;r+=bytes(-len(r)%4);return r
raw=gzip.decompress(old[2]);offset=0;records=[];max_ino=0;trailer=None
while True:
    h=raw[offset:offset+110];assert h[:6]==b'070701';fields=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=fields[6],fields[11]
    name=raw[offset+110:offset+110+namesize-1].decode();offset=(offset+110+namesize+3)&~3;data=raw[offset:offset+size];offset=(offset+size+3)&~3
    if name=='TRAILER!!!':trailer=record(h,name,data);break
    max_ino=max(max_ino,fields[0])
    records.append(record(h,name,rc if name=='init.mrvl.rc' else data))
fields=[max_ino+1,0o100644,0,0,1,0,len(fstab),0,0,0,0,len('fstab.t110.zram')+1,0]
new_header=b'070701'+b''.join(f'{v:08x}'.encode() for v in fields)
records.extend([record(new_header,'fstab.t110.zram',fstab),trailer]);cpio=b''.join(records);cpio+=bytes(-len(cpio)%512);rd=gzip.compress(cpio,mtime=0)
page=2048;align=lambda b:b+bytes(-len(b)%page);header=bytearray(old[0][:page]);struct.pack_into('<I',header,8,len(kernel));struct.pack_into('<I',header,16,len(rd))
h=hashlib.sha1()
for data in [kernel,rd,b'']:h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12);boot=bytes(header)+align(kernel)+align(rd);assert len(boot)<16777216
dest.mkdir(exist_ok=False);full=boot.ljust(16777216,b'\0');(dest/'KERNEL.img').write_bytes(full)
new=ns['unpack'](dest/'KERNEL.img')
assert set(new[3])==set(old[3])|{'fstab.t110.zram'}
changed=[n for n in old[3] if old[3][n]!=new[3][n]];assert changed==['init.mrvl.rc']
assert all(old[4][n]==new[4][n] for n in old[4])
assert new[1]==kernel and new[3]['fstab.t110.zram']==fstab
assert new[0][12:16]==old[0][12:16] and new[0][20:576]==old[0][20:576]
assert sha(new[3]['t110-preload-policy'])==parent['bootstrap_policy_sha256']
result={'status':'OFFLINE_VERIFIED_NOT_BOOT_TESTED','parent':'../android13-boot-v31','system_pair':'../lineage20-rom-v28/system.raw.img','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),'kernel_sha256':sha(kernel),'module_sha256':provenance['module_sha256'],'config_sha256':provenance['config_sha256'],'bootstrap_policy_sha256':parent['bootstrap_policy_sha256'],'changed_existing_ramdisk_files':changed,'new_ramdisk_files':['fstab.t110.zram'],'ramdisk_existing_metadata_retained':True,'kernel_bounds_host_cases':37414,'compressed_ram_bytes':536870912,'swap_backing':'RAM only; standard Android fs_mgr; no eMMC swap','boot_image_bytes':len(boot),'boot_partition_bytes':len(full),'hardware_validated':False,'flashed':False,'startup_anr_free_proven':False}
(dest/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');(e/'boot-v32-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
