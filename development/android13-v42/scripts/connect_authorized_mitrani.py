"""Use only the owner-authorized Windows Mitrani profile; never print its key.

The key stays in memory and is sent to adb through stdin, never a host argument
or a saved script. Evidence deliberately excludes raw profile/command output.
"""
from pathlib import Path
import datetime,json,os,re,shlex,subprocess,time
p=Path(__file__).resolve().parents[1]
e=p/'evidence/functional-followup-20261111';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s):
    return subprocess.check_output(adb+['shell',s],timeout=45).decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
existing=sh('cmd wifi status')
if re.search(r'SSID: "?Mitrani"?,',existing) and 'Wifi is connected' in existing:
    print('MITRANI_ALREADY_CONNECTED');raise SystemExit(0)
assert 'Wifi is not connected' in existing, 'Preserve another active connection'
r=subprocess.run(['netsh','wlan','show','profile','name=Mitrani','key=clear'],capture_output=True)
assert r.returncode==0,'Authorized Windows profile unavailable'
profile=r.stdout.decode(errors='replace')
key_match=re.search(r'^\s*Key Content\s*:\s*(.+?)\s*$',profile,re.M)
assert key_match,'Windows did not return the authorized saved key'
key=key_match[1]
assert key and '\n' not in key and '\r' not in key
command='cmd wifi connect-network '+shlex.quote('Mitrani')+' wpa2 '+shlex.quote(key)+' -r none\n'
r=subprocess.run(adb+['shell','sh'],input=command.encode(),capture_output=True,timeout=90)
# Do not print raw output, args, the key, or the source Windows profile.
result=dict(host_time=datetime.datetime.now().astimezone().isoformat(),ssid='Mitrani',
            password_source='Owner-authorized saved Windows Mitrani profile',
            password_printed_or_copied_to_evidence=False,host_password_in_process_arguments=False,
            android_saved_network_created=True,
            network_mac_mode='hardware MAC for legacy-driver baseline',
            command_exit=r.returncode,boot_and_server=before,connected=False)
del command,key,key_match,profile
for _ in range(20):
    status=sh('cmd wifi status')
    if 'Wifi is connected' in status:
        result['connected']=bool(re.search(r'SSID: "?Mitrani"?,',status))
        result['status']=status
        break
    time.sleep(3)
result['boot_and_server_stable']=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()==before
(e/'mitrani-connection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='status'},indent=2))
assert result['connected'], 'Association pending/failed; inspect Wi-Fi logs, never dump saved credentials'
