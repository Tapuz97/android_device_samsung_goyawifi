/* Isolated guest-only Linux3.4 routing regression. Never run as tablet init.
 * Routes/rules exist only in a QEMU guest with no network adapter or disks.
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <linux/fib_rules.h>
#include <linux/if_addr.h>
#include <linux/netlink.h>
#include <linux/reboot.h>
#include <linux/rtnetlink.h>
#include <net/if.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

enum { MODERN_FRA_UID_RANGE = 20, MODERN_RTA_UID = 25, TEST_UID = 12345 };
static int nl, tests, failed;
static unsigned test_interface;
static unsigned seq;
struct packet { struct nlmsghdr h; unsigned char body[768]; };

static void check(const char *name, int ok, int value) {
    ++tests;
    if (!ok) ++failed;
    printf("UID_TEST %s %s value=%d\n", name, ok ? "PASS" : "FAIL", value);
    fflush(stdout);
}
static void attr(struct packet *p, unsigned type, const void *data, size_t size) {
    size_t at = NLMSG_ALIGN(p->h.nlmsg_len);
    struct rtattr *a = (void *)((char *)p + at);
    if (at + RTA_SPACE(size) > sizeof(*p)) abort();
    a->rta_type = type; a->rta_len = RTA_LENGTH(size);
    memcpy(RTA_DATA(a), data, size);
    p->h.nlmsg_len = at + RTA_ALIGN(a->rta_len);
}
static void u32attr(struct packet *p, unsigned type, unsigned value) {
    attr(p, type, &value, sizeof(value));
}
static int transact(struct packet *p, void *reply, size_t *length) {
    char buffer[8192]; struct sockaddr_nl kernel = { .nl_family = AF_NETLINK };
    p->h.nlmsg_seq = ++seq;
    if (sendto(nl, p, p->h.nlmsg_len, 0, (void *)&kernel, sizeof(kernel)) < 0)
        return -errno;
    for (;;) {
        ssize_t n = recv(nl, buffer, sizeof(buffer), 0);
        if (n < 0) return -errno;
        struct nlmsghdr *h;
        for (h = (void *)buffer; NLMSG_OK(h, n); h = NLMSG_NEXT(h, n)) {
            if (h->nlmsg_seq != seq) continue;
            if (h->nlmsg_type == NLMSG_ERROR)
                return ((struct nlmsgerr *)NLMSG_DATA(h))->error;
            if (reply && length) {
                if (*length < h->nlmsg_len) return -EMSGSIZE;
                *length = h->nlmsg_len; memcpy(reply, h, *length); return 0;
            }
        }
    }
}
static void dummy_interface(void) {
    struct packet p={ .h={.nlmsg_len=NLMSG_LENGTH(sizeof(struct ifinfomsg)),
        .nlmsg_type=RTM_NEWLINK,.nlmsg_flags=NLM_F_REQUEST|NLM_F_ACK|NLM_F_CREATE|NLM_F_EXCL} };
    struct ifinfomsg *info=NLMSG_DATA(&p.h);info->ifi_family=AF_UNSPEC;
    info->ifi_flags=IFF_UP;info->ifi_change=IFF_UP;
    attr(&p,IFLA_IFNAME,"uiddummy0",10);
    size_t at=NLMSG_ALIGN(p.h.nlmsg_len);attr(&p,IFLA_LINKINFO,"",0);
    attr(&p,IFLA_INFO_KIND,"dummy",6);
    ((struct rtattr *)((char *)&p+at))->rta_len=p.h.nlmsg_len-at;
    int value=transact(&p,NULL,NULL);check("isolated-dummy-interface",value==0,value);
    test_interface=if_nametoindex("uiddummy0");check("dummy-index",test_interface>1,test_interface);
}
static void address(int family, const char *ip, unsigned prefix, unsigned index) {
    struct packet p = { .h = { .nlmsg_len = NLMSG_LENGTH(sizeof(struct ifaddrmsg)),
        .nlmsg_type = RTM_NEWADDR, .nlmsg_flags = NLM_F_REQUEST|NLM_F_ACK|NLM_F_CREATE|NLM_F_EXCL } };
    struct ifaddrmsg *a = NLMSG_DATA(&p.h); unsigned char bytes[16];
    a->ifa_family=family; a->ifa_prefixlen=prefix; a->ifa_flags=IFA_F_NODAD;
    a->ifa_scope=RT_SCOPE_UNIVERSE; a->ifa_index=index;
    inet_pton(family, ip, bytes);
    attr(&p, IFA_LOCAL, bytes, family==AF_INET?4:16);
    attr(&p, IFA_ADDRESS, bytes, family==AF_INET?4:16);
    int r=transact(&p,NULL,NULL); check(ip,r==0||r==-EEXIST,r);
}
static int rule(int action, int family, unsigned priority, int uid,
                unsigned start, unsigned end, int length, unsigned flags) {
    struct packet p = { .h = { .nlmsg_len = NLMSG_LENGTH(sizeof(struct fib_rule_hdr)),
        .nlmsg_type = action, .nlmsg_flags = NLM_F_REQUEST|NLM_F_ACK } };
    struct fib_rule_hdr *f=NLMSG_DATA(&p.h);
    if (action==RTM_NEWRULE) p.h.nlmsg_flags|=NLM_F_CREATE|NLM_F_EXCL;
    f->family=family; f->table=uid?100:0;
    f->action=uid?FR_ACT_TO_TBL:FR_ACT_PROHIBIT; f->flags=flags;
    u32attr(&p,FRA_PRIORITY,priority);
    if (uid) {
        unsigned range[3]={start,end,0};
        attr(&p,MODERN_FRA_UID_RANGE,range,length);
        attr(&p,FRA_IIFNAME,"lo",3);
    }
    return transact(&p,NULL,NULL);
}
static void route(int family, const char *ip, const char *source) {
    struct packet p={ .h={ .nlmsg_len=NLMSG_LENGTH(sizeof(struct rtmsg)),
        .nlmsg_type=RTM_NEWROUTE, .nlmsg_flags=NLM_F_REQUEST|NLM_F_ACK|NLM_F_CREATE|NLM_F_EXCL } };
    struct rtmsg *r=NLMSG_DATA(&p.h); unsigned char bytes[16]; int size=family==AF_INET?4:16;
    r->rtm_family=family;r->rtm_dst_len=size*8;r->rtm_table=100;
    r->rtm_protocol=RTPROT_STATIC;r->rtm_scope=RT_SCOPE_LINK;r->rtm_type=RTN_UNICAST;
    inet_pton(family,ip,bytes);attr(&p,RTA_DST,bytes,size);u32attr(&p,RTA_OIF,test_interface);
    if (source) {inet_pton(family,source,bytes);attr(&p,RTA_PREFSRC,bytes,size);}
    int value=transact(&p,NULL,NULL);check("test-route",value==0,value);
}
static int query(int family, unsigned uid) {
    struct packet p={ .h={ .nlmsg_len=NLMSG_LENGTH(sizeof(struct rtmsg)),
        .nlmsg_type=RTM_GETROUTE,.nlmsg_flags=NLM_F_REQUEST } };
    struct rtmsg *r=NLMSG_DATA(&p.h);unsigned char bytes[16],response[4096];size_t length=sizeof(response);
    int size=family==AF_INET?4:16;
    r->rtm_family=family;r->rtm_dst_len=size*8;
    inet_pton(family,family==AF_INET?"198.18.2.42":"2001:db8:2::42",bytes);
    attr(&p,RTA_DST,bytes,size);u32attr(&p,MODERN_RTA_UID,uid);
    int error=transact(&p,response,&length);
    if (error) return error;
    struct nlmsghdr *h=(void *)response;struct rtmsg *rt=NLMSG_DATA(h);
    int remaining=h->nlmsg_len-NLMSG_LENGTH(sizeof(*rt));
    for(struct rtattr *a=RTM_RTA(rt);RTA_OK(a,remaining);a=RTA_NEXT(a,remaining))
        if(a->rta_type==RTA_CACHEINFO && RTA_PAYLOAD(a)>=sizeof(struct rta_cacheinfo)) {
            struct rta_cacheinfo *cache=RTA_DATA(a);
            if(cache->rta_error) return (int)cache->rta_error;
        }
    return rt->rtm_type==RTN_UNREACHABLE ? -ENETUNREACH : 0;
}
static int connect_for_uid(int family, int type, unsigned process_uid, int socket_owner) {
    int pipefd[2]; if (pipe(pipefd)) return -errno;
    pid_t child=fork();
    if (child==0) {
        close(pipefd[0]);int fd=-1,value;gid_t inetgroup=3003;
        if (socket_owner>=0) {
            fd=socket(family,type|SOCK_NONBLOCK,0);
            if (fd<0 || fchown(fd,socket_owner,-1)) {value=-errno;goto done;}
            /* chmod must not change the socket's retained owner. */
            if (fchmod(fd,0600)) {value=-errno;goto done;}
        }
        if (setgroups(1,&inetgroup)||setgid(inetgroup)||setuid(process_uid)) {value=-errno;goto done;}
        if (fd<0) fd=socket(family,type|SOCK_NONBLOCK,0);
        if (fd<0) {value=-errno;goto done;}
        if (family==AF_INET) {
            struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(41000)};
            inet_pton(family,"198.18.2.42",&a.sin_addr);
            value=connect(fd,(void *)&a,sizeof(a));
        } else {
            struct sockaddr_in6 a={.sin6_family=AF_INET6,.sin6_port=htons(41000)};
            inet_pton(family,"2001:db8:2::42",&a.sin6_addr);
            value=connect(fd,(void *)&a,sizeof(a));
        }
        if (value<0)value=-errno;
