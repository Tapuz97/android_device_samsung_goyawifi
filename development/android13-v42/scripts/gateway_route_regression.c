/* Guest-only regression for Android network tables. Never run on the tablet. */
#define main uid_regression_unused_main
#include "uid_routing_regression.c"
#undef main
static int gateway_route(unsigned table,const char *destination,unsigned prefix,const char *gateway,unsigned oif) {
 struct packet p={.h={.nlmsg_len=NLMSG_LENGTH(sizeof(struct rtmsg)),.nlmsg_type=RTM_NEWROUTE,
 .nlmsg_flags=NLM_F_REQUEST|NLM_F_ACK|NLM_F_CREATE|NLM_F_EXCL}};
 struct rtmsg *r=NLMSG_DATA(&p.h);unsigned addr;
 r->rtm_family=AF_INET;r->rtm_dst_len=prefix;r->rtm_protocol=RTPROT_STATIC;
 r->rtm_scope=gateway?RT_SCOPE_UNIVERSE:RT_SCOPE_LINK;r->rtm_type=RTN_UNICAST;
 u32attr(&p,RTA_TABLE,table);u32attr(&p,RTA_OIF,oif);
 if(prefix){inet_pton(AF_INET,destination,&addr);attr(&p,RTA_DST,&addr,4);}
 if(gateway){inet_pton(AF_INET,gateway,&addr);attr(&p,RTA_GATEWAY,&addr,4);}
 return transact(&p,NULL,NULL);
}
int main(void) {
 setbuf(stdout,NULL);mount("proc","/proc","proc",0,NULL);mount("sysfs","/sys","sysfs",0,NULL);
 nl=socket(AF_NETLINK,SOCK_RAW,NETLINK_ROUTE);struct timeval timeout={.tv_sec=3};
 setsockopt(nl,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));dummy_interface();
 address(AF_INET,"198.18.1.1",32,test_interface);
 int v=gateway_route(RT_TABLE_MAIN,"198.19.8.1",32,NULL,test_interface);check("main-host-gateway-route",v==0,v);
 v=gateway_route(103,NULL,0,"198.19.8.1",test_interface);check("legacy-main-fallback-still-works",v==0,v);
 v=rule(RTM_NEWRULE,AF_INET,50,0,0,0,0,0);check("policy-prohibit-for-nonpacket-lookup",v==0,v);
 v=gateway_route(101,"198.18.8.0",24,NULL,test_interface);check("android-table-connected-prefix",v==0,v);
 v=gateway_route(101,NULL,0,"198.18.8.1",test_interface);check("gateway-validated-in-explicit-network-table",v==0,v);
 v=gateway_route(102,NULL,0,"198.18.8.1",test_interface);check("other-table-cannot-borrow-private-prefix",v==-ENETUNREACH||v==-EACCES,v);
 v=gateway_route(101,"203.0.113.0",24,"198.18.9.1",test_interface);check("offlink-gateway-still-rejected",v==-ENETUNREACH||v==-EACCES,v);
 v=gateway_route(101,"203.0.114.0",24,"198.18.8.1",1);check("wrong-device-gateway-still-rejected",v==-ENETUNREACH||v==-EACCES,v);
 printf("GATEWAY_ROUTE_REGRESSION_%s tests=%d failed=%d\n",failed?"FAIL":"PASS",tests,failed);
 close(nl);return failed?1:0;
}
