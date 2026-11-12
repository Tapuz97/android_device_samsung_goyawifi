"""Read native Android network state; exercise DNS/TLS from an ordinary app UID."""
from pathlib import Path
import argparse,datetime,json,os,re,subprocess,time
parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);parser.add_argument('--cycle',action='store_true');parser.add_argument('--revision',type=int,choices=(40,41,42),default=40);parser.add_argument('--system-v36',action='store_true');a=parser.parse_args()
assert re.fullmatch('[a-z0-9-]+',a.label)
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';path=e/(a.label+'.json');assert not path.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=30):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('getprop sys.boot_completed')=='1'
boot=sh('cat /proc/sys/kernel/random/boot_id');server=sh('pidof system_server');netd=sh('pidof netd');assert server and netd
install_path=e/f'boot{a.revision}-installation.json' if a.revision!=41 else p/'evidence/offline-v41/gapps-v35-test/installation.json'
if a.system_v36:
 assert a.revision==42
 install_path=e/'netd-event/v36-installation.json'
install=json.loads(install_path.read_text());assert boot==install['boot_id']
record=dict(host_time=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,system_server=server,netd=netd,kernel_revision=a.revision,system_revision=36 if a.system_v36 else 35,
 manual_routes_added=False,manual_iptables_rules_added=False,network_credentials_exported=False)
def save():path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
try:
 if a.cycle:
  before=sh('cmd wifi status');assert 'Wifi is enabled' in before
  sh('cmd wifi set-wifi-enabled disabled');time.sleep(4)
  record['disabled_status']=sh('cmd wifi status');assert 'Wifi is disabled' in record['disabled_status']
  sh('cmd wifi set-wifi-enabled enabled')
  for retry in range(18):
   time.sleep(5)
   if 'Wifi is connected' in sh('cmd wifi status'):break
  record['automatic_reconnection']='Wifi is connected' in sh('cmd wifi status')
 for name,command in {
  'wifi':'cmd wifi status; ip addr show wlan0; ip rule; ip route show table all',
  'connectivity':'dumpsys connectivity',
  'netd':'dumpsys netd',
  'netd-errors':"logcat -d -b all -t 5000 | grep -E 'networkAddInterface|networkAddRoute|Remote I/O|MARK|IDLETIMER|Fwmark|ConnectivityService|NetworkMonitor' || true",
  'packet-targets':'cat /proc/net/ip_tables_targets; cat /proc/net/ip6_tables_targets',
  'state':'getenforce; cat /proc/uptime; pidof system_server surfaceflinger com.android.systemui com.android.launcher3',
 }.items():
  (e/(a.label+'-'+name+'.txt')).write_text(sh(command,60)+'\n',encoding='utf-8')
 text=sh('am instrument --no-hidden-api-checks -w -e action https dev.tapuz.t110.interaction/.InteractionInstrumentation',90)
 (e/(a.label+'-app-https.txt')).write_text(text+'\n',encoding='utf-8')
 m=re.search(r'INSTRUMENTATION_RESULT: report=(.*)',text)
 record['app_network']=json.loads(m[1]) if m else {'error':'No report'}
 result=record['app_network']
 record['app_dns_tls_pass']=result.get('completed') and result.get('wifi_transport') and result.get('https_code')==204 and result.get('dns_result_count',0)>0
 record['android_validated']=result.get('validated',False)
 record['status']='APP_DNS_TLS_PASS' if record['app_dns_tls_pass'] else 'NETWORK_QUALIFICATION_FAILED'
 if a.cycle:
  time.sleep(20)
  record['idletimer_observation_seconds']=20
finally:
 try:
  if a.cycle and 'Wifi is disabled' in sh('cmd wifi status'):sh('cmd wifi set-wifi-enabled enabled')
 except Exception as error:record['wifi_restore_error']=str(error)
 record['boot_and_server_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server
 record['netd_stable']=sh('pidof netd')==netd
 if not record['boot_and_server_stable'] or not record['netd_stable']:record['status']='NETWORK_PROCESS_RESTART_FAILED'
 if a.cycle and not record.get('automatic_reconnection'):record['status']='WIFI_RECONNECTION_FAILED'
 save()
print(json.dumps(record,indent=2))
