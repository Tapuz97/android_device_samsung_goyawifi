"""Run a normal Android action and save its visible screen and accessibility tree."""
from pathlib import Path
import argparse,os,shlex,subprocess,json,uuid
parser=argparse.ArgumentParser();parser.add_argument('label');parser.add_argument('--action',default='');parser.add_argument('--evidence',default='functional-audit-20261110');a=parser.parse_args()
assert a.label.replace('-','').isalnum()
assert a.evidence.replace('-','').isalnum()
p=Path(__file__).resolve().parents[1];e=p/'evidence'/a.evidence;e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(c,timeout=35):return subprocess.run(adb+['shell',c],capture_output=True,timeout=timeout)
assert call('cat /sys/block/mmcblk0/device/cid').stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL'
import time
call('input keyevent WAKEUP; wm dismiss-keyguard')
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    policy=call('dumpsys window policy').stdout.decode()
    if 'showing=false' in policy and 'inputRestricted=false' in policy:break
    time.sleep(1)
else:raise RuntimeError('Manual unlock needed; audit action not started')
if a.action:
    result=call('input keyevent WAKEUP; '+a.action+'; sleep 2',60)
    (e/(a.label+'-action.txt')).write_bytes(result.stdout+b'\nSTDERR:\n'+result.stderr)
zygote=call('pidof zygote').stdout.decode().split()[0]
raw=subprocess.check_output(adb+['exec-out','cat /proc/'+zygote+'/environ'],timeout=15).decode()
env={}
for item in raw.split('\0'):
    if '=' in item:
        k,v=item.split('=',1)
        if k in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','ANDROID_ART_ROOT','ANDROID_I18N_ROOT','ANDROID_TZDATA_ROOT']:env[k]=v
remote='/data/local/tmp/t110-audit-window-'+uuid.uuid4().hex+'.xml'
result=call(' '.join(k+'='+shlex.quote(v) for k,v in env.items())+' timeout 20 uiautomator dump --compressed '+remote,30)
(e/(a.label+'-tree-command.txt')).write_bytes(result.stdout+b'\nSTDERR:\n'+result.stderr)
data=subprocess.check_output(adb+['exec-out','cat '+remote],timeout=15)
if data.startswith(b'<?xml'):(e/(a.label+'.xml')).write_bytes(data)
else:print('UI_TREE_UNAVAILABLE',data[:50])
call('test ! -f '+remote+' || rm '+remote)
subprocess.run(['python',str(p/'scripts/capture_shade_transition.py'),a.label,'--evidence',a.evidence],check=True)
print(a.label,'capture complete',flush=True)
