#include <android/dlext.h>
#include <dlfcn.h>
#include <hardware/hardware.h>
#include <hardware/gralloc.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "T110Yv12Layout.h"

typedef struct android_namespace_t *(*create_namespace_fn)(const char *, const char *,
        const char *, uint64_t, const char *, struct android_namespace_t *);
typedef bool (*link_namespaces_fn)(struct android_namespace_t *, struct android_namespace_t *, const char *);
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *f = fopen(argv[1], "r");
    char shared[8192];
    if (!f || !fgets(shared, sizeof(shared), f)) return 3;
    fclose(f);
    void *api = dlopen("libdl_android.so", RTLD_NOW | RTLD_LOCAL);
    create_namespace_fn create = api ? (create_namespace_fn)dlsym(api, "android_create_namespace") : NULL;
    link_namespaces_fn link = api ? (link_namespaces_fn)dlsym(api, "android_link_namespaces") : NULL;
    if (!create || !link) { fprintf(stderr, "namespace_api=%s\n", dlerror()); return 4; }
    struct android_namespace_t *ns = create("t110_codec_probe", NULL,
            "/apex/com.android.media.swcodec/lib", 1,
            "/apex/com.android.media.swcodec/lib:/system/lib", NULL);
    if (!ns || !link(ns, NULL, shared)) { fprintf(stderr, "namespace_create=%s\n", dlerror()); return 5; }
    android_dlextinfo info = {0};
    info.flags = ANDROID_DLEXT_USE_NAMESPACE;
    info.library_namespace = ns;
    void *old = android_dlopen_ext("libhardware.so", RTLD_NOW | RTLD_LOCAL, &info);
    printf("old_soname_lookup=%s error=%s\n", old ? "OPENED" : "MISSING", dlerror());
    if (old) return 6; /* The negative control must reproduce the codec namespace. */
    void *fixed = android_dlopen_ext("/system/lib/libhardware.so", RTLD_NOW | RTLD_LOCAL, &info);
    if (!fixed) { fprintf(stderr, "absolute_lookup=%s\n", dlerror()); return 7; }
    int (*get_module)(const char *, const hw_module_t **) = dlsym(fixed, "hw_get_module");
    if (!get_module) { fprintf(stderr, "hw_get_module=%s\n", dlerror()); return 8; }
    const hw_module_t *module = NULL;
    int ret = get_module("gralloc", &module);
    printf("absolute_lookup=OPENED gralloc_module_status=%d module=%s\n", ret,
            module ? module->name : "NULL");
    if (ret || !module) return 9;
    int (*initialize)(void) = dlsym(module->dso, "gcoOS_ModuleConstructor");
    if (!initialize || initialize() < 0) return 10;
    alloc_device_t *allocator = NULL;
    if (gralloc_open(module, &allocator)) return 11;
    buffer_handle_t handle = NULL;
    int stride = 0;
    ret = allocator->alloc(allocator, 256, 144, HAL_PIXEL_FORMAT_YV12,
            GRALLOC_USAGE_SW_READ_OFTEN | GRALLOC_USAGE_SW_WRITE_OFTEN, &handle, &stride);
    printf("yv12_alloc=%d stride=%d gralloc_api=%x\n", ret, stride, module->module_api_version);
    if (ret) { gralloc_close(allocator); return 12; }
    const gralloc_module_t *gralloc = (const gralloc_module_t *)module;
    int result = 0;
    /* Match Gralloc0Hal: some vendor API0.1 modules fill this callback too. */
    if (gralloc->lock_ycbcr) {
        struct android_ycbcr planes = {0};
        ret = gralloc->lock_ycbcr(gralloc, handle, GRALLOC_USAGE_SW_READ_OFTEN, 0, 0, 256, 144, &planes);
        printf("yv12_lock_ycbcr=%d ystride=%zu cstride=%zu chroma_step=%zu\n",
                ret, planes.ystride, planes.cstride, planes.chroma_step);
        if (!ret) gralloc->unlock(gralloc, handle);
        else result = 13;
    } else {
        printf("yv12_lock_ycbcr=UNAVAILABLE\n");
        struct t110_yv12_layout sizes;
        void *data = NULL;
        ret = gralloc->lock(gralloc, handle,
                GRALLOC_USAGE_SW_READ_OFTEN | GRALLOC_USAGE_SW_WRITE_OFTEN,
                0, 0, 256, 144, &data);
        if (ret || !data || !t110_compute_yv12_layout(256, 144, stride, &sizes)) {
            printf("yv12_raw_lock=%d\n", ret);
            if (!ret) gralloc->unlock(gralloc, handle);
            result = 14;
        } else {
            unsigned char *y = data;
            memset(y, 16, sizes.y_size);
            memset(y + sizes.y_size, 128, sizes.c_size);
            memset(y + sizes.y_size + sizes.c_size, 192, sizes.c_size);
            gralloc->unlock(gralloc, handle);
            data = NULL;
            ret = gralloc->lock(gralloc, handle, GRALLOC_USAGE_SW_READ_OFTEN,
                    0, 0, 256, 144, &data);
            y = data;
            bool valid = !ret && y && y[0] == 16 && y[sizes.y_size - 1] == 16 &&
                    y[sizes.y_size] == 128 && y[sizes.y_size + sizes.c_size - 1] == 128 &&
                    y[sizes.y_size + sizes.c_size] == 192 && y[sizes.total_size - 1] == 192;
            if (!ret) gralloc->unlock(gralloc, handle);
            printf("yv12_raw_layout=%s ystride=%zu cstride=%zu bytes=%zu\n",
                    valid ? "PASS" : "FAIL", sizes.y_stride, sizes.c_stride, sizes.total_size);
            if (!valid) result = 15;
        }
    }
    allocator->free(allocator, handle);
    gralloc_close(allocator);
    return result;
}
