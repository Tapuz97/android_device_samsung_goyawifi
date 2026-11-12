from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/input-dispatch';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=90);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /proc/sys/kernel/random/boot_id')=='5730f721-68a5-4035-9800-13a3f8a0a99d'
for name,cmd in [('input','dumpsys input'),('logs','logcat -d -b all -t 12000'),('sf','dumpsys SurfaceFlinger'),('display','dumpsys display'),('fallback',"logcat -d -s ViewRootImpl:I '*:S'")]:
 text=sh(cmd);(e/(name+'.txt')).write_text(text+'\n',encoding='utf-8');print(name,len(text))
