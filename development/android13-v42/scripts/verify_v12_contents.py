from pathlib import Path
import hashlib,json,subprocess,re
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root=Path('/root/t110-build/export-lineage20-rom-v12')
def content(name):
    return subprocess.check_output(['debugfs','-R','cat '+name,str(root/'system.raw.img')],stderr=subprocess.DEVNULL)
prop=content('/system/build.prop')
for value in (b'dalvik.vm.usejit=false',b'dalvik.vm.usejitprofiles=false',b'service.sf.prime_shader_cache=0',b'ro.t110.legacy_gpu=true',b'debug.renderengine.backend=gles',b'ro.zygote.disable_gl_preload=true'):
    assert value in prop,value
composer=content('/system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service')
for marker in (b'T110 direct framebuffer presenter ready',b'T110 first client frame copied and panned to fb0',b'T110 direct fb0 scanout:',b'gcoOS_ModuleConstructor',b'PXA ION read synchronization enabled'):
    assert marker in composer, marker
assert b'HWC2OnFbAdapter' in composer
assert content('/system/bin/installd')[:4] == b'\x7fELF'
assert b'service installd /system/bin/installd\n    class main' in content('/system/etc/init/installd.rc')
init=content('/system/etc/init/hw/init.rc')
assert b'on nonencrypted\n    class_start main\n    class_start late_start' in init
cil=content('/system/vendor/etc/selinux/vendor_sepolicy.cil')
assert re.search(rb'\(allow init(?:_[0-9]+_[0-9]+)? sysfs_t110_vsync_control \(file \([^)]*setattr',cil)
assert content('/system/vendor/bin/hw/android.hardware.health@2.1-service')[:4] == b'\x7fELF'
assert content('/system/vendor/lib/hw/android.hardware.health@2.0-impl-2.1.so')[:4] == b'\x7fELF'
gralloc=content('/system/vendor/lib/hw/gralloc.mrvl.so')
assert gralloc==(project/'work/device/samsung/t110_bringup/graphics/hw/gralloc.mrvl.so').read_bytes()
libui=content('/system/lib/libui.so')
assert b'T110 legacy gralloc: retaining allocation owners in process' in libui
# Match the newly linked artifact, not an old libui copied into the image.
assert libui==Path('/root/t110-build/out-system/target/product/t110_bringup/system/lib/libui.so').read_bytes()
render=content('/system/bin/surfaceflinger')
assert b'T110 resolved GLES frame before handoff' in render
result=dict(status='PASS',gles_backend=True,resolve_before_handoff=True,ion_read_sync=True,zygote_gl_preload_disabled=True,installd_present=True,main_class_event_handler_present=True,
    direct_framebuffer_presenter_present=True,legacy_gpu_opt_in=True,
    composer_sha256=hashlib.sha256(composer).hexdigest(),libui_sha256=hashlib.sha256(libui).hexdigest(),
    gralloc_sha256=hashlib.sha256(gralloc).hexdigest(),hardware_validated=False)
(project/'evidence/v12-combined-fixes-contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
