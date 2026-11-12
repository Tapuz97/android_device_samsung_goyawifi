/* SPDX-License-Identifier: Apache-2.0 */
/* Test only the candidate HAL, restore brightness, never register a service. */
#include <dlfcn.h>
#include <hardware/lights.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

static int read_level(void)
{
    int level = -1;
    FILE *f = fopen("/sys/class/backlight/panel/brightness", "r");
    if (f) { if (fscanf(f, "%d", &level) != 1) level = -1; fclose(f); }
    return level;
}
static int set_level(struct light_device_t *light, unsigned level)
{
    struct light_state_t state;
    memset(&state, 0, sizeof(state));
    state.color = 0xff000000u | (level * 0x010101u);
    state.brightnessMode = BRIGHTNESS_MODE_USER;
    return light->set_light(light, &state);
}
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    int before = read_level();
    if (before < 0 || before > 255) return 3;
    void *lib = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!lib) { fprintf(stderr, "dlopen:%s\n", dlerror()); return 4; }
    struct hw_module_t *module = dlsym(lib, HAL_MODULE_INFO_SYM_AS_STR);
    if (!module || strcmp(module->id, LIGHTS_HARDWARE_MODULE_ID)) return 5;
    struct hw_device_t *device = NULL;
    if (module->methods->open(module, LIGHT_ID_BACKLIGHT, &device)) return 6;
    struct light_device_t *light = (struct light_device_t *)device;
    int result = 0;
    unsigned levels[] = {40, 220};
    for (unsigned i = 0; i < sizeof(levels)/sizeof(levels[0]); ++i) {
        int status = set_level(light, levels[i]);
        int actual = read_level();
        printf("requested=%u actual=%d status=%d\n", levels[i], actual, status);
        if (status || actual != (int)levels[i]) result = 7;
    }
    int restored = set_level(light, (unsigned)before);
    int after = read_level();
    printf("before=%d restored=%d status=%d\n", before, after, restored);
    if (restored || after != before) result = 8;
    struct light_state_t unsupported = {.brightnessMode = BRIGHTNESS_MODE_LOW_PERSISTENCE};
    int low = light->set_light(light, &unsupported);
    if (low != -ENOSYS || read_level() != before) result = 9;
    struct hw_device_t *other = NULL;
    int led = module->methods->open(module, LIGHT_ID_NOTIFICATIONS, &other);
    if (led != -EINVAL || other != NULL) result = 10;
    printf("low_persistence=%d unsupported_led=%d result=%d\n", low, led, result);
    device->close(device);dlclose(lib);return result;
}
