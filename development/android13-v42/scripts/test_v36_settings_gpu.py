"""One normal-app GPU comparison on the same boot; restore the fallback afterward."""
from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';out=e/'v36-settings-gpu.json';assert not out.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
install=json.loads((e/'netd-event/v36-installation.json').read_text());boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot==install['boot_id']
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
before=sh('getprop debug.hwui.t110_window_gpu');assert before=='false'
stay=sh('settings get global stay_on_while_plugged_in');server=sh('pidof system_server');netd=sh('pidof netd')
state=dict(boot_id=boot,system_server=server,netd=netd,additional_boots=0,original_gpu_flag=before)
def save():out.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
save()
try:
 sh('svc power stayon true');sh('input keyevent 224');sh('wm dismiss-keyguard')
 sh('setprop debug.hwui.t110_window_gpu true');assert sh('getprop debug.hwui.t110_window_gpu')=='true'
 sh('am force-stop com.android.settings');started=time.monotonic();state['launch']=sh('am start -W -a android.settings.SETTINGS',100);state['launch_seconds']=round(time.monotonic()-started,3)
 time.sleep(3);state['focus']=sh('dumpsys window | grep mCurrentFocus')
 r=subprocess.run(['python',str(p/'scripts/capture_current_screen.py'),'v36-normal-gpu'],capture_output=True,timeout=90);state['capture_exit']=r.returncode
 if 'com.android.settings/' in state['focus']:
  r=subprocess.run(['python',str(p/'scripts/profile_v24_scrolling.py'),'--label','v36-normal-gpu'],capture_output=True,timeout=180)
  state['profile_exit']=r.returncode;(e/'v36-normal-gpu-profile.txt').write_bytes(r.stdout+r.stderr)
 (e/'v36-normal-gpu-gfxinfo.txt').write_text(sh('dumpsys gfxinfo com.android.settings framestats')+'\n',encoding='utf-8')
 (e/'v36-normal-gpu-logs.txt').write_text(sh('logcat -d -b all -t 5000')+'\n',encoding='utf-8')
 state['boot_server_netd_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server and sh('pidof netd')==netd
finally:
 sh('setprop debug.hwui.t110_window_gpu '+before);state['gpu_flag_restored']=sh('getprop debug.hwui.t110_window_gpu')==before
 sh('am force-stop com.android.settings');sh('am start -a android.settings.SETTINGS',100)
 sh('settings delete global stay_on_while_plugged_in' if stay=='null' else 'settings put global stay_on_while_plugged_in '+stay)
 state['stay_on_restored']=sh('settings get global stay_on_while_plugged_in')==stay;save()
print(json.dumps(state,indent=2))
