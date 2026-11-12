"""Inspect the actual corrected ROM; reuse v26 BOOT only if all pairing checks pass."""
from pathlib import Path
import hashlib
import io
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
b = Path('/root/t110-build')
t = b/'lineage20'
product = b/'out-system/target/product/t110_bringup'
export = b/'export-lineage20-rom-v18'
old_image = b/'export-lineage20-rom-v17/system.raw.img'
e = p/'evidence/offline-v27'
sha = lambda data: hashlib.sha256(data).hexdigest()
fit = json.loads((export/'system-verification.json').read_text())
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert fit['expanded_bytes']==1594884096
assert fit['ext4_features']==json.loads((p/'artifacts/lineage20-rom-v17/system-verification.json').read_text())['ext4_features']
assert json.loads((e/'regressions.json').read_text())['status']=='PASS'

def content(name, image=export/'system.raw.img'):
    data=subprocess.check_output(['debugfs','-R','cat /'+name,str(image)],stderr=subprocess.DEVNULL)
    assert data, name
    return data

unchanged={}
for name in [
    'system/lib/libcodec2_vndk.so','system/lib/libEGL.so','system/lib/libui.so',
    'system/bin/surfaceflinger','system/lib/libservices.core-gnss.so','system/bin/lmkd',
    'system/bin/keystore2','system/framework/framework.jar','system/framework/services.jar',
    'system/apex/com.android.art/lib/libart.so','system/vendor/lib/libGAL.so',
    'system/vendor/lib/egl/libEGL_MRVL.so','system/system_ext/priv-app/SystemUI/SystemUI.apk',
    'system/apex/com.android.wifi/javalib/framework-wifi.jar',
    'system/apex/com.android.wifi/javalib/service-wifi.jar','system/bin/vold',
]:
    data=content(name)
    assert data==content(name,old_image)==(product/name).read_bytes(),name
    unchanged[name]=sha(data)

props={}
for line in content('system/build.prop').decode().splitlines():
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1)
        assert k not in props or props[k]==v,(k,props.get(k),v)
        props[k]=v
expected={'external_storage.sdcardfs.enabled':'false','ro.t110.legacy_gpu':'true',
          'ro.zygote.disable_gl_preload':'true','dalvik.vm.usejit':'false',
          'ro.t110.optional_hal_probe':'true','debug.renderengine.backend':'gles'}
for k,v in expected.items(): assert props[k]==v,(k,props.get(k))

xml_path='system/vendor/etc/permissions/android.hardware.wifi.xml'
xml=content(xml_path)
assert xml==(product/xml_path).read_bytes()==(t/'frameworks/native/data/etc/android.hardware.wifi.xml').read_bytes()
features=[node.attrib['name'] for node in ET.fromstring(xml).findall('feature')]
assert 'android.hardware.wifi' in features

jar_path='system/apex/com.android.tethering/javalib/service-connectivity.jar'
jar=content(jar_path)
assert jar==(product/jar_path).read_bytes() and jar!=content(jar_path,old_image)
found=''
with tempfile.TemporaryDirectory(prefix='v18-dex-',dir=b) as scratch:
    with zipfile.ZipFile(io.BytesIO(jar)) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex',name): continue
            data=archive.read(name)
            if b'Global bandwidth alert unavailable; retaining polling:' not in data: continue
            dex=Path(scratch)/name; dex.write_bytes(data)
            proc=subprocess.Popen([str(t/'prebuilts/sdk/tools/linux/bin/dexdump'),'-d',str(dex)],
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,errors='replace')
            active=False; lines=[]
            for line in proc.stdout:
                if 'Class descriptor' in line:
                    if active: break
                    active="'Lcom/android/server/net/NetworkStatsService;'" in line
                if active: lines.append(line)
            if proc.poll() is None: proc.terminate()
            proc.wait()
            text=''.join(lines)
            marker="name          : 'registerGlobalAlert'"
            if marker not in text: continue
            found=text[text.index(marker):]
            end=re.search(r'\n    #\d+',found)
            if end: found=found[:end.start()]
            break
