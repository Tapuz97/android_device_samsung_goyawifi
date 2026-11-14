#include <cassert>
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
int Surface::hook_dequeueBuffer_DEPRECATED(ANativeWindow* window,
        ANativeWindowBuffer** buffer) {
    Surface* c = getSelf(window);
    ANativeWindowBuffer* buf;
    int fenceFd = -1;
    int result = c->dequeueBuffer(&buf, &fenceFd);
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
        return result;
    }
    sp<Fence> fence(new Fence(fenceFd));
    int waitResult = fence->waitForever("dequeueBuffer_DEPRECATED");
    if (waitResult != OK) {
        ALOGE("dequeueBuffer_DEPRECATED: Fence::wait returned an error: %d",
                waitResult);
        c->cancelBuffer(buf, -1);
        return waitResult;
    }
    *buffer = buf;
    return result;
}

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
