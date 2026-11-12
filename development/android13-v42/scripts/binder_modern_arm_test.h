/* Isolated QEMU regression test for legacy Binder ABI + SELinux hooks.
 * Not an Android userspace compatibility test. Included by seccomp_arm_test.c.
 */
#include <stdint.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include "uapi/binder.h"
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
  struct binder_transaction_data tx={.code=42,.data_size=sizeof(payload),.data.ptr.buffer=(uintptr_t)&payload};
  if(binder_write_command(fd,BC_TRANSACTION,&tx,sizeof(tx)))_exit(11);
  struct binder_transaction_data reply;
  if(deny_call)_exit(binder_receive(fd,BR_FAILED_REPLY,0)?12:0);
  if(binder_receive(fd,BR_REPLY,&reply))_exit(13);
  uint32_t got=0;if(reply.data_size!=sizeof(got))_exit(14);
  memcpy(&got,(void *)(uintptr_t)reply.data.ptr.buffer,sizeof(got));
  _exit(got==(payload^0xffffffffu)?0:15);
 }
 int result=0;
 if(!deny_call) {
  struct binder_transaction_data tx;
  if(binder_receive(manager,BR_TRANSACTION,&tx))result=5;
  else if(tx.code!=42||tx.data_size!=4||tx.sender_pid!=child)result=6;
  else {
   uint32_t value;memcpy(&value,(void *)(uintptr_t)tx.data.ptr.buffer,4);value^=0xffffffffu;
   struct binder_transaction_data reply={.data_size=4,.data.ptr.buffer=(uintptr_t)&value};
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
}/* Modern transport tests use the donor UAPI in 32-bit protocol-7 mode. */
static int modern_open(const char *path, void **map) {
 int fd=open(path,O_RDWR|O_CLOEXEC);if(fd<0){perror(path);return -1;}
 struct binder_version v={0};
 if(ioctl(fd,BINDER_VERSION,&v)||v.protocol_version!=7){close(fd);return -1;}
 *map=mmap(0,1024*1024,PROT_READ,MAP_PRIVATE,fd,0);
 if(*map==MAP_FAILED){close(fd);return -1;}return fd;
}
static int modern_manager(int fd) {
 int zero=0;return ioctl(fd,BINDER_SET_CONTEXT_MGR,&zero)||binder_write_command(fd,BC_ENTER_LOOPER,0,0);
}
static int child_status(pid_t child) {
 int status=0;return waitpid(child,&status,0)!=child||!WIFEXITED(status)||WEXITSTATUS(status);
}
static int modern_free(int fd, struct binder_transaction_data *tx) {
 binder_uintptr_t ptr=tx->data.ptr.buffer;return binder_write_command(fd,BC_FREE_BUFFER,&ptr,sizeof(ptr));
}
static int scalar_request(int fd,uint32_t value,uint32_t code) {
 struct binder_transaction_data tx={.code=code,.data_size=4,.data.ptr.buffer=(uintptr_t)&value};
 if(binder_write_command(fd,BC_TRANSACTION,&tx,sizeof(tx)))return 1;
 struct binder_transaction_data reply;if(binder_receive(fd,BR_REPLY,&reply)||reply.data_size!=4)return 2;
 uint32_t result;memcpy(&result,(void *)(uintptr_t)reply.data.ptr.buffer,4);
 int bad=result!=(value^0xffffffffu);return modern_free(fd,&reply)||bad;
}
static int scalar_reply(int fd,uint32_t code) {
 struct binder_transaction_data tx;if(binder_receive(fd,BR_TRANSACTION,&tx)||tx.data_size!=4||tx.code!=code)return 1;
 uint32_t value;memcpy(&value,(void *)(uintptr_t)tx.data.ptr.buffer,4);value^=0xffffffffu;
 struct binder_transaction_data reply={.data_size=4,.data.ptr.buffer=(uintptr_t)&value};
 return binder_write_command(fd,BC_REPLY,&reply,sizeof(reply))||modern_free(fd,&tx);
}
static int test_binder_contexts(void) {
 alarm(10);const char *paths[]={"/testdev/binder","/testdev/hwbinder","/testdev/vndbinder"};
 void *maps[3];int fds[3];pid_t children[3];
 for(int i=0;i<3;i++){fds[i]=modern_open(paths[i],&maps[i]);if(fds[i]<0||modern_manager(fds[i]))return 1+i;}
 for(int i=0;i<3;i++) {
  children[i]=fork();if(children[i]<0)return 4;
  if(!children[i]){for(int j=0;j<3;j++)close(fds[j]);void *m;int fd=modern_open(paths[i],&m);if(fd<0)_exit(5);_exit(scalar_request(fd,0x11223300+i,100+i));}
 }
 int bad=0;for(int i=0;i<3;i++)bad|=scalar_reply(fds[i],100+i);
 for(int i=0;i<3;i++){bad|=child_status(children[i]);munmap(maps[i],1024*1024);close(fds[i]);}
 alarm(0);return bad;
}
struct sg_parent {uint32_t magic;binder_uintptr_t child;};
struct sg_objects {struct binder_buffer_object parent,child;};
static int sg_send(int fd,uint32_t command,int bad_case) {
 char text[]="T110 nested Binder buffer";
 struct sg_parent parent={.magic=0xaabbccdd,.child=(uintptr_t)text};
 struct sg_objects objects={
  .parent={.hdr.type=BINDER_TYPE_PTR,.buffer=(uintptr_t)&parent,.length=sizeof(parent)},
  .child={.hdr.type=BINDER_TYPE_PTR,.flags=BINDER_BUFFER_FLAG_HAS_PARENT,.buffer=(uintptr_t)text,.length=sizeof(text),.parent=0,.parent_offset=offsetof(struct sg_parent,child)}};
 binder_size_t offsets[]={offsetof(struct sg_objects,parent),offsetof(struct sg_objects,child)};
 if(bad_case==1)objects.child.parent=9;
 struct binder_transaction_data_sg tx={.transaction_data={.code=202,.data_size=sizeof(objects),.offsets_size=sizeof(offsets),.data.ptr.buffer=(uintptr_t)&objects,.data.ptr.offsets=(uintptr_t)offsets},.buffers_size=((sizeof(parent)+7)&~7)+((sizeof(text)+7)&~7)};
 if(bad_case==2)tx.buffers_size=0;
 return binder_write_command(fd,command,&tx,sizeof(tx));
}
static int in_map(void *map,binder_uintptr_t ptr,size_t len) {
 uintptr_t start=(uintptr_t)map;return ptr>=start&&len<=1024*1024&&ptr-start<=1024*1024-len;
}
static int sg_verify(void *map,struct binder_transaction_data *tx) {
 if(tx->data_size!=sizeof(struct sg_objects)||tx->offsets_size!=2*sizeof(binder_size_t)||!in_map(map,tx->data.ptr.buffer,tx->data_size))return 1;
 struct sg_objects o;memcpy(&o,(void *)(uintptr_t)tx->data.ptr.buffer,sizeof(o));
 if(o.parent.hdr.type!=BINDER_TYPE_PTR||o.child.hdr.type!=BINDER_TYPE_PTR||o.parent.length!=sizeof(struct sg_parent)||o.child.length!=sizeof("T110 nested Binder buffer"))return 2;
 if(!in_map(map,o.parent.buffer,o.parent.length)||!in_map(map,o.child.buffer,o.child.length))return 3;
 struct sg_parent p;memcpy(&p,(void *)(uintptr_t)o.parent.buffer,sizeof(p));
 if(p.magic!=0xaabbccdd||p.child!=o.child.buffer||memcmp((void *)(uintptr_t)p.child,"T110 nested Binder buffer",o.child.length))return 4;
 return 0;
}
static int sg_roundtrip(int bad_case) {
 alarm(10);void *map;int fd=modern_open("/testdev/hwbinder",&map);if(fd<0||modern_manager(fd))return 1;
 pid_t child=fork();if(child<0)return 2;
 if(!child) {
  close(fd);void *cm;int c=modern_open("/testdev/hwbinder",&cm);if(c<0||sg_send(c,BC_TRANSACTION_SG,bad_case))_exit(3);
  if(bad_case){if(binder_receive(c,BR_FAILED_REPLY,0))_exit(4);_exit(scalar_request(c,12345,303));}
  struct binder_transaction_data reply;if(binder_receive(c,BR_REPLY,&reply)||sg_verify(cm,&reply))_exit(5);
  _exit(modern_free(c,&reply)?6:0);
 }
 int bad=0;
 if(bad_case)bad=scalar_reply(fd,303);
 else {struct binder_transaction_data tx;bad=binder_receive(fd,BR_TRANSACTION,&tx);if(!bad)bad=sg_verify(map,&tx)||sg_send(fd,BC_REPLY_SG,0)||modern_free(fd,&tx);}
 if(bad)kill(child,SIGKILL);bad|=child_status(child);munmap(map,1024*1024);close(fd);alarm(0);return bad;
}
static int test_binder_sg_ptr(void){return sg_roundtrip(0);}
static int test_binder_sg_bad_parent(void){return sg_roundtrip(1);}
static int test_binder_sg_short_buffer(void){return sg_roundtrip(2);}
struct fda_parent {int fds[2];uint32_t marker;};
struct fda_objects {struct binder_buffer_object parent;struct binder_fd_array_object array;};

static int test_binder_sg_fda(void) {
 alarm(10);void *map;int fd=modern_open("/testdev/hwbinder",&map);if(fd<0||modern_manager(fd))return 1;
 pid_t child=fork();if(child<0)return 2;
 if(!child) {
  close(fd);void *cm;int c=modern_open("/testdev/hwbinder",&cm);if(c<0)_exit(3);
  uint32_t request=404;
  struct binder_transaction_data tx={.code=404,.flags=TF_ACCEPT_FDS,.data_size=4,.data.ptr.buffer=(uintptr_t)&request};
  if(binder_write_command(c,BC_TRANSACTION,&tx,sizeof(tx)))_exit(4);
  struct binder_transaction_data reply;if(binder_receive(c,BR_REPLY,&reply)||reply.data_size!=sizeof(struct fda_objects)||!in_map(cm,reply.data.ptr.buffer,reply.data_size))_exit(5);
  struct fda_objects objects;memcpy(&objects,(void *)(uintptr_t)reply.data.ptr.buffer,sizeof(objects));
  if(!in_map(cm,objects.parent.buffer,sizeof(struct fda_parent)))_exit(6);
  struct fda_parent data;memcpy(&data,(void *)(uintptr_t)objects.parent.buffer,sizeof(data));char a=0,b=0;
  if(data.marker!=0xabcdef01||read(data.fds[0],&a,1)!=1||read(data.fds[1],&b,1)!=1||a!='A'||b!='B')_exit(7);
  for(int i=0;i<2;i++) {int flags=fcntl(data.fds[i],F_GETFD);if(flags<0||!(flags&FD_CLOEXEC))_exit(8);}
  if(modern_free(c,&reply))_exit(9);
  for(int i=0;i<2;i++){errno=0;if(fcntl(data.fds[i],F_GETFD)!=-1||errno!=EBADF)_exit(10);}
  _exit(0);
 }
 struct binder_transaction_data request;int bad=binder_receive(fd,BR_TRANSACTION,&request);
 int a[2],b[2];if(!bad&&(request.code!=404||pipe(a)||pipe(b)))bad=11;
 if(!bad) {
  if(write(a[1],"A",1)!=1||write(b[1],"B",1)!=1)bad=12;
  close(a[1]);close(b[1]);struct fda_parent data={{a[0],b[0]},0xabcdef01};
  struct fda_objects objects={.parent={.hdr.type=BINDER_TYPE_PTR,.buffer=(uintptr_t)&data,.length=sizeof(data)},.array={.hdr.type=BINDER_TYPE_FDA,.num_fds=2,.parent=0,.parent_offset=offsetof(struct fda_parent,fds)}};
  binder_size_t offsets[]={offsetof(struct fda_objects,parent),offsetof(struct fda_objects,array)};
  struct binder_transaction_data_sg reply={.transaction_data={.data_size=sizeof(objects),.offsets_size=sizeof(offsets),.data.ptr.buffer=(uintptr_t)&objects,.data.ptr.offsets=(uintptr_t)offsets},.buffers_size=(sizeof(data)+7)&~7};
  if(binder_write_command(fd,BC_REPLY_SG,&reply,sizeof(reply))||modern_free(fd,&request))bad=13;
  close(a[0]);close(b[0]);
 }
 if(bad)kill(child,SIGKILL);bad|=child_status(child);munmap(map,1024*1024);close(fd);alarm(0);return bad;
}
static int modern_load_policy(const char *path) {
 int fd=open(path,O_RDONLY);struct stat st;if(fd<0||fstat(fd,&st))return 1;
 char *b=malloc(st.st_size);if(!b)return 2;
 ssize_t n=read(fd,b,st.st_size);close(fd);if(n!=st.st_size)return 3;
 fd=open("/selinux/load",O_WRONLY);if(fd<0)return 4;
 n=write(fd,b,st.st_size);close(fd);free(b);return n==st.st_size?0:5;
}
static int test_binder_denied_manager_unclaimed(void) {
 alarm(10);void *m1,*m2;int fd1=modern_open("/testdev/vndbinder",&m1),zero=0;
 if(fd1<0||modern_load_policy("/policy30-deny-manager.bin"))return 1;
 int enforce=open("/selinux/enforce",O_WRONLY);if(enforce<0||write(enforce,"1",1)!=1)return 2;close(enforce);
 errno=0;int result=ioctl(fd1,BINDER_SET_CONTEXT_MGR,&zero),error=errno;
 /* Restore the allow fixture even when the denial assertion fails. */
 if(modern_load_policy("/policy30.bin"))return 3;
 int bad=result!=-1||error!=EACCES;
 int fd2=modern_open("/testdev/vndbinder",&m2);if(fd2<0)return 4;
 if(ioctl(fd2,BINDER_SET_CONTEXT_MGR,&zero)){perror("manager after denied claim");bad=5;}
 munmap(m1,1024*1024);munmap(m2,1024*1024);close(fd1);close(fd2);alarm(0);return bad;
}
