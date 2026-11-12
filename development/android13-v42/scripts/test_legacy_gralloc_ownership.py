"""Exercise the actual libui lifetime helper with a strict mock gralloc HAL."""
from pathlib import Path
import subprocess
import tempfile

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
source = Path('/root/t110-build/lineage20/frameworks/native/libs/ui/Gralloc2.cpp').read_text()
start = source.index('class T110LegacyAllocation {')
end = source.index('\n};', start) + 3
helper = source[start:end]
prefix = r'''
#include <cassert>
#include <cstdint>
#include <climits>
#include <cstdio>
#include <mutex>
#include <unordered_map>
#include <unordered_set>
using status_t = int;
using PixelFormat = int;
struct Handle { const Handle* owner; };
using buffer_handle_t = const Handle*;
constexpr int NO_ERROR = 0, NO_INIT = -19, BAD_VALUE = -22;
constexpr int GRALLOC_USAGE_HW_FB = 0x1000;
constexpr int GRALLOC_USAGE_SW_READ_OFTEN = 3;
constexpr const char* GRALLOC_HARDWARE_MODULE_ID = "gralloc";
#define ALOGE(...) do {} while (0)
#define ALOGI(...) do {} while (0)
#define ALOGE_IF(cond, ...) assert(!(cond))
namespace base { bool GetBoolProperty(const char*, bool) { return true; } }
namespace hardware { struct hidl_handle {
    const Handle* h;
    explicit hidl_handle(const Handle* value) : h(value) {}
}; }
struct hw_module_t {};
struct alloc_device_t {
    int (*alloc)(alloc_device_t*, int, int, int, int, buffer_handle_t*, int*);
    int (*free)(alloc_device_t*, buffer_handle_t);
};
static std::unordered_set<const Handle*> owners;
static std::unordered_set<const Handle*> clones;
static int calls, frees, failAlloc, failImport, importCalls, lastUsage;
static bool differentStride;
int allocate(alloc_device_t*, int, int, int, int usage, buffer_handle_t* out, int* stride) {
    lastUsage = usage;
    if (++calls == failAlloc) return -12;
    auto* h = new Handle{nullptr};
    h->owner = h;
    owners.insert(h);
    *out = h;
    *stride = differentStride ? calls * 64 : 128;
    return 0;
}
int release(alloc_device_t*, buffer_handle_t h) {
    assert(owners.count(h));
    // A local registered clone must be released before its allocation owner.
    for (auto* clone : clones) assert(clone->owner != h);
    owners.erase(h);
    delete h;
    ++frees;
    return 0;
}
int hw_get_module(const char*, const hw_module_t** out) {
    static hw_module_t module;
    *out = &module;
    return 0;
}
constexpr int RTLD_NOW = 2, RTLD_LOCAL = 0;
void* dlopen(const char*, int) { static int library; return &library; }
void* dlsym(void*, const char*) { return reinterpret_cast<void*>(hw_get_module); }
int gralloc_open(const hw_module_t*, alloc_device_t** out) {
    static alloc_device_t device{allocate, release};
    *out = &device;
    return 0;
}
class Gralloc2Mapper {
public:
    status_t importBuffer(hardware::hidl_handle raw, buffer_handle_t* out) const {
        assert(owners.count(raw.h));
        if (++importCalls == failImport) return -22;
        auto* clone = new Handle{raw.h};
        clones.insert(clone);
        *out = clone;
        return 0;
    }
    void freeBuffer(buffer_handle_t h) const;
};
'''
suffix = r'''
void Gralloc2Mapper::freeBuffer(buffer_handle_t h) const {
    assert(clones.count(h));
    assert(owners.count(h->owner));
    clones.erase(h);
    // Match Gralloc2Mapper: release backing owner after mapper unregister.
    T110LegacyAllocation::get().releaseOwner(h);
    delete h;
}
void reset() {
    assert(owners.empty() && clones.empty());
    calls = frees = failAlloc = failImport = importCalls = lastUsage = 0;
    differentStride = false;
}
int main() {
    auto& state = T110LegacyAllocation::get();
    Gralloc2Mapper mapper;
    assert(state.enabled() && state.ready());
    buffer_handle_t handles[3]{};
    uint32_t stride = 0;
    assert(state.allocate(mapper,128,128,1,1,0x1b00,3,&stride,handles,true)==0);
    assert(owners.size()==3 && clones.size()==3 && frees==0 && static_cast<uint32_t>(lastUsage)==0x80000b03u);
    mapper.freeBuffer(handles[1]);
    assert(frees==1 && owners.size()==2);
    mapper.freeBuffer(handles[0]); mapper.freeBuffer(handles[2]);
    assert(frees==3);
    reset(); failAlloc=2;
    assert(state.allocate(mapper,128,128,1,1,0x100,3,&stride,handles,true)==-12);
    assert(frees==1 && handles[0]==nullptr);
    reset(); failImport=2;
    assert(state.allocate(mapper,128,128,1,1,0x100,3,&stride,handles,true)==-22);
    assert(frees==2 && handles[0]==nullptr);
    reset(); differentStride=true;
    assert(state.allocate(mapper,128,128,1,1,0x100,3,&stride,handles,true)==-22);
    assert(frees==2 && handles[0]==nullptr);
    reset();
    assert(state.allocate(mapper,128,128,1,1,0x100,1,&stride,handles,false)==-22);
    assert(state.allocate(mapper,128,128,1,2,0x100,1,&stride,handles,true)==-22);
    assert(state.allocate(mapper,128,128,1,1,1ULL<<32,1,&stride,handles,true)==-22);
    assert(state.allocate(mapper,UINT32_MAX,128,1,1,0x100,1,&stride,handles,true)==-22);
    assert(calls==0);
    Handle external{nullptr}; state.releaseOwner(&external);
    assert(frees==0);
    puts("PASS: retained lifetime, release ordering, allocation/import/stride rollback, raw/layer/usage/size rejection, external handle isolation");
}
'''
with tempfile.TemporaryDirectory(prefix='t110-gralloc-owner-') as directory:
    root = Path(directory)
    cpp, binary = root/'test.cpp', root/'test'
    cpp.write_text(prefix + helper + suffix)
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-g',str(cpp),'-o',str(binary)],check=True)
    result = subprocess.run([str(binary)],capture_output=True,text=True)
    output = result.stdout + result.stderr
    (project/'evidence/gralloc-owner-lifetime-regression.txt').write_text(output)
    print(output)
    result.check_returncode()
