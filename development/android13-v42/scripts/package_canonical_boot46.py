"""Preserve BOOT45 except bootstrap and two canonical read-only partition roots."""
from pathlib import Path
import gzip,hashlib,json,os,stat,struct,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
dest=p/'artifacts/android13-boot-v46';assert not dest.exists()
sha=lambda data:hashlib.sha256(data).hexdigest();ns={'__file__':str(p/'scripts/verify_v28_boot.py')}
exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
base=p/'artifacts/android13-boot-v45';old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text())
assert sha(old[0])==parent['full_boot_sha256'] and sha(old[3]['init'])==parent['stage_sha256']
source=p/'work/core-boot/stage.c';text=source.read_text()
begin=text.index('#ifdef T110_FULL_BOOT\n    /* ART stores class-loader paths')
end=text.index('#endif\n    checkpoint("Android system mounted");',begin)+len('#endif\n')
previous=text[:begin]+text[end:]
assert sha(previous.encode())==parent['stage_source_sha256'],'Unexpected unrelated bootstrap source edits'
dest.mkdir();stage=dest/'stage.init'
subprocess.run(['arm-linux-gnueabi-gcc','-static','-O2','-march=armv7-a','-std=gnu11','-Wall','-Wextra','-Werror','-DT110_FULL_BOOT',str(source),'-o',str(stage)],check=True)
payload=stage.read_bytes();assert payload[:6]==b'\x7fELF\1\1' and struct.unpack_from('<H',payload,18)[0]==40
raw=gzip.decompress(old[2]);offset=0;records=[];changed=[]
while True:
    h=bytearray(raw[offset:offset+110]);assert h[:6]==b'070701';fields=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=fields[6],fields[11]
    names=raw[offset+110:offset+110+namesize];name=names[:-1].decode();offset=(offset+110+namesize+3)&~3;body=raw[offset:offset+size];offset=(offset+size+3)&~3
    if name=='init':body=payload;changed.append(name)
    if name in ['product','system_ext']:
        assert stat.S_ISLNK(fields[1]) and body=={'product':b'/system/product','system_ext':b'/system/system_ext'}[name]
        h[14:22]=f'{stat.S_IFDIR|0o755:08x}'.encode();body=b'';changed.append(name)
    h[54:62]=f'{len(body):08x}'.encode()
    data=bytes(h)+names;data+=bytes(-len(data)%4);data+=body;data+=bytes(-len(data)%4);records.append(data)
    if name=='TRAILER!!!':break
assert sorted(changed)==['init','product','system_ext']
raw=b''.join(records);raw+=bytes(-len(raw)%512);ramdisk=gzip.compress(raw,mtime=0);kernel=old[1]
header=bytearray(old[0][:2048]);struct.pack_into('<I',header,16,len(ramdisk));digest=hashlib.sha1()
for data in [kernel,ramdisk,b'']:digest.update(data);digest.update(struct.pack('<I',len(data)))
header[576:608]=digest.digest()+bytes(12);align=lambda value:value+bytes(-len(value)%2048)
boot=bytes(header)+align(kernel)+align(ramdisk);assert len(boot)<16777216;full=boot.ljust(16777216,b'\0');(dest/'KERNEL.img').write_bytes(full)
new=ns['unpack'](dest/'KERNEL.img');assert new[1]==old[1] and set(new[3])==set(old[3])
assert sorted(key for key in old[3] if old[3][key]!=new[3][key])==sorted(changed)
for key in old[4]:
    if key not in ['product','system_ext']:assert old[4][key]==new[4][key]
    else:
        before=list(old[4][key]);after=list(new[4][key]);assert stat.S_ISDIR(after[1]) and stat.S_IMODE(after[1])==0o755
        before[1]=after[1];assert before==after
system=json.loads((p/'artifacts/lineage20-rom-v40-gapps/host-verification.json').read_text())
record={**parent,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent':'../android13-boot-v45','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),
        'ramdisk_changed_files':changed,'stage_sha256':sha(payload),'stage_source_sha256':sha(source.read_bytes()),'boot_image_bytes':len(boot),
        'kernel_unchanged_from_boot45':True,'paired_system_sha256':system['sha256'],'system_image_required':'lineage20-rom-v40-gapps',
        'canonical_partition_roots':['/product','/system_ext'],'read_only_source_preserved':True,'hardware_validated':False}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n');print('BOOT46_CANONICAL_ROOTS_OFFLINE_VERIFIED',record['full_boot_sha256'],flush=True)
