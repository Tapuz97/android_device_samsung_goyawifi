"""Qualify automatic radio startup and normal Android scanning on one boot.

Does not load a module, write rfkill, provision credentials, or join a network.
Keeps raw diagnostics local; the result reports only access-point counts.
"""
from pathlib import Path
import argparse, datetime, json, os, re, subprocess, time

parser=argparse.ArgumentParser()
parser.add_argument('--revision',type=int,required=True,choices=[33])
args=parser.parse_args()
p=Path(__file__).resolve().parents[1]
e=p/f'evidence/offline-v41/gapps-v{args.revision}-test'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']

def sh(command,timeout=60):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout,check=True)
    return r.stdout.decode(errors='replace').strip()

identity=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
installed=json.loads((e/'installation.json').read_text())
assert identity[0]==installed['boot_id']
assert sh('getprop sys.boot_completed')=='1'
assert sh('getenforce')=='Enforcing'
radio=sh('dmesg | grep -E "t110-radio-init|t110_radio_init|mlan:|wlan:|WLAN FW|firmware"')
(e/'automatic-radio-kernel.txt').write_text(radio+'\n')
startup_ok=bool(re.search(r"Service 't110-radio-init'.*exited with status 0",radio))
interface=sh('test -d /sys/class/net/wlan0 && echo PRESENT')=='PRESENT'
result=dict(host_time=datetime.datetime.now().astimezone().isoformat(),boot_and_server=identity,
            manual_driver_start=False,automatic_radio_exit_zero=startup_ok,
            wlan0_present=interface,selinux='Enforcing',network_credentials_used=False,
            association_dhcp_dns_internet_tested=False)

def save():
    (e/'wifi-qualification.json').write_text(json.dumps(result,indent=2)+'\n')

save()
assert startup_ok and interface, 'Automatic driver startup failed; no manual workaround applied'
before=sh('cmd wifi status')
assert 'Wifi is not connected' in before or 'Wifi is disabled' in before, 'Preserve an existing connection'
was_enabled='Wifi is enabled' in before
try:
    sh('cmd wifi set-wifi-enabled disabled');time.sleep(4)
    result['disabled_status']=sh('cmd wifi status')
    result['supplicant_when_disabled']=sh('getprop init.svc.wpa_supplicant')
    assert 'Wifi is disabled' in result['disabled_status']
    sh('cmd wifi set-wifi-enabled enabled');time.sleep(10)
    result['enabled_status']=sh('cmd wifi status')
    result['supplicant_when_enabled']=sh('getprop init.svc.wpa_supplicant')
    assert 'Wifi is enabled' in result['enabled_status']
    assert result['supplicant_when_enabled']=='running'
    sh('cmd wifi start-scan');time.sleep(12)
    scans=sh('cmd wifi list-scan-results')
    result['access_point_count']=len(re.findall(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}',scans))
    assert result['access_point_count']>0, 'No access points returned by Android scan'
    result['status']='AUTOMATIC_RADIO_TOGGLE_AND_SCAN_PASS'
finally:
    if not was_enabled:
        sh('cmd wifi set-wifi-enabled disabled')
    result['original_enabled_state_restored']=('Wifi is enabled' in sh('cmd wifi status'))==was_enabled
    result['boot_and_server_stable']=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()==identity
    save()
assert result['boot_and_server_stable'] and result['original_enabled_state_restored']
print(json.dumps(result,indent=2))
