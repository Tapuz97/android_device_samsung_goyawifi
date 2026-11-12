/* Return a live RAM diagnostic to installed recovery after a long probe. */
#include <linux/reboot.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void)
{
    if (getuid() != 0 || access("/init.t110-core.rc", F_OK))
        return 2;
    FILE *cid_file = fopen("/sys/class/block/mmcblk0/device/cid", "r");
    char cid[40] = {0};
    if (!cid_file)
        return 2;
    int read = fscanf(cid_file, "%39s", cid);
    fclose(cid_file);
    if (read != 1 || strcmp(cid, "1101003030384745T110_ADB_SERIAL"))
        return 2;
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_RESTART2, "recovery");
    perror("reboot to TWRP");
    return 1;
}
