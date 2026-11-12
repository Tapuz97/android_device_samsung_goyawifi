"""Package the matched ION kernel and ADB init fixes; never flash from this script."""
from pathlib import Path
import json,hashlib,struct,gzip,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=Path('/root/t110-build')
e=p/'evidence/remote-fixes-20261110';old=p/'artifacts/android13-boot-v29';dest=p/'artifacts/android13-boot-v30'
sha=lambda b:hashlib.sha256(b).hexdigest()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')}
exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
image,kernel_old,rd_old,files,metadata,end=ns['unpack'](old/'KERNEL.img')
prov=json.loads((old/'provenance.json').read_text());assert sha(image)==prov['full_boot_sha256']
out=base/'out-display-i2c';log=(base/'logs/ion-map-build-20261110.log').read_text()
assert 'Kernel: arch/arm/boot/zImage is ready' in log and 'error:' not in log
assert (out/'.config').read_bytes()==(p/'artifacts/kernel-display-i2c/kernel.config').read_bytes()
kernel=(out/'arch/arm/boot/zImage').read_bytes();assert kernel!=kernel_old
modules=list(out.rglob('galcore.ko'));assert len(modules)==1
assert modules[0].read_bytes()==files['lib/modules/galcore.ko']
rc=(p/'work/core-boot/init.mrvl.rc').read_bytes()
expected=files['init.mrvl.rc'].replace(b'socket adbd stream 0660 system system',b'socket adbd seqpacket 0660 system system')
expected=expected.replace(b'    write /dev/t110-keepalive 1\n',b'''    write /dev/t110-keepalive 1
    # Early diagnostic ADB starts before derive_classpath/load_exports. Refresh
    # it after startup so Java shell tools inherit Android's final classpaths.
    restart adbd
''')
assert rc==expected,(sha(rc),sha(expected))
raw=gzip.decompress(rd_old);offset=0;records=[];count=0
while True:
    header=bytearray(raw[offset:offset+110]);assert header[:6]==b'070701'
    f=[int(header[i:i+8],16) for i in range(6,110,8)];size,namesize=f[6],f[11]
    namebytes=raw[offset+110:offset+110+namesize];name=namebytes[:-1].decode();offset=(offset+110+namesize+3)&~3
    data=raw[offset:offset+size];offset=(offset+size+3)&~3
    if name=='init.mrvl.rc':data=rc;count+=1;header[54:62]=f'{len(data):08x}'.encode()
    r=bytes(header)+namebytes;r+=bytes(-len(r)%4);r+=data;r+=bytes(-len(r)%4);records.append(r)
    if name=='TRAILER!!!':break
assert count==1
raw=b''.join(records);raw+=bytes(-len(raw)%512);rd=gzip.compress(raw,mtime=0)
page=2048;align=lambda b:b+bytes(-len(b)%page);header=bytearray(image[:page])
struct.pack_into('<I',header,8,len(kernel));struct.pack_into('<I',header,16,len(rd))
h=hashlib.sha1()
for data in [kernel,rd,b'']:h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12)
boot=bytes(header)+align(kernel)+align(rd);assert len(boot)<16777216
dest.mkdir(exist_ok=False);(dest/'KERNEL.img').write_bytes(boot.ljust(16777216,b'\0'))
new=ns['unpack'](dest/'KERNEL.img')
assert new[4]==metadata and set(new[3])==set(files)
assert [k for k in files if files[k]!=new[3][k]]==['init.mrvl.rc']
assert image[12:16]==new[0][12:16] and image[20:576]==new[0][20:576]
source=(base/'kernel-display-i2c/drivers/gpu/ion/ion.c').read_text();assert 'case ION_IOC_SHARE:\n\tcase ION_IOC_MAP:' in source
result={'status':'BUILT_PACKAGED_OFFLINE_VERIFIED_NOT_FLASHED','parent':'../android13-boot-v29','full_boot_sha256':sha(new[0]),'kernel_sha256':sha(kernel),'module_sha256':sha(new[3]['lib/modules/galcore.ko']),'boot_partition_bytes':len(new[0]),'boot_image_bytes':len(boot),'config_unchanged':True,'ramdisk_changed_files':['init.mrvl.rc'],'changes':['ION_IOC_MAP aliases ION_IOC_SHARE, matching common-3.4','ADB authentication socket uses standard seqpacket','Refresh early ADB runtime environment after boot'],'hardware_validated':False,'recovery_modified':False,'flashed':False}
(dest/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');(dest/'SHA256SUMS').write_text(sha(new[0])+'  KERNEL.img\n')
(e/'boot-v30-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
