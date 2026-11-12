#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <sys/random.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
static _Thread_local int tls_value;
static void *thread(void *unused) { (void)unused; tls_value=42; return (void *)(long)(tls_value!=42); }
int main(int argc,char **argv) {
 if(argc>1 && !strcmp(argv[1],"--child")) return 0;
 setvbuf(stdout,NULL,_IONBF,0);
 struct utsname u;if(uname(&u))return 1;
 printf("Android 13 bionic probe on %s %s\n",u.machine,u.release);
 struct timespec ts;if(clock_gettime(CLOCK_MONOTONIC,&ts))return 2;
 pthread_t t;void *result;tls_value=17;
 if(pthread_create(&t,NULL,thread,NULL)||pthread_join(t,&result)||result||tls_value!=17)return 3;
 puts("PASS pthread/TLS and monotonic clock");
 int event=eventfd(0,EFD_CLOEXEC),ep=epoll_create1(EPOLL_CLOEXEC);if(event<0||ep<0)return 4;close(event);close(ep);
 puts("PASS eventfd and epoll");
 unsigned char random[16];errno=0;ssize_t n=getrandom(random,sizeof(random),0);
 printf("getrandom bytes=%ld errno=%d (ENOSYS identifies a kernel compatibility gap)\n",(long)n,errno);
 if(getentropy(random,sizeof(random)))return 7;
 puts("PASS getentropy fallback");
 pid_t child=fork();if(child<0)return 5;if(!child){execl("/proc/self/exe","t110_bionic_probe","--child",NULL);_exit(99);}
 int status;if(waitpid(child,&status,0)!=child||!WIFEXITED(status)||WEXITSTATUS(status))return 6;
 puts("PASS fork/exec");puts("PASS Android 13 static bionic runtime");return 0;
}
