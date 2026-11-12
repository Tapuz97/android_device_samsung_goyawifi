"""Run only the candidate backlight adapter, restoring the original panel value."""
from pathlib import Path
import subprocess,json,hashlib,os
p=Path(__file__).resolve().parents[1];e=p/'evidence/remote-fixes-20261110';candidate=e/'lights-candidate'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(a):return subprocess.run(adb+list(map(str,a)),capture_output=True,timeout=30,check=True)
def sh(s):return call(['shell',s]).stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
prov=json.loads((candidate/'provenance.json').read_text());remote='/data/local/tmp/t110-lights-candidate'
sh('mkdir -p '+remote)
for name in ['lights.mrvl.so','t110_lights_probe']:
    assert hashlib.sha256((candidate/name).read_bytes()).hexdigest()==prov['files'][name]['sha256']
    call(['push',candidate/name,remote+'/'+name]);assert sh('sha256sum '+remote+'/'+name).split()[0]==prov['files'][name]['sha256']
sh('chmod 0755 '+remote+'/t110_lights_probe; input keyevent WAKEUP')
before=sh('cat /sys/class/backlight/panel/brightness')
result=call(['shell',remote+'/t110_lights_probe '+remote+'/lights.mrvl.so'])
text=result.stdout.decode();(e/'lights-hardware-probe.txt').write_text(text)
after=sh('cat /sys/class/backlight/panel/brightness');assert before==after
assert 'requested=40 actual=40 status=0' in text and 'requested=220 actual=220 status=0' in text and 'result=0' in text
assert sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()==boot
record={'status':'PASS_CANDIDATE_HAL_TO_REAL_PANEL_NODE','original_brightness':before,'restored_brightness':after,'android_slider_integration_passed':False,'physical_brightness_observation_passed':False,'os_libraries_replaced':False,'additional_boots':0,'boot_and_server':boot}
(e/'lights-hardware-test.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
