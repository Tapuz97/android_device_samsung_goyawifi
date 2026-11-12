#pragma once
#include <ui/GraphicBuffer.h>
#include <hardware/gralloc.h>
#include <array>
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <sys/socket.h>
#include <unistd.h>
using namespace android;
inline bool checkPixels(const sp<GraphicBuffer>& target,const char* label) {
    const uint32_t width=target->getWidth(),height=target->getHeight();
    void* address=nullptr;status_t result=target->lock(GRALLOC_USAGE_SW_READ_OFTEN,&address);
    if(result!=NO_ERROR||!address){printf("%s lock=%d\n",label,result);return false;}
    uint64_t rgbBad=0,bgrBad=0,alphaBad=0;
    const uint8_t expected[4][3]={{255,0,0},{0,255,0},{0,0,255},{255,255,255}};
    const uint32_t stride=target->getStride();const auto* pixels=static_cast<const uint8_t*>(address);
    for(uint32_t y=0;y<height;++y)for(uint32_t x=0;x<width;++x) {
        const uint8_t* value=pixels+4*(static_cast<size_t>(y)*stride+x);
        uint32_t band=x*4/width;if(band>3)band=3;
        bool rgb=false,bgr=false;
        for(int c=0;c<3;++c) {
            rgb|=std::abs(int(value[c])-int(expected[band][c]))>3;
            bgr|=std::abs(int(value[2-c])-int(expected[band][c]))>3;
        }
        rgbBad+=rgb;bgrBad+=bgr;alphaBad+=value[3]<252;
    }
    target->unlock();
    printf("%s width=%u height=%u stride=%u usage=%llx rgb_bad=%llu bgr_bad=%llu alpha_bad=%llu total=%llu\n",
        label,width,height,stride,(unsigned long long)target->getUsage(),(unsigned long long)rgbBad,
        (unsigned long long)bgrBad,(unsigned long long)alphaBad,(unsigned long long)width*height);
    fflush(stdout);return rgbBad==0;
}
struct Packet {uint32_t size,count;alignas(4) std::array<uint8_t,4096> bytes;};
union Control {cmsghdr alignment;char bytes[CMSG_SPACE(32*sizeof(int))];};
inline int receiveBuffer(int fd,const char* label) {
    struct CloseSocket {int value;~CloseSocket(){close(value);}} socket{fd};
    Packet packet{};Control control{};iovec io{&packet,sizeof(packet)};msghdr message{};
    message.msg_iov=&io;message.msg_iovlen=1;message.msg_control=control.bytes;message.msg_controllen=sizeof(control.bytes);
    ssize_t got=recvmsg(fd,&message,0);
    if(got<8||packet.size>packet.bytes.size()||packet.count>32||got!=ssize_t(packet.size+8)||message.msg_flags&MSG_CTRUNC)return 20;
    auto* cm=CMSG_FIRSTHDR(&message);
    if(!cm||cm->cmsg_level!=SOL_SOCKET||cm->cmsg_type!=SCM_RIGHTS||cm->cmsg_len!=CMSG_LEN(packet.count*sizeof(int)))return 21;
    std::array<int,32> fds{};memcpy(fds.data(),CMSG_DATA(cm),packet.count*sizeof(int));
    auto imported=sp<GraphicBuffer>::make();const void* cursor=packet.bytes.data();size_t size=packet.size,count=packet.count;const int* fdCursor=fds.data();
    status_t status=imported->unflatten(cursor,size,fdCursor,count);
    if(status!=NO_ERROR){printf("%s unflatten=%d\n",label,status);return 22;}
    char permission=0;
    if(send(fd,"I",1,MSG_NOSIGNAL)!=1||recv(fd,&permission,1,0)!=1||permission!='R')return 24;
    return checkPixels(imported,label)?0:23;
}
