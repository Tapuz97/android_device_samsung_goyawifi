#include <stdio.h>
#include <sys/reboot.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void) {
    setbuf(stdout,NULL);
    pid_t child=fork();int status=0;
    if(child==0){execl("/netd-target-probe","/netd-target-probe",(char *)0);_exit(127);}
    if(child<0||waitpid(child,&status,0)<0||!WIFEXITED(status)||WEXITSTATUS(status)){
        puts("NETD_TARGET_GUEST_FAIL");reboot(RB_POWER_OFF);return 1;
    }
    execl("/uid-regression","/uid-regression",(char *)0);
    puts("NETD_UID_EXEC_FAIL");reboot(RB_POWER_OFF);return 1;
}
