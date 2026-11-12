"""Read-only Bluetooth and button-light inventory on the current Android boot."""
from pathlib import Path
import datetime,json,os,subprocess
p=Path(__file__).resolve().parents[1];out=p/'evidence/hardware-v35'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=30):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id')
commands={
 'button-lights':'''ls -l /sys/class/sec/sec_touchkey/; for r in /sys/class/regulator/regulator.*; do echo "$r"; cat "$r/name" "$r/state" "$r/num_users" 2>/dev/null; done; dumpsys lights''',
 'bluetooth-transport':'''for r in /sys/class/rfkill/rfkill*; do echo "$r"; cat "$r/name" "$r/type" "$r/state" 2>/dev/null; done; ls -l /sys/bus/sdio/devices/; ls -l /dev/mbt* /dev/hci* 2>/dev/null; cat /proc/modules; dumpsys bluetooth_manager''',
}
for name,command in commands.items():
    text=sh(command,60);(out/(name+'.txt')).write_text(text+'\n',encoding='utf-8');print(name,len(text),'characters')
assert boot==sh('cat /proc/sys/kernel/random/boot_id')
(out/'aux-readonly.json').write_text(json.dumps({'host_time':datetime.datetime.now().astimezone().isoformat(),
 'boot_id':boot,'writes':False,'additional_boots':0},indent=2)+'\n')
