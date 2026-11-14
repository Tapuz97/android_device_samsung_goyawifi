from pathlib import Path
import subprocess,json,hashlib
root=Path('/root/t110-android13-audit')
project=root/'platform/hardware/interfaces'
file=project/'graphics/composer/2.1/default/T110Framebuffer.cpp'
s=file.read_text()
anchor='''    d->blanked = !enable;
    ALOGI("T110 framebuffer power: %s", enable ? "on" : "off");'''
replacement='''    d->blanked = !enable;
    if (enable) {
        // Suspend may reset the controller's scanned page. Do not select the
        // next back page using pre-suspend yoffset; refresh the kernel state.
        fb_var_screeninfo current{};
        fb_fix_screeninfo fixed{};
        if (ioctl(d->fd, FBIOGET_VSCREENINFO, &current) < 0 ||
                ioctl(d->fd, FBIOGET_FSCREENINFO, &fixed) < 0) {
            return -errno;
        }
        // The mapping and cached rotation buffer were sized at open. Reject
        // a changed layout rather than copying through obsolete dimensions.
        if (!t110::validFramebuffer(fixed, current) ||
                fixed.line_length != d->fixed.line_length ||
                fixed.smem_len != d->fixed.smem_len ||
                fixed.smem_start != d->fixed.smem_start ||
                current.yoffset % current.yres ||
                uint64_t(current.yoffset) + current.yres > current.yres_virtual ||
                current.xoffset != 0) {
            return -EINVAL;
        }
        d->mode = current;
    }
    ALOGI("T110 framebuffer power: %s", enable ? "on" : "off");'''
if replacement not in s:
    assert s.count(anchor)==1
    s=s.replace(anchor,replacement);file.write_text(s)
audit=root/'device/development/android13-audit-20261114'
patch=subprocess.check_output(['git','-C',str(project),'diff','--binary','HEAD'])
(audit/'patches/0002-composer-refresh-scanout-after-unblank.patch').write_bytes(patch)
start=s.index('int enableScreen(');end=s.index('\nint closeDevice(',start)
function=s[start:end]
inc=project/'graphics/composer/2.1/default'
test=r'''#include <cassert>
#include <cerrno>
#include <mutex>
#include <cstdio>
#include "T110Scanout.h"
struct framebuffer_device_t { int placeholder; };
struct Device {
 framebuffer_device_t fb{};int fd=7;bool blanked=false;std::mutex mutex;
 fb_var_screeninfo mode{};fb_fix_screeninfo fixed{};
};
fb_var_screeninfo kernelMode;fb_fix_screeninfo kernelFixed;
unsigned long failRequest=0;int calls=0;
int ioctl(int fd,unsigned long request,int level){assert(fd==7&&request==FBIOBLANK);++calls;if(failRequest==request){errno=EIO;return -1;}assert(level==FB_BLANK_UNBLANK||level==FB_BLANK_POWERDOWN);return 0;}
int ioctl(int fd,unsigned long request,fb_var_screeninfo* out){assert(fd==7&&request==FBIOGET_VSCREENINFO);++calls;if(failRequest==request){errno=EIO;return -1;}*out=kernelMode;return 0;}
int ioctl(int fd,unsigned long request,fb_fix_screeninfo* out){assert(fd==7&&request==FBIOGET_FSCREENINFO);++calls;if(failRequest==request){errno=EIO;return -1;}*out=kernelFixed;return 0;}
#define ALOGE(...) ((void)0)
#define ALOGI(...) ((void)0)
'''+function+r'''
void reset(Device& d){
 calls=0;failRequest=0;d.blanked=true;
 kernelMode={};kernelFixed={};
 kernelMode.xres=1024;kernelMode.yres=600;kernelMode.xres_virtual=1024;kernelMode.yres_virtual=1200;kernelMode.bits_per_pixel=32;
 kernelMode.red.length=kernelMode.green.length=kernelMode.blue.length=kernelMode.transp.length=8;
 kernelMode.red.offset=16;kernelMode.green.offset=8;kernelMode.blue.offset=0;kernelMode.transp.offset=24;
 kernelFixed.line_length=4096;kernelFixed.smem_len=4096*1200;kernelFixed.ypanstep=1;kernelFixed.visual=FB_VISUAL_TRUECOLOR;
 d.mode=kernelMode;d.mode.yoffset=600;d.fixed=kernelFixed;
 assert(t110::validFramebuffer(kernelFixed,kernelMode));
}
int main(){
 Device d;reset(d);assert(enableScreen(&d.fb,1)==0&&!d.blanked&&d.mode.yoffset==0&&calls==3);
 reset(d);kernelMode.yoffset=600;assert(enableScreen(&d.fb,1)==0&&d.mode.yoffset==600);
 reset(d);assert(enableScreen(&d.fb,0)==0&&d.blanked&&calls==1);
 reset(d);assert(enableScreen(&d.fb,3)==-EINVAL&&calls==0);
 reset(d);failRequest=FBIOBLANK;assert(enableScreen(&d.fb,1)==-EIO&&d.blanked&&d.mode.yoffset==600);
 reset(d);failRequest=FBIOGET_VSCREENINFO;assert(enableScreen(&d.fb,1)==-EIO&&!d.blanked&&d.mode.yoffset==600);
 reset(d);kernelFixed.line_length+=64;kernelFixed.smem_len+=64*1200;assert(enableScreen(&d.fb,1)==-EINVAL&&d.mode.yoffset==600);
 reset(d);kernelMode.yoffset=1;assert(enableScreen(&d.fb,1)==-EINVAL&&d.mode.yoffset==600);
 reset(d);kernelMode.xoffset=1;assert(enableScreen(&d.fb,1)==-EINVAL);
 puts("PASS: actual unblank callback refreshes reset/retained page; validates power/errors/mapping/offsets");
}
'''
p=audit/'tests/framebuffer_resume_test.cpp';p.write_text(test)
binary=root/'framebuffer_resume_test'
subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(inc),str(p),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
subprocess.run(['git','-C',str(project),'diff','--check'],check=True)
(audit/'resume-verification.json').write_text(json.dumps(dict(status='HOST_CALLBACK_REGRESSION_PASS_NOT_HARDWARE_SUSPEND_TEST',cases=9,patch_sha256=hashlib.sha256(patch).hexdigest(),flashed=False),indent=2)+'\n')
