"""Exercise the real lights adapter against a temporary file, not panel hardware."""
from pathlib import Path
import subprocess,tempfile,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');t=Path('/root/t110-build/lineage20')
e=p/'evidence/remote-fixes-20261110/source-tests'
source='''#include <assert.h>
static const char *test_path;
#define T110_BACKLIGHT_PATH test_path
#include "'''+str(p/'work/device/samsung/t110_bringup/lights/lights.c')+'''"
static int value(void){FILE*f=fopen(test_path,"r");assert(f);int n=-1;assert(fscanf(f,"%d",&n)==1);fclose(f);return n;}
int main(int argc,char**argv){assert(argc==2);test_path=argv[1];
struct hw_device_t *d=NULL;assert(open_light(&HAL_MODULE_INFO_SYM,LIGHT_ID_BACKLIGHT,&d)==0);assert(d);
struct light_device_t*l=(struct light_device_t*)d;
unsigned levels[]={0,1,40,220,255};for(unsigned i=0;i<5;i++){
struct light_state_t s={.color=0xff000000u|levels[i]*0x010101u};assert(l->set_light(l,&s)==0);assert(value()==(int)levels[i]);}
struct light_state_t low={.color=0,.brightnessMode=BRIGHTNESS_MODE_LOW_PERSISTENCE};
assert(l->set_light(l,&low)==-ENOSYS);assert(value()==255);
struct hw_device_t *led=NULL;assert(open_light(&HAL_MODULE_INFO_SYM,LIGHT_ID_NOTIFICATIONS,&led)==-EINVAL&&led==NULL);
assert(l->set_light(l,NULL)==-EINVAL);assert(unlink(test_path)==0);
struct light_state_t s={.color=0xff404040};assert(l->set_light(l,&s)==-ENOENT);
assert(d->close(d)==0);puts("PASS:backlight 0/1/40/220/255, unsupported modes/types, missing node and cleanup");}
'''
f=e/'lights-backend-test.c';f.write_text(source)
incs=[t/'hardware/libhardware/include',t/'system/core/libcutils/include',t/'system/core/libsystem/include',t/'system/core/libutils/include',t/'system/core/libcutils/include_vndk']
subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror',*['-I'+str(x) for x in incs],str(f),'-o',str(e/'lights-backend-test')],check=True)
with tempfile.TemporaryDirectory(prefix='t110-light-test-') as d:
    temp=Path(d)/'brightness';temp.write_text('195\n')
    text=subprocess.check_output([str(e/'lights-backend-test'),str(temp)],text=True)
(e.parent/'lights-source-test.json').write_text(json.dumps({'result':text.strip(),'scope':'Real adapter compiled with real Android headers; fake sysfs file. Android service/real panel remain unqualified.'},indent=2)+'\n')
print(text)
