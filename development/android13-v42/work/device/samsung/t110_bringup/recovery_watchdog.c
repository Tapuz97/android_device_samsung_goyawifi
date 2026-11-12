/* Minimal diagnostic recovery process, not a recovery UI or flashing tool.
 * Return to the untouched installed recovery unless the operator creates the
 * ephemeral /dev/t110-keepalive file through ADB within two minutes. */
#include <errno.h>
#include <fcntl.h>
#include <linux/reboot.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
    int log = open("/dev/kmsg", O_WRONLY | O_CLOEXEC);
    if (log >= 0) dprintf(log, "<6>T110: Android 13 diagnostic init started; recovery fallback in 120s\n");
    for (int seconds = 0; seconds < 120; ++seconds) {
        if (access("/dev/t110-keepalive", F_OK) == 0) {
            if (log >= 0) dprintf(log, "<6>T110: diagnostic keepalive received\n");
            return 0;
        }
        sleep(1);
    }
    if (log >= 0) dprintf(log, "<4>T110: diagnostic timeout; rebooting installed recovery\n");
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_RESTART2, "recovery");
    if (log >= 0) dprintf(log, "<3>T110: recovery reboot failed, errno=%d\n", errno);
    return 1;
}
