#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/loop.h>
#include <linux/reboot.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <linux/fs.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/klog.h>
#include <sys/xattr.h>
#include <unistd.h>
#if defined(T110_FULL_BOOT) && !defined(T110_QEMU)
#include "legacy_galcore.h"
#endif

static int checkpoint_fd = -1;

static void checkpoint(const char *message)
{
    if (checkpoint_fd >= 0) {
        dprintf(checkpoint_fd, "%s\n", message);
        fsync(checkpoint_fd);
    }
}

static void recovery(void)
{
#ifndef T110_QEMU
    checkpoint("Requesting recovery");
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_RESTART2, "recovery");
#endif
}

static __attribute__((noreturn)) void fail(const char *step)
{
    int saved_errno = errno;
    if (checkpoint_fd >= 0) {
        dprintf(checkpoint_fd, "FAIL %s: %s\n", step, strerror(saved_errno));
        fsync(checkpoint_fd);
    }
    errno = saved_errno;
    dprintf(STDERR_FILENO, "<3>t110-stage: %s: %s\n", step, strerror(errno));
    recovery();
    for (;;)
        pause();
}

#if defined(T110_FULL_BOOT)
static void bootstrap_policy(void)
{
    // Standard Android init will reload this same policy and enable enforcing.
    // The old kernel only supports ext4 SELinux labels after a policy is loaded.
    int enforce = open("/sys/fs/selinux/enforce", O_WRONLY | O_CLOEXEC);
    if (enforce < 0 || write(enforce, "0", 1) != 1)
        fail("initial policy setup");
    close(enforce);
    int fd = open("/t110-preload-policy", O_RDONLY | O_CLOEXEC);
    struct stat info;
    if (fd < 0 || fstat(fd, &info) || info.st_size <= 0 || info.st_size > 2 * 1024 * 1024)
        fail("bootstrap policy file");
    char *policy = malloc(info.st_size);
    if (!policy || read(fd, policy, info.st_size) != info.st_size)
        fail("read bootstrap policy");
    close(fd);
    fd = open("/sys/fs/selinux/load", O_WRONLY | O_CLOEXEC);
    if (fd < 0 || write(fd, policy, info.st_size) != info.st_size)
        fail("load bootstrap policy");
    close(fd);
    free(policy);
}

#ifndef T110_QEMU
static void label_log_fd(int fd)
{
    const char label[] = "u:object_r:t110_bootlog_file:s0";
    if (fsetxattr(fd, "security.selinux", label, sizeof(label), 0))
        fail("label persistent boot log");
}

