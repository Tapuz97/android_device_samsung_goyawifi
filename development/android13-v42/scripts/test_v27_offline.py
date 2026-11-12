"""Host regressions against production methods; no Android boot or device access."""
from pathlib import Path
import json
import re
import subprocess

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t = Path('/root/t110-build/lineage20')
e = p/'evidence/offline-v27'
b = Path('/root/t110-build/test-v27-host')
b.mkdir(exist_ok=True)
(e/'regressions.json').write_text(json.dumps(dict(status='RUNNING',android_boots=0,tablet_access=False))+'\n')

def body(path, signature):
    text = path.read_text()
    start = text.index(signature)
    opening = text.index('{',start)
    depth = 1
    pos = opening+1
    while depth:
        depth += (text[pos]=='{') - (text[pos]=='}')
        pos += 1
    return text[start:pos]

def run(name, args):
    result = subprocess.run(list(map(str,args)),cwd=b,capture_output=True,text=True)
    (e/(name+'.log')).write_text(result.stdout+result.stderr)
    sanitizer_failure = re.search(r'runtime error:|ERROR: (?:Address|Leak)Sanitizer',result.stdout+result.stderr)
    if result.returncode or sanitizer_failure:
        (e/'regressions.json').write_text(json.dumps(dict(status='FAILED',check=name,android_boots=0,tablet_access=False))+'\n')
        print((result.stdout+result.stderr)[-6000:],flush=True)
        result.check_returncode()
        raise AssertionError('Sanitizer reported a runtime fault')
    print(name+' PASS',flush=True)

method = body(t/'packages/modules/Connectivity/service-t/src/com/android/server/net/NetworkStatsService.java',
              '    private void registerGlobalAlert()')
java = '''import java.util.function.Consumer;
public class GlobalAlertTest {
 static class ServiceSpecificException extends RuntimeException {}
 static class RemoteException extends Exception {}
 static class Log { static void w(String t, String m) { warnings++; } }
 static int warnings;
 static final String TAG="test";
 long mGlobalAlertBytes=123;
 int callbacks;
 class Netd { int mode, calls; void bandwidthSetGlobalAlert(long n) throws RemoteException {
  calls++; if(n!=123) throw new AssertionError();
  if(mode==1) throw new ServiceSpecificException();
  if(mode==2) throw new IllegalStateException();
  if(mode==3) throw new RemoteException();
  if(mode==4) throw new NullPointerException("unexpected programming error");
 } }
 Netd mNetd=new Netd();
 class Provider { void onSetAlert(long n) { if(n!=123) throw new AssertionError(); callbacks++; } }
 class Callback { Provider mProvider=new Provider(); }
 void invokeForAllStatsProviderCallbacks(Consumer<Callback> consumer) { consumer.accept(new Callback()); }
 METHOD
 public static void main(String[] args) {
  GlobalAlertTest test=new GlobalAlertTest();
  for(int mode=0;mode<4;mode++) { test.mNetd.mode=mode; test.registerGlobalAlert(); }
  if(test.callbacks!=4 || test.mNetd.calls!=4 || warnings!=2) throw new AssertionError();
  test.mNetd.mode=0; test.registerGlobalAlert();
  if(test.callbacks!=5 || test.mNetd.calls!=5) throw new AssertionError();
  test.mNetd.mode=4;
  try { test.registerGlobalAlert(); throw new AssertionError(); } catch(NullPointerException expected) {}
  System.out.println("Global alert: success, service failure, state failure, reconnect, callback retention PASS");
 }
}
'''.replace('METHOD',method)
(b/'GlobalAlertTest.java').write_text(java)
jdk=t/'prebuilts/jdk/jdk11/linux-x86/bin'
run('global-alert-javac',[jdk/'javac',b/'GlobalAlertTest.java'])
run('global-alert-java',[jdk/'java','-ea','-cp',b,'GlobalAlertTest'])

method=body(t/'system/netd/server/BandwidthController.cpp','int BandwidthController::setGlobalAlert(')
cpp='''#include <cassert>
#include <cstdint>
#include <cerrno>
#define ALOGE(...) ((void)0)
const char ALERT_GLOBAL_NAME[]="globalAlert";
enum IptOp { IptOpInsert };
int insert_result=0, update_result=0, inserts=0, updates=0;
int updateQuota(const char*,int64_t) { ++updates; return update_result; }
int runIptablesAlertCmd(IptOp,const char*,int64_t) { ++inserts; return insert_result; }
struct BandwidthController { int64_t mGlobalAlertBytes=0; int setGlobalAlert(int64_t); };
METHOD
int main() {
 BandwidthController c;
 assert(c.setGlobalAlert(0)==-ERANGE && inserts==0 && updates==0);
 insert_result=-1;
 assert(c.setGlobalAlert(123)==-EREMOTEIO && c.mGlobalAlertBytes==0 && inserts==1);
 insert_result=0;
 assert(c.setGlobalAlert(123)==0 && c.mGlobalAlertBytes==123 && inserts==2 && updates==0);
 update_result=-ENOENT;
 assert(c.setGlobalAlert(456)==-ENOENT && c.mGlobalAlertBytes==123 && updates==1);
 update_result=0;
 assert(c.setGlobalAlert(456)==0 && c.mGlobalAlertBytes==456 && updates==2);
}
'''.replace('METHOD',method)
(b/'netd-alert.cpp').write_text(cpp)
run('netd-alert-compile',['g++','-std=c++17','-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g',b/'netd-alert.cpp','-o',b/'netd-alert'])
run('netd-alert-regression',[b/'netd-alert'])

