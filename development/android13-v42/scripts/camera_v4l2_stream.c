/* Bounded standard V4L2 stream probe. Report statistics; do not save images. */
#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

struct ion_alloc {
    uint32_t length, alignment, heap_mask, flags, handle;
};
struct ion_fd {
    uint32_t handle;
    int fd;
};
#define T110_ION_ALLOC _IOWR('I', 0, struct ion_alloc)
#define T110_ION_FREE _IOWR('I', 1, uint32_t)
#define T110_ION_SHARE _IOWR('I', 4, struct ion_fd)

static void *map_carveout(int ion, size_t length) {
    struct ion_alloc allocation = {.length=length,.alignment=4096,.heap_mask=1u<<2};
    if(ioctl(ion,T110_ION_ALLOC,&allocation)) return MAP_FAILED;
    struct ion_fd shared = {.handle=allocation.handle,.fd=-1};
    void *address=MAP_FAILED;
    if(!ioctl(ion,T110_ION_SHARE,&shared)) {
        address=mmap(NULL,length,PROT_READ|PROT_WRITE,MAP_SHARED,shared.fd,0);
        close(shared.fd);
    }
    int error=errno;
    ioctl(ion,T110_ION_FREE,&allocation.handle);
    errno=error;
    return address;
}

int main(int argc, char **argv) {
    int use_ion=argc==2&&!strcmp(argv[1],"--ion-userptr");
    if(argc!=1&&!use_ion){fprintf(stderr,"usage: %s [--ion-userptr]\n",argv[0]);return 2;}
    int result=1, streaming=0;
    int ion=-1;
    void *buffers[4]={0}; size_t lengths[4]={0};
    setvbuf(stdout,NULL,_IONBF,0);
    int fd=open("/dev/video0",O_RDWR|O_NONBLOCK|O_CLOEXEC);
    if(fd<0){perror("open");return 1;}
    struct v4l2_format fmt={.type=V4L2_BUF_TYPE_VIDEO_CAPTURE};
    fmt.fmt.pix.width=640;fmt.fmt.pix.height=480;
    fmt.fmt.pix.pixelformat=V4L2_PIX_FMT_UYVY;fmt.fmt.pix.field=V4L2_FIELD_ANY;
    if(ioctl(fd,VIDIOC_S_FMT,&fmt)){perror("S_FMT");goto done;}
    printf("format=%08x width=%u height=%u stride=%u size=%u\n",
            fmt.fmt.pix.pixelformat,fmt.fmt.pix.width,fmt.fmt.pix.height,
            fmt.fmt.pix.bytesperline,fmt.fmt.pix.sizeimage);
    struct v4l2_frmivalenum interval={.pixel_format=fmt.fmt.pix.pixelformat,
            .width=fmt.fmt.pix.width,.height=fmt.fmt.pix.height};
    if(ioctl(fd,VIDIOC_ENUM_FRAMEINTERVALS,&interval)) {
        printf("enum_frame_intervals_errno=%d\n",errno);
    } else if(interval.type==V4L2_FRMIVAL_TYPE_DISCRETE) {
        printf("first_frame_interval=%u/%u\n",
                interval.discrete.numerator,interval.discrete.denominator);
    }
    struct v4l2_streamparm parameters={.type=V4L2_BUF_TYPE_VIDEO_CAPTURE};
    if(ioctl(fd,VIDIOC_G_PARM,&parameters)) {
        printf("get_stream_parameters_errno=%d\n",errno);
    } else {
        printf("capture_capabilities=%x nominal_frame_interval=%u/%u\n",
                parameters.parm.capture.capability,
                parameters.parm.capture.timeperframe.numerator,
                parameters.parm.capture.timeperframe.denominator);
    }
    if(!fmt.fmt.pix.sizeimage||fmt.fmt.pix.sizeimage>16*1024*1024){puts("unexpected buffer size");goto done;}
    if(use_ion) {
        ion=open("/dev/ion",O_RDWR|O_CLOEXEC);
        if(ion<0){perror("open ion");goto done;}
    }
    struct v4l2_requestbuffers req={.count=2,.type=V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .memory=use_ion?V4L2_MEMORY_USERPTR:V4L2_MEMORY_MMAP};
    if(ioctl(fd,VIDIOC_REQBUFS,&req)){perror("REQBUFS");goto done;}
    if(req.count<2||req.count>4){puts("unexpected buffer count");goto done;}
    for(unsigned n=0;n<req.count;n++){
        struct v4l2_buffer b={.type=req.type,.memory=req.memory,.index=n};
        if(use_ion) {
            b.length=fmt.fmt.pix.sizeimage;
        } else if(ioctl(fd,VIDIOC_QUERYBUF,&b)){perror("QUERYBUF");goto done;}
        lengths[n]=b.length;
        if(b.length>16*1024*1024){puts("unexpected mmap size");goto done;}
        buffers[n]=use_ion?map_carveout(ion,b.length):
                mmap(NULL,b.length,PROT_READ|PROT_WRITE,MAP_SHARED,fd,b.m.offset);
        if(buffers[n]==MAP_FAILED){buffers[n]=NULL;perror("mmap");goto done;}
        if(use_ion) b.m.userptr=(unsigned long)buffers[n];
        if(ioctl(fd,VIDIOC_QBUF,&b)){perror("QBUF");goto done;}
    }
    enum v4l2_buf_type type=req.type;
    if(ioctl(fd,VIDIOC_STREAMON,&type)){perror("STREAMON");goto done;}
    streaming=1;
    struct timespec started;
    if(clock_gettime(CLOCK_MONOTONIC,&started)) goto done;
    for(unsigned n=0;n<3;n++){
        struct pollfd p={.fd=fd,.events=POLLIN};
        if(poll(&p,1,3000)<=0){puts("frame poll timeout");goto done;}
        struct v4l2_buffer b={.type=req.type,.memory=req.memory};
        if(ioctl(fd,VIDIOC_DQBUF,&b)){perror("DQBUF");goto done;}
        if(b.index>=req.count||!b.bytesused||b.bytesused>lengths[b.index]||
                (b.flags&V4L2_BUF_FLAG_ERROR)){puts("invalid frame");goto done;}
        struct timespec now;
        if(clock_gettime(CLOCK_MONOTONIC,&now)) goto done;
        double elapsed_ms=(now.tv_sec-started.tv_sec)*1000.0+
                (now.tv_nsec-started.tv_nsec)/1000000.0;
        const uint8_t *v=buffers[b.index];uint32_t hash=2166136261u;unsigned lo=255,hi=0;
        for(unsigned i=0;i<b.bytesused;i++){hash=(hash^v[i])*16777619u;if(v[i]<lo)lo=v[i];if(v[i]>hi)hi=v[i];}
        printf("frame=%u sequence=%u bytes=%u hash=%08x min=%u max=%u flags=%x elapsed_ms=%.1f\n",
                n,b.sequence,b.bytesused,hash,lo,hi,b.flags,elapsed_ms);
        if(use_ion){b.m.userptr=(unsigned long)buffers[b.index];b.length=lengths[b.index];}
        if(ioctl(fd,VIDIOC_QBUF,&b)){perror("QBUF");goto done;}
    }
    puts("THREE_V4L2_FRAMES_RECEIVED_NO_IMAGES_SAVED");result=0;
done:
    if(streaming){enum v4l2_buf_type t=V4L2_BUF_TYPE_VIDEO_CAPTURE;ioctl(fd,VIDIOC_STREAMOFF,&t);}
    close(fd);
    for(unsigned n=0;n<4;n++)if(buffers[n])munmap(buffers[n],lengths[n]);
    if(ion>=0)close(ion);
    return result;
}
