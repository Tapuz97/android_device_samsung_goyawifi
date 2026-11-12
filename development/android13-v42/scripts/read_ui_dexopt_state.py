from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
for name,command in {'dexopt':'dumpsys package dexopt','runtime':'getprop dalvik.vm.usejit; getprop dalvik.vm.usejitprofiles; getprop persist.sys.dalvik.vm.lib.2; getprop dalvik.vm.dex2oat-filter; getprop dalvik.vm.systemuicompilerfilter; cat /proc/sys/vm/swappiness; cat /sys/devices/system/cpu/online',
 'ui-suspend':'pidof com.android.systemui system_server; cat /proc/meminfo; cat /proc/vmstat'}.items():
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=60);text=(r.stdout+r.stderr).decode(errors='replace');(e/(name+'.txt')).write_text(text,encoding='utf-8')
 if name=='dexopt':
  lines=text.splitlines();keep=False;selected=[]
  for line in lines:
   if line.startswith('['):keep=any(x in line for x in ['com.android.systemui','com.android.launcher3','com.google.android.googlequicksearchbox'])
   if keep:selected.append(line)
  print('\n'.join(selected)[:4000])
 if name=='runtime':print('RUNTIME\n'+text)
