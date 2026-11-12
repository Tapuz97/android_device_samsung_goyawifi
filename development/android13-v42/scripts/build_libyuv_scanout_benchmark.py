"""Compile a scanout benchmark against the ROM's Android ABI."""
from pathlib import Path
import argparse,shlex,subprocess
parser=argparse.ArgumentParser()
parser.add_argument('--neon',action='store_true')
options=parser.parse_args()
t=Path('/root/t110-build/lineage20');b=t.parent
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
if options.neon:
    e=p/'evidence/offline-v41';name='scanout-neon-bench'
    benchmark=p/'scripts/bench_t110_scanout_neon.cpp'
    includes=['-I'+str(p/'work')]
    libraries=[]
else:
    e=p/'evidence/offline-v39';name='libyuv-scanout-benchmark'
    benchmark=p/'scripts/benchmark_libyuv_scanout.cpp'
    includes=['-Iexternal/libyuv/files/include']
    libraries=['yuv']
log=(b/'logs/system-image-20261106T173909Z.log').read_text()
line=next(x for x in log.splitlines() if x.startswith('PWD=/proc/self/cwd ') and 'gl/GLESRenderEngine.cpp' in x)
args=shlex.split(line)[1:]
for flag in ['-o','-MF']:
    i=args.index(flag);del args[i:i+2]
args=[x for x in args if x not in ['-MD','-MMD','-DNDEBUG']]
src='frameworks/native/libs/renderengine/gl/GLESRenderEngine.cpp'
obj=b/(name+'.o')
cmd=[str(benchmark) if x==src else x for x in args]+['-UNDEBUG',*includes,'-o',str(obj)]
subprocess.run(cmd,cwd=t,check=True)
out=b/'out-system';arch='android_arm_armv7-a-neon_cortex-a9';crt=out/'soong/.intermediates/bionic/libc'
begin=crt/'crtbegin_dynamic'/arch/'crtbegin_dynamic.o';end=next((crt/'crtend_android'/arch).rglob('crtend.o'))
builtins=t/'prebuilts/clang/host/linux-x86/clang-r450784d/lib64/clang/14.0.6/lib/linux/libclang_rt.builtins-arm-android.a'
lib=out/'target/product/t110_bringup/system/lib'
cmd=[args[0],'-target','armv7a-linux-androideabi','-fuse-ld=lld','-nostdlib','-pie','-Wl,--dynamic-linker,/system/bin/linker',str(begin),str(obj),'-L'+str(lib),'-L'+str(lib.parent/'apex/com.android.runtime/lib/bionic'),'-Wl,--no-as-needed',*['-l'+x for x in libraries+['c++','c','m','dl','log']],str(builtins),str(end),'-o',str(e/name)]
subprocess.run(cmd,cwd=t,check=True)
print(e/name)
