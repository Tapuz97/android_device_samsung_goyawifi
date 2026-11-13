"""Select the matched stock HAL dependency closure; keep Nougat platform libraries."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

ROOT=Path('/root/t110-lineage14')
STOCK=ROOT/'reference/stock-ani7/extracted'
DEVICE=ROOT/'android/device/samsung/goyawifi'
DEST=DEVICE/'proprietary'
CORE={'libc.so','libm.so','libdl.so','liblog.so','libcutils.so','libutils.so',
      'libhardware.so','libhardware_legacy.so','libbinder.so','libui.so','libgui.so',
      'libmedia.so','libcamera_client.so','libaudioutils.so','libeffects.so',
      'libexpat.so','libz.so','libstdc++.so','libsync.so',
      'libEGL.so','libGLESv1_CM.so','libGLESv2.so','libGLES_trace.so',
      'libxml2.so','libicuuc.so','libicui18n.so'}
roots=['lib/egl/libEGL_MRVL.so','lib/egl/libGLESv1_CM_MRVL.so','lib/egl/libGLESv2_MRVL.so',
       'lib/hw/gralloc.mrvl.so','lib/hw/hwcomposer.mrvl.so','lib/hw/camera.mrvl.so',
       'lib/hw/audio.primary.mrvl.so','lib/hw/sensors.mrvl.so','lib/hw/power.mrvl.so']
roots += [str(p.relative_to(STOCK)) for p in sorted((STOCK/'lib/hw').glob('audio_path.*.mrvl.so'))]
# Proven Android13 dynamic dependency: not declared in DT_NEEDED.
roots += ['lib/libGLESv2SC.so']
assert hashlib.sha256((STOCK/'lib/libGLESv2SC.so').read_bytes()).hexdigest() == 'ad6e492a98834b34079eb32024fc70e77b8df543b5118e762a4fe8d96c64706f'

seen={};queue=list(roots);missing=[]
while queue:
    name=queue.pop(0)
    if name in seen:continue
    p=STOCK/name
    if not p.is_file():missing.append(name);continue
    dynamic=subprocess.check_output(['readelf','-d',str(p)],text=True)
    deps=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic)
    seen[name]=deps
    for dep in deps:
        if dep in CORE:continue
        candidates=[STOCK/'lib'/dep,STOCK/'vendor/lib'/dep,STOCK/'lib/egl'/dep]
        candidate=next((x for x in candidates if x.is_file()),None)
        if candidate is None:missing.append(dep)
        else:queue.append(str(candidate.relative_to(STOCK)))
if missing:raise RuntimeError('Missing stock dependencies: '+repr(sorted(set(missing))))
records=[];copies=[]
def install(source,relative):
    target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    copies.append('    $(LOCAL_PATH)/proprietary/'+relative+':system/vendor/'+relative)
    records.append({'stock_source':str(source),'destination':'/system/vendor/'+relative,
                    'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size})
for name,deps in sorted(seen.items()):
    relative=name.removeprefix('vendor/')
    install(STOCK/name,relative)
for directory in ['etc/audio','etc/audio_VR','etc/sensor','etc/firmware/mrvl','cameradata']:
    p=STOCK/directory
    if p.is_dir():
        for source in sorted(p.rglob('*')):
            if source.is_file():install(source,str(source.relative_to(STOCK)))
for name in ['etc/asound.conf','etc/camera_profiles.xml']:
    if (STOCK/name).is_file():install(STOCK/name,name)
for source in sorted((STOCK/'etc').glob('audio_*.xml')):
    install(source,'etc/'+source.name)
for name,relative in [('mlan.ko','etc/wifi/modules/mlan.ko'),('sd8xxx.ko','etc/wifi/modules/sd8xxx.ko'),('mbt8xxx.ko','etc/bluetooth/modules/mbt8xxx.ko')]:
    install(DEVICE/'prebuilt'/name,relative)
# The board loaders use the established firmware path, not a renamed stock image.
for name in ['sd8777_uapsta.bin','cal_data.conf']:
    install(STOCK/'etc/firmware/mrvl'/name,'firmware/mrvl/'+name)
manifest='# Matched Samsung ANI7 HALs plus private dependency closure. Never replace platform libc/libEGL.\n'
manifest+='PRODUCT_COPY_FILES += \\\n'+' \\\n'.join(copies)+'\n'
# Proprietary audio engines use standard /system/etc configuration paths.
for name in ['audio','audio_VR','sensor']:
    for source in sorted((DEST/'etc'/name).rglob('*')):
        if source.is_file():manifest+='PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/'+str(source.relative_to(DEST))+':system/'+str(source.relative_to(DEST))+'\n'
for name in ['asound.conf','camera_profiles.xml']:
    if (DEST/'etc'/name).is_file():manifest+='PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/'+name+':system/etc/'+name+'\n'
for source in sorted((DEST/'cameradata').rglob('*')):
    if source.is_file():manifest+='PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/'+str(source.relative_to(DEST))+':system/'+str(source.relative_to(DEST))+'\n'
for source in sorted((DEST/'etc').glob('audio_*.xml')):
    manifest+='PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/'+source.name+':system/etc/'+source.name+'\n'
(DEVICE/'vendor-blobs.mk').write_text(manifest)
(DEVICE/'vendor-inputs.json').write_text(json.dumps({'files':records,'dependencies':seen,'platform_dependencies':sorted(CORE)},indent=2)+'\n')
print('Selected',len(seen),'stock HAL/private libraries and',len(records),'total driver inputs.')
print('Graphics hashes:',[(x['destination'],x['sha256']) for x in records if '/hw/gralloc.' in x['destination'] or '/hw/hwcomposer.' in x['destination']])
