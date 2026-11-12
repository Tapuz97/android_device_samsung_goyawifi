"""Apply the captured allocator and app-EGL fixes without any tablet access."""
from pathlib import Path
import subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
tree = Path('/root/t110-build/lineage20')
evidence = project / 'evidence/offline-v26'
evidence.mkdir(exist_ok=True)

def change(path, old, new):
    text = path.read_text()
    if new in text:
        return
    assert text.count(old) == 1, path
    path.write_text(text.replace(old, new))

allocator = tree / 'frameworks/av/media/codec2/vndk/C2AllocatorIon.cpp'
change(allocator, '''    if (mIonFd < 0) {
        switch (errno) {
        case ENOENT:    mInit = C2_OMITTED; break;
        default:        mInit = c2_map_errno<EACCES>(errno); break;
        }
    } else {
        C2MemoryUsage minUsage = { 0, 0 };
        C2MemoryUsage maxUsage = { C2MemoryUsage::CPU_READ, C2MemoryUsage::CPU_WRITE };
        Traits traits = { "android.allocator.ion", id, LINEAR, minUsage, maxUsage };
        mTraits = std::make_shared<Traits>(traits);
        mBlockSize = ::getpagesize();
    }
''', '''    // Traits remain queryable even when /dev/ion cannot be opened. C2Store
    // calls setUsageMapper before any allocation checks mInit.
    const int openError = mIonFd < 0 ? errno : 0;
    C2MemoryUsage minUsage = { 0, 0 };
    C2MemoryUsage maxUsage = { C2MemoryUsage::CPU_READ, C2MemoryUsage::CPU_WRITE };
    Traits traits = { "android.allocator.ion", id, LINEAR, minUsage, maxUsage };
    mTraits = std::make_shared<Traits>(traits);
    mBlockSize = ::getpagesize();
    if (mIonFd < 0) {
        switch (openError) {
        case ENOENT:    mInit = C2_OMITTED; break;
        default:        mInit = c2_map_errno<EACCES>(openError); break;
        }
        ALOGW("ION unavailable; preserving allocator traits and allocation error %d", mInit);
    }
''')

loader = tree / 'frameworks/native/opengl/libs/EGL/Loader.cpp'
change(loader, '''    ALOGD("loaded %s", driver_absolute_path);

    return dso;
''', '''    if (android::base::GetBoolProperty("ro.t110.legacy_gpu", false) &&
            (!strcmp(kind, "EGL") || !strcmp(kind, "GLES"))) {
        // This stock libGAL has no DT_INIT/DT_INIT_ARRAY. Resolve through
        // the EGL handle so initialization uses its own linker namespace.
        // The vendor constructor checks the PID, including after fork.
        auto initialize = reinterpret_cast<int (*)()>(
                dlsym(dso, "gcoOS_ModuleConstructor"));
        const int status = initialize ? initialize() : -1;
        if (status < 0) {
            ALOGE("T110 EGL: Vivante process initialization failed: %d", status);
            do_android_unload_sphal_library(dso);
            return nullptr;
        }
        ALOGI("T110 EGL: Vivante process initialized before entrypoint lookup");
    }
    ALOGD("loaded %s", driver_absolute_path);

    return dso;
''')

gralloc = tree / 'frameworks/native/libs/ui/Gralloc2.cpp'
change(gralloc, '''        int error = getModule(GRALLOC_HARDWARE_MODULE_ID, &module);
        if (!error) error = gralloc_open(module, &mDevice);
''', '''        int error = getModule(GRALLOC_HARDWARE_MODULE_ID, &module);
        if (!error) {
            // An app can allocate a buffer before creating its first EGL
            // display. Use the HAL's own libGAL dependency in that case.
            auto initialize = module && module->dso ? reinterpret_cast<int (*)()>(
                    dlsym(module->dso, "gcoOS_ModuleConstructor")) : nullptr;
            if (!initialize || initialize() < 0) {
                ALOGE("T110 legacy gralloc: Vivante process initialization failed");
                error = -ENODEV;
            }
        }
        if (!error) error = gralloc_open(module, &mDevice);
''')

