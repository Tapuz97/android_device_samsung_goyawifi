// Offscreen composition cost and spare reuse check. Never maps the display.
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include <ui/GraphicBuffer.h>
#include <chrono>
#include <cstdio>
#include <unistd.h>
#include "T110EglWindow.h"
using namespace android;
using android::renderengine::gl::T110EglWindow;
static void require(bool ok, const char* what) {
    if (!ok) {printf("FAIL %s egl=%x gl=%x\n",what,eglGetError(),glGetError());_exit(1);}
}
int main() {
    setbuf(stdout,nullptr);
    EGLDisplay d=eglGetDisplay(EGL_DEFAULT_DISPLAY);
    require(eglInitialize(d,nullptr,nullptr),"initialize");
    EGLint attr[]={EGL_SURFACE_TYPE,EGL_WINDOW_BIT|EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES2_BIT,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE};
    EGLConfig cfg;EGLint n=0;require(eglChooseConfig(d,attr,&cfg,1,&n)&&n,"config");
    EGLint ca[]={EGL_CONTEXT_CLIENT_VERSION,2,EGL_NONE};
    EGLContext c=eglCreateContext(d,cfg,EGL_NO_CONTEXT,ca);require(c!=EGL_NO_CONTEXT,"context");
    EGLint sa[]={EGL_WIDTH,1,EGL_HEIGHT,1,EGL_NONE};
    EGLSurface stub=eglCreatePbufferSurface(d,cfg,sa);
    require(stub!=EGL_NO_SURFACE&&eglMakeCurrent(d,stub,stub,c),"stub");
    auto output=sp<GraphicBuffer>::make(600,1024,HAL_PIXEL_FORMAT_RGBA_8888,1,0x1b00,"T110 benchmark output");
    require(output->initCheck()==0,"output");
    auto start=std::chrono::steady_clock::now();
    for(int frame=0;frame<40;++frame) {
        T110EglWindow window(d,cfg,c,stub,output);require(window.status()==0,"window");
        glViewport(0,0,600,1024);glDisable(GL_SCISSOR_TEST);
        float red=(frame&1)?1.f:0.f;glClearColor(red,0.5f,0.25f,1);glClear(GL_COLOR_BUFFER_BIT);
        if(frame%10==0) {
            unsigned char pixel[4]={};glReadPixels(300,512,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);
            require(pixel[0]==(red?255:0)&&pixel[1]>=126&&pixel[1]<=129&&pixel[2]>=62&&pixel[2]<=65,"pixel");
        }
        require(window.finish()==0,"swap");
    }
    double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    printf("SWAP_BENCHMARK_PASS frames=40 total_ms=%.3f average_ms=%.3f\n",ms,ms/40);
    return 0;
}
