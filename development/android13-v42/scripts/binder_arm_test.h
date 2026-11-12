/* Isolated QEMU regression test for legacy Binder ABI + SELinux hooks.
 * Not an Android userspace compatibility test. Included by seccomp_arm_test.c.
 */
#include <stdint.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include "binder.h"
static int binder_write_command(int fd, uint32_t cmd, const void *payload, size_t len) {
 unsigned char bytes[256];
 if(len+4>sizeof(bytes))return -1;
 memcpy(bytes,&cmd,4);if(len)memcpy(bytes+4,payload,len);
 struct binder_write_read b={.write_size=(long)(len+4),.write_buffer=(unsigned long)bytes};
 int r;do{r=ioctl(fd,BINDER_WRITE_READ,&b);}while(r<0&&errno==EINTR);
 return r||b.write_consumed!=(long)(len+4)?-1:0;
}
static int binder_receive(int fd, uint32_t wanted, struct binder_transaction_data *tx) {
 for(int tries=0;tries<32;tries++) {
  unsigned char bytes[1024];
  struct binder_write_read b={.read_size=sizeof(bytes),.read_buffer=(unsigned long)bytes};
  if(ioctl(fd,BINDER_WRITE_READ,&b)<0){perror("binder read");return -1;}
  for(size_t at=0;at<(size_t)b.read_consumed;) {
   uint32_t cmd;if(at+4>(size_t)b.read_consumed)return -1;
   memcpy(&cmd,bytes+at,4);at+=4;size_t n=_IOC_SIZE(cmd);
   if(at+n>(size_t)b.read_consumed)return -1;
   if(cmd==wanted){if(tx){if(n!=sizeof(*tx))return -1;memcpy(tx,bytes+at,n);}return 0;}
   if(cmd==BR_FAILED_REPLY||cmd==BR_DEAD_REPLY||cmd==BR_ERROR){fprintf(stderr,"Unexpected Binder error %x\n",cmd);return -1;}
   at+=n;
  }
 }
 return -1;
}
static int binder_open_test(void **mapping) {
 int fd=open("/testdev/binder",O_RDWR|O_CLOEXEC);if(fd<0){perror("open binder");return -1;}
 struct binder_version v={0};
 if(ioctl(fd,BINDER_VERSION,&v)||v.protocol_version!=7){close(fd);return -1;}
 *mapping=mmap(0,1024*1024,PROT_READ,MAP_PRIVATE,fd,0);
 if(*mapping==MAP_FAILED){close(fd);return -1;}
 return fd;
}
static int binder_roundtrip(int deny_call) {
 alarm(8);void *manager_map=0;int manager=binder_open_test(&manager_map),zero=0;
 if(manager<0)return 1;
 if(ioctl(manager,BINDER_SET_CONTEXT_MGR,&zero)){perror("binder context manager");return 2;}
 if(binder_write_command(manager,BC_ENTER_LOOPER,0,0))return 3;
 pid_t child=fork();
 if(child<0)return 4;
 if(!child) {
  close(manager);void *map=0;int fd=binder_open_test(&map);if(fd<0)_exit(10);
  uint32_t payload=0x13579bdf;
  struct binder_transaction_data tx={.code=42,.data_size=sizeof(payload),.data.ptr.buffer=&payload};
  if(binder_write_command(fd,BC_TRANSACTION,&tx,sizeof(tx)))_exit(11);
  struct binder_transaction_data reply;
  if(deny_call)_exit(binder_receive(fd,BR_FAILED_REPLY,0)?12:0);
  if(binder_receive(fd,BR_REPLY,&reply))_exit(13);
  uint32_t got=0;if(reply.data_size!=sizeof(got))_exit(14);
  memcpy(&got,reply.data.ptr.buffer,sizeof(got));
  _exit(got==(payload^0xffffffffu)?0:15);
 }
 int result=0;
 if(!deny_call) {
  struct binder_transaction_data tx;
  if(binder_receive(manager,BR_TRANSACTION,&tx))result=5;
  else if(tx.code!=42||tx.data_size!=4||tx.sender_pid!=child)result=6;
  else {
   uint32_t value;memcpy(&value,tx.data.ptr.buffer,4);value^=0xffffffffu;
   struct binder_transaction_data reply={.data_size=4,.data.ptr.buffer=&value};
   if(binder_write_command(manager,BC_REPLY,&reply,sizeof(reply)))result=7;
  }
 }
 if(result)kill(child,SIGKILL);
 int status=0;if(waitpid(child,&status,0)!=child||!WIFEXITED(status)||WEXITSTATUS(status))result=8;
 munmap(manager_map,1024*1024);close(manager);alarm(0);return result;
}
static int test_binder_allow(void){return binder_roundtrip(0);}
static int test_binder_deny(void){return binder_roundtrip(1);}
static int install_binder_deny_policy(void) {
 int fd=open("/policy30-deny-binder.bin",O_RDONLY);struct stat st;
 if(fd<0||fstat(fd,&st))return 1;
 char *b=malloc(st.st_size);if(!b)return 2;
 ssize_t n=read(fd,b,st.st_size);close(fd);if(n!=st.st_size)return 3;
 fd=open("/selinux/load",O_WRONLY);if(fd<0)return 4;
 n=write(fd,b,st.st_size);close(fd);free(b);if(n!=st.st_size)return 5;
 fd=open("/selinux/enforce",O_WRONLY);if(fd<0)return 6;
 n=write(fd,"1",1);close(fd);return n==1?0:7;
}