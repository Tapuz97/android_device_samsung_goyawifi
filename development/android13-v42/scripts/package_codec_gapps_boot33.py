"""Build a metadata-preserving BOOT pair for codec/swap fixes and Google loop size."""
from pathlib import Path
import gzip,hashlib,json,shutil,struct,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build')
e=p/'evidence/offline-v41';base=p/'artifacts/android13-boot-v32';dest=p/'artifacts/android13-boot-v33'
kdir=p/'artifacts/kernel-reboot-alias';out=b/'out-display-i2c';src=b/'kernel-display-i2c'
assert not dest.exists() and not kdir.exists()
sha=lambda data:hashlib.sha256(data).hexdigest()
source=json.loads((e/'reboot-alias-source.json').read_text())
assert sha((src/'arch/arm/mach-mmp/board-goya.c').read_bytes())==source['sha256']
assert sha((out/'.config').read_bytes())=='144712c4c94a79619da5cdaabcc5e530724ede0f51b42b3accbfa8a4b81c792d'
assert sha((src/'drivers/input/touchscreen/bt532_ts.c').read_bytes())=='1a4706eafa67cdf68e5b08ca10c683d07e87910cae439d974715bbf9a0623484'
assert sha((src/'drivers/gpu/ion/ion_system_heap.c').read_bytes())=='4f478578deace498db5cb2a2004b2d5d4dc784c3b3e65bc9d47ed228282ab419'
kernel=(out/'arch/arm/boot/zImage').read_bytes();modules=list(out.rglob('galcore.ko'));assert len(modules)==1
module=modules[0].read_bytes()
assert sha(module)=='0d93682f6a54f51aabfd7c91ab77af0b26c61c86aa8e8519c487c70d7f5c3900'
stage=e/'boot33-stage.init'
subprocess.run(['arm-linux-gnueabi-gcc','-static','-O2','-march=armv7-a','-std=gnu11','-Wall','-Wextra','-Werror','-DT110_FULL_BOOT',str(p/'work/core-boot/stage.c'),'-o',str(stage)],check=True)
policy=(e/'system-v29-sepolicy.bin').read_bytes();assert len(policy)>500000
fstab=(p/'work/core-boot/fstab.t110.zram').read_bytes()
assert 'zramsize=536870912,max_comp_streams=-1' in fstab.decode()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text())
assert sha(old[0])==parent['full_boot_sha256']
replacements={'init':stage.read_bytes(),'t110-preload-policy':policy,'fstab.t110.zram':fstab}
assert old[3]['init.mrvl.rc']==(p/'work/core-boot/init.mrvl.rc').read_bytes()
raw=gzip.decompress(old[2]);offset=0;records=[];seen=set()
while True:
    h=bytearray(raw[offset:offset+110]);assert h[:6]==b'070701'
    fields=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=fields[6],fields[11]
    names=raw[offset+110:offset+110+namesize];name=names[:-1].decode();offset=(offset+110+namesize+3)&~3
    data=raw[offset:offset+size];offset=(offset+size+3)&~3
    if name in replacements:data=replacements[name];h[54:62]=f'{len(data):08x}'.encode();seen.add(name)
    record=bytes(h)+names;record+=bytes(-len(record)%4);record+=data;record+=bytes(-len(record)%4);records.append(record)
    if name=='TRAILER!!!':break
assert seen==set(replacements)
raw=b''.join(records);raw+=bytes(-len(raw)%512);rd=gzip.compress(raw,mtime=0)
page=2048;align=lambda data:data+bytes(-len(data)%page);header=bytearray(old[0][:page])
struct.pack_into('<I',header,8,len(kernel));struct.pack_into('<I',header,16,len(rd))
h=hashlib.sha1()
for data in [kernel,rd,b'']:h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12);boot=bytes(header)+align(kernel)+align(rd)
assert len(boot)<16777216;full=boot.ljust(16777216,b'\0')
dest.mkdir();(dest/'KERNEL.img').write_bytes(full);new=ns['unpack'](dest/'KERNEL.img')
assert new[4]==old[4] and set(new[3])==set(old[3])
changed=[n for n in old[3] if old[3][n]!=new[3][n]]
assert set(changed)==set(replacements) and new[1]==kernel
assert new[0][12:16]==old[0][12:16] and new[0][20:576]==old[0][20:576]
kdir.mkdir()
for f,name in [(out/'arch/arm/boot/zImage','zImage'),(modules[0],'galcore.ko'),(out/'.config','kernel.config'),(b/'logs/display-i2c-build.log','kernel-build.log')]:shutil.copyfile(f,kdir/name)
record={'status':'OFFLINE_VERIFIED_NOT_INSTALLED','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),
 'kernel_sha256':sha(kernel),'module_sha256':sha(module),'bootstrap_policy_sha256':sha(policy),
 'stage_sha256':sha(stage.read_bytes()),'stage_source_sha256':sha((p/'work/core-boot/stage.c').read_bytes()),
 'ramdisk_changed_files':changed,'ramdisk_metadata_preserved':True,'supported_loop_sizes':[1594884096,2146435072],
 'zram_logical_bytes':536870912,'zram_missing_control_skipped':True,'kernel_reboot_alias':'bootloader -> download',
 'boot_partition_bytes':16777216,'recovery_untouched':True,'hardware_validated':False}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n');(kdir/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
(e/'boot-v33-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print('BOOT33_OFFLINE_VERIFIED',record['full_boot_sha256'])