assert found, 'New DEX method not found'
(e/'NetworkStats-registerGlobalAlert-dex.txt').write_text(found)
assert 'bandwidthSetGlobalAlert:' in found
assert 'Global bandwidth alert unavailable; retaining polling:' in found
catches=found[found.index('catches'):]
assert 'Landroid/os/ServiceSpecificException;' in catches
assert 'Ljava/lang/IllegalStateException;' in catches and 'Landroid/os/RemoteException;' in catches
assert 'invokeForAllStatsProviderCallbacks:' in found

precompiled={}
for ext in ('odex','vdex'):
    name='system/framework/oat/arm/apex@com.android.tethering@javalib@service-connectivity.jar@classes.'+ext
    data=content(name)
    assert data==(product/name).read_bytes() and data!=content(name,old_image),name
    precompiled[ext]=sha(data)

apk_name='system/apex/com.android.mediaprovider/priv-app/MediaProvider@TQ3A.230901.001/MediaProvider.apk'
apk=content(apk_name)
assert apk==(product/apk_name).read_bytes()
fuse_libraries={}
with zipfile.ZipFile(io.BytesIO(apk)) as archive:
    for module,repo in [('libfuse','external/libfuse'),('libfuse_jni','packages/providers/MediaProvider/jni')]:
        name='lib/armeabi-v7a/'+module+'.so'
        data=archive.read(name)
        folder=b/'out-system/soong/.intermediates'/repo/module
        outputs=list(folder.glob('android_arm*_shared_apex30/'+module+'.so'))
        assert len(outputs)==1,outputs
        assert data==outputs[0].read_bytes(),name
        fuse_libraries[name]=sha(data)

netd=content('system/bin/netd')
assert netd==(product/'system/bin/netd').read_bytes()
assert netd!=content('system/bin/netd',old_image)
assert netd[:4]==b'\x7fELF'

# The existing BOOT can be reused only if its early policy and classpath file
# exactly match this system's root output, and embedded policy matches too.
boot=p/'artifacts/android13-full-v26'
prov=json.loads((boot/'provenance.json').read_text())
assert sha((boot/'KERNEL.img').read_bytes())==prov['full_boot_sha256']
policy=(product/'root/sepolicy').read_bytes()
assert sha(policy)==prov['bootstrap_policy_sha256']
embedded=content('system/vendor/etc/selinux/precompiled_sepolicy')
assert embedded==policy
assert sha((product/'root/init.environ.rc').read_bytes())==prov['unchanged_ramdisk_files']['init.environ.rc']
for repo,patch in [('packages/modules/Connectivity','0049-networkstats-global-alert-service-errors.patch'),
                   ('system/netd','0050-netd-global-alert-commit-on-success.patch'),
                   ('external/libfuse','0051-libfuse-unsigned-passthrough-mask.patch'),
                   ('frameworks/av','0046-codec2-ion-error-state-traits.patch'),
                   ('frameworks/native','0047-egl-t110-process-initialization.patch'),
                   ('frameworks/native','0048-gralloc-t110-process-initialization.patch')]:
    subprocess.run(['git','-C',t/repo,'apply','--reverse','--check',p/'patches'/patch],check=True)
result=dict(status='PASS', system_sha256=fit['sha256'],system_bytes=fit['expanded_bytes'],
    features=features, verified_properties=expected, unchanged=unchanged,
    service_connectivity_sha256=sha(jar),netd_sha256=sha(netd),
    service_connectivity_precompiled=precompiled,mediaprovider_native_libraries=fuse_libraries,
    actual_networkstats_dex_error_handler=True,provider_callbacks_retained=True,
    existing_v26_boot_compatible=True,boot_sha256=prov['full_boot_sha256'],
    bootstrap_policy_sha256=sha(policy),embedded_policy_identical=True,
    android_boots=0,tablet_access=False,
    limits=['Offline checks do not prove Wi-Fi radio functionality, storage mounts or a usable hardware boot'])
(e/'contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
