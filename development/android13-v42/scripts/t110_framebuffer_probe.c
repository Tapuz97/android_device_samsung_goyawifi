/* Run on the T110 diagnostic. --pattern briefly replaces the visible page. */
#include <errno.h>
#include <fcntl.h>
#include <linux/fb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

static uint32_t channel(struct fb_bitfield field)
{
    return field.length ? ((1u << field.length) - 1u) << field.offset : 0;
}

int main(int argc, char **argv)
{
    int pattern = argc == 2 && !strcmp(argv[1], "--pattern");
    if ((argc != 1 && !pattern) || access("/t110-native-diagnostic", F_OK)) {
        fprintf(stderr, "Usage in T110 RAM diagnostic: t110_framebuffer_probe [--pattern]\n");
        return 2;
    }
    int mode = pattern ? O_RDWR : O_RDONLY;
    int fd = open("/dev/graphics/fb0", mode | O_CLOEXEC);
    if (fd < 0)
        fd = open("/dev/fb0", mode | O_CLOEXEC);
    if (fd < 0) {
        perror("open fb0");
        return 1;
    }
    struct fb_fix_screeninfo fixed;
    struct fb_var_screeninfo var;
    if (ioctl(fd, FBIOGET_FSCREENINFO, &fixed) < 0 ||
        ioctl(fd, FBIOGET_VSCREENINFO, &var) < 0) {
        perror("get framebuffer geometry");
        close(fd);
        return 1;
    }
    printf("fb0 %.16s %ux%u, virtual %ux%u, offset %u,%u, %u bpp, stride %u, mapped bytes %u\n",
           fixed.id, var.xres, var.yres, var.xres_virtual, var.yres_virtual,
           var.xoffset, var.yoffset, var.bits_per_pixel, fixed.line_length, fixed.smem_len);
    if (!pattern) {
        close(fd);
        return 0;
    }

    const struct fb_bitfield fields[] = {var.red, var.green, var.blue, var.transp};
    uint32_t channel_mask = 0;
    for (size_t i = 0; i < sizeof(fields)/sizeof(fields[0]); ++i) {
        struct fb_bitfield field = fields[i];
        if (field.length > 8 || field.offset > 31 || field.offset + field.length > 32 ||
            field.msb_right || (channel_mask & channel(field))) {
            fprintf(stderr, "Unsupported framebuffer channel layout\n");
            close(fd);
            return 2;
        }
        channel_mask |= channel(field);
    }
    struct fb_var_screeninfo display = var;
    if (var.yres == 600 && var.yres_virtual >= 1200 && fixed.ypanstep &&
        var.yres % fixed.ypanstep == 0)
        display.yoffset = var.yoffset == 0 ? var.yres : 0;
    uint64_t start = (uint64_t)display.yoffset * fixed.line_length + (uint64_t)var.xoffset * 4;
    uint64_t row_bytes = (uint64_t)var.xres * 4;
    if (var.bits_per_pixel != 32 || var.xres != 1024 || var.yres != 600 ||
        fixed.type != FB_TYPE_PACKED_PIXELS || fixed.visual != FB_VISUAL_TRUECOLOR ||
        (uint64_t)var.xoffset * 4 + row_bytes > fixed.line_length ||
        start + (uint64_t)(var.yres - 1) * fixed.line_length + row_bytes > fixed.smem_len ||
        start % 4 || fixed.line_length % 4 || !var.red.length || !var.green.length || !var.blue.length) {
        fprintf(stderr, "Framebuffer geometry is outside the expected T110 visible page\n");
        close(fd);
        return 2;
    }
    unsigned char *saved = malloc((size_t)row_bytes * var.yres);
    if (!saved) {
        perror("allocate visible page backup");
        close(fd);
        return 1;
    }
    unsigned char *mapped = mmap(NULL, fixed.smem_len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) {
        perror("map framebuffer");
        free(saved);
        close(fd);
        return 1;
    }
    const uint32_t colors[] = {channel(var.red), channel(var.green), channel(var.blue),
                               channel(var.red) | channel(var.green) | channel(var.blue)};
    for (unsigned int y = 0; y < var.yres; ++y) {
        unsigned char *row = mapped + start + (size_t)y * fixed.line_length;
        memcpy(saved + (size_t)y * row_bytes, row, (size_t)row_bytes);
        uint32_t *pixels = (uint32_t *)row;
        for (unsigned int x = 0; x < var.xres; ++x)
            pixels[x] = colors[4 * x / var.xres] | channel(var.transp);
    }
    __sync_synchronize();
    int presented = ioctl(fd, FBIOPAN_DISPLAY, &display) == 0;
    if (!presented) {
        perror("present framebuffer page");
    } else {
        printf("Presenting red, green, blue and white bars for 12 seconds at yoffset %u\n", display.yoffset);
        fflush(stdout);
        sleep(12);
        if (ioctl(fd, FBIOPAN_DISPLAY, &var) < 0) {
            perror("restore original framebuffer scanout");
            presented = 0;
        }
    }
    for (unsigned int y = 0; y < var.yres; ++y)
        memcpy(mapped + start + (size_t)y * fixed.line_length,
               saved + (size_t)y * row_bytes, (size_t)row_bytes);
    munmap(mapped, fixed.smem_len);
    free(saved);
    close(fd);
    puts("Framebuffer page restored");
    return presented ? 0 : 1;
}
