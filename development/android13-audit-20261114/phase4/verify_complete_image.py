from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

base=Path('/root/t110-android13');audit=Path('/root/t110-android13-audit')
product=base/'out/target/product/t110_bringup';dest=audit/'complete-image'
dest.mkdir(exist_ok=True)
log=Path(sys.argv[1]) if len(sys.argv)>1 else base/'logs/complete-image-3.log'
assert 'T110_COMPLETE_SYSTEMIMAGE_BUILD_PASS' in log.read_text(errors='replace'),log
image=product/'system.img';raw=dest/'system.raw.img'
with image.open('rb') as f:magic=f.read(4)
if magic==b'\x3a\xff\x26\xed':
    subprocess.run(['/usr/bin/simg2img',str(image),str(raw)],check=True)
else:shutil.copy2(image,raw)
assert raw.stat().st_size==2146435072,raw.stat().st_size
check=subprocess.run(['e2fsck','-fn',str(raw)],capture_output=True,text=True)
(dest/'filesystem-check.txt').write_text(check.stdout+check.stderr)
assert check.returncode==0,check.stdout+check.stderr
header=subprocess.check_output(['dumpe2fs','-h',str(raw)],text=True,stderr=subprocess.DEVNULL)
(dest/'filesystem-header.txt').write_text(header)
features=set(re.search(r'^Filesystem features:\s*(.+)$',header,re.M)[1].split())
allowed={'ext_attr','dir_index','filetype','extent','sparse_super','large_file','huge_file',
         'uninit_bg','dir_nlink','extra_isize','has_journal','resize_inode','flex_bg'}
assert features<=allowed,features-allowed
blocksize=int(re.search(r'^Block size:\s*(\d+)$',header,re.M)[1])
blocks=int(re.search(r'^Block count:\s*(\d+)$',header,re.M)[1])
free=int(re.search(r'^Free blocks:\s*(\d+)$',header,re.M)[1])
assert blocksize==4096 and blocks*blocksize==raw.stat().st_size
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
extracted=dest/'extracted';extracted.mkdir(exist_ok=True)
records=[];component_deltas=[]
def extract(name,expected=None):
    path=extracted/name;path.parent.mkdir(parents=True,exist_ok=True)
    result=subprocess.run(['debugfs','-R','dump /'+name+' '+str(path),str(raw)],capture_output=True,text=True)
    assert path.is_file() and path.stat().st_size,(name,result.stderr)
    digest=sha(path)
    if expected:assert digest==expected,(name,digest,expected)
    records.append(dict(path=name,bytes=path.stat().st_size,sha256=digest))
    return path
prior=json.loads((audit/'full-build-verification.json').read_text())
for item in prior['outputs']:
    prefix='out/target/product/t110_bringup/'
    assert item['path'].startswith(prefix),item['path']
    name=item['path'][len(prefix):]
    expected=item['sha256']
    if name=='system/vendor/etc/selinux/vendor_file_contexts':
        expected=sha(product/name)
        if expected!=item['sha256']:
            component_deltas.append(dict(path=name,old_sha256=item['sha256'],sha256=expected,
                reason='Exact real galcore device-node label carried from14.1'))
    extract(name,expected)
for name in ('system/build.prop','system/vendor/build.prop','system/etc/init/hw/init.rc',
             'system/vendor/usr/keylayout/gpio-keys.kl','system/vendor/usr/keylayout/sec_touchscreen.kl'):
    extract(name,sha(product/name))
device=base/'android/device/samsung/t110_bringup'
uevent=extract('system/vendor/etc/ueventd.rc',sha(device/'graphics/ueventd.t110.rc'))
assert '/dev/graphics/galcore 0666 system graphics' in uevent.read_text()
vendor_contexts=(extracted/'system/vendor/etc/selinux/vendor_file_contexts').read_text()
assert '/dev/graphics/galcore' in vendor_contexts and 'u:object_r:gpu_device:s0' in vendor_contexts
props={}
for item in records:
    if item['path'].endswith('build.prop'):
        for line in (extracted/item['path']).read_text().splitlines():
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1);props[k]=v
assert props['ro.build.version.sdk']=='33'
model=props.get('ro.product.model',props.get('ro.product.system.model'))
assert model=='SM-T110',model
assert props['ro.sf.lcd_density']=='200'
assert props['ro.opengles.version']=='131072'
assert props['ro.t110.legacy_audio']=='true' and props['ro.t110.legacy_gpu']=='true'
assert props.get('dalvik.vm.usejit')=='false'
assert props.get('persist.sys.strictmode.disable')=='true'
for name in ('system/vendor/etc/primary_audio_policy_configuration.xml',):ET.parse(extracted/name)
required_labels={
    'system/vendor/lib/libippsp.so':'u:object_r:t110_audio_textrel_file:s0',
    'system/vendor/bin/hw/android.hardware.audio.service':'u:object_r:hal_audio_default_exec:s0',
}
label_results=[]
for name,label in required_labels.items():
    text=subprocess.check_output(['debugfs','-R','ea_list /'+name,str(raw)],text=True,stderr=subprocess.DEVNULL)
    assert label in text,(name,text)
    label_results.append(dict(path=name,expected=label,status='PASS'))
result=dict(status='PASS',source_log=str(log),source_log_sha256=sha(log),
    sparse_image_sha256=sha(image),raw_image_sha256=sha(raw),raw_bytes=raw.stat().st_size,
    filesystem_features=sorted(features),free_bytes=free*blocksize,files=records,labels=label_results,
    intentional_component_deltas=component_deltas,
    fits_supported_loop_geometry=True,physical_system_write_allowed=False,
    fits_physical_system_partition=False,live_userdata_free_space_checked=False,
    hardware_tested=False,flashed=False)
(audit/'complete-image-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'PASS complete image: {len(records)} extracted hashes, clean old-kernel-compatible ext4, {free*blocksize} free bytes.')
