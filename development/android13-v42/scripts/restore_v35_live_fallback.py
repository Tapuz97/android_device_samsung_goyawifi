"""Restore verified software windows on this boot without changing the Wi-Fi kernel."""
from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';path=e/'v35-live-fallback.json';assert not path.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd,timeout=40):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot=='8644e9ae-31e3-4e1a-a62f-1e0d58cdc01e'
before=sh('pidof system_server');ui=sh('pidof com.android.systemui').split();assert len(ui)==1 and ui[0].isdigit()
assert (e/'v35-live-threads/targets.json').exists()
sh('setprop debug.hwui.t110_window_gpu false');assert sh('getprop debug.hwui.t110_window_gpu')=='false'
sh('am force-stop com.android.settings');sh('am force-stop com.android.launcher3');sh('kill -TERM '+ui[0]);time.sleep(8)
sh('input keyevent 224');time.sleep(2);sh('wm dismiss-keyguard');time.sleep(2);sh('input touchscreen swipe 300 900 300 250 400');time.sleep(2)
launch=sh('am start -W -a android.settings.SETTINGS',100);time.sleep(4)
result=dict(boot_id=boot,old_systemui=ui[0],systemui_after=sh('pidof com.android.systemui'),system_server_stable=sh('pidof system_server')==before,
 boot_stable=sh('cat /proc/sys/kernel/random/boot_id')==boot,graphics_flag=sh('getprop debug.hwui.t110_window_gpu'),
 launch=launch,focus=sh('dumpsys window | grep mCurrentFocus || true'),reboot_requests=0,
 caution='Live flag resets on next boot; persist safe default before any reboot')
path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
