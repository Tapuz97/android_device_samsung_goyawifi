// Retain the Android13 T110 process-initialization contract on Nougat.
#ifndef ANDROID_UI_T110_VIVANTE_H
#define ANDROID_UI_T110_VIVANTE_H
#include <dlfcn.h>
#include <errno.h>
namespace android {
static inline int t110InitializeVivante(void* driver) {
    // libGAL has no ELF initializer. Its constructor has its own PID guard;
    // do not cache success across fork or resolve a different library instance.
    if (!driver) return -ENODEV;
    auto initialize = reinterpret_cast<int (*)()>(
            dlsym(driver, "gcoOS_ModuleConstructor"));
    return initialize ? initialize() : -ENODEV;
}
}
#endif
