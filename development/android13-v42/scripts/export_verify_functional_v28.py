"""Export only the needed raw image and verify the built functional repair pair."""
from pathlib import Path
import hashlib,io,json,re,shutil,subprocess,tempfile,zipfile,datetime
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build');t=b/'lineage20'
e=p/'evidence/offline-v41';a=p/'artifacts/lineage20-rom-v28';native=b/'export-lineage20-rom-v28';product=b/'out-system/target/product/t110_bringup'
sha=lambda data:hashlib.sha256(data).hexdigest()
logname=(e/'system-build-log-name.txt').read_text().strip();assert re.fullmatch(r'system-image-\d{8}T\d{6}Z.log',logname)
log=(b/'logs'/logname).read_text(errors='replace');assert 'build completed successfully' in log
a.mkdir(exist_ok=True);native.mkdir(exist_ok=True);raw=native/'system.raw.img'
assert not raw.exists(),'Do not silently replace an already exported candidate'
subprocess.run(['simg2img',str(product/'system.img'),str(raw)],check=True)
subprocess.run(['python3',str(p/'scripts/verify_system_image_fit.py'),str(raw),'--report',str(native/'system-verification.json')],check=True)
fit=json.loads((native/'system-verification.json').read_text());assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0 and fit['expanded_bytes']==1594884096
assert fit['ext4_features']==json.loads((p/'artifacts/lineage20-rom-v27/system-verification.json').read_text())['ext4_features']
def content(name):
    data=subprocess.check_output(['debugfs','-R','cat /'+name,str(raw)],stderr=subprocess.DEVNULL)
    assert data and data==(product/name).read_bytes(),name
    return data
names=['system/lib/libgui.so','system/lib/libui.so','system/framework/org.lineageos.platform.jar',
       'system/vendor/lib/hw/lights.mrvl.so','system/vendor/lib/hw/android.hardware.light@2.0-impl.so',
       'system/vendor/bin/hw/android.hardware.light@2.0-service','system/vendor/etc/init/init.t110.lights.rc',
       'system/vendor/etc/init/android.hardware.light@2.0-service.rc','system/vendor/etc/vintf/manifest.xml',
       'system/vendor/etc/selinux/precompiled_sepolicy','system/framework/services.jar',
       'system/system_ext/priv-app/SystemUI/SystemUI.apk','system/system_ext/priv-app/TrebuchetQuickStep/TrebuchetQuickStep.apk',
       'system/system_ext/priv-app/LineageParts/LineageParts.apk','system/system_ext/priv-app/ThemePicker/ThemePicker.apk']
# Product path spellings are fixed by actual installed-files metadata.
for i,name in enumerate(names):
    if name.endswith('TrebuchetQuickStep.apk') and not(product/name).exists():
        found=list((product/'system/system_ext/priv-app').glob('*/Trebuchet*.apk'));assert len(found)==1
        names[i]=str(found[0].relative_to(product))
hashes={name:sha(content(name)) for name in names}
for name,expected in [('gpio-keys.kl','key 102 HOME\nkey 114 VOLUME_DOWN\nkey 115 VOLUME_UP\n'),('sec_touchscreen.kl','key 139 APP_SWITCH\nkey 158 BACK\n')]:assert content('system/vendor/usr/keylayout/'+name).decode()==expected
assert b'chown system system /sys/class/backlight/panel/brightness' in content('system/vendor/etc/init/init.t110.lights.rc')
manifest=content('system/vendor/etc/vintf/manifest.xml');assert b'android.hardware.light' in manifest and b'ILight' in manifest
props={}
for line in content('system/build.prop').decode().splitlines():
    if line and not line.startswith('#') and '=' in line:k,v=line.split('=',1);props[k]=v
for key in ['ro.t110.legacy_gpu','ro.t110.optional_hal_probe','persist.sys.strictmode.disable']:assert props.get(key)=='true',(key,props.get(key))
assert props.get('dalvik.vm.usejit')=='false'
sdk=content('system/framework/org.lineageos.platform.jar');section=None
with zipfile.ZipFile(io.BytesIO(sdk)) as jar,tempfile.TemporaryDirectory(prefix='t110-sdk-dex-') as temp:
    for name in jar.namelist():
        if not name.endswith('.dex'):continue
        data=jar.read(name)
        if b'Llineageos/hardware/LineageHardwareManager;' not in data:continue
        f=Path(temp)/'sdk.dex';f.write_bytes(data)
        dump=subprocess.check_output([str(t/'prebuilts/sdk/tools/linux/bin/dexdump'),'-d',str(f)],text=True)
        descriptor="Class descriptor  : 'Llineageos/hardware/LineageHardwareManager;'"
        if descriptor in dump:
            section=dump[dump.index(descriptor):];end=section.find('\nClass #')
            if end>=0:section=section[:end]
            break
