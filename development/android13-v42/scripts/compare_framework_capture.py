"""Capture only after unlocking and settling Settings, then compare the real framebuffer."""
from pathlib import Path
import os,subprocess,json,time,hashlib
from PIL import Image,ImageChops,ImageStat
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s,timeout=30,check=True):return subprocess.run(adb+['shell',s],capture_output=True,timeout=timeout,check=check)
assert sh('cat /sys/block/mmcblk0/device/cid').stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL'
original=sh('settings get system screen_off_timeout; settings get global stay_on_while_plugged_in').stdout.decode().splitlines()
sh('settings put system screen_off_timeout 600000; settings put global stay_on_while_plugged_in 7')
try:
    subprocess.run(['python',str(p/'scripts/audit_ui_check.py'),'capture-settings','--evidence','offline-v41','--action','am start -W -a android.settings.SETTINGS'],check=True,timeout=100)
    lib=p/'evidence/remote-fixes-20261110/libui-candidate/libui.so';remote='/data/local/tmp/t110-gpu-readback'
    subprocess.run(adb+['push',str(lib),remote+'/libui.so'],check=True,capture_output=True)
    assert sh('sha256sum '+remote+'/libui.so').stdout.decode().split()[0]==hashlib.sha256(lib.read_bytes()).hexdigest()
    result=sh('LD_LIBRARY_PATH='+remote+' timeout 15 /system/bin/screencap -p '+remote+'/capture.png',timeout=25,check=False)
    (e/'capture-settings-command.txt').write_bytes(result.stdout+b'\nSTDERR\n'+result.stderr)
    subprocess.run(adb+['pull',remote+'/capture.png',str(e/'framework-settings.png')],check=True,capture_output=True)
    subprocess.run(['python',str(p/'scripts/capture_shade_transition.py'),'capture-after','--evidence','offline-v41'],check=True,timeout=40)
    a=Image.open(e/'framework-settings.png').convert('RGB');b=Image.open(e/'capture-after.png').convert('RGB');assert a.size==b.size
    difference=ImageChops.difference(a,b);stats=ImageStat.Stat(difference)
    record={'command_returncode':result.returncode,'dimensions':a.size,'channel_mean_absolute_difference':stats.mean,'window':sh('dumpsys window policy; dumpsys window windows | grep mCurrentFocus').stdout.decode(),'requires_visual_review':True}
    (e/'capture-settings-comparison.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='window'},indent=2))
finally:
    assert len(original)==2 and all(x.isdecimal() for x in original)
    sh('settings put system screen_off_timeout '+original[0]+'; settings put global stay_on_while_plugged_in '+original[1])
