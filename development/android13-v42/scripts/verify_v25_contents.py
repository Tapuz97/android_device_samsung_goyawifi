"""Verify the actual v25 filesystem, navigation, diagnostics, graphics and v28 boot."""
from pathlib import Path
import hashlib,io,json,subprocess,zipfile,re
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build');t=b/'lineage20'
e=p/'evidence/offline-v35';export=b/'export-lineage20-rom-v25';product=b/'out-system/target/product/t110_bringup'
sha=lambda data:hashlib.sha256(data).hexdigest()
fit=json.loads((export/'system-verification.json').read_text());assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert fit['expanded_bytes']==1594884096
assert fit['ext4_features']==json.loads((p/'artifacts/lineage20-rom-v24/system-verification.json').read_text())['ext4_features']
def content(name,old=False):
    image=b/('export-lineage20-rom-v24' if old else 'export-lineage20-rom-v25')/'system.raw.img'
    data=subprocess.check_output(['debugfs','-R','cat /'+name,str(image)],stderr=subprocess.DEVNULL)
    assert data,name
    if not old:assert data==(product/name).read_bytes(),name
    return data
previous=json.loads((p/'evidence/offline-v34/contents.json').read_text())
changed_names={'system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service','system/bin/surfaceflinger','system/framework/services.jar','system/system_ext/priv-app/SystemUI/SystemUI.apk'}
retained={}
for name in set(previous['retained'])|set(previous['changed']):
    if name in changed_names:continue
    data=content(name);assert data==content(name,True),name;retained[name]=sha(data)
changed={}
for name in changed_names:
    data=content(name);assert data!=content(name,True),name;changed[name]=sha(data)
assert b'copy_ns=%llu post_ns=%llu' in content('system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service')
def dex(name):
    with zipfile.ZipFile(io.BytesIO(content(name))) as jar:
        return b''.join(jar.read(n) for n in jar.namelist() if n.endswith('.dex'))
assert b'T110NavigationKeys' in dex('system/framework/services.jar')
assert b'persist.sys.strictmode.disable' in dex('system/system_ext/priv-app/SystemUI/SystemUI.apk')
name='system/system_ext/priv-app/LineageParts/LineageParts.apk'
assert b't110_bringup' in dex(name);changed[name]=sha(content(name))
keylayouts={}
for name,expected in [('gpio-keys.kl','key 102 HOME\nkey 114 VOLUME_DOWN\nkey 115 VOLUME_UP\n'),('sec_touchscreen.kl','key 139 APP_SWITCH\nkey 158 BACK\n')]:
    data=content('system/vendor/usr/keylayout/'+name);assert data.decode()==expected;keylayouts[name]=expected
name='system/framework/org.lineageos.platform-res.apk'
apk=e/'lineage-res-v25.apk';apk.write_bytes(content(name));changed[name]=sha(apk.read_bytes())
resources=subprocess.check_output([str(b/'out-system/host/linux-x86/bin/aapt2'),'dump','resources',str(apk)],text=True)
(e/'lineage-res-resources.txt').write_text(resources,encoding='utf-8')
for resource,expected in [('config_deviceHardwareKeys',83),('config_deviceHardwareWakeKeys',65)]:
    match=re.search(r'resource [^\n]*integer/'+resource+r'[^\n]*\n\s+\(\)\s+([^\s]+)',resources)
    assert match and int(match[1],0)==expected,(resource,match[1] if match else 'missing')
props={}
for line in content('system/build.prop').decode().splitlines():
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1);assert k not in props or props[k]==v;props[k]=v
expected=previous['verified_properties']|{'persist.sys.strictmode.disable':'true'}
for k,v in expected.items():assert props[k]==v,(k,props.get(k))
odex=content('system/system_ext/priv-app/Settings/oat/arm/Settings.odex')
assert b'compiler-filter\x00speed\x00' in odex,'Settings must have full AOT code'
boot=p/'artifacts/android13-full-v28';prov=json.loads((boot/'provenance.json').read_text())
assert sha((boot/'KERNEL.img').read_bytes())==prov['full_boot_sha256']
assert sha((product/'root/sepolicy').read_bytes())==prov['bootstrap_policy_sha256']
assert content('system/vendor/etc/selinux/precompiled_sepolicy')==(product/'root/sepolicy').read_bytes()
assert sha((product/'root/init.environ.rc').read_bytes())==prov['unchanged_ramdisk_files']['init.environ.rc']
for repo,patch in [('frameworks/base','0062-framework-t110-exclusive-navigation.patch'),('packages/apps/LineageParts','0063-lineageparts-t110-navigation-mode-switch.patch'),('hardware/interfaces','0064-composer-t110-cached-scanout-staging.patch'),('frameworks/native','0065-renderengine-t110-reuse-idle-swap-spares.patch'),('frameworks/base','0066-systemui-respect-strictmode-default-optout.patch')]:
    subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/patch)],cwd=t/repo,check=True)
result=dict(status='PASS',system_sha256=fit['sha256'],system_bytes=fit['expanded_bytes'],retained=retained,changed=changed,keylayouts=keylayouts,verified_properties=expected,boot_sha256=prov['full_boot_sha256'],boot_md5=prov['full_boot_md5'],settings_preopt='speed',bootstrap_policy_sha256=prov['bootstrap_policy_sha256'],full_image_hardware_validated=False,performance_improvement_unverified=True)
(e/'contents.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
