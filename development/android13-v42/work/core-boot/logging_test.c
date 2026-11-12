#define main stage_main
#include "stage.c"
#undef main

int main(void)
{
    if (getpid() != 1) return 2;
    mount_fs("devtmpfs", "/dev", "devtmpfs", 0, NULL);
    int console = open("/dev/console", O_RDWR);
    if (console < 0) fail("console");
    dup2(console, 1);
    dup2(console, 2);
    mount_fs("proc", "/proc", "proc", 0, NULL);
    mount_fs("sysfs", "/sys", "sysfs", 0, NULL);
    mount_fs("selinuxfs", "/sys/fs/selinux", "selinuxfs", 0, NULL);
    mount_fs("/dev/mmcblk0", "/stage-data", "ext4", 0, NULL);
    mkdir("/stage-data/local", 0755);
    mkdir("/stage-data/local/tmp", 0755);
    bootstrap_policy();
    persistent_logging();
    checkpoint("LOG_TEST_BEFORE_POLICY");
    int input = open("/policy", O_RDONLY);
    struct stat info;
    if (input < 0 || fstat(input, &info)) fail("policy stat");
    void *policy = malloc(info.st_size);
    if (!policy || read(input, policy, info.st_size) != info.st_size) fail("policy read");
    int output = open("/sys/fs/selinux/load", O_WRONLY);
    if (output < 0 || write(output, policy, info.st_size) != info.st_size) fail("policy load");
    close(output);
    output = open("/sys/fs/selinux/enforce", O_WRONLY);
    if (output < 0 || write(output, "1", 1) != 1) fail("policy enforce");
    close(output);
    checkpoint("LOG_TEST_AFTER_ENFORCING");
    dprintf(2, "T110_LOGGING_POLICY_ENFORCING\n");
    sleep(8);
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2, LINUX_REBOOT_CMD_POWER_OFF, NULL);
    for (;;) pause();
}
