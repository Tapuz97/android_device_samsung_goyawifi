"""ARM Android component link against providers from our preserved Android13 image."""
from pathlib import Path
import subprocess,json,hashlib
r=Path('/root/t110-android13-audit');dest=r/'arm-checks';providers=dest/'android13-providers';providers.mkdir(exist_ok=True)
image=Path('/root/t110-lineage14/reference/android13-current-system.raw.img')
src=r/'device/development/android13-audit-20261114/implementation/audio'
report=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True);report.append(dict(command=cmd,exit=p.returncode,diagnostics=p.stdout+p.stderr));print(p.stdout+p.stderr,end='',flush=True)
 if p.returncode:(dest/'android-link-results.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(p.returncode)
for name,path in {'libc++.so':'/system/lib/libc++.so','libc.so':'/system/apex/com.android.runtime/lib/bionic/libc.so','libm.so':'/system/apex/com.android.runtime/lib/bionic/libm.so','libdl.so':'/system/apex/com.android.runtime/lib/bionic/libdl.so'}.items():
 target=providers/name
 run(['debugfs','-R','dump '+path+' '+str(target),str(image)])
 assert target.is_file() and target.stat().st_size>1000
base=Path('/root/t110-lineage14/android')
flags=['clang++','--target=armv7a-linux-androideabi','-std=c++17','-fno-exceptions','-fno-rtti','-fPIC','-Wall','-Wextra','-Werror','-I'+str(r/'arm-headers'),'-I'+str(src)]
for name in ('bionic/libc/include','bionic/libc/arch-arm/include','bionic/libc/kernel/uapi','bionic/libc/kernel/uapi/asm-arm','external/libcxx/include','external/libcxxabi/include'):
 flags+=['-isystem',str(base/name)]
for name in ('AudioAdapter','AudioModule','LegacyList'):
 run(flags+['-c',str(src/(name+'.cpp')),'-o',str(dest/(name+'-bionic.o'))])
gcc=next(Path('/root/t110-lineage14/toolchains/arm-linux-androideabi-4.6').glob('lib/gcc/arm-linux-androideabi/*/libgcc.a'))
so=dest/'audio.primary.t110.so'
run(['clang++','--target=armv7a-linux-androideabi','-fuse-ld=lld','-shared','-nostdlib','-Wl,--no-undefined','-Wl,-soname,audio.primary.t110.so',str(dest/'AudioAdapter-bionic.o'),str(dest/'AudioModule-bionic.o'),'-L'+str(providers),'-lc++','-lc','-lm','-ldl',str(gcc),'-o',str(so)])
run(['readelf','-h',str(so)])
run(['readelf','-d',str(so)])
shim=dest/'libt110_audio_legacy_compat.so'
run(['clang++','--target=armv7a-linux-androideabi','-fuse-ld=lld','-shared','-nostdlib','-Wl,--no-undefined','-Wl,-soname,libt110_audio_legacy_compat.so',str(dest/'LegacyList-bionic.o'),'-L'+str(providers),'-lc',str(gcc),'-o',str(shim)])
shim_symbols=subprocess.check_output(['readelf','--dyn-syms','-W',str(shim)],text=True)
for name in ('list_init','list_add_tail','list_remove'):
 assert any('GLOBAL' in line and 'DEFAULT' in line and line.endswith(' '+name) and ' UND ' not in line for line in shim_symbols.splitlines()),name
symbols=subprocess.check_output(['readelf','--dyn-syms','-W',str(so)],text=True)
assert any('GLOBAL' in line and 'DEFAULT' in line and ' HMI' in line and ' UND ' not in line for line in symbols.splitlines())
report.append(dict(component_sha256=hashlib.sha256(so.read_bytes()).hexdigest(),shim_sha256=hashlib.sha256(shim.read_bytes()).hexdigest(),providers={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in providers.iterdir()},status='ARM_ANDROID_COMPONENT_LINK_PASS_NOT_FULL_PLATFORM_OR_VENDOR_LOAD_TEST',header_context='Pinned Android13 hardware/system headers; retained Nougat Bionic/libc++ build headers; linked against actual Android13 shared providers',flashed=False))
(dest/'android-link-results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: complete audio HAL module is ARM Android ELF, exports HMI, and links with no unresolved references against preserved Android13 providers.')
