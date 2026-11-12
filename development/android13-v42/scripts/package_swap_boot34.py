"""Package a T110 boot image with the verified Android preload policy."""
from pathlib import Path
import argparse,gzip,hashlib,json,struct
parser=argparse.ArgumentParser()
parser.add_argument('--combined',action='store_true')
parser.add_argument('--revision',type=int,default=31)
options=parser.parse_args()
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41/swap-label-fix'
assert options.revision in (31,32,33,34)
parent_number=options.revision+3 if options.combined else 33
if options.combined and options.revision==33:
    parent_number=35  # v32/BOOT36 was superseded before installation.
base=p/f'artifacts/android13-boot-v{parent_number}'
boot_number=options.revision+4 if options.combined else 34
dest=p/f'artifacts/android13-boot-v{boot_number}'
assert not dest.exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
old=ns['unpack'](base/'KERNEL.img');parent=json.loads((base/'provenance.json').read_text());assert sha(old[0])==parent['full_boot_sha256']
kernel=old[1]
if options.combined:
    product=Path(r'\\wsl.localhost\T110Build\root\t110-build\out-system\target\product\t110_bringup')
    out=Path(r'\\wsl.localhost\Ubuntu\root\t110-build\out-display-i2c')
    src=out.parent/'kernel-display-i2c'
    policy=(product/'root/sepolicy').read_bytes()
    assert policy==(product/'system/vendor/etc/selinux/precompiled_sepolicy').read_bytes()
    system=json.loads((p/f'artifacts/lineage20-rom-v{options.revision}-gapps/host-verification.json').read_text())
    assert sha(policy)==system['bootstrap_policy_sha256']
    kernel=(out/'arch/arm/boot/zImage').read_bytes()
    report=(p/'evidence/stock-radio-reference/compiled-kernel.txt').read_text().splitlines()
    assert sha(kernel)==report[0].split()[0]
    assert options.revision!=31 or kernel!=old[1]
    assert sha((out/'.config').read_bytes())==report[1].split()[0]=='144712c4c94a79619da5cdaabcc5e530724ede0f51b42b3accbfa8a4b81c792d'
    assert (out/'drivers/marvell/graphics/galcore_src/galcore.ko').read_bytes()==old[3]['lib/modules/galcore.ko']
    alias=json.loads((p/'evidence/offline-v41/reboot-alias-source.json').read_text())
    assert sha((src/'arch/arm/mach-mmp/board-goya.c').read_bytes())==alias['sha256']
    assert b'NLA_PUT(msg, NL80211_ATTR_MAC, ETH_ALEN, dev->dev_addr);' in (src/'net/wireless/nl80211.c').read_bytes()
    replacements={} if policy==old[3]['t110-preload-policy'] else {'t110-preload-policy':policy}
else:
    policy=(e/'root/sepolicy').read_bytes()
    rc=(p/'work/core-boot/init.mrvl.rc').read_bytes()
    assert b'    restorecon /dev/block/zram0\n    swapon_all /fstab.t110.zram\n' in rc
    assert b'    write /proc/sys/vm/swappiness 100\n    write /proc/sys/vm/page-cluster 0\n' in rc
    replacements={'t110-preload-policy':policy,'init.mrvl.rc':rc}
assert len(policy)>500000 and (policy!=old[3]['t110-preload-policy'] or options.revision>=34)
raw=gzip.decompress(old[2]);offset=0;records=[];seen=set()
while True:
    h=bytearray(raw[offset:offset+110]);assert h[:6]==b'070701'
    f=[int(h[i:i+8],16) for i in range(6,110,8)];size,namesize=f[6],f[11]
    names=raw[offset+110:offset+110+namesize];name=names[:-1].decode();offset=(offset+110+namesize+3)&~3
    data=raw[offset:offset+size];offset=(offset+size+3)&~3
    if name in replacements:data=replacements[name];h[54:62]=f'{len(data):08x}'.encode();seen.add(name)
    r=bytes(h)+names;r+=bytes(-len(r)%4);r+=data;r+=bytes(-len(r)%4);records.append(r)
    if name=='TRAILER!!!':break
assert seen==set(replacements)
raw=b''.join(records);raw+=bytes(-len(raw)%512);rd=gzip.compress(raw,mtime=0)
page=2048;align=lambda b:b+bytes(-len(b)%page);header=bytearray(old[0][:page])
struct.pack_into('<I',header,8,len(kernel));struct.pack_into('<I',header,16,len(rd))
h=hashlib.sha1()
for data in [kernel,rd,b'']:h.update(data);h.update(struct.pack('<I',len(data)))
header[576:608]=h.digest()+bytes(12);boot=bytes(header)+align(kernel)+align(rd);assert len(boot)<16777216
full=boot.ljust(16777216,b'\0');dest.mkdir();(dest/'KERNEL.img').write_bytes(full);new=ns['unpack'](dest/'KERNEL.img')
assert new[1]==kernel and new[4]==old[4] and set(new[3])==set(old[3])
changed=[n for n in old[3] if old[3][n]!=new[3][n]];assert set(changed)==set(replacements)
result={**parent,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent':f'../android13-boot-v{parent_number}','full_boot_sha256':sha(full),'full_boot_md5':hashlib.md5(full).hexdigest(),'kernel_sha256':sha(kernel),'bootstrap_policy_sha256':sha(policy),'ramdisk_changed_files':changed,'standard_swap_label':'swap_block_device','swappiness':100,'page_cluster':0,'boot_image_bytes':len(boot),'boot_partition_bytes':16777216,'hardware_validated':False}
(dest/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(f'BOOT{boot_number}_OFFLINE_VERIFIED',result['full_boot_sha256'])
