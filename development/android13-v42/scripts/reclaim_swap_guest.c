#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/reboot.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/swap.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <unistd.h>

static void finish(int ok, const char *message)
{
    printf("RECLAIM_SWAP_%s %s\n", ok ? "PASS" : "FAIL", message);
    fflush(stdout);
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_POWER_OFF, 0);
    for (;;) pause();
}

static void write_control(const char *path, const char *value)
{
    int fd = open(path, O_WRONLY);
    if (fd < 0 || write(fd, value, strlen(value)) != (ssize_t)strlen(value))
        finish(0, path);
    close(fd);
}

static unsigned long counter(const char *name)
{
    FILE *f = fopen("/proc/vmstat", "r");
    char key[128];
    unsigned long value;
    if (!f) finish(0, "vmstat");
    while (fscanf(f, "%127s %lu", key, &value) == 2) {
        if (!strcmp(key, name)) { fclose(f); return value; }
    }
    fclose(f);
    finish(0, "missing swap counter");
    return 0;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    mkdir("/proc", 0755); mkdir("/sys", 0755); mkdir("/dev", 0755);
    if (mount("proc", "/proc", "proc", 0, NULL) ||
        mount("sysfs", "/sys", "sysfs", 0, NULL)) finish(0, "mount");
    write_control("/sys/block/zram0/disksize", "134217728");
    unsigned int major_id, minor_id;
    FILE *device = fopen("/sys/block/zram0/dev", "r");
    if (!device || fscanf(device, "%u:%u", &major_id, &minor_id) != 2)
        finish(0, "zram device identity");
    fclose(device);
    if (mknod("/dev/zram0", S_IFBLK | 0600, makedev(major_id, minor_id)))
        finish(0, "zram node");
    unsigned char header[4096] = {0};
    uint32_t version = 1, last_page = 134217728 / 4096 - 1;
    memcpy(header + 1024, &version, sizeof(version));
    memcpy(header + 1028, &last_page, sizeof(last_page));
    memcpy(header + sizeof(header) - 10, "SWAPSPACE2", 10);
    int fd = open("/dev/zram0", O_RDWR);
    if (fd < 0 || write(fd, header, sizeof(header)) != sizeof(header))
        finish(0, "swap header");
    close(fd);
    if (swapon("/dev/zram0", 0)) finish(0, "swapon");
    unsigned long before_out = counter("pswpout"), before_in = counter("pswpin");
    const size_t pages = 160 * 1024 * 1024 / 4096;
    unsigned char *memory = mmap(NULL, pages * 4096, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (memory == MAP_FAILED) finish(0, "pressure allocation");
    for (size_t page = 0; page < pages; page++) {
        memset(memory + page * 4096, (page % 251) + 1, 4096);
        *(uint32_t *)(memory + page * 4096) = (uint32_t)page;
    }
    for (size_t page = 0; page < pages; page++) {
        if (*(volatile uint32_t *)(memory + page * 4096) != page ||
            memory[page * 4096 + 4095] != (page % 251) + 1)
            finish(0, "memory integrity across swap");
    }
    unsigned long after_out = counter("pswpout"), after_in = counter("pswpin");
    printf("RECLAIM_SWAP_COUNTERS out=%lu in=%lu verified_pages=%zu\n",
           after_out-before_out, after_in-before_in, pages);
    if (after_out <= before_out || after_in <= before_in)
        finish(0, "normal reclaim did not use compressed swap");
    finish(1, "normal reclaim swaps anonymous pages and preserves their contents");
    return 0;
}
