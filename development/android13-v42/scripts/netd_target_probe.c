/* Query actual xtables target/match revisions. No packet/rule changes. */
#include <errno.h>
#include <netinet/in.h>
#include <linux/netfilter/x_tables.h>
#include <linux/netfilter_ipv4/ip_tables.h>
#include <linux/netfilter_ipv6/ip6_tables.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
int main(void) {
    static const struct { const char *name; unsigned revision; int target; } cases[]={
        {"MARK",2,1},{"mark",1,0},{"CONNMARK",1,1},{"connmark",1,0},{"IDLETIMER",1,1}};
    int failed=0;
    for(int family=AF_INET;family<=AF_INET6;family+=AF_INET6-AF_INET) {
        int fd=socket(family,SOCK_RAW,IPPROTO_RAW);
        if(fd<0){perror("socket");return 2;}
        for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
            struct xt_get_revision revision={0};socklen_t size=sizeof(revision);
            snprintf(revision.name,sizeof(revision.name),"%s",cases[i].name);revision.revision=cases[i].revision;
            int option=family==AF_INET?(cases[i].target?IPT_SO_GET_REVISION_TARGET:IPT_SO_GET_REVISION_MATCH)
                                     :(cases[i].target?IP6T_SO_GET_REVISION_TARGET:IP6T_SO_GET_REVISION_MATCH);
            int result=getsockopt(fd,family==AF_INET?SOL_IP:SOL_IPV6,option,&revision,&size);
            if(result)++failed;
            printf("NETD_TARGET family=%d name=%s revision=%u %s errno=%d\n",family,cases[i].name,cases[i].revision,result?"FAIL":"PASS",result?errno:0);
        }
        close(fd);
    }
    printf("NETD_TARGET_PROBE_%s checks=10 failed=%d\n",failed?"FAIL":"PASS",failed);return failed?1:0;
}
