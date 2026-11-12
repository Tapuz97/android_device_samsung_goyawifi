"""Same-boot Bluetooth transport check with verified module, no firmware download."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,subprocess,time
parser=argparse.ArgumentParser();parser.add_argument('--legacy-loader',action='store_true');args=parser.parse_args()
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';suffix='-legacy' if args.legacy_loader else '';receipt=e/('controller-probe'+suffix+'.json');assert not receipt.exists()
previous=json.loads((e/'controller-probe.json').read_text()) if args.legacy_loader else None
if previous:assert previous['insmod_exit']==1 and previous['boot_server_netd_stable']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=45,check=True):
 r=subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,r.stderr.decode(errors='replace')+r.stdout.decode(errors='replace')
 return r
def sh(command,timeout=45,check=True):return call(['shell',command],timeout,check).stdout.decode(errors='replace').strip()
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
module=json.loads((e/'module-build.json').read_text());probe=json.loads((e/'h4-build.json').read_text())
assert digest(e/'mbt8xxx.ko')==module['module_sha256'] and digest(e/'t110_bt_h4_probe')==probe['binary_sha256']
assert digest(p/'scripts/bt_h4_probe.cpp')==probe['source_sha256']
assert module['config_sha256']=='ad4c532f67160c36c130232b09717c19a045bd9f9abcfb85f0a6026901bfb832'
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL' and sh('id -u')=='0'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]=='8b5dc0d14169d5cb6f898d2f0e978242ace8aaef621a90ac47515939c887c0ab'
assert sh('getenforce')=='Enforcing'
assert sh('test ! -d /sys/module/mbt8xxx && test ! -e /dev/mbtchar0 && echo ABSENT')=='ABSENT'
assert sh('cat /sys/bus/sdio/devices/mmc2:0001:2/vendor /sys/bus/sdio/devices/mmc2:0001:2/device').split()==['0x02df','0x9132']
assert sh('test ! -L /sys/bus/sdio/devices/mmc2:0001:2/driver && echo UNBOUND')=='UNBOUND'
state=dict(host_time=datetime.datetime.now().astimezone().isoformat(),boot_id=sh('cat /proc/sys/kernel/random/boot_id'),
 system_server=sh('pidof system_server'),netd=sh('pidof netd'),module_sha256=module['module_sha256'],probe_sha256=probe['binary_sha256'],
 additional_boots=0,firmware_download_allowed=False,boot_written=False,system_written=False,status='HOST_VERIFIED')
def save():receipt.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
def internet(label):
 text=sh('am instrument --no-hidden-api-checks -w -e action https dev.tapuz.t110.interaction/.InteractionInstrumentation',100)
 (e/(label+suffix+'.txt')).write_text(text+'\n',encoding='utf-8');m=re.search(r'INSTRUMENTATION_RESULT: report=(.*)',text)
 return json.loads(m[1]) if m else dict(error='No instrumentation report')
state['internet_before']=internet('internet-before-bt');assert state['internet_before'].get('https_code')==204
remote_probe='/data/local/tmp/t110_bt_h4_probe';remote_module='/data/local/tmp/t110-bt-module-0100.ko'
for host,remote,expected,mode in [(e/'t110_bt_h4_probe',remote_probe,probe['binary_sha256'],'0700'),(e/'mbt8xxx.ko',remote_module,module['module_sha256'],'0600')]:
 if previous:
  assert sh('test -f '+remote+' && test ! -L '+remote+' && echo FILE')=='FILE'
  old_hash=previous['probe_sha256'] if remote==remote_probe else previous['module_sha256']
  assert sh('sha256sum '+remote).split()[0]==old_hash
 else:assert sh('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT')=='ABSENT'
 call(['push',host,remote],90);assert sh('sha256sum '+remote).split()[0]==expected;sh('chmod '+mode+' '+remote)
state['h4_self_test']=sh(remote_probe+' --self-test',20);assert state['h4_self_test']=='H4_SELF_TEST_PASS 8'
state['status']='STAGED_AND_SELF_TESTED';save()
try:
 loader=remote_probe+' --load-module' if args.legacy_loader else 'insmod '+remote_module+' drv_mode=1 debug_intf=0 require_fw_ready=1 req_fw_nowait=0'
 state['loader']='legacy_init_module' if args.legacy_loader else 'toybox_insmod'
 r=call(['shell',loader],55,False)
 state['insmod_exit']=r.returncode;(e/('insmod'+suffix+'.txt')).write_bytes(r.stdout+r.stderr)
 state['status']='MODULE_LOAD_RETURNED';save();time.sleep(2)
 assert r.returncode==0,'Module load failed; inspect saved kernel log'
 assert sh('test -c /dev/mbtchar0 && test ! -L /dev/mbtchar0 && echo CHAR')=='CHAR','Bluetooth node was not registered'
 state['node_before_label']=sh('ls -lZ /dev/mbtchar0')
 assert sh('stat -c %a:%u:%g /dev/mbtchar0')=='660:1000:1002'
 sh('chcon u:object_r:bluetooth_device:s0 /dev/mbtchar0')
 r=call(['shell',remote_probe],25,False);state['probe_exit']=r.returncode
 (e/('h4-controller'+suffix+'.txt')).write_bytes(r.stdout+r.stderr);state['h4_output']=r.stdout.decode(errors='replace').strip()
 state['transport_pass']=r.returncode==0 and 'BLUETOOTH_H4_TRANSPORT_PASS' in state['h4_output']
 state['internet_after']=internet('internet-after-bt')
 state['wifi_coexistence_pass']=state['internet_after'].get('https_code')==204 and state['internet_after'].get('wifi_transport') is True
 state['status']='H4_CONTROLLER_AND_WIFI_PASS' if state['transport_pass'] and state['wifi_coexistence_pass'] else 'CONTROLLER_QUALIFICATION_FAILED'
finally:
 (e/('kernel-after-bt'+suffix+'.txt')).write_text(sh('dmesg | tail -n 380')+'\n',encoding='utf-8')
 (e/('module-after-bt'+suffix+'.txt')).write_text(sh('cat /proc/modules; ls -lZ /dev/mbt*; getenforce; true')+'\n',encoding='utf-8')
 state['boot_server_netd_stable']=sh('cat /proc/sys/kernel/random/boot_id')==state['boot_id'] and sh('pidof system_server')==state['system_server'] and sh('pidof netd')==state['netd']
 save()
print(json.dumps(state,indent=2))
