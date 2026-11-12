"""Reload native SystemUI after successful package compilation; no OS reboot."""
from pathlib import Path
import argparse,json,os,subprocess,time
parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';record=e/'v36-systemui-speed.json';assert record.exists()==args.resume
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
install=json.loads((e/'netd-event/v36-installation.json').read_text())
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot==install['boot_id']
package=sh('dumpsys package com.android.systemui');assert 'arm: [status=speed] [reason=cmdline]' in package
(e/'v36-systemui-speed-package.txt').write_text(package+'\n',encoding='utf-8')
old_pid=json.loads(record.read_text())['old_systemui_pid'] if args.resume else sh('pidof com.android.systemui');assert old_pid.isdigit()
server=sh('pidof system_server');netd=sh('pidof netd');before=sh('settings get global stay_on_while_plugged_in')
state=json.loads(record.read_text()) if args.resume else dict(boot_id=boot,old_systemui_pid=old_pid,system_server=server,netd=netd,native_speed_compilation_confirmed=True,additional_boots=0)
assert state['boot_id']==boot and state['system_server']==server and state['netd']==netd
def save():record.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
save()
try:
 sh('svc power stayon true')
 if not args.resume:sh('kill -15 '+old_pid)
 started=time.monotonic()
 while time.monotonic()-started<90:
  time.sleep(3);current=sh('pidof com.android.systemui || true')
  if current.isdigit() and current!=old_pid:break
 else:raise RuntimeError('SystemUI did not restart automatically')
 state['new_systemui_pid']=current;time.sleep(20)
 sh('input keyevent 224');sh('wm dismiss-keyguard');sh('input touchscreen swipe 300 900 300 250 400');time.sleep(2)
 started=time.monotonic();state['settings_launch']=sh('am start -W -a android.settings.SETTINGS',100);state['launch_command_seconds']=round(time.monotonic()-started,3)
 state['focus']=sh('dumpsys window | grep mCurrentFocus')
 r=subprocess.run(['python',str(p/'scripts/capture_current_screen.py'),'v36-after-speed'],capture_output=True,timeout=90)
 state['capture_exit']=r.returncode
 if 'com.android.settings/' in state['focus']:
  r=subprocess.run(['python',str(p/'scripts/profile_v24_scrolling.py'),'--label','v36-after-speed'],capture_output=True,timeout=180)
  state['profile_exit']=r.returncode;(e/'v36-after-speed-profile-output.txt').write_bytes(r.stdout+r.stderr)
 state['systemui_alive']=sh('pidof com.android.systemui')==current
 state['boot_server_netd_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server and sh('pidof netd')==netd
finally:
 sh('settings delete global stay_on_while_plugged_in' if before=='null' else 'settings put global stay_on_while_plugged_in '+before)
 state['stay_on_restored']=sh('settings get global stay_on_while_plugged_in')==before;save()
print(json.dumps(state,indent=2))
