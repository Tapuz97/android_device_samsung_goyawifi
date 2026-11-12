"""Load the optional legacy HAL without adding an APEX dependency to libui."""
from pathlib import Path
import subprocess
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/frameworks/native')
p=repo/'libs/ui/Gralloc2.cpp'
s=p.read_text()
s=s.replace('#include <hardware/gralloc.h>', '#include <hardware/gralloc.h>\n#include <dlfcn.h>')
old='''        const hw_module_t* module = nullptr;
        int error = hw_get_module(GRALLOC_HARDWARE_MODULE_ID, &module);'''
new='''        // libui also has an APEX variant. Keep this device-only legacy
        // backend optional instead of imposing libhardware on every APEX.
        void* library = dlopen("libhardware.so", RTLD_NOW | RTLD_LOCAL);
        auto getModule = library ? reinterpret_cast<int (*)(const char*, const hw_module_t**)>(
                dlsym(library, "hw_get_module")) : nullptr;
        if (!getModule) {
            ALOGE("T110 legacy gralloc loader unavailable");
            return;
        }
        // Keep the library loaded for the process-long alloc_device_t.
        const hw_module_t* module = nullptr;
        int error = getModule(GRALLOC_HARDWARE_MODULE_ID, &module);'''
assert s.count(old)==1
p.write_text(s.replace(old,new))
p=repo/'libs/ui/Android.bp'
s=p.read_text()
assert s.count('        "libhardware",\n')==1
p.write_text(s.replace('        "libhardware",\n',''))
patch=subprocess.check_output(['git','-C',str(repo),'diff','--','libs/ui/Gralloc2.cpp','libs/ui/Android.bp'])
(project/'patches/0030-ui-t110-retained-gralloc-owners.patch').write_bytes(patch)
print('Optional legacy HAL loader patched; APEX dependency unchanged.')
