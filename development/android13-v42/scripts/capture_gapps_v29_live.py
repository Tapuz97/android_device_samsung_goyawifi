"""Capture the one combined boot's real state without rebooting or completing setup."""
from pathlib import Path
import datetime,json,os,subprocess,sys
p=Path(__file__).resolve().parents[1]
v30='--v30' in sys.argv
v31='--v31' in sys.argv
v32='--v32' in sys.argv
v33='--v33' in sys.argv
v34='--v34' in sys.argv
assert sum([v30,v31,v32,v33,v34])<=1
version='v34' if v34 else 'v33' if v33 else 'v32' if v32 else 'v31' if v31 else 'v30' if v30 else 'v29'
e=p/'evidence/offline-v41'/f'gapps-{version}-test'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
    r=subprocess.run(adb+args,capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(args,r.stdout[-1000:],r.stderr[-1000:])
    return r
def sh(s,timeout=45,check=True):return call(['shell',s],timeout,check).stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines();assert len(before)==2
assert before[0]!='046c74cc-c706-4b07-8105-bd06c5818ffe'
if v30 or v31 or v32 or v33 or v34:
    assert before[0]==json.loads((e/'installation.json').read_text())['boot_id']
record={'host_time':datetime.datetime.now().astimezone().isoformat(),'boot_and_server':before,'boot_completed':sh('getprop sys.boot_completed'),'user_state':sh('cmd user list -v',check=False),'getenforce':sh('getenforce'),'additional_boot_requests':0}
commands={
 'kernel':'dmesg','crash':'logcat -b crash -d -v threadtime','startup':'logcat -b all -d -v threadtime',
 'memory':'cat /proc/meminfo; cat /proc/swaps; cat /sys/block/zram0/disksize /sys/block/zram0/initstate; cat /sys/block/zram0/orig_data_size /sys/block/zram0/compr_data_size /sys/block/zram0/mem_used_total',
 'packages':'pm path com.android.vending; pm path com.google.android.gms; pm path com.google.android.gsf; pm path com.google.android.setupwizard; pm path com.android.settings; pm path org.lineageos.lineageparts; pm path org.lineageos.trebuchet',
 'focus':'dumpsys activity activities; dumpsys window windows',
 'input':'dumpsys input','power':'dumpsys power','disk':'df -k /data /system /stage-data; ls -ldZ /stage-data/local/tmp/t110-rom-data*',
 'time':'date; getprop persist.sys.timezone; getprop ro.build.fingerprint; getprop ro.com.google.gmsversion; getprop ro.bionic.arch; getprop ro.build.version.sdk; getprop ro.boottime.bootanim; getprop service.bootanim.exit',
 'policy':'ls -lZ /dev/block/zram0 /sys/block/zram0/disksize; cat /proc/sys/vm/swappiness',
}
for name,cmd in commands.items():
    r=call(['shell',cmd],90,False);(e/('current-'+name+'.txt')).write_bytes(r.stdout+b'\nSTDERR:\n'+r.stderr)
swaps=sh('cat /proc/swaps');record['zram_active']='/dev/block/zram0' in swaps
record['google_core_packages_registered']=all('package:' in sh('pm path '+pkg) for pkg in ['com.android.vending','com.google.android.gms','com.google.android.gsf'])
record['google_online_signin_or_download_tested']=False
record['old_data_profile_present']=sh('test -d /stage-data/local/tmp/t110-rom-data.pre-gapps && echo YES')=='YES'
record['user_unlocked']='RUNNING_UNLOCKED' in sh('dumpsys user')
record['zram_node_type']=sh('ls -lZ /dev/block/zram0')
record['swap_reclaim_values']=sh('cat /proc/sys/vm/swappiness /proc/sys/vm/page-cluster').splitlines()
if v30 or v31 or v32 or v33 or v34:
    record['zram_started_without_manual_activation']=record['zram_active'] and 'swap_block_device' in record['zram_node_type']
    record['unsupported_optional_keyboard_library_absent']=sh('test ! -e /system/product/lib/libjni_latinimegoogle.so && echo YES')=='YES'
    record['native_keyboard_library_sha256']=sh('sha256sum /system/product/lib/libjni_latinime.so').split()[0]
after=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines();record['boot_and_server_stable']=after==before
assert after==before
(e/'live-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
