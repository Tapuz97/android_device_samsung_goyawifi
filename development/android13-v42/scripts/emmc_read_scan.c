#define _GNU_SOURCE
#define _FILE_OFFSET_BITS 64
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <linux/fs.h>
#include <time.h>
#include <unistd.h>
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
int main(void){
 int fd=open("/dev/block/mmcblk0",O_RDONLY|O_DIRECT|O_CLOEXEC);if(fd<0){perror("open");return 2;}
 uint64_t size=0;if(ioctl(fd,BLKGETSIZE64,&size)||size!=7818182656ULL)return 2;
 void *buf=0;if(posix_memalign(&buf,4096,65536))return 2;
 setvbuf(stdout,0,_IONBF,0);double start=now();unsigned bad=0;uint64_t offset;
 for(offset=0;offset<size;offset+=65536){
  size_t count=size-offset<65536?size-offset:65536;
  ssize_t n=pread(fd,buf,count,(off_t)offset);
  if(n!=(ssize_t)count){
   for(size_t i=0;i<count;i+=4096){
    errno=0;n=pread(fd,buf,4096,(off_t)(offset+i));int e=errno;
    if(n!=4096){bad++;printf("{\"bad_block\":%" PRIu64 ",\"bytes\":%ld,\"errno\":%d}\n",(offset+i)/4096,(long)n,e);}
    if(bad>=64||now()-start>360){printf("{\"complete\":false,\"bad_count\":%u,\"stopped_offset\":%" PRIu64 "}\n",bad,offset+i);return 3;}
   }
  }
  if(offset%(128*1024*1024)==0)printf("{\"progress_bytes\":%" PRIu64 ",\"seconds\":%.3f}\n",offset+count,now()-start);
  if(now()-start>360){printf("{\"complete\":false,\"bad_count\":%u,\"stopped_offset\":%" PRIu64 "}\n",bad,offset);return 3;}
 }
 printf("{\"complete\":true,\"bytes_scanned\":%" PRIu64 ",\"bad_count\":%u,\"seconds\":%.3f}\n",size,bad,now()-start);free(buf);close(fd);return bad?1:0;
}