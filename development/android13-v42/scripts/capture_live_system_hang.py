"""Capture the owner's current system-process hang without rebooting or clearing logs."""
from pathlib import Path
import datetime,json,os,re,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=20):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
 return r.stdout.decode(errors='replace'),r.stderr.decode(errors='replace'),r.returncode
text,_,code=sh('cat /sys/block/mmcblk0/device/cid');assert code==0 and text.strip()=='1101003030384745T110_ADB_SERIAL'
server=sh('pidof system_server')[0].strip();assert server.isdigit();boot=sh('cat /proc/sys/kernel/random/boot_id')[0].strip()
record=dict(time=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,system_server=server,owner_report='process system isnt responding',reboot_requested=False)
commands={'identity':'cat /proc/uptime; pidof system_server com.android.systemui; getenforce',
 'kernel':'dmesg','events':'logcat -d -b events -t 2000','logcat':'logcat -d -b all -t 5000',
 'last-anr':'dumpsys activity lastanr','processes':'ps -A -T','memory':'cat /proc/meminfo; cat /proc/vmstat; cat /proc/pressure/memory',
 'server-status':'cat /proc/'+server+'/status; cat /proc/'+server+'/wchan; cat /proc/'+server+'/stack',
 'anr-files-before':'ls -lt /data/anr'}
for name,command in commands.items():
 try:
  out,err,code=sh(command);(e/(name+'.txt')).write_text(out+'\nSTDERR:\n'+err,encoding='utf-8');record[name+'_exit']=code
 except subprocess.TimeoutExpired:record[name+'_timeout']=True
 (e/'capture.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
# SIGQUIT is ART's thread-dump signal, not a restart signal.
if sh('pidof system_server')[0].strip()==server:
 record['sigquit_result']=sh('kill -3 '+server)[2];time.sleep(3)
 names=sh('ls -t /data/anr')[0].splitlines()
 for name in names[:5]:
  assert re.fullmatch('[a-zA-Z0-9_.-]+',name)
  try:
   out,err,code=sh('cat /data/anr/'+name,30)
   if 'Cmd line: system_server' in out or 'Cmd line: com.android.systemui' in out:
    (e/name).write_text(out,encoding='utf-8')
  except subprocess.TimeoutExpired:record['anr_read_timeout']=name
record['server_after']=sh('pidof system_server')[0].strip();record['boot_after']=sh('cat /proc/sys/kernel/random/boot_id')[0].strip()
(e/'capture.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2))
