"""Capture awake input/display state after the v36 normal-window qualification."""
from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/v36-ui-diagnostics';assert not e.exists();e.mkdir()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=60):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
install=json.loads((p/'evidence/hardware-v35/netd-event/v36-installation.json').read_text())
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('cat /proc/sys/kernel/random/boot_id')==install['boot_id']
before=sh('settings get global stay_on_while_plugged_in')
try:
 sh('svc power stayon true');sh('input keyevent 224')
 for name,command in [
  ('input','dumpsys input'),('window','dumpsys window'),('sf','dumpsys SurfaceFlinger'),
  ('display','dumpsys display'),('logs','logcat -d -b all -t 16000'),
  ('state','cat /proc/uptime; pidof netd system_server surfaceflinger com.android.systemui com.android.settings com.android.launcher3; cat /proc/meminfo; cat /proc/loadavg'),
  ('last-anr','dumpsys activity lastanr'),('gfxinfo','dumpsys gfxinfo com.android.settings framestats')]:
  value=sh(command,90);(e/(name+'.txt')).write_text(value+'\n',encoding='utf-8');print(name,len(value),flush=True)
finally:
 sh('settings delete global stay_on_while_plugged_in' if before=='null' else 'settings put global stay_on_while_plugged_in '+before)
 assert sh('settings get global stay_on_while_plugged_in')==before
(e/'record.json').write_text(json.dumps(dict(boot_id=install['boot_id'],screen_woken=True,stay_on_restored=True,additional_boots=0),indent=2)+'\n')
