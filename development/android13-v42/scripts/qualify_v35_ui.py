"""Same-boot native app drawing/profile checks with temporary screen-on setting."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time
parser=argparse.ArgumentParser();parser.add_argument('--fallback',action='store_true');parser.add_argument('--system-v36',action='store_true');options=parser.parse_args()
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';prefix='v36-safe' if options.system_v36 else ('v35-safe' if options.fallback else 'v35-native');label=prefix;path=e/(prefix+'-ui-qualification.json');assert not path.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd,timeout=45):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
if options.system_v36:assert options.fallback
install=json.loads((e/'netd-event/v36-installation.json' if options.system_v36 else (e/'boot42-installation.json' if options.fallback else p/'evidence/offline-v41/gapps-v35-test/installation.json')).read_text())
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot==install['boot_id']
assert sh('getprop sys.boot_completed')=='1' and sh('getenforce')=='Enforcing'
host=json.loads((p/('artifacts/lineage20-rom-v36-gapps/host-verification.json' if options.system_v36 else 'artifacts/lineage20-rom-v35-gapps/host-verification.json')).read_text())
for name in ['system/lib/libhwui.so','system/framework/framework.jar']:
 assert sh('sha256sum /'+name).split()[0]==host['native_components_unchanged'][name],name
assert (sh('getprop debug.hwui.t110_window_gpu')=='false')==options.fallback
before=sh('settings get global stay_on_while_plugged_in')
state=dict(boot_id=boot,system_server=sh('pidof system_server'),original_stay_on=before,native_hwui_and_framework_hashes_match=True,
           normal_gpu_window_default=not options.fallback,additional_boots=0)
def save():path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
save()
try:
 sh('svc power stayon true');sh('input keyevent 224');time.sleep(2);sh('wm dismiss-keyguard');time.sleep(2)
 sh('input touchscreen swipe 300 900 300 250 400');time.sleep(2)
 state['settings_launch']=sh('am start -W -a android.settings.SETTINGS',100)
 time.sleep(3)
 state['settings_focus']=sh("dumpsys window | grep mCurrentFocus || true")
 if 'com.android.settings/' in state['settings_focus']:
  profile_label=label+'-gpu' if not options.fallback else label+'-software'
  r=subprocess.run(['python',str(p/'scripts/profile_v24_scrolling.py'),'--label',profile_label],capture_output=True,timeout=180)
  state['profile_exit']=r.returncode
  (e/(profile_label+'-profile-output.txt')).write_bytes(r.stdout+r.stderr)
  if r.returncode==0:state['scroll_profile']=json.loads((p/('evidence/offline-v35/'+profile_label+'-scroll-profile.json')).read_text())
 for label,command in [('settings','am start -W -a android.settings.SETTINGS'),('home','input keyevent 3'),('recents','input keyevent 187')]:
  sh(command,100);time.sleep(3)
  capture_label=prefix+'-'+label
  r=subprocess.run(['python',str(p/'scripts/capture_current_screen.py'),capture_label],capture_output=True,timeout=90)
  state[label+'_framebuffer_capture_exit']=r.returncode
  (e/(capture_label+'-capture.txt')).write_bytes(r.stdout+r.stderr)
  (e/(capture_label+'-window.txt')).write_text(sh('dumpsys window')+'\n',encoding='utf-8')
 sh('input keyevent 3')
 state['pids_after']=sh('pidof system_server surfaceflinger com.android.systemui com.android.launcher3')
 state['server_stable']=sh('pidof system_server')==state['system_server']
 state['boot_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot
finally:
 sh('settings delete global stay_on_while_plugged_in' if before=='null' else 'settings put global stay_on_while_plugged_in '+before)
 state['stay_on_restored']=sh('settings get global stay_on_while_plugged_in')==before;save()
print(json.dumps(state,indent=2))
