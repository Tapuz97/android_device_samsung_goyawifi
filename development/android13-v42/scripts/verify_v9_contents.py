from pathlib import Path
import hashlib,json,subprocess
root=Path('/root/t110-build/export-lineage20-rom-v9')
def content(name):
 return subprocess.check_output(['debugfs','-R','cat '+name,str(root/'system.raw.img')],stderr=subprocess.DEVNULL)
prop=content('/system/build.prop')
for value in (b'dalvik.vm.usejit=false',b'dalvik.vm.usejitprofiles=false',b'service.sf.prime_shader_cache=0'):
 assert value in prop,value
composer=content('/system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service')
assert b'T110: Vivante process state initialized before HWC' in composer
assert b'gcoOS_ModuleConstructor' in composer
cil=content('/system/vendor/etc/selinux/vendor_sepolicy.cil')
assert b'/devices/platform/pxa168-fb.0/vsync' in cil
assert b'sysfs_t110_vsync_control' in cil
assert b'/graphics/fb0/vsync_ts' not in cil
result=dict(status='PASS',jit_disabled=True,vivante_preinitialization_present=True,vsync_platform_path_corrected=True,composer_sha256=hashlib.sha256(composer).hexdigest())
Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence/v9-combined-fixes-contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
