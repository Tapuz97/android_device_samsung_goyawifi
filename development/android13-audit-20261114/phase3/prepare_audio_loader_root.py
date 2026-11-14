from pathlib import Path
import subprocess,shutil,re,json,os
r=Path('/root/t110-android13-audit');root=r/'loader-rootfs';root.mkdir(exist_ok=True)
image=Path('/root/t110-lineage14/reference/android13-current-system.raw.img')
stock=Path('/root/t110-lineage14/reference/stock-ani7/extracted')
core={'libc.so','libm.so','libdl.so','liblog.so','libcutils.so','libutils.so','libhardware.so','libhardware_legacy.so','libbinder.so','libui.so','libgui.so','libmedia.so','libcamera_client.so','libaudioutils.so','libeffects.so','libexpat.so','libz.so','libstdc++.so','libsync.so','libEGL.so','libGLESv1_CM.so','libGLESv2.so','libGLES_trace.so','libxml2.so','libicuuc.so','libicui18n.so','libcrypto.so'}
records={};pending=[]
def extract(path,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['debugfs','-R','dump '+path+' '+str(target),str(image)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 return target.is_file() and target.stat().st_size>0
def dependencies(file):
 text=subprocess.check_output(['readelf','-d',str(file)],text=True)
 return re.findall(r'\(NEEDED\).*\[(.*?)\]',text)
def platform(name):
 candidates=['/system/vendor/lib/'+name,'/system/lib/'+name,'/system/apex/com.android.runtime/lib/bionic/'+name,'/system/apex/com.android.vndk.v33/lib/'+name,'/system/apex/com.android.i18n/lib/'+name]
 if name in ('libc.so','libm.so','libdl.so'):
  candidates.remove('/system/apex/com.android.runtime/lib/bionic/'+name)
  candidates.insert(0,'/system/apex/com.android.runtime/lib/bionic/'+name)
 for path in candidates:
  target=root/path.lstrip('/')
  if extract(path,target):
   alias=root/'system/lib'/name
   if alias!=target:
    alias.parent.mkdir(parents=True,exist_ok=True)
    if alias.is_symlink():alias.unlink()
    if alias.is_file() and alias.stat().st_size==0:alias.unlink()
    if not alias.exists():alias.symlink_to(os.path.relpath(target,alias.parent))
   records[name]=dict(source='preserved Android13 image',path=str(target.relative_to(root)))
   vendor_alias=root/'vendor/lib'/name
   if name in core and vendor_alias!=target:
    if vendor_alias.exists() or vendor_alias.is_symlink():vendor_alias.unlink()
    vendor_alias.parent.mkdir(parents=True,exist_ok=True)
    vendor_alias.symlink_to(os.path.relpath(target,vendor_alias.parent))
   pending.append(target);return target
 return None
for path in ['lib/hw/audio.primary.mrvl.so','usr/lib/alsa-lib/libasound_module_ctl_codec.so','usr/lib/alsa-lib/libasound_module_ctl_phone.so','usr/lib/alsa-lib/libasound_module_pcm_phone.so']:
 p=stock/path;dest=root/'vendor/lib'/('hw' if '/hw/' in path else 'alsa-lib')/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);records[p.name]=dict(source='ANI7 stock',path=str(dest.relative_to(root)));pending.append(dest)
platform('libcrypto.so')
platform('libdl_android.so')
for name in ['audio.primary.t110.so','libt110_audio_legacy_compat.so']:
 p=r/'arm-checks'/name;dest=root/'vendor/lib'/('hw' if name.startswith('audio.') else '')/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);pending.append(dest);records[name]=dict(source='new component',path=str(dest.relative_to(root)))
missing=[]
while pending:
 p=pending.pop()
 for name in dependencies(p):
  if name in records:continue
  if name in core and platform(name):continue
  f=stock/'lib'/name
  if f.is_file():
   dest=root/'vendor/lib'/name;shutil.copy2(f,dest);records[name]=dict(source='ANI7 stock',path=str(dest.relative_to(root)));pending.append(dest);continue
  if platform(name):continue
  missing.append(dict(parent=str(p.relative_to(root)),dependency=name))
link=root/'system/bin/linker';assert extract('/system/apex/com.android.runtime/bin/linker',link);link.chmod(0o755)
(root/'data/local/tmp').mkdir(parents=True,exist_ok=True)
(r/'audio-loader-closure.json').write_text(json.dumps(dict(libraries=records,missing=missing),indent=2)+'\n')
print('Prepared',len(records),'libraries; missing:',missing)
