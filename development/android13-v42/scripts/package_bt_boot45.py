"""Keep the platform dependency trigger; return to the native HAL service definition."""
from pathlib import Path
import gzip,hashlib,json,struct
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';dest=p/'artifacts/android13-boot-v45';assert not dest.exists()
sha=lambda data:hashlib.sha256(data).hexdigest();ns={'__file__':str(p/'scripts/verify_v28_boot.py')}
exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
base=p/'artifacts/android13-boot-v44';old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text());assert sha(old[0])==parent['full_boot_sha256']
system=json.loads((p/'artifacts/lineage20-rom-v38-gapps/host-verification.json').read_text());assert system['status']=='OFFLINE_VERIFIED_NOT_INSTALLED'
before=old[3]['init.mrvl.rc'];marker=b'# This pre-Treble product uses the legacy linker namespace';assert before.count(marker)==1
after=before.split(marker)[0];assert b'on property:init.svc.t110-radio-init=stopped\n    start t110-bluetooth-init\n' in after
assert b'service vendor.bluetooth-1-1' not in after and b'LD_LIBRARY_PATH' not in after
(e/'boot45-init.mrvl.rc').write_bytes(after)
raw=gzip.decompress(old[2]);offset=0;records=[];seen=0
while True:
 h=bytearray(raw[offset:offset+110]);assert h[:6]==b'070701';fields=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=fields[6],fields[11]
 names=raw[offset+110:offset+110+namesize];name=names[:-1].decode();offset=(offset+110+namesize+3)&~3;body=raw[offset:offset+size];offset=(offset+size+3)&~3
 if name=='init.mrvl.rc':body=after;h[54:62]=f'{len(body):08x}'.encode();seen+=1
 data=bytes(h)+names;data+=bytes(-len(data)%4);data+=body;data+=bytes(-len(data)%4);records.append(data)
 if name=='TRAILER!!!':break
assert seen==1;raw=b''.join(records);raw+=bytes(-len(raw)%512);ramdisk=gzip.compress(raw,mtime=0);kernel=old[1]
header=bytearray(old[0][:2048]);struct.pack_into('<I',header,16,len(ramdisk));digest=hashlib.sha1()
for data in [kernel,ramdisk,b'']:digest.update(data);digest.update(struct.pack('<I',len(data)))
header[576:608]=digest.digest()+bytes(12);align=lambda value:value+bytes(-len(value)%2048)
boot=bytes(header)+align(kernel)+align(ramdisk);assert len(boot)<16777216;full=boot.ljust(16777216,b'\0');dest.mkdir();(dest/'KERNEL.img').write_bytes(full);new=ns['unpack'](dest/'KERNEL.img')
assert old[1]==new[1] and old[4]==new[4] and set(old[3])==set(new[3])
assert [key for key in old[3] if old[3][key]!=new[3][key]]==['init.mrvl.rc']
record={**parent,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent':'../android13-boot-v44','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),
 'paired_system_sha256':system['sha256'],'ramdisk_changed_files':['init.mrvl.rc'],'boot_image_bytes':len(boot),'hardware_validated':False,
 'kernel_unchanged_from_boot44':True,'service_library_path':None,'native_vendor_service_definition_retained':True}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n');(p/'work/core-boot/init.mrvl.rc').write_bytes(after)
system['paired_boot_sha256']=record['full_boot_sha256'];assert system['system_image_required_boot']=='android13-boot-v45'
(p/'artifacts/lineage20-rom-v38-gapps/host-verification.json').write_text(json.dumps(system,indent=2)+'\n')
print('BOOT45_NATIVE_SERVICE_OFFLINE_VERIFIED',record['full_boot_sha256'])