# Compile the pinned libfuse source for a host-only protocol exchange. The
# transport is a socketpair, never /dev/fuse or a mount. The callback is the
# actual MediaProvider init body with a minimal userdata/logging fixture.
lib=t/'external/libfuse'
sources=['buffer.c','cuse_lowlevel.c','fuse.c','fuse_log.c','fuse_loop.c',
         'fuse_loop_mt.c','fuse_lowlevel.c','fuse_opt.c','fuse_signals.c','helper.c',
         'modules/subdir.c','modules/iconv.c','mount.c','mount_util.c']
flags=['-D_GNU_SOURCE','-D_FILE_OFFSET_BITS=64','-DFUSE_USE_VERSION=35','-DFUSERMOUNT_DIR="/system/bin"',
       '-I'+str(lib/'include'),'-I'+str(lib/'lib'),'-pthread','-g','-O1',
       '-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-include','signal.h']
objects=[]
for src in sources:
    obj=b/(src.replace('/','_')+'.o')
    run('fuse-compile-'+src.replace('/','_'),['gcc',*flags,'-c',lib/'lib'/src,'-o',obj])
    objects.append(obj)
init=body(t/'packages/providers/MediaProvider/jni/FuseDaemon.cpp','static void pf_init(')
assert re.search(r'#define FUSE_KERNEL_MINOR_VERSION\s+18', (e/'kernel-fuse.h').read_text())
kernel=(e/'kernel-fuse-inode.c').read_text()
assert '"fd=%u"' in kernel and '"rootmode=%o"' in kernel and '"allow_other"' in kernel
flags_expr=re.search(r'arg->flags \|= (.*?);',kernel[kernel.index('void fuse_send_init'):],re.S).group(1)
harness=r'''#include <atomic>
#include <cassert>
#include <cstring>
#include <iostream>
#include <sys/socket.h>
#include <unistd.h>
#include "fuse_lowlevel.h"
#include "fuse_i.h"
#include "fuse_kernel.h"
#define LOG(level) std::cerr
const size_t MAX_READ_SIZE=256*4096;
struct fuse { bool passthrough; std::atomic<bool>* active; };
INIT_BODY
static void test(unsigned minor, unsigned flags, bool passthrough) {
 int fd[2]; assert(socketpair(AF_UNIX,SOCK_SEQPACKET,0,fd)==0);
 std::atomic<bool> active(false); struct fuse context={passthrough,&active};
 char name[]="fuse-protocol-test", option[]="-omax_read=1048576";
 char* argv[]={name,option}; struct fuse_args args=FUSE_ARGS_INIT(2,argv);
 struct fuse_lowlevel_ops ops={}; ops.init=pf_init;
 struct fuse_session* session=fuse_session_new(&args,&ops,sizeof(ops),&context);
 assert(session); session->fd=fd[0];
 struct { struct fuse_in_header h; struct fuse_init_in init; } request={};
 // The old kernel's fuse_init_in is 16 bytes; avoid silently supplying new fields.
 request.h.len=sizeof(request.h)+16; request.h.opcode=FUSE_INIT;
 request.h.unique=1; request.h.uid=getuid(); request.h.gid=getgid();
 request.init.major=7; request.init.minor=minor; request.init.max_readahead=131072;
 request.init.flags=flags;
 struct fuse_buf buffer={}; buffer.size=request.h.len; buffer.mem=&request;
 fuse_session_process_buf(session,&buffer);
 unsigned char reply[256]; ssize_t n=read(fd[1],reply,sizeof(reply));
 assert(n==sizeof(fuse_out_header)+FUSE_COMPAT_22_INIT_OUT_SIZE);
 auto* header=reinterpret_cast<fuse_out_header*>(reply);
 auto* out=reinterpret_cast<fuse_init_out*>(reply+sizeof(*header));
 assert(header->error==0 && header->unique==1 && session->error==0);
 assert(active.load() && out->major==7 && out->minor>=minor);
 assert(!(out->flags & (FUSE_DO_READDIRPLUS|FUSE_READDIRPLUS_AUTO|FUSE_WRITEBACK_CACHE|FUSE_PASSTHROUGH)));
 assert(!context.passthrough); // absent kernel capability is never assumed
 close(fd[1]); fuse_session_destroy(session); fuse_opt_free_args(&args);
}
int main() {
 unsigned flags=KERNEL_FLAGS;
 test(18,flags,false); test(18,flags,true); test(18,0,false);
 std::cout<<"Pinned libfuse + MediaProvider callback, kernel protocol7.18 exchange PASS\n";
}
'''.replace('INIT_BODY',init).replace('KERNEL_FLAGS',flags_expr)
(b/'fuse-protocol.cpp').write_text(harness)
run('fuse-protocol-link',['g++','-std=c++17',*flags,b/'fuse-protocol.cpp',*objects,'-ldl','-lrt','-o',b/'fuse-protocol'])
run('fuse-protocol-regression',[b/'fuse-protocol'])

for repo,name in [('packages/modules/Connectivity','0049-networkstats-global-alert-service-errors.patch'),
                  ('system/netd','0050-netd-global-alert-commit-on-success.patch'),
                  ('external/libfuse','0051-libfuse-unsigned-passthrough-mask.patch')]:
    run(name+'-reverse-check',['git','-C',t/repo,'apply','--reverse','--check',p/'patches'/name])
report=dict(status='PASS',android_boots=0,tablet_access=False,
    tests=['Extracted NetworkStats registration: remote/kernel errors, retries and callbacks',
           'Extracted netd quota state: failed insertion/update and successful retry under ASan/UBSan',
           'Pinned libfuse with production MediaProvider init callback: protocol7.18 over socketpair under ASan/UBSan'],
    limits=['Host API fixtures and protocol exchange, not Android or tablet runtime',
            'Full storage mount/access and Wi-Fi service startup still require later hardware validation'])
(e/'regressions.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
