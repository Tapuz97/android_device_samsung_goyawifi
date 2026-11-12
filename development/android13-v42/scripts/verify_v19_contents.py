"""Verify actual display-corrected v19 contents and unchanged v27 BOOT compatibility."""
from pathlib import Path
import hashlib
import json
import subprocess

p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
b=Path('/root/t110-build')
t=b/'lineage20'
product=b/'out-system/target/product/t110_bringup'
export=b/'export-lineage20-rom-v19'
old=b/'export-lineage20-rom-v18/system.raw.img'
e=p/'evidence/offline-v29'
sha=lambda data:hashlib.sha256(data).hexdigest()
fit=json.loads((export/'system-verification.json').read_text())
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert fit['expanded_bytes']==1594884096
assert fit['ext4_features']==json.loads((p/'artifacts/lineage20-rom-v18/system-verification.json').read_text())['ext4_features']
assert json.loads((e/'regressions.json').read_text())['status']=='PASS'
def content(name,image=export/'system.raw.img'):
    data=subprocess.check_output(['debugfs','-R','cat /'+name,str(image)],stderr=subprocess.DEVNULL)
    assert data,name
    return data

retained={}
for name in ['system/lib/libcodec2_vndk.so','system/lib/libEGL.so','system/lib/libui.so',
             'system/lib/libservices.core-gnss.so','system/bin/lmkd','system/bin/keystore2',
             'system/framework/framework.jar','system/framework/services.jar',
             'system/apex/com.android.art/lib/libart.so','system/vendor/lib/libGAL.so',
             'system/vendor/lib/egl/libEGL_MRVL.so','system/system_ext/priv-app/SystemUI/SystemUI.apk',
             'system/apex/com.android.wifi/javalib/framework-wifi.jar',
             'system/apex/com.android.wifi/javalib/service-wifi.jar','system/bin/vold',
             'system/bin/netd','system/apex/com.android.tethering/javalib/service-connectivity.jar',
             'system/vendor/etc/permissions/android.hardware.wifi.xml',
             'system/apex/com.android.mediaprovider/priv-app/MediaProvider@TQ3A.230901.001/MediaProvider.apk']:
    data=content(name)
    assert data==content(name,old)==(product/name).read_bytes(),name
    retained[name]=sha(data)

props={}
for line in content('system/build.prop').decode().splitlines():
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1)
        assert k not in props or props[k]==v
        props[k]=v
expected={'ro.surface_flinger.primary_display_orientation':'ORIENTATION_270',
          'ro.sf.lcd_density':'160','external_storage.sdcardfs.enabled':'false',
          'ro.t110.legacy_gpu':'true','ro.zygote.disable_gl_preload':'true',
          'dalvik.vm.usejit':'false','debug.renderengine.backend':'gles'}
for k,v in expected.items(): assert props[k]==v,(k,props.get(k))

changed={}
for name in ['system/bin/surfaceflinger','system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service',
             'system/vendor/lib/libhwc2onfbadapter.so']:
    data=content(name)
    assert data==(product/name).read_bytes() and data!=content(name,old),name
    assert data[:4]==b'\x7fELF' and data[4]==1 and int.from_bytes(data[18:20],'little')==40
    changed[name]=sha(data)
composer=content('system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service')
assert b'T110 framebuffer power: %s' in composer
assert b'T110 framebuffer power transition failed:' in composer
assert b'setPowerMode' in content('system/vendor/lib/libhwc2onfbadapter.so')
boot=p/'artifacts/android13-full-v27'
prov=json.loads((boot/'provenance.json').read_text())
assert sha((boot/'KERNEL.img').read_bytes())==prov['full_boot_sha256']
policy=(product/'root/sepolicy').read_bytes()
assert sha(policy)==prov['bootstrap_policy_sha256']
assert content('system/vendor/etc/selinux/precompiled_sepolicy')==policy
assert sha((product/'root/init.environ.rc').read_bytes())==prov['unchanged_ramdisk_files']['init.environ.rc']
for repo,patch in [('frameworks/native','0053-renderengine-t110-oriented-window-bridge.patch'),
                   ('hardware/interfaces','0054-composer-t110-scanout-and-display-power.patch')]:
    subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/patch)],cwd=t/repo,check=True)
result=dict(status='PASS',system_sha256=fit['sha256'],system_bytes=fit['expanded_bytes'],
    retained=retained,changed=changed,verified_properties=expected,
    existing_v27_boot_compatible=True,boot_sha256=prov['full_boot_sha256'],
    bootstrap_policy_sha256=sha(policy),embedded_policy_identical=True,
    android_boots=0,tablet_access=False)
(e/'contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
