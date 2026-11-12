"""Keep BOOT46's ramdisk/modules; replace its kernel with qualified standard reclaim."""
from pathlib import Path
import hashlib,json,struct
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112'
sha=lambda data:hashlib.sha256(data).hexdigest()
kernel_meta=json.loads((e/'kernel-standard-reclaim.json').read_text());assert kernel_meta['status']=='KERNEL_COMPILED_MODULE_QUALIFICATION_PENDING'
assert json.loads((e/'qemu-standard-reclaim.json').read_text())['status']=='PASS'
equivalence=json.loads((p/'evidence/hardware-v35/module-equivalence-standard-reclaim-installed.json').read_text())
assert len(equivalence)==4 and all(row['status']=='ALLOC_AND_RELOCATIONS_IDENTICAL' for row in equivalence.values())
assert equivalence['drivers/marvell/sd8787/mbtc_src/mbt8xxx.ko']['old_file_sha256']=='9d66b073e388ceebad4dca45ecebcb271f626bf6b30b254c09ce3f51874ab45d'
system=json.loads((p/'artifacts/lineage20-rom-v40-gapps/host-verification.json').read_text())
for filename in ['mlan.ko','sd8xxx.ko']:
    module=next(value for name,value in equivalence.items() if name.endswith('/'+filename))
    assert module['old_file_sha256']==system['native_components_unchanged']['system/vendor/etc/wifi/modules/'+filename]
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
parent=p/'artifacts/android13-boot-v46';dest=p/'artifacts/android13-boot-v47';assert not dest.exists()
old=ns['unpack'](parent/'KERNEL.img');meta=json.loads((parent/'provenance.json').read_text());assert sha(old[0])==meta['full_boot_sha256']
kernel=(e/'standard-reclaim-components/zImage').read_bytes();config=(e/'standard-reclaim-components/kernel.config').read_bytes()
assert sha(kernel)==kernel_meta['kernel_sha256'] and sha(config)==kernel_meta['config_sha256']
assert kernel!=old[1] and b'CONFIG_ZRAM=y\n' in config and b'CONFIG_ZRAM_FOR_ANDROID=y\n' not in config and b'CONFIG_ZRAM_FOR_RTCC2=y\n' not in config
page=2048;align=lambda data:data+bytes(-len(data)%page);header=bytearray(old[0][:page]);struct.pack_into('<I',header,8,len(kernel));digest=hashlib.sha1()
for data in [kernel,old[2],b'']:digest.update(data);digest.update(struct.pack('<I',len(data)))
header[576:608]=digest.digest()+bytes(12);boot=bytes(header)+align(kernel)+align(old[2]);assert len(boot)<16777216
full=boot.ljust(16777216,b'\0');dest.mkdir();(dest/'KERNEL.img').write_bytes(full);new=ns['unpack'](dest/'KERNEL.img')
assert new[1]==kernel and new[2:5]==old[2:5]
record={key:value for key,value in meta.items() if not key.startswith('kernel_unchanged_from')}
record.update(status='OFFLINE_VERIFIED_AWAITING_SYSTEM_PAIR',parent='../android13-boot-v46',full_boot_sha256=sha(full),full_boot_md5=hashlib.md5(full).hexdigest(),
              kernel_sha256=sha(kernel),kernel_config_sha256=sha(config),kernel_variant='gateway-standard-reclaim',
              kernel_changed_from_boot46=True,ramdisk_changed_files=[],ramdisk_bytes_unchanged=True,boot_image_bytes=len(boot),
              system_image_required='lineage20-rom-v41-gapps',paired_system_sha256=None,hardware_validated=False,
              standard_reclaim_enabled=True,legacy_android_idle_reclaim_disabled=True,module_equivalence_verified=True,
              swap_pressure_arm_qemu='evidence/ui-system-hang-20261112/qemu-standard-reclaim.json')
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
kernel_meta.update(status='OFFLINE_KERNEL_AND_MODULES_QUALIFIED',modules_verified=True,arm_swap_pressure_passed=True)
(e/'kernel-standard-reclaim.json').write_text(json.dumps(kernel_meta,indent=2)+'\n');print('BOOT47_STANDARD_RECLAIM_OFFLINE_VERIFIED',record['full_boot_sha256'])
