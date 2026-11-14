"""Save bounded UI qualification and restore temporary display test settings."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
from PIL import Image
WORK=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14-ui')
DEST=WORK/'hardware-test';LOCAL=Path(__file__).parent.parent/'tests/modern-ui'
ADB=r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe'
def shell(command):
    p=subprocess.run([ADB,'-s','3004523270272200','shell',command],capture_output=True,timeout=40)
    assert p.returncode==0,p.stderr.decode(errors='replace')[-200:]
    return p.stdout.decode(errors='replace').replace('\r','')
props=shell('getprop ro.build.version.incremental; getprop ro.bq.gpu_to_cpu_unsupported; getprop sys.boot_completed')
assert props.splitlines()==['T110_UI_20261114_R2','1','1'],props
crashes=shell('logcat -b crash -d -t 100')
(DEST/'final-crash-buffer-PRIVATE.txt').write_text(crashes,encoding='utf-8')
assert 'FATAL EXCEPTION' not in crashes,'A Java crash requires review before calling UI qualification passed.'
for name in ('settings','quick-settings','landscape','drawer','recents'):
    original=LOCAL/('r2-'+name+'-native.png')
    with Image.open(original) as frame:frame.transpose(Image.Transpose.ROTATE_270).save(LOCAL/('preview-'+name+'.png'))
shell('input keyevent 3; am start -a android.settings.SETTINGS; settings put global stay_on_while_plugged_in 0; settings put system screen_off_timeout 60000; settings delete system user_rotation; settings put system accelerometer_rotation 1')
settings=shell('settings get global stay_on_while_plugged_in; settings get system screen_off_timeout; settings get system user_rotation; settings get system accelerometer_rotation; settings get secure camera_double_tap_power_gesture_disabled')
assert settings.splitlines()==['0','60000','null','1','1'],settings
report={'status':'INSTALLED_AUTOMATIC_UI_CHECKS_PASSED_MANUAL_TOUCH_PENDING',
    'recorded_utc':datetime.now(timezone.utc).isoformat(),'build_id':'T110_UI_20261114_R2',
    'kernel_and_recovery_unchanged':True,'original_working14_image_retained':True,
    'data_profiles_preserved':True,'native_app_set_preserved':79,
    'verified':['normal screenshot capture as standard ADB shell user',
        'readable native Settings dashboard and search/keyboard flow',
        'Quick Settings portrait and full-width landscape layouts',
        'Wi-Fi-only default tile list', 'compact native launcher drawer',
        'new Settings Recents preview and native Clear all dismissal',
        'native power menu styling on R1; unchanged R2 menu resources'],
    'physical_finger_touch_rechecked':False,'new_java_crashes_in_bounded_snapshot':False,
    'baseline_bootanimation_native_crash_seen':'BootAnimation' in crashes and 'Fatal signal' in crashes,
    'remaining':['owner physical display/touch confirmation',
        'separate baseline BootAnimation native-crash audit',
        'Google-enabled distribution/root/publication qualification'],
    'scope':'Visual backport on API25; not a port of the newest Android APIs, dynamic color engine or Quickstep',
    'temporary_screen_settings_restored':True,'continuous_capture_running':False,
    'source_branch':'t110/lineage14-modern-ui-20261114'}
(DEST/'ui-acceptance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
