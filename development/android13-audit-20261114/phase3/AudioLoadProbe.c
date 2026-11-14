/* SPDX-License-Identifier: Apache-2.0 */
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <hardware/hardware.h>

int main(void) {
    puts("Android Bionic loader probe started");fflush(stdout);
    /* Diagnostic only: inspect legacy dependencies before the rebuilt linker
       with exact-path exceptions exists. Never included in the real HAL. */
    if(getenv("T110_PROBE_LEGACY_SDK")) {
        void (*setSdk)(int)=dlsym(RTLD_DEFAULT,"android_set_application_target_sdk_version");
        if(!setSdk){void* h=dlopen("/system/lib/libdl_android.so",RTLD_NOW);if(h)setSdk=dlsym(h,"android_set_application_target_sdk_version");}
        if(!setSdk)return 10;
        setSdk(22);puts("Diagnostic probe process only: legacy target SDK22");
    }
    const char* libraries[]={"/vendor/lib/hw/audio.primary.mrvl.so",
        "/vendor/lib/alsa-lib/libasound_module_ctl_codec.so",
        "/vendor/lib/alsa-lib/libasound_module_ctl_phone.so",
        "/vendor/lib/alsa-lib/libasound_module_pcm_phone.so"};
    for(unsigned i=0;i<sizeof(libraries)/sizeof(libraries[0]);++i) {
        void* h=dlopen(libraries[i],RTLD_NOW|RTLD_LOCAL);
        if(!h){fprintf(stderr,"FAIL %s: %s\n",libraries[i],dlerror());return 20+(int)i;}
        printf("Loaded %s\n",libraries[i]);fflush(stdout);
        if(i==0){hw_module_t* m=dlsym(h,HAL_MODULE_INFO_SYM_AS_STR);
            if(!m||!m->name||strcmp(m->name,"Marvll audio HW HAL"))return 30;}
    }
    void* alsa=dlopen("/vendor/lib/libasound.so",RTLD_NOW|RTLD_LOCAL);
    if(!alsa){fprintf(stderr,"ALSA: %s\n",dlerror());return 40;}
    int (*update)(void)=dlsym(alsa,"snd_config_update");
    int (*search)(void*,const char*,const char*,void**)=dlsym(alsa,"snd_config_search_definition");
    int (*field)(void*,const char*,void**)=dlsym(alsa,"snd_config_search");
    int (*getString)(void*,const char**)=dlsym(alsa,"snd_config_get_string");
    void** config=dlsym(alsa,"snd_config");
    if(!update||!search||!field||!getString||!config)return 41;
    int result=update();if(result<0){fprintf(stderr,"ALSA config update: %d\n",result);return 42;}
    void* definition=0;void* value=0;const char* path=0;
    if(search(*config,"ctl_type","codec",&definition)<0||field(definition,"lib",&value)<0||getString(value,&path)<0)return 43;
    printf("ALSA codec plugin configured at %s\n",path);
    if(strcmp(path,"/vendor/lib/alsa-lib/libasound_module_ctl_codec.so"))return 44;
    puts("PASS actual Android13 loader, stock audio/plugin relocations and ALSA config; no hardware opened");
    return 0;
}
