"""Reversible control checks only; restore all preferences and retain raw evidence."""
from pathlib import Path
import json,os,subprocess,time
from PIL import Image
p=Path(__file__).resolve().parents[1];e=p/'evidence/functional-audit-20261110'
a=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s,timeout=20):return subprocess.check_output(a+['shell',s],timeout=timeout).decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
record={};original={'brightness':sh('settings get system screen_brightness'),'brightness_mode':sh('settings get system screen_brightness_mode'),'navigation':sh('settings get --lineage system force_show_navbar')}
(e/'control-original-settings.json').write_text(json.dumps(original,indent=2)+'\n')
try:
    sh('input keyevent WAKEUP; wm dismiss-keyguard')
    for value in [40,220]:
        sh(f'settings put system screen_brightness_mode 0; settings put system screen_brightness {value}; sleep 1')
        record.setdefault('brightness',[]).append({'requested':value,'sysfs':sh('cat /sys/class/backlight/panel/brightness'),'power':sh('dumpsys power | grep -E "mScreenBrightnessSetting|mScreenBrightnessOverrideFromWindowManager|Display Power"')})
    sh('input keyevent SLEEP; sleep 1')
    record['screen_sleep']=sh('dumpsys power | grep -E "mWakefulness=|Display Power|mScreenOn"; cat /sys/class/graphics/fb0/blank')
    sh('input keyevent WAKEUP; wm dismiss-keyguard; sleep 1')
    record['screen_wake']=sh('dumpsys power | grep -E "mWakefulness=|Display Power|mScreenOn"; cat /sys/class/graphics/fb0/blank')
    # This is the stock framework screenshot API, independent from the framebuffer reader.
    try:
        cap=subprocess.run(a+['exec-out','screencap -p'],capture_output=True,timeout=25)
        if cap.stdout.startswith(b'\x89PNG'):
            out=e/'framework-screencap.png';out.write_bytes(cap.stdout)
            with Image.open(out) as image:record['framework_screenshot']={'status':'PNG_CAPTURED_VISUAL_REVIEW_PENDING','size':image.size,'bytes':len(cap.stdout)}
        else:record['framework_screenshot']={'status':'FAIL_NO_PNG','exit':cap.returncode,'stderr':cap.stderr.decode(errors='replace')[:800]}
    except subprocess.TimeoutExpired:record['framework_screenshot']={'status':'TIMEOUT'}
finally:
    sh('settings put system screen_brightness '+original['brightness']+'; settings put system screen_brightness_mode '+original['brightness_mode']+'; settings put --lineage system force_show_navbar '+original['navigation']+'; input keyevent WAKEUP; wm dismiss-keyguard')
    (e/'controls.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2),flush=True)
