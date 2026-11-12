from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/input-dispatch'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
for name,cmd in [('dexopt','dumpsys package dexopt'),('art-logs',"logcat -d -b all -t 20000 | grep -Ei 'ClassLoaderContext|boot image|oat file|oatfile|dexopt|dex2oat|compiler-filter|Failed to open.*art|Failed to map' || true")]:
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=90);assert r.returncode==0
 (e/(name+'.txt')).write_bytes(r.stdout);print(name,len(r.stdout))
