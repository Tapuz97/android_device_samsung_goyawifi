"""Exercise actual changed projection and power control code without a device boot."""
from pathlib import Path
import json
import subprocess

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
tree = Path('/root/t110-build/lineage20')
e = p/'evidence/offline-v29'
scratch = Path('/root/t110-build/test-v29-host')
scratch.mkdir(exist_ok=True)

def function(text, signature):
    start = text.index(signature)
    brace = text.index('{', start)
    depth = 1
    end = brace+1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

native = tree/'frameworks/native'
renderer = (native/'libs/renderengine/gl/GLESRenderEngine.cpp').read_text()
projection = renderer[renderer.index('    mat4 projectionMatrix ='):renderer.index('    Mesh mesh =',renderer.index('    mat4 projectionMatrix ='))]
projection = projection.replace('ui::Transform(display.orientation).asMatrix4()', 'rotation').replace('mState.projectionMatrix','base')
code = '''#include <math/mat4.h>
#include <cassert>
#include <cmath>
#include <cstdio>
using namespace android;
mat4 compose(const mat4& rotation, const mat4& base, bool legacyWindow) {
''' + projection + '''    return projectionMatrix;
}
void close(float a, float b) { assert(std::abs(a-b)<0.0001f); }
int main() {
  for (auto size: {vec2(600,1024),vec2(1024,600)}) {
    for (int q=0;q<4;++q) {
      const float c[] = {1,0,-1,0}, s[] = {0,1,0,-1};
      mat4 r(vec4(c[q],s[q],0,0),vec4(-s[q],c[q],0,0),vec4(0,0,1,0),vec4(0,0,0,1));
      mat4 base = mat4::ortho(7,7+size.x,11,11+size.y,0,1);
      for (int ix=0;ix<2;++ix) for (int iy=0;iy<2;++iy) {
        vec4 point(7+ix*size.x,11+iy*size.y,0,1);
        float x=ix?1:-1, y=iy?1:-1;
        float rx=x,ry=y;
        for(int n=0;n<q;++n) {float old=rx;rx=-ry;ry=old;}
        auto window = compose(r,base,true)*point;
        auto fbo = compose(r,base,false)*point;
        close(window.x,rx); close(window.y,-ry);
        close(fbo.x,rx); close(fbo.y,ry);
      }
    }
  }
  puts("PROJECTION_ALL_ROTATIONS_PASS");
}
'''
(scratch/'projection.cpp').write_text(code)