for path in [project / 'work/core-boot/init.mrvl.rc']:
    text = path.read_text()
    text = text.replace('chmod 0660 /dev/galcore', 'chmod 0666 /dev/galcore')
    text = text.replace('chmod 0660 /dev/ion', 'chmod 0666 /dev/ion')
    path.write_text(text)
package = project / 'scripts/package_core_boot.py'
text = package.read_text()
text = text.replace('/dev/galcore 0660 system graphics', '/dev/galcore 0666 system graphics')
text = text.replace('/dev/ion 0660 system graphics', '/dev/ion 0666 system graphics')
package.write_text(text)

policy = project / 'work/device/samsung/t110_bringup/sepolicy/t110_gpu.te'
text = policy.read_text()
addition = '''
# The stock in-process gralloc opens ION O_RDWR. Modern app and system-server
# policy already grants the remaining ION operations, but only read access.
# Keep isolated apps excluded, as in the platform's existing ION/GPU rules.
allow { appdomain -isolated_app } ion_device:chr_file write;
allow system_server ion_device:chr_file write;
'''
if addition not in text:
    policy.write_text(text.rstrip() + '\n' + addition)

for repository, paths, name in [
    ('frameworks/av', ['media/codec2/vndk/C2AllocatorIon.cpp'],
     '0046-codec2-ion-error-state-traits.patch'),
    ('frameworks/native', ['opengl/libs/EGL/Loader.cpp'],
     '0047-egl-t110-process-initialization.patch'),
]:
    diff = subprocess.check_output(['git', 'diff', '--', *paths], cwd=tree/repository)
    assert diff
    (project / 'patches' / name).write_bytes(diff)

# Gralloc2 already carries patch0034. Export only this additional hunk,
# relative to its saved, previously built version rather than upstream HEAD.
import difflib
new = gralloc.read_text()
old = new.replace('''        if (!error) {
            // An app can allocate a buffer before creating its first EGL
            // display. Use the HAL's own libGAL dependency in that case.
            auto initialize = module && module->dso ? reinterpret_cast<int (*)()>(
                    dlsym(module->dso, "gcoOS_ModuleConstructor")) : nullptr;
            if (!initialize || initialize() < 0) {
                ALOGE("T110 legacy gralloc: Vivante process initialization failed");
                error = -ENODEV;
            }
        }
''', '')
assert old != new
diff = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
    fromfile='a/libs/ui/Gralloc2.cpp', tofile='b/libs/ui/Gralloc2.cpp'))
(evidence / '0048-incremental-review.patch').write_text(diff)
# Supersede0034 in the reproducible build list: both touch the same added
# class, so reverse-checking the old full-class hunk would fail after this fix.
(project / 'patches/0048-gralloc-t110-process-initialization.patch').write_bytes(
    subprocess.check_output(['git', 'diff', '--', 'libs/ui/Gralloc2.cpp'],
                            cwd=tree/'frameworks/native'))

build = project / 'scripts/build_system_image.sh'
text = build.read_text()
anchor = " 'frameworks/base:0045-systemui-empty-active-appops.patch'; do"
replacement = " 'frameworks/base:0045-systemui-empty-active-appops.patch' 'frameworks/av:0046-codec2-ion-error-state-traits.patch' 'frameworks/native:0047-egl-t110-process-initialization.patch' 'frameworks/native:0048-gralloc-t110-process-initialization.patch'; do"
if replacement not in text:
    assert anchor in text
    build.write_text(text.replace(anchor, replacement))
text = build.read_text()
text = text.replace(" 'frameworks/native:0048-gralloc-t110-process-initialization.patch'; do", '; do')
text = text.replace('frameworks/native:0034-ui-t110-linear-scanout-targets.patch',
                    'frameworks/native:0048-gralloc-t110-process-initialization.patch')
build.write_text(text)

for path in [allocator, loader, gralloc]:
    (evidence / path.name).write_bytes(path.read_bytes())
print('OFFLINE_V26_SOURCES_APPLIED; no tablet access or boots')