done:  if (fd>=0)close(fd);ssize_t written=write(pipefd[1],&value,sizeof(value));_exit(written==sizeof(value)?0:2);
    }
    close(pipefd[1]);int value=-EIO,status;
    if (child<0)value=-errno;
    else {ssize_t n=read(pipefd[0],&value,sizeof(value));if(n!=sizeof(value))value=-EIO;waitpid(child,&status,0);}
    close(pipefd[0]);return value;
}
static void protocol_tests(int family) {
    char name[96];int v;const char *version=family==AF_INET?"ipv4":"ipv6";
    for (int type=SOCK_DGRAM;type>=SOCK_STREAM;--type) {
        const char *protocol=type==SOCK_DGRAM?"udp":"tcp";
        for(int pass=0;pass<4;++pass) {
            int allowed=!(pass&1);unsigned uid=TEST_UID+!allowed;
            v=connect_for_uid(family,type,uid,-1);
            snprintf(name,sizeof(name),"%s-%s-%s-cache-cycle%d",version,protocol,allowed?"allow":"deny",pass);
            check(name,allowed?(v==0||(type==SOCK_STREAM&&v==-EINPROGRESS)):(v==-EACCES||v==-ENETUNREACH),v);
        }
    }
    v=connect_for_uid(family,SOCK_DGRAM,TEST_UID+1,TEST_UID);
    snprintf(name,sizeof(name),"%s-fchown-uses-socket-owner-not-caller",version);check(name,v==0,v);
    v=connect_for_uid(family,SOCK_DGRAM,TEST_UID,TEST_UID+1);
    snprintf(name,sizeof(name),"%s-fchown-denies-excluded-owner",version);check(name,v==-EACCES||v==-ENETUNREACH,v);
}
static void dump_rule(int family) {
    struct packet p={ .h={ .nlmsg_len=NLMSG_LENGTH(sizeof(struct fib_rule_hdr)),
        .nlmsg_type=RTM_GETRULE,.nlmsg_flags=NLM_F_REQUEST|NLM_F_DUMP } };
    ((struct fib_rule_hdr *)NLMSG_DATA(&p.h))->family=family;
    p.h.nlmsg_seq=++seq;struct sockaddr_nl kernel={.nl_family=AF_NETLINK};
    int found=0,done=0;
    sendto(nl,&p,p.h.nlmsg_len,0,(void *)&kernel,sizeof(kernel));
    while(!done) {
        char b[8192];ssize_t n=recv(nl,b,sizeof(b),0);if(n<0)break;
        for(struct nlmsghdr *h=(void *)b;NLMSG_OK(h,n);h=NLMSG_NEXT(h,n)) {
            if(h->nlmsg_seq!=seq)continue;
            if(h->nlmsg_type==NLMSG_DONE||h->nlmsg_type==NLMSG_ERROR){done=1;break;}
            struct fib_rule_hdr *f=NLMSG_DATA(h);int len=h->nlmsg_len-NLMSG_LENGTH(sizeof(*f));
            for(struct rtattr *a=(void *)((char *)f+NLMSG_ALIGN(sizeof(*f)));RTA_OK(a,len);a=RTA_NEXT(a,len))
                if(a->rta_type==MODERN_FRA_UID_RANGE&&RTA_PAYLOAD(a)==8){
                    unsigned *u=RTA_DATA(a);if(u[0]==TEST_UID&&u[1]==TEST_UID)++found;
                }
        }
    }
    check(family==AF_INET?"ipv4-dump-modern-range":"ipv6-dump-modern-range",found==1,found);
}
int main(void) {
    setbuf(stdout,NULL);mount("proc","/proc","proc",0,NULL);mount("sysfs","/sys","sysfs",0,NULL);
    printf("UID_ROUTING_GUEST_START\n");
    int fd=socket(AF_INET,SOCK_DGRAM,0);struct ifreq ifr={0};strcpy(ifr.ifr_name,"lo");ifr.ifr_flags=IFF_UP;
    check("loopback-up",ioctl(fd,SIOCSIFFLAGS,&ifr)==0,errno);close(fd);
    nl=socket(AF_NETLINK,SOCK_RAW,NETLINK_ROUTE);
    struct timeval timeout={.tv_sec=3};setsockopt(nl,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
    dummy_interface();
    address(AF_INET,"127.0.0.1",8,1);address(AF_INET,"198.18.1.1",32,test_interface);
    address(AF_INET6,"::1",128,1);address(AF_INET6,"2001:db8:1::1",128,test_interface);
    route(AF_INET,"198.18.2.42","198.18.1.1");route(AF_INET6,"2001:db8:2::42",NULL);
    for(int family=AF_INET;family<=AF_INET6;family+=(AF_INET6-AF_INET)) {
        int v=rule(RTM_NEWRULE,family,100,1,TEST_UID,TEST_UID,8,0);check("add-uid-rule",v==0,v);
        v=rule(RTM_NEWRULE,family,200,0,0,0,0,0);check("add-prohibit-fallback",v==0,v);
        v=rule(RTM_NEWRULE,family,99,1,100,99,8,0);check("reject-reversed-range",v==-EINVAL,v);
        v=rule(RTM_NEWRULE,family,99,1,0xffffffff,0xffffffff,8,0);check("reject-invalid-uid",v==-EINVAL,v);
        v=rule(RTM_NEWRULE,family,99,1,TEST_UID,TEST_UID,4,0);check("reject-short-range",v<0,v);
        v=rule(RTM_NEWRULE,family,99,1,TEST_UID,TEST_UID,12,0);check("reject-overlong-range",v==-EINVAL,v);
        dump_rule(family);
        v=query(family,TEST_UID);check("modern-route-query-allow",v==0,v);
        v=query(family,TEST_UID+1);check("modern-route-query-deny",v==-EACCES||v==-ENETUNREACH,v);
        protocol_tests(family);
        v=rule(RTM_DELRULE,family,100,1,TEST_UID+1,TEST_UID+1,8,0);check("delete-wrong-range-keeps-rule",v==-ESRCH||v==-ENOENT,v);
        v=query(family,TEST_UID);check("correct-range-survives-wrong-delete",v==0,v);
        v=rule(RTM_DELRULE,family,100,1,TEST_UID,TEST_UID,8,0);check("delete-correct-range",v==0,v);
        v=rule(RTM_NEWRULE,family,100,1,TEST_UID,TEST_UID,8,FIB_RULE_INVERT);check("add-inverted-range",v==0,v);
        v=query(family,TEST_UID);check("inverted-range-deny",v==-EACCES||v==-ENETUNREACH,v);
        v=query(family,TEST_UID+1);check("inverted-range-allow",v==0,v);
        v=rule(RTM_DELRULE,family,100,1,TEST_UID,TEST_UID,8,FIB_RULE_INVERT);check("delete-inverted-range",v==0,v);
        v=rule(RTM_NEWRULE,family,100,1,0,0x7fffffff,8,0);check("add-android-all-users-range",v==0,v);
        v=query(family,0);check("range-includes-root",v==0,v);
        v=query(family,0x7fffffff);check("range-includes-upper-bound",v==0,v);
        v=query(family,0x80000000);check("range-excludes-next-uid",v==-EACCES||v==-ENETUNREACH,v);
        v=rule(RTM_DELRULE,family,100,1,0,0x7fffffff,8,0);check("delete-all-users-range",v==0,v);
    }
    printf("UID_ROUTING_REGRESSION_%s tests=%d failed=%d\n",failed?"FAIL":"PASS",tests,failed);
    sync();reboot(LINUX_REBOOT_CMD_POWER_OFF);return failed?1:0;
}
