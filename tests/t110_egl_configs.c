/* Enumerate supported window configurations without creating a display surface. */
#include <EGL/egl.h>
#include <dlfcn.h>
#include <stdio.h>
int main(void) {
    void *gal = dlopen("/system/vendor/lib/libGAL.so", RTLD_NOW | RTLD_GLOBAL);
    if (!gal) { fprintf(stderr, "%s\n", dlerror()); return 1; }
    int (*initialize)(void) = (int (*)(void))dlsym(gal, "gcoOS_ModuleConstructor");
    if (!initialize || initialize()) return 2;
    EGLDisplay d = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    EGLint major, minor, count;
    if (!eglInitialize(d, &major, &minor)) return 3;
    EGLConfig configs[256];
    if (!eglGetConfigs(d, configs, 256, &count)) return 4;
    printf("{\"egl\":\"%d.%d\",\"configurations\":[", major, minor);
    int printed = 0;
    for (int i = 0; i < count; ++i) {
        EGLint visual, id, surface, renderable;
        if (!eglGetConfigAttrib(d, configs[i], EGL_NATIVE_VISUAL_ID, &visual) ||
            !eglGetConfigAttrib(d, configs[i], EGL_CONFIG_ID, &id) ||
            !eglGetConfigAttrib(d, configs[i], EGL_SURFACE_TYPE, &surface) ||
            !eglGetConfigAttrib(d, configs[i], EGL_RENDERABLE_TYPE, &renderable)) return 5;
        if (!(surface & EGL_WINDOW_BIT) || !(renderable & EGL_OPENGL_ES2_BIT)) continue;
        printf("%s{\"id\":%d,\"visual\":%d,\"surface\":%d}", printed++ ? "," : "", id, visual, surface);
    }
    printf("]}\n");
    eglTerminate(d);
    return 0;
}
