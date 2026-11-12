"""Replace only kernel/module in verified v27 boot; no device or emulator IO."""
from pathlib import Path
import gzip,hashlib,json,struct
p=Path(__file__).resolve().parents[1]
old=p/'artifacts/android13-full-v27'; dest=p/'artifacts/android13-full-v28'
kernel=p/'artifacts/kernel-display-i2c'; prov=json.loads((kernel/'provenance.json').read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
newkernel=(kernel/'zImage').read_bytes(); module=(kernel/'galcore.ko').read_bytes()
assert sha(newkernel)==prov['files']['zImage']['sha256']
assert sha(module)==prov['files']['galcore.ko']['sha256']
image=(old/'KERNEL.img').read_bytes(); oldprov=json.loads((old/'provenance.json').read_text())
assert sha(image)==oldprov['full_boot_sha256']
ksize=struct.unpack_from('<I',image,8)[0]; rsize=struct.unpack_from('<I',image,16)[0]
page=struct.unpack_from('<I',image,36)[0]; assert page==2048
align=lambda data:data+bytes(-len(data)%page)
start=page+len(align(image[page:page+ksize])); rd=gzip.decompress(image[start:start+rsize])
offset=0; entries=[]; files={}; replaced=0
while offset+110<=len(rd):
    header=bytearray(rd[offset:offset+110]); assert header[:6]==b'070701'
    fields=[int(header[i:i+8],16) for i in range(6,110,8)]
    length,namesize=fields[6],fields[11]; namebytes=rd[offset+110:offset+110+namesize]
    name=namebytes[:-1].decode(); offset=(offset+110+namesize+3)&~3
    data=rd[offset:offset+length]; offset=(offset+length+3)&~3
    files[name]=data
    if name=='lib/modules/galcore.ko':
        assert sha(data)==oldprov['module_sha256']; data=module; replaced+=1
        header[54:62]=f'{len(data):08x}'.encode()
    record=bytes(header)+namebytes; record+=bytes(-len(record)%4)
    record+=data; record+=bytes(-len(record)%4);entries.append(record)
    if name=='TRAILER!!!':break
assert replaced==1
assert files['init.environ.rc']==(p/'work/core-boot/init.environ.rc').read_bytes()
assert files['init.mrvl.rc']==(p/'work/core-boot/init.mrvl.rc').read_bytes()
assert sha(files['t110-preload-policy'])==oldprov['bootstrap_policy_sha256']
raw=b''.join(entries);raw+=bytes(-len(raw)%512); newrd=gzip.compress(raw,mtime=0)
header=bytearray(image[:page]);struct.pack_into('<I',header,8,len(newkernel));struct.pack_into('<I',header,16,len(newrd))
h=hashlib.sha1()
for data in [newkernel,newrd,b'']:h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12)
boot=bytes(header)+align(newkernel)+align(newrd); assert len(boot)<16777216
full=boot.ljust(16777216,b'\0');dest.mkdir(exist_ok=False)
for name,data in {'boot.img':boot,'KERNEL.img':full,'ramdisk.cpio.gz':newrd}.items():(dest/name).write_bytes(data)
oldprov.update(status='PACKAGED_OFFLINE_NOT_BOOT_TESTED',kernel_sha256=sha(newkernel),module_sha256=sha(module),
    ramdisk_sha256=sha(newrd),full_boot_sha256=sha(full),full_boot_md5=hashlib.md5(full).hexdigest(),
    boot_image_bytes=len(boot),boot_partition_bytes=len(full),parent='../android13-full-v27',
    modifications=['Keep shared GOYA I2C pins active on framebuffer blank without early suspend','Matching rebuilt galcore module'],
    unchanged_ramdisk_files={name:sha(data) for name,data in files.items() if name not in ['lib/modules/galcore.ko','TRAILER!!!']})
oldprov.pop('qemu_ramdisk_sha256',None);oldprov.pop('reused_from',None);oldprov.pop('reason',None)
(dest/'provenance.json').write_text(json.dumps(oldprov,indent=2)+'\n')
(dest/'SHA256SUMS').write_text(''.join(sha((dest/n).read_bytes())+'  '+n+'\n' for n in ['boot.img','KERNEL.img','ramdisk.cpio.gz']))
print('Packaged v28 display I2C kernel/module; other ramdisk contents preserved')

pair=dict(boot_sha256=sha(full),boot_md5=hashlib.md5(full).hexdigest(),module_sha256=sha(module),bootstrap_policy_sha256=oldprov['bootstrap_policy_sha256'],status='PACKAGED_NOT_BOOT_TESTED')
(dest/'system-pair.json').write_text(json.dumps(pair,indent=2)+'\n')
