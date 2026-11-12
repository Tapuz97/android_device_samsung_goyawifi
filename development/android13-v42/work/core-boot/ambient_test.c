#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/capability.h>
#include <linux/reboot.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

static struct __user_cap_header_struct header = {_LINUX_CAPABILITY_VERSION_3, 0};
static struct __user_cap_data_struct caps[2];

static void check(int condition, const char *name)
{
    if (!condition) {
        dprintf(2, "AMBIENT_FAIL %s errno=%d\n", name, errno);
        _exit(1);
    }
}

static void inherited_test(void)
{
    check(getuid() == 1000, "exec uid");
    check(syscall(SYS_capget, &header, caps) == 0, "get caps after exec");
    check(caps[0].effective == (1U << CAP_NET_BIND_SERVICE), "exec effective set");
    check(caps[0].permitted == caps[0].effective, "exec permitted set");
    check(prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_IS_SET, CAP_NET_BIND_SERVICE, 0, 0) == 1,
          "ambient inherited across exec");
    caps[0].inheritable = 0;
    check(syscall(SYS_capset, &header, caps) == 0, "drop inheritable");
    check(prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_IS_SET, CAP_NET_BIND_SERVICE, 0, 0) == 0,
          "ambient cleared with inheritable");
    _exit(0);
}

int main(int argc, char **argv)
{
    if (argc == 2 && !strcmp(argv[1], "child"))
        inherited_test();
    if (getpid() != 1)
        return 2;
    mount("devtmpfs", "/dev", "devtmpfs", 0, NULL);
    int console = open("/dev/console", O_RDWR);
    check(console >= 0, "console");
    dup2(console, 1);
    dup2(console, 2);
    mount("proc", "/proc", "proc", 0, NULL);
    pid_t child = fork();
    check(child >= 0, "fork");
    if (child == 0) {
        check(prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, CAP_NET_BIND_SERVICE, 0, 0) == -1 &&
              errno == EPERM, "reject raise without inheritable");
        check(prctl(PR_SET_KEEPCAPS, 1, 0, 0, 0) == 0, "keep permitted on uid change");
        check(syscall(SYS_capget, &header, caps) == 0, "capget");
        caps[0].inheritable = 1U << CAP_NET_BIND_SERVICE;
        check(syscall(SYS_capset, &header, caps) == 0, "set inheritable");
        check(prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, CAP_NET_BIND_SERVICE, 0, 0) == 0,
              "raise ambient as root");
        check(setresuid(1000, 1000, 1000) == 0, "switch uid");
        check(prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_IS_SET, CAP_NET_BIND_SERVICE, 0, 0) == 0,
              "uid change clears ambient");
        check(prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, CAP_NET_BIND_SERVICE, 0, 0) == 0,
              "raise ambient as service uid");
        execl("/init", "init", "child", NULL);
        check(0, "exec");
    }
    int status;
    check(waitpid(child, &status, 0) == child, "wait child");
    if (WIFEXITED(status) && WEXITSTATUS(status) == 0)
        dprintf(2, "T110_AMBIENT_REGRESSION_PASS\n");
    else
        dprintf(2, "T110_AMBIENT_REGRESSION_FAIL status=%d\n", status);
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2, LINUX_REBOOT_CMD_POWER_OFF, NULL);
    for (;;)
        pause();
}
