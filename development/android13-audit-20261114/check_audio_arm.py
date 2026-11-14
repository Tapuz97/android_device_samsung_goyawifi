from pathlib import Path
import subprocess,json
r=Path('/root/t110-android13-audit')
src=r/'device/development/android13-audit-20261114/implementation/audio'
dest=r/'arm-checks';dest.mkdir(exist_ok=True)
inc=['-I'+str(r/'arm-headers'),'-I'+str(src)]
common=['-std=c++17','-Wall','-Wextra','-Werror']
arm=['clang++','--target=armv7a-linux-gnueabihf','--sysroot=/usr/arm-linux-gnueabihf','--gcc-toolchain=/usr',*common,*inc]
records=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 records.append(dict(command=cmd,exit=p.returncode,diagnostics=p.stdout+p.stderr))
 print(p.stdout+p.stderr,end='',flush=True)
 if p.returncode:
  (dest/'audio-results.json').write_text(json.dumps(records,indent=2)+'\n')
  raise SystemExit(p.returncode)
for name in ('AudioAdapter.cpp','AudioModule.cpp','AudioAdapterTest.cpp'):
 run(arm+['-c',str(src/name),'-o',str(dest/(name+'.o'))])
run(['arm-linux-gnueabihf-g++',str(dest/'AudioAdapter.cpp.o'),str(dest/'AudioAdapterTest.cpp.o'),'-o',str(dest/'audio-test-arm')])
run(['qemu-arm','-L','/usr/arm-linux-gnueabihf',str(dest/'audio-test-arm')])
run(['clang++',*common,*inc,'-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie',str(src/'AudioAdapter.cpp'),str(src/'AudioAdapterTest.cpp'),'-o',str(dest/'audio-test-host')])
run([str(dest/'audio-test-host')])
run(['file',str(dest/'AudioAdapter.cpp.o'),str(dest/'AudioModule.cpp.o'),str(dest/'audio-test-arm')])
(dest/'audio-results.json').write_text(json.dumps(records,indent=2)+'\n')
print('PASS: Android13 audio headers, ARM32 ABI assertions, cross objects, ARM emulation and host sanitizers.')
