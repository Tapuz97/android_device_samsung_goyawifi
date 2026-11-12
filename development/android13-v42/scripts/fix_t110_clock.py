"""Set clock through AlarmManager, preserving a before/after repair record."""
from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/remote-fixes-20261110';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s):
    r=subprocess.run(adb+['shell',s],capture_output=True,timeout=20,check=True)
    return r.stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
def state():return {'host_epoch':time.time(),'device':sh('date +%s; getprop persist.sys.timezone; cat /sys/class/rtc/rtc0/date /sys/class/rtc/rtc0/time'),'boot':sh('cat /proc/sys/kernel/random/boot_id')}
before=state();result=sh('cmd alarm set-time '+str(int(time.time()*1000)))
zone=sh('cmd alarm set-timezone Asia/Jerusalem');time.sleep(3);after=state()
offset=int(after['device'].splitlines()[0])-after['host_epoch'];assert abs(offset)<3,offset
assert before['boot']==after['boot']
record={'before':before,'set_time_result':result,'set_timezone_result':zone,'after':after,'offset_seconds':offset,'status':'CURRENT_CLOCK_CORRECTED_RTC_WRITTEN_PERSISTENCE_PENDING','additional_boots':0}
(e/'clock-fix.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
