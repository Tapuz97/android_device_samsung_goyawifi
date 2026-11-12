"""Apply the combined compositor initialization and startup corrections."""
from pathlib import Path
import subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo = Path('/root/t110-build/lineage20/hardware/interfaces')
rel = Path('graphics/composer/2.1/default/service.cpp')
p = repo / rel
s = p.read_text()
assert 'T110: Vivante process state initialized before HWC' not in s
s = s.replace('#include <sched.h>', '#include <sched.h>\n#include <dlfcn.h>\n#include <android-base/properties.h>')
anchor = '    android::sp<IComposer> composer = HwcLoader::load();'
assert s.count(anchor) == 1
s = s.replace(anchor, '''    // Stock T110 HWC calls gcoHAL_Get2DEngine before gralloc has allocated
    // any buffers. Unlike old SurfaceFlinger, this standalone service has
    // not loaded EGL, so Vivante's explicit per-process initialization has
    // never run. The verified stock constructor is PID-guarded/idempotent.
    if (android::base::GetBoolProperty("ro.t110.legacy_gpu", false)) {
        void* gal = dlopen("libGAL.so", RTLD_NOW | RTLD_LOCAL);
        auto initialize = gal ? reinterpret_cast<int (*)()>(
                dlsym(gal, "gcoOS_ModuleConstructor")) : nullptr;
        if (!initialize || initialize() < 0) {
            ALOGE("T110: Vivante process initialization failed before HWC");
            return 1;
        }
        // Keep the driver loaded for the lifetime of its HAL objects.
        ALOGI("T110: Vivante process state initialized before HWC");
    }

''' + anchor)
p.write_text(s)
bp = repo / 'graphics/composer/2.1/default/Android.bp'
s = bp.read_text()
assert '"libdl"' not in s
s = s.replace('        "libbase",', '        "libbase",\n        "libdl",')
bp.write_text(s)
diff = subprocess.check_output(['git', '-C', str(repo), 'diff', '--', str(rel), str(bp.relative_to(repo))])
assert diff and b'gcoOS_ModuleConstructor' in diff
(project / 'patches/0031-composer-t110-vivante-initialization.patch').write_bytes(diff)
print('Composer patch prepared')
