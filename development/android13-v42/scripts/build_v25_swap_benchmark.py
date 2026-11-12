from pathlib import Path
import shlex,subprocess
t=Path('/root/t110-build/lineage20');b=t.parent
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
e=p/'evidence/offline-v35';s=b/'swap-benchmark';s.mkdir(exist_ok=True)
log=(b/'logs/system-image-20261106T173909Z.log').read_text()
line=next(x for x in log.splitlines() if x.startswith('PWD=/proc/self/cwd ') and 'gl/GLESRenderEngine.cpp' in x)
args=shlex.split(line)[1:]
for flag in ['-o','-MF']:
    i=args.index(flag);del args[i:i+2]
args=[x for x in args if x not in ['-MD','-MMD']]
source='frameworks/native/libs/renderengine/gl/GLESRenderEngine.cpp'
current=t/'frameworks/native/libs/renderengine/gl/T110EglWindow.cpp'
original=s/'T110EglWindow-original.cpp'
r=subprocess.run(['patch','--reverse','--output',str(original),str(current)],input=(e/'0065-renderengine-t110-reuse-idle-swap-spares.patch.incremental').read_text(),capture_output=True,text=True)
assert r.returncode==0,r.stdout+r.stderr
objects={}
for name,file in [('probe',p/'scripts/t110_swap_benchmark.cpp'),('original',original),('reuse',current)]:
    obj=s/(name+'.o');objects[name]=obj
    command=[str(file) if x==source else x for x in args]+['-Iframeworks/native/libs/renderengine/gl','-o',str(obj)]
    r=subprocess.run(command,cwd=t,capture_output=True,text=True)
    (e/(name+'-benchmark-compile.log')).write_text(r.stdout+r.stderr)
    assert r.returncode==0,r.stderr
out=b/'out-system';arch='android_arm_armv7-a-neon_cortex-a9'
crt=out/'soong/.intermediates/bionic/libc'
begin=crt/'crtbegin_dynamic'/arch/'crtbegin_dynamic.o';end=next((crt/'crtend_android'/arch).rglob('crtend.o'))
builtins=t/'prebuilts/clang/host/linux-x86/clang-r450784d/lib64/clang/14.0.6/lib/linux/libclang_rt.builtins-arm-android.a'
lib=out/'target/product/t110_bringup/system/lib'
for variant in ('original','reuse'):
    exe=e/('swap-benchmark-'+variant)
    command=[args[0],'-target','armv7a-linux-androideabi','-fuse-ld=lld','-nostdlib','-pie','-Wl,--dynamic-linker,/system/bin/linker',str(begin),str(objects['probe']),str(objects[variant]),'-L'+str(lib),'-L'+str(lib.parent/'apex/com.android.runtime/lib/bionic'),'-Wl,--no-as-needed',*['-l'+x for x in ['ui','utils','cutils','log','EGL','GLESv2','nativewindow','sync','c++','c','m','dl']],str(builtins),str(end),'-o',str(exe)]
    r=subprocess.run(command,cwd=t,capture_output=True,text=True);assert r.returncode==0,r.stderr
print('SWAP_BENCHMARKS_COMPILED')
