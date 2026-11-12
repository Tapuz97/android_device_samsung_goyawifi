"""Host regression tests of the changed source, without Android/device boots."""
from pathlib import Path
import json, subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
tree = Path('/root/t110-build/lineage20')
out = Path('/root/t110-build/offline-v24-tests')
out.mkdir(exist_ok=True)
evidence = project/'evidence/offline-v24'
evidence.mkdir(exist_ok=True)

def run(name, source):
    cpp = out/(name+'.cpp'); cpp.write_text(source)
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-g',str(cpp),'-o',str(out/name)],check=True)
    result = subprocess.run([str(out/name)],check=True,capture_output=True,text=True)
    (evidence/(name+'.log')).write_text(result.stdout+result.stderr)
    print(result.stdout.strip())

s = (tree/'frameworks/base/services/core/jni/gnss/Gnss.cpp').read_text()
helper = s[s.index('template <typename Interface>'):s.index('GnssLocationAidl createGnssLocation')]
constructor = s[s.index('GnssHal::GnssHal()'):s.index('jboolean GnssHal::isSupported()')]
prefix = r'''
#include <cassert>
#include <memory>
#include <cstdio>
#include <cstring>
template<class T> using sp = std::shared_ptr<T>;
#define ALOGI(...) ((void)0)
#define ALOGD(...) ((void)0)
static bool declaredOnly=true, managerAvailable=true, transportOk=true;
static int declared=0, available=0, tries=0, waits=0, lookups=0;
static int aidlChecks=0, aidlWaits=0, aidlVersion=0;
namespace base { bool GetBoolProperty(const char*,bool) { return declaredOnly; } }
namespace hidl::manager::V1_0 {
struct IServiceManager { enum class Transport { EMPTY, HWBINDER }; };
}
using Transport=hidl::manager::V1_0::IServiceManager::Transport;
struct Reply {
 Transport value; bool isOk() const { return transportOk; }
 bool operator==(Transport other) const { return value==other; }
};
struct Manager {
 Reply getTransport(const char* desc,const char*) {
  ++lookups; return {(declared & (1 << (*desc-'0'))) ? Transport::HWBINDER : Transport::EMPTY};
 }
};
namespace hardware {
sp<Manager> defaultServiceManager() { return managerAvailable ? std::make_shared<Manager>() : nullptr; }
}
struct Root {};
template<int N,class Parent> struct Version : Parent {
 static constexpr char descriptor[2]={char('0'+N),0};
 static sp<Version> getService() { ++waits; return result(); }
 static sp<Version> tryGetService() { ++tries; return result(); }
 static sp<Version> result() { return available & (1<<N) ? std::make_shared<Version>() : nullptr; }
};
using IGnss_V1_0=Version<0,Root>;
using IGnss_V1_1=Version<1,IGnss_V1_0>;
using IGnss_V2_0=Version<2,IGnss_V1_1>;
using IGnss_V2_1=Version<3,IGnss_V2_0>;
struct IGnssAidl { int getInterfaceVersion() { return aidlVersion; } };
template<class T> sp<T> checkVintfService() { ++aidlChecks; return aidlVersion ? std::make_shared<T>() : nullptr; }
template<class T> sp<T> waitForVintfService() { ++aidlWaits; return aidlVersion ? std::make_shared<T>() : nullptr; }
struct GnssHal {
 sp<IGnss_V1_0> gnssHal=nullptr;
 sp<IGnss_V1_1> gnssHal_V1_1=nullptr;
 sp<IGnss_V2_0> gnssHal_V2_0=nullptr;
 sp<IGnss_V2_1> gnssHal_V2_1=nullptr;
 sp<IGnssAidl> gnssHalAidl=nullptr;
 GnssHal();
};
void reset() {
 declaredOnly=true; managerAvailable=transportOk=true;
 declared=available=tries=waits=lookups=aidlChecks=aidlWaits=aidlVersion=0;
}
'''
tests = r'''
int main() {
 reset(); { GnssHal g; assert(!g.gnssHal && !g.gnssHalAidl); }
 assert(lookups==4 && tries==0 && waits==0 && aidlChecks==1 && aidlWaits==0);
 for(int v=0;v<4;++v) {
  reset(); declared=available=1<<v;
  GnssHal g; assert(g.gnssHal); assert(tries==1 && waits==0 && aidlWaits==0);
 }
 reset(); declared=15; { GnssHal g; assert(!g.gnssHal); }
 assert(tries==4 && waits==0); // declared but not ready never waits
 reset(); available=15; { GnssHal g; assert(!g.gnssHal); }
 assert(tries==0); // undeclared provider is not probed
 reset(); managerAvailable=false; { GnssHal g; assert(!g.gnssHal); } assert(tries==0);
 reset(); transportOk=false; declared=available=15;
 { GnssHal g; assert(!g.gnssHal); } assert(tries==0);
 reset(); aidlVersion=2; { GnssHal g; assert(g.gnssHalAidl); }
 assert(lookups==0 && aidlChecks==1 && aidlWaits==0);
 reset(); aidlVersion=1; declared=available=1;
 { GnssHal g; assert(g.gnssHalAidl && g.gnssHal); }
 reset(); declaredOnly=false; { GnssHal g; assert(!g.gnssHal); }
 assert(waits==4 && tries==0 && lookups==0 && aidlWaits==1);
 puts("PASS: actual GNSS constructor/helper, absent/not-ready/transport-error/version fallback and unchanged normal-device path (host API doubles)");
}
'''
run('gnss-lookup',prefix+helper+constructor+tests)

