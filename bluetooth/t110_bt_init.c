// SPDX-License-Identifier: Apache-2.0
// Reuse the active Wi-Fi combo firmware. Never reload it or toggle shared power.
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static long long now_ms(void) {
    struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return (long long)t.tv_sec*1000+t.tv_nsec/1000000;
}
static int save_controller_address(void) {
    int fd=open("/dev/mbtchar0",O_RDWR|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);
    if(fd<0){perror("open Bluetooth controller address transport");return 1;}
    const unsigned char command[]={1,9,16,0};
    if(write(fd,command,sizeof(command))!=sizeof(command)){close(fd);return 1;}
    unsigned char bytes[1024];size_t have=0;int result=1;
    long long deadline=now_ms()+3000;
    while(now_ms()<deadline) {
        while(have>=3) {
            if(bytes[0]!=4)goto done;
            size_t count=3+bytes[2];if(have<count)break;
            if(bytes[1]==14 && count==13 && bytes[4]==9 && bytes[5]==16 && bytes[6]==0) {
                int any=0,all_ff=1;for(int i=7;i<13;++i){any|=bytes[i];all_ff&=bytes[i]==255;}
                if(!any||all_ff)goto done;
                char address[19];int length=snprintf(address,sizeof(address),"%02x:%02x:%02x:%02x:%02x:%02x\n",bytes[12],bytes[11],bytes[10],bytes[9],bytes[8],bytes[7]);
                int out=open("/data/vendor/t110-bluetooth/controller_address.tmp",O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC|O_NOFOLLOW,0640);
                if(out<0){perror("create controller address file");goto done;}
                // init's restrictive umask removes the requested group-read bit.
                // Set the exact root:bluetooth mode before publishing the file.
                int ok=fchmod(out,0640)==0 && write(out,address,length)==length && fsync(out)==0;close(out);
                if(ok && !rename("/data/vendor/t110-bluetooth/controller_address.tmp","/data/vendor/t110-bluetooth/controller_address"))result=0;
                goto done;
            }
            memmove(bytes,bytes+count,have-count);have-=count;
        }
        long long remaining=deadline-now_ms();if(remaining<=0)break;
        struct pollfd poller={fd,POLLIN,0};int ready=poll(&poller,1,(int)remaining);
        if(ready<0&&errno==EINTR)continue;
        if(ready<=0)continue;
        if(poller.revents&(POLLERR|POLLHUP|POLLNVAL))break;
        ssize_t n=read(fd,bytes+have,sizeof(bytes)-have);
        if(n<0&&(errno==EINTR||errno==EAGAIN))continue;
        if(n<=0)break;
        have+=n;if(have==sizeof(bytes))break;
    }
done:
    close(fd);return result;
}
int main(void) {
    if(getuid()!=0)return 2;
    struct stat st;
    if(!lstat("/dev/mbtchar0",&st) && S_ISCHR(st.st_mode) && !(st.st_mode&0007))return save_controller_address();
    if(access("/sys/module/sd8xxx",F_OK)){fputs("Wi-Fi combo firmware not initialized\n",stderr);return 1;}
    int fd=open("/vendor/etc/bluetooth/modules/mbt8xxx.ko",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
    if(fd<0){perror("open Bluetooth module");return 1;}
    if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<64||st.st_size>2*1024*1024){close(fd);return 2;}
    size_t size=st.st_size;void* bytes=mmap(NULL,size,PROT_READ,MAP_PRIVATE,fd,0);close(fd);
    if(bytes==MAP_FAILED){perror("map Bluetooth module");return 1;}
    if(memcmp(bytes,"\177ELF\1\1",6)){munmap(bytes,size);return 2;}
    long result=syscall(SYS_init_module,bytes,size,"fw=1 drv_mode=1 debug_intf=0 require_fw_ready=1 req_fw_nowait=0");
    if(result)perror("initialize Bluetooth module");
    munmap(bytes,size);
    if(result)return 1;
    if(lstat("/dev/mbtchar0",&st)||!S_ISCHR(st.st_mode)||(st.st_mode&0007))return 1;
    return save_controller_address();
}
