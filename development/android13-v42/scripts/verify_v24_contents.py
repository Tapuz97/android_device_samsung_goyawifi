"""Verify v24 app fixes, compact Settings header and matching v28 BOOT."""
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
export=b/'export-lineage20-rom-v24'
old=b/'export-lineage20-rom-v23/system.raw.img'
e=p/'evidence/offline-v34'
sha=lambda data:hashlib.sha256(data).hexdigest()
fit=json.loads((export/'system-verification.json').read_text())
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert fit['expanded_bytes']==1594884096
assert fit['ext4_features']==json.loads((p/'artifacts/lineage20-rom-v23/system-verification.json').read_text())['ext4_features']
candidate=json.loads((e/'launcher-candidate/installation.json').read_text())
assert candidate['visual_result']=='HOME_DRAWER_SETTINGS_RECENTS_RENDER_CORRECTLY'
assert candidate['new_launcher_crash_after_update'] is False
assert json.loads((e/'kernel-verification.json').read_text())['display_i2c_remux_removed_from_compiled_object']
assert json.loads((e/'boot-verification.json').read_text())['status']=='PASS'
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
             'system/vendor/lib/egl/libEGL_MRVL.so',
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
expected={'ro.surface_flinger.primary_display_orientation':'ORIENTATION_0',
          'ro.sf.lcd_density':'160','external_storage.sdcardfs.enabled':'false',
          'ro.t110.legacy_gpu':'true','ro.zygote.disable_gl_preload':'true',
          'dalvik.vm.usejit':'false','debug.renderengine.backend':'gles'}
for k,v in expected.items(): assert props[k]==v,(k,props.get(k))

changed={}
name='system/framework/framework.jar'
data=content(name)
assert data==(product/name).read_bytes()==content(name,old),name
with zipfile.ZipFile(io.BytesIO(data)) as jar:
    dex=[jar.read(n) for n in jar.namelist() if n.endswith('.dex')]
    assert dex and any(b'T110 window rendering: software Canvas for ' in d for d in dex)
retained[name]=sha(data)
for filename,expected_features in [
        ('android.software.app_widgets.xml',{'android.software.app_widgets'}),
        ('android.hardware.touchscreen.xml',{'android.hardware.touchscreen','android.hardware.faketouch'})]:
    name='system/vendor/etc/permissions/'+filename
    data=content(name)
    assert data==(product/name).read_bytes()
    assert {n.attrib['name'] for n in ET.fromstring(data).findall('feature')}==expected_features
    changed[name]=sha(data)
for app in ['TrebuchetQuickStep','SystemUI','LineageSetupWizard','Settings']:
    name=f'system/system_ext/priv-app/{app}/{app}.apk'
    data=content(name)
    assert data==(product/name).read_bytes(),name
    if app=='TrebuchetQuickStep':
        assert sha(data)==candidate['sha256']
        assert data==(e/'launcher-candidate/TrebuchetQuickStep.apk').read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as jar:
        dex=b''.join(jar.read(n) for n in jar.namelist() if n.endswith('.dex'))
    if app in ('TrebuchetQuickStep','SystemUI'):
        assert b't110_bringup' in dex,app
    if app=='Settings':
        apk=e/'Settings-v24.apk'
        apk.write_bytes(data)
        resources=subprocess.check_output([str(b/'out-system/host/linux-x86/bin/aapt2'),
                                          'dump','resources',str(apk)],text=True)
        (e/'settings-resources.txt').write_text(resources)
        import re
        match=re.search(r'resource [^\n]*dimen/avatar_margin_top[^\n]*\n([^\n]+)',resources)
        value=re.search(r'\(\)\s+([0-9.]+)dp',match.group(1)) if match else None
        assert value and float(value.group(1))==8.0, 'Compact header missing from actual Settings APK'
    if data==content(name,old): retained[name]=sha(data)
    else: changed[name]=sha(data)

# Verify the framework's matching precompiled artifacts in the actual image.
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
boot=p/'artifacts/android13-full-v28'
prov=json.loads((boot/'provenance.json').read_text())
assert sha((boot/'KERNEL.img').read_bytes())==prov['full_boot_sha256']
policy=(product/'root/sepolicy').read_bytes()
assert sha(policy)==prov['bootstrap_policy_sha256']
assert content('system/vendor/etc/selinux/precompiled_sepolicy')==policy
assert sha((product/'root/init.environ.rc').read_bytes())==prov['unchanged_ramdisk_files']['init.environ.rc']
for repo,patch in [('frameworks/native','0053-renderengine-t110-oriented-window-bridge.patch'),
                   ('hardware/interfaces','0056-composer-t110-padded-portrait-scanout.patch'),
                   ('packages/apps/SetupWizard','0057-setupwizard-configurable-canvas-rendering.patch'),
                   ('frameworks/base','0058-framework-t110-software-window-rendering.patch'),
                   ('frameworks/libs/systemui','0059-iconloader-t110-software-bitmaps.patch'),
                   ('frameworks/base','0060-systemui-shared-t110-software-task-snapshots.patch')]:
    subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/patch)],cwd=t/repo,check=True)
result=dict(status='PASS',system_sha256=fit['sha256'],system_bytes=fit['expanded_bytes'],
    retained=retained,changed=changed,verified_properties=expected,
    matching_v28_boot_verified=True,boot_sha256=prov['full_boot_sha256'],
    bootstrap_policy_sha256=sha(policy),embedded_policy_identical=True,
    offline_image_check=True,boot_preopt=boot_preopt,
    setup_app_same_boot_validated=True,ordinary_window_fallback_hardware_validated=True,
    launcher_candidate_same_boot_validated=True,compact_settings_header_verified=True,
    full_image_hardware_validated=False)
(e/'contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
