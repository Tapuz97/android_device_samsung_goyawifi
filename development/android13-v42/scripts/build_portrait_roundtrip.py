from pathlib import Path
import shlex, subprocess
root=Path('/root/t110-build/lineage20')
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
e=p/'evidence/offline-v30'; e.mkdir(exist_ok=True)
s=Path('/root/t110-build/portrait-roundtrip');s.mkdir(exist_ok=True)
log=Path('/root/t110-build/logs/system-image-20261106T173909Z.log').read_text()
line=next(x for x in log.splitlines() if x.startswith('PWD=/proc/self/cwd ') and 'gl/GLESRenderEngine.cpp' in x)
args=shlex.split(line)[1:]
for flag in ['-o','-MF']:
    i=args.index(flag);del args[i:i+2]
args=[a for a in args if a not in ['-MD','-MMD']]
src='frameworks/native/libs/renderengine/gl/GLESRenderEngine.cpp'
objects=[]
window=(root/'frameworks/native/libs/renderengine/gl/T110EglWindow.cpp').read_text()
window=window.replace('#include <array>','#include <array>\n#include <cstdlib>\n#include <cstdio>')
window=window.replace('case NATIVE_WINDOW_TRANSFORM_HINT:', 'case NATIVE_WINDOW_TRANSFORM_HINT: *value = getenv("T110_PROBE_HINT") ? atoi(getenv("T110_PROBE_HINT")) : 0; printf("QUERY_HINT %d\\n", *value); return 0;')
(s/'T110EglWindowDiagnostic.cpp').write_text(window)
for name,file in [('probe',p/'scripts/t110_portrait_roundtrip.cpp'),('window',s/'T110EglWindowDiagnostic.cpp')]:
    obj=s/(name+'.o'); objects.append(str(obj))
    cmd=[str(file) if x==src else x for x in args]+['-Iframeworks/native/libs/renderengine/gl','-o',str(obj)]
    r=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
    (e/(name+'-compile.log')).write_text(r.stdout+r.stderr)
    assert r.returncode==0,r.stderr
out=Path('/root/t110-build/out-system')
crt=out/'soong/.intermediates/bionic/libc'
arch='android_arm_armv7-a-neon_cortex-a9'
begin=crt/'crtbegin_dynamic'/arch/'crtbegin_dynamic.o'
end=next((crt/'crtend_android'/arch).rglob('crtend.o'))
builtins=root/'prebuilts/clang/host/linux-x86/clang-r450784d/lib64/clang/14.0.6/lib/linux/libclang_rt.builtins-arm-android.a'
lib=out/'target/product/t110_bringup/system/lib'
cmd=[args[0],'-target','armv7a-linux-androideabi','-fuse-ld=lld','-nostdlib','-pie','-Wl,--dynamic-linker,/system/bin/linker',str(begin),*objects,'-L'+str(lib),'-L'+str(lib.parent/'apex/com.android.runtime/lib/bionic'),'-Wl,--no-as-needed',*['-l'+x for x in ['ui','utils','cutils','log','EGL','GLESv2','nativewindow','sync','c++','c','m','dl']],str(builtins),str(end),'-o',str(s/'t110_portrait_roundtrip')]
r=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
(e/'link.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
(e/'t110_portrait_roundtrip').write_bytes((s/'t110_portrait_roundtrip').read_bytes())
print('PORTRAIT_ROUNDTRIP_COMPILED')
