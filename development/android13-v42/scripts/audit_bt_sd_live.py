"""Read-only current Bluetooth, microSD and USB inventory."""
from pathlib import Path
import datetime,json,os,subprocess
p=Path(__file__).resolve().parents[1];out=p/'evidence/hardware-bt-sd';out.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
 assert r.returncode==0,r.stderr.decode(errors='replace')
 return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('id -u')=='0'
boot=sh('cat /proc/sys/kernel/random/boot_id');assert sh('getprop sys.boot_completed')=='1'
state=dict(host_time=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,read_only=True,additional_boots=0)
commands={
 'identity':'uname -a; getenforce; getprop ro.build.fingerprint; sha256sum /dev/block/mmcblk0p10; pidof netd system_server',
 'bluetooth':'''ls -l /sys/bus/sdio/devices; for d in /sys/bus/sdio/devices/*; do echo "$d"; cat "$d/vendor" "$d/device" "$d/class" "$d/modalias" 2>/dev/null; readlink "$d/driver"; done; cat /proc/modules; ls -lZ /dev/mbt* /dev/hci* 2>/dev/null; dumpsys bluetooth_manager; true''',
 'storage':'''cat /proc/partitions; cat /proc/mounts; sm list-disks; sm list-volumes all; dumpsys mount; for d in /sys/class/mmc_host/*; do echo "$d"; ls -l "$d"/; done; true''',
 'usb':'''getprop sys.usb.config; getprop sys.usb.state; ls -l /sys/class/android_usb/android0; dumpsys usb; ls -lZ /dev/mtp_usb /dev/usb-ffs/adb /dev/socket/adbd 2>/dev/null; true''',
 'kernel':'dmesg | tail -n 320',
}
for name,command in commands.items():
 text=sh(command,90);(out/(name+'.txt')).write_text(text+'\n',encoding='utf-8');print(name,len(text),flush=True)
assert sh('cat /proc/sys/kernel/random/boot_id')==boot
(out/'audit.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');print(json.dumps(state))
