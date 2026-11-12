from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
for name,command in {'aot-failure-log':'logcat -d -b all -t 10000','aot-failure-kernel':'dmesg','aot-failure-state':'df -k /data; pidof dex2oat32 system_server com.android.systemui'}.items():
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=30);text=(r.stdout+r.stderr).decode(errors='replace');(e/(name+'.txt')).write_text(text,encoding='utf-8')
 if name.endswith('state'):print(text)
 else:
  keys=['dex2oat','lowmemorykiller','Out of memory','oom-kill','ENOSPC','I/O error','mmcblk0: error']
  lines=[line for line in text.splitlines() if any(k in line for k in keys)]
  print(name+'\n'+'\n'.join(lines[-28:]))
