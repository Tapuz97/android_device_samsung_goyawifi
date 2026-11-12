"""Host source-contract checks. No Android, emulator or tablet boots."""
from pathlib import Path
import subprocess, json, hashlib
base=Path('/root/t110-build'); project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
e=project/'evidence/offline-v25'; work=base/'offline-v25-tests'; work.mkdir(exist_ok=True)
source=(base/'kernel-binder-secctx/drivers/staging/android/binder.c').read_text()
acquire=source[source.index('\tif (target_node && target_node->txn_security_ctx) {'):source.index('\n\ttrace_binder_transaction(reply, t, target_node);')]
copy=source[source.index('\tif (secctx) {\n\t\tsize_t ctx_offset'):source.index('\n\tt->buffer->allow_user_free = 0;')]
cleanup=source[source.index('err_binder_alloc_buf_failed:\n'):source.index('\n\tkfree(tcomplete);')]
assert 'extra_buffers_size - secctx_space' in source
sgline=next(line.strip() for line in source.splitlines() if 'sg_buf_end = sg_bufp +' in line)
assert 'if (cmd != BR_REPLY && !(t->flags & TF_ONE_WAY))' in source
assert '&tr.transaction_data' in source and '&trd->transaction_data' not in source
c=r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
typedef uint32_t u32; typedef uint64_t u64; typedef uint8_t u8;
typedef uint32_t binder_size_t; typedef uint32_t binder_uintptr_t;
#define ALIGN(x,a) (((x)+((a)-1)) & ~((a)-1))
#define BR_FAILED_REPLY 123
static int releases, mode;
static const char label[]="u:r:system_server:s0";
static int security_secid_to_secctx(u32 sid,char **p,u32 *sz) {
 assert(sid==42); if(mode==1) return -1;
 *sz=sizeof(label); *p=malloc(*sz); memcpy(*p,label,*sz);
 if(mode==2) (*p)[*sz-1]='x'; return 0;
}
static void security_release_secctx(char *p,u32 sz) {assert(p && sz);free(p);releases++;}
static void test(uint32_t original, uint32_t data, uint32_t offsets,int requested,int failure) {
 struct {u32 opener_sid;} proc_value={42}, *proc=&proc_value;
 struct {int txn_security_ctx;} node={requested}, *target_node=&node;
 struct {uint32_t data_size,offsets_size;} tr_value={data,offsets},*tr=&tr_value;
 struct {uintptr_t user_buffer_offset;} target_value={0x1000},*target_proc=&target_value;
 struct {void *data;} buffer={NULL};
 struct {typeof(buffer)*buffer; binder_uintptr_t security_ctx;} trans={&buffer,0}, *t=&trans;
 char *secctx=NULL; u32 secctx_sz=0; binder_size_t secctx_space=0,extra_buffers_size=original;
 int ret=0, return_error=0, prior=releases; mode=failure;
 ACQUIRE
 // Model allocator boundary only; the kernel allocator itself is ARM-compiled.
 uint64_t total=ALIGN((uint64_t)data,sizeof(void*))+ALIGN((uint64_t)offsets,sizeof(void*))+extra_buffers_size;
 if(total>4096 || failure==3) {return_error=BR_FAILED_REPLY;goto err_binder_alloc_buf_failed;}
 buffer.data=malloc(total+16); memset(buffer.data,0xa5,total+16);
 COPY
 u8 *sg_bufp=(u8*)buffer.data+ALIGN(data,sizeof(void*))+ALIGN(offsets,sizeof(void*));
 u8 *sg_buf_end;
 SGEND
 assert((size_t)(sg_buf_end-sg_bufp)==original);
 memset(sg_bufp,0x5a,original);
 if(requested) {
  size_t at=ALIGN(data,sizeof(void*))+ALIGN(offsets,sizeof(void*))+original;
  assert(!memcmp((char*)buffer.data+at,label,sizeof(label)));
  assert(t->security_ctx==(uint32_t)((uintptr_t)buffer.data+at+0x1000));
  for(size_t i=sizeof(label);i<secctx_space;i++) assert(((u8*)buffer.data)[at+i]==0);
  assert(releases==prior+1); assert(secctx==NULL);
 } else assert(!t->security_ctx && !secctx_space && releases==prior);
 for(int i=0;i<16;i++) assert(((u8*)buffer.data)[total+i]==0xa5);
 free(buffer.data); return;
 CLEANUP
 assert(return_error==BR_FAILED_REPLY);
 assert(releases==prior+((requested && failure!=1)?1:0));
}
int main(void){
 for(unsigned d=0;d<33;d++) for(unsigned o=0;o<17;o+=4) for(unsigned sg=0;sg<65;sg+=8){
  test(sg,d,o,1,0);test(sg,d,o,0,0);
 }
 test(0,0,0,1,1); test(0,0,0,1,2); test(0,0,0,1,3);
 test(UINT32_MAX-7,0,0,1,0); test(0,UINT32_MAX,0,1,0);
 puts("BINDER_SECCTX_HOST_CONTRACT_PASS");
}
'''.replace('ACQUIRE',acquire).replace('COPY',copy).replace('CLEANUP',cleanup).replace('SGEND',sgline)
(work/'secctx.c').write_text(c)
subprocess.run(['gcc','-std=gnu11','-g','-fsanitize=address,undefined',str(work/'secctx.c'),'-o',str(work/'secctx')],check=True)
r=subprocess.run([str(work/'secctx')],capture_output=True,text=True)
(e/'binder-host.log').write_text(r.stdout+r.stderr); assert r.returncode==0,(r.stdout,r.stderr)

# Use the unmodified production method body with lightweight API doubles.
java=(e/'AppOpsControllerImpl.java').read_text()
start=java.index('    private void fetchCurrentActiveOps() {'); end=java.index('\n    }',start)+6
method=java[start:end]
j=r'''
import java.util.*;
class AppOpsRegression {
 static class AppOpsManager {
  static int ATTRIBUTION_FLAGS_NONE=0,ATTRIBUTION_CHAIN_ID_NONE=-1;
  static class AttributedOpEntry {boolean running; AttributedOpEntry(boolean r){running=r;} boolean isRunning(){return running;}}
  static class OpEntry {Map<String,AttributedOpEntry> values=new HashMap<>(); Map<String,AttributedOpEntry> getAttributedOpEntries(){return values;} String getOpStr(){return "camera";}}
  static class PackageOps {List<OpEntry> values=new ArrayList<>(); List<OpEntry> getOps(){return values;} int getUid(){return 1000;} String getPackageName(){return "test";}}
  List<PackageOps> result; List<PackageOps> getPackagesForOps(int[] ops){return result;}
 }
 AppOpsManager mAppOps=new AppOpsManager(); static int[] OPS={1}; int calls;
 void onOpActiveChanged(String op,int uid,String pkg,String attr,boolean active,int flags,int chain){if(!active)throw new AssertionError();calls++;}
 METHOD
 public static void main(String[]args){
  AppOpsRegression t=new AppOpsRegression();
  t.fetchCurrentActiveOps(); if(t.calls!=0)throw new AssertionError();
  t.mAppOps.result=new ArrayList<>(); t.fetchCurrentActiveOps();
  AppOpsManager.PackageOps p=new AppOpsManager.PackageOps(); AppOpsManager.OpEntry op=new AppOpsManager.OpEntry();
  op.values.put("active",new AppOpsManager.AttributedOpEntry(true));op.values.put("inactive",new AppOpsManager.AttributedOpEntry(false));
  p.values.add(op);t.mAppOps.result.add(p);t.fetchCurrentActiveOps();if(t.calls!=1)throw new AssertionError();
  t.mAppOps.result=null;t.fetchCurrentActiveOps();if(t.calls!=1)throw new AssertionError();
  System.out.println("SYSTEMUI_APP_OPS_SOURCE_CONTRACT_PASS");
 }
}
'''.replace('METHOD',method)
(work/'AppOpsRegression.java').write_text(j)
jdk=base/'lineage20/prebuilts/jdk/jdk11/linux-x86/bin'
subprocess.run([str(jdk/'javac'),str(work/'AppOpsRegression.java')],check=True)
r=subprocess.run([str(jdk/'java'),'-cp',str(work),'AppOpsRegression'],capture_output=True,text=True)
(e/'systemui-host.log').write_text(r.stdout+r.stderr); assert r.returncode==0
# ABI checks compile the actual new public header in 32-bit Binder mode.
header=base/'kernel-binder-secctx/drivers/staging/android/uapi/binder.h'
abi='#include <linux/types.h>\n#include <sys/types.h>\n#define BINDER_IPC_32BIT\n#include "'+str(header)+'"\n_Static_assert(sizeof(struct binder_transaction_data)==40,"legacy size");\n_Static_assert(sizeof(struct binder_transaction_data_secctx)==44,"secctx size");\n_Static_assert(BR_TRANSACTION!=BR_TRANSACTION_SEC_CTX,"distinct command");\nint main(void){return 0;}\n'
(work/'abi.c').write_text(abi)
subprocess.run(['gcc',str(work/'abi.c'),'-o',str(work/'abi')],check=True)
subprocess.run([str(work/'abi')],check=True)
(e/'regressions.json').write_text(json.dumps(dict(status='PASS',
 scope=['Extracted Binder label allocation/copy/cleanup blocks with ASan/UBSan and API doubles',
        'Extracted SystemUI method: null, empty, mixed active/inactive operations',
        'Actual Binder 32-bit UAPI size and command compile checks'],
 android_boots=0,tablet_access=False,kernel_runtime_tested=False),indent=2)+'\n')
print('V25_OFFLINE_HOST_CONTRACTS_PASS')
