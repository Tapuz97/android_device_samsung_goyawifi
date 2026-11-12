"""Wait read-only for USB return and preserve crash evidence; never reboot."""
from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
end=time.monotonic()+180
def call(cmd,timeout=15):
    return subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout)
while time.monotonic()<end:
    try:
        r=call('cat /sys/block/mmcblk0/device/cid',5)
        if r.stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL':break
    except subprocess.TimeoutExpired:pass
    time.sleep(3)
else:
    (e/'disconnect-watch.json').write_text(json.dumps({'usb_returned':False,'wait_seconds':180,'reboot_requested':False},indent=2)+'\n')
    print('USB_STILL_ABSENT_NO_DEVICE_CHANGES');raise SystemExit(2)
for name,cmd in {
    'disconnect-return-state.txt':'cat /proc/sys/kernel/random/boot_id; cat /proc/uptime; getprop sys.boot_completed; test ! -x /sbin/recovery || echo TWRP; pidof system_server',
    'disconnect-last-kmsg.txt':'cat /proc/last_kmsg',
    'disconnect-current-dmesg.txt':'dmesg',
    'disconnect-logcat.txt':'logcat -b all -d -t 10000',
    'disconnect-codec-report.json':'cat /data/user/0/dev.tapuz.t110.audit/files/report.json',
}.items():
    try:
        r=call(cmd,50);(e/name).write_bytes(r.stdout)
        (e/(name+'.stderr')).write_bytes(r.stderr);print(name,r.returncode,len(r.stdout),flush=True)
    except subprocess.TimeoutExpired as x:
        (e/(name+'.timeout')).write_bytes(x.stdout or b'')
(e/'disconnect-watch.json').write_text(json.dumps({'usb_returned':True,'reboot_requested':False},indent=2)+'\n')
