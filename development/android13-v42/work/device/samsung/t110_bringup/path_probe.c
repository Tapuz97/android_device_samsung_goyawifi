#define _GNU_SOURCE 1
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    const char *paths[] = {"/", "/proc/self/exe"};
    struct stat st;
    int failures = 0;
    for (unsigned int i = 0; i < sizeof(paths) / sizeof(paths[0]); ++i) {
        int fd = open(paths[i], O_PATH | O_CLOEXEC);
        if (fd < 0) { perror("open O_PATH"); return 2; }
        errno = 0;
        int rc = fstat(fd, &st), saved = errno;
        printf("%s O_PATH fstat %s rc=%d errno=%d\n", rc ? "FAIL" : "PASS", paths[i], rc, saved);
        failures += rc != 0;
        char byte;
        errno = 0;
        rc = read(fd, &byte, 1);
        if (rc != -1 || errno != EBADF) ++failures;
        else puts("PASS O_PATH still rejects read");
        close(fd);
        char *resolved = realpath(paths[i], NULL);
        printf("%s Android 13 realpath %s: %s\n", resolved ? "PASS" : "FAIL", paths[i], resolved ? resolved : strerror(errno));
        failures += resolved == NULL;
        free(resolved);
    }
    errno = 0;
    if (fstat(-1, &st) != -1 || errno != EBADF) ++failures;
    else puts("PASS invalid fstat fd rejected");
    printf("PATH TEST failures=%d\n", failures);
    return failures ? 1 : 0;
}
