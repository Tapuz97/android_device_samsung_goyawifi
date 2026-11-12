"""Retain the qualified Wi-Fi kernel and select software windows before zygote."""
from pathlib import Path
import gzip,hashlib,json,struct
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=p/'artifacts/android13-boot-v41';dest=p/'artifacts/android13-boot-v42';assert not dest.exists()
sha=lambda value:hashlib.sha256(value).hexdigest()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text());assert sha(old[0])==parent['full_boot_sha256']=='6d2930f8b48b45d82a8ff580cf64940eca002950d95673684d1984e9f1cbd8e4'
name='init.mrvl.rc';before=old[3][name]
assert before.count(b'\non init\n')==1
after=before.replace(b'\non init\n',b'\non init\n    # Keep normal windows on the validated path while GPU presentation is repaired.\n    setprop debug.hwui.t110_window_gpu false\n',1)
assert after.index(b'setprop debug.hwui.t110_window_gpu false')<after.index(b'\non post-fs-data\n')
source=p/'work/core-boot/init.mrvl.rc';assert source.read_bytes() in (before,after);source.write_bytes(after)
raw=gzip.decompress(old[2]);offset=0;records=[];seen=False
while True:
 h=bytearray(raw[offset:offset+110]);assert h[:6]==b'070701'
 f=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=f[6],f[11]
 names=raw[offset+110:offset+110+namesize];entry=names[:-1].decode();offset=(offset+110+namesize+3)&~3
 body=raw[offset:offset+size];offset=(offset+size+3)&~3
 if entry==name:body=after;h[54:62]=f'{len(body):08x}'.encode();seen=True
 data=bytes(h)+names;data+=bytes(-len(data)%4);data+=body;data+=bytes(-len(data)%4);records.append(data)
 if entry=='TRAILER!!!':break
assert seen;raw=b''.join(records);raw+=bytes(-len(raw)%512);ramdisk=gzip.compress(raw,mtime=0)
kernel=old[1];header=bytearray(old[0][:2048]);struct.pack_into('<I',header,16,len(ramdisk));digest=hashlib.sha1()
for data in (kernel,ramdisk,b''):digest.update(data);digest.update(struct.pack('<I',len(data)))
header[576:608]=digest.digest()+bytes(12);align=lambda value:value+bytes(-len(value)%2048)
boot=bytes(header)+align(kernel)+align(ramdisk);assert len(boot)<16777216;full=boot.ljust(16777216,b'\0')
dest.mkdir();(dest/'KERNEL.img').write_bytes(full);new=ns['unpack'](dest/'KERNEL.img')
assert new[1]==old[1] and new[4]==old[4] and set(new[3])==set(old[3])
changed=[key for key in old[3] if old[3][key]!=new[3][key]];assert changed==[name]
record={**parent,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent':'../android13-boot-v41','full_boot_sha256':sha(full),
 'full_boot_md5':hashlib.md5(full).hexdigest(),'ramdisk_changed_files':changed,'ramdisk_bytes_unchanged':False,
 'safe_window_default':'debug.hwui.t110_window_gpu=false before zygote','ramdisk_init_mrvl_sha256':sha(after),
 'boot_image_bytes':len(boot),'hardware_validated':False,'normal_gpu_window_mode_qualified':False}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n');print('BOOT42_SAFE_DEFAULT_VERIFIED',record['full_boot_sha256'])
