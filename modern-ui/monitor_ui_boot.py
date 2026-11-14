"""Bounded boot-property checks, then one status/crash snapshot. No live feed."""
from pathlib import Path
import json,subprocess,time
ADB=r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe'
DEST=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14-ui\hardware-test')
def adb(*args):
    result=subprocess.run([ADB,'-s','3004523270272200',*args],capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr.decode(errors='replace')[-100:]
    return result.stdout.decode(errors='replace').replace('\r','')
start=time.monotonic();last=None
for _ in range(90):
    try:
        state=adb('get-state').strip()
        if state=='device':
            data=adb('shell','getprop ro.build.version.incremental; getprop sys.boot_completed; getprop init.svc.zygote').splitlines()
            status=(state,*data)
            if status!=last:print('Boot status:',status,flush=True);last=status
            if len(data)==3 and data[0]=='T110_UI_20261114_R2' and data[1]=='1' and data[2]=='running':break
    except Exception:pass
    time.sleep(4)
else:raise RuntimeError('Full UI boot has not completed within the bounded observation window.')
snapshot=adb('shell',
    'cat /proc/sys/kernel/random/boot_id; getprop ro.build.fingerprint; '
    'settings get secure camera_double_tap_power_gesture_disabled; '
    'pidof system_server com.android.systemui com.cyanogenmod.trebuchet; '
    'dumpsys window windows | grep -E "mCurrentFocus|mFocusedApp"')
(DEST/'boot-status-PRIVATE.txt').write_text(snapshot,encoding='utf-8')
crashes=adb('shell','logcat -b crash -d -t 80')
(DEST/'boot-crash-buffer-PRIVATE.txt').write_text(crashes,encoding='utf-8')
print(snapshot,flush=True)
result={'status':'ANDROID_BOOT_COMPLETED_PHYSICAL_UI_UNVERIFIED',
        'build_id':'T110_UI_20261114_R2','boot_id':snapshot.splitlines()[0],
        'observed_completion_seconds':round(time.monotonic()-start,1),
        'timing_scope':'Time from starting this observer, not a cold-boot benchmark',
        'crash_snapshot_has_fatal_exception':'FATAL EXCEPTION' in crashes}
(DEST/'boot-observation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
