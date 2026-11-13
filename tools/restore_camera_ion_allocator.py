"""Restore the observed Samsung ION allocation contract without changing C++ layout."""
from pathlib import Path
root = Path('/root/t110-lineage14/android')
p = root/'frameworks/native/libs/binder/MemoryHeapBase.cpp'
s = p.read_text()
old = '#include <binder/MemoryHeapBase.h>\n'
new = '''#include <binder/MemoryHeapBase.h>

#ifdef T110_MRVL_LEGACY
#include <linux/ion.h>
#include <string.h>

// Samsung's camera calls MemoryHeapBase("/dev/ion", ...). /dev/ion is
// an allocator, not a mappable buffer. Export a dma-buf before mapfd().
// ANI7 libbinder mapion uses carveout mask 4, 4096 alignment and flags 3
// unless NO_CACHING is requested. Keep the upstream object layout unchanged.
static int t110AllocateIonBuffer(int client, size_t size, uint32_t flags) {
    static_assert(sizeof(ion_allocation_data) == 20, "T110 ION allocation ABI");
    static_assert(sizeof(ion_fd_data) == 8, "T110 ION fd ABI");
    ion_allocation_data allocation = {};
    allocation.len = size;
    allocation.align = 4096;
    allocation.heap_id_mask = ION_HEAP_CARVEOUT_MASK;
    allocation.flags = (flags & android::MemoryHeapBase::NO_CACHING) ? 0
            : ION_FLAG_CACHED | ION_FLAG_CACHED_NEEDS_SYNC;
    if (size == 0 || ioctl(client, ION_IOC_ALLOC, &allocation) < 0) {
        const int savedError = size == 0 ? EINVAL : errno;
        close(client);
        errno = savedError;
        return -1;
    }
    ion_fd_data shared = {};
    shared.handle = allocation.handle;
    shared.fd = -1;
    const int result = ioctl(client, ION_IOC_SHARE, &shared);
    const int savedError = errno;
    ion_handle_data handle = {};
    handle.handle = allocation.handle;
    ioctl(client, ION_IOC_FREE, &handle);
    // The exported dma-buf now owns its reference, including across Binder.
    close(client);
    if (result < 0) {
        errno = savedError;
        return -1;
    }
    fcntl(shared.fd, F_SETFD, FD_CLOEXEC);
    return shared.fd;
}
#endif
'''
if new not in s:
    assert s.count(old) == 1
    s = s.replace(old,new)
old = '''        if (mapfd(fd, size) == NO_ERROR) {
            mDevice = device;
        }'''
new = '''#ifdef T110_MRVL_LEGACY
        if (strcmp(device, "/dev/ion") == 0) {
            fd = t110AllocateIonBuffer(fd, size, flags);
            if (fd < 0) {
                ALOGE("T110 ION allocation failed (%s)", strerror(errno));
                return;
            }
        }
#endif
        if (mapfd(fd, size) == NO_ERROR) {
            mDevice = device;
        }'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
old='''    mapfd(dup(fd), size, offset);'''
new='''    int ownedFd = dup(fd);
#ifdef T110_MRVL_LEGACY
    struct stat supplied, allocator;
    if (ownedFd >= 0 && fstat(ownedFd, &supplied) == 0 &&
            S_ISCHR(supplied.st_mode) && stat("/dev/ion", &allocator) == 0 &&
            supplied.st_rdev == allocator.st_rdev) {
        ownedFd = t110AllocateIonBuffer(ownedFd, size, flags);
        if (ownedFd < 0) {
            ALOGE("T110 ION fd allocation failed (%s)", strerror(errno));
            return;
        }
    }
#endif
    mapfd(ownedFd, size, offset);'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
p.write_text(s)
print('Restored T110 MemoryHeapBase ION constructor path; object layout unchanged.')
