"""Save current hardware/UI diagnostics locally; no input, reboot or settings writes."""
from pathlib import Path
import argparse,datetime,json,os,re,subprocess
ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);a=ap.parse_args();assert re.fullmatch('[a-z0-9-]+',a.label)
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';record=e/(a.label+'.json');assert not record.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=60);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
state=dict(host_time=datetime.datetime.now().astimezone().isoformat(),boot_id=sh('cat /proc/sys/kernel/random/boot_id'),pids=sh('pidof system_server surfaceflinger com.android.systemui com.android.launcher3 com.android.settings'),boot_completed=sh('getprop sys.boot_completed'),enforcing=sh('getenforce'))
for name,cmd in {
 'window':'dumpsys window',
 'activity':'dumpsys activity activities',
 'crash':'logcat -d -b crash -t 120',
 'last-anr':'dumpsys activity lastanr',
 'cpu':'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq; cat /proc/loadavg; cat /proc/meminfo',
 'gfxinfo':'dumpsys gfxinfo com.android.settings framestats',
}.items():
 text=sh(cmd);(e/(a.label+'-'+name+'.txt')).write_text(text+'\n',encoding='utf-8')
 if name=='window':state['focus']=[line.strip() for line in text.splitlines() if 'mCurrentFocus=' in line]
state['native_screencap_skipped']='Use the verified framebuffer-file/pull capture path separately'
state['boot_stable']=sh('cat /proc/sys/kernel/random/boot_id')==state['boot_id']
record.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');print(json.dumps(state,indent=2))
