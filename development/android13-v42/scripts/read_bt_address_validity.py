from pathlib import Path
import hashlib,json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';out=e/'controller-address-validity.json';assert not out.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=25);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
previous=json.loads((e/'controller-features.json').read_text());build=json.loads((e/'h4-build.json').read_text())
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('cat /proc/sys/kernel/random/boot_id')==previous['boot_id'] and sh('cat /sys/module/mbt8xxx/parameters/require_fw_ready')=='Y'
remote='/data/local/tmp/t110_bt_h4_probe';assert sh('sha256sum '+remote).split()[0]==previous['probe_sha256']
binary=e/'t110_bt_h4_probe';assert hashlib.sha256(binary.read_bytes()).hexdigest()==build['binary_sha256']
assert hashlib.sha256((p/'scripts/bt_h4_probe.cpp').read_bytes()).hexdigest()==build['source_sha256']
subprocess.run(adb+['push',str(binary),remote],capture_output=True,timeout=45,check=True);assert sh('sha256sum '+remote).split()[0]==build['binary_sha256'];sh('chmod 0700 '+remote)
text=sh(remote);assert 'opcode=0x1009 status=0 bytes=13 controller_address_valid=1' in text and 'BLUETOOTH_H4_TRANSPORT_PASS' in text
(e/'controller-address-validity.txt').write_text(text+'\n',encoding='utf-8')
record=dict(boot_id=previous['boot_id'],controller_address_valid=True,controller_address_exported=False,address_programmed=False,probe_sha256=build['binary_sha256'])
out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
