/* Enumerate the kernel mixer's controls without reading or changing routes. */
#include <fcntl.h>
#include <sound/asound.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <unistd.h>

int main(void) {
    int fd = open("/dev/snd/controlC0", O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        perror("ALSA control");
        return 1;
    }
    struct snd_ctl_elem_list list = {0};
    if (ioctl(fd, SNDRV_CTL_IOCTL_ELEM_LIST, &list) || !list.count || list.count > 4096) {
        perror("ALSA control count");
        close(fd);
        return 1;
    }
    list.space = list.count;
    list.pids = calloc(list.space, sizeof(*list.pids));
    if (!list.pids) {
        close(fd);
        return 1;
    }
    if (ioctl(fd, SNDRV_CTL_IOCTL_ELEM_LIST, &list) || list.used > list.space) {
        perror("ALSA control enumeration");
        free(list.pids);
        close(fd);
        return 1;
    }
    for (unsigned i = 0; i < list.used; ++i) {
        const struct snd_ctl_elem_id *id = &list.pids[i];
        printf("%u iface=%u index=%u %.*s\n", id->numid, id->iface, id->index,
               (int)sizeof(id->name), (const char *)id->name);
    }
    free(list.pids);
    close(fd);
    return 0;
}
