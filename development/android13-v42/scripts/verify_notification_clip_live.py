"""Capture native notification expansion/scrolling after the integrated ROM update."""
from pathlib import Path
import json,os,subprocess,sys,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v40'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(c):return subprocess.check_output(adb+['shell',c],timeout=40).decode().strip()
def shot(label,action=''):
    label=label.replace('shade-fixed','shade-verified')
    args=[sys.executable,str(p/'scripts/capture_shade_transition.py'),label]
    if action:args+=['--action',action]
    subprocess.run(args,check=True)
assert sh('getprop sys.boot_completed')=='1'
boot=sh('cat /proc/sys/kernel/random/boot_id')
assert boot!='9f48e9ba-49c8-4cf8-a1f2-0fca599e83c1'
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
expected=json.loads((e/'contents.json').read_text())['files']['system/system_ext/priv-app/SystemUI/SystemUI.apk']
assert sh('pm path com.android.systemui')=='package:/system/system_ext/priv-app/SystemUI/SystemUI.apk'
assert sh('sha256sum /system/system_ext/priv-app/SystemUI/SystemUI.apk').split()[0]==expected
pid=sh('pidof com.android.systemui');server=sh('pidof system_server')
sh('input keyevent WAKEUP; wm dismiss-keyguard')
deadline=time.monotonic()+45
while time.monotonic()<deadline:
    policy=sh('dumpsys window policy')
    if 'showing=false' in policy and 'inputRestricted=false' in policy:break
    time.sleep(1)
else:raise RuntimeError('Keyguard has not finished dismissing; no interaction sequence started')
assert 'Application Not Responding' not in sh('dumpsys window | grep mCurrentFocus')
shot('shade-fixed-rest','input keyevent WAKEUP; wm dismiss-keyguard; cmd statusbar expand-notifications; sleep 2')
shot('shade-fixed-collapsed','input tap 544 305; sleep 1')
shot('shade-fixed-expanded','input tap 544 305; sleep 1')
drag=subprocess.Popen(adb+['shell','input swipe 300 750 300 330 4000'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
    time.sleep(.6);shot('shade-fixed-drag')
    stdout,stderr=drag.communicate(timeout=15);assert drag.returncode==0,(stdout,stderr)
finally:
    if drag.poll() is None:drag.kill();drag.wait()
shot('shade-fixed-reopened','cmd statusbar collapse; cmd statusbar expand-notifications; sleep 2')
assert sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server and sh('pidof com.android.systemui')==pid
(e/'shade-verified-systemui.txt').write_text(sh('dumpsys activity service com.android.systemui/.SystemUIService'),encoding='utf-8')
(e/'post-update-crash-log.txt').write_text(sh('logcat -b crash -d -v threadtime'),encoding='utf-8')
record=dict(status='INSTALLED_HASH_AND_SAME_PROCESS_INTERACTIONS_VERIFIED_VISUAL_REVIEW_PENDING',boot_id=boot,system_server=server,system_ui=pid,systemui_sha256=expected,additional_full_system_boots=1,software_window_clipping_fix='0076',navigation_mode=sh('settings get --lineage system force_show_navbar'),boot_completed=True)
(e/'runtime.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2))
