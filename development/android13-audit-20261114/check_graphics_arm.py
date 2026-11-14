from pathlib import Path
import subprocess,json
r=Path('/root/t110-android13-audit');out=r/'device/development/android13-audit-20261114'
source=r/'platform/frameworks/base/libs/hwui/renderthread/EglManager.cpp'
def function(text,signature):
 start=text.index(signature);brace=text.index('{',start);depth=1;end=brace+1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[start:end]
text=source.read_text()
fixture=r'''#include <cassert>
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
'''+function(text,'EGLint EglManager::queryBufferAge(')+'\n'+function(text,'bool EglManager::swapBuffers(')+r'''
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
'''
tests=out/'tests';(tests/'hwui_window_swap_test.cpp').write_text(fixture)
dest=r/'arm-checks';records=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True);records.append(dict(command=cmd,exit=p.returncode,diagnostics=p.stdout+p.stderr));print(p.stdout+p.stderr,end='',flush=True)
 if p.returncode:(dest/'graphics-results.json').write_text(json.dumps(records,indent=2)+'\n');raise SystemExit(p.returncode)
arm=['clang++','--target=armv7a-linux-gnueabihf','--sysroot=/usr/arm-linux-gnueabihf','--gcc-toolchain=/usr','-std=c++17','-Wall','-Wextra','-Werror']
run(arm+['-c',str(tests/'hwui_window_swap_test.cpp'),'-o',str(dest/'hwui-window-arm.o')])
run(['arm-linux-gnueabihf-g++',str(dest/'hwui-window-arm.o'),'-o',str(dest/'hwui-window-arm')])
for flags in ([],['legacy']):run(['qemu-arm','-L','/usr/arm-linux-gnueabihf',str(dest/'hwui-window-arm'),*flags])
# Earlier fixes: compile and execute the actual-source fixtures on ARM32 too.
for name in ('dequeue_callback_test','framebuffer_resume_test'):
 run(arm+['-I'+str(r/'platform/hardware/interfaces/graphics/composer/2.1/default'),'-c',str(tests/(name+'.cpp')),'-o',str(dest/(name+'-arm.o'))])
 run(['arm-linux-gnueabihf-g++',str(dest/(name+'-arm.o')),'-o',str(dest/(name+'-arm'))])
 run(['qemu-arm','-L','/usr/arm-linux-gnueabihf',str(dest/(name+'-arm'))])
(dest/'graphics-results.json').write_text(json.dumps(records,indent=2)+'\n')
print('PASS: ARM callback semantics only; not full libhwui/libgui/composer builds or GPU execution.')
