from pathlib import Path
import json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=45);return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
f='/data/vendor/t110-bluetooth/controller_address';data=sh('cat '+f)
state=dict(address_text_valid=bool(re.fullmatch(r'[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}',data)),address_nonzero=data!='00:00:00:00:00:00',address_exported=False)
text=sh('ls -ldZ /data /data/vendor /data/vendor/t110-bluetooth; ls -lZ '+f+'; getprop ro.bt.bdaddr_path; cat /proc/self/attr/current')
print(text);(e/'identity-parent-access.txt').write_text(text+'\n')
kernel=sh('dmesg');(e/'identity-access-kernel.txt').write_text(kernel+'\n')
print('\n'.join(line for line in kernel.splitlines() if 'denied' in line and any(x in line for x in ['hal_bluetooth','t110_bt_address','vendor_data_file'])))
(e/'identity-text-validation.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))