s = (tree/'system/memory/lmkd/lmkd.cpp').read_text()
start=s.index('    // Linux 3.4 does not inherit')
end=s.index('    ALOGI("lmkd data connection established");',start)
snippet=s[start:end].replace('return;', 'return false;')
prefix=r'''
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <cassert>
#define ALOGE(...) ((void)0)
struct { int sock; } data_sock[1];
bool configure(int fd) {
 const int free_dscock_idx=0; data_sock[0].sock=fd;
'''
suffix=r'''
 return true;
}
bool receive(int fd) {
 char data=0, control[CMSG_SPACE(sizeof(ucred))];
 iovec iov{&data,1}; msghdr msg{};
 msg.msg_iov=&iov; msg.msg_iovlen=1;
 msg.msg_control=control; msg.msg_controllen=sizeof(control);
 assert(recvmsg(fd,&msg,0)==1 && data=='X');
 for(auto* c=CMSG_FIRSTHDR(&msg);c;c=CMSG_NXTHDR(&msg,c)) {
  if(c->cmsg_level==SOL_SOCKET && c->cmsg_type==SCM_CREDENTIALS) {
   assert(c->cmsg_len>=CMSG_LEN(sizeof(ucred)));
   auto cred=reinterpret_cast<ucred*>(CMSG_DATA(c));
   assert(cred->pid==getpid() && cred->uid==getuid() && cred->gid==getgid());
   return true;
  }
 }
 return false;
}
int main() {
 for(int i=0;i<20;++i) {
  int listener=socket(AF_UNIX,SOCK_SEQPACKET,0); assert(listener>=0);
  sockaddr_un addr{}; addr.sun_family=AF_UNIX;
  snprintf(addr.sun_path+1,sizeof(addr.sun_path)-1,"t110-credentials-%d-%d",getpid(),i);
  int enabled=1, disabled=0;
  assert(setsockopt(listener,SOL_SOCKET,SO_PASSCRED,&enabled,sizeof(enabled))==0);
  assert(bind(listener,reinterpret_cast<sockaddr*>(&addr),sizeof(addr))==0);
  assert(listen(listener,1)==0);
  int client=socket(AF_UNIX,SOCK_SEQPACKET,0); assert(client>=0);
  assert(connect(client,reinterpret_cast<sockaddr*>(&addr),sizeof(addr))==0);
  int accepted=accept(listener,nullptr,nullptr); assert(accepted>=0);
  // Reproduce the old kernel's missing flag, even on a modern host kernel.
  assert(setsockopt(accepted,SOL_SOCKET,SO_PASSCRED,&disabled,sizeof(disabled))==0);
  assert(send(client,"X",1,0)==1); assert(!receive(accepted));
  assert(configure(accepted));
  for(int n=0;n<10;++n) { assert(send(client,"X",1,0)==1); assert(receive(accepted)); }
  close(accepted); close(client);
  // Also cover the first packet already queued when the server accepts.
  client=socket(AF_UNIX,SOCK_SEQPACKET,0); assert(client>=0);
  assert(connect(client,reinterpret_cast<sockaddr*>(&addr),sizeof(addr))==0);
  assert(send(client,"X",1,0)==1);
  accepted=accept(listener,nullptr,nullptr); assert(accepted>=0);
  assert(setsockopt(accepted,SOL_SOCKET,SO_PASSCRED,&disabled,sizeof(disabled))==0);
  assert(configure(accepted) && receive(accepted));
  close(accepted); close(client); close(listener);
 }
 assert(!configure(-1) && data_sock[0].sock==-1);
 puts("PASS: actual lmkd accepted-socket fix, 20 reproduced missing-credential failures, 200 verified subsequent packets and 20 queued-before-accept packets; setup failure rejects socket");
}
'''
run('lmkd-passcred',prefix+snippet+suffix)
(evidence/'regressions.json').write_text(json.dumps(dict(status='PASS',
 scope=['GNSS changed source with host service API doubles',
        'LMKD changed source with real Linux AF_UNIX seqpacket sockets; missing inherited flag simulated'],
 android_boots=0,tablet_access=False),indent=2)+'\n')
