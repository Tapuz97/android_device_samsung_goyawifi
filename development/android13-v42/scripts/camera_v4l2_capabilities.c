/* Read camera capabilities only; no format changes, buffers or capture. */
#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int fd = open("/dev/video0", O_RDWR | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) { perror("open video0"); return 1; }
    struct v4l2_capability cap = {0};
    if (ioctl(fd, VIDIOC_QUERYCAP, &cap)) { perror("QUERYCAP"); close(fd); return 1; }
    printf("driver=%s card=%s version=%u capabilities=0x%x device_caps=0x%x\n",
            cap.driver, cap.card, cap.version, cap.capabilities, cap.device_caps);
    for (unsigned n = 0; n < 32; ++n) {
        struct v4l2_fmtdesc fmt = {.index=n, .type=V4L2_BUF_TYPE_VIDEO_CAPTURE};
        if (ioctl(fd, VIDIOC_ENUM_FMT, &fmt)) {
            printf("ENUM_FMT end index=%u errno=%d\n", n, errno); break;
        }
        unsigned f = fmt.pixelformat;
        printf("format=%c%c%c%c description=%s flags=0x%x\n",
                f&255, (f>>8)&255, (f>>16)&255, f>>24, fmt.description, fmt.flags);
        for (unsigned i=0; i<16; ++i) {
            struct v4l2_frmsizeenum size = {.index=i,.pixel_format=f};
            if (ioctl(fd, VIDIOC_ENUM_FRAMESIZES, &size)) break;
            if (size.type == V4L2_FRMSIZE_TYPE_DISCRETE)
                printf("  size=%ux%u\n",size.discrete.width,size.discrete.height);
            else {
                printf("  size-range=%ux%u..%ux%u step=%ux%u type=%u\n",
                        size.stepwise.min_width,size.stepwise.min_height,
                        size.stepwise.max_width,size.stepwise.max_height,
                        size.stepwise.step_width,size.stepwise.step_height,size.type);
                break;
            }
        }
    }
    close(fd); return 0;
}
