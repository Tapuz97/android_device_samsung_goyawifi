"""Finish a BOOT40 monitor interrupted by the adbd startup identity transition.
Read-only on the tablet. Never requests a reboot or repeats installation.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';path=e/'boot40-installation.json'
r=json.loads(path.read_text());assert r['status']=='BOOTING' and r['boot_requests']==1
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd):
 c=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=60);assert c.returncode==0,(cmd,c.stderr.decode(errors='replace'));return c.stdout.decode(errors='replace').strip()
assert sh('getprop sys.boot_completed')=='1' and sh('getenforce')=='Enforcing'
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==r['boot_sha256']
assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]=='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot!=r['previous_boot_id']
r.update(status='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING',boot_id=boot,system_server=sh('pidof system_server'),
 uptime=sh('cat /proc/uptime'),kernel=sh('uname -a'),verification_time=datetime.datetime.now().astimezone().isoformat(),
 monitor_interruption='Single ADB shell returned rc1 during startup; identity and both partition hashes reverified without reboot',
 seconds_to_boot_completed=None)
(e/'boot40-boot-events.txt').write_text(sh('logcat -d -b events -s boot_progress_start boot_progress_system_run boot_progress_enable_screen boot_progress_pms_ready')+'\n')
path.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
