"""Verify the exported native wallpaper ROM and its retained v29 boot pairing."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,zipfile
parser=argparse.ArgumentParser()
parser.add_argument('--version',type=int,default=26,choices=[26,27])
parser.add_argument('--evidence',default='offline-v39')
args=parser.parse_args();assert args.evidence in ['offline-v39','offline-v40']
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build')
t=b/'lineage20';image=b/f'export-lineage20-rom-v{args.version}/system.raw.img';e=p/'evidence'/args.evidence
product=b/'out-system/target/product/t110_bringup'
fit=json.loads(image.with_name('system-verification.json').read_text())
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0 and fit['expanded_bytes']==1594884096
sha=lambda v:hashlib.sha256(v).hexdigest()
def content(name):
    d=subprocess.check_output(['debugfs','-R','cat /'+name,str(image)],stderr=subprocess.DEVNULL)
    assert d and d==(product/name).read_bytes(),name
    return d
def dex(name):
    d=content(name)
    with zipfile.ZipFile(io.BytesIO(d)) as z:return b''.join(z.read(n) for n in z.namelist() if n.endswith('.dex'))
paths=['system/framework/services.jar','system/system_ext/priv-app/SystemUI/SystemUI.apk',
       'system/system_ext/priv-app/ThemePicker/ThemePicker.apk','system/system_ext/priv-app/Settings/Settings.apk',
       'system/system_ext/priv-app/TrebuchetQuickStep/TrebuchetQuickStep.apk',
       'system/system_ext/priv-app/LineageParts/LineageParts.apk',
       'system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service']
hashes={name:sha(content(name)) for name in paths}
for name in paths[:3]:assert b't110_bringup' in dex(name),name
assert b'T110NavigationKeys' in dex(paths[0])
assert hashes[paths[-1]]==json.loads((p/'evidence/offline-v35/contents.json').read_text())['changed'][paths[-1]],'No unproven compositor optimization'
for app in ['SystemUI','Settings','ThemePicker']:
    odex=content(f'system/system_ext/priv-app/{app}/oat/arm/{app}.odex')
    assert b'compiler-filter\x00speed\x00' in odex,app
props={line.split('=',1)[0]:line.split('=',1)[1] for line in content('system/build.prop').decode().splitlines() if line and not line.startswith('#') and '=' in line}
assert props['ro.sf.lcd_density']=='200' and props['ro.t110.legacy_gpu']=='true'
assert 'org.lineageos.t110.wallpapers' not in props.get('ro.config.wallpaper_component','')
installed=(product/'installed-files.txt').read_text()
assert 'T110Wallpapers' not in installed
for resource in ['android.hardware.touchscreen.xml','android.software.app_widgets.xml']:
    content('system/vendor/etc/permissions/'+resource)
for name,expected in [('gpio-keys.kl','key 102 HOME\nkey 114 VOLUME_DOWN\nkey 115 VOLUME_UP\n'),('sec_touchscreen.kl','key 139 APP_SWITCH\nkey 158 BACK\n')]:
    assert content('system/vendor/usr/keylayout/'+name).decode()==expected
boot=p/'artifacts/android13-boot-v29';meta=json.loads((boot/'provenance.json').read_text());blob=(boot/'KERNEL.img').read_bytes()
assert sha(blob)==meta['full_boot_sha256']
policy=content('system/vendor/etc/selinux/precompiled_sepolicy')
assert sha(policy)==meta['unchanged_ramdisk_files']['t110-preload-policy']
assert sha((product/'root/init.environ.rc').read_bytes())==meta['unchanged_ramdisk_files']['init.environ.rc']
patches=[('frameworks/base','0071-wallpaper-t110-software-crop.patch'),('frameworks/base','0072-systemui-t110-readable-lock-wallpaper.patch'),('frameworks/base','0073-systemui-t110-software-image-wallpaper.patch'),('packages/apps/WallpaperPicker2','0075-wallpaperpicker-t110-readable-bitmaps.patch'),('packages/apps/Settings','0070-settings-hearing-aid-without-bluetooth.patch'),('frameworks/base','0062-framework-t110-exclusive-navigation.patch'),('packages/apps/LineageParts','0063-lineageparts-t110-navigation-mode-switch.patch')]
if args.version==27:
    patches.append(('frameworks/base','0076-systemui-t110-finite-notification-clips.patch'))
    candidate=e/'systemui-candidate/SystemUI.apk'
    assert hashes[paths[1]]==sha(candidate.read_bytes())
    prior=json.loads((p/'evidence/offline-v39/contents.json').read_text())['files']
    for name in paths:
        if name!=paths[1]:assert hashes[name]==prior[name],name
for repo,patch in patches:subprocess.run(['git','-C',str(t/repo),'apply','--reverse','--check',str(p/'patches'/patch)],check=True)
result=dict(status='PASS',system_sha256=fit['sha256'],system_bytes=fit['expanded_bytes'],files=hashes,source_patches=[v for _,v in patches],boot_sha256=sha(blob),boot_md5=hashlib.md5(blob).hexdigest(),preopt='speed',bootstrap_policy_sha256=sha(policy),workaround_in_system=False,standard_theme_picker=True,hardware_validated=False,limitations=['Camera not ported','General UI lag remains'])
(e/'contents.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
