from pathlib import Path
import subprocess,shutil,re,json,hashlib
r=Path('/root/t110-android13-audit');full=Path('/root/t110-android13/android');product=full/'device/samsung/t110_bringup';audio=product/'audio';dest=audio/'vendor';dest.mkdir(exist_ok=True)
stock=Path('/root/t110-lineage14/reference/stock-ani7/extracted');closure=json.loads((r/'audio-loader-closure.json').read_text())
assert not closure['missing']
names={name:item for name,item in closure['libraries'].items() if item['source']=='ANI7 stock'}
mapping={name:'t110_ani7_'+name.removesuffix('.so').replace('.','_').replace('+','p') for name in names}
mapping['libstdc++.so']='t110_libstdcpp' # Already supplied by the graphics product.
records=[];packages=[];definitions=[]
for name,item in sorted(names.items()):
 if name=='libstdc++.so':continue
 relative=item['path'].removeprefix('vendor/')
 source=stock/relative
 if relative.startswith('lib/alsa-lib/'):source=stock/'usr'/relative
 assert source.is_file(),source
 target=dest/relative
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 original=hashlib.sha256(source.read_bytes()).hexdigest()
 if name=='audio.primary.mrvl.so':subprocess.run(['patchelf','--add-needed','libt110_audio_legacy_compat.so',str(target)],check=True)
 if name=='libacm.so':subprocess.run(['patchelf','--add-needed','libcrypto.so',str(target)],check=True)
 soname=subprocess.check_output(['patchelf','--print-soname',str(target)],text=True).strip()
 if not soname:subprocess.run(['patchelf','--set-soname',name,str(target)],check=True)
 needed=re.findall(r'\(NEEDED\).*\[(.*?)\]',subprocess.check_output(['readelf','-d',str(target)],text=True))
 libs=[mapping.get(x,x.removesuffix('.so')) for x in needed]
 assert not any(x.startswith('/') for x in libs)
 install=Path(relative).parent.relative_to('lib').as_posix()
 definition=dict(name=mapping[name],stem=name.removesuffix('.so'),vendor=True,compile_multilib='32',srcs=['vendor/'+relative],strip={'none':True},shared_libs=libs,check_elf_files=True)
 if install!='.':definition['relative_install_path']=install
 definitions.append('cc_prebuilt_library_shared '+json.dumps(definition,indent=4).replace('"name":','name:').replace('"stem":','stem:').replace('"vendor":','vendor:').replace('"compile_multilib":','compile_multilib:').replace('"srcs":','srcs:').replace('"strip":','strip:').replace('"none":','none:').replace('"shared_libs":','shared_libs:').replace('"check_elf_files":','check_elf_files:').replace('"relative_install_path":','relative_install_path:'))
 packages.append(mapping[name]);records.append(dict(name=name,source_sha256=original,packaged_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),needed=needed,path=str(target.relative_to(audio))))
base=(r/'device/development/android13-audit-20261114/implementation/audio/Android.bp').read_text()
(audio/'Android.bp').write_text(base+'\n\n'+'\n\n'.join(definitions)+'\n')
copies=[]
def copy(source,relative,target):
 p=audio/relative;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,p)
 copies.append('    device/samsung/t110_bringup/audio/'+relative+':'+target)
# The standard root reads only vendor data and explicitly named plugin libraries.
conf=audio/'config';conf.mkdir(exist_ok=True)
text=(stock/'usr/share/alsa/alsa.conf').read_text().replace('"/etc/asound.conf"','"/vendor/etc/alsa/asound.conf"')
text+='\nctl_type.codec { lib "/vendor/lib/alsa-lib/libasound_module_ctl_codec.so" }\nctl_type.phone { lib "/vendor/lib/alsa-lib/libasound_module_ctl_phone.so" }\npcm_type.phone { lib "/vendor/lib/alsa-lib/libasound_module_pcm_phone.so" }\n'
(conf/'alsa.conf').write_text(text)
copies.append('    device/samsung/t110_bringup/audio/config/alsa.conf:$(TARGET_COPY_OUT_VENDOR)/etc/alsa/alsa.conf')
copy(stock/'etc/asound.conf','config/asound.conf','$(TARGET_COPY_OUT_VENDOR)/etc/alsa/asound.conf')
# Data-only stock paths: no system/usr plugin libraries are installed.
for source in sorted((stock/'usr/share/alsa').rglob('*')):
 if source.is_file():
  rel=str(source.relative_to(stock/'usr/share/alsa'));copy(source,'config/alsa-data/'+rel,'$(TARGET_COPY_OUT_SYSTEM)/usr/share/alsa/'+rel)
for source in sorted((stock/'etc').glob('audio_*.xml')):
 copy(source,'config/'+source.name,'$(TARGET_COPY_OUT_SYSTEM)/etc/'+source.name)
for folder in ('audio','audio_VR'):
 for source in sorted((stock/'etc'/folder).rglob('*')):
  if source.is_file():
   rel=str(source.relative_to(stock/'etc'));copy(source,'config/'+rel,'$(TARGET_COPY_OUT_SYSTEM)/etc/'+rel)
(audio/'vendor-audio.mk').write_text('# Exact ANI7 dependencies; retain modern platform providers.\n# Explicit source-root paths survive product inheritance/import expansion.\nPRODUCT_PACKAGES += '+' '.join(packages)+'\nPRODUCT_COPY_FILES += \\\n'+' \\\n'.join(copies)+'\n')
(r/'vendor-audio-packaging.json').write_text(json.dumps(records,indent=2)+'\n')
(r/'vendor-audio-targets.json').write_text(json.dumps(packages,indent=2)+'\n')
print('Packaged',len(records),'vendor audio binaries with ELF checks enabled,',len(copies),'configuration/data files.')
# Re-test the patched dynamic dependencies without diagnostic LD_PRELOAD.
for rec in records:
 shutil.copy2(audio/rec['path'],r/'loader-rootfs/vendor'/Path(rec['path']).relative_to('vendor'))
