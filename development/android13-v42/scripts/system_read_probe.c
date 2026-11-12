#define _GNU_SOURCE
#define _FILE_OFFSET_BITS 64
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <linux/fs.h>
#include <time.h>
#include <unistd.h>
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
int main(int argc,char **argv){
 if(argc<2||argc>17){fprintf(stderr,"Specify 1-16 SYSTEM 4KiB block indices. Reads only.\n");return 2;}
 int fd=open("/dev/block/mmcblk0p15",O_RDONLY|O_DIRECT|O_CLOEXEC);if(fd<0){perror("open");return 2;}
 uint64_t size=0;if(ioctl(fd,BLKGETSIZE64,&size)||size!=1594884096ULL){fprintf(stderr,"Unexpected SYSTEM geometry\n");return 2;}
 void *buffer=0;if(posix_memalign(&buffer,4096,4096))return 2;
 int failed=0;setvbuf(stdout,0,_IONBF,0);
 for(int i=1;i<argc;i++) {
  char *end;unsigned long block=strtoul(argv[i],&end,10);if(*end||block>=size/4096)return 2;
  double start=now();errno=0;ssize_t n=pread(fd,buffer,4096,(off_t)block*4096);int error=errno;
  uint32_t hash=2166136261u;for(ssize_t j=0;j<n;j++)hash=(hash^((unsigned char*)buffer)[j])*16777619u;
  printf("{\"block\":%lu,\"bytes\":%ld,\"errno\":%d,\"seconds\":%.6f,\"fnv1a32\":\"%08x\"}\n",block,(long)n,error,now()-start,hash);
  if(n!=4096)failed=1;
 }
 free(buffer);close(fd);return failed;
}