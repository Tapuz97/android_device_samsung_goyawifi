"""Host regressions using the production allocator/loader code; no Android boots."""
from pathlib import Path
import json
import subprocess
import tempfile

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
tree = Path('/root/t110-build/lineage20')
evidence = project / 'evidence/offline-v26'
compiler = Path('/usr/bin/g++')  # Host compiler with matching sanitizer runtimes.

def function(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    pos = brace + 1
    while depth:
        depth += (source[pos] == '{') - (source[pos] == '}')
        pos += 1
    return source[start:pos]

source = (tree/'frameworks/av/media/codec2/vndk/C2AllocatorIon.cpp').read_text()
methods = '\n'.join(function(source, signature) for signature in [
    'C2AllocatorIon::C2AllocatorIon(id_t id)',
    'C2AllocatorIon::~C2AllocatorIon()',
    'C2Allocator::id_t C2AllocatorIon::getId() const',
    'C2String C2AllocatorIon::getName() const',
    'std::shared_ptr<const C2Allocator::Traits> C2AllocatorIon::getTraits() const',
    'void C2AllocatorIon::setUsageMapper(',
    'c2_status_t C2AllocatorIon::newLinearAllocation(',
])
allocator_test = r'''
#include <cassert>
#include <cerrno>
#include <cstdint>
#include <functional>
#include <list>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <unistd.h>
using c2_status_t = int;
using C2String = std::string;
constexpr int C2_OK=0, C2_OMITTED=1, C2_BAD_VALUE=2, C2_NO_INIT=3;
struct C2MemoryUsage {
    static constexpr uint64_t CPU_READ=1, CPU_WRITE=2;
    uint64_t expected, unexpected;
    C2MemoryUsage(uint64_t a=0,uint64_t b=0):expected(a),unexpected(b){}
};
struct C2Allocator {
    using id_t = unsigned;
    enum { LINEAR=1 };
    struct Traits { C2String name; id_t id; int type; C2MemoryUsage minUsage,maxUsage; };
};
struct C2LinearAllocation { virtual ~C2LinearAllocation()=default; };
static int openError=0, closeCount=0, allocationCount=0;
static int ion_open() { errno=openError; return openError ? -1 : 987; }
static int ion_close(int fd) { assert(fd==987); ++closeCount; return 0; }
template<int E> static int c2_map_errno(int error) { return -error; }
#define ALOGW(...) ((void)0)
struct C2AllocationIon : C2LinearAllocation {
    C2AllocationIon(int,size_t,size_t,unsigned,unsigned,unsigned){++allocationCount;}
    int status()const{return C2_OK;}
};
class C2AllocatorIon : public C2Allocator {
public:
    using UsageMapperFn=std::function<int(C2MemoryUsage,size_t,size_t*,unsigned*,unsigned*)>;
    C2AllocatorIon(id_t); ~C2AllocatorIon();
    id_t getId()const; C2String getName()const;
    std::shared_ptr<const Traits> getTraits()const;
    void setUsageMapper(const UsageMapperFn&,uint64_t,uint64_t,uint64_t);
    int newLinearAllocation(uint32_t,C2MemoryUsage,std::shared_ptr<C2LinearAllocation>*);
    int mapUsage(C2MemoryUsage,size_t,size_t*,unsigned*,unsigned*){return C2_NO_INIT;}
private:
    int mInit,mIonFd;
    mutable std::mutex mUsageMapperLock;
    std::shared_ptr<const Traits> mTraits;
    std::map<int,int> mUsageMapperCache;
    std::list<int> mUsageMapperLru;
    UsageMapperFn mUsageMapper;
    uint64_t mBlockSize;
};
''' + methods + r'''
int main() {
    for(int error : {0,EACCES,ENOENT,EMFILE}) {
        openError=error;
        const int previousCloses=closeCount;
        {
            C2AllocatorIon allocator(37);
            assert(allocator.getId()==37);
            assert(allocator.getName()=="android.allocator.ion");
            auto first=allocator.getTraits();
            assert(first && first->id==37);
            allocator.setUsageMapper({},1,3,4096);
            assert(allocator.getId()==37);
            assert(allocator.getTraits()->minUsage.expected==1);
            assert(first->minUsage.expected==0);
            assert(allocator.newLinearAllocation(4096,{},nullptr)==C2_BAD_VALUE);
            if(error) {
                auto allocation=std::make_shared<C2LinearAllocation>();
                assert(allocator.newLinearAllocation(4096,{},&allocation)==
                       (error==ENOENT?C2_OMITTED:-error));
                assert(!allocation && allocationCount==0);
            }
        }
        assert(closeCount==previousCloses+(error==0));
    }
}
'''

loader_source = (tree/'frameworks/native/opengl/libs/EGL/Loader.cpp').read_text()
start = loader_source.index('    if (android::base::GetBoolProperty("ro.t110.legacy_gpu"')
end = loader_source.index('\n    return dso;\n}', start) + len('\n    return dso;')
loader_block = loader_source[start:end]
gralloc_source = (tree/'frameworks/native/libs/ui/Gralloc2.cpp').read_text()
start = gralloc_source.index('        int error = getModule(GRALLOC_HARDWARE_MODULE_ID, &module);')
end = gralloc_source.index('\n        if (error) {', start)
gralloc_block = gralloc_source[start:end]
graphics_test = r'''
#include <cassert>
#include <cerrno>
#include <cstring>
#include <cstdint>
static bool enabled=true,hasSymbol=true;
static int initStatus=0,initCount=0,unloadCount=0,openCount=0,moduleError=0;
static void* expectedHandle=reinterpret_cast<void*>(0x1234);
static int initDriver(){ ++initCount; return initStatus; }
static void* dlsym(void* handle,const char* name) {
    assert(handle==expectedHandle);
    assert(!strcmp(name,"gcoOS_ModuleConstructor"));
    return hasSymbol?reinterpret_cast<void*>(&initDriver):nullptr;
}
static int do_android_unload_sphal_library(void* h){assert(h==expectedHandle);++unloadCount;return 0;}
namespace android::base { static bool GetBoolProperty(const char*,bool){return enabled;} }
#define ALOGE(...) ((void)0)
#define ALOGD(...) ((void)0)
#define ALOGI(...) ((void)0)
static void* loadDriver(void* dso,const char* kind) {
''' + loader_block + r'''
}
struct hw_module_t { void* dso; };
static hw_module_t moduleValue{expectedHandle};
#define GRALLOC_HARDWARE_MODULE_ID "gralloc"
static int getModule(const char*,const hw_module_t** module) {*module=&moduleValue;return moduleError;}
static int gralloc_open(const hw_module_t*,void**){++openCount;return 0;}
static int openGralloc() {
    const hw_module_t* module=nullptr;
    void* mDevice=nullptr;
''' + gralloc_block + r'''
    return error;
}
int main() {
    enabled=false;
    assert(loadDriver(expectedHandle,"EGL")==expectedHandle && initCount==0);
    enabled=true;
    assert(loadDriver(expectedHandle,"GLESv2")==expectedHandle && initCount==0);
    assert(loadDriver(expectedHandle,"EGL")==expectedHandle && initCount==1);
    assert(loadDriver(expectedHandle,"GLES")==expectedHandle && initCount==2);
    initStatus=-2;
    assert(loadDriver(expectedHandle,"EGL")==nullptr && unloadCount==1);
    assert(openGralloc()==-ENODEV && openCount==0);
    initStatus=0; hasSymbol=false;
    assert(loadDriver(expectedHandle,"EGL")==nullptr && unloadCount==2);
    assert(openGralloc()==-ENODEV && openCount==0);
    hasSymbol=true;
    assert(openGralloc()==0 && openCount==1);
    moduleValue.dso=nullptr;
    assert(openGralloc()==-ENODEV && openCount==1);
    moduleError=-7;
    assert(openGralloc()==-7 && openCount==1);
}
'''

checks=[]
with tempfile.TemporaryDirectory(prefix='t110-v26-') as scratch:
    for name, code in [('allocator', allocator_test), ('graphics', graphics_test)]:
        source_file = Path(scratch)/(name+'.cpp')
        source_file.write_text(code)
        (evidence/(name+'-host-test.cpp')).write_text(code)
        binary = Path(scratch)/name
        subprocess.run([str(compiler), '-std=c++17', '-g', '-O1',
                        '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                        str(source_file), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
        checks.append(name+' extracted production code: ASan/UBSan PASS')

for repository, patch in [
    ('frameworks/av','0046-codec2-ion-error-state-traits.patch'),
    ('frameworks/native','0047-egl-t110-process-initialization.patch'),
    ('frameworks/native','0048-gralloc-t110-process-initialization.patch'),
]:
    subprocess.run(['git','apply','--reverse','--check',str(project/'patches'/patch)],
                   cwd=tree/repository,check=True)
    checks.append(patch+' reverse check PASS')

report = dict(status='PASS', checks=checks, android_boots=0, tablet_access=False,
              limits='Host API doubles; actual ARM build, compiled policy and image checks still required')
(evidence/'regressions.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
