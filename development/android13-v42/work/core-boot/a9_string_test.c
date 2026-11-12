#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <unistd.h>

extern char *strcpy_a9(char *, const char *);
extern char *stpcpy_a9(char *, const char *);
extern char *strcat_a9(char *, const char *);
static unsigned checks;
static void require(int ok, const char *what)
{
    if (!ok) {
        dprintf(2, "A9_STRING_FAIL %s check=%u\n", what, checks);
        reboot(RB_POWER_OFF);
        _exit(1);
    }
    checks++;
}
int main(void)
{
    if (getpid() != 1) return 2;
    mount("devtmpfs", "/dev", "devtmpfs", 0, NULL);
    int console = open("/dev/console", O_RDWR);
    dup2(console, 1);
    dup2(console, 2);
    char src[272] __attribute__((aligned(16)));
    char dst[288] __attribute__((aligned(16)));
    for (int n = 0; n <= 128; n++) {
        for (int s = 0; s < 8; s++) {
            for (int d = 0; d < 8; d++) {
                memset(src, 'q', sizeof(src));
                src[s+n] = 0;
                memset(dst, 0x5a, sizeof(dst));
                require(strcpy_a9(dst+d, src+s) == dst+d, "strcpy return");
                require(!memcmp(dst+d, src+s, n+1) && dst[d+n+1] == 0x5a, "strcpy contents/boundary");
                memset(dst, 0x5a, sizeof(dst));
                require(stpcpy_a9(dst+d, src+s) == dst+d+n, "stpcpy return");
                require(!memcmp(dst+d, src+s, n+1) && dst[d+n+1] == 0x5a, "stpcpy contents/boundary");
                memset(dst, 0x5a, sizeof(dst));
                dst[d] = 'x'; dst[d+1] = 0;
                require(strcat_a9(dst+d, src+s) == dst+d, "strcat return");
                require(dst[d] == 'x' && !memcmp(dst+d+1, src+s, n+1) && dst[d+n+2] == 0x5a, "strcat contents/boundary");
            }
        }
    }
    char *guard_src = mmap(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    char *guard_dst = mmap(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    require(guard_src != MAP_FAILED && guard_dst != MAP_FAILED, "guard allocations");
    require(!mprotect(guard_src+4096, 4096, PROT_NONE) && !mprotect(guard_dst+4096, 4096, PROT_NONE), "guard pages");
    for (int n = 0; n < 128; n++) {
        char *s = guard_src+4095-n, *d = guard_dst+4095-n;
        memset(s, 'p', n); s[n] = 0;
        require(stpcpy_a9(d, s) == d+n && !memcmp(d, s, n+1), "page-edge stpcpy");
        require(strcpy_a9(d, s) == d && !memcmp(d, s, n+1), "page-edge strcpy");
        d[0] = 0;
        require(strcat_a9(d, s) == d && !memcmp(d, s, n+1), "page-edge strcat");
    }
    dprintf(2, "T110_A9_STRING_REGRESSION_PASS checks=%u\n", checks);
    reboot(RB_POWER_OFF);
    return 0;
}
