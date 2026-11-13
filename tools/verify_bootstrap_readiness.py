from pathlib import Path
import subprocess,json
base=Path('/root/t110-lineage14');src=(base/'android/device/samsung/goyawifi/bootstrap/stage.c').read_text();fn=src[src.index('static void block('):src.index('static void load_policy(')]
header=r'''
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <setjmp.h>
#include <assert.h>
static jmp_buf env;
static int mode,calls,waits,nodes,failure;
static __attribute__((noreturn)) void failed(const char *p){(void)p;failure=errno;longjmp(env,1);}
static FILE *mock_fopen(const char *p,const char *m){
 (void)p;(void)m;++calls;
 if(mode==2 || (mode==1 && calls<=3)){errno=ENOENT;return NULL;}
 if(mode==3){errno=EACCES;return NULL;}
 static char good[]="179:16\n",bad[]="bad\n";
 return fmemopen(mode==4?bad:good,mode==4?sizeof(bad):sizeof(good),"r");
}
static int mock_usleep(unsigned n){assert(n==100000);++waits;return 0;}
static int mock_mknod(const char *p,mode_t m,dev_t d){(void)p;assert(m==(S_IFBLK|0600));assert(major(d)==179 && minor(d)==16);++nodes;return 0;}
#define fopen mock_fopen
#define usleep mock_usleep
#define mknod mock_mknod
'''
footer=r'''
#undef fopen
#undef usleep
#undef mknod
int main(void){
 for(mode=0;mode<5;++mode){calls=waits=nodes=failure=0;
  if(!setjmp(env))block("mmcblk0p16","/dev/block/mmcblk0p16");
  if(mode==0)assert(calls==1&&waits==0&&nodes==1&&!failure);
  if(mode==1)assert(calls==4&&waits==3&&nodes==1&&!failure);
  if(mode==2)assert(calls==100&&waits==100&&nodes==0&&failure==ETIMEDOUT);
  if(mode==3)assert(calls==1&&waits==0&&nodes==0&&failure==EACCES);
  if(mode==4)assert(calls==1&&waits==0&&nodes==0&&failure==EINVAL);
 }
 return 0;
}
'''
p=base/'records/bootstrap-readiness-test.c';p.write_text(header+fn+footer)
subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p),'-o',str(p.with_suffix(''))],check=True)
subprocess.run([str(p.with_suffix(''))],check=True)
report={'status':'PASS','scope':'Actual bootstrap block-readiness helper with delayed/missing/malformed/sysfs-access fault injection; host sanitizer test, not hardware qualification','cases':['immediately ready','ready after three absent probes','bounded ten-second timeout','immediate permission-error failure','invalid device-number failure']}
(base/'records/bootstrap-readiness-test.json').write_text(json.dumps(report,indent=2)+'\n')
print('All five readiness/error-path fault-injection cases passed under ASan/UBSan.')
