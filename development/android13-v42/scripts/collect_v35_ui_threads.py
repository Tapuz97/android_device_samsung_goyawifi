"""Request nonfatal Java/native thread dumps before changing the graphics mode."""
from pathlib import Path
import json,os,re,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/v35-live-threads';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /proc/sys/kernel/random/boot_id')=='8644e9ae-31e3-4e1a-a62f-1e0d58cdc01e'
targets={name:sh('pidof '+name).split()[0] for name in ['com.android.systemui','com.android.settings','com.android.launcher3']}
for pid in targets.values():sh('kill -3 '+pid);time.sleep(2)
time.sleep(3)
names=sh('ls -t /data/anr').splitlines()[:16];saved=[]
for name in names:
 assert re.fullmatch('[a-zA-Z0-9_.-]+',name)
 text=sh('cat /data/anr/'+name,60)
 if any(re.search(r'^----- pid '+re.escape(pid)+r'\b',text,re.M) for pid in targets.values()):
  (e/name).write_text(text+'\n',encoding='utf-8');saved.append(name)
(e/'targets.json').write_text(json.dumps(dict(targets=targets,files=saved,nonfatal_SIGQUIT=True),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(targets=targets,saved=saved)))
