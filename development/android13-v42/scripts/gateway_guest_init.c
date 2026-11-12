#include <stdio.h>
#include <sys/reboot.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void) {
 setbuf(stdout,NULL);pid_t child=fork();int status=0;
 if(child==0){execl("/gateway-regression","/gateway-regression",(char *)0);_exit(127);}
 if(child<0||waitpid(child,&status,0)<0||!WIFEXITED(status)||WEXITSTATUS(status))puts("GATEWAY_GUEST_FAIL");
 else puts("GATEWAY_GUEST_PASS");
 reboot(RB_POWER_OFF);return 0;
}
