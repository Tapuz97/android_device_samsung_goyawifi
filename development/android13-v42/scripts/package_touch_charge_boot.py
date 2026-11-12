"""Verify the linked touch repair and replace the kernel/module in the v28 boot."""
from pathlib import Path
import gzip, hashlib, json, struct, subprocess

p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
b=Path('/root/t110-build');out=b/'out-display-i2c'
e=p/'evidence/offline-v38';dest=p/'artifacts/android13-boot-v29'
sha=lambda v:hashlib.sha256(v).hexdigest()
record=json.loads((e/'source.json').read_text())
assert sha((b/'kernel-display-i2c'/record['source']).read_bytes())==record['after_sha256']
obj=out/'drivers/input/touchscreen/bt532_ts.o'
dis=subprocess.check_output([str(b/'toolchain/bin/arm-eabi-objdump'),'-dr',str(obj)],text=True)
init=dis.split('<bt532_ts_init>:',1)[1].split('\n\n',1)[0]
assert 'i2c_register_driver' in init and 'lpcharge' not in init and 'spa_lpm' not in init,init
(e/'touch-init-disassembly.txt').write_text(init+'\n')
assert (out/'.config').read_bytes()==(p/'artifacts/kernel-display-i2c/kernel.config').read_bytes()
log=(b/'logs/touch-charge-build.log').read_text(errors='replace')
assert 'Kernel: arch/arm/boot/zImage is ready' in log and 'error:' not in log
(e/'build.log').write_text(log)
kernel=(out/'arch/arm/boot/zImage').read_bytes()
modules=list(out.rglob('galcore.ko'));assert len(modules)==1
module=modules[0].read_bytes()
old=p/'artifacts/android13-full-v28'
meta=json.loads((old/'provenance.json').read_text())
image=(old/'KERNEL.img').read_bytes();assert sha(image)==meta['full_boot_sha256']
page=struct.unpack_from('<I',image,36)[0];assert page==2048
align=lambda v:v+bytes(-len(v)%page)
ksize=struct.unpack_from('<I',image,8)[0];rsize=struct.unpack_from('<I',image,16)[0]
start=page+len(align(image[page:page+ksize]));raw=gzip.decompress(image[start:start+rsize])
offset=0;entries=[];unchanged={};replaced=0
while offset+110<=len(raw):
    header=bytearray(raw[offset:offset+110]);assert header[:6]==b'070701'
    fields=[int(header[i:i+8],16) for i in range(6,110,8)]
    length,namesize=fields[6],fields[11];namebytes=raw[offset+110:offset+110+namesize]
    name=namebytes[:-1].decode();offset=(offset+110+namesize+3)&~3
    data=raw[offset:offset+length];offset=(offset+length+3)&~3
    if name=='lib/modules/galcore.ko':
        assert sha(data)==meta['module_sha256'];data=module;replaced+=1
        header[54:62]=f'{len(data):08x}'.encode()
    else:unchanged[name]=sha(data)
    entry=bytes(header)+namebytes;entry+=bytes(-len(entry)%4)
    entry+=data;entry+=bytes(-len(entry)%4);entries.append(entry)
    if name=='TRAILER!!!':break
assert replaced==1 and sha(kernel)!=meta['kernel_sha256']
rd=b''.join(entries);rd+=bytes(-len(rd)%512);rd=gzip.compress(rd,mtime=0)
header=bytearray(image[:page]);struct.pack_into('<I',header,8,len(kernel));struct.pack_into('<I',header,16,len(rd))
h=hashlib.sha1()
for data in [kernel,rd,b'']:h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12)
boot=bytes(header)+align(kernel)+align(rd);assert len(boot)<16777216
full=boot.ljust(16777216,b'\0');dest.mkdir(exist_ok=True)
(dest/'KERNEL.img').write_bytes(full)
result=dict(status='OFFLINE_VERIFIED',parent='../android13-full-v28',full_boot_sha256=sha(full),kernel_sha256=sha(kernel),module_sha256=sha(module),ramdisk_sha256=sha(rd),boot_image_bytes=len(boot),boot_partition_bytes=len(full),source=record,unchanged_ramdisk_files=unchanged,config_unchanged=True,linked_touch_init_ignores_lpcharge=True,hardware_validated=False)
(dest/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['unchanged_ramdisk_files','source']},indent=2))
