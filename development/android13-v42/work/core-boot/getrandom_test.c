#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/random.h>
#include <linux/reboot.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

#define ARM_GETRANDOM 384
static volatile sig_atomic_t interrupted;
static int checks;
static void check(int ok, const char *name)
{
    dprintf(2, "GETRANDOM_%s %s errno=%d\n", ok ? "PASS" : "FAIL", name, errno);
    if (!ok) {
        if (getpid() == 1)
            reboot(RB_POWER_OFF);
        _exit(1);
    }
    checks++;
}
static long rng(void *p, size_t n, unsigned flags)
{
    return syscall(ARM_GETRANDOM, p, n, flags);
}
static void alarm_handler(int sig)
{
    (void)sig;
    interrupted = 1;
}
int main(void)
{
    char a[256], b[256];
    int status, pipefd[2];
    if (getpid() != 1)
        return 2;
    mount("devtmpfs", "/dev", "devtmpfs", 0, NULL);
    int console = open("/dev/console", O_RDWR);
    dup2(console, 1);
    dup2(console, 2);
    check(rng(a, 32, 4) == -1 && errno == EINVAL, "invalid flags");
    check(rng(a, 32, GRND_NONBLOCK) == -1 && errno == EAGAIN, "unseeded nonblock");
    check(rng(a, 32, GRND_NONBLOCK | GRND_RANDOM) == -1 && errno == EAGAIN, "unseeded random pool");
    pid_t child = fork();
    check(child >= 0, "fork interrupt test");
    if (!child) {
        struct sigaction sa = {.sa_handler = alarm_handler};
        sigemptyset(&sa.sa_mask);
        sigaction(SIGALRM, &sa, NULL);
        alarm(1);
        check(rng(a, 32, 0) == -1 && errno == EINTR && interrupted, "blocking call interrupt");
        _exit(0);
    }
    check(waitpid(child, &status, 0) == child && WIFEXITED(status) && !WEXITSTATUS(status), "interrupt child passed");
    check(pipe(pipefd) == 0, "pipe");
    child = fork();
    check(child >= 0, "fork blocked reader");
    if (!child) {
        close(pipefd[0]);
        struct sigaction sa = {.sa_handler = alarm_handler, .sa_flags = SA_RESTART};
        sigemptyset(&sa.sa_mask);
        sigaction(SIGUSR1, &sa, NULL);
        check(write(pipefd[1], "R", 1) == 1, "notify reader ready");
        check(rng(a, 32, 0) == 32, "blocked reader wakes with seed");
        check(interrupted, "restart signal delivered");
        _exit(0);
    }
    close(pipefd[1]);
    check(read(pipefd[0], a, 1) == 1, "reader ready");
    usleep(100000);
    kill(child, SIGUSR1);
    usleep(100000);
    check(waitpid(child, &status, WNOHANG) == 0, "restart keeps unseeded read blocked");
    /* Deterministic entropy injection is ONLY for this isolated QEMU test. */
    struct { int entropy_count; int buf_size; unsigned char buf[128]; } seed = {1024, 128, {0}};
    for (unsigned i = 0; i < sizeof(seed.buf); i++)
        seed.buf[i] = (unsigned char)(i * 73 + 11);
    int random = open("/dev/random", O_RDWR);
    int urandom = open("/dev/urandom", O_RDONLY);
    check(random >= 0 && urandom >= 0, "random devices");
    check(ioctl(random, RNDADDENTROPY, &seed) == 0, "test-only input entropy");
    check(read(urandom, a, sizeof(a)) == sizeof(a), "transfer entropy to nonblocking pool");
    check(waitpid(child, &status, 0) == child && WIFEXITED(status) && !WEXITSTATUS(status), "blocked child passed");
    check(rng(a, 256, 0) == 256, "seeded 256-byte request");
    check(rng(b, 256, GRND_NONBLOCK) == 256, "seeded nonblock request");
    check(memcmp(a, b, sizeof(a)) != 0, "successive buffers differ");
    check(rng((void *)1, 32, 0) == -1 && errno == EFAULT, "bad user pointer");
    check(rng(a, 0, 0) == 0, "zero length");
    check(rng(a, 32, 8) == -1 && errno == EINVAL, "invalid flags after initialization");
    check(ioctl(random, RNDADDENTROPY, &seed) == 0, "test-only random pool refill");
    long n = rng(a, 32, GRND_RANDOM | GRND_NONBLOCK);
    check(n > 0 && n <= 32, "seeded random pool read");
    dprintf(2, "T110_GETRANDOM_REGRESSION_PASS checks=%d\n", checks);
    reboot(RB_POWER_OFF);
    return 0;
}
