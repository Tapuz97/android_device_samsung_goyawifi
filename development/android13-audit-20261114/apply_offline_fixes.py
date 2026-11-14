from pathlib import Path
import shutil,subprocess,json,hashlib,urllib.request
root=Path('/root/t110-android13-audit')
native=root/'platform/frameworks/native'
surface=native/'libs/gui/Surface.cpp'
s=surface.read_text()
assert 'T110 legacy dequeue retry' not in s
s=s.replace('#include <gui/Surface.h>','#include <gui/Surface.h>\n#include <cutils/properties.h>')
anchor='''    int result = c->dequeueBuffer(&buf, &fenceFd);
    if (result != OK) {
'''
assert s.count(anchor)==1
addition='''    int result = c->dequeueBuffer(&buf, &fenceFd);
    // T110 legacy dequeue retry: the stock EGL worker can queue after swap
    // returns. Match the working Nougat contract, scoped to this device and
    // this deprecated callback. Preserve the normal fence/cancel path below.
    if (result == INVALID_OPERATION && property_get_bool("ro.t110.legacy_gpu", false)) {
        const nsecs_t deadline = systemTime(SYSTEM_TIME_MONOTONIC) + ms2ns(100);
        do {
            {
                Mutex::Autolock lock(c->mMutex);
                const nsecs_t remaining = deadline - systemTime(SYSTEM_TIME_MONOTONIC);
                if (remaining <= 0) break;
                c->mQueueBufferCondition.waitRelative(c->mMutex,
                        remaining < ms2ns(5) ? remaining : ms2ns(5));
            }
            result = c->dequeueBuffer(&buf, &fenceFd);
        } while (result == INVALID_OPERATION &&
                systemTime(SYSTEM_TIME_MONOTONIC) < deadline);
    }
    if (result != OK) {
'''
s=s.replace(anchor,addition);surface.write_text(s)
# Verify this include's link dependency in the exact pinned build description.
url='https://raw.githubusercontent.com/LineageOS/android_frameworks_native/915ad642e331e0f8ea107b5f5519f2c6f1e7e01c/libs/gui/Android.bp'
bp=urllib.request.urlopen(url,timeout=30).read()
assert b'"libcutils"' in bp
(root/'libgui-Android.bp').write_bytes(bp)
# Build inputs are reviewed source only; binaries remain in the private restoration tree.
audit=root/'device/development/android13-audit-20261114'
audit.mkdir(exist_ok=True)
out=audit/'patches';out.mkdir(exist_ok=True)
patch=subprocess.check_output(['git','-C',str(native),'diff','--binary','HEAD'])
(out/'0001-libgui-t110-bounded-legacy-dequeue.patch').write_bytes(patch)
shutil.copy2(root/'upstream-provenance.json',audit/'upstream-provenance.json')
# Compile/test the actual changed callback with controlled queue/fence/clock
# boundaries. This is a host semantic regression, not an ARM or GPU qualification.
start=s.index('int Surface::hook_dequeueBuffer_DEPRECATED(')
end=s.index('\nint Surface::hook_cancelBuffer_DEPRECATED',start)
function=s[start:end]
harness=r'''#include <cassert>
#include <cerrno>
#include <memory>
#include <vector>
#include <algorithm>
#include <cstdio>
using nsecs_t=long long;
constexpr int OK=0,INVALID_OPERATION=-38,SYSTEM_TIME_MONOTONIC=0;
long long now=0; bool enabled=true; int fenceWait=0,closed=0;
long long systemTime(int){return now;}
long long ms2ns(long long n){return n*1000000;}
bool property_get_bool(const char*,bool){return enabled;}
struct Mutex { struct Autolock { explicit Autolock(Mutex&){} }; };
struct Condition { int waits=0; int waitRelative(Mutex&,long long n){assert(n>0&&n<=ms2ns(5));now+=n;++waits;return 0;} };
struct ANativeWindowBuffer{};
struct ANativeWindow{};
struct Fence { explicit Fence(int fd):fd(fd){} ~Fence(){if(fd>=0)++closed;} int waitForever(const char*){return fenceWait;} int fd; };
template<class T> using sp=std::shared_ptr<T>;
#define ALOGE(...) ((void)0)
struct Surface:ANativeWindow {
 Mutex mMutex;Condition mQueueBufferCondition;std::vector<int> results;int calls=0,cancels=0;ANativeWindowBuffer b;
 static Surface* getSelf(ANativeWindow*w){return static_cast<Surface*>(w);}
 int dequeueBuffer(ANativeWindowBuffer** out,int* fd){int r=results[std::min(size_t(calls++),results.size()-1)];if(!r){*out=&b;*fd=19;}return r;}
 int cancelBuffer(ANativeWindowBuffer* out,int fd){assert(out==&b&&fd==-1);++cancels;return 0;}
 static int hook_dequeueBuffer_DEPRECATED(ANativeWindow*,ANativeWindowBuffer**);
};
'''+function+r'''
void reset(){now=0;enabled=true;fenceWait=0;closed=0;}
int main(){
 ANativeWindowBuffer* b=nullptr;
 reset();Surface immediate;immediate.results={0};assert(Surface::hook_dequeueBuffer_DEPRECATED(&immediate,&b)==0&&b==&immediate.b&&immediate.calls==1&&closed==1);
 reset();Surface delayed;delayed.results={INVALID_OPERATION,INVALID_OPERATION,0};assert(Surface::hook_dequeueBuffer_DEPRECATED(&delayed,&b)==0&&delayed.calls==3&&now==ms2ns(10)&&closed==1);
 reset();Surface timeout;timeout.results={INVALID_OPERATION};assert(Surface::hook_dequeueBuffer_DEPRECATED(&timeout,&b)==INVALID_OPERATION&&now==ms2ns(100)&&timeout.calls==21&&closed==0);
 reset();enabled=false;Surface other;other.results={INVALID_OPERATION,0};assert(Surface::hook_dequeueBuffer_DEPRECATED(&other,&b)==INVALID_OPERATION&&other.calls==1&&now==0);
 reset();Surface error;error.results={-ENOMEM};assert(Surface::hook_dequeueBuffer_DEPRECATED(&error,&b)==-ENOMEM&&error.calls==1&&now==0);
 reset();fenceWait=-ETIMEDOUT;Surface fence;fence.results={INVALID_OPERATION,0};assert(Surface::hook_dequeueBuffer_DEPRECATED(&fence,&b)==-ETIMEDOUT&&fence.cancels==1&&closed==1);
 puts("PASS: real callback immediate/delayed/timeout/device isolation/error/fence ownership cases");
}
'''
(audit/'tests').mkdir(exist_ok=True)
(audit/'tests/dequeue_callback_test.cpp').write_text(harness)
binary=root/'dequeue_callback_test'
subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(audit/'tests/dequeue_callback_test.cpp'),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
subprocess.run(['git','-C',str(native),'diff','--check'],check=True)
report=dict(status='HOST_CALLBACK_REGRESSION_PASS_NOT_ARM_BUILD_OR_GPU_TEST',cases=6,
            patch_sha256=hashlib.sha256(patch).hexdigest(),libgui_dependency_url=url,
            timeout_ms=100,full_android13_build=False,flashed=False)
(audit/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Saved reviewed patch and verification record:',audit)
