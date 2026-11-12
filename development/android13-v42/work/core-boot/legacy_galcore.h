/* Targeted legacy loader for the matched full-ROM galcore module. */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>
static int load_galcore(void) {
    if (getuid() != 0) return 2;
    int fd = open("/lib/modules/galcore.ko", O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    struct stat st;
    if (fd < 0 || fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_size < 100000 || st.st_size > 8000000) return 2;
    void *data = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (data == MAP_FAILED || memcmp(data, "\177ELF", 4)) return 2;
    int result = syscall(SYS_init_module, data, st.st_size, "");
    if (result) perror("galcore init_module");
    else puts("GALCORE_LEGACY_MODULE_LOADED");
    munmap(data, st.st_size);
    return result ? 1 : 0;
}
