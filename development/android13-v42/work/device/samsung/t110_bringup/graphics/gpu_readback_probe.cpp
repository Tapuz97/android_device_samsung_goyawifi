// SPDX-License-Identifier: Apache-2.0
// Render to private offscreen targets only; do not touch the display or its services.
#include "T110EglWindow.h"
#include "GpuReadbackProtocol.h"
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include <hardware/gralloc.h>
#include <ui/GraphicBuffer.h>
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <array>
#include <cstring>
#include <cerrno>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include <binder/Binder.h>
#include <binder/IServiceManager.h>
#include <binder/ProcessState.h>
#include <binder/Parcel.h>
#include <gui/ScreenCaptureResults.h>
using namespace android;
using android::renderengine::gl::T110EglWindow;

class ProbeBufferService final : public BBinder {
public:
    ProbeBufferService(const sp<GraphicBuffer>& buffer,bool retain) : mBuffer(buffer),mRetain(retain) {}
    status_t onTransact(uint32_t code,const Parcel&,Parcel* reply,uint32_t) override {
        if(code!=IBinder::FIRST_CALL_TRANSACTION||!mBuffer)return BAD_VALUE;
        gui::ScreenCaptureResults results;results.buffer=std::move(mBuffer);
        if(mRetain)return results.writeToParcel(reply);
        // Exact old capture payload: only FD-backed handle, without an owner.
        reply->writeBool(true);reply->write(*results.buffer);reply->writeBool(false);
        reply->writeBool(false);reply->writeBool(false);
        reply->writeUint32(static_cast<uint32_t>(results.capturedDataspace));reply->writeInt32(0);
        return NO_ERROR;
    }
private:
    sp<GraphicBuffer> mBuffer;const bool mRetain;
};

static int binderProcess(sp<GraphicBuffer>& target,const char* label,bool retain) {
    ProcessState::self()->startThreadPool();char name[100];
    snprintf(name,sizeof(name),"dev.t110.captureprobe.%d.%d",getpid(),retain?1:0);
    auto service=sp<ProbeBufferService>::make(target,retain);
    status_t status=defaultServiceManager()->addService(String16(name),service);
    if(status!=NO_ERROR){printf("%s add_service=%d\n",label,status);return 40;}
    target.clear();
    char* args[]={const_cast<char*>("/data/local/tmp/t110-gpu-readback/t110_graphic_import_probe"),const_cast<char*>("--binder"),name,const_cast<char*>(label),nullptr};
    fflush(stdout);pid_t child=fork();
    if(child==0){for(int fd=3;fd<4096;++fd)close(fd);execv(args[0],args);_exit(41);}
    if(child<0)return 42;int childStatus=0;
    while(waitpid(child,&childStatus,0)<0)if(errno!=EINTR)return 43;
    return WIFEXITED(childStatus)?WEXITSTATUS(childStatus):44;
}

