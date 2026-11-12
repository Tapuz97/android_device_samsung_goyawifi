/* Use the legacy init_module syscall directly in the T110 diagnostic. */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void)
{
    if (getuid() != 0 || access("/t110-native-diagnostic", F_OK))
        return 2;
    int fd = open("/tmp/t110-galcore.ko", O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    struct stat info;
    if (fd < 0 || fstat(fd, &info) || !S_ISREG(info.st_mode) || info.st_size != 2675027) {
        fprintf(stderr, "Unexpected galcore module file\n");
        if (fd >= 0)
            close(fd);
        return 2;
    }
    size_t size = (size_t)info.st_size;
    void *module = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (module == MAP_FAILED) {
        perror("mmap galcore");
        return 1;
    }
    if (memcmp(module, "\177ELF", 4)) {
        munmap(module, size);
        return 2;
    }
    long rc = syscall(SYS_init_module, module, size, "");
    if (rc)
        perror("init_module galcore");
    else
        puts("GALCORE_INIT_MODULE_PASS");
    munmap(module, size);
    return rc ? 1 : 0;
}
