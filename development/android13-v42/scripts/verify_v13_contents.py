"""Read the completed image, verifying the actual renderer and ART binaries."""
from pathlib import Path
import hashlib,json,subprocess,re

project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root=Path('/root/t110-build/export-lineage20-rom-v13')
product=Path('/root/t110-build/out-system/target/product/t110_bringup')
def content(name):
    return subprocess.check_output(['debugfs','-R','cat '+name,str(root/'system.raw.img')],stderr=subprocess.DEVNULL)
def sha(data): return hashlib.sha256(data).hexdigest()
prop=content('/system/build.prop')
for value in (b'dalvik.vm.usejit=false',b'dalvik.vm.usejitprofiles=false',
              b'ro.t110.legacy_gpu=true',b'debug.renderengine.backend=gles',
              b'ro.zygote.disable_gl_preload=true'):
    assert value in prop,value
render=content('/system/bin/surfaceflinger')
assert render == (product/'system/bin/surfaceflinger').read_bytes()
assert b'T110 EGL window swap published the exact client target' in render
assert b'T110 EGL swap did not publish the requested client target' in render
assert b'T110 resolved GLES frame before handoff' not in render
composer=content('/system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service')
assert b'PXA ION read synchronization enabled' in composer
assert b'T110 direct framebuffer presenter ready' in composer
assert content('/system/bin/installd')[:4] == b'\x7fELF'
assert content('/system/vendor/bin/hw/android.hardware.health@2.1-service')[:4] == b'\x7fELF'
assert b'on nonencrypted\n    class_start main\n    class_start late_start' in content('/system/etc/init/hw/init.rc')
gralloc=content('/system/vendor/lib/hw/gralloc.mrvl.so')
assert gralloc==(project/'work/device/samsung/t110_bringup/graphics/hw/gralloc.mrvl.so').read_bytes()
libui=content('/system/lib/libui.so')
assert libui==(product/'system/lib/libui.so').read_bytes()
assert b'T110 legacy gralloc: retaining allocation owners in process' in libui

art=[]
for filename in ['libart.so','libartd.so']:
    paths=list((product/'system/apex').glob('*/lib/'+filename))
    assert paths,filename
    for path in paths:
        relative='/' + str(path.relative_to(product))
        data=content(relative)
        assert data==path.read_bytes(),relative
        assert data[:4]==b'\x7fELF'
        old=subprocess.check_output(['debugfs','-R','cat '+relative,
            str(project/'artifacts/lineage20-rom-v12/system.raw.img')],stderr=subprocess.DEVNULL)
        assert old[:4]==b'\x7fELF' and sha(old)!=sha(data), 'ART fix not rebuilt: '+relative
        art.append(dict(path=relative,sha256=sha(data),previous_sha256=sha(old)))
assert json.loads((project/'evidence/offline-v23/zygote-lock-contract.json').read_text())['status']=='PASS'
assert 'PASS:' in (project/'evidence/offline-v23/window-ownership-test.log').read_text()
result=dict(status='PASS',egl_window_bridge=True,old_fbo_workaround_removed=True,
    art=art,surfaceflinger_sha256=sha(render),composer_sha256=sha(composer),
    libui_sha256=sha(libui),gralloc_sha256=sha(gralloc),
    startup_check_scope='Host test of extracted pre-fork function with lock-contract doubles; ARM build',
    hardware_tested=False,hardware_validated=False)
(project/'evidence/v13-combined-fixes-contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