adapter = (tree/'hardware/interfaces/graphics/composer/2.1/utils/hwc2onfbadapter/HWC2OnFbAdapter.cpp').read_text()
fb = (tree/'hardware/interfaces/graphics/composer/2.1/default/T110Framebuffer.cpp').read_text()
power = function(adapter, 'int32_t HWC2OnFbAdapter::setPowerMode(')
enable = function(fb, 'int enableScreen(')
code = '''#include <linux/fb.h>
#include <cassert>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <mutex>
#define ALOGE(...) ((void)0)
#define ALOGI(...) ((void)0)
struct framebuffer_device_t {int (*enableScreen)(framebuffer_device_t*,int)=nullptr;};
struct Device {framebuffer_device_t fb; int fd=7; std::mutex mutex; bool blanked=false;};
int ioctlCalls=0,ioctlLevel=-1,ioctlResult=0;
int fakeIoctl(int fd,unsigned long cmd,int level) {
  assert(fd==7 && cmd==FBIOBLANK); ++ioctlCalls; ioctlLevel=level;
  errno=EIO;return ioctlResult;
}
#define ioctl fakeIoctl
''' + enable + '''
enum {HWC2_ERROR_NONE=0,HWC2_ERROR_BAD_PARAMETER=4,HWC2_ERROR_UNSUPPORTED=8};
enum {HWC2_POWER_MODE_OFF=0,HWC2_POWER_MODE_DOZE=1,HWC2_POWER_MODE_ON=2,HWC2_POWER_MODE_DOZE_SUSPEND=3};
struct HWC2OnFbAdapter {framebuffer_device_t* mFbDevice;int32_t setPowerMode(int32_t mode);};
''' + power + '''
int main() {
  Device device;device.fb.enableScreen=enableScreen;
  HWC2OnFbAdapter a{&device.fb};
  assert(a.setPowerMode(HWC2_POWER_MODE_OFF)==0 && device.blanked && ioctlLevel==FB_BLANK_POWERDOWN);
  assert(a.setPowerMode(HWC2_POWER_MODE_ON)==0 && !device.blanked && ioctlLevel==FB_BLANK_UNBLANK);
  int calls=ioctlCalls;
  assert(a.setPowerMode(HWC2_POWER_MODE_DOZE)==HWC2_ERROR_UNSUPPORTED);
  assert(a.setPowerMode(HWC2_POWER_MODE_DOZE_SUSPEND)==HWC2_ERROR_UNSUPPORTED);
  assert(a.setPowerMode(999)==HWC2_ERROR_BAD_PARAMETER && ioctlCalls==calls);
  assert(enableScreen(&device.fb,7)==-EINVAL && ioctlCalls==calls);
  ioctlResult=-1;
  assert(a.setPowerMode(HWC2_POWER_MODE_OFF)==HWC2_ERROR_UNSUPPORTED && !device.blanked);
  ioctlResult=0;
  assert(a.setPowerMode(HWC2_POWER_MODE_OFF)==0 && device.blanked);
  ioctlResult=-1;
  assert(a.setPowerMode(HWC2_POWER_MODE_ON)==HWC2_ERROR_UNSUPPORTED && device.blanked);
  device.fb.enableScreen=nullptr;calls=ioctlCalls;
  assert(a.setPowerMode(HWC2_POWER_MODE_ON)==0 && ioctlCalls==calls);
  puts("FRAMEBUFFER_POWER_ERROR_AND_MODE_CONTRACT_PASS");
}
'''
(scratch/'power.cpp').write_text(code)

for name in ['projection','power']:
    command = ['g++','-std=c++17','-O1','-g','-fsanitize=address,undefined',
               '-fno-sanitize-recover=all','-I'+str(native/'libs/math/include'),
               '-I'+str(tree/'system/core/libutils/include'),
               '-I'+str(tree/'system/core/libcutils/include'),
               '-I'+str(tree/'system/logging/liblog/include'),
               str(scratch/(name+'.cpp')),'-o',str(scratch/name)]
    result = subprocess.run(command,capture_output=True,text=True)
    (e/(name+'-compile.log')).write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stderr
    result = subprocess.run([str(scratch/name)],capture_output=True,text=True)
    (e/(name+'-regression.log')).write_text(result.stdout+result.stderr)
    assert result.returncode==0 and 'runtime error:' not in result.stderr and 'AddressSanitizer' not in result.stderr, result.stdout+result.stderr
    print(result.stdout.strip())

prop = (p/'work/device/samsung/t110_bringup/t110_system.mk').read_text()
assert 'ro.surface_flinger.primary_display_orientation=ORIENTATION_270' in prop
assert 'ro.sf.hwrotation=270' in (p/'stock/T110XXUANI7/system/build.prop').read_text()
for repo,patch in [('frameworks/native','0053-renderengine-t110-oriented-window-bridge.patch'),
                   ('hardware/interfaces','0054-composer-t110-scanout-and-display-power.patch')]:
    subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/patch)],cwd=tree/repo,check=True)
(e/'regressions.json').write_text(json.dumps(dict(status='PASS',
    projection='Production composition block with real Android mat4: both aspect ratios, all rotations/corners',
    framebuffer_power='Production methods: OFF/ON, invalid modes, missing hook, failed ioctl state retention',
    sanitizers='AddressSanitizer and UBSan, recovery disabled',
    hardware_or_android_boots=0, limits='Host contracts do not establish physical display or touch behavior'),indent=2)+'\n')
