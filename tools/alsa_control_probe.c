#include <dlfcn.h>
#include <stdio.h>
int main(void) {
    void *plugin = dlopen("/system/usr/lib/alsa-lib/libasound_module_ctl_codec.so", RTLD_NOW);
    printf("codec plugin: %s\n", plugin ? "loaded" : dlerror());
    void *lib = dlopen("libasound.so", RTLD_NOW);
    if (!lib) { puts(dlerror()); return 1; }
    int (*open_ctl)(void **, const char *, int) = dlsym(lib, "snd_ctl_open");
    int (*close_ctl)(void *) = dlsym(lib, "snd_ctl_close");
    const char *(*error)(int) = dlsym(lib, "snd_strerror");
    if (!open_ctl || !close_ctl || !error) return 2;
    void *ctl = NULL;
    int result = open_ctl(&ctl, "codec", 0);
    printf("codec control: %d %s\n", result, error(result));
    if (result == 0) close_ctl(ctl);
    return result == 0 ? 0 : 3;
}
