"""Read the current UI failure evidence without changing rendering or app settings."""
from pathlib import Path
import datetime,json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-status-20261112';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd,timeout=45):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace')[-1000:]
 return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id');out=e/(boot+'.json');assert not out.exists()
state=dict(checked=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,system_server=sh('pidof system_server'),
 systemui_pid=sh('pidof com.android.systemui'),gpu_windows=sh('getprop debug.hwui.t110_window_gpu'),settings_changed=False,ui_fix_claimed=False)
for name,cmd in {'last-anr':'dumpsys activity lastanr','ui-render':'dumpsys gfxinfo com.android.systemui','memory':'cat /proc/meminfo; cat /proc/vmstat',
                 'events':'logcat -d -b events -t 1500'}.items():
 text=sh(cmd,60);(e/(boot+'-'+name+'.txt')).write_text(text+'\n',encoding='utf-8')
 if name=='events':state['recent_anr_events']=[line for line in text.splitlines() if 'am_anr:' in line][-10:]
 if name=='last-anr':state['last_anr_present']='no anr has occurred' not in text.lower()
state['boot_unchanged']=sh('cat /proc/sys/kernel/random/boot_id')==boot
out.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:state[k] for k in ['systemui_pid','gpu_windows','last_anr_present','boot_unchanged','ui_fix_claimed']},indent=2))
