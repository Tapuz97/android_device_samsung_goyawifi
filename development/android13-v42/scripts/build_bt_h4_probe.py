"""Compile a small ARM diagnostic with the current Android toolchain and CRT."""
from pathlib import Path
import hashlib,json,os,shlex,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');root=Path('/root/t110-build/lineage20');out=Path('/root/t110-build/out-system');e=p/'evidence/hardware-bt-sd'
log=Path('/root/t110-build/logs/system-image-20261106T173909Z.log')
with log.open() as stream:line=next(x for x in stream if x.startswith('PWD=/proc/self/cwd ') and 'gl/GLESRenderEngine.cpp' in x)
args=shlex.split(line)[1:]
for flag in ['-o','-MF']:
 i=args.index(flag);del args[i:i+2]
args=[x for x in args if x not in ['-MD','-MMD']]
src=p/'scripts/bt_h4_probe.cpp';work=Path('/root/t110-build/bt-h4-probe');work.mkdir(exist_ok=True);obj=work/'probe.o'
cmd=[str(src) if x=='frameworks/native/libs/renderengine/gl/GLESRenderEngine.cpp' else x for x in args]+['-o',str(obj)]
r=subprocess.run(cmd,cwd=root,capture_output=True);(e/'h4-compile.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,r.stderr.decode(errors='replace')
crt=out/'soong/.intermediates/bionic/libc';arch='android_arm_armv7-a-neon_cortex-a9'
begin=crt/'crtbegin_dynamic'/arch/'crtbegin_dynamic.o';end=next((crt/'crtend_android'/arch).rglob('crtend.o'))
lib=out/'target/product/t110_bringup/system/lib';builtins=root/'prebuilts/clang/host/linux-x86/clang-r450784d/lib64/clang/14.0.6/lib/linux/libclang_rt.builtins-arm-android.a'
target=work/'t110_bt_h4_probe'
cmd=[args[0],'-target','armv7a-linux-androideabi','-fuse-ld=lld','-nostdlib','-pie','-Wl,--dynamic-linker,/system/bin/linker',str(begin),str(obj),'-L'+str(lib),'-L'+str(lib.parent/'apex/com.android.runtime/lib/bionic'),'-Wl,--no-as-needed','-lc++','-lc','-lm','-ldl',str(builtins),str(end),'-o',str(target)]
r=subprocess.run(cmd,cwd=root,capture_output=True);(e/'h4-link.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,r.stderr.decode(errors='replace')
(e/target.name).write_bytes(target.read_bytes());record=dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),status='COMPILED_NOT_RUN')
(e/'h4-build.json').write_text(json.dumps(record,indent=2)+'\n');print('H4_PROBE_COMPILED',record['binary_sha256'])
