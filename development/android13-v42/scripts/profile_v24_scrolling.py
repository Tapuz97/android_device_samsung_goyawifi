"""Measure CPU time and presented frames on the existing boot; never reboot."""
from pathlib import Path
import subprocess, os, time, json, re, argparse
parser=argparse.ArgumentParser()
parser.add_argument('--label',default='v24')
args=parser.parse_args()
assert re.fullmatch(r'[a-z0-9-]+',args.label)
p = Path(__file__).resolve().parents[1]
out = p / 'evidence/offline-v35'
out.mkdir(exist_ok=True)
adb = [str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'), '-s', 'T110_ADB_SERIAL']
def shell(s, timeout=40):
    return subprocess.check_output(adb+['shell',s], timeout=timeout).decode(errors='replace').strip()
boot=shell('cat /proc/sys/kernel/random/boot_id')
assert shell('getprop ro.product.device')=='t110_bringup'
launch_started=time.monotonic()
launch=shell('input keyevent WAKEUP; wm dismiss-keyguard; sleep 2; am start -W -a android.settings.SETTINGS',timeout=100)
launch_seconds=time.monotonic()-launch_started
time.sleep(2)
pids={name:int(shell('pidof '+name).split()[0]) for name in ['surfaceflinger','android.hardware.graphics.composer@2.1-service','com.android.settings','system_server']}
def snapshot():
    raw=shell('cat /proc/uptime; '+'; '.join('cat /proc/%s/stat'%pid for pid in pids.values()))
    lines=raw.splitlines()
    ticks={}
    for name,line in zip(pids,lines[1:]):
        fields=line.rsplit(')',1)[1].split()
        ticks[name]=dict(user=int(fields[11]),system=int(fields[12]),minor_faults=int(fields[7]),major_faults=int(fields[9]))
    return dict(uptime=float(lines[0].split()[0]),processes=ticks)
before_dump=shell('dumpsys SurfaceFlinger')
assert 'blanked=0' in before_dump, 'Wake the display before measuring scrolling'
activity=shell('dumpsys activity activities')
focused=re.search(r'(?:topResumedActivity=|\bResumedActivity:|mResumedActivity:)\s*([^\n]+)',activity)
assert focused and 'com.android.settings/' in focused[1], 'Settings must be the foreground app'
window_focus=shell('dumpsys window | grep mCurrentFocus')
# Removed/hidden ANR windows can remain in the full dump. The current focus
# determines whether the modal dialog actually intercepts this input.
assert 'com.android.settings/' in window_focus, 'Settings must receive the scrolling input'
before=snapshot()
shell('input touchscreen -d 0 swipe 300 850 300 300 1200; input touchscreen -d 0 swipe 300 300 300 850 1200; input touchscreen -d 0 swipe 300 850 300 300 1200; input touchscreen -d 0 swipe 300 300 300 850 1200',timeout=70)
after=snapshot()
after_dump=shell('dumpsys SurfaceFlinger')
assert 'com.android.settings/' in shell('dumpsys window | grep mCurrentFocus'), 'Settings lost scrolling input focus'
elapsed=after['uptime']-before['uptime']
frames=lambda s:int(re.search(r'T110 direct fb0 scanout: frames=(\d+)',s)[1])
result=dict(boot_id=boot,pids=pids,seconds=elapsed,presented_frames=frames(after_dump)-frames(before_dump),before=before,after=after,additional_boots=0)
result['activity_start_output']=launch
result['activity_start_command_seconds']=round(launch_seconds,3)
assert result['presented_frames']>0, 'No presented frames; scrolling performance was not measured'
# This kernel's saved config records HZ=100.
result['cpu_one_core_percent']={name:round(100*sum(after['processes'][name][k]-before['processes'][name][k] for k in ('user','system'))/100/elapsed,2) for name in pids}
for counter in ('copy_ns','post_ns'):
    old=re.search(counter+r'=(\d+)',before_dump)
    new=re.search(counter+r'=(\d+)',after_dump)
    if old and new and result['presented_frames']:
        result[counter.replace('_ns','_milliseconds_per_frame')]=(int(new[1])-int(old[1]))/1e6/result['presented_frames']
assert shell('cat /proc/sys/kernel/random/boot_id')==boot
(out/(args.label+'-scroll-profile.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(out/(args.label+'-surfaceflinger-after.txt')).write_text(after_dump,encoding='utf-8')
print(json.dumps(result,indent=2))
