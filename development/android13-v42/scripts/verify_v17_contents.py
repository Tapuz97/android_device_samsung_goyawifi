"""Verify the combined fixes in the exported filesystem, without tablet access."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
base=Path('/root/t110-build')
tree=base/'lineage20'
product=base/'out-system/target/product/t110_bringup'
export=base/'export-lineage20-rom-v17'
evidence=project/'evidence/offline-v26'
sha=lambda data:hashlib.sha256(data).hexdigest()
fit=json.loads((export/'system-verification.json').read_text())
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert fit['expanded_bytes']==1594884096
assert fit['ext4_features']==json.loads((project/'artifacts/lineage20-rom-v16/system-verification.json').read_text())['ext4_features']

def content(path, image=export/'system.raw.img'):
    return subprocess.check_output(['debugfs','-R','cat /'+path,str(image)],stderr=subprocess.DEVNULL)

files={}
for path,marker in [
    ('system/lib/libcodec2_vndk.so',b'ION unavailable; preserving allocator traits and allocation error'),
    ('system/lib/libEGL.so',b'T110 EGL: Vivante process initialized before entrypoint lookup'),
    ('system/lib/libui.so',b'T110 legacy gralloc: Vivante process initialization failed'),
    ('system/bin/surfaceflinger',b'T110 EGL window swap published the exact client target'),
    ('system/lib/libservices.core-gnss.so',b'T110 GNSS probing declared services without waiting'),
    ('system/bin/lmkd',b'lmkd accepted socket SO_PASSCRED failed'),
]:
    data=content(path)
    assert data==(product/path).read_bytes(),path
    assert data[:4]==b'\x7fELF' and marker in data,path
    files[path]=dict(sha256=sha(data),bytes=len(data),marker=marker.decode())
assert b'T110 legacy gralloc: retaining allocation owners in process' in content('system/lib/libui.so')

properties=content('system/build.prop')
for marker in [b'ro.t110.legacy_gpu=true',b'ro.zygote.disable_gl_preload=true',
               b'debug.renderengine.backend=gles',b'dalvik.vm.usejit=false',
               b'ro.t110.optional_hal_probe=true']:
    assert marker in properties,marker

unchanged={}
old_image=project/'artifacts/lineage20-rom-v16/system.raw.img'
for path in ['system/bin/keystore2','system/framework/framework.jar',
             'system/framework/services.jar','system/apex/com.android.art/lib/libart.so',
             'system/vendor/lib/libGAL.so','system/vendor/lib/egl/libEGL_MRVL.so']:
    data=content(path)
    assert data and data==content(path,old_image),path
    unchanged[path]=sha(data)

policy=(product/'root/sepolicy').read_bytes()
assert policy
policy_file=evidence/'compiled-policy.bin'
policy_file.write_bytes(policy)
subprocess.run([sys.executable,str(project/'scripts/check_v26_policy.py'),str(policy_file),
    '--report',str(evidence/'policy-after.json')],check=True)
embedded=content('system/vendor/etc/selinux/precompiled_sepolicy')
assert embedded==(product/'system/vendor/etc/selinux/precompiled_sepolicy').read_bytes()
embedded_file=evidence/'embedded-policy.bin'
embedded_file.write_bytes(embedded)
subprocess.run([sys.executable,str(project/'scripts/check_v26_policy.py'),str(embedded_file),
    '--report',str(evidence/'embedded-policy.json')],check=True)

for repo,patch in [('frameworks/av','0046-codec2-ion-error-state-traits.patch'),
                   ('frameworks/native','0047-egl-t110-process-initialization.patch'),
                   ('frameworks/native','0048-gralloc-t110-process-initialization.patch'),
                   ('frameworks/base','0045-systemui-empty-active-appops.patch')]:
    subprocess.run(['git','apply','--reverse','--check',str(project/'patches'/patch)],
                   cwd=tree/repo,check=True)
assert json.loads((evidence/'regressions.json').read_text())['status']=='PASS'
report=dict(status='PASS',files=files,unchanged=unchanged,
    bootstrap_policy_sha256=sha(policy),embedded_policy_sha256=sha(embedded),
    system_sha256=fit['sha256'],ext4_features=fit['ext4_features'],
    system_bytes=fit['expanded_bytes'],android_boots=0,
    limits='Native ARM build and offline checks; app rendering and codecs require the authorized boot')
(evidence/'contents.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
