"""Bounded final checks on the already-installed ROM; never flash or reboot."""
from pathlib import Path
import datetime,json,os,re,subprocess,time

p=Path(__file__).resolve().parents[1]
out=p/'evidence/functional-followup-20261111'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def run(args,timeout=45):
    return subprocess.run(args,capture_output=True,timeout=timeout)
def sh(command,timeout=45):
    r=run(adb+['shell',command],timeout)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    return r.stdout.decode(errors='replace').strip()
deadline=time.monotonic()+360
while time.monotonic()<deadline:
    try:
        if sh('getprop sys.boot_completed',8)=='1':break
    except (AssertionError,subprocess.TimeoutExpired):pass
    time.sleep(5)
else:raise RuntimeError('Android startup did not complete; no further interaction attempted')
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id')
server=sh('pidof system_server')
result=dict(host_time=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,
            system_server=server,boot_completed=True,additional_boot_requests=0)
for name,command in {
    'wifi':'cmd wifi status; ip addr show wlan0; ip rule; ip route show table all',
    'memory':'cat /proc/meminfo; cat /proc/swaps; cat /proc/vmstat',
    'startup':'logcat -b all -d -t 6000',
    'graphics':'dumpsys SurfaceFlinger',
}.items():
    (out/('v34-final-'+name+'.txt')).write_text(sh(command,90)+'\n',encoding='utf-8')
https=run(adb+['shell','am instrument --no-hidden-api-checks -w -e action https dev.tapuz.t110.interaction/.InteractionInstrumentation'],60)
https_text=https.stdout.decode(errors='replace')
(out/'v34-final-app-network.txt').write_text(https_text,encoding='utf-8')
match=re.search(r'INSTRUMENTATION_RESULT: report=(.*)',https_text)
result['ordinary_app_network']=json.loads(match[1]) if match else {'error':'Missing instrumentation result'}
original_stay=sh('settings get global stay_on_while_plugged_in')
try:
    sh('settings put global stay_on_while_plugged_in 2; input keyevent 224; wm dismiss-keyguard')
    profile=run(['python',str(p/'scripts/profile_v24_scrolling.py'),'--label','v34-final'],180)
    (out/'v34-scroll-command.txt').write_bytes(profile.stdout+b'\nSTDERR:\n'+profile.stderr)
    result['scroll_profile_completed']=profile.returncode==0
    profile_path=p/'evidence/offline-v35/v34-final-scroll-profile.json'
    if profile.returncode==0:result['scroll_profile']=json.loads(profile_path.read_text())
finally:
    sh('settings put global stay_on_while_plugged_in '+original_stay)
result['final_stay_on']=sh('settings get global stay_on_while_plugged_in')
result['advanced_restart']=sh('settings get --lineage secure advanced_reboot')
result['getenforce']=sh('getenforce')
result['boot_and_server_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server
result['temporary_packages_removed']={}
for package in ('dev.tapuz.t110.interaction','com.android.frameworks.libnet.tests'):
    r=run(adb+['uninstall',package],60)
    result['temporary_packages_removed'][package]=r.returncode==0 and 'Success' in r.stdout.decode(errors='replace')
(out/'v34-final-checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
