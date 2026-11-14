from pathlib import Path
import json,urllib.request,concurrent.futures,subprocess
r=Path('/root/t110-android13-audit')
projects={x['path']:x['head'] for x in json.loads((r/'restored/source-delta/projects.json').read_text())}
headers=r/'arm-headers';headers.mkdir(exist_ok=True)
sets={
'hardware/libhardware':('LineageOS/android_hardware_libhardware','include/',['hardware/audio.h','hardware/hardware.h','hardware/audio_effect.h']),
'system/media':('LineageOS/android_system_media','audio/include/',['system/audio.h','system/audio-base.h','system/audio-base-utils.h','system/audio_common-base.h','system/audio-hal-enums.h','system/audio_effect.h']),
'system/core':('LineageOS/android_system_core','libcutils/include/',['cutils/bitops.h','cutils/native_handle.h','cutils/compiler.h']),
}
provenance=[]
for project,(repo,prefix,names) in sets.items():
 for n in names:
  url='https://raw.githubusercontent.com/'+repo+'/'+projects[project]+'/'+prefix+n
  try:b=urllib.request.urlopen(url,timeout=30).read()
  except urllib.error.HTTPError as e:
   if e.code==404:continue
   raise
  p=headers/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  provenance.append(dict(url=url,path=n))
(r/'arm-header-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('Restored',len(provenance),'pinned Android13 platform headers.')
# Fetch just the HWUI producer files. No full framework checkout or build outputs.
p=r/'platform/frameworks/base';p.mkdir(parents=True,exist_ok=True)
names=['libs/hwui/renderthread/EglManager.cpp','libs/hwui/renderthread/EglManager.h',
       'libs/hwui/pipeline/skia/SkiaOpenGLPipeline.cpp','libs/hwui/pipeline/skia/SkiaOpenGLPipeline.h',
       'libs/hwui/Properties.cpp','libs/hwui/Properties.h','libs/hwui/renderthread/CanvasContext.cpp']
for n in names:
 u='https://raw.githubusercontent.com/LineageOS/android_frameworks_base/'+projects['frameworks/base']+'/'+n
 b=urllib.request.urlopen(u,timeout=30).read();f=p/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
subprocess.run(['git','init','-q',str(p)],check=True)
subprocess.run(['git','-C',str(p),'add','.'],check=True)
subprocess.run(['git','-C',str(p),'-c','user.name=T110 audit','-c','user.email=audit@localhost','commit','-qm','Pinned Android13 HWUI subset'],check=True)
subprocess.run(['git','-C',str(p),'apply','--include=libs/hwui/renderthread/EglManager.cpp',str(r/'restored/source-delta/patches/frameworks/base.patch')],check=True)
subprocess.run(['git','-C',str(p),'add','.'],check=True)
subprocess.run(['git','-C',str(p),'-c','user.name=T110 audit','-c','user.email=audit@localhost','commit','-qm','Restored checkpoint HWUI resolve patch'],check=True)
print('Restored pinned HWUI producer source.')
