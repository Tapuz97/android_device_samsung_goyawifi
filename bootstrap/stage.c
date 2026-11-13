/* SM-T110 loop-image bootstrap. Never opens physical SYSTEM p15. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/loop.h>
#include <linux/reboot.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/xattr.h>
#include <unistd.h>

static int checkpoint_fd=-1;
static void checkpoint(const char *step) {
    dprintf(2,"<5>t110-nougat-stage: %s\n",step);
    if(checkpoint_fd>=0){dprintf(checkpoint_fd,"%s\n",step);fsync(checkpoint_fd);}
}
static __attribute__((noreturn)) void failed(const char *step) {
    int saved_errno=errno;
    if(checkpoint_fd>=0){dprintf(checkpoint_fd,"FAIL %s: %s\n",step,strerror(saved_errno));fsync(checkpoint_fd);}
    errno=saved_errno;
    dprintf(2,"<3>t110-nougat-stage: %s: %s\n",step,strerror(errno));
    sync();
    syscall(SYS_reboot,LINUX_REBOOT_MAGIC1,LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_RESTART2,"recovery");
    for (;;) pause();
}
static void mounted(const char *src,const char *dst,const char *type,
                    unsigned long flags,const char *data) {
    if(mount(src,dst,type,flags,data)) failed(dst);
}
static void directory(const char *path,mode_t mode) {
    if(mkdir(path,mode) && errno!=EEXIST) failed(path);
    struct stat st;
    if(lstat(path,&st)||!S_ISDIR(st.st_mode)) failed(path);
}
static void block(const char *name,const char *path) {
    char sys[160];unsigned maj,min;
    snprintf(sys,sizeof(sys),"/sys/class/block/%s/dev",name);
    /* eMMC enumeration is asynchronous. Preserve the working loader's
     * bounded readiness wait; a single early fopen can fail before probing. */
    for(unsigned attempt=0;attempt<100;++attempt){
        FILE *f=fopen(sys,"r");
        if(f){
            int count=fscanf(f,"%u:%u",&maj,&min);fclose(f);
            if(count!=2){errno=EINVAL;failed(sys);}
            if(mknod(path,S_IFBLK|0600,makedev(maj,min))&&errno!=EEXIST)failed(path);
            return;
        }
        if(errno!=ENOENT && errno!=ENODEV)failed(sys);
        usleep(100000);
    }
    errno=ETIMEDOUT;failed(sys);
}
static void load_policy(void) {
    /* Match the proven bring-up order before the new policy restricts kernel
     * domain operations. This candidate is explicitly permissive. */
    int enforce=open("/sys/fs/selinux/enforce",O_WRONLY|O_CLOEXEC);
    if(enforce<0||write(enforce,"0",1)!=1)failed("initial policy mode");
    close(enforce);
    int fd=open("/sepolicy",O_RDONLY|O_CLOEXEC);struct stat st;
    if(fd<0||fstat(fd,&st)||st.st_size<1024||st.st_size>4*1024*1024)failed("policy input");
    void *bytes=mmap(NULL,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);close(fd);
    if(bytes==MAP_FAILED)failed("policy mapping");
    fd=open("/sys/fs/selinux/load",O_WRONLY|O_CLOEXEC);
    if(fd<0||write(fd,bytes,st.st_size)!=st.st_size)failed("policy preload");
    close(fd);munmap(bytes,st.st_size);
    fd=open("/sys/fs/selinux/enforce",O_WRONLY|O_CLOEXEC);
    if(fd<0||write(fd,"0",1)!=1)failed("bring-up policy mode");
    close(fd);
    fd=open("/sys/fs/selinux/checkreqprot",O_WRONLY|O_CLOEXEC);
    if(fd<0||write(fd,"0",1)!=1)failed("policy checkreqprot");
    close(fd);
}
static void load_gpu(void) {
    int fd=open("/system/vendor/lib/modules/galcore.ko",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    struct stat st;
    if(fd<0||fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<100000||st.st_size>8000000)failed("matched GPU module");
    /* stat.st_size is 64-bit on Nougat ARM32; the raw syscall wants a
     * 32-bit unsigned long. Passing it directly shifts the parameters slot. */
    size_t size=(size_t)st.st_size;
    void *bytes=mmap(NULL,size,PROT_READ,MAP_PRIVATE,fd,0);close(fd);
    if(bytes==MAP_FAILED)failed("GPU module mapping");
    if(syscall(SYS_init_module,bytes,size,""))failed("GPU module load");
    munmap(bytes,size);
}
int main(void) {
    if(getpid()!=1)return 1;
    umask(0);
    mounted("tmpfs","/dev","tmpfs",MS_NOSUID,"mode=0755");
    if(mknod("/dev/kmsg",S_IFCHR|0600,makedev(1,11)))failed("kmsg node");
    int log=open("/dev/kmsg",O_WRONLY|O_CLOEXEC);
    if(log>=0){if(dup2(log,2)<0)failed("kmsg redirect");if(log!=2)close(log);}
    mounted("proc","/proc","proc",MS_NOSUID|MS_NODEV|MS_NOEXEC,NULL);
    mounted("sysfs","/sys","sysfs",MS_NOSUID|MS_NODEV|MS_NOEXEC,NULL);
    directory("/sys/fs/selinux",0755);
    mounted("selinuxfs","/sys/fs/selinux","selinuxfs",0,NULL);
    load_policy();
    directory("/dev/block",0755);
    directory("/dev/pts",0755);directory("/dev/socket",0755);
    mounted("devpts","/dev/pts","devpts",MS_NOSUID|MS_NOEXEC,"mode=0620,gid=5");
    if(mknod("/dev/null",S_IFCHR|0666,makedev(1,3)) ||
       mknod("/dev/random",S_IFCHR|0666,makedev(1,8)) ||
       mknod("/dev/urandom",S_IFCHR|0666,makedev(1,9)) ||
       mknod("/dev/ptmx",S_IFCHR|0666,makedev(5,2)))failed("early character nodes");
    block("mmcblk0p16","/dev/block/mmcblk0p16");
    /* Fixed T110 geometry. Installation separately verifies physical device identity. */
    FILE *geometry=fopen("/sys/class/block/mmcblk0p16/size","r");
    unsigned long sectors=0;
    if(!geometry||fscanf(geometry,"%lu",&sectors)!=1||sectors!=10760192UL)failed("userdata geometry");
    fclose(geometry);
    directory("/stage-data",0755);
    mounted("/dev/block/mmcblk0p16","/stage-data","ext4",MS_NOSUID|MS_NODEV|MS_NOATIME,NULL);
    checkpoint_fd=open("/stage-data/local/tmp/t110-lineage14-last-stage.log",
                       O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC|O_NOFOLLOW,0600);
    if(checkpoint_fd<0)failed("one-shot startup record");
    checkpoint("Physical userdata mounted; new bootstrap active");
    const char *data="/stage-data/local/tmp/t110-lineage14-data";
    directory(data,0771);directory("/data",0771);
    mounted(data,"/data",NULL,MS_BIND,NULL);
    directory("/data/cache",0770);directory("/cache",0770);
    mounted("/data/cache","/cache",NULL,MS_BIND,NULL);
    checkpoint("Isolated Nougat userdata mounted");
    int image=open("/stage-data/local/tmp/t110-lineage14-system.raw",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    struct stat info;
    if(image<0||fstat(image,&info)||!S_ISREG(info.st_mode)||info.st_size!=1594884096)failed("Nougat system geometry");
    block("loop0","/dev/block/loop0");
    int loop=open("/dev/block/loop0",O_RDONLY|O_CLOEXEC);int readonly=0;
    if(loop<0||ioctl(loop,LOOP_SET_FD,image)||ioctl(loop,BLKROGET,&readonly)||readonly!=1)failed("read-only system loop");
    close(loop);close(image);
    directory("/system",0755);
    mounted("/dev/block/loop0","/system","ext4",MS_RDONLY|MS_NODEV,"noload");
    checkpoint("Verified system loop mounted read-only");
    load_gpu();
    checkpoint("Matched GPU module loaded from system");
    dprintf(2,"<5>t110-nougat-stage: system mounted read-only; starting Android7 init\n");
    pid_t watchdog=fork();
    if(watchdog<0)failed("recovery safeguard");
    if(watchdog==0){
        unsigned remaining=1200;
        while(remaining)remaining=sleep(remaining);
        if(access("/dev/t110-keepalive",F_OK))failed("boot timeout");
        _exit(0);
    }
    /* Policy and early mounts are already prepared. Running N7 first-stage
     * would overlay /dev and re-exec argv[0], previously restarting this stage.
     * Label the real platform binary so exec transitions kernel -> init. */
    const char init_label[]="u:object_r:init_exec:s0";
    if(lsetxattr("/init.android","security.selinux",init_label,sizeof(init_label),0))
        failed("platform init label");
    checkpoint("Executing real Android7 init second-stage");
    char *args[]={"/init.android","--second-stage",NULL};
    execv("/init.android",args);
    failed("Android7 init exec");
    return 1;
}
