#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/reboot.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
#ifndef SYS_SECCOMP
#define SYS_SECCOMP 1
#endif
#ifndef SYS_seccomp
#define SYS_seccomp 383
#endif
static int failures;
static volatile sig_atomic_t trapped, trap_ok;
static int filter(unsigned action, unsigned flags, int via_prctl) {
 struct sock_filter insns[]={
  BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,arch)),
  BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,AUDIT_ARCH_ARM,1,0),
  BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL),
  BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr)),
  BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,SYS_getppid,0,1),
  BPF_STMT(BPF_RET|BPF_K,action),
  BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)};
 struct sock_fprog prog={.len=sizeof(insns)/sizeof(insns[0]),.filter=insns};
 return via_prctl?prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&prog):syscall(SYS_seccomp,SECCOMP_SET_MODE_FILTER,flags,&prog);
}
static int denied(void) { errno=0;return syscall(SYS_getppid)==-1 && errno==EPERM; }
static int nnp(void){return prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0);}
static int test_nnp(void) {
 if(nnp() || prctl(PR_GET_NO_NEW_PRIVS,0,0,0,0)!=1)return 1;
 errno=0;if(prctl(PR_SET_NO_NEW_PRIVS,0,0,0,0)!=-1 || errno!=EINVAL)return 2;
 return 0;
}
static int test_unprivileged(void) {
 if(setgid(1000)||setuid(1000))return 1;
 errno=0;if(filter(SECCOMP_RET_ALLOW,0,0)!=-1||errno!=EACCES)return 2;
 return nnp()||filter(SECCOMP_RET_ERRNO|EPERM,0,0)||!denied();
}
static int test_errno(void) {return nnp()||filter(SECCOMP_RET_ERRNO|EPERM,0,0)||!denied()||syscall(SYS_getpid)<=0;}
static int test_prctl(void) {return nnp()||filter(SECCOMP_RET_ERRNO|EPERM,0,1)||!denied();}
static int test_fork(void) {
 if(test_errno())return 1;
 pid_t p=fork();if(p<0)return 2;if(!p)_exit(!denied());
 int s;if(waitpid(p,&s,0)<0)return 3;return !WIFEXITED(s)||WEXITSTATUS(s);
}
static int test_exec(void) {
 if(test_errno())return 1;
 execl("/init","/init","--exec-probe",NULL);return 2;
}
static void on_trap(int s,siginfo_t *i,void *ctx) {(void)ctx;trapped=1;trap_ok=s==SIGSYS&&i->si_code==SYS_SECCOMP&&i->si_syscall==SYS_getppid&&i->si_arch==AUDIT_ARCH_ARM;}
static int test_trap(void) {
 struct sigaction a={.sa_sigaction=on_trap,.sa_flags=SA_SIGINFO};sigemptyset(&a.sa_mask);
 if(sigaction(SIGSYS,&a,NULL)||nnp()||filter(SECCOMP_RET_TRAP,0,0))return 1;
 syscall(SYS_getppid);return !trapped||!trap_ok;
}
static int test_kill(void) {
 if(nnp()||filter(SECCOMP_RET_KILL,0,0))return 1;
 syscall(SYS_getppid);return 2;
}
static pthread_barrier_t ready,installed;
static void *worker(void *arg){pthread_barrier_wait(&ready);pthread_barrier_wait(&installed);return (void *)(long)!denied();}
static int test_tsync(void) {
 pthread_t thread;void *ret;
 if(pthread_barrier_init(&ready,0,2)||pthread_barrier_init(&installed,0,2)||pthread_create(&thread,0,worker,0))return 1;
 pthread_barrier_wait(&ready);
 int bad=nnp()||filter(SECCOMP_RET_ERRNO|EPERM,SECCOMP_FILTER_FLAG_TSYNC,0);
 pthread_barrier_wait(&installed);pthread_join(thread,&ret);
 return bad||ret!=0||!denied();
}
static void run(const char *name,int(*test)(void),int expect_signal) {
 pid_t p=fork();if(!p)_exit(test());int s=0;
 int ok=p>0&&waitpid(p,&s,0)==p&&(expect_signal?(WIFSIGNALED(s)&&WTERMSIG(s)==expect_signal):(WIFEXITED(s)&&WEXITSTATUS(s)==0));
 printf("%s %s status=%d\n",ok?"PASS":"FAIL",name,s);if(!ok)failures++;
}
#ifdef TEST_POLICY30
static int load_policy30(void) {
 mkdir("/selinux",0755);
 if(mount("selinuxfs","/selinux","selinuxfs",0,0)){perror("mount selinuxfs");return 1;}
 FILE *v=fopen("/selinux/policyvers","r");int version=0;
 if(!v)return 2;
 if(fscanf(v,"%d",&version)!=1){fclose(v);return 2;}fclose(v);printf("SELinux maximum policy version=%d\n",version);
 if(version<30)return 3;
 int fd=open("/policy30.bin",O_RDONLY);if(fd<0)return 4;
 struct stat st;if(fstat(fd,&st)){close(fd);return 5;}
 char *b=malloc(st.st_size);if(!b)return 6;
 ssize_t n=read(fd,b,st.st_size);close(fd);if(n!=st.st_size)return 7;
 fd=open("/selinux/load",O_WRONLY);if(fd<0){perror("open selinux load");return 8;}
 n=write(fd,b,st.st_size);close(fd);free(b);
 if(n!=st.st_size){perror("load policy30");return 9;}
 return 0;
}
#endif
#ifdef TEST_BINDER
#include "binder_arm_test.h"
#endif
int main(int argc,char **argv){
 if(argc>1&&!strcmp(argv[1],"--exec-probe"))return !denied()||prctl(PR_GET_NO_NEW_PRIVS,0,0,0,0)!=1;
 setvbuf(stdout,0,_IONBF,0);mount("proc","/proc","proc",0,0);puts("T110 SECCOMP ARM TEST START");
 #ifdef TEST_POLICY30
 int policy_result=load_policy30();printf("%s SELinux policy30 with ioctl xperms result=%d\n",policy_result?"FAIL":"PASS",policy_result);if(policy_result)failures++;
#endif
 run("no_new_privs sticky",test_nnp,0);run("unprivileged filter gate",test_unprivileged,0);run("seccomp syscall errno/allow",test_errno,0);run("prctl filter",test_prctl,0);run("fork inheritance",test_fork,0);run("exec inheritance",test_exec,0);run("SIGSYS trap metadata",test_trap,0);run("kill action",test_kill,SIGSYS);run("thread synchronization",test_tsync,0);
#ifdef TEST_BINDER
 mkdir("/testdev",0755);
 if(mount("devtmpfs","/testdev","devtmpfs",0,0)){perror("mount devtmpfs");failures++;}
 else {
  run("Binder protocol7 cross-process roundtrip",test_binder_allow,0);
  int policy_bad=install_binder_deny_policy();
  if(policy_bad){printf("FAIL Binder deny policy load result=%d\n",policy_bad);failures++;}
  else run("Binder SELinux denies call in enforcing mode",test_binder_deny,0);
 }
#endif
 printf("T110 SECCOMP ARM TEST RESULT failures=%d\n",failures);sync();reboot(RB_POWER_OFF);for(;;)pause();
}
