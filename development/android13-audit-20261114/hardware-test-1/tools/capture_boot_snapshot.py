"""One bounded host-side snapshot; no continuous tablet logging."""
from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recovery_transport import adb,BASE,ADB,SERIAL
name=sys.argv[1] if len(sys.argv)>1 else 'startup'
assert name.replace('-','').isalnum()
dest=BASE/'tests/android13-complete-20261114';dest.mkdir(exist_ok=True)
for filename,command in (
    ('logcat-private.txt','logcat -b all -d -t 1200'),
    ('kernel-private.txt','dmesg'),
    ('activity.txt','dumpsys activity activities | head -n 100'),
    ('audio-flinger.txt','dumpsys media.audio_flinger'),
    ('audio-policy.txt','dumpsys media.audio_policy'),
    ('graphics.txt','dumpsys SurfaceFlinger'),
):
    try:(dest/(name+'-'+filename)).write_text(adb('shell',command,timeout=25),encoding='utf-8')
    except Exception as exc:(dest/(name+'-'+filename+'.error')).write_text(str(exc))
# The legacy GPU loader prints a textrel warning to the shell; a device file
# plus sync pull keeps those diagnostics out of PNG bytes on this build.
adb('shell','screencap -p /data/local/tmp/t110-current-screen.png',timeout=30)
adb('pull','/data/local/tmp/t110-current-screen.png',dest/(name+'-screen.png'))
assert (dest/(name+'-screen.png')).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
print(dest/(name+'-screen.png'))
