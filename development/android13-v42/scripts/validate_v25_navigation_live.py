"""Exercise existing physical input devices in both navigation modes on one boot."""
from pathlib import Path
import argparse,json,os,re,subprocess,time,sys
parser=argparse.ArgumentParser();parser.add_argument('trial',type=Path);a=parser.parse_args()
p=Path(__file__).resolve().parents[1]
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def shell(s,timeout=35):return subprocess.check_output(adb+['shell',s],timeout=timeout).decode(errors='replace').strip()
assert shell('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
checks=json.loads((p/'evidence/offline-v35/contents.json').read_text(encoding='utf-8'))
assert checks['status']=='PASS'
for name in ['system/framework/services.jar','system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service','system/system_ext/priv-app/SystemUI/SystemUI.apk']:
    assert shell('sha256sum /'+name).split()[0]==checks['changed'][name],name
assert shell('cat /sys/class/input/event0/device/name')=='gpio-keys'
assert shell('cat /sys/class/input/event1/device/name')=='sec_touchscreen'
boot=shell('cat /proc/sys/kernel/random/boot_id');server=shell('pidof system_server')
mapping=shell('dumpsys input')
assert '/vendor/usr/keylayout/gpio-keys.kl' in mapping
assert '/vendor/usr/keylayout/sec_touchscreen.kl' in mapping
def focused():return shell('dumpsys window | grep mCurrentFocus')
def wait_focus(package):
    started=time.monotonic()
    while time.monotonic()-started<12:
        state=focused()
        if package in state:return state,round(time.monotonic()-started,3)
        time.sleep(0.3)
    raise AssertionError(('Focus did not change',package,state))
def key(device,code):
    shell(f'sendevent /dev/input/event{device} 1 {code} 1; sendevent /dev/input/event{device} 0 0 0; sendevent /dev/input/event{device} 1 {code} 0; sendevent /dev/input/event{device} 0 0 0')
    time.sleep(1.5)
def capture(label):
    subprocess.run([sys.executable,str(p/'scripts/capture_v26_framebuffer.py'),str(a.trial),'--label',label],check=True)
report=dict(boot_id=boot,physical_key_checks=[],extra_boots=0,method='sendevent through identified built-in devices; not a physical finger test')
old_timeout=shell('settings get system screen_off_timeout')
try:
    shell('settings put system screen_off_timeout 180000; input keyevent WAKEUP; wm dismiss-keyguard')
    time.sleep(2)
    shell('settings put --lineage system force_show_navbar 1')
    time.sleep(2)
    shell('am start -W -a android.settings.SETTINGS')
    time.sleep(2)
    initial=focused();assert 'com.android.settings' in initial,initial
    for name,device,code in [('Home',0,102),('Recents',1,139),('Back',1,158)]:
        key(device,code);state=focused();assert state==initial,(name,initial,state)
        report['physical_key_checks'].append(dict(mode='touch',key=name,suppressed=True))
    capture('v25-touch-navigation-physical-keys-blocked')
    shell('settings put --lineage system force_show_navbar 0');time.sleep(2)
    key(0,102);state,wait=wait_focus('com.android.launcher3')
    report['physical_key_checks'].append(dict(mode='physical',key='Home',opens_launcher=True,extra_wait_seconds=wait))
    shell('am start -W -a android.settings.SETTINGS');time.sleep(1)
    key(1,139);capture('v25-physical-recents')
    report['physical_key_checks'].append(dict(mode='physical',key='Recents',focused=focused(),visual_review_required=True))
    key(0,102)
    shell('am start -W -a android.settings.SETTINGS');time.sleep(1)
    key(1,158);state,wait=wait_focus('com.android.launcher3')
    report['physical_key_checks'].append(dict(mode='physical',key='Back',returns_from_settings=True,extra_wait_seconds=wait))
    assert shell('cat /proc/sys/kernel/random/boot_id')==boot
    assert shell('pidof system_server')==server
    report['status']='AUTOMATED_NAVIGATION_CHECKS_PASS_RECENTS_NEEDS_VISUAL_REVIEW'
finally:
    shell('settings put --lineage system force_show_navbar 1')
    if old_timeout.isdigit():shell('settings put system screen_off_timeout '+old_timeout)
    (a.trial/'navigation-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
