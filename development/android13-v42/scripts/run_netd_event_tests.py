from pathlib import Path
import hashlib,json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/netd-event';record=json.loads((e/'compiled.json').read_text());binary=e/'netd_idletimer_event_test'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==record['sha256']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45):
 r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
def sh(cmd,timeout=45):return call(['shell',cmd],timeout)
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
target='/data/local/tmp/t110-netd-idletimer-test';assert sh('test ! -e '+target+' && test ! -L '+target+' && echo ABSENT')=='ABSENT'
call(['push',binary,target]);assert sh('sha256sum '+target).split()[0]==record['sha256'];sh('chmod 0755 '+target)
try:
 result=sh(target+' --gtest_filter=IdletimerEventTest.*',60)
 (e/'unit-tests.txt').write_text(result+'\n',encoding='utf-8');assert '[  PASSED  ] 8 tests.' in result
finally:
 assert sh('test ! -L '+target+' && readlink -f '+target)==target;sh('rm '+target)
print(result)
