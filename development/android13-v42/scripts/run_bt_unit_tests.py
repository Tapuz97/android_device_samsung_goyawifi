from pathlib import Path
import hashlib,json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';out=e/'h4-unit-tests.json';assert not out.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
previous=json.loads((e/'controller-probe-legacy.json').read_text());assert sh('cat /proc/sys/kernel/random/boot_id')==previous['boot_id']
f=e/'bluetooth-vendor-interface-unit-tests';sha=hashlib.sha256(f.read_bytes()).hexdigest();assert sha==json.loads((e/'h4-unit-build.json').read_text())['sha256']
remote='/data/local/tmp/t110_bt_h4_unit_tests';assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT'
subprocess.run(adb+['push',str(f),remote],capture_output=True,timeout=60,check=True);assert sh('sha256sum '+remote).split()[0]==sha;sh('chmod 0700 '+remote)
try:
 try:r=subprocess.run(adb+['shell',remote+' --gtest_filter=H4ProtocolTest.*:T110AtomicH4Test.*'],capture_output=True,timeout=100)
 except subprocess.TimeoutExpired as error:
  (e/'h4-unit-tests.txt').write_bytes((error.stdout or b'')+(error.stderr or b''))
  out.write_text(json.dumps(dict(status='TIMEOUT',binary_sha256=sha),indent=2)+'\n');raise
 text=(r.stdout+r.stderr).decode(errors='replace').replace('\r','');(e/'h4-unit-tests.txt').write_text(text,encoding='utf-8')
 legacy=len(re.findall(r'^\[\s+OK\s+\]\s+H4ProtocolTest\.',text,re.M));atomic=len(re.findall(r'^\[\s+OK\s+\]\s+T110AtomicH4Test\.',text,re.M))
 passed=r.returncode==0 and '[  PASSED  ]' in text and atomic==2 and legacy>0
 state=dict(status='PASS' if passed else 'FAIL',legacy_tests_passed=legacy,atomic_tests_passed=atomic,exit_code=r.returncode,binary_sha256=sha,boot_id=previous['boot_id'],hardware_commands_sent=False)
 out.write_text(json.dumps(state,indent=2)+'\n');print(text);assert passed
finally:
 pid=sh('pidof t110_bt_h4_unit_tests || true')
 if pid:
  assert pid.isdigit() and sh('sha256sum /proc/'+pid+'/exe').split()[0]==sha;sh('kill -9 '+pid)
 assert sh('test -f '+remote+' && test ! -L '+remote+' && sha256sum '+remote).split()[0]==sha
 sh('rm '+remote)
