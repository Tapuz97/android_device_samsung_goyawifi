"""Exercise Android's normal screenshot shortcut and inspect its saved image."""
from pathlib import Path
import hashlib,json,os,subprocess,time
from PIL import Image,ImageStat
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=35):return subprocess.run(adb+args,capture_output=True,timeout=timeout,check=True)
def sh(s):return call(['shell',s]).stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id');server=sh('pidof system_server')
def listing():
    return set(sh('if [ -d /data/media/0/Pictures/Screenshots ]; then find /data/media/0/Pictures/Screenshots -maxdepth 1 -type f; fi').splitlines())
before=listing();start=time.time();sh('input keyevent WAKEUP; wm dismiss-keyguard; input keyevent 120')
created=set()
while time.time()-start<35:
    time.sleep(2);created=listing()-before
    if created:break
record={'boot':boot,'system_server':server,'action':'Android KEYCODE_SYSRQ screenshot shortcut','new_files':sorted(created),'elapsed_seconds':time.time()-start,'native_action_passed':False}
for n,remote in enumerate(sorted(created)):
    assert remote.startswith('/data/media/0/Pictures/Screenshots/') and '\n' not in remote and remote.endswith('.png')
    r=call(['exec-out','cat '+"'"+remote.replace("'","'\\''")+"'"],60)
    local=e/f'native-screenshot-action-{n}.png';local.write_bytes(r.stdout)
    im=Image.open(local);im.load();assert im.size==(600,1024),im.size
    record.setdefault('images',[]).append({'file':local.name,'sha256':hashlib.sha256(r.stdout).hexdigest(),'dimensions':im.size,'stddev':ImageStat.Stat(im.convert('RGB')).stddev})
record['native_action_passed']=bool(created)
assert sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server
(e/'native-screenshot-action.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
