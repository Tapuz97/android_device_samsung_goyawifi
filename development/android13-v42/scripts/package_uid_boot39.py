"""Package the tested networking kernel; retain BOOT38's entire ramdisk."""
from pathlib import Path
import argparse,hashlib,json,struct
parser=argparse.ArgumentParser();parser.add_argument('--netd-targets',action='store_true');args=parser.parse_args()
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
b=Path('/root/t110-build');out=b/('out-netd-targets' if args.netd_targets else 'out-uid-routing');e=p/'evidence/hardware-v35'
sha=lambda data:hashlib.sha256(data).hexdigest()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')}
exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
number=40 if args.netd_targets else 39
base=p/f'artifacts/android13-boot-v{number-1}';dest=p/f'artifacts/android13-boot-v{number}'
assert not dest.exists(),'Do not overwrite a packaged candidate'
old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text())
expected_parent='33462a6a2cffc1695ac8d8f986d42eac13b12b0708a5eb9db26f66c9baa73701' if args.netd_targets else 'b5bab81d2693d3b8b3e479963275173c938b3110e3110fa20489f72cae5694c5'
assert sha(old[0])==parent['full_boot_sha256']==expected_parent
expected_config=json.loads((e/'netd-targets-source.json').read_text())['candidate_config_sha256'] if args.netd_targets else '144712c4c94a79619da5cdaabcc5e530724ede0f51b42b3accbfa8a4b81c792d'
assert sha((out/'.config').read_bytes())==expected_config
kernel=(out/'arch/arm/boot/zImage').read_bytes()
assert sha(kernel)==(e/('compiled-kernel-netd-targets.txt' if args.netd_targets else 'compiled-kernel.txt')).read_text().split()[0] and kernel!=old[1]
assert 'UID_ROUTING_REGRESSION_PASS tests=71 failed=0' in (e/'uid-qemu.log').read_text(errors='replace')
source=json.loads((e/'uid-source.json').read_text())
for item in source['files']:
    assert sha((b/'kernel-display-i2c'/item['path']).read_bytes())==item['after_sha256']
if args.netd_targets:
    virtual=(e/'netd-targets-qemu.log').read_text(errors='replace')
    assert 'NETD_TARGET_PROBE_PASS checks=10 failed=0' in virtual and 'UID_ROUTING_REGRESSION_PASS tests=71 failed=0' in virtual
equivalence=json.loads((e/('module-equivalence-netd.json' if args.netd_targets else 'module-equivalence.json')).read_text())
assert len(equivalence)==4 and all(row['status']=='ALLOC_AND_RELOCATIONS_IDENTICAL' for row in equivalence.values())
assert equivalence['drivers/marvell/graphics/galcore_src/galcore.ko']['old_file_sha256']==sha(old[3]['lib/modules/galcore.ko'])
page=2048;align=lambda data:data+bytes(-len(data)%page)
header=bytearray(old[0][:page]);struct.pack_into('<I',header,8,len(kernel))
h=hashlib.sha1()
for data in (kernel,old[2],b''):h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12)
boot=bytes(header)+align(kernel)+align(old[2]);assert len(boot)<16777216
full=boot.ljust(16777216,b'\0');dest.mkdir();(dest/'KERNEL.img').write_bytes(full)
new=ns['unpack'](dest/'KERNEL.img')
assert new[1]==kernel and new[2]==old[2] and new[3]==old[3] and new[4]==old[4]
record={**parent,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent':f'../android13-boot-v{number-1}',
 'full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),
 'kernel_sha256':sha(kernel),'ramdisk_changed_files':[],'ramdisk_bytes_unchanged':True,
 'kernel_variant':'netd-targets' if args.netd_targets else 'uid-routing','uid_routing_patch_sha256':sha((p/'patches/0095-kernel-modern-uid-routing.patch').read_bytes()),
 'packet_target_qemu_checks':10 if args.netd_targets else 0,'kernel_config_sha256':expected_config,
 'uid_qemu_regression_tests':71,'uid_qemu_regression_failures':0,'module_equivalence_verified':True,
 'system_image_required':'lineage20-rom-v34-gapps','system_image_changed':False,
 'boot_image_bytes':len(boot),'hardware_validated':False}
(dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
(e/('netd-targets-qemu-result.json' if args.netd_targets else 'uid-qemu-result.json')).write_text(json.dumps({'status':'PASS','tests':81 if args.netd_targets else 71,'failed':0,
 'log_sha256':sha((e/('netd-targets-qemu.log' if args.netd_targets else 'uid-qemu.log')).read_bytes()),'source_files':source['files'],
 'limitations':'Isolated Linux routing regression; not physical Wi-Fi, Internet, VPN certification or Android app verification.'},indent=2)+'\n')
print(f'BOOT{number}_OFFLINE_VERIFIED',record['full_boot_sha256'])
