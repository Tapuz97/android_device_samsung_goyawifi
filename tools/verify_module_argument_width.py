from pathlib import Path
import subprocess,json
base=Path('/root/t110-lineage14/records');p=base/'module-argument-width-test.c'
p.write_text(r'''
#include <stdarg.h>
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
static const char *seen;
__attribute__((noinline)) static void capture(long nr,...){
 va_list ap;va_start(ap,nr);(void)va_arg(ap,void*);assert(va_arg(ap,unsigned long)==2674971UL);seen=va_arg(ap,const char*);va_end(ap);
}
int main(void){
 _Static_assert(sizeof(size_t)==4,"32-bit syscall argument width");
 int64_t stat_size=2674971;char payload=0;const char *params="";
 capture(128,&payload,stat_size,params);assert(seen==0);
 size_t size=(size_t)stat_size;capture(128,&payload,size,params);assert(seen==params);
 return 0;
}
''')
subprocess.run(['gcc','-m32','-O2','-Wall','-Wextra','-Werror',str(p),'-o',str(p.with_suffix(''))],check=True)
subprocess.run([str(p.with_suffix(''))],check=True)
(base/'module-argument-width-test.json').write_text(json.dumps({'status':'PASS','scope':'32-bit vararg ABI regression; no module loading','old_64bit_length_parameters_seen_as_null':True,'corrected_size_t_retains_actual_parameters_pointer':True},indent=2)+'\n')
print('32-bit argument packing reproduced the NULL parameters slot; bounded size_t fixes it.')
