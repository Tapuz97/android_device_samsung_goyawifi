/* SPDX-License-Identifier: Apache-2.0 */
#include "LegacyDevice.h"
#include <dlfcn.h>
#include <cerrno>
#include <cstring>
#include <mutex>

namespace {
std::mutex loaderMutex;
hw_module_t* vendorModule=nullptr;
void* vendorLibrary=nullptr; // Conventional HAL-module lifetime: service lifetime.
int open(const hw_module_t*,const char* id,hw_device_t** out) {
    if(!out)return -EINVAL;
    *out=nullptr;
    if(!id||strcmp(id,AUDIO_HARDWARE_INTERFACE))return -EINVAL;
    std::lock_guard<std::mutex> lock(loaderMutex);
    if(!vendorModule) {
        void* handle=dlopen("/vendor/lib/hw/audio.primary.mrvl.so",RTLD_NOW|RTLD_LOCAL);
        if(!handle)return -ENODEV;
        auto* module=static_cast<hw_module_t*>(dlsym(handle,HAL_MODULE_INFO_SYM_AS_STR));
        if(!module||module->tag!=HARDWARE_MODULE_TAG||!module->id||strcmp(module->id,AUDIO_HARDWARE_MODULE_ID)||
           module->module_api_version!=AUDIO_MODULE_API_VERSION_0_1||!module->methods||!module->methods->open||
           !module->name||strcmp(module->name,"Marvll audio HW HAL")||
           !module->author||strcmp(module->author,"Marvell APSE/PIE")) {
            dlclose(handle);return -EINVAL;
        }
        vendorModule=module;vendorLibrary=handle;
        vendorModule->dso=vendorLibrary;
    }
    hw_device_t* original=nullptr;
    int result=vendorModule->methods->open(vendorModule,id,&original);
    if(result)return result;
    if(!original)return -ENODEV;
    audio_hw_device_t* adapted=nullptr;
    result=t110::adaptDevice(reinterpret_cast<t110::LegacyDevice*>(original),&adapted);
    if(result){if(original->close)original->close(original);return result;}
    *out=&adapted->common;return 0;
}
hw_module_methods_t methods={open};
}
extern "C" {
audio_module HAL_MODULE_INFO_SYM={
    .common={
        .tag=HARDWARE_MODULE_TAG,
        .module_api_version=AUDIO_MODULE_API_VERSION_0_1,
        .hal_api_version=HARDWARE_HAL_API_VERSION,
        .id=AUDIO_HARDWARE_MODULE_ID,
        .name="T110 ANI7 Audio Compatibility HAL",
        .author="The LineageOS Project",
        .methods=&methods,
        .dso=nullptr,
        .reserved={0},
    }
};
}
