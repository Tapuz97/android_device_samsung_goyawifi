#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

static int load_module(const char *path, const char *parameters)
{
    const char *name = strrchr(path, '/');
    if (!name || (strcmp(name, "/mlan.ko") && strcmp(name, "/sd8xxx.ko")))
        return 2;
    int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) {
        perror("open radio module");
        return 1;
    }
    struct stat st;
    if (fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_size < 64
            || st.st_size > 2 * 1024 * 1024) {
        close(fd);
        return 2;
    }
    size_t size = st.st_size;
    void *module = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (module == MAP_FAILED) {
        perror("mmap radio module");
        return 1;
    }
    if (memcmp(module, "\177ELF", 4)) {
        munmap(module, size);
        return 2;
    }
    long result = syscall(SYS_init_module, module, size, parameters);
    if (result)
        perror("init_module radio");
    munmap(module, size);
    return result ? 1 : 0;
}

#ifdef __ANDROID__
static int start_radio(void)
{
    static const char base[] = "/sys/devices/platform/sd8x-rfkill/rfkill/rfkill0";
    char path[sizeof(base) + sizeof("/state")];
    snprintf(path, sizeof(path), "%s/name", base);
    int name_fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (name_fd < 0) {
        perror("open SD8777 rfkill name");
        return 1;
    }
    char name[32] = {0};
    ssize_t bytes = read(name_fd, name, sizeof(name) - 1);
    close(name_fd);
    if (bytes != 12 || memcmp(name, "sd8xxx-wlan\n", 12)) {
        fputs("Unexpected SD8777 rfkill name\n", stderr);
        return 1;
    }
    snprintf(path, sizeof(path), "%s/state", base);
    int state_fd = open(path, O_RDWR | O_CLOEXEC | O_NOFOLLOW);
    if (state_fd < 0) {
        perror("open SD8777 rfkill state");
        return 1;
    }
    char old_state;
    if (read(state_fd, &old_state, 1) != 1 || old_state != '0') {
        fputs("Unexpected initial SD8777 rfkill state\n", stderr);
        close(state_fd);
        return 1;
    }
    if (lseek(state_fd, 0, SEEK_SET) < 0 || write(state_fd, "1", 1) != 1) {
        perror("enable SD8777");
        close(state_fd);
        return 1;
    }
    sleep(2);  // The SDIO device enumerates asynchronously after rfkill changes.
    int mlan = load_module("/vendor/etc/wifi/modules/mlan.ko", "");
    int result = mlan;
    if (!mlan) {
        result = load_module("/vendor/etc/wifi/modules/sd8xxx.ko",
                "drv_mode=1 sta_name=wlan cfg80211_wext=4 "
                "fw_name=mrvl/sd8777_uapsta.bin cal_data_cfg=mrvl/cal_data.conf");
        if (result && syscall(SYS_delete_module, "mlan", O_NONBLOCK))
            perror("unload SD8777 mlan");
    }
    if (result && (lseek(state_fd, 0, SEEK_SET) < 0 || write(state_fd, "0", 1) != 1))
        perror("restore SD8777 rfkill state");
    close(state_fd);
    return result;
}
#endif

int main(int argc, char **argv)
{
    if (getuid() != 0)
        return 2;
#ifdef __ANDROID__
    (void)argv;
    if (argc == 1)
        return start_radio();
    return 2;
#else
    if (argc != 3)
        return 2;
    return load_module(argv[1], argv[2]);
#endif
}
