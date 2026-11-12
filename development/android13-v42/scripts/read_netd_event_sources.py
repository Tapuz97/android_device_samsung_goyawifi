from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/netd-event';e.mkdir(exist_ok=True)
base='/root/t110-build/lineage20'
for name in ['system/netd/server/NetlinkHandler.cpp','system/core/libsysutils/src/NetlinkEvent.cpp','system/core/libsysutils/include/sysutils/NetlinkEvent.h']:
 r=subprocess.run(['wsl.exe','-d','T110Build','--','cat',base+'/'+name],capture_output=True,timeout=60);assert r.returncode==0
 (e/Path(name).name).write_bytes(r.stdout)
clang=base+'/prebuilts/clang/host/linux-x86/clang-r450784d/bin/llvm-addr2line'
binary='/root/t110-build/out-system/target/product/t110_bringup/symbols/system/bin/netd'
r=subprocess.run(['wsl.exe','-d','T110Build','--',clang,'-e',binary,'-C','-f','0x2755c'],capture_output=True,timeout=60)
(e/'crash-symbolized.txt').write_bytes(r.stdout+r.stderr);print(r.stdout.decode(errors='replace'))
