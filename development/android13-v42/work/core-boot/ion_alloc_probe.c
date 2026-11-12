/* Bounded legacy ION alloc/share/map/free probe; all allocations are temporary. */
#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
struct alloc_data {uint32_t len,align,heap_mask,flags,handle;};
struct fd_data {uint32_t handle;int fd;};
#define ION_ALLOC _IOWR('I',0,struct alloc_data)
#define ION_FREE _IOWR('I',1,uint32_t)
#define ION_MAP _IOWR('I',2,struct fd_data)
#define ION_SHARE _IOWR('I',4,struct fd_data)
int main(void) {
    int ion=open("/dev/ion",O_RDWR|O_CLOEXEC);
    printf("ion_open=%d errno=%d uid=%d\n",ion,ion<0?errno:0,getuid());
    if(ion<0)return 1;
    const unsigned masks[]={~0u,1u,1u<<2};
    const unsigned sizes[]={4096,65536,1048576};int successes=0;
    for(unsigned m=0;m<3;m++)for(unsigned s=0;s<3;s++) {
        struct alloc_data a={sizes[s],0,masks[m],0,0};
        errno=0;int r=ioctl(ion,ION_ALLOC,&a);int error=errno;
        printf("mask=%08x size=%u alloc=%d errno=%d handle=%08x",masks[m],sizes[s],r,error,a.handle);
        if(!r) {
            struct fd_data legacy={a.handle,-1};errno=0;int mapped=ioctl(ion,ION_MAP,&legacy);
            printf(" legacy_map=%d errno=%d",mapped,errno);
            if(!mapped)close(legacy.fd);
            struct fd_data fd={a.handle,-1};errno=0;int shared=ioctl(ion,ION_SHARE,&fd);
            printf(" share=%d errno=%d fd=%d",shared,errno,fd.fd);
            if(!shared) {
                void *p=mmap(0,sizes[s],PROT_READ|PROT_WRITE,MAP_SHARED,fd.fd,0);
                printf(" map=%s errno=%d",p==MAP_FAILED?"FAIL":"OK",p==MAP_FAILED?errno:0);
                if(p!=MAP_FAILED) {volatile unsigned char *b=p;b[0]=0x37;b[sizes[s]-1]=0x59;
                    int ok=b[0]==0x37&&b[sizes[s]-1]==0x59;successes+=ok;printf(" bytes=%s",ok?"OK":"FAIL");munmap(p,sizes[s]);}
                close(fd.fd);
            }
            errno=0;int freed=ioctl(ion,ION_FREE,&a.handle);printf(" free=%d errno=%d",freed,errno);
        }
        puts("");
    }
    close(ion);return successes?0:2;
}
