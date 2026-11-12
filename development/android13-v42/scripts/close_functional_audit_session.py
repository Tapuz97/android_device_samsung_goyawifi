"""Remove only owned QA tools and restore the audit's temporary display preferences."""
from pathlib import Path
import subprocess,os,hashlib,json,time,sys
p=Path(__file__).resolve().parents[1];audit=p/'evidence/functional-audit-20261110'
label=sys.argv[sys.argv.index('--evidence')+1] if '--evidence' in sys.argv else 'remote-fixes-20261110'
assert all(part.replace('-','').isalnum() for part in Path(label).parts)
e=p/'evidence'/label;e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL'];pkg='dev.tapuz.t110.audit'
def call(args,check=True):return subprocess.run(adb+args,capture_output=True,timeout=30,check=check)
def sh(s,**kw):return call(['shell',s],**kw).stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
installed=sh('pm path '+pkg,check=False)
if installed:
    assert installed.startswith('package:/data/app/') and '\n' not in installed
    apk=audit/'qa-build/T110FunctionalAudit.apk'
    assert sh('sha256sum '+installed.removeprefix('package:')).split()[0]==hashlib.sha256(apk.read_bytes()).hexdigest()
    sh('appwidget revokebind --package '+pkg+' --user 0')
    assert b'Success' in call(['uninstall',pkg]).stdout
assert not sh('pm path '+pkg,check=False)
original=json.loads((audit/'ui-original-settings.json').read_text())
assert original=={'timeout':'60000','stay_on':'0'}
sh('settings put system screen_off_timeout 60000; settings put global stay_on_while_plugged_in 0')
after=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines();assert after==before
state=sh('settings get system screen_off_timeout; settings get global stay_on_while_plugged_in; settings get system screen_brightness; settings get system force_show_navbar').splitlines()
assert state[:2]==['60000','0']
record={'boot_and_server':after,'qa_package_uninstalled':True,'qa_widget_permission_revoked':True,'restored_screen_settings':state,'additional_boots':0,'device_clock_epoch':int(sh('date +%s')),'host_epoch':time.time(),'timezone':sh('getprop persist.sys.timezone')}
(e/'session-restoration.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
