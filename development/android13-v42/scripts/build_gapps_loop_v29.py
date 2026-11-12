"""Populate a private loop image with the unmodified official ARM13 GApps payload.

Never runs the recovery installer or accesses a host/tablet block device.
All image changes use debugfs against a new regular file under the Linux build root.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, re, shutil, stat, struct, subprocess, zipfile
import xml.etree.ElementTree as ET
parser=argparse.ArgumentParser()
parser.add_argument('--combined-log',help='Log basename of the completed grouped Android build')
parser.add_argument('--revision',type=int,default=31)
options=parser.parse_args()
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
b=Path('/root/t110-build'); t=b/'lineage20'; product=b/'out-system/target/product/t110_bringup'
assert options.revision in (31,32,33,34,35)
version=f'v{options.revision}' if options.combined_log else 'v29'
e=p/'evidence/offline-v41'; a=p/f'artifacts/lineage20-rom-{version}-gapps'
work=b/f'export-lineage20-rom-{version}-gapps'; raw=work/'system.raw.img'; payload=work/'payload'
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
assert not work.exists() and not a.exists(), 'Do not overwrite an exported candidate'
zipfile_path=p/'artifacts/mindthegapps-arm13/MindTheGapps-13.0.0-arm-20231025_200806.zip'
def digest(f,kind='sha256'):
    with f.open('rb') as stream:return hashlib.file_digest(stream,kind).hexdigest()
assert digest(zipfile_path)=='9f0c3663872488acf98eb3dd548ed53a584f119161192dcd20f904b4cd05a37e'
logname=options.combined_log or (e/'system-v29-build-log-name.txt').read_text().strip()
pattern=r'combined-t110-\d{8}T\d{6}Z\.log' if options.combined_log else r'system-image-\d{8}T\d{6}Z\.log'
assert re.fullmatch(pattern,logname)
log=(b/'logs'/logname).read_text(errors='replace')
assert 'build completed successfully' in log
if not options.combined_log:
    assert 'CODEC_ZRAM_V29_BUILD_COMPLETED' in log
for repo,name in [('frameworks/native','0082-gralloc-t110-isolated-apex-hardware-lookup.patch'),('system/sepolicy','0083-sepolicy-t110-legacy-swap-permission.patch'),('frameworks/av','0084-codec2-t110-standard-yv12-raw-lock.patch')]:
    subprocess.run(['git','-C',str(t/repo),'apply','--reverse','--check',str(p/'patches'/name)],check=True)
if options.combined_log:
    for repo,name in [
        ('build/soong','0086-soong-preopt-selected-t110-tethering-app.patch'),
        ('frameworks/base','0087-policy-honor-advanced-restart-in-fallback-menu.patch'),
        ('frameworks/base','0088-framework-export-fallback-restart-labels.patch'),
        ('hardware/interfaces','0089-composer-t110-neon-scanout.patch'),
    ]:
        subprocess.run(['git','-C',str(t/repo),'apply','--reverse','--check',
                        str(p/'patches'/name)],check=True)
    if options.revision >= 33:
        subprocess.run(['git','-C',str(t/'system/core'),'apply','--reverse','--check',
                        str(p/'patches/0091-init-allow-pmic-recovery-without-misc.patch')],check=True)
    if options.revision >= 34:
        for repo,name in [('frameworks/libs/net','0092-netlink-accept-legacy-address-header-flags.patch'),
                          ('frameworks/base','0093-tonal-parse-palettes-with-literal-replacement.patch')]:
            subprocess.run(['git','-C',str(t/repo),'apply','--reverse','--check',str(p/'patches'/name)],check=True)
work.mkdir(); payload.mkdir()
subprocess.run(['simg2img',str(product/'system.img'),str(raw)],check=True)
subprocess.run(['python3',str(p/'scripts/verify_system_image_fit.py'),str(raw),'--report',str(work/'vanilla-verification.json')],check=True)
vanilla=json.loads((work/'vanilla-verification.json').read_text())
assert vanilla['status']=='FIT_AND_EXT4_VERIFIED' and raw.stat().st_size==1594884096
def debug(command, binary=False):
    result=subprocess.run(['debugfs','-R',command,str(raw)],capture_output=True,check=True)
    return result.stdout if binary else result.stdout.decode(errors='replace')
assert 'Type: directory' in debug('stat /system/product')
assert 'Type: directory' in debug('stat /system/system_ext')
policy=(product/'root/sepolicy').read_bytes()
assert policy==(product/'system/vendor/etc/selinux/precompiled_sepolicy').read_bytes()
assert debug('cat /system/vendor/etc/selinux/precompiled_sepolicy',True)==policy
if options.revision >= 33:
    assert b'ro.t110.reboot_without_misc=true' in debug('cat /system/build.prop',True)
    assert b'ro.t110.reboot_without_misc' in debug('cat /system/bin/init',True)
native_names=['system/lib/libgui.so','system/lib/libui.so','system/lib/libcodec2_vndk.so',
 'system/system_ext/priv-app/SystemUI/SystemUI.apk','system/system_ext/priv-app/LineageParts/LineageParts.apk',
 'system/system_ext/priv-app/ThemePicker/ThemePicker.apk','system/framework/services.jar']
native_names += [str(f.relative_to(product)) for f in (product/'system/system_ext/priv-app').glob('*/Trebuchet*.apk')]
assert len(native_names)==8
if options.revision >= 33:
    native_names += ['system/bin/init','system/build.prop']
if options.revision >= 34:
    native_names += ['system/framework/framework.jar','system/priv-app/NetworkStack/NetworkStack.apk']
if options.revision >= 35:
    subprocess.run(['git','-C',str(t/'frameworks/base'),'apply','--reverse','--check',str(p/'patches/0098-hwui-t110-resolve-window-before-presentation.patch')],check=True)
    source_check=json.loads((p/'evidence/hardware-v35/hwui-source.json').read_text())
    for name,expected in source_check['files'].items():assert digest(t/'frameworks/base'/name)==expected,name
    native_names += ['system/lib/libhwui.so']
precompiled={}
if options.combined_log:
    native_names += [
        'system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service',
        'system/vendor/bin/hw/wpa_supplicant',
        'system/vendor/bin/t110_radio_init',
        'system/vendor/etc/init/init.t110.radio.rc',
        'system/vendor/etc/wifi/modules/mlan.ko',
        'system/vendor/etc/wifi/modules/sd8xxx.ko',
        'system/vendor/firmware/mrvl/sd8777_uapsta.bin',
        'system/vendor/firmware/mrvl/cal_data.conf',
    ]
    baseline=json.loads((p/'artifacts/lineage20-rom-v30-gapps/host-verification.json').read_text())
    preopt_locations={'NetworkStack':product/'system/priv-app/NetworkStack/oat/arm/NetworkStack.odex'}
    for name,apex in [('TetheringNext','com.android.tethering'),('PermissionController','com.android.permission')]:
        prefix=f'apex@{apex}@priv-app@{name}@'
        matches=list((product/'system/framework/oat/arm').glob(f'{prefix}*@{name}.apk@classes.odex'))
        assert len(matches)==1, f'Missing unambiguous {name} APEX precompile'
        preopt_locations[name]=matches[0]
    for name,odex in preopt_locations.items():
        vdex=odex.with_suffix('.vdex')
        assert odex.is_file() and vdex.is_file(), f'Missing precompiled {name} at its installed path'
        assert b'compiler-filter\x00speed\x00' in odex.read_bytes(), f'{name} was not compiled with speed'
        precompiled[name]={'compiler_filter':'speed','odex_sha256':digest(odex),'vdex_sha256':digest(vdex)}
        native_names.extend(str(path.relative_to(product)) for path in (odex,vdex))
native_hashes={n:digest(product/n) for n in native_names}
validated_archives=[]
validated_elf=[]
if options.combined_log:
    for name in native_names:
        file=product/name
        if file.suffix in ('.apk','.jar'):
            with zipfile.ZipFile(file) as archive:
                assert archive.testzip() is None, f'Archive integrity failed: {name}'
            validated_archives.append(name)
        elif file.suffix in ('.so','.odex') or '/bin/' in name:
            header=file.read_bytes()[:20]
            assert header[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',header,18)[0]==40, name
            validated_elf.append(name)
    manifest=product/'system/vendor/etc/vintf/manifest/android.hardware.wifi.supplicant.xml'
    root=ET.parse(manifest).getroot()
    assert any(hal.get('format')=='aidl' and hal.findtext('name')=='android.hardware.wifi.supplicant'
               and hal.findtext('fqname')=='ISupplicant/default' for hal in root.findall('hal'))
    supplicant_rc=product/'system/vendor/etc/init/android.hardware.wifi.supplicant-service.rc'
    assert 'interface aidl android.hardware.wifi.supplicant.ISupplicant/default' in supplicant_rc.read_text()
    if options.revision>=32:
        radio_rc=product/'system/vendor/etc/init/init.t110.radio.rc'
        assert 'capabilities SYS_MODULE NET_ADMIN' in radio_rc.read_text()
    native_hashes[str(manifest.relative_to(product))]=digest(manifest)
    native_hashes[str(supplicant_rc.relative_to(product))]=digest(supplicant_rc)
for n,h in native_hashes.items(): assert hashlib.sha256(debug('cat /'+n,True)).hexdigest()==h
with zipfile.ZipFile(zipfile_path) as z:
    assert z.testzip() is None
    assert b'arch=arm' in z.read('build.prop') and b'version=33' in z.read('build.prop')
    for item in z.infolist():
        n=PurePosixPath(item.filename)
        assert not n.is_absolute() and '..' not in n.parts and '\\' not in item.filename
        assert not stat.S_ISLNK(item.external_attr>>16)
        if item.filename.startswith('system/') and not item.is_dir():
            f=payload.joinpath(*n.parts);f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(item))
system=payload/'system'; head=system/'addon.d/addond_head'; tail=system/'addon.d/addond_tail'
excluded=[]
if options.combined_log:
    gesture=system/'product/lib/libjni_latinimegoogle.so'
    omitted=baseline['gapps_optional_library_excluded']
    assert gesture.is_file() and str(gesture.relative_to(payload))==omitted['file']
    excluded.append(omitted['file'])
    gesture.unlink()
files=sorted(f for f in system.rglob('*') if f.is_file() and 'addon.d' not in f.relative_to(system).parts)
addon=system/'addon.d/30-gapps.sh'
addon.write_bytes(head.read_bytes()+b''.join((str(f.relative_to(system))+'\n').encode() for f in files)+tail.read_bytes())
head.unlink();tail.unlink()
assert not (system/'product/priv-app/VelvetTitan').exists()
payload_hashes={str(f.relative_to(payload)):digest(f) for f in payload.rglob('*') if f.is_file()}
assert not set(payload_hashes)&set(native_hashes)
if options.combined_log:
    old_google=baseline['gapps_files']
    assert payload_hashes.keys()==old_google.keys()
    assert all(payload_hashes[name]==old_google[name] for name in old_google
               if name!='system/addon.d/30-gapps.sh')
# Keep the entire official package, including accessibility, speech and restore.
target_bytes=2047*1024*1024
with raw.open('r+b') as f:f.truncate(target_bytes)
subprocess.run(['resize2fs',str(raw),str(target_bytes//4096)],check=True)
context=work/'system-file-context.bin';context.write_bytes(b'u:object_r:system_file:s0\0')
commands=[];new_dirs=[]
for d in sorted((f for f in payload.rglob('*') if f.is_dir()),key=lambda f:(len(f.parts),str(f))):
    n='/'+str(d.relative_to(payload));info=debug('stat '+n)
    if not info:
        commands += ['mkdir '+n,'set_inode_field '+n+' mode 040755','set_inode_field '+n+' uid 0','set_inode_field '+n+' gid 0',f'ea_set -f {context} {n} security.selinux']
        new_dirs.append(n)
    else:assert 'Type: directory' in info,n
for f in sorted(f for f in payload.rglob('*') if f.is_file()):
    n='/'+str(f.relative_to(payload))
    if debug('stat '+n): commands.append('rm '+n)
    mode='0100755' if f.suffix=='.sh' or not f.suffix else '0100644'
    commands += [f'write {f} {n}',f'set_inode_field {n} mode {mode}',f'set_inode_field {n} uid 0',f'set_inode_field {n} gid 0',f'ea_set -f {context} {n} security.selinux']
# The official installer removes Provision when Google SetupWizard is present.
provision=product/'system/system_ext/priv-app/Provision'
if provision.exists():
    for f in sorted(provision.rglob('*'),key=lambda f:len(f.parts),reverse=True):
        assert not f.is_symlink()
        commands.append(('rmdir ' if f.is_dir() else 'rm ')+'/'+str(f.relative_to(product)))
    commands.append('rmdir /system/system_ext/priv-app/Provision')
batch=work/'populate.debugfs';batch.write_text('\n'.join(commands)+'\n')
result=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,text=True)
(work/'populate.log').write_text(result.stdout+result.stderr)
assert result.returncode==0
for n,h in payload_hashes.items():
    assert hashlib.sha256(debug('cat /'+n,True)).hexdigest()==h,n
    s=debug('stat /'+n); assert 'User:     0' in s and 'Group:     0' in s,s
    assert 'security.selinux' in debug('ea_list /'+n),n
for n in native_names:assert hashlib.sha256(debug('cat /'+n,True)).hexdigest()==native_hashes[n]
assert not debug('stat /system/system_ext/priv-app/Provision')
ns={};exec((p/'scripts/verify_system_image_fit.py').read_text().split("if __name__",1)[0],ns)
ext4=ns['inspect_ext4'](raw)
assert ext4['fsck_exit']==0 and ext4['ext4_features']==vanilla['ext4_features'],ext4
assert ext4['ext4_bytes']==target_bytes
record={'status':'OFFLINE_VERIFIED_NOT_INSTALLED','bytes':target_bytes,'sha256':digest(raw),'md5':digest(raw,'md5'),
 'storage':'read-only loop file on userdata; NEVER flash this image to SYSTEM',
 'fits_physical_system':False,'physical_system_bytes':1594884096,'vanilla_build_sha256':vanilla['sha256'],
 'build_log':logname,'bootstrap_policy_sha256':hashlib.sha256(policy).hexdigest(),
 'gapps_source':'https://github.com/MindTheGapps/13.0.0-arm/releases/tag/MindTheGapps-13.0.0-arm-20231025_200806',
 'gapps_zip_sha256':digest(zipfile_path),'gapps_files':payload_hashes,'native_components_unchanged':native_hashes,
 'payload_optional_apps_removed':[],'payload_optional_libraries_removed':excluded,
 'startup_precompiled_apps':precompiled,
 'validated_native_archives':validated_archives,'validated_arm_elf_files':validated_elf,
 'new_directories':new_dirs,'ext4':ext4,'fresh_android_data_required':not options.combined_log,
 'old_data_profile_must_be_preserved':True,'hardware_validated':False}
a.mkdir();target=a/'system.raw.incoming';shutil.copyfile(raw,target)
assert digest(target)==record['sha256'];target.rename(a/'system.raw.img')
(a/'host-verification.json').write_text(json.dumps(record,indent=2)+'\n')
(a/'system-build.log').write_text(log)
(e/f'gapps-{version}-offline-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(f'GAPPS_SYSTEM_{version.upper()}_OFFLINE_VERIFIED',record['sha256'],flush=True)
