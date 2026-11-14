"""Restore the exact checkpoint, then integrate reviewed candidates. Never flashes."""
from pathlib import Path
import subprocess,shutil,json,hashlib,re,os
root=Path('/root/t110-android13');android=root/'android';audit=Path('/root/t110-android13-audit')
assert (root/'SYNC-COMPLETE.json').is_file(),'Pinned sync must complete before integration'
restored=audit/'restored';records=json.loads((restored/'source-delta/projects.json').read_text())
marker=root/'CHECKPOINT-RESTORED.json'
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
if not marker.exists():
 for record in records:
  name=record['path'];p=android/name
  assert git(p,'rev-parse','HEAD')==record['head'],name
  if not record['diff_bytes']:continue
  patch=restored/'source-delta/patches'/str(name+'.patch')
  assert not git(p,'status','--porcelain'),name
  subprocess.run(['git','-C',str(p),'apply','--check',str(patch)],check=True)
  subprocess.run(['git','-C',str(p),'apply',str(patch)],check=True)
 if (restored/'untracked').exists():shutil.copytree(restored/'untracked',android,dirs_exist_ok=True)
 shutil.copytree(restored/'custom-product/t110_bringup',android/'device/samsung/t110_bringup',dirs_exist_ok=True)
 marker.write_text(json.dumps(dict(status='CHECKPOINT_RESTORED',projects=len(records)))+'\n')
 print('Restored checkpoint source changes and custom product.',flush=True)
