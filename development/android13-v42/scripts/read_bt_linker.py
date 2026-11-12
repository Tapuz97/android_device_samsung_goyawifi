from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
for name,command in {'bt-linker':'cat /linkerconfig/ld.config.txt','bt-impl-node':'ls -lZ /vendor/lib/hw/android.hardware.bluetooth@1.0-impl.so; ls -lZ /vendor/lib/libbt-vendor.so; getprop init.svc.vendor.bluetooth-1-1'}.items():
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=30,check=True);text=r.stdout.decode(errors='replace');(e/(name+'.txt')).write_text(text)
 if name=='bt-linker':
  print('\n'.join(line for line in text.splitlines() if any(x in line for x in ['[vendor]','namespace.default','dir.vendor','hw'])))
 else:print(text)
