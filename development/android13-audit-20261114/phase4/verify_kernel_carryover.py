from pathlib import Path
import gzip
import hashlib
import json
import struct
import subprocess
import zlib

base=Path('/root/t110-lineage14')
dev=base/'android/device/samsung/goyawifi'
source=base/'reference/current-private/artifacts/android13-boot-v48/KERNEL.img'
boot=source.read_bytes();page=struct.unpack_from('<I',boot,36)[0]
oldkernel=boot[page:page+struct.unpack_from('<I',boot,8)[0]]
kernel=(dev/'prebuilt/zImage').read_bytes()
record=json.loads((dev/'kernel-source.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(boot)=='09da369cd22d09e1b59b70ce273fa305c96cc83bc83bca8a48132737763d3690'
assert sha(kernel)==record['kernel_sha256']=='df1f3245e750c207e17c0ac1063ac0e13c48f3c468249285bb281f7c5043766a'
def config(data):
    # Same extraction used by the14.1 audit: IKCONFIG is inside compressed
    # vmlinux, not normally visible in the outer ARM zImage container.
    if b'IKCFG_ST\x1f\x8b' not in data:
        data=zlib.decompress(data[data.index(b'\x1f\x8b\x08'):],16+zlib.MAX_WBITS)
    i=data.index(b'IKCFG_ST\x1f\x8b')+8
    return zlib.decompress(data[i:],16+zlib.MAX_WBITS)
assert config(kernel)==config(oldkernel)
assert sha(config(kernel))==record['config_sha256']
changed=subprocess.check_output(['git','-C',str(base/'kernel-initramfs-source'),'diff','--name-only',
    record['baseline_commit'],record['source_commit']],text=True).splitlines()
assert changed==['init/initramfs.c'],changed
ksize=struct.unpack_from('<I',boot,8)[0];rsize=struct.unpack_from('<I',boot,16)[0]
offset=page+((ksize+page-1)//page)*page
raw=gzip.decompress(boot[offset:offset+rsize]);cursor=0;module=None
while True:
    assert raw[cursor:cursor+6]==b'070701'
    fields=[int(raw[n:n+8],16) for n in range(cursor+6,cursor+110,8)]
    name=raw[cursor+110:cursor+110+fields[11]-1].decode();cursor=(cursor+110+fields[11]+3)&~3
    data=raw[cursor:cursor+fields[6]];cursor=(cursor+fields[6]+3)&~3
    if name=='lib/modules/galcore.ko':module=data
    if name=='TRAILER!!!':break
assert module==(dev/'prebuilt/galcore.ko').read_bytes()
current=(base/'artifacts/lineage14-first-build/boot.img').read_bytes()
current_page=struct.unpack_from('<I',current,36)[0]
assert current[current_page:current_page+len(kernel)]==kernel
result=dict(status='PASS',old13_kernel_sha256=sha(oldkernel),candidate_kernel_sha256=sha(kernel),
    same_embedded_config=True,config_sha256=sha(config(kernel)),matched_galcore_sha256=sha(module),
    changed_kernel_files=changed,source=record,working14_images_modified=False,
    current14_boot_uses_this_kernel=True,android13_hardware_tested=False,
    selected_config_lines=[line for line in config(kernel).decode().splitlines()
        if any(n in line for n in ('CONFIG_CMDLINE','CONFIG_ANDROID_BINDER','CONFIG_SECURITY_SELINUX_POLICYDB_VERSION'))])
Path('/root/t110-android13-audit/kernel-carryover-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: proven14 kernel adds only initramfs archive fix; embedded13 config and GPU module match exactly.')
print('\n'.join(result['selected_config_lines']))
