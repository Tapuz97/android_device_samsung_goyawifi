"""Qualify the installed repair pair on its single boot; restore UI preferences."""
from pathlib import Path
import argparse,hashlib,io,json,os,subprocess,time,uuid
from PIL import Image,ImageChops,ImageStat
parser=argparse.ArgumentParser();parser.add_argument('--boot32',action='store_true');args=parser.parse_args()
p=Path(__file__).resolve().parents[1];root=p/'evidence/offline-v41';e=root/'boot32-test' if args.boot32 else root
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=40,check=True):
    r=subprocess.run(adb+args,capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(args,r.stdout[-2000:],r.stderr[-2000:])
    return r
def sh(s,timeout=40,check=True):return call(['shell',s],timeout,check).stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot!='a17c0d2a-5f5d-4bcd-874d-1930feebe07b'
assert sh('getprop sys.boot_completed')=='1'
pair=json.loads((root/'contents.json').read_text())
target_boot=json.loads((p/'artifacts/android13-boot-v32/provenance.json').read_text())['full_boot_sha256'] if args.boot32 else pair['boot_sha256']
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==target_boot
record={'boot':boot,'system_server':sh('pidof system_server'),'host_epoch':time.time(),'device_epoch':int(sh('date +%s')),'timezone':sh('getprop persist.sys.timezone'),'boot_requests':1}
commands={
    'boot-live.txt':'cat /proc/uptime; getprop ro.boottime.init; getprop ro.boottime.bootanim; getprop init.svc.bootanim; getprop service.bootanim.exit; dumpsys activity users; ps -A',
    'boot-events.txt':'logcat -b events -d -v threadtime',
    'boot-crash.txt':'logcat -b crash -d -v threadtime',
    'boot-logcat.txt':"logcat -b all -d -t 12000 'snet_event_log:S' '*:V'",
    'boot-kernel.txt':'dmesg',
    'boot-lights.txt':'lshal | grep -E "light@|ILight"; dumpsys power; ls -lZ /sys/class/backlight/panel/brightness; cat /sys/class/backlight/panel/max_brightness',
    'boot-adb.txt':'cat /proc/net/unix | grep adbd; ls -lZ /dev/socket/adbd; getprop init.svc.adbd; echo "$BOOTCLASSPATH"; cmd activity get-current-user',
    'boot-input.txt':'cat /proc/bus/input/devices; dumpsys input',
    'boot-clock.txt':'date; cat /sys/class/rtc/rtc0/date /sys/class/rtc/rtc0/time; getprop persist.sys.timezone',
    'boot-memory.txt':'cat /proc/meminfo; cat /proc/swaps; cat /sys/block/zram0/disksize /sys/block/zram0/initstate; ls -lZ /dev/block/zram0',
}
for name,cmd in commands.items():
    r=call(['shell',cmd],60,False);(e/name).write_bytes(r.stdout+b'\nSTDERR\n'+r.stderr)
    print(name,r.returncode,len(r.stdout),flush=True)
original=sh('settings get system screen_off_timeout; settings get global stay_on_while_plugged_in; settings get system screen_brightness; settings get system screen_brightness_mode').splitlines()
assert len(original)==4 and all(x.isdecimal() for x in original)
try:
    sh('settings put system screen_off_timeout 600000; settings put global stay_on_while_plugged_in 7; input keyevent WAKEUP; wm dismiss-keyguard')
    end=time.monotonic()+25
    while time.monotonic()<end:
        policy=sh('dumpsys window policy')
        if 'showing=false' in policy and 'inputRestricted=false' in policy:break
        time.sleep(1)
    else:raise RuntimeError('Keyguard has not unlocked; no UI regression result')
    sh('am start -W -a android.settings.SETTINGS',60);time.sleep(3)
    captures=[]
    for n in range(1 if args.boot32 else 3):
        remote='/data/local/tmp/t110-v28-capture-'+uuid.uuid4().hex+'.png'
        try:
            r=call(['shell','screencap -p '+remote],35,False)
            (e/f'installed-screencap-{n}.stderr.txt').write_bytes(r.stdout+b'\nSTDERR\n'+r.stderr)
            assert r.returncode==0,(n,r.returncode,r.stderr)
            data=call(['exec-out','cat '+remote]).stdout
        finally:sh('test ! -f '+remote+' || rm '+remote)
        f=e/f'installed-screencap-{n}.png';f.write_bytes(data)
        assert data.startswith(b'\x89PNG\r\n\x1a\n'),(n,data[:200])
        image=Image.open(io.BytesIO(data));image.load();assert image.size==(600,1024),image.size
        captures.append({'file':f.name,'sha256':hashlib.sha256(data).hexdigest(),'dimensions':image.size,'stddev':ImageStat.Stat(image.convert('RGB')).stddev})
    subprocess.run(['python',str(p/'scripts/capture_shade_transition.py'),'installed-real-framebuffer','--evidence',str(e.relative_to(p/'evidence'))],check=True,timeout=50)
    a=Image.open(e/captures[-1]['file']).convert('RGB');b=Image.open(e/'installed-real-framebuffer.png').convert('RGB')
    record['framework_capture']={'captures':captures,'framebuffer_mean_absolute_difference':ImageStat.Stat(ImageChops.difference(a,b)).mean,'visual_review_pending':True}
    brightness=[]
    sh('settings put system screen_brightness_mode 0')
    for value in (40,220):
        sh('settings put system screen_brightness '+str(value));time.sleep(2)
        brightness.append({'setting':value,'panel':int(sh('cat /sys/class/backlight/panel/brightness'))})
    assert brightness[0]['panel']<brightness[1]['panel'],brightness
    record['native_brightness']=brightness
finally:
    sh('settings put system screen_brightness '+original[2]+'; settings put system screen_brightness_mode '+original[3]+'; settings put system screen_off_timeout '+original[0]+'; settings put global stay_on_while_plugged_in '+original[1])
record['post_system_server']=sh('pidof system_server');assert record['post_system_server']==record['system_server']
assert sh('cat /proc/sys/kernel/random/boot_id')==boot
record['temporary_settings_restored']=sh('settings get system screen_off_timeout; settings get global stay_on_while_plugged_in; settings get system screen_brightness; settings get system screen_brightness_mode').splitlines()==original
assert record['temporary_settings_restored']
(e/'live-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
