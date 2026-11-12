"""Refresh early-started adbd after classpath exports, without rebooting Android."""
from pathlib import Path
import subprocess,os,time,json
p=Path(__file__).resolve().parents[1];e=p/'evidence/remote-fixes-20261110'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def cmd(args,timeout=20,check=True):return subprocess.run(adb+args,capture_output=True,timeout=timeout,check=check)
def sh(s,**kw):return cmd(['shell',s],**kw).stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('getprop ro.adb.secure')=='0'
assert sh('id -u')=='0'
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server; pidof adbd').splitlines()
old=cmd(['shell','appwidget help'],check=False)
def java_works(r):return r.returncode==0 and b'usage: adb shell appwidget' in (r.stdout+r.stderr).lower()
if java_works(old):raise SystemExit('Java shell runtime already available; no restart needed')
cmd(['shell','setprop ctl.restart adbd'],check=False)
deadline=time.monotonic()+35
while time.monotonic()<deadline:
    try:
        r=cmd(['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server; pidof adbd'],timeout=3,check=False)
        after=r.stdout.decode().strip().splitlines()
        if r.returncode==0 and len(after)==3:break
    except subprocess.TimeoutExpired:pass
    time.sleep(1)
else:raise RuntimeError('ADB did not reconnect; no further device operations attempted')
assert before[:2]==after[:2] and before[2]!=after[2],(before,after)
test=cmd(['shell','appwidget help'],check=False)
record={'before_boot_server_adbd':before,'after_boot_server_adbd':after,'old_java_command_returncode':old.returncode,'old_java_command_stdout':old.stdout.decode(),'old_java_command_stderr':old.stderr.decode(),'new_java_command_returncode':test.returncode,'new_java_command_stdout':test.stdout.decode(),'new_java_command_stderr':test.stderr.decode(),'additional_boots':0}
(e/'adbd-runtime-refresh.json').write_text(json.dumps(record,indent=2)+'\n')
assert java_works(test),record
print('ADB_RECONNECTED_SAME_ANDROID_BOOT_JAVA_SHELL_RUNTIME_FIXED')