device=android/'device/samsung/t110_bringup'
new=audit/'device/development/android13-audit-20261114'
for project,filename in [('frameworks/native','0001-libgui-t110-bounded-legacy-dequeue.patch'),('hardware/interfaces','0002-composer-refresh-scanout-after-unblank.patch'),('frameworks/base','0003-hwui-t110-full-gpu-window-swap.patch')]:
 p=android/project;patch=new/'patches'/filename
 check=subprocess.run(['git','-C',str(p),'apply','--reverse','--check',str(patch)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if check.returncode:
  subprocess.run(['git','-C',str(p),'apply','--check',str(patch)],check=True)
  subprocess.run(['git','-C',str(p),'apply',str(patch)],check=True)
audio=device/'audio';shutil.copytree(new/'implementation/audio',audio,dirs_exist_ok=True)
# Exact-path textrel exception, independent of the already present GPU switch.
p=android/'bionic/linker/linker.cpp';s=p.read_text()
old='''    if (app_target_api_level >= 23 && !t110_gpu) {'''
newtext='''    const bool t110_audio = android::base::GetBoolProperty("ro.t110.legacy_audio", false) &&
        (strcmp(get_realpath(), "/vendor/lib/libippsp.so") == 0 ||
         strcmp(get_realpath(), "/system/vendor/lib/libippsp.so") == 0);
    if (app_target_api_level >= 23 && !t110_gpu && !t110_audio) {'''
if newtext not in s:assert old in s;s=s.replace(old,newtext);p.write_text(s)
# Frozen API and live policy stay synchronized. Other execmod prohibitions remain.
policy=android/'system/sepolicy'
for prefix in ('','prebuilts/api/33.0/'):
 p=policy/(prefix+'public/attributes');s=p.read_text()
 if 'attribute t110_audio_file_type;' not in s:s='attribute t110_audio_file_type;\n'+s;p.write_text(s)
 p=policy/(prefix+'public/domain.te');s=p.read_text()
 if '-t110_audio_file_type' not in s:
  s=s.replace('  -t110_gpu_file_type\n','  -t110_gpu_file_type\n  -t110_audio_file_type\n')
  s=s.replace('{ file_type -t110_gpu_file_type }:file execmod;','{ file_type -t110_gpu_file_type -t110_audio_file_type }:file execmod;')
  s+='\n# Only audio HAL servers may relocate this device-owned DSP file type.\nneverallow { domain -hal_audio_server } t110_audio_file_type:file execmod;\n'
  p.write_text(s)
 p=policy/(prefix+'private/property_contexts');s=p.read_text()
 if 'ro.t110.legacy_audio ' not in s:s+='\nro.t110.legacy_audio u:object_r:exported_default_prop:s0 exact bool\n';p.write_text(s)
 for name in ('apmaster','gsspmaster','codecmaster'):
  line='persist.audio.'+name+' u:object_r:audio_config_prop:s0 exact bool\n'
  if line not in s:s+='\n'+line
 p.write_text(s)
audio_policy='''# Exact ANI7 DSP/clock paths; no new permissive domains.
type t110_audio_textrel_file, file_type, vendor_file_type, t110_audio_file_type;
allow hal_audio_default t110_audio_textrel_file:file { getattr open read execute map execmod };
type proc_t110_audio_clock, fs_type, proc_type;
allow init proc_t110_audio_clock:file { rw_file_perms setattr };
allow hal_audio_default proc_t110_audio_clock:file rw_file_perms;
'''
(device/'sepolicy/t110_audio.te').write_text(audio_policy)
p=device/'sepolicy/file_contexts';s=p.read_text()
line='/(vendor|system/vendor)/lib/libippsp\\.so u:object_r:t110_audio_textrel_file:s0\n'
if line not in s:s+='\n'+line;p.write_text(s)
p=device/'sepolicy/genfs_contexts';s=p.read_text()
for node in ('ssp_master','gssp_master'):
 line='genfscon proc /driver/'+node+' u:object_r:proc_t110_audio_clock:s0\n'
 if line not in s:s+='\n'+line
p.write_text(s)
# Preserve the actual standard service groups/profiles, adding only its config env.
standard=(android/'hardware/interfaces/audio/common/all-versions/default/service/android.hardware.audio.service.rc').read_text()
standard=standard.replace('    class hal','    override\n    setenv ALSA_CONFIG_PATH /vendor/etc/alsa/alsa.conf\n    class hal',1)
clocks=(audio/'init.t110.audio.rc').read_text()
(audio/'init.t110.audio.rc').write_text(clocks.split('\nservice vendor.audio-hal')[0]+'\n'+standard)
# Product wiring replaces the stub and preserves standard submix/effects/volumes.
p=device/'t110_system.mk';s=p.read_text()
s=s.replace('audio.primary.default audio.r_submix.default','audio.primary.t110 libt110_audio_legacy_compat audio.r_submix.default')
s=s.replace('frameworks/av/services/audiopolicy/config/primary_audio_policy_configuration_7_0.xml:$(TARGET_COPY_OUT_VENDOR)/etc/primary_audio_policy_configuration.xml','$(LOCAL_PATH)/audio/primary_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/primary_audio_policy_configuration.xml')
for line in ('PRODUCT_VENDOR_PROPERTIES += ro.hardware.audio.primary=t110','PRODUCT_SYSTEM_PROPERTIES += ro.t110.legacy_audio=true','PRODUCT_COPY_FILES += $(LOCAL_PATH)/audio/init.t110.audio.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.t110.audio.rc','$(call inherit-product, $(LOCAL_PATH)/audio/vendor-audio.mk)'):
 if line not in s:s+='\n'+line+'\n'
s=s.replace('# Engineering audio fallback: keeps framework audio services alive. This stub\n# does not drive the T110 speaker or microphone; native audio remains unported.','# Exact ANI7 primary audio is adapted to full modern structs; no silent stub.')
p.write_text(s)
(root/'INTEGRATION-SOURCE-READY.json').write_text(json.dumps(dict(status='SOURCE_INTEGRATED_VENDOR_INPUTS_AND_BUILD_PENDING',flashed=False))+'\n')
print('Integrated graphics/audio source and scoped SELinux/linker changes. Vendor packaging/build still required.',flush=True)
