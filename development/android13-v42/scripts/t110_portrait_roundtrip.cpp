// Offscreen GPU/texture check. Never opens fb0 or changes display configuration.
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES2/gl2.h>
#include <GLES2/gl2ext.h>
#include <ui/GraphicBuffer.h>
#include <hardware/gralloc.h>
#include <cstdio>
#include <cstdlib>
#include <unistd.h>
#include "T110EglWindow.h"
using namespace android;
using android::renderengine::gl::T110EglWindow;
static void require(bool ok, const char* what) {
    if (!ok) { printf("FAIL %s EGL=%x GL=%x\n", what, eglGetError(), glGetError()); fflush(stdout); _exit(1); }
}
static GLuint shader(GLenum type, const char* text) {
    GLuint s=glCreateShader(type); glShaderSource(s,1,&text,nullptr); glCompileShader(s);
    GLint ok=0;glGetShaderiv(s,GL_COMPILE_STATUS,&ok);
    if (!ok) {char b[2048];glGetShaderInfoLog(s,sizeof(b),nullptr,b);puts(b);}
    require(ok,"shader");return s;
}
int main(int argc, char** argv) {
    setbuf(stdout,nullptr);
    const char* hint=argc>1?argv[1]:"0";
    EGLDisplay d=eglGetDisplay(EGL_DEFAULT_DISPLAY);require(eglInitialize(d,nullptr,nullptr),"initialize");
    EGLint attributes[]={EGL_SURFACE_TYPE,EGL_WINDOW_BIT|EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES2_BIT,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE};
    EGLConfig cfg;EGLint n=0;require(eglChooseConfig(d,attributes,&cfg,1,&n)&&n,"config");
    EGLint ca[]={EGL_CONTEXT_CLIENT_VERSION,2,EGL_NONE};EGLContext c=eglCreateContext(d,cfg,EGL_NO_CONTEXT,ca);
    require(c!=EGL_NO_CONTEXT,"context");EGLint sa[]={EGL_WIDTH,1,EGL_HEIGHT,1,EGL_NONE};EGLSurface stub=eglCreatePbufferSurface(d,cfg,sa);
    require(stub!=EGL_NO_SURFACE&&eglMakeCurrent(d,stub,stub,c),"stub");
    const char* vs="attribute vec2 position; attribute vec2 uv; varying vec2 texcoord; void main(){gl_Position=vec4(position,0.,1.);texcoord=uv;}";
    const char* fs="#extension GL_OES_EGL_image_external : require\nprecision mediump float; varying vec2 texcoord; uniform samplerExternalOES tex; void main(){gl_FragColor=texture2D(tex,texcoord);}";
    GLuint program=glCreateProgram();glAttachShader(program,shader(GL_VERTEX_SHADER,vs));glAttachShader(program,shader(GL_FRAGMENT_SHADER,fs));
    glBindAttribLocation(program,0,"position");glBindAttribLocation(program,1,"uv");glLinkProgram(program);GLint ok;glGetProgramiv(program,GL_LINK_STATUS,&ok);require(ok,"link");
    auto createImage=(PFNEGLCREATEIMAGEKHRPROC)eglGetProcAddress("eglCreateImageKHR");
    auto imageTarget=(PFNGLEGLIMAGETARGETTEXTURE2DOESPROC)eglGetProcAddress("glEGLImageTargetTexture2DOES");
    auto destroyImage=(PFNEGLDESTROYIMAGEKHRPROC)eglGetProcAddress("eglDestroyImageKHR");
    require(createImage&&imageTarget&&destroyImage,"image functions");
    for (bool portrait: {false,true}) {
        int w=portrait?600:1024,h=portrait?1024:600;
        auto source=sp<GraphicBuffer>::make(w,h,HAL_PIXEL_FORMAT_RGBA_8888,1,0xb00,"T110 offscreen source");require(source->initCheck()==0,"source allocation");
        printf("SOURCE %dx%d stride=%d\n",w,h,source->getStride());
        {
            setenv("T110_PROBE_HINT",hint,1);
            T110EglWindow window(d,cfg,c,stub,source);require(window.status()==0,"source window");
            EGLint ew=0,eh=0;eglQuerySurface(d,eglGetCurrentSurface(EGL_DRAW),EGL_WIDTH,&ew);eglQuerySurface(d,eglGetCurrentSurface(EGL_DRAW),EGL_HEIGHT,&eh);printf("EGL_SIZE %dx%d hint=%s\n",ew,eh,hint);
            glViewport(0,0,w,h);glEnable(GL_SCISSOR_TEST);
            const float colors[4][3]={{1,0,0},{0,1,0},{0,0,1},{1,1,1}};
            for(int q=0;q<4;q++){glScissor((q%2)*w/2,(q/2)*h/2,w/2,h/2);glClearColor(colors[q][0],colors[q][1],colors[q][2],1);glClear(GL_COLOR_BUFFER_BIT);}
            glDisable(GL_SCISSOR_TEST);require(window.finish()==0,"source swap");
        }
        unsetenv("T110_PROBE_HINT");
        EGLint ia[]={EGL_IMAGE_PRESERVED_KHR,EGL_TRUE,EGL_NONE};
        auto image=createImage(d,EGL_NO_CONTEXT,EGL_NATIVE_BUFFER_ANDROID,source->getNativeBuffer(),ia);require(image!=EGL_NO_IMAGE_KHR,"image import");
        GLuint texture;glGenTextures(1,&texture);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_EXTERNAL_OES,texture);imageTarget(GL_TEXTURE_EXTERNAL_OES,image);
        glTexParameteri(GL_TEXTURE_EXTERNAL_OES,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_EXTERNAL_OES,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_EXTERNAL_OES,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_EXTERNAL_OES,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
        require(glGetError()==0,"texture bind");
        for(int rotation: {0,3}) {
            int ow=600,oh=1024;
            auto output=sp<GraphicBuffer>::make(ow,oh,HAL_PIXEL_FORMAT_RGBA_8888,1,0x1b00,"T110 offscreen output");require(output->initCheck()==0,"output allocation");
            const auto* words=reinterpret_cast<const uint32_t*>(output->handle);
            printf("OUTPUT logical=%dx%d stride=%u header=%d,%d,%d words=",ow,oh,output->getStride(),output->handle->version,output->handle->numFds,output->handle->numInts);for(int k=5;k<30;k++)printf(" %d:%x",k,words[k]);puts("");
            T110EglWindow window(d,cfg,c,stub,output);require(window.status()==0,"output window");
            glViewport(0,0,ow,oh);glDisable(GL_SCISSOR_TEST);glDisable(GL_BLEND);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
            const float pos[]={-1,-1,1,-1,-1,1,1,1};
            const float uv0[]={0,0,1,0,0,1,1,1},uv3[]={1,0,1,1,0,0,0,1};
            glUseProgram(program);glUniform1i(glGetUniformLocation(program,"tex"),0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,0,pos);glVertexAttribPointer(1,2,GL_FLOAT,GL_FALSE,0,rotation?uv3:uv0);glEnableVertexAttribArray(0);glEnableVertexAttribArray(1);glDrawArrays(GL_TRIANGLE_STRIP,0,4);glFinish();
            for(int q=0;q<4;q++){unsigned char pixel[4]={};glReadPixels(ow/4+(q%2)*ow/2,oh/4+(q/2)*oh/2,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);printf("SAMPLE %dx%d rot=%d quadrant=%d rgba=%u,%u,%u,%u GL=%x\n",w,h,rotation,q,pixel[0],pixel[1],pixel[2],pixel[3],glGetError());}
            require(window.finish()==0,"output swap");
        }
        glDeleteTextures(1,&texture);destroyImage(d,image);
    }
    puts("ROUNDTRIP_COMPLETED_NO_DISPLAY_WRITES");fflush(stdout);_exit(0);
}
