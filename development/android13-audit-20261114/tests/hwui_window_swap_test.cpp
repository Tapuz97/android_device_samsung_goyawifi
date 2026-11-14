#include <cassert>
#include <cstdint>
#include <cstdio>
using EGLint=int;using EGLBoolean=int;using EGLSurface=void*;using GLubyte=unsigned char;
constexpr int EGL_TRUE=1,EGL_FALSE=0,EGL_SUCCESS=0x3000,EGL_BAD_SURFACE=0x300d,EGL_BAD_NATIVE_WINDOW=0x300b;
constexpr int EGL_BUFFER_AGE_EXT=0x313d,GL_RGBA=0x1908,GL_UNSIGNED_BYTE=0x1401;
bool legacy=false;int reads=0,plain=0,damage=0,ageQueries=0;EGLint error=EGL_SUCCESS;EGLBoolean swapResult=EGL_TRUE;
bool property_get_bool(const char*,bool){return legacy;}
void glReadPixels(int,int,int,int,int,int,void*){++reads;}
EGLBoolean eglSwapBuffers(void*,EGLSurface){++plain;return swapResult;}
EGLBoolean eglSwapBuffersWithDamageKHR(void*,EGLSurface,int*,int){++damage;return EGL_TRUE;}
EGLint eglGetError(){return error;}
bool eglQuerySurface(void*,EGLSurface,int,int* out){++ageQueries;*out=4;return true;}
#define CC_UNLIKELY(x) (x)
#define CC_LIKELY(x) (x)
#define ATRACE_NAME(x) ((void)0)
#define ALOGW(...) ((void)0)
#define LOG_ALWAYS_FATAL(...) assert(false)
const char* egl_error_str(int){return "test";}
struct Properties {static bool waitForGpuCompletion;};bool Properties::waitForGpuCompletion=false;
struct SkRect {bool isEmpty()const{return false;}};
struct Frame {EGLSurface mSurface=nullptr;void map(const SkRect&,int*)const{}};
struct EglManager {
 enum class SwapBehavior{Discard,Preserved,BufferAge};SwapBehavior mSwapBehavior=SwapBehavior::BufferAge;
 void* mEglDisplay=nullptr;void fence(){}
 int queryBufferAge(EGLSurface);bool swapBuffers(const Frame&,const SkRect&);
};
EGLint EglManager::queryBufferAge(EGLSurface surface) {
    // Age zero makes CanvasContext expand damage to the complete window.
    if (property_get_bool("ro.t110.legacy_gpu", false)) return 0;
    switch (mSwapBehavior) {
        case SwapBehavior::Discard:
            return 0;
        case SwapBehavior::Preserved:
            return 1;
        case SwapBehavior::BufferAge:
            EGLint bufferAge;
            eglQuerySurface(mEglDisplay, surface, EGL_BUFFER_AGE_EXT, &bufferAge);
            return bufferAge;
    }
    return 0;
}
bool EglManager::swapBuffers(const Frame& frame, const SkRect& screenDirty) {
    if (CC_UNLIKELY(Properties::waitForGpuCompletion)) {
        ATRACE_NAME("Finishing GPU work");
        fence();
    }

    // The stock T110 Vivante driver leaves window geometry in an unresolved
    // render target across swap, even after glFinish. A one-pixel read forces
    // its legacy window resolve without reading the full frame. Full-panel
    // geometry, clipping, texture and surface-recreation fixtures validate it.
    static const bool legacyT110 = property_get_bool("ro.t110.legacy_gpu", false);
    if (legacyT110) {
        GLubyte pixel[4];
        glReadPixels(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel);
    }

    EGLBoolean swapped = EGL_TRUE;
    if (legacyT110) {
        // Stock window queueing/resolve is the ordinary EGL swap contract.
        // Full GPU redraw above means no retained-pixel/damage hint is needed.
        swapped = eglSwapBuffers(mEglDisplay, frame.mSurface);
    } else {
        EGLint rects[4];
        frame.map(screenDirty, rects);
        eglSwapBuffersWithDamageKHR(mEglDisplay, frame.mSurface, rects, screenDirty.isEmpty() ? 0 : 1);
    }

    EGLint err = eglGetError();
    if (legacyT110 && swapped != EGL_TRUE && err == EGL_SUCCESS) {
        ALOGW("T110 legacy window swap returned false without an EGL error");
        return false;
    }
    if (CC_LIKELY(err == EGL_SUCCESS)) {
        return true;
    }
    if (err == EGL_BAD_SURFACE || err == EGL_BAD_NATIVE_WINDOW) {
        // For some reason our surface was destroyed out from under us
        // This really shouldn't happen, but if it does we can recover easily
        // by just not trying to use the surface anymore
        ALOGW("swapBuffers encountered EGL error %d on %p, halting rendering...", err,
              frame.mSurface);
        return false;
    }
    LOG_ALWAYS_FATAL("Encountered EGL error %d %s during rendering", err, egl_error_str(err));
    // Impossible to hit this, but the compiler doesn't know that
    return false;
}
int main(int argc,char**){
 legacy=argc>1;
 EglManager manager;Frame frame;SkRect dirty;
 if(legacy){
  assert(manager.queryBufferAge(nullptr)==0&&ageQueries==0);
  assert(manager.swapBuffers(frame,dirty)&&reads==1&&plain==1&&damage==0);
  swapResult=EGL_FALSE;error=EGL_SUCCESS;assert(!manager.swapBuffers(frame,dirty));
  error=EGL_BAD_SURFACE;assert(!manager.swapBuffers(frame,dirty));
  error=EGL_BAD_NATIVE_WINDOW;assert(!manager.swapBuffers(frame,dirty));
 }else{
  assert(manager.queryBufferAge(nullptr)==4&&ageQueries==1);
  assert(manager.swapBuffers(frame,dirty)&&reads==0&&plain==0&&damage==1);
  error=EGL_BAD_SURFACE;assert(!manager.swapBuffers(frame,dirty));
 }
 puts(legacy?"PASS: ARM T110 full-frame GPU swap semantics":"PASS: ARM non-T110 age/damage behavior preserved");
}
