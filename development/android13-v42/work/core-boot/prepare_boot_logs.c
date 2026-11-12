#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/xattr.h>
#include <unistd.h>

static void require(int condition, const char *step)
{
    if (!condition) { perror(step); exit(1); }
}

static void directory(const char *path)
{
    if (mkdir(path, 0700)) require(errno == EEXIST, path);
    struct stat info;
    require(lstat(path, &info) == 0 && S_ISDIR(info.st_mode), "real directory");
}

static void label_file(const char *path, const char *label, int create)
{
    int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | (create ? O_CREAT : 0), 0600);
    require(fd >= 0, path);
    struct stat info;
    require(fstat(fd, &info) == 0 && S_ISREG(info.st_mode), "regular file");
    require(fsetxattr(fd, "security.selinux", label, strlen(label) + 1, 0) == 0, "set label");
    char actual[128] = {0};
    require(fgetxattr(fd, "security.selinux", actual, sizeof(actual)) > 0 &&
            strcmp(actual, label) == 0, "read back label");
    require(fsync(fd) == 0, "sync labelled file");
    close(fd);
}

int main(void)
{
    require(getuid() == 0 && access("/sbin/recovery", X_OK) == 0, "TWRP root required");
    char cid[80] = {0};
    FILE *file = fopen("/sys/class/block/mmcblk0/device/cid", "r");
    require(file && fgets(cid, sizeof(cid), file), "read tablet CID");
    fclose(file);
    require(strcmp(cid, "1101003030384745T110_ADB_SERIAL\n") == 0, "tablet CID");
    const char *image = "/data/local/tmp/t110-rom-system.raw";
    struct stat info;
    require(lstat(image, &info) == 0 && S_ISREG(info.st_mode) && info.st_size == 1594884096,
            "staged system image");
    label_file(image, "u:object_r:shell_data_file:s0", 0);
    const char *parent = "/data/local/tmp/t110-bootlogs";
    directory(parent);
    char path[192], folder[160];
    const char *names[] = {"checkpoints.txt", "kernel-0.txt", "kernel-1.txt", "logger-status.txt"};
    for (int slot = 1; slot <= 64; ++slot) {
        snprintf(folder, sizeof(folder), "%s/boot-%04d", parent, slot);
        directory(folder);
        for (unsigned int name = 0; name < 4; ++name) {
            snprintf(path, sizeof(path), "%s/%s", folder, names[name]);
            label_file(path, "u:object_r:t110_bootlog_file:s0", 1);
        }
    }
    sync();
    puts("T110_BACKING_FILE_AND_64_BOOT_LOG_SLOTS_LABELLED_VERIFIED");
    return 0;
}
