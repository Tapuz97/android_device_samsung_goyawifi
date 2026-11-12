#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/epoll.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/timerfd.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static int checks;
static void check(int ok, const char *name) {
    dprintf(2, "ALARM_%s %s errno=%d\n", ok ? "PASS" : "FAIL", name, errno);
    if (!ok) { if (getpid() == 1) reboot(RB_POWER_OFF); _exit(1); }
    ++checks;
}
int main(void) {
    if (getpid() != 1) return 2;
    mount("devtmpfs", "/dev", "devtmpfs", 0, NULL);
    int console = open("/dev/console", O_RDWR);
    dup2(console, 1); dup2(console, 2);
    const int clocks[] = {CLOCK_REALTIME_ALARM, CLOCK_REALTIME,
                         CLOCK_BOOTTIME_ALARM, CLOCK_BOOTTIME, CLOCK_MONOTONIC};
    int ep = epoll_create1(EPOLL_CLOEXEC);
    check(ep >= 0, "epoll_create");
    for (unsigned i = 0; i < sizeof(clocks)/sizeof(clocks[0]); ++i) {
        dprintf(2, "TEST_CLOCK %d\n", clocks[i]);
        int fd = timerfd_create(clocks[i], TFD_CLOEXEC | TFD_NONBLOCK);
        check(fd >= 0, "create Android clock");
        struct epoll_event ev = {.events = EPOLLIN | EPOLLWAKEUP, .data.fd = fd}, got;
        check(epoll_ctl(ep, EPOLL_CTL_ADD, fd, &ev) == 0, "epoll register");
        struct itimerspec arm = {.it_value = {.tv_nsec = 20000000}}, remaining;
        check(timerfd_settime(fd, 0, &arm, NULL) == 0, "relative arm");
        check(timerfd_gettime(fd, &remaining) == 0, "get remaining");
        check(epoll_wait(ep, &got, 1, 1000) == 1 && got.data.fd == fd, "epoll expiry");
        uint64_t ticks = 0;
        check(read(fd, &ticks, sizeof(ticks)) == sizeof(ticks) && ticks == 1, "one shot count");
        check(read(fd, &ticks, sizeof(ticks)) == -1 && errno == EAGAIN, "consumed event");
        arm.it_interval.tv_nsec = 10000000;
        arm.it_value.tv_nsec = 10000000;
        check(timerfd_settime(fd, 0, &arm, NULL) == 0, "periodic arm");
        usleep(85000);
        check(read(fd, &ticks, sizeof(ticks)) == sizeof(ticks) && ticks >= 2, "periodic overruns");
        check(timerfd_gettime(fd, &remaining) == 0 && remaining.it_interval.tv_nsec == 10000000,
              "periodic gettime rearms");
        check(epoll_wait(ep, &got, 1, 1000) == 1, "periodic next expiry");
        arm = (struct itimerspec){0};
        check(timerfd_settime(fd, 0, &arm, NULL) == 0, "disarm");
        check(epoll_wait(ep, &got, 1, 30) == 0, "disarm clears readiness");
        // Android obtains absolute deadlines from the underlying wall/boot
        // clocks. QEMU's RTC is not marked as a system wakeup device, so its
        // separate POSIX alarm clock_gettime path is intentionally not used.
        const int reference = clocks[i] == CLOCK_REALTIME_ALARM ? CLOCK_REALTIME :
                              clocks[i] == CLOCK_BOOTTIME_ALARM ? CLOCK_BOOTTIME : clocks[i];
        check(clock_gettime(reference, &arm.it_value) == 0, "reference clock time");
        arm.it_value.tv_nsec += 20000000;
        if (arm.it_value.tv_nsec >= 1000000000) { ++arm.it_value.tv_sec; arm.it_value.tv_nsec -= 1000000000; }
        check(timerfd_settime(fd, TFD_TIMER_ABSTIME, &arm, NULL) == 0, "absolute arm");
        check(epoll_wait(ep, &got, 1, 1000) == 1, "absolute expiry");
        check(read(fd, &ticks, sizeof(ticks)) == sizeof(ticks) && ticks == 1, "absolute count");
        close(fd);
    }
    for (int i = 0; i < 2; ++i) {
        int fd = timerfd_create(i ? CLOCK_REALTIME_ALARM : CLOCK_REALTIME, TFD_NONBLOCK);
        check(fd >= 0, "cancellation clock");
        struct timespec now;
        check(clock_gettime(CLOCK_REALTIME, &now) == 0, "realtime read");
        struct itimerspec arm = {.it_value = now};
        arm.it_value.tv_sec += 120;
        check(timerfd_settime(fd, TFD_TIMER_ABSTIME | TFD_TIMER_CANCEL_ON_SET, &arm, NULL) == 0,
              "cancel-on-set arm");
        now.tv_sec += 1;
        check(clock_settime(CLOCK_REALTIME, &now) == 0, "change wallclock");
        uint64_t ticks;
        check(read(fd, &ticks, sizeof(ticks)) == -1 && errno == ECANCELED, "clock-change cancellation");
        close(fd);
    }
    check(timerfd_create(CLOCK_PROCESS_CPUTIME_ID, 0) == -1 && errno == EINVAL, "invalid clock rejected");
    check(timerfd_create(CLOCK_REALTIME, 0x40000000) == -1 && errno == EINVAL, "invalid flags rejected");
    pid_t child = fork();
    check(child >= 0, "fork unprivileged check");
    if (!child) {
        check(setuid(10000) == 0, "drop privileges");
        check(timerfd_create(CLOCK_REALTIME_ALARM, 0) == -1 && errno == EPERM, "realtime alarm requires capability");
        check(timerfd_create(CLOCK_BOOTTIME_ALARM, 0) == -1 && errno == EPERM, "boottime alarm requires capability");
        int fd = timerfd_create(CLOCK_BOOTTIME, 0);
        check(fd >= 0, "ordinary boottime unprivileged"); close(fd); _exit(0);
    }
    int status;
    check(waitpid(child, &status, 0) == child && WIFEXITED(status) && !WEXITSTATUS(status), "capability child passed");
    dprintf(2, "T110_ALARM_REGRESSION_PASS checks=%d\n", checks);
    reboot(RB_POWER_OFF);
    return 0;
}