static void persistent_logging(void)
{
    const char *parent = "/stage-data/local/tmp/t110-bootlogs";
    if (mkdir(parent, 0700) && errno != EEXIST)
        fail(parent);
    struct stat info;
    if (lstat(parent, &info) || !S_ISDIR(info.st_mode))
        fail("boot log parent directory");
    char directory[160], file[192];
    int made = 0;
    for (int sequence = 1; sequence <= 9999; ++sequence) {
        snprintf(directory, sizeof(directory), "%s/boot-%04d", parent, sequence);
        if (mkdir(directory, 0700) == 0) { made = 1; break; }
        if (errno != EEXIST) fail("unique boot log directory");
    }
    if (!made) fail("boot log directory limit");
    snprintf(file, sizeof(file), "%s/checkpoints.txt", directory);
    checkpoint_fd = open(file, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (checkpoint_fd < 0) fail("open boot checkpoints");
    label_log_fd(checkpoint_fd);
    checkpoint("Persistent logging opened after userdata mount");
    snprintf(file, sizeof(file), "%s/logger-status.txt", directory);
    int status_fd = open(file, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (status_fd < 0) fail("open logger status");
    label_log_fd(status_fd);
    int logs[2];
    for (int slot = 0; slot < 2; ++slot) {
        snprintf(file, sizeof(file), "%s/kernel-%d.txt", directory, slot);
        logs[slot] = open(file, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
        if (logs[slot] < 0) fail("open kernel snapshot");
        label_log_fd(logs[slot]);
    }
    sync();
    /* Periodic full-ring writes are a recovery diagnostic, not normal runtime
     * work on this eMMC. Keep one early snapshot and all boot checkpoints by
     * default. A root-owned, non-writable marker enables the existing worker. */
    struct stat marker;
    const char *periodic = "/stage-data/local/tmp/t110-bootlogs/periodic-enabled";
    int periodic_enabled = lstat(periodic, &marker) == 0 &&
        S_ISREG(marker.st_mode) && marker.st_uid == 0 && !(marker.st_mode & 0022);
    if (!periodic_enabled) {
        char buffer[512 * 1024];
        int length = klogctl(3, buffer, sizeof(buffer));
        if (length >= 0 && pwrite(logs[0], buffer, length, 0) == length &&
            ftruncate(logs[0], length) == 0)
            fsync(logs[0]);
        close(logs[0]);
        close(logs[1]);
        close(status_fd);
        checkpoint("Periodic kernel snapshots disabled; one early snapshot retained");
        return;
    }
    pid_t child = fork();
    if (child < 0) fail("fork persistent logger");
    if (child == 0) {
        close(checkpoint_fd);
        checkpoint_fd = status_fd;
        char buffer[512 * 1024];
        for (int sample = 0; sample < 660; ++sample) {
            int length = klogctl(3, buffer, sizeof(buffer));
            if (length >= 0) {
                int fd = logs[sample % 2];
                ssize_t done = pwrite(fd, buffer, length, 0);
                if (done == length && ftruncate(fd, length) == 0 && fsync(fd) == 0) {
                    char enforcing = '?';
                    int state = open("/sys/fs/selinux/enforce", O_RDONLY | O_CLOEXEC);
                    if (state >= 0) {
                        if (read(state, &enforcing, 1) != 1) enforcing = '?';
                        close(state);
                    }
                    dprintf(checkpoint_fd, "Kernel snapshot %d: %d bytes; enforcing=%c\n", sample, length, enforcing);
                } else {
                    dprintf(checkpoint_fd, "Snapshot write failed: %s\n", strerror(errno));
                }
            } else {
                dprintf(checkpoint_fd, "Kernel snapshot failed: %s\n", strerror(errno));
            }
            fsync(checkpoint_fd);
            sleep(2);
        }
        _exit(0);
    }
    close(logs[0]);
    close(logs[1]);
    close(status_fd);
    checkpoint("Persistent logger forked");
}
#endif
#endif

static void mount_fs(const char *source, const char *target, const char *type,
                     unsigned long flags, const char *options)
{
    if (mount(source, target, type, flags, options))
        fail(target);
}

static void node(const char *path, mode_t mode, unsigned int major_num,
                 unsigned int minor_num)
{
    if (mknod(path, mode, makedev(major_num, minor_num)) && errno != EEXIST)
        fail(path);
}

static void block_node(const char *name, const char *path)
{
    char sysfs[128];
    unsigned int major_num, minor_num;
    snprintf(sysfs, sizeof(sysfs), "/sys/class/block/%s/dev", name);
    for (int attempt = 0; attempt < 100; ++attempt) {
        FILE *file = fopen(sysfs, "r");
        if (file) {
            int fields = fscanf(file, "%u:%u", &major_num, &minor_num);
            fclose(file);
            if (fields != 2) {
                errno = EINVAL;
                fail(sysfs);
            }
            node(path, S_IFBLK | 0600, major_num, minor_num);
            return;
        }
        usleep(100000);
    }
    fail(sysfs);
}

#ifndef T110_QEMU
static void expect_sysfs(const char *path, const char *expected)
{
    char value[128];
    FILE *file = fopen(path, "r");
    if (!file)
        fail(path);
    if (!fgets(value, sizeof(value), file) || strcmp(value, expected)) {
        errno = EINVAL;
        fail(path);
    }
    fclose(file);
}

static void watchdog(void)
{
    pid_t child = fork();
    if (child < 0)
        fail("fork watchdog");
    if (child == 0) {
        unsigned int remaining =
#ifdef T110_FULL_BOOT
            1200;
#else
            150;
#endif
        while (remaining)
            remaining = sleep(remaining);
#ifdef T110_FULL_BOOT
        if (access("/dev/t110-keepalive", F_OK) == 0)
            _exit(0);
#endif
        dprintf(STDERR_FILENO, "<4>t110-stage: returning to recovery\n");
        recovery();
        _exit(1);
    }
}
#endif

static const char *system_device(void)
{
#ifdef T110_QEMU
    block_node("mmcblk0", "/dev/block/mmcblk0");
    return "/dev/block/mmcblk0";
#else
    block_node("mmcblk0p16", "/dev/block/mmcblk0p16");
    expect_sysfs("/sys/class/block/mmcblk0/device/cid",
                 "1101003030384745T110_ADB_SERIAL\n");
    expect_sysfs("/sys/class/block/mmcblk0p16/size", "10760192\n");
#ifdef T110_FULL_BOOT
    mount_fs("/dev/block/mmcblk0p16", "/stage-data", "ext4",
             MS_NOSUID | MS_NODEV | MS_NOATIME, NULL);
    persistent_logging();
    const char *path = "/stage-data/local/tmp/t110-rom-system.raw";
    const char *userdata = "/stage-data/local/tmp/t110-rom-data";
    if (mkdir(userdata, 0771) && errno != EEXIST)
        fail(userdata);
    struct stat userdata_info;
    if (lstat(userdata, &userdata_info) || !S_ISDIR(userdata_info.st_mode))
        fail("ROM userdata directory");
    mount_fs(userdata, "/data", NULL, MS_BIND, NULL);
    checkpoint("Persistent Android userdata mounted");
#else
    mount_fs("/dev/block/mmcblk0p16", "/stage-data", "ext4",
             MS_RDONLY | MS_NOSUID | MS_NODEV | MS_NOEXEC, "noload");
    const char *path = "/stage-data/local/tmp/t110-stage-system.raw";
#endif
    int image = open(path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    struct stat info;
    if (image < 0 || fstat(image, &info))
        fail(path);
    /* These are loop-file geometries, never physical SYSTEM write sizes.
     * The optional full Google payload needs 2047 MiB. Keep it below the
     * signed 32-bit off_t limit and retain the original vanilla geometry. */
    int supported_image_size = info.st_size == 1594884096;
#ifdef T110_FULL_BOOT
    supported_image_size |= info.st_size == 2146435072;
#endif
    if (!S_ISREG(info.st_mode) || !supported_image_size) {
        errno = EINVAL;
        fail(path);
    }
#ifdef T110_FULL_BOOT
    const char image_label[] = "u:object_r:shell_data_file:s0";
    if (fsetxattr(image, "security.selinux", image_label, sizeof(image_label), 0))
        fail("label staged system backing file");
    checkpoint("Staged system backing file labelled for loop I/O");
#endif
    block_node("loop0", "/dev/block/loop0");
    int loop = open("/dev/block/loop0", O_RDONLY | O_CLOEXEC);
    int readonly = 0;
    if (loop < 0 || ioctl(loop, LOOP_SET_FD, image) ||
        ioctl(loop, BLKROGET, &readonly))
        fail("attach staged image");
    if (readonly != 1) {
        errno = EROFS;
        fail("loop0 is writable");
    }
    close(loop);
    close(image);
    checkpoint("Read-only system loop attached");
    return "/dev/block/loop0";
#endif
}

static void install_cgroup_config(void)
{
    mount_fs("tmpfs", "/stage-config", "tmpfs", MS_NODEV | MS_NOSUID | MS_NOEXEC,
             "mode=0755,size=4k");
    const char *target = "/stage-config/cgroups.json";
    int input = open("/t110-cgroups.json", O_RDONLY | O_CLOEXEC);
    int output = open(target, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0644);
    char buffer[4096];
    if (input < 0 || output < 0)
        fail("open cgroup config");
    ssize_t length = read(input, buffer, sizeof(buffer));
    if (length <= 0 || length == sizeof(buffer) || write(output, buffer, length) != length)
        fail("copy cgroup config");
    close(input);
    close(output);
    mount_fs(target, "/system/etc/cgroups.json", NULL, MS_BIND, NULL);
}

int main(void)
{
    if (getpid() != 1)
        return 1;
    umask(0);
    mount_fs("tmpfs", "/dev", "tmpfs", MS_NOSUID, "mode=0755");
    node("/dev/kmsg", S_IFCHR | 0600, 1, 11);
    node("/dev/kmsg_debug", S_IFCHR | 0622, 1, 11);
    int kmsg = open("/dev/kmsg", O_WRONLY | O_CLOEXEC);
    if (kmsg >= 0) {
        if (dup2(kmsg, STDERR_FILENO) < 0)
            fail("redirect stderr");
        if (kmsg != STDERR_FILENO)
            close(kmsg);
    }
#ifndef T110_QEMU
    watchdog();
#endif
    mount_fs("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC,
             "hidepid=2,gid=3009");
    mount_fs("sysfs", "/sys", "sysfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL);
    mount_fs("selinuxfs", "/sys/fs/selinux", "selinuxfs", 0, NULL);
    mount_fs("tmpfs", "/mnt", "tmpfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, "mode=0755");
    mkdir("/mnt/vendor", 0755);
    mkdir("/mnt/product", 0755);
    mkdir("/dev/block", 0755);
    mkdir("/dev/pts", 0755);
    mkdir("/dev/selinux", 0755);
    if (mkdir("/dev/socket", 0755))
        fail("/dev/socket");
    mount_fs("devpts", "/dev/pts", "devpts", MS_NOSUID | MS_NOEXEC, "mode=0620,gid=5");
    node("/dev/null", S_IFCHR | 0666, 1, 3);
    node("/dev/random", S_IFCHR | 0666, 1, 8);
    node("/dev/urandom", S_IFCHR | 0666, 1, 9);
    node("/dev/ptmx", S_IFCHR | 0666, 5, 2);
    node("/dev/console", S_IFCHR | 0600, 5, 1);

#if defined(T110_FULL_BOOT)
    bootstrap_policy();
#endif
    const char *device = system_device();
    // SELinux setup still runs in the kernel domain; platform init transitions
    // to its final domain on its own second-stage exec.
    mount_fs(device, "/stage-system", "ext4", MS_RDONLY | MS_NODEV, "noload");
    mount_fs("/stage-system/system", "/system", NULL, MS_BIND, NULL);
#ifdef T110_FULL_BOOT
    /* ART stores class-loader paths using the standard partition roots. A
     * symlink resolves them to /system/system_ext and rejects otherwise valid
     * compiled code. Bind the same read-only directories at their real roots.
     * Ramdisk targets must be directories: mounting onto a symlink would bind
     * onto the source instead and leave the canonical-path mismatch intact. */
    const char *partition_roots[] = {"/product", "/system_ext"};
    const char *partition_sources[] = {"/system/product", "/system/system_ext"};
    for (size_t i = 0; i < sizeof(partition_roots) / sizeof(partition_roots[0]); ++i) {
        struct stat partition_info;
        if (lstat(partition_roots[i], &partition_info) || !S_ISDIR(partition_info.st_mode))
            fail("partition alias requires a real directory");
        mount_fs(partition_sources[i], partition_roots[i], NULL, MS_BIND, NULL);
    }
    checkpoint("Read-only product/system_ext mounted at canonical partition roots");
#endif
    checkpoint("Android system mounted");
    install_cgroup_config();
#if defined(T110_FULL_BOOT) && !defined(T110_QEMU)
    // Android init's finit_module syscall is absent on this 3.4 kernel.
    // Load the package-pinned module before platform services start.
    if (load_galcore()) fail("load matched galcore via init_module");
    checkpoint("Matched galcore module loaded via init_module");
#endif
#ifdef T110_FULL_BOOT
    // Preloading policy for ext4 labels would otherwise transition too early.
    // This override applies to the next exec only and is cleared by that exec.
    const char setup_context[] = "u:r:kernel:s0";
    int exec_context = open("/proc/self/attr/exec", O_WRONLY | O_CLOEXEC);
    if (exec_context < 0 ||
        write(exec_context, setup_context, sizeof(setup_context)) != sizeof(setup_context))
        fail("preserve kernel domain for SELinux setup");
    close(exec_context);
    checkpoint("SELinux setup exec pinned to kernel domain");
#endif
    checkpoint("Executing Android platform init");
    dprintf(STDERR_FILENO, "<5>t110-stage: SYSTEM mounted read-only, executing platform init\n");
    char *const args[] = {"/system/bin/init", "selinux_setup", NULL};
    execv(args[0], args);
    fail("exec platform init");
}
