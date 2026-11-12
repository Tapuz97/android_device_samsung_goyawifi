"""Read cgroup reclaim policy and swap counters; do not change memory settings."""
from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
commands={
 'reclaim-policy':'cat /proc/swaps; cat /proc/1/cgroup; cat /proc/317/cgroup; cat /proc/sys/vm/swappiness; cat /sys/block/zram0/mm_stat; cat /sys/block/zram0/stat; cat /sys/block/zram0/disksize; grep cgroup /proc/mounts; cat /dev/memcg/memory.swappiness /dev/memcg/apps/memory.swappiness /sys/fs/cgroup/memory/memory.swappiness',
 'reclaim-group-files':'find /dev/memcg -maxdepth 4 -name memory.swappiness -print -exec cat {} ;',
 'reclaim-kernel':'dmesg',
 'current-anr-list':'ls -lt /data/anr',
}
for name,cmd in commands.items():
    r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=45)
    text=(r.stdout+r.stderr).decode(errors='replace').replace('\r','');(e/(name+'.txt')).write_text(text,encoding='utf-8')
    if name not in ['reclaim-kernel','current-anr-list']:print(name+'\n'+text[:5000],flush=True)
