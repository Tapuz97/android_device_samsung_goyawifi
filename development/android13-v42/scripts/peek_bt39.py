from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
for name,cmd in {'bt39-live-log':'logcat -d -b all -t 4000','bt39-live-manager':'dumpsys bluetooth_manager'}.items():
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=45,check=True);text=r.stdout.decode(errors='replace');(e/(name+'.txt')).write_text(text,encoding='utf-8')
 if name.endswith('manager'):lines=[line for line in text.splitlines() if any(k in line for k in ['enabled:','state:','Bluetooth crashed'])]
 else:lines=[line for line in text.splitlines() if any(k in line for k in ['Abort message:','Firmware configured','Fatal signal','assertion \'init_status','initializationComplete:'])][-14:]
 print(name+'\n'+'\n'.join(lines))
