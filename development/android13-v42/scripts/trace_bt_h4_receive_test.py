"""Bound and inspect the isolated upstream receive harness; never opens the radio."""
from pathlib import Path
import hashlib,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=25):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
remote='/data/local/tmp/t110_bt_h4_read_trace';assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT'
file=e/'bluetooth-vendor-interface-unit-tests';sha=hashlib.sha256(file.read_bytes()).hexdigest()
subprocess.run(adb+['push',str(file),remote],capture_output=True,timeout=45,check=True);assert sh('sha256sum '+remote).split()[0]==sha;sh('chmod 0700 '+remote)
process=None;pid=''
try:
 with (e/'h4-receive-harness.txt').open('wb') as log:
  process=subprocess.Popen(adb+['shell',remote+' --gtest_filter=H4ProtocolTest.TestReads'],stdout=log,stderr=subprocess.STDOUT)
  time.sleep(2)
  if process.poll() is None:
   pid=sh('pidof t110_bt_h4_read_trace || true');assert pid.isdigit()
   assert sh('sha256sum /proc/'+pid+'/exe').split()[0]==sha
   result=subprocess.run(adb+['shell','debuggerd -b '+pid],capture_output=True,timeout=35)
   (e/'h4-receive-backtrace.txt').write_bytes(result.stdout+result.stderr)
   if sh('pidof t110_bt_h4_read_trace || true')==pid:sh('kill -9 '+pid)
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
 print('H4_RECEIVE_HARNESS_CAPTURED',process.returncode)
finally:
 if pid and sh('pidof t110_bt_h4_read_trace || true')==pid:sh('kill -9 '+pid)
 if process and process.poll() is None:process.kill();process.wait(timeout=5)
 assert sh('test -f '+remote+' && test ! -L '+remote+' && sha256sum '+remote).split()[0]==sha;sh('rm '+remote)
