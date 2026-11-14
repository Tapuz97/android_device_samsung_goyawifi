/* SPDX-License-Identifier: Apache-2.0 */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <hardware/hardware.h>

int main(void) {
    if (getenv("LD_LIBRARY_PATH") || getenv("LD_PRELOAD") || getenv("T110_PROBE_LEGACY_SDK")) return 2;
    void* hardware=dlopen("libhardware.so",RTLD_NOW|RTLD_LOCAL);
    if (!hardware){fprintf(stderr,"FAIL libhardware: %s\n",dlerror());return 3;}
    int (*select_module)(const char*,const char*,const hw_module_t**)=dlsym(hardware,"hw_get_module_by_class");
    const hw_module_t* selected=0;
    if (!select_module||select_module("audio","primary",&selected)||!selected||!selected->name||
        strcmp(selected->name,"T110 ANI7 Audio Compatibility HAL")) {
        fputs("FAIL actual hardware-module selection did not choose the modern proxy\n",stderr);return 4;
    }
    puts("PASS real libhardware audio.primary selection chose the modern T110 proxy; device not opened");
    const char* libraries[]={"/vendor/lib/hw/audio.primary.t110.so","/vendor/lib/hw/audio.primary.mrvl.so",
        "/vendor/lib/alsa-lib/libasound_module_ctl_codec.so",
        "/vendor/lib/alsa-lib/libasound_module_ctl_phone.so",
        "/vendor/lib/alsa-lib/libasound_module_pcm_phone.so"};
    for (unsigned i=0;i<sizeof(libraries)/sizeof(libraries[0]);++i) {
        void* h=dlopen(libraries[i],RTLD_NOW|RTLD_LOCAL);
        if (!h) {fprintf(stderr,"FAIL %s: %s\n",libraries[i],dlerror());return 10;}
        if (i<2) {
            hw_module_t* m=dlsym(h,HAL_MODULE_INFO_SYM_AS_STR);
            const char* expected=i==0?"T110 ANI7 Audio Compatibility HAL":"Marvll audio HW HAL";
            if (!m||!m->name||strcmp(m->name,expected))return 11;
        }
    }
    void* alsa=dlopen("/vendor/lib/libasound.so",RTLD_NOW|RTLD_LOCAL);
    if (!alsa)return 12;
    int (*update)(void)=dlsym(alsa,"snd_config_update");
    int (*search)(void*,const char*,const char*,void**)=dlsym(alsa,"snd_config_search_definition");
    int (*field)(void*,const char*,void**)=dlsym(alsa,"snd_config_search");
    int (*get_string)(void*,const char**)=dlsym(alsa,"snd_config_get_string");
    void** config=dlsym(alsa,"snd_config");
    if (!update||!search||!field||!get_string||!config)return 13;
    int result=update();
    if (result<0){fprintf(stderr,"FAIL actual ALSA configuration: %d\n",result);return 14;}
    const char* types[]={"ctl_type","ctl_type","pcm_type"};
    const char* names[]={"codec","phone","phone"};
    const char* paths[]={"/vendor/lib/alsa-lib/libasound_module_ctl_codec.so",
        "/vendor/lib/alsa-lib/libasound_module_ctl_phone.so","/vendor/lib/alsa-lib/libasound_module_pcm_phone.so"};
    for (unsigned i=0;i<3;++i) {
        void* definition=0;void* value=0;const char* path=0;
        if (search(*config,types[i],names[i],&definition)<0||field(definition,"lib",&value)<0||
            get_string(value,&path)<0||strcmp(path,paths[i]))return 15;
        printf("PASS actual ALSA plugin configuration %s.%s=%s\n",types[i],names[i],path);
    }
    puts("PASS full-image production audio loading/config; normal SDK and namespaces; no hardware opened");
    return 0;
}
