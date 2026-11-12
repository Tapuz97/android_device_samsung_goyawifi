"""Package the regression-verified gateway kernel using BOOT40's exact ramdisk."""
from pathlib import Path
import hashlib,json,struct
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-v35';b=Path('/root/t110-build');out=b/'out-gateway'
sha=lambda v:hashlib.sha256(v).hexdigest()
source=json.loads((e/'gateway-source.json').read_text())
assert sha((b/'kernel-display-i2c'/source['path']).read_bytes())==source['after_sha256']
for file,pattern in [('gateway-corrected-qemu.log','GATEWAY_ROUTE_REGRESSION_PASS tests=11 failed=0'),('gateway-netd-qemu.log','UID_ROUTING_REGRESSION_PASS tests=71 failed=0'),('gateway-netd-qemu.log','NETD_TARGET_PROBE_PASS checks=10 failed=0')]:
 assert pattern in (e/file).read_text(errors='replace'),file
assert 'gateway-validated-in-explicit-network-table FAIL' in (e/'gateway-baseline-qemu.log').read_text(errors='replace')
equivalence=json.loads((e/'module-equivalence-gateway.json').read_text());assert len(equivalence)==4
for row in equivalence.values():assert row['status']=='ALLOC_AND_RELOCATIONS_IDENTICAL'
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
parent=p/'artifacts/android13-boot-v40';dest=p/'artifacts/android13-boot-v41';assert not dest.exists()
old=ns['unpack'](parent/'KERNEL.img');meta=json.loads((parent/'provenance.json').read_text())
assert sha(old[0])==meta['full_boot_sha256']=='7b49a9475c2083cebb3bddd2d121e0b7f309c115db1f020417cd4c139652fa52'
kernel=(out/'arch/arm/boot/zImage').read_bytes()
assert sha(kernel)==(e/'compiled-kernel-gateway.txt').read_text().split()[0] and kernel!=old[1]
assert sha((out/'.config').read_bytes())==meta['kernel_config_sha256']
page=2048;align=lambda data:data+bytes(-len(data)%page)
header=bytearray(old[0][:page]);struct.pack_into('<I',header,8,len(kernel));digest=hashlib.sha1()
for data in (kernel,old[2],b''):digest.update(data);digest.update(struct.pack('<I',len(data)))
header[576:608]=digest.digest()+bytes(12);boot=bytes(header)+align(kernel)+align(old[2]);assert len(boot)<16777216
full=boot.ljust(16777216,b'\0');dest.mkdir();(dest/'KERNEL.img').write_bytes(full)
new=ns['unpack'](dest/'KERNEL.img');assert new[1]==kernel and new[2:]==old[2:]
record={**meta,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent':'../android13-boot-v40',
 'full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),'kernel_sha256':sha(kernel),
 'kernel_variant':'gateway-table-lookup','gateway_qemu_tests':11,'gateway_qemu_failures':0,
 'gateway_source_sha256':source['after_sha256'],'gateway_patch_sha256':sha((p/'patches/0097-kernel-explicit-table-gateway-validation.patch').read_bytes()),
 'system_image_required':'lineage20-rom-v35-gapps','system_image_changed':True,'boot_image_bytes':len(boot),'hardware_validated':False}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
print('BOOT41_OFFLINE_VERIFIED',record['full_boot_sha256'])
