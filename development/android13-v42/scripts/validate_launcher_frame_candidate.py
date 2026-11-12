from pathlib import Path
import json,subprocess,os,time,sys
p=Path(__file__).resolve().parents[1];trial=p/'hardware-tests/20261107-200616-core';e=p/'evidence/offline-v36/launcher-candidate'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=40):return subprocess.check_output(adb+['shell',command],timeout=timeout).decode(errors='replace').strip()
install=json.loads((e/'installation.json').read_text());path=sh('pm path com.android.launcher3').removeprefix('package:')
assert path==install['installed_path'] and sh('sha256sum '+path).split()[0]==install['sha256']
boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot==install['boot_and_server'][0]
server=sh('pidof system_server');assert server=='378'
report=dict(status='RUNNING',boot_id=boot,additional_boots=0,checks=[])
def focus():return sh('dumpsys window | grep mCurrentFocus')
def wait_focus(package):
    start=time.monotonic()
    while time.monotonic()-start<12:
        state=focus()
        if package in state:return round(time.monotonic()-start,3)
        time.sleep(.3)
    raise AssertionError((package,state))
timeout=sh('settings get system screen_off_timeout')
try:
    sh('settings put system screen_off_timeout 180000; input keyevent WAKEUP; wm dismiss-keyguard')
    time.sleep(2)
    marker='RECENTS_SOFTWARE_START_'+str(time.monotonic_ns())
    sh('log -t T110V26Validation '+marker)
    for mode in ['touch','physical']:
        sh('settings put --lineage system force_show_navbar '+('1' if mode=='touch' else '0'))
        time.sleep(2)
        sh('am start -W -a android.settings.SETTINGS');wait_focus('com.android.settings');time.sleep(1)
        if mode=='touch':sh('input keyevent APP_SWITCH')
        else:sh('sendevent /dev/input/event1 1 139 1; sendevent /dev/input/event1 0 0 0; sendevent /dev/input/event1 1 139 0; sendevent /dev/input/event1 0 0 0')
        delay=wait_focus('com.android.launcher3');time.sleep(1)
        label='v26-'+mode+'-recents-from-settings'
        subprocess.run([sys.executable,str(p/'scripts/capture_v26_framebuffer.py'),str(trial),'--label',label],check=True)
        report['checks'].append(dict(mode=mode,recents_from_settings=True,focus_wait_seconds=delay,screenshot_label=label))
        sh('input keyevent HOME');time.sleep(1)
    logs=sh('logcat -b main -b system -d -s T110V26Validation T110SoftwareFrame T110SoftwareSurface AndroidRuntime')
    assert marker in logs
    fresh=logs.split(marker,1)[1]
    assert 'Applying launcher surface transaction without RenderThread' in fresh
    report['software_surface_callback_seen']=True
    report['software_frame_callback_seen']='Using software draw completion for launcher transition' in fresh
    assert 'FATAL EXCEPTION' not in fresh
    (trial/'v26-software-frame-log.txt').write_text(logs,encoding='utf-8')
    assert sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server
    report.update(status='RECENTS_CALLBACK_AND_FOCUS_PASS_VISUAL_REVIEW_PENDING',launcher_pid=sh('pidof com.android.launcher3'),systemui_pid=sh('pidof com.android.systemui'))
finally:
    sh('settings put --lineage system force_show_navbar 1')
    if timeout.isdigit():sh('settings put system screen_off_timeout '+timeout)
    (trial/'v26-launcher-runtime.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
