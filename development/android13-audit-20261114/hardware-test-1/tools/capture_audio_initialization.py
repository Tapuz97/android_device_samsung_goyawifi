"""Bounded same-boot diagnostic after the as-installed speaker test failed."""
from pathlib import Path
import subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recovery_transport import adb,BASE,ADB,SERIAL
dest=BASE/'tests/android13-complete-20261114'
before=adb('shell','cat /proc/sys/kernel/random/boot_id').strip()
with (dest/'audio-reinitialization-private.txt').open('wb') as out:
    p=subprocess.Popen([ADB,'-s',SERIAL,'shell','logcat','-b','all','-T','1','-v','threadtime'],
                       stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        adb('shell','setprop ctl.restart audioserver')
        time.sleep(12)
    finally:p.terminate();p.wait(timeout=10)
assert adb('shell','cat /proc/sys/kernel/random/boot_id').strip()==before
(dest/'audio-policy-after-reinit.txt').write_text(adb('shell','dumpsys media.audio_policy'),encoding='utf-8')
print('Saved bounded audio startup diagnostics; same boot ID, no ROM reboot or flash.')
