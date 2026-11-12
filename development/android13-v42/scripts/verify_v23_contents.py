"""Verify actual display-corrected v23 contents and unchanged v27 BOOT compatibility."""
from pathlib import Path
import hashlib
import json
import subprocess
import io
import zipfile
import xml.etree.ElementTree as ET

p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
b=Path('/root/t110-build')
t=b/'lineage20'
product=b/'out-system/target/product/t110_bringup'
export=b/'export-lineage20-rom-v23'
old=b/'export-lineage20-rom-v22/system.raw.img'
e=p/'evidence/offline-v33'
sha=lambda data:hashlib.sha256(data).hexdigest()
fit=json.loads((export/'system-verification.json').read_text())
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert fit['expanded_bytes']==1594884096
assert fit['ext4_features']==json.loads((p/'artifacts/lineage20-rom-v22/system-verification.json').read_text())['ext4_features']
candidate=json.loads((p/'evidence/offline-v32/setup-candidate/installation.json').read_text())
assert candidate['visual_result']=='WELCOME_RENDERED_CORRECTLY'
def content(name,image=export/'system.raw.img'):
    data=subprocess.check_output(['debugfs','-R','cat /'+name,str(image)],stderr=subprocess.DEVNULL)
    assert data,name
    return data

retained={}
for name in ['system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service','system/bin/surfaceflinger','system/vendor/lib/libhwc2onfbadapter.so',
             'system/lib/libcodec2_vndk.so','system/lib/libEGL.so','system/lib/libui.so',
             'system/lib/libservices.core-gnss.so','system/bin/lmkd','system/bin/keystore2',
             'system/framework/services.jar',
             'system/apex/com.android.art/lib/libart.so','system/vendor/lib/libGAL.so',
             'system/vendor/lib/egl/libEGL_MRVL.so','system/system_ext/priv-app/SystemUI/SystemUI.apk',
             'system/apex/com.android.wifi/javalib/framework-wifi.jar',
             'system/apex/com.android.wifi/javalib/service-wifi.jar','system/bin/vold',
             'system/bin/netd','system/apex/com.android.tethering/javalib/service-connectivity.jar',
             'system/vendor/etc/permissions/android.hardware.wifi.xml',
             'system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk',
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
expected={'ro.surface_flinger.primary_display_orientation':'ORIENTATION_0',
          'ro.sf.lcd_density':'160','external_storage.sdcardfs.enabled':'false',
          'ro.t110.legacy_gpu':'true','ro.zygote.disable_gl_preload':'true',
          'dalvik.vm.usejit':'false','debug.renderengine.backend':'gles'}
for k,v in expected.items(): assert props[k]==v,(k,props.get(k))

changed={}
name='system/framework/framework.jar'
data=content(name)
assert data==(product/name).read_bytes() and data!=content(name,old),name
with zipfile.ZipFile(io.BytesIO(data)) as jar:
    dex=[jar.read(n) for n in jar.namelist() if n.endswith('.dex')]
    assert dex and any(b'T110 window rendering: software Canvas for ' in d for d in dex)
changed[name]=sha(data)
for filename,expected_features in [
        ('android.software.app_widgets.xml',{'android.software.app_widgets'}),
        ('android.hardware.touchscreen.xml',{'android.hardware.touchscreen','android.hardware.faketouch'})]:
    name='system/vendor/etc/permissions/'+filename
    data=content(name)
    assert data==(product/name).read_bytes()
    assert {n.attrib['name'] for n in ET.fromstring(data).findall('feature')}==expected_features
    changed[name]=sha(data)
assert retained['system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk']==candidate['sha256']
# The framework changed, so verify the newly built boot-image artifacts are
# actually present in this image, rather than retaining old precompiled files.
boot_preopt={}
for path in sorted(list((product/'system/framework/arm').glob('boot*'))+list((product/'system/framework').glob('boot*.vdex'))):
    if path.is_file() and not path.is_symlink() and path.suffix in ('.art','.oat','.vdex'):
        name=path.relative_to(product).as_posix()
        data=content(name)
        assert data==path.read_bytes()
        boot_preopt[name]=sha(data)
assert boot_preopt,'Missing rebuilt framework boot preopt artifacts'
composer=content('system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service')
assert b'final panel rotation=270' in composer
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
                   ('hardware/interfaces','0056-composer-t110-padded-portrait-scanout.patch'),
                   ('packages/apps/SetupWizard','0057-setupwizard-configurable-canvas-rendering.patch'),
                   ('frameworks/base','0058-framework-t110-software-window-rendering.patch')]:
    subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/patch)],cwd=t/repo,check=True)
result=dict(status='PASS',system_sha256=fit['sha256'],system_bytes=fit['expanded_bytes'],
    retained=retained,changed=changed,verified_properties=expected,
    existing_v27_boot_compatible=True,boot_sha256=prov['full_boot_sha256'],
    bootstrap_policy_sha256=sha(policy),embedded_policy_identical=True,
    offline_image_check=True,boot_preopt=boot_preopt,
    setup_app_same_boot_validated=True,ordinary_window_fallback_hardware_validated=False)
(e/'contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