assert section
method=section[section.index("name          : 'getHIDLService'"):];end=method.find('\n    #',1)
if end>=0:method=method[:end]
(e/'compiled-lineage-hardware-probe.txt').write_text(method)
assert 'ro.t110.optional_hal_probe' in method and 'IHighTouchPollingRate' in method and 'getBoolean' in method
assert method.count('getService:')==16,method
tool=t/'prebuilts/clang/host/linux-x86/clang-r450784d/bin'
unstripped=b/'out-system/soong/.intermediates/frameworks/native/libs/gui/libgui/android_arm_armv7-a-neon_cortex-a9_shared/unstripped/libgui.so'
symbols=subprocess.check_output([str(tool/'llvm-nm'),'-C',str(unstripped)],text=True)
assert 'T110CaptureBufferOwner' in symbols
def build_id(f):
    text=subprocess.check_output([str(tool/'llvm-readelf'),'-n',str(f)],text=True)
    return re.search(r'Build ID:\s*([a-f0-9]+)',text)[1]
assert build_id(unstripped)==build_id(product/'system/lib/libgui.so')
for repo,patch in [('lineage-sdk','0077-lineage-sdk-t110-nonblocking-hardware-probes.patch'),('frameworks/native','0078-gralloc-t110-initialize-import-only-clients.patch'),('frameworks/native','0080-gui-t110-retain-capture-buffer-owner.patch')]:subprocess.run(['git','-C',str(t/repo),'apply','--reverse','--check',str(p/'patches'/patch)],check=True)
boot=p/'artifacts/android13-boot-v31';prov=json.loads((boot/'provenance.json').read_text())
assert sha((boot/'KERNEL.img').read_bytes())==prov['full_boot_sha256']
assert sha(content('system/vendor/etc/selinux/precompiled_sepolicy'))==prov['bootstrap_policy_sha256']
# No extra wallpaper app; native ThemePicker remains present.
assert not list((product/'system').rglob('T110Wallpapers.apk'))
tmp=a/'system.raw.incoming';assert not tmp.exists() and not(a/'system.raw.img').exists()
shutil.copyfile(raw,tmp)
with tmp.open('rb') as f:host_sha=hashlib.file_digest(f,'sha256').hexdigest()
assert host_sha==fit['sha256'];tmp.rename(a/'system.raw.img')
with (a/'system.raw.img').open('rb') as f:md5=hashlib.file_digest(f,'md5').hexdigest()
shutil.copyfile(native/'system-verification.json',a/'system-verification.json');(a/'system-build.log').write_text(log)
host={'status':'VERIFIED','sha256':host_sha,'md5':md5,'bytes':1594884096,'build_exit':0,'build_log':logname,'verified_at':datetime.datetime.now().astimezone().isoformat()}
(a/'host-verification.json').write_text(json.dumps(host,indent=2)+'\n')
checks={'status':'PASS','system_sha256':host_sha,'system_bytes':1594884096,'boot_sha256':prov['full_boot_sha256'],'boot_md5':prov['full_boot_md5'],'previous_boot_sha256':'83c0454a31d10aff0c80e32c94bc552a279670c4d367fe9e81ea498c6f25f29a','bootstrap_policy_sha256':prov['bootstrap_policy_sha256'],'components':hashes,'sdk_nonblocking_hidl_calls':16,'capture_owner_compiled_and_build_id_matched':True,'hardware_validated':False}
(e/'contents.json').write_text(json.dumps(checks,indent=2)+'\n')
(a/'rom-pair.json').write_text(json.dumps({'status':'OFFLINE_VERIFIED_NOT_BOOT_TESTED','system_sha256':host_sha,'system_md5':md5,'boot_artifact':'../android13-boot-v31/KERNEL.img','boot_sha256':prov['full_boot_sha256'],'boot_md5':prov['full_boot_md5'],'full_boot_passed':False,'functional_checklist_complete':False,'features_phase_started':False},indent=2)+'\n')
print('FUNCTIONAL_V28_SYSTEM_BOOT_PAIR_OFFLINE_VERIFIED',host_sha)
