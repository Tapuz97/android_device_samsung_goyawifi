#include <binder/MemoryHeapBase.h>
#include <utils/StrongPointer.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/mman.h>
#include <unistd.h>
using namespace android;
static int fdCount() {
    DIR* dir = opendir("/proc/self/fd");
    if (!dir) return -1;
    int count = 0;
    while (readdir(dir)) ++count;
    closedir(dir);
    return count;
}
int main() {
    const int before = fdCount();
    for (int i = 0; i < 32; ++i) {
        const uint32_t flags = i % 2 ? MemoryHeapBase::NO_CACHING : 0;
        sp<MemoryHeapBase> heap;
        if (i % 4 < 2) {
            const int client = open("/dev/ion", O_RDWR);
            if (client < 0) return 9;
            heap = new MemoryHeapBase(client, 8192, flags);
            close(client);
        } else {
            heap = new MemoryHeapBase("/dev/ion", 8192, flags);
        }
        if (heap->getHeapID() < 0 || heap->getBase() == MAP_FAILED) return 10;
        unsigned char* bytes = static_cast<unsigned char*>(heap->getBase());
        bytes[0] = 0x35; bytes[8191] = 0xa7;
        int copy = dup(heap->getHeapID());
        if (copy < 0) return 11;
        heap.clear();
        void* mapping = mmap(NULL, 8192, PROT_READ | PROT_WRITE, MAP_SHARED, copy, 0);
        if (mapping == MAP_FAILED) return 12;
        const unsigned char* result = static_cast<unsigned char*>(mapping);
        if (result[0] != 0x35 || result[8191] != 0xa7) return 13;
        munmap(mapping, 8192); close(copy);
    }
    {
        sp<MemoryHeapBase> heap = new MemoryHeapBase("/dev/ion", 2880000,
                MemoryHeapBase::DONT_MAP_LOCALLY);
        if (heap->getHeapID() < 0 || heap->getBase() != NULL) return 14;
    }
    {
        sp<MemoryHeapBase> heap = new MemoryHeapBase(8192, 0, "T110AshmemRegression");
        if (heap->getHeapID() < 0 || heap->getBase() == MAP_FAILED) return 15;
        sp<MemoryHeapBase> imported = new MemoryHeapBase(heap->getHeapID(), 8192);
        if (imported->getHeapID() < 0 || imported->getBase() == MAP_FAILED) return 17;
    }
    const int after = fdCount();
    printf("ION allocation/export/map/lifetime: 32 cycles; fd count %d -> %d\n", before, after);
    printf("Unmapped 1600x1200 YUV-sized allocation and normal ashmem: PASS\n");
    return before == after ? 0 : 16;
}
