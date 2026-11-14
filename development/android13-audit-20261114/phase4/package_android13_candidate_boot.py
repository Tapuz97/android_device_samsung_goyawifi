"""Prepare a matching13 boot only after complete-image/namespace verification.

Reuse the established14.1 packaging layout and kernel archive fix while keeping
the13 bootstrap, module, data paths, logging and memory setup. Never flash.
"""
from pathlib import Path
import gzip
import hashlib
import json
import stat
import struct

audit=Path('/root/t110-android13-audit');dest=audit/'complete-image'
image=json.loads((audit/'complete-image-verification.json').read_text())
ns=json.loads((audit/'production-namespace-verification.json').read_text())
carry=json.loads((audit/'kernel-carryover-verification.json').read_text())
policy_checks=json.loads((audit/'complete-image-policy-verification.json').read_text())
assert image['status']==ns['status']==carry['status']==policy_checks['status']=='PASS'
assert ns['image_sha256']==image['raw_image_sha256']
source=Path('/root/t110-lineage14/reference/current-private/artifacts/android13-boot-v48/KERNEL.img')
old=source.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(old)=='09da369cd22d09e1b59b70ce273fa305c96cc83bc83bca8a48132737763d3690'
page=struct.unpack_from('<I',old,36)[0];ksize=struct.unpack_from('<I',old,8)[0]
rsize=struct.unpack_from('<I',old,16)[0];offset=page+((ksize+page-1)//page)*page
assert page==2048 and struct.unpack_from('<I',old,24)[0]==0 and struct.unpack_from('<I',old,40)[0]==0

def records(data):
    cursor=0
    while True:
        assert data[cursor:cursor+6]==b'070701'
        fields=[int(data[n:n+8],16) for n in range(cursor+6,cursor+110,8)]
        name=data[cursor+110:cursor+110+fields[11]-1].decode()
        cursor=(cursor+110+fields[11]+3)&~3
        body=data[cursor:cursor+fields[6]];cursor=(cursor+fields[6]+3)&~3
        if name=='TRAILER!!!':return
        yield name,fields,body

def entry(name,fields,body):
    values=list(fields);values[6]=len(body);values[11]=len(name.encode())+1
    blob=b'070701'+b''.join(('%08x'%x).encode() for x in values)+name.encode()+b'\0'
    blob+=bytes(-len(blob)%4);blob+=body;blob+=bytes(-len(blob)%4)
    return blob

original={n:(f,b) for n,f,b in records(gzip.decompress(old[offset:offset+rsize]))}
items=dict(original)
policy=(dest/'extracted/system/vendor/etc/selinux/precompiled_sepolicy').read_bytes()
assert 0<len(policy)<2*1024*1024
name_len=struct.unpack_from('<I',policy,4)[0]
policy_version=struct.unpack_from('<I',policy,8+name_len)[0]
assert policy_version==30,policy_version
fields,_=items['t110-preload-policy'];items['t110-preload-policy']=(fields,policy)
fields,rc=items['init.mrvl.rc'];text=rc.decode()
old_gpu='    # Keep normal windows on the validated path while GPU presentation is repaired.\n    setprop debug.hwui.t110_window_gpu false\n'
new_gpu='''    # Full HWUI/EGL window compatibility is built into this candidate.
    # Setting this property false still selects the retained Canvas fallback.
    setprop debug.hwui.t110_window_gpu true
    # Same exact-device access fix qualified in14.1; Android13 also places the
    # actual node under /dev/graphics. The standard vendor ueventd rule agrees.
    symlink /dev/graphics/galcore /dev/galcore
    chown system graphics /dev/graphics/galcore
    chmod 0666 /dev/graphics/galcore
    restorecon /dev/graphics/galcore
'''
assert text.count(old_gpu)==1
text=text.replace(old_gpu,new_gpu)
assert 'start t110-logcat' not in text
for retained in ('write /proc/sys/vm/swappiness 100','write /proc/sys/vm/page-cluster 0',
                 'swapon_all /fstab.t110.zram','    start adbd\n','    trigger nonencrypted\n'):
    assert retained in text,retained
items['init.mrvl.rc']=(fields,text.encode())
fields,rules=items['ueventd.mrvl.rc']
if b'/dev/graphics/galcore 0666 system graphics' not in rules:
    rules+=b'\n/dev/graphics/galcore 0666 system graphics\n'
items['ueventd.mrvl.rc']=(fields,rules)
for name in ('product','system_ext','system','stage-data','data'):
    assert stat.S_ISDIR(items[name][0][1]),name
assert items['init'][1]==original['init'][1] and b'/stage-data/local/tmp/t110-stage-system.raw' in items['init'][1]
assert sha(items['lib/modules/galcore.ko'][1])==carry['matched_galcore_sha256']
kernel=Path('/root/t110-lineage14/android/device/samsung/goyawifi/prebuilt/zImage').read_bytes()
assert sha(kernel)==carry['candidate_kernel_sha256']
raw=b''.join(entry(n,f,b) for n,(f,b) in sorted(items.items()))
raw+=entry('TRAILER!!!',[0,0,0,0,1,0,0,0,0,0,0,0,0],b'');raw+=bytes(-len(raw)%512)
parsed={n:(f,b) for n,f,b in records(raw)}
assert set(parsed)==set(original)
changed=[n for n in items if items[n][1]!=original[n][1]]
assert set(changed)=={'init.mrvl.rc','ueventd.mrvl.rc','t110-preload-policy'},changed
for n,(fields,body) in items.items():
    expected=list(fields);expected[6]=len(body);expected[11]=len(n.encode())+1
    assert parsed[n]==(expected,body),n
ramdisk=gzip.compress(raw,mtime=0)
header=bytearray(old[:page]);struct.pack_into('<I',header,8,len(kernel));struct.pack_into('<I',header,16,len(ramdisk))
identity=hashlib.sha1()
for payload in (kernel,ramdisk,b''):
    identity.update(payload);identity.update(struct.pack('<I',len(payload)))
header[576:608]=identity.digest()+bytes(12)
align=lambda b:b+bytes(-len(b)%page)
boot=bytes(header)+align(kernel)+align(ramdisk)
assert len(boot)<16777216
assert boot[page:page+len(kernel)]==kernel
assert gzip.decompress(boot[page+len(align(kernel)):page+len(align(kernel))+len(ramdisk)])==raw
path=dest/'boot.img';path.write_bytes(boot.ljust(16777216,b'\0'))
(dest/'candidate-init.mrvl.rc').write_text(text)
result=dict(status='PASS_OFFLINE_NOT_HARDWARE_QUALIFIED',bytes=path.stat().st_size,sha256=sha(path.read_bytes()),
    source_boot_sha256=sha(old),kernel_sha256=sha(kernel),kernel_carryover=carry,
    system_sha256=image['raw_image_sha256'],bootstrap_policy_sha256=sha(policy),policy_version=policy_version,
    ramdisk_changed_files=changed,original_stage_unchanged=True,module_unchanged=True,
    window_gpu_enabled=True,software_fallback_retained=True,continuous_logcat_enabled=False,
    memory_fixes_retained=True,working14_images_modified=False,flashed=False)
(audit/'candidate-boot-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS matching candidate boot: archive-fixed kernel, identical config/module, new policy and exact GPU node/alias; not flashed.')
