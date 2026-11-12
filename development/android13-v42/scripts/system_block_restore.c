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
#include <unistd.h>
static const unsigned blocks[]={250715,250728,250730,250731};
static const uint32_t hashes[]={0x35c2a3df,0xb50fbb82,0xcf2c4ceb,0xc3508747};
static uint32_t fnv(const unsigned char *p,size_t n){uint32_t h=2166136261u;for(size_t i=0;i<n;i++)h=(h^p[i])*16777619u;return h;}
static int text_equals(const char *path,const char *expected){char b[256];FILE*f=fopen(path,"r");if(!f)return 0;char*r=fgets(b,sizeof(b),f);fclose(f);if(!r)return 0;b[strcspn(b,"\r\n")]=0;return !strcmp(b,expected);}
static int load(const char *p,void *b,size_t n){int f=open(p,O_RDONLY);if(f<0)return 1;ssize_t r=read(f,b,n);unsigned char extra;ssize_t tail=read(f,&extra,1);close(f);return r!=(ssize_t)n||tail!=0;}
int main(int argc,char**argv){
 setvbuf(stdout,0,_IONBF,0);int selected=-1;
 if(argc==3&&!strcmp(argv[1],"--restore-block")){char*e;unsigned long n=strtoul(argv[2],&e,10);if(*e)return 2;for(int i=0;i<4;i++)if(n==blocks[i])selected=i;if(selected<0)return 2;}
 else if(argc!=2||strcmp(argv[1],"--check-only")){fprintf(stderr,"Use --check-only or --restore-block <one of four verified blocks>.\n");return 2;}
 if(!text_equals("/sys/block/mmcblk0/device/cid","1101003030384745T110_ADB_SERIAL")||!text_equals("/sys/block/mmcblk0/mmcblk0p15/start","1392640")||!text_equals("/sys/block/mmcblk0/mmcblk0p15/size","3115008")){fprintf(stderr,"Device identity/partition mismatch\n");return 2;}
 FILE*m=fopen("/proc/mounts","r");if(!m)return 2;char line[1024];while(fgets(line,sizeof(line),m))if(strstr(line,"/dev/block/mmcblk0")){fclose(m);fprintf(stderr,"Refusing mounted eMMC\n");return 2;}fclose(m);
 unsigned char *buffer=0,*readback=0;if(posix_memalign((void**)&buffer,4096,16384)||posix_memalign((void**)&readback,4096,4096))return 2;
 for(int i=0;i<4;i++){char path[96];snprintf(path,sizeof(path),"/tmp/t110-dictionary-repair/block-%u.bin",blocks[i]);if(load(path,buffer+i*4096,4096)||fnv(buffer+i*4096,4096)!=hashes[i]){fprintf(stderr,"Payload mismatch %u\n",blocks[i]);return 2;}}
 unsigned char inode[256];if(load("/tmp/t110-dictionary-repair/expected-inode.bin",inode,sizeof(inode))||fnv(inode,sizeof(inode))!=0xbbac87c4){fprintf(stderr,"Inode reference mismatch\n");return 2;}
 int fd=open("/dev/block/mmcblk0p15",(selected<0?O_RDONLY:O_RDWR)|O_DIRECT|O_SYNC|O_CLOEXEC);if(fd<0){perror("open SYSTEM");return 2;}
 uint64_t size=0;if(ioctl(fd,BLKGETSIZE64,&size)||size!=1594884096ULL)return 2;
 if(pread(fd,readback,4096,112*4096)!=4096||memcmp(readback+1024,inode,256)){fprintf(stderr,"Live dictionary inode does not match stock reference\n");return 2;}
 if(selected<0){puts("CHECK_ONLY_PASS: identity, geometry, unmounted state, all payloads and live inode verified; no device write");close(fd);return 0;}
 unsigned block=blocks[selected];off_t offset=(off_t)block*4096;
 printf("RESTORE_BEGIN block=%u bytes=4096\n",block);
 ssize_t n=pwrite(fd,buffer+selected*4096,4096,offset);if(n!=4096){perror("pwrite");return 3;}
 if(fsync(fd)){perror("fsync");return 3;}
 if(pread(fd,readback,4096,offset)!=4096||memcmp(readback,buffer+selected*4096,4096)){perror("direct readback mismatch");return 4;}
 printf("RESTORE_VERIFIED block=%u bytes=4096 fnv1a32=%08x\n",block,fnv(readback,4096));close(fd);free(buffer);free(readback);return 0;
}