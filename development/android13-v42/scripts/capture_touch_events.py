"""Bounded, read-only capture of the identified touchscreen during UI validation."""
from pathlib import Path
import argparse,json,os,re,subprocess,time
p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path);p.add_argument('--seconds',type=int,default=180);a=p.parse_args()
assert a.trial.is_dir() and 1<=a.seconds<=300
base=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
r=subprocess.run(base+['shell','test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid'],capture_output=True,timeout=10,check=True)
assert r.stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL'
r=subprocess.run(base+['shell','getevent -lp'],capture_output=True,timeout=10,check=True)
devices=r.stdout.decode(errors='replace');(a.trial/'touch-devices.txt').write_text(devices)
matches=re.findall(r'add device \d+: (/dev/input/event\d+)\s+name:\s+"sec_touchscreen"',devices)
assert len(matches)==1,devices
device=matches[0];stop=a.trial/'stop-touch-capture';assert not stop.exists()
report={'device':device,'seconds_limit':a.seconds,'device_writes':False,'started_at':time.time()}
(a.trial/'touch-capture.json').write_text(json.dumps(report,indent=2)+'\n')
print('TOUCH_CAPTURE_STARTED '+device,flush=True)
with (a.trial/'touch-events.txt').open('wb') as out,(a.trial/'touch-events-stderr.txt').open('wb') as err:
    process=subprocess.Popen(base+['shell',f'timeout {a.seconds} getevent -lt {device}'],stdout=out,stderr=err)
    while process.poll() is None:
        if stop.exists() or time.time()-report['started_at']>a.seconds+10:
            process.terminate();break
        time.sleep(.5)
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait()
report.update(returncode=process.returncode,bytes=(a.trial/'touch-events.txt').stat().st_size,ended_at=time.time())
(a.trial/'touch-capture.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
