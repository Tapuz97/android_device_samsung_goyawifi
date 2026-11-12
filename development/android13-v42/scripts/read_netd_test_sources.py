from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/netd-event'
base='/root/t110-build/lineage20/system/netd'
for name in ['server/Android.bp','server/NetlinkHandler.h','server/NetlinkManager.h']:
 r=subprocess.run(['wsl.exe','-d','T110Build','--','cat',base+'/'+name],capture_output=True,timeout=60)
 if r.returncode==0:(e/Path(name).name).write_bytes(r.stdout)
r=subprocess.run(['wsl.exe','-d','T110Build','--','find',base,'-name','*Netlink*Test*'],capture_output=True,timeout=60)
print(r.stdout.decode(errors='replace'))
