"""Read traces from the current boot without causing another ANR or reboot."""
from pathlib import Path
import os,re,subprocess,json
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s,timeout=40):
    r=subprocess.run(adb+['shell',s],capture_output=True,timeout=timeout,check=True);return r.stdout
boot=sh('cat /proc/sys/kernel/random/boot_id').decode().strip()
assert boot==json.loads((e/'installation.json').read_text())['boot_id']
for name in sh('ls /data/anr').decode().splitlines():
    if not re.fullmatch(r'anr_2026-11-10-19-41-\d\d-\d\d\d',name):continue
    data=sh('cat /data/anr/'+name,60);(e/name).write_bytes(data);print(name,len(data),flush=True)
for name,cmd in {
    'settled-memory.txt':'cat /proc/uptime; cat /proc/meminfo; cat /proc/swaps; cat /sys/block/zram0/disksize /sys/block/zram0/initstate; dumpsys meminfo --oom',
    'settled-runtime.txt':'pidof system_server; pidof com.android.systemui; pidof com.android.launcher3; dumpsys activity users; dumpsys window windows | grep mCurrentFocus; cat /proc/309/task/309/wchan',
}.items():
    data=sh(cmd,60);(e/name).write_bytes(data);print(name,len(data),flush=True)
