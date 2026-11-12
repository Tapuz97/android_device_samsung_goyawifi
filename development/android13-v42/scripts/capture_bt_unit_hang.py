from pathlib import Path
import hashlib,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=30):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
pid=sh('pidof t110_bt_h4_unit_tests || true')
if not pid:print('NO_TEST_PROCESS_REMAINS');raise SystemExit(0)
assert pid.isdigit()
expected=hashlib.sha256((e/'bluetooth-vendor-interface-unit-tests').read_bytes()).hexdigest()
assert sh('sha256sum /proc/'+pid+'/exe').split()[0]==expected
try:
 r=subprocess.run(adb+['shell','debuggerd -b '+pid],capture_output=True,timeout=35);(e/'h4-unit-hang.txt').write_bytes(r.stdout+r.stderr)
finally:
 if sh('pidof t110_bt_h4_unit_tests || true')==pid:sh('kill -9 '+pid)
print('H4_UNIT_HANG_CAPTURED_TEST_PROCESS_STOPPED')
