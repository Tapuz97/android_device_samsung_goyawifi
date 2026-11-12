"""Read the actual init writes, labels and errors before any live policy change."""
from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
commands={
 'v41-reclaim-controls':'cat /proc/sys/vm/swappiness /proc/sys/vm/page-cluster; ls -lZ /proc/sys/vm/swappiness /proc/sys/vm/page-cluster; grep -n swappiness /system/etc/init/hw/init.rc /init.rc /init.mrvl.rc; cat /proc/sys/vm/min_free_kbytes; cat /proc/sys/vm/extra_free_kbytes; cat /proc/meminfo; grep -e pswp -e pgscan -e pgsteal /proc/vmstat',
 'v41-reclaim-init-log':'logcat -d -b all -t 10000',
 'v41-reclaim-kernel-log':'dmesg',
}
for name,cmd in commands.items():
    r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=45)
    text=(r.stdout+r.stderr).decode(errors='replace').replace('\r','');(e/(name+'.txt')).write_text(text,encoding='utf-8')
    if name=='v41-reclaim-controls':print(text[:2400])
    elif name=='v41-reclaim-init-log':print('\n'.join(line for line in text.splitlines() if 'swappiness' in line or 'page-cluster' in line)[-3000:])
