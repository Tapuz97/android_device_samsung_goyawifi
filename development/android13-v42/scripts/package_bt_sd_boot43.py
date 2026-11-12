"""Retain BOOT42's tested kernel; update policy, SD fstab and BT node ownership."""
from pathlib import Path
import gzip,hashlib,json,struct
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=p/'artifacts/android13-boot-v42';dest=p/'artifacts/android13-boot-v43';assert not dest.exists()
sha=lambda data:hashlib.sha256(data).hexdigest()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text());assert sha(old[0])==parent['full_boot_sha256']=='8b5dc0d14169d5cb6f898d2f0e978242ace8aaef621a90ac47515939c887c0ab'
system=json.loads((p/'artifacts/lineage20-rom-v37-gapps/host-verification.json').read_text());assert system['status']=='OFFLINE_VERIFIED_NOT_INSTALLED'
policy=(p/'evidence/hardware-bt-sd/sepolicy').read_bytes();assert sha(policy)==system['bootstrap_policy_sha256']
def version(data):
 size=struct.unpack_from('<I',data,4)[0];assert data[8:8+size]==b'SE Linux';return struct.unpack_from('<I',data,8+size)[0]
assert version(policy)==version(old[3]['t110-preload-policy'])==30
fstab=(p/'work/device/samsung/t110_bringup/storage/fstab.mrvl').read_bytes()
for line in old[3]['fstab.mrvl'].splitlines():assert line in fstab.splitlines(),line
assert b'mmcblk0p15' not in fstab and b'voldmanaged=sdcard1:auto' in fstab
uevent=old[3]['ueventd.mrvl.rc'];assert b'mbtchar' not in uevent and uevent.endswith(b'\n')
uevent+=b'/dev/mbtchar* 0660 system bluetooth\n'
changes={'t110-preload-policy':policy,'fstab.mrvl':fstab,'ueventd.mrvl.rc':uevent}
raw=gzip.decompress(old[2]);offset=0;records=[];seen=set()
while True:
 h=bytearray(raw[offset:offset+110]);assert h[:6]==b'070701';fields=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=fields[6],fields[11]
 names=raw[offset+110:offset+110+namesize];entry=names[:-1].decode();offset=(offset+110+namesize+3)&~3
 body=raw[offset:offset+size];offset=(offset+size+3)&~3
 if entry in changes:body=changes[entry];h[54:62]=f'{len(body):08x}'.encode();seen.add(entry)
 data=bytes(h)+names;data+=bytes(-len(data)%4);data+=body;data+=bytes(-len(data)%4);records.append(data)
 if entry=='TRAILER!!!':break
assert seen==changes.keys();raw=b''.join(records);raw+=bytes(-len(raw)%512);ramdisk=gzip.compress(raw,mtime=0)
kernel=old[1];header=bytearray(old[0][:2048]);struct.pack_into('<I',header,16,len(ramdisk));digest=hashlib.sha1()
for data in [kernel,ramdisk,b'']:digest.update(data);digest.update(struct.pack('<I',len(data)))
header[576:608]=digest.digest()+bytes(12);align=lambda value:value+bytes(-len(value)%2048)
boot=bytes(header)+align(kernel)+align(ramdisk);assert len(boot)<16777216;full=boot.ljust(16777216,b'\0')
dest.mkdir();(dest/'KERNEL.img').write_bytes(full);new=ns['unpack'](dest/'KERNEL.img')
assert new[1]==old[1] and new[4]==old[4] and set(new[3])==set(old[3])
changed=sorted(key for key in old[3] if old[3][key]!=new[3][key]);assert changed==sorted(changes)
assert b'setprop debug.hwui.t110_window_gpu false' in new[3]['init.mrvl.rc']
record={**parent,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent':'../android13-boot-v42','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),
 'ramdisk_changed_files':changed,'bootstrap_policy_sha256':sha(policy),'ramdisk_bytes_unchanged':False,'boot_image_bytes':len(boot),'hardware_validated':False,
 'kernel_unchanged_from_boot42':True,'bluetooth_node_mode':'0660 system:bluetooth','paired_system_sha256':system['sha256']}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
(p/'work/core-boot/logging-test-policy').write_bytes(policy)
(p/'work/core-boot/fstab.mrvl').write_bytes(fstab);(p/'work/core-boot/ueventd.mrvl.rc').write_bytes(uevent)
print('BOOT43_BLUETOOTH_SD_OFFLINE_VERIFIED',record['full_boot_sha256'])
