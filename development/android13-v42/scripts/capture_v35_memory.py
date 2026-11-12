from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/input-dispatch'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
commands={
 'memory':'cat /proc/meminfo; cat /proc/swaps; cat /proc/loadavg; cat /sys/block/zram0/mm_stat; cat /sys/module/lowmemorykiller/parameters/adj /sys/module/lowmemorykiller/parameters/minfree; getprop ro.config.low_ram; getprop ro.lmk.use_psi; getprop init.svc.lmkd',
 'process-memory':'ps -A -o PID,PPID,RSS,NAME',
 'memory-logs':"logcat -d -b all -t 30000 | grep -Ei 'lmkd|lowmemory|dex2oat|boot image|ClassLoaderContext|oatfile|am_anr|am_kill|low_ram' || true",
}
for name,command in commands.items():
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=90)
 (e/(name+'.txt')).write_bytes(r.stdout+r.stderr);print(name,len(r.stdout))
