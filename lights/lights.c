/* SPDX-License-Identifier: Apache-2.0 */
/* SM-T110 backlight adapter for Android's standard legacy-to-HIDL lights HAL. */
#include <errno.h>
#include <fcntl.h>
#include <hardware/lights.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef T110_BACKLIGHT_PATH
#define T110_BACKLIGHT_PATH "/sys/class/backlight/panel/brightness"
#endif

static int set_backlight(struct light_device_t *device, const struct light_state_t *state)
{
    (void)device;
    if (!state) return -EINVAL;
    if (state->brightnessMode == BRIGHTNESS_MODE_LOW_PERSISTENCE) return -ENOSYS;
    unsigned color = state->color;
    unsigned level = (77 * ((color >> 16) & 255) +
                      150 * ((color >> 8) & 255) + 29 * (color & 255)) >> 8;
    char text[8];
    int size = snprintf(text, sizeof(text), "%u\n", level);
    int fd = open(T110_BACKLIGHT_PATH, O_WRONLY | O_CLOEXEC);
    if (fd < 0) return -errno;
    ssize_t wrote;
    do { wrote = write(fd, text, (size_t)size); } while (wrote < 0 && errno == EINTR);
    int result = wrote == size ? 0 : wrote < 0 ? -errno : -EIO;
    close(fd);
    return result;
}

static int close_light(struct hw_device_t *device)
{
    free(device);
    return 0;
}

static int open_light(const struct hw_module_t *module, const char *name,
                      struct hw_device_t **out)
{
    if (!out || !name || strcmp(name, LIGHT_ID_BACKLIGHT)) return -EINVAL;
    *out = NULL;
    struct light_device_t *device = calloc(1, sizeof(*device));
    if (!device) return -ENOMEM;
    device->common.tag = HARDWARE_DEVICE_TAG;
    device->common.version = LIGHTS_DEVICE_API_VERSION_2_0;
    device->common.module = (struct hw_module_t *)module;
    device->common.close = close_light;
    device->set_light = set_backlight;
    *out = &device->common;
    return 0;
}

static struct hw_module_methods_t methods = { .open = open_light };
struct hw_module_t HAL_MODULE_INFO_SYM = {
    .tag = HARDWARE_MODULE_TAG,
    .module_api_version = HARDWARE_MODULE_API_VERSION(1, 0),
    .hal_api_version = HARDWARE_HAL_API_VERSION,
    .id = LIGHTS_HARDWARE_MODULE_ID,
    .name = "Samsung SM-T110 panel backlight",
    .author = "SM-T110 bring-up contributors",
    .methods = &methods,
};