static int crossProcess(sp<GraphicBuffer>& target,const char* label,bool worker,int release=0) {
    Packet packet{};packet.size=target->getFlattenedSize();packet.count=target->getFdCount();
    if(packet.size>packet.bytes.size()||packet.count>32)return 30;
    std::array<int,32> fds{};void* cursor=packet.bytes.data();size_t size=packet.size,count=packet.count;int* fdCursor=fds.data();
    if(target->flatten(cursor,size,fdCursor,count)!=NO_ERROR)return 31;
    int sv[2];if(socketpair(AF_UNIX,SOCK_SEQPACKET,0,sv))return 32;
    char number[24];snprintf(number,sizeof(number),"%d",sv[1]);
    char* args[]={const_cast<char*>("/data/local/tmp/t110-gpu-readback/t110_graphic_import_probe"),const_cast<char*>(worker?"--receive":"--receive-main"),number,const_cast<char*>(label),nullptr};
    fflush(stdout);pid_t child=fork();
    if(child==0){for(int fd=3;fd<4096;++fd)if(fd!=sv[1])close(fd);execv(args[0],args);_exit(33);}
    close(sv[1]);if(child<0){close(sv[0]);return 34;}
    Control control{};iovec io{&packet,size_t(packet.size+8)};msghdr message{};
    message.msg_iov=&io;message.msg_iovlen=1;message.msg_control=control.bytes;message.msg_controllen=CMSG_SPACE(packet.count*sizeof(int));
    auto* cm=CMSG_FIRSTHDR(&message);cm->cmsg_level=SOL_SOCKET;cm->cmsg_type=SCM_RIGHTS;cm->cmsg_len=CMSG_LEN(packet.count*sizeof(int));
    memcpy(CMSG_DATA(cm),fds.data(),packet.count*sizeof(int));
    ssize_t sent=sendmsg(sv[0],&message,MSG_NOSIGNAL);
    if(release==1)target.clear();
    char imported=0;ssize_t ack=recv(sv[0],&imported,1,0);
    if(release==2)target.clear();
    if(ack==1&&imported=='I')send(sv[0],"R",1,MSG_NOSIGNAL);
    close(sv[0]);int status=0;
    while(waitpid(child,&status,0)<0)if(errno!=EINTR)return 35;
    if(sent!=ssize_t(packet.size+8)||!WIFEXITED(status))return 36;
    return WEXITSTATUS(status);
}
static bool probe(EGLDisplay display,EGLConfig config,EGLContext context,EGLSurface stub,
                  const char* label,uint32_t width,uint32_t height,uint64_t usage,int release=0) {
    auto target=sp<GraphicBuffer>::make(width,height,HAL_PIXEL_FORMAT_RGBA_8888,1,usage,label);
    if(target->initCheck()!=NO_ERROR){printf("%s allocation=%d\n",label,target->initCheck());return false;}
    status_t result;
    {
        T110EglWindow window(display,config,context,stub,target);
        if(window.status()!=NO_ERROR){printf("%s window=%d\n",label,window.status());return false;}
        glViewport(0,0,width,height);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glEnable(GL_SCISSOR_TEST);
        const GLfloat colors[4][3]={{1,0,0},{0,1,0},{0,0,1},{1,1,1}};
        for(uint32_t i=0;i<4;++i){uint32_t left=width*i/4,right=width*(i+1)/4;
            glScissor(left,0,right-left,height);glClearColor(colors[i][0],colors[i][1],colors[i][2],1);glClear(GL_COLOR_BUFFER_BIT);}
        glDisable(GL_SCISSOR_TEST);result=window.finish();
    }
    if(result!=NO_ERROR){printf("%s finish=%d\n",label,result);return false;}
    if(release>=3){int status=binderProcess(target,label,release==4);
        printf("%s owner_token=%d imported_process_exit=%d\n",label,release==4,status);return status==0;}
    if(release){int status=crossProcess(target,label,true,release);
        printf("%s owner_release_mode=%d imported_worker_exit=%d\n",label,release,status);return status==0;}
    // The consumer must read before any CPU lock in the allocation owner.
    int worker=crossProcess(target,label,true),main=crossProcess(target,label,false);
    printf("%s imported_worker_exit=%d imported_main_exit=%d\n",label,worker,main);
    return checkPixels(target,label)&&worker==0&&main==0;
}
int main() {
    EGLDisplay display=eglGetDisplay(EGL_DEFAULT_DISPLAY);EGLint major=0,minor=0;
    if(!eglInitialize(display,&major,&minor)){printf("initialize=%x\n",eglGetError());return 2;}
    eglBindAPI(EGL_OPENGL_ES_API);
    EGLint attrs[]={EGL_SURFACE_TYPE,EGL_WINDOW_BIT|EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_DEPTH_SIZE,0,EGL_STENCIL_SIZE,0,EGL_NONE};
    EGLConfig config=nullptr;EGLint count=0;
    if(!eglChooseConfig(display,attrs,&config,1,&count)||count<1){printf("config=%x\n",eglGetError());return 3;}
    const EGLint contextAttrs[]={EGL_CONTEXT_CLIENT_VERSION,2,EGL_NONE};
    EGLContext context=eglCreateContext(display,config,EGL_NO_CONTEXT,contextAttrs);
    const EGLint pbufferAttrs[]={EGL_WIDTH,1,EGL_HEIGHT,1,EGL_NONE};
    EGLSurface stub=eglCreatePbufferSurface(display,config,pbufferAttrs);
    if(context==EGL_NO_CONTEXT||stub==EGL_NO_SURFACE||!eglMakeCurrent(display,stub,stub,context)){
        printf("context_or_stub=%x\n",eglGetError());return 4;
    }
    const uint64_t base=GRALLOC_USAGE_HW_RENDER|GRALLOC_USAGE_HW_TEXTURE|GRALLOC_USAGE_SW_READ_OFTEN;
    probe(display,config,context,stub,"client-landscape",1024,600,base|GRALLOC_USAGE_HW_FB);
    probe(display,config,context,stub,"client-portrait",600,1024,base|GRALLOC_USAGE_HW_FB);
    const uint64_t shot=base|GRALLOC_USAGE_HW_COMPOSER|GRALLOC_USAGE_SW_WRITE_OFTEN;
    probe(display,config,context,stub,"screenshot-portrait",600,1024,shot);
    probe(display,config,context,stub,"screenshot-landscape",1024,600,shot);
    probe(display,config,context,stub,"screenshot-linear",600,1024,shot|0x80000000u);
    probe(display,config,context,stub,"owner-freed-before-import",600,1024,shot,1);
    probe(display,config,context,stub,"owner-freed-after-import",600,1024,shot,2);
    probe(display,config,context,stub,"binder-old-payload",600,1024,shot,3);
    probe(display,config,context,stub,"binder-owner-token",600,1024,shot,4);
    eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);
    eglDestroySurface(display,stub);eglDestroyContext(display,context);eglTerminate(display);
    return 0; // Per-case pixel results, not exit status, qualify correctness.
}
