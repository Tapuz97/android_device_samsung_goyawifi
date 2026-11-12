#define _GNU_SOURCE
#define _FILE_OFFSET_BITS 64
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(void){void *b=0;if(posix_memalign(&b,4096,65536))return 2;int fd=open("/dev/block/mmcblk0p15",O_RDONLY|O_DIRECT);if(fd<0)return 2;for(int i=0;i<3;i++){errno=0;ssize_t n=pread(fd,b,65536,(off_t)250720*4096);uint32_t hash=2166136261U;if(n>0)for(ssize_t j=0;j<n;j++){hash^=((unsigned char*)b)[j];hash*=16777619U;}printf("attempt=%d bytes=%ld errno=%d fnv1a=%08x\n",i+1,(long)n,errno,hash);fflush(stdout);if(n!=65536)return 1;}free(b);close(fd);return 0;}
