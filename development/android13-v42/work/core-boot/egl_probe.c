#include <stdbool.h>

extern void android_set_application_target_sdk_version(int target);
extern void *dlopen(const char *filename, int flags);
extern void *dlsym(void *handle, const char *symbol);
extern const char *dlerror(void);
extern int dprintf(int fd, const char *format, ...);
extern _Noreturn void _exit(int status);

static int probe(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    bool legacy = argv[1][0] == '2' && argv[1][1] == '2' && argv[1][2] == '\0';
    if (legacy)
        android_set_application_target_sdk_version(22);

    void *egl = dlopen("libEGL_MRVL.so", 2); // RTLD_NOW
    if (!egl) {
        dprintf(2, "EGL_DLOPEN_FAILED: %s\n", dlerror());
        return 3;
    }
    void *gles = dlopen("libGLESv2_MRVL.so", 2);
    if (!gles) {
        dprintf(2, "GLES2_DLOPEN_FAILED: %s\n", dlerror());
        return 4;
    }
    dprintf(2, "T110_EGL_GLES2_LOAD_PASS legacy_target=%d\n", legacy);

    void *(*get_display)(void *) = dlsym(egl, "eglGetDisplay");
    unsigned int (*initialize)(void *, int *, int *) = dlsym(egl, "eglInitialize");
    unsigned int (*terminate)(void *) = dlsym(egl, "eglTerminate");
    int (*get_error)(void) = dlsym(egl, "eglGetError");
    if (!get_display || !initialize || !terminate || !get_error)
        return 5;

    void *display = get_display(0);
    int major, minor;
    if (!display || !initialize(display, &major, &minor)) {
        dprintf(2, "EGL_INIT_FAILED: 0x%x\n", get_error());
        return 6;
    }
    dprintf(2, "T110_EGL_INIT_PASS version=%d.%d\n", major, minor);
    terminate(display);
    return 0;
}

int main(int argc, char **argv)
{
    _exit(probe(argc, argv));
}
